from source.company.PublicCompany import PublicCompany
from source.Messaging import Responder, Requester, Subscriber, Pusher
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps, string_to_time
import asyncio
import random
import string
import traceback


def generate_names(num_companies=20) -> list:
    """
    A function that randomly generates one to five letter company names
    """
    names = []
    for i in range(num_companies):
        name = ''
        for j in range(random.randint(1,5)):
            name += random.choice(string.ascii_letters)
        if name not in names:    
            names.append(name)
        else:
            i -= 1
    return names

def generate_companies(names, requester, time) -> list:
    companies = []
    for name in names:
        companies.append(PublicCompany(name, time, requester))
    return companies

async def run_companies(time_channel=5114, exchange_channel=5570, company_channel=5572) -> None:
    try:
        num_companies = 20

        responder = Responder(company_channel)
        requester = Requester(channel=exchange_channel)
        time_puller = Subscriber(time_channel)
        await responder.connect()
        await requester.connect()
        
        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else:
                return string_to_time(clock) 

        time = get_time()
        companies = generate_companies(generate_names(num_companies), Requests(requester), time)

        async def callback(msg):
            if msg['topic'] == 'get_date': return dumps(time)
            elif msg['topic'] == 'get_companies': return dumps([company.name for company in companies])
            elif "company" in msg:
                for company in companies:
                    if company.name == msg['company']:
                        if msg['topic'] == 'get_company': return dumps(company.to_dict())
                        elif msg['topic'] == 'get_income_statement': return dumps(company.income_statement)
                        elif msg['topic'] == 'get_balance_sheet': return dumps(company.balance_sheet)
                        elif msg['topic'] == 'get_cash_flow': return dumps(company.cash_flow)
                        elif msg['topic'] == 'get_dividend_payment_date': return dumps(company.dividend_payment_date)
                        elif msg['topic'] == 'get_ex_dividend_date': return dumps(company.ex_dividend_date)
                        elif msg['topic'] == 'get_dividends_to_distribute': return dumps(company.dividends_to_distribute)
                        break
                    else: return f'unknown company {msg["company"]}'

            else: return f'unknown topic {msg["topic"]}'

        for company in companies:
            await company.issue_initial_shares(random.randint(500,10000), random.randint(0,500))
            await company.initial_financials()

        while True:
            time = get_time()
            for company in companies:
                company.current_date = time
                await company.next(time)
            msg = await responder.lazy_respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(run_companies())