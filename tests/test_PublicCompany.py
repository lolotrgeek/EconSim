import unittest
import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from datetime import datetime, timedelta
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompany import PublicCompany
from .MockRequester import MockRequester

class TestPublicCompany(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requester= MockRequester()
        self.requests = ExchangeRequests(requester=self.requester)
        self.exchange = self.requester.responder.exchange
        self.agent = (await self.exchange.register_agent("company_agent", 100000))['registered_agent']
        self.shareholder = (await self.exchange.register_agent("shareholder", 100000))['registered_agent']

    def test_initialization(self):
        startdate = datetime(2023, 1, 1)
        company = PublicCompany("TestCompany", startdate, self.requests)

        self.assertEqual(company.name, "TestCompany")
        self.assertEqual(company.symbol, "TES")
        self.assertEqual(company.startdate, startdate)
        self.assertEqual(company.currentdate, startdate)
        self.assertEqual(len(company.quarters), 4)
        self.assertEqual(company.outstanding_shares, 0)
        self.assertEqual(len(company.shareholders), 0)
        self.assertIsNone(company.balance_sheet)
        self.assertIsNone(company.income_statement)
        self.assertIsNone(company.cash_flow)
        self.assertIsNone(company.ex_dividend_date)
        self.assertIsNone(company.dividend_payment_date)
        self.assertEqual(company.dividends_to_distribute, 0)
        self.assertEqual(company.requests, self.requests)

    async def test_generate_financial_report(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)
        date = datetime(2023, 4, 1)
        period = "annual"

        # Call the method being tested
        await company.generate_financial_report(date, period)

        # Assertions
        self.assertEqual(type(company.balance_sheet), dict )
        self.assertEqual(type(company.income_statement), dict )
        self.assertEqual(type(company.cash_flow), dict )

    async def test_quarterly_things(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)
        date = datetime(2023, 4, 1)
        
        async def mocked(date, period): return None
        company.generate_financial_report = mocked

        company.dividends_to_distribute = 1000

        # Call the method being tested
        await company.quarterly_things("Q1")

        # Assertions
        self.assertEqual(company.ex_dividend_date, company.currentdate + timedelta(weeks=2))
        self.assertEqual(company.dividend_payment_date, company.ex_dividend_date + timedelta(weeks=4))

    async def test_issue_initial_shares(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)
        shares = 1000
        price = 50

        await company.issue_initial_shares(shares, price)
        print(self.exchange.assets)
        outstanding_shares = await self.exchange.get_outstanding_shares(company.symbol)
        self.assertEqual(outstanding_shares, 0)
        self.assertIsNotNone(self.exchange.assets[company.symbol])
        self.assertEqual(self.exchange.assets[company.symbol]["type"], "stock")

    async def test_distribute_dividends(self):
        company = PublicCompany("DivTestCompany", datetime(2023, 1, 1), self.requests)

        cash_distributed = {
            "Shareholder1": 0,
            "Shareholder2": 0
        }

        async def mocked_get_outstanding_shares(symbol): return 150
        async def add_cash_mocked(agent, amount, note): cash_distributed[agent] = amount 
            
        self.requests.get_outstanding_shares = mocked_get_outstanding_shares
        self.requests.add_cash = add_cash_mocked

        company.shareholders = [
            {"agent": "Shareholder1", "positions": [{"dt": datetime(2023, 1, 15), "transactions": [{"dt": datetime(2023, 1, 10), "qty": 100}] }] },
            {"agent": "Shareholder2", "positions": [{"dt": datetime(2023, 1, 20), "transactions": [{"dt": datetime(2023, 1, 5), "qty": 50}] }] }
        ]
        eligible_shareholders = [
            {"name": "Shareholder1", "shares": 100},
            {"name": "Shareholder2", "shares": 50}
        ]
        dividends_paid = 500

        await company.distribute_dividends(eligible_shareholders, dividends_paid)

        # Assertions for mock calls and shareholder modifications
        self.assertEqual(cash_distributed["Shareholder1"], 333.3333333333333)
        self.assertEqual(cash_distributed["Shareholder2"], 166.66666666666666)

    async def test_get_eligible_shareholders(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)

        company.shareholders = [
            {"agent": "Shareholder1", "positions": [{"dt": datetime(2023, 1, 10), "transactions": [{"dt": datetime(2023, 1, 11), "qty": 100}] }] },
            {"agent": "Shareholder2", "positions": [{"dt": datetime(2023, 1, 20), "transactions": [{"dt": datetime(2023, 1, 21), "qty": 50}] }] }
        ]
        company.ex_dividend_date = datetime(2023, 1, 12)

        eligible_shareholders = await company.get_eligible_shareholders()

        # Assertions
        self.assertEqual(eligible_shareholders, [
            {"name": "Shareholder1", "shares": 100}
        ])

if __name__ == '__main__':
    asyncio.run(unittest.main())    