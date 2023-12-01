# FILEPATH: /c:/Users/Jon/Projects/Finance/EconSim/tests/test_TradersCrypto.py

import unittest
import sys
import os
from decimal import Decimal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.utils._utils import prec
from source.utils.logger import Logger
from source.agents.TraderCrypto import CryptoTrader as Trader
from source.agents.TradersCrypto import RandomMarketTaker, NaiveMarketMaker, SimpleMarketTaker, LowBidder
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests as ExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from .MockRequesterCrypto import MockRequesterCryptoExchange as MockRequester

class TestRandomMarketTaker(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "RandomMarketTaker"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.random_taker = RandomMarketTaker(self.trader_name, self.aum, requests=self.requests)
        await self.random_taker.register()

    async def test_init(self):
        self.assertEqual(self.random_taker.name[:17], self.trader_name)
        self.assertEqual(self.random_taker.cash, self.aum)
        self.assertEqual(self.random_taker.initial_cash, self.aum)

    async def test_take_action(self):
        # Test that the market taker buys or sells an asset
        has_traded = await self.random_taker.next()
        self.assertTrue(has_traded)

class TestSimpleMarketTaker(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "SimpleMarketTaker"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.simple_taker = SimpleMarketTaker(self.trader_name, self.aum, requests=self.requests)
        await self.simple_taker.register()

    async def test_init(self):
        self.assertEqual(self.simple_taker.name[:17], self.trader_name)
        self.assertEqual(self.simple_taker.cash, self.aum)
        self.assertEqual(self.simple_taker.initial_cash, self.aum)

    async def test_spend_cash(self):
        # Test that the market taker buys or sells an asset
        self.simple_taker.tickers = await self.simple_taker.get_tickers()
        self.simple_taker.assets = (await self.simple_taker.get_assets())['assets']
        self.simple_taker.cash = self.simple_taker.assets['USD']
        cash_before = self.simple_taker.cash    
        await self.simple_taker.spend_cash()
        
        self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        txn = self.mock_requester.responder.exchange.pending_transactions[0]
        base_txn = self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].to_dict()
        quote_txn = self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].to_dict()
        await self.mock_requester.responder.exchange._complete_trade(txn, base_txn, quote_txn)

        assets = (await self.simple_taker.get_assets())['assets']
        self.assertTrue(cash_before > self.simple_taker.assets['USD'])
        self.assertTrue('BTC' in assets)

    async def test_dump_assets(self):
        # Test that the market taker buys or sells an asset
        self.simple_taker.tickers = await self.simple_taker.get_tickers()
        self.simple_taker.assets = (await self.simple_taker.get_assets())['assets']
        self.simple_taker.cash = self.simple_taker.assets['USD']
        await self.simple_taker.spend_cash()
        
        self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        txn = self.mock_requester.responder.exchange.pending_transactions[0]
        base_txn = self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].to_dict()
        quote_txn = self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].to_dict()
        await self.mock_requester.responder.exchange.next()

        assets_before = self.simple_taker.assets['BTC']

        buy = await self.mock_requester.responder.exchange.limit_buy("BTC", "USD", price=151, qty=500, fee='0.0001', creator=self.mock_requester.responder.agent)
             
        
        print(self.mock_requester.responder.exchange.books['BTCUSD'].bids)
        await self.simple_taker.dump_assets()

        self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        # txn = self.mock_requester.responder.exchange.pending_transactions[0]
        # base_txn = self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].to_dict()
        # quote_txn = self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].to_dict()
        # await self.mock_requester.responder.exchange._complete_trade(txn, base_txn, quote_txn)
        await self.mock_requester.responder.exchange.next()
        print(self.mock_requester.responder.exchange.books['BTCUSD'].bids)

        assets = (await self.simple_taker.get_assets())['assets']
        self.assertEqual(assets_before > assets['BTC'], True)
        

    async def test_take_action(self):
        # Test that the market taker buys or sells an asset
        has_traded = await self.simple_taker.next()
        self.assertTrue(has_traded)

class TestLowBidder(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "LowBidder"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.low_bidder = LowBidder(self.trader_name, self.aum, requests=self.requests)
        await self.low_bidder.register()

    async def test_init(self):
        self.assertEqual(self.low_bidder.name[:9], self.trader_name)
        self.assertEqual(self.low_bidder.cash, self.aum)
        self.assertEqual(self.low_bidder.initial_cash, self.aum)

    async def test_take_action(self):
        # Test that the market taker buys or sells an asset
        has_traded = await self.low_bidder.next()
        self.assertTrue(has_traded)

class TestNaiveMarketMaker(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "NaiveMarketMaker"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.market_maker = NaiveMarketMaker(self.trader_name, self.aum, requests=self.requests)
        self.market_maker.logger = Logger('NaiveMarketMaker', debug_print=True, level=10)
        await self.market_maker.register()

    async def complete_trade(self):
        print(self.mock_requester.responder.exchange.books['BTCUSD'].bids)
        print(self.mock_requester.responder.exchange.books['BTCUSD'].asks)
        self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        txn = self.mock_requester.responder.exchange.pending_transactions[0]
        base_txn = self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].to_dict()
        quote_txn = self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].to_dict()
        await self.mock_requester.responder.exchange._complete_trade(txn, base_txn, quote_txn)        

    async def test_init(self):
        self.assertEqual(self.market_maker.name[:16], self.trader_name)
        self.assertEqual(self.market_maker.cash, self.aum)
        self.assertEqual(self.market_maker.initial_cash, self.aum)


    async def test_set_tradable_cash(self):
        # Test that the market maker sets tradable cash
        await self.market_maker.set_tradable_cash()
        self.assertEqual(self.market_maker.cash_to_trade, self.market_maker.aum -self.market_maker.fee_reserve)

    async def test_acquire_assets(self):
        # Test that the market maker buys an asset
        self.market_maker.tickers = await self.market_maker.get_tickers()
        await self.market_maker.set_tradable_cash()
        ticker = self.market_maker.tickers[0]['base']+self.market_maker.tickers[0]['quote']
        
        acquired = await self.market_maker.acquire_assets(self.market_maker.tickers[0])
        await self.complete_trade()

        get_assets = await self.market_maker.get_assets()
        self.market_maker.assets = get_assets['assets']
        print(get_assets)
        self.assertTrue(acquired)
        self.assertTrue(self.market_maker.tickers[0]['base'] in self.market_maker.assets)

    async def test_acquire_assets_no_asks(self):
        # Test that the market maker buys an asset
        self.market_maker.tickers = await self.market_maker.get_tickers()
        await self.market_maker.set_tradable_cash()
        ticker = self.market_maker.tickers[0]['base']+self.market_maker.tickers[0]['quote']
        self.mock_requester.responder.exchange.books['BTCUSD'].asks = []
        acquired = await self.market_maker.acquire_assets(self.market_maker.tickers[0])

        get_assets = await self.market_maker.get_assets()
        self.market_maker.assets = get_assets['assets']
        print(get_assets)
        self.assertTrue(acquired)
        self.assertTrue(self.market_maker.tickers[0]['base'] not in self.market_maker.assets)        

    async def test_market_make(self):
        # Test that the market maker buys an asset
        await self.market_maker.next()
        self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        txn = self.mock_requester.responder.exchange.pending_transactions[0]
        base_txn = self.mock_requester.responder.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].to_dict()
        quote_txn = self.mock_requester.responder.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].to_dict()
        await self.mock_requester.responder.exchange._complete_trade(txn, base_txn, quote_txn)

        get_assets = await self.market_maker.get_assets()
        order_qty = prec(str(self.market_maker.assets['BTC'] * self.market_maker.qty_pct_per_order), 8)

        latest_trade = await self.market_maker.get_latest_trade(self.market_maker.tickers[0]['base'], self.market_maker.tickers[0]['quote'])
        await self.market_maker.make_market(self.market_maker.tickers[0], latest_trade['price'])

        print(self.mock_requester.responder.exchange.books['BTCUSD'].bids)
        print(self.mock_requester.responder.exchange.books['BTCUSD'].asks)

        self.market_maker.assets = get_assets['assets']
        print(get_assets)
        self.assertTrue(self.market_maker.tickers[0]['base'] in self.market_maker.assets)
        self.assertEqual(len(self.mock_requester.responder.exchange.books['BTCUSD'].bids), 3)
        self.assertEqual(len(self.mock_requester.responder.exchange.books['BTCUSD'].asks), 2)
        self.assertEqual(self.mock_requester.responder.exchange.books['BTCUSD'].bids[0].creator, self.market_maker.name)
        self.assertEqual(self.mock_requester.responder.exchange.books['BTCUSD'].asks[1].creator, self.market_maker.name)
        
        self.assertEqual(self.mock_requester.responder.exchange.books['BTCUSD'].asks[1].qty, order_qty)

        self.assertEqual(self.mock_requester.responder.exchange.books['BTCUSD'].bids[0].qty, order_qty)
        self.assertEqual(self.mock_requester.responder.exchange.books['BTCUSD'].bids[0].price, prec(latest_trade['price'] * self.market_maker.buy_spread, 2))
        self.assertEqual(self.mock_requester.responder.exchange.books['BTCUSD'].asks[1].price, prec(latest_trade['price'] * self.market_maker.sell_spread, 2))

    async def test_take_action(self):
        # Test that the market taker buys or sells an asset
        has_traded = await self.market_maker.next()
        self.assertTrue(has_traded)
        self.assertEqual(len(self.market_maker.tickers), 1)
        self.assertTrue( 'USD' in self.market_maker.assets)

