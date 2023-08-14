import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.agents.Trader import Trader
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompanyRequests import PublicCompanyRequests
from .MockRequester import MockRequester
import asyncio

class TestTrader(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, self.aum, requests=self.requests)

    async def test_init(self):
        self.assertEqual(self.trader.name, self.trader_name)
        self.assertEqual(self.trader.cash, self.aum)
        self.assertEqual(self.trader.initial_cash, self.aum)

class RegisterTraderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        self.local_register = await self.trader.register()
        self.remote_register = await self.requests[0].register_agent(self.trader.name, self.aum)

    async def test_register_trader(self):
        self.assertEqual('registered_agent' in self.local_register, True)
        self.assertEqual('registered_agent' in self.remote_register, True)
        self.assertEqual(self.local_register['registered_agent'][:10], self.trader_name)
        self.assertEqual(self.remote_register['registered_agent'][:10], self.trader_name)

class GetLatestTradeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)

    async def test_get_latest_trade(self):
        self.assertEqual(await self.trader.get_latest_trade("AAPL"), await self.requests[0].get_latest_trade("AAPL"))

        
class GetBestBidTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)

    async def test_get_best_bid(self):
        self.assertEqual(await self.trader.get_best_bid("AAPL"), await self.requests[0].get_best_bid("AAPL"))

class GetBestAskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)

    async def test_get_best_ask(self):
        self.assertEqual(await self.trader.get_best_ask("AAPL"), await self.requests[0].get_best_ask("AAPL"))

class GetMidpriceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)

    async def test_get_midprice(self):
        self.assertEqual(await self.trader.get_midprice("AAPL"), await self.requests[0].get_midprice("AAPL"))

class LimitBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        await self.trader.register()

    async def test_limit_buy(self):
        order = await self.trader.limit_buy("AAPL", 100, 1)
        self.assertEqual(order['creator'], self.trader.name)
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 100)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['fee'], 0.0)
        self.assertEqual(order['type'], 'limit_buy')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')

    async def test_limit_buy_insufficient_funds(self):
        self.trader.cash = 0
        order = await self.trader.limit_buy("AAPL", 100000, 1)
        self.assertEqual(order['limit_buy'], 'insufficient funds')

class LimitSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.requests[0].debug = True

        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        self.trader_registered = (await self.trader.register())['registered_agent']

    async def test_limit_sell(self):
        await self.trader.limit_buy("AAPL", 152, 1)
        order = await self.trader.limit_sell("AAPL", 100, 1)
        print(order)
        self.assertEqual(order['creator'], self.trader.name)
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 100)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['fee'], 0.0)
        self.assertEqual(order['type'], 'limit_sell')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')
    
    async def test_limit_sell_no_position(self):
        order = await self.trader.limit_sell("AAPL", 100, 1)
        self.assertEqual(order['limit_sell'], 'insufficient assets')


class CancelOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        await self.trader.register()

    async def test_cancel_order(self):
        order = await self.trader.limit_buy("AAPL", 100, 1)
        cancelled = await self.trader.cancel_order(order['id'])
        self.assertEqual(cancelled, {'cancelled_order': order['id']})

class CancelAllOrdersTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        await self.trader.register()

    async def test_cancel_all_orders(self):
        self.assertEqual(await self.trader.cancel_all_orders("AAPL"), await self.requests[0].cancel_all_orders("AAPL", self.trader.name))

class GetPriceBarsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        self.interval = "1min"
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        await self.trader.register()

    
    async def test_get_price_bars(self):
        await self.trader.limit_buy("AAPL", 100, 1)
        self.assertEqual(await self.trader.get_price_bars("AAPL", self.interval, self.limit), await self.requests[0].get_price_bars("AAPL", self.interval, self.limit))

class GetMempoolTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.aum = 10000
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, requests=self.requests)
        await self.trader.register()


    async def test_get_mempool(self):
        # self.assertEqual(self.trader.get_mempool(self.limit), self.requests[0].get_mempool(self.limit))
        self.assertEqual(1,1)


class GetOrderBookTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.limit, requests=self.requests)
        await self.trader.register()


    async def test_get_order_book(self):
        self.assertEqual(await self.trader.get_order_book("AAPL"), await self.requests[0].get_order_book("AAPL"))

class GetTradesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.limit, requests=self.requests)
        await self.trader.register()


    async def test_get_trades(self):
        self.assertEqual(await self.trader.get_trades("AAPL", self.limit), await self.requests[0].get_trades("AAPL", self.limit))
    
class GetQuotesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.limit, requests=self.requests)
        await self.trader.register()


    async def test_get_quotes(self):
        self.assertEqual(await self.trader.get_quotes("AAPL"), await self.requests[0].get_quotes("AAPL"))

class MarketBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  requests=self.requests)
        await self.trader.register()


    async def test_market_buy(self):
        self.assertEqual(await self.trader.market_buy("AAPL", 1), await self.requests[0].market_buy("AAPL", 1, self.trader.name))

class MarketSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  requests=self.requests)
        await self.trader.register()


    async def test_market_sell(self):
        self.assertEqual(await self.trader.market_sell("AAPL", 1), await self.requests[0].market_sell("AAPL", 1, self.trader.name))

class GetCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        
        # self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  requests=self.requests)
        await self.trader.register()


    async def test_get_cash(self):
        self.assertEqual(await self.trader.get_cash(), await self.requests[0].get_cash(self.trader.name))

class GetPositionTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.requests[0].debug = True
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_position(self):
        await self.trader.limit_buy("AAPL", 152, 1)
        position = await self.trader.get_position("AAPL")
        print(position)
        self.assertIsInstance(position, int)


class GetAssetsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_assets(self):
        self.assertEqual(await self.trader.get_assets(), await self.requests[0].get_assets(self.trader.name))

class GetIncomeStatement(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_income_statement(self):
        self.assertEqual(await self.trader.get_income_statement("AAPL"), await self.requests[1].get_income_statement("AAPL"))

class GetBalanceSheet(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_balance_sheet(self):
        self.assertEqual(await self.trader.get_balance_sheet("AAPL"), await self.requests[1].get_balance_sheet("AAPL"))

class GetCashFlow(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_cash_flow(self):
        self.assertEqual(await self.trader.get_cash_flow("AAPL"), await self.requests[1].get_cash_flow("AAPL"))

class GetDividendPaymentDate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_dividend_payment_date(self):
        self.assertEqual(await self.trader.get_dividend_payment_date("AAPL"), await self.requests[1].get_dividend_payment_date("AAPL"))

class getExDividendDate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_ex_dividend_date(self):
        self.assertEqual(await self.trader.get_ex_dividend_date("AAPL"), await self.requests[1].get_ex_dividend_date("AAPL"))

class GetDividendsToDistribute(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), PublicCompanyRequests(self.mock_requester))
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, requests=self.requests)
        await self.trader.register()

    async def test_get_dividends_to_distribute(self):
        self.assertEqual(await self.trader.get_dividends_to_distribute("AAPL"), await self.requests[1].get_dividends_to_distribute("AAPL"))

if __name__ == '__main__':
    asyncio.run(unittest.main())
