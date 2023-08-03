from source.company.PublicCompany import PublicCompany
from source.Messaging import Responder, Requester, Puller
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps
import asyncio
import random
import string


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

def generate_companies(names, requester, responder, time) -> list:
    companies = []
    for name in names:
        companies.append(PublicCompany(name, time, requester, responder))
    return companies

async def run_companies(time_channel=5114, exchange_channel=5570, company_channel=5572) -> None:
    try:
        num_companies = 20

        responder = Responder(company_channel)
        requester = Requester(channel=exchange_channel)
        time_puller = Puller(time_channel)
        await responder.connect()
        await requester.connect()
        
        def get_time():
            clock = time_puller.pull()
            if clock == None: 
                pass
            elif type(clock) is dict and 'time' not in clock:
                pass
            elif type(clock['time']) is dict:
                pass
            else: 
                return clock['time']  

        time = get_time()
        companies = generate_companies(generate_names(num_companies), Requests(requester), responder, time)

        async def callback(msg):
            if msg['topic'] == 'get_income_statement': return (company.income_statement for company in companies if company.name == msg['company'])
            elif msg['topic'] == 'get_balance_sheet': return (company.balance_sheet for company in companies if company.name == msg['company'])
            elif msg['topic'] == 'get_cash_flow': return (company.cash_flow for company in companies if company.name == msg['company'])
            elif msg['topic'] == 'get_dividend_payment_date': return (company.dividend_payment_date for company in companies if company.name == msg['company'])
            elif msg['topic'] == 'get_ex_dividend_date': return (company.ex_dividend_date for company in companies if company.name == msg['company'])
            elif msg['topic'] == 'get_dividends_to_distribute': return (company.dividends_to_distribute for company in companies if company.name == msg['company'])
            else: return f'unknown topic {msg["topic"]}'

        for company in companies:
            await company.initial_shares(random.randint(500,10000), random.randint(0,500))

        while True:
            for company in companies:
                await company.next(time)
            msg = await responder.respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(run_companies)