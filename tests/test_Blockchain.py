import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import unittest
from datetime import datetime
import random
import pandas as pd
from source.crypto.Blockchain import Blockchain,  MempoolTransaction

class BlockchainTests(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain(datetime(2022, 1, 1))

    def test_new_block(self):
        transactions = [
            MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1'),
            MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        ]
        previous_hash = 'previous_hash'
        block = self.blockchain.new_block(transactions, previous_hash, datetime(2022, 1, 2))

        self.assertEqual(len(self.blockchain.chain), 2)
        self.assertEqual(block['index'], 2)
        self.assertEqual(block['timestamp'], datetime(2022, 1, 2))
        self.assertEqual(block['transactions'], transactions)
        self.assertEqual(block['previous_hash'], previous_hash)

    def test_add_transaction(self):
        ticker = 'BTC'
        fee = 0.001
        amount = 1.0
        sender = 'sender1'
        recipient = 'recipient1'
        dt = datetime(2022, 1, 3)

        self.blockchain.add_transaction(ticker, fee, amount, sender, recipient, dt)
        mempool_transactions = self.blockchain.mempool.transactions
        self.assertEqual(len(mempool_transactions), 1)
        self.assertEqual(mempool_transactions[0].ticker, ticker)
        self.assertEqual(mempool_transactions[0].fee, fee)
        self.assertEqual(mempool_transactions[0].amount, amount)
        self.assertEqual(mempool_transactions[0].sender, sender)
        self.assertEqual(mempool_transactions[0].recipient, recipient)
        self.assertEqual(mempool_transactions[0].dt, dt)

    def test_process_transactions(self):
        self.blockchain.add_transaction('BTC', 0.001, 1.0, 'sender1', 'recipient1', datetime(2022, 1, 4))
        self.blockchain.add_transaction('ETH', 0.002, 2.0, 'sender2', 'recipient2', datetime(2022, 1, 5))
        self.blockchain.add_transaction('LTC', 0.003, 3.0, 'sender3', 'recipient3', datetime(2022, 1, 6))
        pending_transactions = self.blockchain.mempool.get_pending_transactions()
        length_before = len(self.blockchain.chain)
        
        random.seed(42)  # Set seed for predictable random number generation
        self.blockchain.process_transactions(datetime(2022, 1, 7))
        self.assertEqual(len(pending_transactions), len(self.blockchain.chain)-length_before + 1)
        #TODO: could also check timestamps of transactions in chain...

    def test_last_block(self):
        block1 = self.blockchain.last_block
        self.assertEqual(block1.dt, datetime(2022, 1, 1))
        self.assertEqual(len(self.blockchain.chain), 1)

        transactions = [
            MempoolTransaction('BTC', 0.001, 1.0, 'sender1', 'recipient1'),
            MempoolTransaction('ETH', 0.002, 2.0, 'sender2', 'recipient2')
        ]
        previous_hash = 'previous_hash'
        self.blockchain.new_block(transactions, previous_hash, datetime(2022, 1, 8))
        block2 = self.blockchain.last_block
        self.assertEqual(block2['timestamp'], datetime(2022, 1, 8))
        self.assertEqual(len(self.blockchain.chain), 2)

if __name__ == '__main__':
    unittest.main()
