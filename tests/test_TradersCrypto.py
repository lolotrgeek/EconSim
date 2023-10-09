# FILEPATH: /c:/Users/Jon/Projects/Finance/EconSim/tests/test_TradersCrypto.py

import unittest
import sys
import os
from decimal import Decimal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.agents.TraderCrypto import CryptoTrader as Trader
from source.agents.TradersCrypto import RandomMarketTaker
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

class TestLowBidder(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.trader_name = "LowBidder"
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester), CryptoCurrencyRequests(self.mock_requester))
        self.aum = 10000
        
        await self.mock_requester.init()
        self.low_bidder = RandomMarketTaker(self.trader_name, self.aum, requests=self.requests)
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
        self.market_maker = RandomMarketTaker(self.trader_name, self.aum, requests=self.requests)
        await self.market_maker.register()

    async def test_init(self):
        self.assertEqual(self.market_maker.name[:16], self.trader_name)
        self.assertEqual(self.market_maker.cash, self.aum)
        self.assertEqual(self.market_maker.initial_cash, self.aum)

    async def test_take_action(self):
        # Test that the market taker buys or sells an asset
        has_traded = await self.market_maker.next()
        self.assertTrue(has_traded)