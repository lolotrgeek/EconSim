import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .runner import Runner
from source.company.PublicCompany import PublicCompany
from source.Messaging import Responder, Requester, Subscriber, Pusher
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps, string_to_time
from typing import Dict
import asyncio
import random
import traceback
from source.Channels import Channels

class CompaniesRunner(Runner):
    def __init__(self):
        self.channels = Channels()
        self.responder = Responder(self.channels.company_channel)
        self.requester = Requester(self.channels.exchange_channel)
        self.names= ['A', 'frXoX', 'wAt', 'Ayc', 'EXCAb', 'Qw', 'vbcY', 'ZM', 'j', 'nNLga', 'Ln', 'ao', 'k', 'icyJ', 'r', 'qk', 'BeHN', 'if', 'yAnL', 'sw']
        self.time = string_to_time('1700-01-01')
        self.companies: Dict[str, PublicCompany] = {}

    def generate_companies(self, requests, time) -> None:
        for name in self.names:
            company = PublicCompany(name, time, requests)
            self.companies[company.symbol] = company

    async def callback(self, msg):
        if msg['topic'] == 'get_date': return dumps(self.time)
        elif msg['topic'] == 'get_companies': return dumps([company.symbol for company in self.companies.values()])
        elif "company" in msg:
            if msg['company'] in self.companies:
                if msg['topic'] == 'get_company': return dumps(self.companies[msg['company']].to_dict())
                elif msg['topic'] == 'get_income_statement': return dumps(self.companies[msg['company']].income_statement)
                elif msg['topic'] == 'get_balance_sheet': return dumps(self.companies[msg['company']].balance_sheet)
                elif msg['topic'] == 'get_cash_flow': return dumps(self.companies[msg['company']].cash_flow)
                elif msg['topic'] == 'get_dividend_payment_date': return dumps(self.companies[msg['company']].dividend_payment_date)
                elif msg['topic'] == 'get_ex_dividend_date': return dumps(self.companies[msg['company']].ex_dividend_date)
                elif msg['topic'] == 'get_dividends_to_distribute': return dumps(self.companies[msg['company']].dividends_to_distribute)
            else: return dumps({"warning": f'unknown company {msg["company"]}'})

        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})

    async def run_companies(self) -> None:
        try:
            await self.responder.connect()
            await self.requester.connect()

            time = await self.get_time()
            self.generate_companies(Requests(self.requester), time)

            for company in self.companies.values():
                await company.issue_initial_shares(random.randint(500,10000), random.randint(1,150))
                await company.initial_operate_and_report()

            while True:
                time = await self.get_time()
                for company in self.companies.values():
                    company.currentdate = time
                    await company.next(time)
                msg = await self.responder.lazy_respond(self.callback)
                if msg == None:
                    continue

        except Exception as e:
            print(e)
            print(traceback.format_exc())

if __name__ == '__main__':
    runner = CompaniesRunner()
    asyncio.run(runner.run_companies())