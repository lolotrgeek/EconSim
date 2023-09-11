import unittest
from datetime import datetime
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange

class getAgentsPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("BTC", pairs=[], seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agent19", initial_assets={"USD": 2000000}))['registered_agent']
        self.buy_exit_agent = (await self.exchange.register_agent("buy_exit", initial_assets={"USD": 2000000}))['registered_agent']

    async def test_get_agents_enter_positions(self):
        await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent, fee=0)
        result = await self.exchange.get_agents_positions("BTC", "USD")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]['agent'], self.agent)
        self.assertEqual(result[1]['positions'][0]['base'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['qty'], 1000)
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['quote_flow'], -151500.0)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['base'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['qty'], 1000)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['exits'], [])

    async def test_get_agents_exit_positions(self):
        await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent, fee=0)
        await self.exchange.limit_buy("BTC" , "USD", price=100, qty=1000, creator=self.buy_exit_agent, fee=0)
        sell_result = await self.exchange.market_sell("BTC", "USD", qty=1000, seller=self.agent, fee=0)
        agent_idx = await self.exchange.get_agent_index(self.agent)
        result = await self.exchange.get_agents_positions("BTC", "USD")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]['agent'], self.agent)
        self.assertEqual(result[1]['positions'][0]['base'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['qty'], 0)
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['quote_flow'], -151500.0)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['base'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['qty'], 0)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['exits'][0]['quote_flow'], 148.5)
        self.assertEqual(result[1]['positions'][0]['exits'][1]['quote_flow'], 99900)
        self.assertEqual(result[1]['positions'][0]['exits'][0]['base'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['exits'][0]['qty'], 1)
        self.assertEqual(result[1]['positions'][0]['exits'][1]['qty'], 999)
        self.assertEqual(result[1]['positions'][0]['exits'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['exits'][0]['pnl'], -3.0)
        self.assertEqual(result[1]['positions'][0]['exits'][1]['pnl'], -51448.5)
