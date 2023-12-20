import unittest
from datetime import datetime
import pandas as pd
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from decimal import Decimal

from source.crypto.CryptoCurrency import CryptoCurrency
from source.crypto.MemPool import MempoolTransaction

class CryptoCurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.crypto = CryptoCurrency("BTC", datetime(2022, 1, 1))
        
    async def test_init(self):
        self.assertEqual(self.crypto.symbol, "BTC")
        self.assertEqual(self.crypto.blockchain.datetime, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.blockchain.total_transactions, 0)
        self.assertEqual(self.crypto.blockchain.mempool.transactions, [])
        self.assertEqual(self.crypto.supply, 1)
        self.assertEqual(self.crypto.max_supply, 0)
        self.assertEqual(self.crypto.burn_address, '0x00000000000000000000000000')
        self.assertEqual(self.crypto.startdate, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.currentdate, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.halving_period, 210_000)
        self.assertEqual(self.crypto.last_halving_block, 0)

    async def test_to_dict(self):
        self.assertEqual(self.crypto.to_dict(), {
            "name": "BTC",
            "symbol": "BTC",
            "decimals": 8,
            "block_reward": 50,
            "max_supply": 0,
            "burn_address": "0x00000000000000000000000000",
            "halving_period": 210_000,
            "last_halving_block": 0,
            'supply': 1,
            "startdate": datetime(2022, 1, 1,0,0),
            "currentdate": datetime(2022, 1, 1, 0, 0),
        })

    async def test_validate_address(self):
        self.assertEqual((await self.crypto.validate_address('0x0')), False)
        self.assertEqual((await self.crypto.validate_address('0x0'*10)), True)
        self.assertEqual((await self.crypto.validate_address('0x0'*40)), False)
        self.assertEqual((await self.crypto.validate_address('0x0'*35)), False)


    async def test_get_last_fee(self):
        self.crypto.blockchain.chain.append(MempoolTransaction("BTC", Decimal('0.01'), 0, 'sender', 'recipient', datetime(2022, 1, 1))) 
        self.assertEqual(await self.crypto.get_last_fee(), Decimal('0.01'))

    async def test_get_fees(self):
        self.crypto.blockchain.chain.append(MempoolTransaction("BTC", Decimal('0.01'), 0, 'sender', 'recipient', datetime(2022, 1, 1))) 
        self.assertEqual(await self.crypto.get_fees(10), ['1E-8', '0.01'])

    async def test_next(self):
        await self.crypto.next(datetime(2022, 1, 2))
        self.assertEqual(self.crypto.currentdate, datetime(2022, 1, 2))
        self.assertEqual(self.crypto.blockchain.datetime, datetime(2022, 1, 2))
        self.assertEqual(self.crypto.blockchain.total_transactions, 0)
        self.assertEqual(self.crypto.blockchain.mempool.transactions, [])
        self.assertEqual(self.crypto.supply, 1)
        self.assertEqual(self.crypto.max_supply, 0)
        self.assertEqual(self.crypto.burn_address, '0x00000000000000000000000000')
        self.assertEqual(self.crypto.startdate, datetime(2022, 1, 1))
        self.assertEqual(self.crypto.currentdate, datetime(2022, 1, 2))
        self.assertEqual(self.crypto.halving_period, 210_000)
        self.assertEqual(self.crypto.last_halving_block, 0) 