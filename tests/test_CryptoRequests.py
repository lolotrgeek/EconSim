import sys,os
from decimal import Decimal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import unittest
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from .MockRequesterCrypto import MockRequesterCrypto as MockRequester

class TestCryptoRequests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = Requests(MockRequester())

    async def test_get_transactions(self):
        usd_txns = await self.requests.get_transactions('USD')
        btc_txns = await self.requests.get_transactions('BTC')
        eth_txns = await self.requests.get_transactions('ETH')
        print(usd_txns)
        self.assertEqual(usd_txns[0]['asset'], 'USD')
        self.assertEqual(usd_txns[0]['fee'], 0.0)
        self.assertEqual(usd_txns[0]['amount'], 0)
        self.assertEqual(usd_txns[0]['sender'], 'init_seed')
        self.assertEqual(usd_txns[0]['recipient'], 'init_seed')
        self.assertEqual(usd_txns[0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(usd_txns[0]['confirmed'], True)
        self.assertEqual(usd_txns[0]['timestamp'], None)

        self.assertEqual(btc_txns[0]['asset'], 'BTC')
        self.assertEqual(btc_txns[0]['fee'], 0.0)
        self.assertEqual(btc_txns[0]['amount'], 0.0)
        self.assertEqual(btc_txns[0]['sender'], 'init_seed')
        self.assertEqual(btc_txns[0]['recipient'], 'init_seed')
        self.assertEqual(btc_txns[0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(btc_txns[0]['confirmed'], True)
        self.assertEqual(btc_txns[0]['timestamp'], None)

        self.assertEqual(eth_txns[0]['asset'], 'ETH')
        self.assertEqual(eth_txns[0]['fee'], 0.0)
        self.assertEqual(eth_txns[0]['amount'], 0.0)
        self.assertEqual(eth_txns[0]['sender'], 'init_seed')
        self.assertEqual(eth_txns[0]['recipient'], 'init_seed')
        self.assertEqual(eth_txns[0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(eth_txns[0]['confirmed'], True)
        self.assertEqual(eth_txns[0]['timestamp'], None)

    async def test_get_transaction(self):
        id = self.requests.requester.responder.cryptos['BTC'].blockchain.chain[0].id
        print(id)
        txn_id = await self.requests.get_transaction('BTC', id)
        self.assertEqual(txn_id['id'], id)

    async def test_add_transaction(self):
        txn = await self.requests.add_transaction('USD', 0.1, 1000, 'sender', 'recipient')
        self.assertEqual(txn['asset'], 'USD')
        self.assertEqual(txn['fee'], 0.1)
        self.assertEqual(txn['amount'], 1000)
        self.assertEqual(txn['sender'], 'sender')
        self.assertEqual(txn['recipient'], 'recipient')
        self.assertEqual(txn['confirmed'], False)
        self.assertEqual(txn['timestamp'], None)

    async def test_get_mempool(self):
        mempool = await self.requests.get_mempool('BTC')
        self.assertEqual(type(mempool), list)
        self.assertEqual(len(mempool), 0)      

    async def test_get_pending_transactions(self):
        pending = await self.requests.get_pending_transactions('BTC')
        self.assertEqual(type(pending), list)
        self.assertEqual(len(pending), 0)

    async def test_get_confirmed_transactions(self):
        confirmed = await self.requests.get_confirmed_transactions('BTC')
        self.assertEqual(type(confirmed), list)
        self.assertEqual(len(confirmed), 0)
