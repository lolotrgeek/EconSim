import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.agents.TraderCrypto import CryptoTrader as Trader
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests as ExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from .MockRequesterCrypto import MockRequesterCryptoExchange as MockRequester
1
class TestTrader(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])

    async def test_init(self):
        self.assertEqual(self.trader.name, self.trader_name)
        self.assertEqual(self.trader.cash, self.aum)
        self.assertEqual(self.trader.initial_cash, self.aum)

class RegisterTraderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        self.local_register = await self.trader.register()
        self.remote_register = await self.requests[0].register_agent(self.trader.name, {"USD": self.aum})

    async def test_register_trader(self):
        print(self.local_register)
        self.assertEqual('registered_agent' in self.local_register, True)
        self.assertEqual('registered_agent' in self.remote_register, True)
        self.assertEqual(self.local_register['registered_agent'][:10], self.trader_name)
        self.assertEqual(self.remote_register['registered_agent'][:10], self.trader_name)

class GetLatestTradeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])

    async def test_get_latest_trade(self):
        self.assertEqual(await self.trader.get_latest_trade("BTC","USD"), await self.requests[0].get_latest_trade("BTC", "USD"))

class GetBestBidTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])

    async def test_get_best_bid(self):
        self.assertEqual(await self.trader.get_best_bid("BTC"), await self.requests[0].get_best_bid("BTC"))

class GetBestAskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])

    async def test_get_best_ask(self):
        self.assertEqual(await self.trader.get_best_ask("BTC"), await self.requests[0].get_best_ask("BTC"))

class GetMidpriceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])

    async def test_get_midprice(self):
        self.assertEqual(await self.trader.get_midprice("BTC"), await self.requests[0].get_midprice("BTC"))

class LimitBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_limit_buy(self):
        order = await self.trader.limit_buy("BTC", "USD", 100, 1)
        self.assertEqual(order['creator'], self.trader.name)
        self.assertEqual(order['ticker'], "BTCUSD")
        self.assertEqual(order['price'], '100')
        self.assertEqual(order['qty'], '1')
        self.assertEqual(order['exchange_fee'], '0.001')
        self.assertEqual(order['type'], 'limit_buy')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')

    async def test_limit_buy_insufficient_funds(self):
        self.trader.cash = 0
        order = await self.trader.limit_buy("BTC", "USD", 100000, 1)
        self.assertEqual(order['limit_buy'], 'insufficient_funds')

class LimitSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.requests[0].debug = True

        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        self.trader_registered = (await self.requests[0].register_agent(self.trader.name, {"BTC": 2}))['registered_agent']
        self.trader.name = self.trader_registered

    async def test_limit_sell(self):
        order = await self.trader.limit_sell("BTC", "USD", 100, 1, .01)

        self.assertEqual(order['creator'], self.trader_registered)
        self.assertEqual(order['ticker'], "BTCUSD")
        self.assertEqual(order['price'], '100')
        self.assertEqual(order['qty'], '1')
        self.assertEqual(order['exchange_fee'], '0.200')
        self.assertEqual(order['network_fee'], '0.01')
        self.assertEqual(order['type'], 'limit_sell')
        self.assertEqual(order['dt'], '2023-01-01 00:00:00')
    
    async def test_limit_sell_no_position(self):
        order = await self.trader.limit_sell("BTC", "USD", 100, 3)
        self.assertEqual(order['limit_sell'], 'insufficient_assets')

class CancelOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_cancel_order(self):
        order = await self.trader.limit_buy("BTC", "USD", 100, 1)
        cancelled = await self.trader.cancel_order('BTC', 'USD', order['id'])
        print(cancelled)
        self.assertEqual(type (cancelled['cancelled_order']), dict)
        self.assertEqual(cancelled['cancelled_order']['id'],order['id'] )

class CancelAllOrdersTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_cancel_all_orders(self):
        self.assertEqual(await self.trader.cancel_all_orders("BTC", "USD"), await self.requests[0].cancel_all_orders("BTC", "USD", self.trader.name))

class GetPriceBarsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.aum = 10000
        self.interval = "1min"
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.aum, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    
    async def test_get_price_bars(self):
        await self.trader.limit_buy("BTC", "USD", 100, 1)
        self.assertEqual(await self.trader.get_price_bars("BTCUSD", self.interval, self.limit), await self.requests[0].get_price_bars("BTCUSD", self.interval, self.limit))

class GetOrderBookTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.limit, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()


    async def test_get_order_book(self):
        self.assertEqual(await self.trader.get_order_book("BTCUSD"), await self.requests[0].get_order_book("BTCUSD"))

class GetTradesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.limit, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()


    async def test_get_trades(self):
        self.assertEqual(await self.trader.get_trades("BTC", "USD", self.limit), await self.requests[0].get_trades("BTC", "USD", self.limit))
    
class GetQuotesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        self.limit = 1
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  self.limit, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()


    async def test_get_quotes(self):
        self.assertEqual(await self.trader.get_quotes("BTCUSD"), await self.requests[0].get_quotes("BTCUSD"))

class MarketBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()


    async def test_market_buy(self):
        self.assertEqual(await self.trader.market_buy("BTC", "USD", 1), await self.requests[0].market_buy("BTC", "USD", 1, self.trader.name))

class MarketSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()


    async def test_market_sell(self):
        self.assertEqual(await self.trader.market_sell("BTC", "USD", 1), await self.requests[0].market_sell("BTC", "USD", 1, self.trader.name))

class GetCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        # self.aum = 10000
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name,  exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()


    async def test_get_cash(self):
        self.assertEqual(await self.trader.get_cash(), await self.requests[0].get_cash(self.trader.name))

class GetPositionSimpleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        await self.mock_requester.init()
        self.requests[0].debug = True
        self.trader = Trader(self.trader_name, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_get_position_simple(self):
        position = await self.trader.get_simple_position("USD")
        print(position)
        self.assertIsInstance(position, int)

class GetPositionTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        await self.mock_requester.init()
        self.requests[0].debug = True
        self.trader = Trader(self.trader_name, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_get_position(self):
        position = await self.trader.get_position("USD")
        print(position)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['asset'], "USD")
        self.assertEqual(position['qty'], '10000')
        self.assertEqual(len(position['enters']), 1)
        self.assertEqual(len(position['exits']), 0)

class GetAssetsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_get_assets(self):
        self.assertEqual(await self.trader.get_assets(), await self.requests[0].get_assets(self.trader.name))

class GetMemPool(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_get_mempool(self):
        self.assertEqual(await self.trader.get_mempool("BTC"), await self.requests[1].get_mempool("BTC"))

class GetTransactions(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()
        
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_get_transactions(self):
        self.assertEqual(await self.trader.get_transactions("BTC"), await self.requests[1].get_transactions("BTC"))

class GetTransaction(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.trader_name = "TestTrader"
        self.mock_requester = MockRequester()

        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        
        await self.mock_requester.init()
        self.trader = Trader(self.trader_name, exchange_requests=self.requests[0], crypto_requests=self.requests[1])
        await self.trader.register()

    async def test_get_transaction(self):
        self.assertEqual(await self.trader.get_transaction("BTC", "1"), await self.requests[1].get_transaction("BTC", "1"))
