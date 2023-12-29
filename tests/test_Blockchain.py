import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import unittest
from datetime import datetime
import random
from decimal import Decimal
from source.crypto.Blockchain import Blockchain, MempoolTransaction

class BlockchainTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.blockchain = Blockchain("test", datetime(2022, 1, 1))

    async def test_new_block(self):
        transactions = [
            MempoolTransaction('BTC', '0.001', '1.0', 'sender1', 'recipient1', datetime(2022, 1, 1)),
            MempoolTransaction('ETH', '0.002', '2.0', 'sender2', 'recipient2', datetime(2022, 1, 1))
        ]
        previous_hash = 'previous_hash'
        block = await self.blockchain.new_block(transactions, previous_hash)

        self.assertEqual(len(self.blockchain.chain), 2)
        self.assertEqual(block['index'], 2)
        self.assertEqual(block['timestamp'], datetime(2022, 1, 1))
        self.assertEqual(block['transactions'], transactions)
        self.assertEqual(block['previous_hash'], previous_hash)

    async def test_add_transaction(self):
        asset = 'BTC'
        fee = Decimal('0.001000000000000000')
        amount = Decimal('1.000000000000000000')
        sender = 'sender1'
        recipient = 'recipient1'
        self.blockchain.datetime=datetime(2022, 1, 3)

        await self.blockchain.add_transaction(asset, fee, amount, sender, recipient)
        mempool_transactions = self.blockchain.mempool.transactions
        self.assertEqual(len(mempool_transactions), 1)
        self.assertEqual(mempool_transactions[0].asset, asset)
        self.assertEqual(mempool_transactions[0].fee, fee)
        self.assertEqual(mempool_transactions[0].amount, amount)
        self.assertEqual(mempool_transactions[0].sender, sender)
        self.assertEqual(mempool_transactions[0].recipient, recipient)
        self.assertEqual(mempool_transactions[0].confirmed, False)
        self.assertEqual(mempool_transactions[0].dt, datetime(2022, 1, 3))

    async def test_cancel_transaction(self):
        asset = 'BTC'
        fee = Decimal('0.001000000000000000')
        amount = Decimal('1.000000000000000000')
        sender = 'sender1'
        recipient = 'recipient1'
        self.blockchain.datetime=datetime(2022, 1, 3)

        transaction = await self.blockchain.add_transaction(asset, fee, amount, sender, recipient)
        cancelled_transaction = await self.blockchain.cancel_transaction(transaction.id)
        mempool_transactions = self.blockchain.mempool.transactions
        self.assertEqual(len(mempool_transactions), 0)
        self.assertEqual(cancelled_transaction['asset'], asset)
        self.assertEqual(cancelled_transaction['fee'], fee)
        self.assertEqual(cancelled_transaction['amount'], amount)
        self.assertEqual(cancelled_transaction['sender'], sender)
        self.assertEqual(cancelled_transaction['recipient'], recipient)
        self.assertEqual(cancelled_transaction['confirmed'], False)
        self.assertEqual(cancelled_transaction['dt'], datetime(2022, 1, 3))

    async def test_process_transactions(self):
        self.blockchain.datetime = datetime(2022, 1, 3)
        await self.blockchain.add_transaction('BTC', '0.001', '1.0', 'sender1', 'recipient1')
        self.blockchain.datetime = datetime(2022, 1, 5)
        await self.blockchain.add_transaction('ETH', '0.002', '2.0', 'sender2', 'recipient2')
        self.blockchain.datetime = datetime(2022, 1, 6)
        await self.blockchain.add_transaction('LTC', '0.003', '3.0', 'sender3', 'recipient3')
        pending_transactions = await self.blockchain.mempool.get_pending_transactions()
        pending_transactions.sort( key=lambda x: x.fee, reverse=True)
        
        length_before = len(self.blockchain.chain)
        
        random.seed(42)  # Set seed for predictable random number generation
        processed = await self.blockchain.process_transactions()
        self.assertEqual(len(pending_transactions), len(self.blockchain.chain)-length_before + 1)
        self.assertEqual(pending_transactions[0].fee, Decimal('0.003'))
        self.assertEqual(pending_transactions[1].fee, Decimal('0.002'))
        self.assertEqual(pending_transactions[2].fee, Decimal('0.001'))
        self.assertEqual(processed['confirmed'], 2)
        self.assertEqual(processed['unconfirmed'], 1)

    async def test_confirmation_odds(self):
        odds = await self.blockchain.confirmation_odds(0, 10)
        lower_odds = await self.blockchain.confirmation_odds(1, 10)
        lowest_odds = await self.blockchain.confirmation_odds(2, 10)
        self.assertGreater(odds, lower_odds)
        self.assertGreater(lower_odds, lowest_odds)

    async def test_prune(self):
        self.blockchain.max_transactions = 20
        for i in range(20):
            self.blockchain.chain.append(MempoolTransaction('BTC', '0.001', 1.0, 'sender1', 'recipient1', datetime(2022, 1, i+1)))

        self.assertEqual(len(self.blockchain.chain), 21)

        await self.blockchain.prune()
        self.assertEqual(len(self.blockchain.chain), 11)
        self.assertEqual(datetime(2022, 1, 10), self.blockchain.chain[0].dt)
        self.assertEqual(datetime(2022, 1, 20), self.blockchain.chain[-1].dt)
        self.assertEqual(len(self.blockchain.pruned_chain.get(str(datetime(2022, 1, 10)))), 10)
        os.remove("archive/testchain.bak")
        os.remove("archive/testchain.dat")
        os.remove("archive/testchain.dir")

    async def test_get_transactions(self):
        transaction1 = MempoolTransaction('BTC', '0.001', '1.0', 'sender1', 'recipient1', datetime(2022, 1, 6))
        transaction2 = MempoolTransaction('ETH', '0.002', '2.0', 'sender2', 'recipient2', datetime(2022, 1, 6))
        transaction3 = MempoolTransaction('LTC', '0.003', '3.0', 'sender3', 'recipient3', datetime(2022, 1, 6))
        self.blockchain.chain = [transaction1, transaction2, transaction3]
        transactions = await self.blockchain.get_transactions()
        self.assertEqual(len(transactions), 3)
        self.assertIn(transaction1.to_dict(), transactions)
        self.assertIn(transaction2.to_dict(), transactions)
        self.assertIn(transaction3.to_dict(), transactions)

    async def test_get_transaction(self):
        transaction1 = MempoolTransaction('BTC', '0.001', '1.0', 'sender1', 'recipient1', datetime(2022, 1, 8))
        transaction2 = MempoolTransaction('ETH', '0.002', '2.0', 'sender2', 'recipient2', datetime(2022, 1, 8))
        transaction3 = MempoolTransaction('LTC', '0.003', '3.0', 'sender3', 'recipient3', datetime(2022, 1, 8))
        self.blockchain.chain = [transaction1, transaction2, transaction3]
        transaction = await self.blockchain.get_transaction(transaction2.id)
        self.assertEqual(transaction, transaction2.to_dict())

    async def test_last_block(self):
        block1 = self.blockchain.last_block
        self.assertEqual(block1.dt, datetime(2022, 1, 1))
        self.assertEqual(len(self.blockchain.chain), 1)

        transactions = [
            MempoolTransaction('BTC', '0.001', '1.0', 'sender1', 'recipient1'),
            MempoolTransaction('ETH', '0.002', '2.0', 'sender2', 'recipient2')
        ]
        previous_hash = 'previous_hash'
        self.blockchain.datetime = datetime(2022, 1, 8)
        await self.blockchain.new_block(transactions, previous_hash)
        block2 = self.blockchain.last_block
        self.assertEqual(block2['timestamp'], datetime(2022, 1, 8))
        self.assertEqual(len(self.blockchain.chain), 2)

if __name__ == '__main__':
    asyncio.run(unittest.main())
