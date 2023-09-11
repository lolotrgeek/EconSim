import unittest
from datetime import datetime
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange


class getAgentsSimpleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.agent1 = (await self.exchange.register_agent("agent19", initial_assets={"USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent20", initial_assets={"USD" : 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent21", initial_assets={"USD" : 10000}))['registered_agent']
        await self.exchange.create_asset("BTC", pairs=[], seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_agents_simple(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee=0)
        await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee=0)
        await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee=0)
        result = await self.exchange.get_agents_simple()
        self.assertCountEqual(result, [{'agent': 'init_seed_BTCUSD', 'assets': {'BTC': 991, "USD": 151363.5}}, {'agent': self.agent1, 'assets': {'BTC': 2, 'USD': 9697.0}}, {'agent': self.agent2, 'assets': {'BTC': 3, "USD": 9545.5}}, {'agent': self.agent3, 'assets': {'BTC': 4, 'USD': 9394.0}}])
