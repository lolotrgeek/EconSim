import unittest
from datetime import datetime
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange

class getSharesOutstandingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("BTC", pairs=[], seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agentoutstand", initial_assets={"USD": 200000}))['registered_agent']
        await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent, fee=0)

    async def test_get_outstanding_shares(self):
        result = await self.exchange.get_outstanding_shares("BTC")
        self.assertEqual(result, 1000)