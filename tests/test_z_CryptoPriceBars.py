import unittest
from datetime import datetime
import sys
import os
import random
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange


class GetPriceBarsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("BTC", pairs=[], seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agent", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10)
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0)})

    async def test_get_minute_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1T")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})     

    async def test_get_5minute_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="5T")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_week_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1W")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )}) 

    async def test_get_month_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1M")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_year_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1Y")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_price_bars_over_time(self):
        day = 1
        while day < 10:
            self.exchange.datetime = datetime(2023, 1, day)
            await self.exchange.limit_buy("BTC", "USD", price=random.randint(100,180), qty=random.randint(1,10), creator=self.agent, fee=0)
            await self.exchange.limit_sell("BTC", "USD", price=random.randint(100,180), qty=random.randint(1,10), creator=self.agent, fee=0)
            day+=1

        get_price_bars = await self.exchange.get_price_bars("BTC", limit=10)
        print(self.exchange.trade_log)
        print(len(get_price_bars), get_price_bars)
        