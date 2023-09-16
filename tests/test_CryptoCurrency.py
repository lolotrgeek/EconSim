import unittest
from datetime import datetime
import pandas as pd
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.crypto.CryptoCurrency import CryptoCurrency
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests as Requests
from .MockRequesterCrypto import MockRequesterCrypto as MockRequester

class CryptoCurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.crypto = CryptoCurrency("BTC", datetime(2022, 1, 1), requester=Requests(MockRequester()))
        
    async def test_init(self):
        self.assertEqual(self.crypto.symbol, "BTC")
        self.assertEqual(self.crypto.blockchain.datetime, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.blockchain.total_transactions, 0)
        self.assertEqual(self.crypto.blockchain.mempool.transactions, [])
        self.assertEqual(self.crypto.supply, 1)
        self.assertEqual(self.crypto.max_supply, 0)
        self.assertEqual(self.crypto.burn_address, '0x0')
        self.assertEqual(self.crypto.startdate, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.currentdate, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.halving_period, 210_000)
        self.assertEqual(self.crypto.last_halving_block, 0)

    async def test_to_dict(self):
        self.assertEqual(self.crypto.to_dict(), {
            "name": "BTC",
            "symbol": "BTC",
            "startdate": datetime(2022, 1, 1),
            "currentdate": datetime(2022, 1, 1),
        })

    async def test_validate_address(self):
        self.assertEqual((await self.crypto.validate_address('0x0')), False)
        self.assertEqual((await self.crypto.validate_address('0x0'*10)), True)
        self.assertEqual((await self.crypto.validate_address('0x0'*40)), False)
        self.assertEqual((await self.crypto.validate_address('0x0'*35)), False)


    async def test_issue_coins(self):
        await self.crypto.issue_coins(pairs = [{'asset': "USD" ,'market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}], amount=1000)
        self.assertEqual(self.crypto.supply, 1001)

    async def test_halving(self):
        self.assertEqual(self.crypto.block_reward, 50)
        self.assertEqual(self.crypto.last_halving_block, 0)
        await self.crypto.halving()
        self.assertEqual(self.crypto.block_reward, 25)
        self.assertEqual(self.crypto.last_halving_block, 1)

    async def test_next(self):
        await self.crypto.next(datetime(2022, 1, 2))
        self.assertEqual(self.crypto.currentdate, datetime(2022, 1, 2))
        self.assertEqual(self.crypto.blockchain.datetime, datetime(2022, 1, 2))
        self.assertEqual(self.crypto.blockchain.total_transactions, 0)
        self.assertEqual(self.crypto.blockchain.mempool.transactions, [])
        self.assertEqual(self.crypto.supply, 1)
        self.assertEqual(self.crypto.max_supply, 0)
        self.assertEqual(self.crypto.burn_address, '0x0')
        self.assertEqual(self.crypto.startdate, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.currentdate, datetime(2022, 1, 2))
        self.assertEqual(self.crypto.halving_period, 210_000)
        self.assertEqual(self.crypto.last_halving_block, 0) 