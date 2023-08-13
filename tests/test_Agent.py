import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.agents.Agent import Agent
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from .MockRequester import MockRequester
import asyncio

class TestAgent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agent_name = "TestAgent"
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name, self.aum, requester=self.requester)

    async def test_init(self):
        self.assertEqual(self.agent.name, self.agent_name)
        self.assertEqual(self.agent.cash, self.aum)
        self.assertEqual(self.agent.initial_cash, self.aum)

class RegisterAgentTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        self.local_register = await self.agent.register()
        self.remote_register = await self.requester.register_agent(self.agent.name, self.aum)

    async def test_register_agent(self):
        self.assertEqual('registered_agent' in self.local_register, True)
        self.assertEqual('registered_agent' in self.remote_register, True)
        self.assertEqual(self.local_register['registered_agent'][:9], self.agent_name)
        self.assertEqual(self.remote_register['registered_agent'][:9], self.agent_name)

class GetLatestTradeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)

    async def test_get_latest_trade(self):
        self.assertEqual(await self.agent.get_latest_trade("AAPL"), await self.requester.get_latest_trade("AAPL"))

        
class GetBestBidTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)

    async def test_get_best_bid(self):
        self.assertEqual(await self.agent.get_best_bid("AAPL"), await self.requester.get_best_bid("AAPL"))

class GetBestAskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)

    async def test_get_best_ask(self):
        self.assertEqual(await self.agent.get_best_ask("AAPL"), await self.requester.get_best_ask("AAPL"))

class GetMidpriceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)

    async def test_get_midprice(self):
        self.assertEqual(await self.agent.get_midprice("AAPL"), await self.requester.get_midprice("AAPL"))

class LimitBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        await self.agent.register()

    async def test_limit_buy(self):
        order = await self.agent.limit_buy("AAPL", 100, 1)
        self.assertEqual(order['creator'], self.agent.name)
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 100)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['fee'], 0.0)
        self.assertEqual(order['type'], 'limit_buy')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')

    async def test_limit_buy_insufficient_funds(self):
        self.agent.cash = 0
        order = await self.agent.limit_buy("AAPL", 100000, 1)
        self.assertEqual(order['limit_buy'], 'insufficient funds')

class LimitSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.requester.debug = True

        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        self.agent_registered = (await self.agent.register())['registered_agent']

    async def test_limit_sell(self):
        await self.agent.limit_buy("AAPL", 152, 1)
        order = await self.agent.limit_sell("AAPL", 100, 1)
        print(order)
        self.assertEqual(order['creator'], self.agent.name)
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 100)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['fee'], 0.0)
        self.assertEqual(order['type'], 'limit_sell')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')
    
    async def test_limit_sell_no_position(self):
        order = await self.agent.limit_sell("AAPL", 100, 1)
        self.assertEqual(order['limit_sell'], 'insufficient assets')


class CancelOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        await self.agent.register()

    async def test_cancel_order(self):
        order = await self.agent.limit_buy("AAPL", 100, 1)
        cancelled = await self.agent.cancel_order(order['id'])
        self.assertEqual(cancelled, {'cancelled_order': order['id']})

class CancelAllOrdersTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        await self.agent.register()

    async def test_cancel_all_orders(self):
        self.assertEqual(await self.agent.cancel_all_orders("AAPL"), await self.requester.cancel_all_orders("AAPL", self.agent.name))

class GetPriceBarsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.interval = "1min"
        self.limit = 1
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        await self.agent.register()

    
    async def test_get_price_bars(self):
        await self.agent.limit_buy("AAPL", 100, 1)
        self.assertEqual(await self.agent.get_price_bars("AAPL", self.interval, self.limit), await self.requester.get_price_bars("AAPL", self.interval, self.limit))

class GetMempoolTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.aum = 10000
        self.limit = 1
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.aum, requester=self.requester)
        await self.agent.register()


    async def test_get_mempool(self):
        # self.assertEqual(self.agent.get_mempool(self.limit), self.requester.get_mempool(self.limit))
        self.assertEqual(1,1)


class GetOrderBookTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.limit = 1
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.limit, requester=self.requester)
        await self.agent.register()


    async def test_get_order_book(self):
        self.assertEqual(await self.agent.get_order_book("AAPL"), await self.requester.get_order_book("AAPL"))

class GetTradesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.limit = 1
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.limit, requester=self.requester)
        await self.agent.register()


    async def test_get_trades(self):
        self.assertEqual(await self.agent.get_trades("AAPL", self.limit), await self.requester.get_trades("AAPL", self.limit))
    
class GetQuotesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.limit = 1
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  self.limit, requester=self.requester)
        await self.agent.register()


    async def test_get_quotes(self):
        self.assertEqual(await self.agent.get_quotes("AAPL"), await self.requester.get_quotes("AAPL"))

class MarketBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  requester=self.requester)
        await self.agent.register()


    async def test_market_buy(self):
        self.assertEqual(await self.agent.market_buy("AAPL", 1), await self.requester.market_buy("AAPL", 1, self.agent.name))

class MarketSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  requester=self.requester)
        await self.agent.register()


    async def test_market_sell(self):
        self.assertEqual(await self.agent.market_sell("AAPL", 1), await self.requester.market_sell("AAPL", 1, self.agent.name))

class GetCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        
        # self.aum = 10000
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name,  requester=self.requester)
        await self.agent.register()


    async def test_get_cash(self):
        self.assertEqual(await self.agent.get_cash(), await self.requester.get_cash(self.agent.name))

class GetPositionTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.requester.debug = True
        self.agent = Agent(self.agent_name, requester=self.requester)
        await self.agent.register()

    async def test_get_position(self):
        await self.agent.limit_buy("AAPL", 152, 1)
        position = await self.agent.get_position("AAPL")
        print(position)
        self.assertIsInstance(position, int)


class GetAssetsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requester = Requests(self.mock_requester)
        self.agent = Agent(self.agent_name, requester=self.requester)
        await self.agent.register()

    async def test_get_assets(self):
        self.assertEqual(await self.agent.get_assets(), await self.requester.get_assets(self.agent.name))

if __name__ == '__main__':
    asyncio.run(unittest.main())
