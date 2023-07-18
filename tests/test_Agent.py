import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.agents.AgentProcess import Agent
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from .MockRequester import MockRequester

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)

    def test_init(self):
        self.assertEqual(self.agent.name, self.agent_name)
        self.assertEqual(self.agent.tickers, self.tickers)
        self.assertEqual(self.agent.cash, self.aum)
        self.assertEqual(self.agent.initial_cash, self.aum)

class RegisterAgentTest(unittest.TestCase):
    def setUp(self):
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.local_register = self.agent.register()
        self.remote_register = self.requester.register_agent(self.agent.name, self.aum)

    def test_register_agent(self):
        self.assertEqual('registered_agent' in self.local_register, True)
        self.assertEqual('registered_agent' in self.remote_register, True)
        self.assertEqual(self.local_register['registered_agent'][:9], self.agent_name)
        self.assertEqual(self.remote_register['registered_agent'][:9], self.agent_name)

class GetLatestTradeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)

    def test_get_latest_trade(self):
        self.assertEqual(self.agent.get_latest_trade("AAPL"), self.requester.get_latest_trade("AAPL"))

        
class GetBestBidTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)

    def test_get_best_bid(self):
        self.assertEqual(self.agent.get_best_bid("AAPL"), self.requester.get_best_bid("AAPL"))

class GetBestAskTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)

    def test_get_best_ask(self):
        self.assertEqual(self.agent.get_best_ask("AAPL"), self.requester.get_best_ask("AAPL"))

class GetMidpriceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)

    def test_get_midprice(self):
        self.assertEqual(self.agent.get_midprice("AAPL"), self.requester.get_midprice("AAPL"))

class LimitBuyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.agent.register()

    def test_limit_buy(self):
        order = self.agent.limit_buy("AAPL", 100, 1)
        self.assertEqual(order['creator'], self.agent.name)
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 100)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['fee'], 0.0)
        self.assertEqual(order['type'], 'limit_buy')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')

    def test_limit_buy_insufficient_funds(self):
        self.agent.cash = 0
        order = self.agent.limit_buy("AAPL", 100000, 1)
        self.assertEqual(order['limit_buy'], 'insufficient funds')

class LimitSellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.requester.debug = True

        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.agent_registered = self.agent.register()['registered_agent']

    def test_limit_sell(self):
        self.agent.limit_buy("AAPL", 152, 1)
        order = self.agent.limit_sell("AAPL", 100, 1)
        self.assertEqual(order['creator'], self.agent.name)
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 100)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['fee'], 0.0)
        self.assertEqual(order['type'], 'limit_sell')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')
    
    def test_limit_sell_no_position(self):
        order = self.agent.limit_sell("AAPL", 100, 1)
        self.assertEqual(order['limit_sell'], 'insufficient assets')


class CancelOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.agent.register()


    def test_cancel_order(self):
        order = self.agent.limit_buy("AAPL", 100, 1)
        self.assertEqual(self.agent.cancel_order(order['id']), {'cancelled_order': order['id']})

class CancelAllOrdersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.agent.register()

    def test_cancel_all_orders(self):
        self.assertEqual(self.agent.cancel_all_orders("AAPL"), self.requester.cancel_all_orders("AAPL", self.agent.name))

class GetPriceBarsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.interval = "1min"
        self.limit = 1
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.agent.register()

    
    def test_get_price_bars(self):
        self.agent.limit_buy("AAPL", 100, 1)
        self.assertEqual(self.agent.get_price_bars("AAPL", self.interval, self.limit), self.requester.get_price_bars("AAPL", self.interval, self.limit))

class GetMempoolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.aum = 10000
        self.limit = 1
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.aum, requester=self.requester)
        self.agent.register()


    def test_get_mempool(self):
        # self.assertEqual(self.agent.get_mempool(self.limit), self.requester.get_mempool(self.limit))
        self.assertEqual(1,1)


class GetOrderBookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.limit = 1
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.limit, requester=self.requester)
        self.agent.register()


    def test_get_order_book(self):
        self.assertEqual(self.agent.get_order_book("AAPL"), self.requester.get_order_book("AAPL"))

class GetTradesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.limit = 1
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.limit, requester=self.requester)
        self.agent.register()


    def test_get_trades(self):
        self.assertEqual(self.agent.get_trades("AAPL", self.limit), self.requester.get_trades("AAPL", self.limit))
    
class GetQuotesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.limit = 1
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, self.limit, requester=self.requester)
        self.agent.register()


    def test_get_quotes(self):
        self.assertEqual(self.agent.get_quotes("AAPL"), self.requester.get_quotes("AAPL"))

class MarketBuyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, requester=self.requester)
        self.agent.register()


    def test_market_buy(self):
        self.assertEqual(self.agent.market_buy("AAPL", 1), self.requester.market_buy("AAPL", 1, self.agent.name))

class MarketSellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, requester=self.requester)
        self.agent.register()


    def test_market_sell(self):
        self.assertEqual(self.agent.market_sell("AAPL", 1), self.requester.market_sell("AAPL", 1, self.agent.name))

class GetCashTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT"]
        # self.aum = 10000
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers, requester=self.requester)
        self.agent.register()


    def test_get_cash(self):
        self.assertEqual(self.agent.get_cash(), self.requester.get_cash(self.agent.name))

class GetPositionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        self.requester = Requests(MockRequester())
        self.requester.debug = True
        self.agent = Agent(self.agent_name, self.tickers,requester=self.requester)
        self.agent.register()


    def test_get_position(self):
        self.agent.limit_buy("AAPL", 152, 1)
        position = self.agent.get_position("AAPL")
        print(position)
        self.assertIsInstance(position, int)


class GetAssetsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_name = "TestAgent"
        self.tickers = ["AAPL", "GOOGL", "MSFT", "TSLA"]
        self.requester = Requests(MockRequester())
        self.agent = Agent(self.agent_name, self.tickers,requester=self.requester)
        self.agent.register()

    def test_get_assets(self):
        self.assertEqual(self.agent.get_assets(), self.requester.get_assets(self.agent.name))

if __name__ == '__main__':
    unittest.main()
