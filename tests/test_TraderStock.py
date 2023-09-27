import unittest
import sys
import os
parent_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.agents.TraderStock import StockTrader as Trader
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompanyRequests import PublicCompanyRequests
from .MockRequester import MockRequester
import asyncio

class GetIncomeStatement(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name="TestTrader"
        self.mock_requester=MockRequester()
        self.exchange_requests=ExchangeRequests(self.mock_requester)
        self.public_company_requests=PublicCompanyRequests(self.mock_requester)
        self.tickers=["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader=Trader(self.trader_name, exchange_requests=self.exchange_requests, public_company_requests=self.public_company_requests)
        await self.trader.register()

    async def test_get_income_statement(self):
        self.assertEqual(await self.trader.get_income_statement("AAPL"), await self.public_company_requests.get_income_statement("AAPL"))

class GetBalanceSheet(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name="TestTrader"
        self.mock_requester=MockRequester()
        self.exchange_requests=ExchangeRequests(self.mock_requester)
        self.public_company_requests=PublicCompanyRequests(self.mock_requester)
        self.tickers=["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader=Trader(self.trader_name, exchange_requests=self.exchange_requests, public_company_requests=self.public_company_requests)
        await self.trader.register()

    async def test_get_balance_sheet(self):
        self.assertEqual(await self.trader.get_balance_sheet("AAPL"), await self.public_company_requests.get_balance_sheet("AAPL"))

class GetCashFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name="TestTrader"
        self.mock_requester=MockRequester()
        self.exchange_requests=ExchangeRequests(self.mock_requester)
        self.public_company_requests=PublicCompanyRequests(self.mock_requester)
        self.tickers=["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader=Trader(self.trader_name, exchange_requests=self.exchange_requests, public_company_requests=self.public_company_requests)
        await self.trader.register()

    async def test_get_cash_flow(self):
        self.assertEqual(await self.trader.get_cash_flow("AAPL"), await self.public_company_requests.get_cash_flow("AAPL"))

class GetDividendPaymentDate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name="TestTrader"
        self.mock_requester=MockRequester()
        self.exchange_requests=ExchangeRequests(self.mock_requester)
        self.public_company_requests=PublicCompanyRequests(self.mock_requester)
        self.tickers=["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader=Trader(self.trader_name, exchange_requests=self.exchange_requests, public_company_requests=self.public_company_requests)
        await self.trader.register()

    async def test_get_dividend_payment_date(self):
        self.assertEqual(await self.trader.get_dividend_payment_date("AAPL"), await self.public_company_requests.get_dividend_payment_date("AAPL"))

class getExDividendDate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name="TestTrader"
        self.mock_requester=MockRequester()
        self.exchange_requests=ExchangeRequests(self.mock_requester)
        self.public_company_requests=PublicCompanyRequests(self.mock_requester)
        self.tickers=["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader=Trader(self.trader_name, exchange_requests=self.exchange_requests, public_company_requests=self.public_company_requests)
        await self.trader.register()

    async def test_get_ex_dividend_date(self):
        self.assertEqual(await self.trader.get_ex_dividend_date("AAPL"), await self.public_company_requests.get_ex_dividend_date("AAPL"))

class GetDividendsToDistribute(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name="TestTrader"
        self.mock_requester=MockRequester()
        self.exchange_requests=ExchangeRequests(self.mock_requester)
        self.public_company_requests=PublicCompanyRequests(self.mock_requester)
        self.tickers=["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader=Trader(self.trader_name, exchange_requests=self.exchange_requests, public_company_requests=self.public_company_requests)
        await self.trader.register()

    async def test_get_dividends_to_distribute(self):
        self.assertEqual(await self.trader.get_dividends_to_distribute("AAPL"), await self.public_company_requests.get_dividends_to_distribute("AAPL"))

if __name__ == '__main__':
    asyncio.run(unittest.main())
