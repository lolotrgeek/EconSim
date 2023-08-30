import unittest,asyncio,sys,os,pprint
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from datetime import datetime, timedelta
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompany import PublicCompany
from source.company.operations import Operations
from .MockRequester import MockRequester

class TestPublicCompany(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requester= MockRequester()
        self.requests = ExchangeRequests(requester=self.requester)
        self.exchange = self.requester.responder.exchange

    def test_initialization(self):
        startdate = datetime(2023, 1, 1)
        company = PublicCompany("TestCompany", startdate, self.requests)

        self.assertEqual(company.name, "TestCompany")
        self.assertEqual(company.symbol, "TES")
        self.assertEqual(company.startdate, startdate)
        self.assertEqual(company.currentdate, startdate)
        self.assertEqual(company.quarter_length, 13)
        self.assertEqual(company.next_quarter, {"period": "Q1", "date": startdate + timedelta(weeks=13)})
        self.assertEqual(len(company.shares_issued), 0)
        self.assertEqual(len(company.shareholders), 0)
        self.assertEqual(type(company.market_cap), str)
        self.assertIsInstance(company.operations, Operations)
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

    async def test_value_shares(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)
        
        company.shares_issued = [{"shares": 1000, "price": 100, "value": 100000, "date": datetime(2023, 1, 1)}]

        async def mock_midprice(ticker): return 50
        self.exchange.get_midprice = mock_midprice
        async def mock_outstanding_shares(ticker): return 1000
        self.exchange.get_outstanding_shares = mock_outstanding_shares

        outstanding_shares_value, shares_issued_value = await company.value_of_shares("Q1")
        self.assertEqual(outstanding_shares_value, 50000)
        self.assertEqual(shares_issued_value, 100000)
        
        #test annual value
        company.shares_issued.append({"shares": 1000, "price": 100, "value": 100000, "date": datetime(2024, 1, 1)})
        company.currentdate = datetime(2024, 12, 31)
        outstanding_shares_value_annual, shares_issued_value_annual = await company.value_of_shares("annual")
        self.assertEqual(outstanding_shares_value_annual, 50000)
        self.assertEqual(shares_issued_value_annual, 100000)        

    async def test_operate_and_report(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)
        date = datetime(2023, 4, 1)
        
        
        company.shares_issued = [{"shares": 1000, "price": 100,"value": 100000, "date": datetime(2023, 1, 1)}]

        async def mock_midprice(ticker): return 50
        self.exchange.get_midprice = mock_midprice
        async def mock_outstanding_shares(ticker): return 1000
        self.exchange.get_outstanding_shares = mock_outstanding_shares

        async def mocked(date, period): return None
        company.generate_financial_report = mocked

        company.dividends_to_distribute = 1000

        # Call the method being tested
        await company.operate_and_report("Q1")

        # Assertions
        self.assertEqual(company.ex_dividend_date, company.currentdate + timedelta(weeks=2))
        self.assertEqual(company.dividend_payment_date, company.ex_dividend_date + timedelta(weeks=4))

    async def test_issue_initial_shares(self):
        company = PublicCompany("TestCompany", datetime(2023, 1, 1), self.requests)
        shares = 1000
        price = 50

        await company.issue_initial_shares(shares, price)
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
        company = PublicCompany("EligibleCompany", datetime(2023, 1, 1), self.requests)
        await company.issue_initial_shares(10, 5)
        self.sold_before_agent = (await self.exchange.register_agent("soldbefore", 100000))['registered_agent']
        self.bought_after_agent = (await self.exchange.register_agent("boughtafter", 100000))['registered_agent']
        self.bought_before_agent = (await self.exchange.register_agent("boughtbefore", 100000))['registered_agent']
        self.exchange.datetime = datetime(2023, 1, 2)
        await self.exchange.market_buy(company.symbol,qty=10, buyer=self.sold_before_agent)
        sells = await self.exchange.limit_sell(ticker=company.symbol, qty=10, price=1, creator=self.sold_before_agent)
        buys = await self.exchange.limit_buy(company.symbol,qty=10,price=2, creator=self.bought_before_agent)

        print(sells.to_dict())
        # print(buys.to_dict())
        self.exchange.datetime = datetime(2024, 1, 1) 
        await self.exchange.market_buy(company.symbol,qty=10, buyer=self.bought_after_agent)


        company.shareholders = await self.exchange.get_agents_positions(company.symbol)
        pp = pprint.PrettyPrinter(indent=1)
        pp.pprint(company.shareholders)

        company.ex_dividend_date = datetime(2023, 1, 12)
        
        eligible_shareholders = await company.get_eligible_shareholders()


        print(eligible_shareholders)
        # Assertions
        self.assertEqual(eligible_shareholders, [
            {"name": self.bought_before_agent, "shares": 9}
        ])

if __name__ == '__main__':
    asyncio.run(unittest.main())    