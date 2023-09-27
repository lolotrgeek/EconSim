import unittest
from datetime import datetime
import pandas as pd
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.crypto.MemPool import MempoolTransaction, MemPool

class MemPoolTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mem_pool = MemPool()

    async def test_get_pending_transactions_empty(self):
        pending_transactions = await self.mem_pool.get_pending_transactions()
        self.assertEqual(len(pending_transactions), 0)

    async def test_get_confirmed_transactions_empty(self):
        confirmed_transactions = await self.mem_pool.get_confirmed_transactions()
        self.assertEqual(len(confirmed_transactions), 0)

    async def test_transaction_log_empty(self):
        transaction_log = self.mem_pool.transactions
        self.assertEqual(len(transaction_log), 0)

    async def test_get_pending_transactions(self):
        transaction1 = MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1')
        transaction2 = MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        transaction3 = MempoolTransaction('BTC', 0.003, 3.0, 'sender3', 'recipient3')
        self.mem_pool.transactions = [transaction1, transaction2, transaction3]

        pending_transactions = await self.mem_pool.get_pending_transactions()
        self.assertEqual(len(pending_transactions), 3)
        self.assertIn(transaction1, pending_transactions)
        self.assertIn(transaction2, pending_transactions)
        self.assertIn(transaction3, pending_transactions)

    async def test_get_confirmed_transactions(self):
        transaction1 = MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1')
        transaction2 = MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        transaction3 = MempoolTransaction('BTC', 0.003, 3.0, 'sender3', 'recipient3')
        transaction1.confirmed = True
        transaction3.confirmed = True
        self.mem_pool.transactions = [transaction1, transaction2, transaction3]

        confirmed_transactions = await self.mem_pool.get_confirmed_transactions()
        self.assertEqual(len(confirmed_transactions), 2)
        self.assertIn(transaction1, confirmed_transactions)
        self.assertNotIn(transaction2, confirmed_transactions)
        self.assertIn(transaction3, confirmed_transactions)

    async def test_transaction_log(self):
        transaction1 = MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1')
        transaction2 = MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        transaction3 = MempoolTransaction('BTC', 0.003, 3.0, 'sender3', 'recipient3')
        self.mem_pool.transactions = [transaction1, transaction2, transaction3]

        transaction_log = self.mem_pool.transactions
        self.assertEqual(len(transaction_log), 3)

if __name__ == '__main__':
    unittest.main()
