import unittest
from datetime import datetime
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange

class calculateMarketCapTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("BTC",pairs=[], seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent1 = (await self.exchange.register_agent("agentcap", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent1, fee=0)

    # @unittest.skip("Run manually to test")
    async def test_calculate_market_cap(self):
        result = await self.exchange.calculate_market_cap("BTC", "USD")
        self.assertEqual(result, 1500000)