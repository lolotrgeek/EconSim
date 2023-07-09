import unittest
from datetime import datetime
import pandas as pd
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.crypto.MemPool import MempoolTransaction, MemPool

class MemPoolTests(unittest.TestCase):

    def setUp(self):
        self.mem_pool = MemPool()

    def test_get_pending_transactions_empty(self):
        pending_transactions = self.mem_pool.get_pending_transactions()
        self.assertEqual(len(pending_transactions), 0)

    def test_get_confirmed_transactions_empty(self):
        confirmed_transactions = self.mem_pool.get_confirmed_transactions()
        self.assertEqual(len(confirmed_transactions), 0)

    def test_transaction_log_empty(self):
        transaction_log = self.mem_pool.transaction_log
        self.assertTrue(isinstance(transaction_log, pd.DataFrame))
        self.assertEqual(len(transaction_log), 0)

    def test_get_pending_transactions(self):
        transaction1 = MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1')
        transaction2 = MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        transaction3 = MempoolTransaction('BTC', 0.003, 3.0, 'sender3', 'recipient3')
        self.mem_pool.transactions = [transaction1, transaction2, transaction3]

        pending_transactions = self.mem_pool.get_pending_transactions()
        self.assertEqual(len(pending_transactions), 3)
        self.assertIn(transaction1, pending_transactions)
        self.assertIn(transaction2, pending_transactions)
        self.assertIn(transaction3, pending_transactions)

    def test_get_confirmed_transactions(self):
        transaction1 = MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1')
        transaction2 = MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        transaction3 = MempoolTransaction('BTC', 0.003, 3.0, 'sender3', 'recipient3')
        transaction1.confirmed = True
        transaction3.confirmed = True
        self.mem_pool.transactions = [transaction1, transaction2, transaction3]

        confirmed_transactions = self.mem_pool.get_confirmed_transactions()
        self.assertEqual(len(confirmed_transactions), 2)
        self.assertIn(transaction1, confirmed_transactions)
        self.assertNotIn(transaction2, confirmed_transactions)
        self.assertIn(transaction3, confirmed_transactions)

    def test_transaction_log(self):
        transaction1 = MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1')
        transaction2 = MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        transaction3 = MempoolTransaction('BTC', 0.003, 3.0, 'sender3', 'recipient3')
        self.mem_pool.transactions = [transaction1, transaction2, transaction3]

        transaction_log = self.mem_pool.transaction_log
        self.assertTrue(isinstance(transaction_log, pd.DataFrame))
        self.assertEqual(len(transaction_log), 3) 
        self.assertEqual(transaction_log.loc[transaction1.dt]['ticker'][0], 'BTC')
        self.assertEqual(transaction_log.loc[transaction1.dt]['sender'][0], 'sender1')
        self.assertEqual(transaction_log.loc[transaction1.dt]['recipient'][0], 'recipient1')
        self.assertEqual(transaction_log.loc[transaction1.dt]['fee'][0], 0.001)
        self.assertEqual(transaction_log.loc[transaction1.dt]['amount'][0], 1.0)
    
        self.assertEqual(transaction_log.loc[transaction2.dt]['ticker'][1], 'ETH')
        self.assertEqual(transaction_log.loc[transaction2.dt]['sender'][1], 'sender2')
        self.assertEqual(transaction_log.loc[transaction2.dt]['recipient'][1], 'recipient2')
        self.assertEqual(transaction_log.loc[transaction2.dt]['amount'][1], 2.0)
        self.assertEqual(transaction_log.loc[transaction2.dt]['fee'][1], 0.002)

        self.assertEqual(transaction_log.loc[transaction3.dt]['ticker'][2], 'BTC')
        self.assertEqual(transaction_log.loc[transaction3.dt]['sender'][2], 'sender3')
        self.assertEqual(transaction_log.loc[transaction3.dt]['recipient'][2], 'recipient3')
        self.assertEqual(transaction_log.loc[transaction3.dt]['fee'][2], 0.003)
        self.assertEqual(transaction_log.loc[transaction3.dt]['amount'][2], 3.0)

if __name__ == '__main__':
    unittest.main()
