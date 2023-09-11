from source.company.PublicCompany import PublicCompany
from source.Messaging import Responder, Requester, Subscriber, Pusher
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps, string_to_time
import asyncio
import random
import traceback
from Channels import Channels

names= ['A', 'frXoX', 'wAt', 'Ayc', 'EXCAb', 'Qw', 'vbcY', 'ZM', 'j', 'nNLga', 'Ln', 'ao', 'k', 'icyJ', 'r', 'qk', 'BeHN', 'if', 'yAnL', 'sw']

def generate_companies(names, requester, time) -> dict:
    companies = {}
    for name in names:
        company = PublicCompany(name, time, requester)
        companies[company.symbol] = company
    return companies



async def run_companies() -> None:
    try:
        channels = Channels()
        responder = Responder(channels.company_channel)
        requester = Requester(channel=channels.exchange_channel)
        time_puller = Subscriber(channels.time_channel)
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
        companies = generate_companies(names, Requests(requester), time)

        async def callback(msg):
            if msg['topic'] == 'get_date': return dumps(time)
            elif msg['topic'] == 'get_companies': return dumps([company.symbol for company in companies])
            elif "company" in msg:
                if msg['company'] in companies:
                    if msg['topic'] == 'get_company': return dumps(companies[msg['company']].to_dict())
                    elif msg['topic'] == 'get_income_statement': return dumps(companies[msg['company']].income_statement)
                    elif msg['topic'] == 'get_balance_sheet': return dumps(companies[msg['company']].balance_sheet)
                    elif msg['topic'] == 'get_cash_flow': return dumps(companies[msg['company']].cash_flow)
                    elif msg['topic'] == 'get_dividend_payment_date': return dumps(companies[msg['company']].dividend_payment_date)
                    elif msg['topic'] == 'get_ex_dividend_date': return dumps(companies[msg['company']].ex_dividend_date)
                    elif msg['topic'] == 'get_dividends_to_distribute': return dumps(companies[msg['company']].dividends_to_distribute)
                else: return dumps({"warning": f'unknown company {msg["company"]}'})

            else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})

        for company in companies:
            await companies[company].issue_initial_shares(random.randint(500,10000), random.randint(1,150))
            await companies[company].initial_operate_and_report()

        while True:
            time = get_time()
            for company in companies:
                companies[company].current_date = time
                await companies[company].next(time)
            msg = await responder.lazy_respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)
        print(traceback.format_exc())

if __name__ == '__main__':
    asyncio.run(run_companies())