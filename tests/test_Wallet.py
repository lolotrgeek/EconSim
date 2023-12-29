import unittest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime
from source.crypto.Wallet import Wallet
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.MemPool import MempoolTransaction
from .MockRequesterDefi import MockRequesterDefiExchange as MockRequester
from .MockRequesterCrypto import MockRequesterCrypto

class TestWallet(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.wallet = Wallet("MyWallet")
        self.wallet.crypto_requests = CryptoCurrencyRequests( MockRequesterCrypto())
        self.wallet.requests = DefiExchangeRequests( MockRequester())
        self.seed_address = self.wallet.crypto_requests.requester.responder.currencies['ETH'].burn_address
   
    async def test_connect(self):
        # Test connecting to a chain
        chain = "ETH"
        await self.wallet.connect(chain)
        self.assertEqual(self.wallet.chain['symbol'], "ETH")

    async def test_is_connected(self):
        # Test checking if wallet is connected to a chain
        self.assertFalse(await self.wallet.is_connected())

        # Connect the wallet to a chain
        chain = "ETH"
        await self.wallet.connect(chain)
        self.assertTrue(await self.wallet.is_connected())
    
    async def test_update_holdings(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 

        self.assertEqual(self.wallet.holdings['ETH'], 1)

    async def test_update_holdings_transfers(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, Decimal('2.01'), self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 

        transfers_in = [
            {'asset': 'ETH', 'address': '0x0', 'from': self.wallet.address, 'to': self.seed_address, 'for': 1, 'decimals': 8},
            {'asset': 'CAKE', 'address': '0x01', 'from': self.seed_address, 'to': self.wallet.address, 'for': 1, 'decimals': 8}
        ]
        txn = MempoolTransaction('ETH', Decimal('0.01'), 0, self.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_in).to_dict()
        result = await self.wallet.update_holdings(txn)
        self.assertEqual(self.wallet.holdings['ETH'], 1)
        self.assertEqual(self.wallet.holdings['CAKE'], 1)

    async def test_revert_holdings(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, Decimal('2.01'), self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 

        transfers_in = [
            {'asset': 'ETH', 'address': '0x0', 'from': self.wallet.address, 'to': self.seed_address, 'for': 1, 'decimals': 8},
            {'asset': 'CAKE', 'address': '0x01', 'from': self.seed_address, 'to': self.wallet.address, 'for': 1, 'decimals': 8}
        ]
        txn = MempoolTransaction('ETH', Decimal('0.01'), 0, self.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_in).to_dict()
        await self.wallet.update_holdings(txn)
        await self.wallet.revert_holdings(txn)
        self.assertEqual(self.wallet.holdings['ETH'], Decimal('2.01'))
        self.assertEqual(self.wallet.holdings['CAKE'], 0)

    async def test_get_balance(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, Decimal('2.01'), self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 
        balance = Decimal('2.01')
        asset = "ETH"
        result = await self.wallet.get_balance(asset)
        self.assertEqual(result, balance)

    async def test_check_txn(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn)

        no_asset_txn = MempoolTransaction('CAKE', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict() 
        not_enough_txn = MempoolTransaction('ETH', 0, 10, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict() 
        wrong_address_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        not_enough_fee = MempoolTransaction('ETH', 1, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict() 
        valid_txn = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict() 

        transfers_valid = [
            {'asset': 'ETH', 'address': '0x0', 'from': self.wallet.address, 'to': self.seed_address, 'for': 1, 'decimals': 8},
            {'asset': 'USDT', 'address': '0x01', 'from': self.seed_address, 'to': self.wallet.address, 'for': 1, 'decimals': 2}
        ]
        valid_transfer_txn = MempoolTransaction('ETH', Decimal('0.01'), 0, self.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_valid).to_dict()

        transfers_no_asset = [
            {'asset': 'BTC', 'address': '0x0', 'from': self.wallet.address, 'to': self.seed_address, 'for': 1, 'decimals': 8},
            {'asset': 'USDT', 'address': '0x01', 'from': self.seed_address, 'to': self.wallet.address, 'for': 1, 'decimals': 2}
        ]
        no_asset_transfer_txn = MempoolTransaction('ETH', Decimal('0.01'), 0, self.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_no_asset).to_dict()

        transfers_not_enough = [
            {'asset': 'ETH', 'address': '0x0', 'from': self.wallet.address, 'to': self.seed_address, 'for': 10, 'decimals': 8},
            {'asset': 'USDT', 'address': '0x01', 'from': self.seed_address, 'to': self.wallet.address, 'for': 1, 'decimals': 2}
        ]
        not_enough_transfer_txn = MempoolTransaction('ETH', Decimal('0.01'), 0, self.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_not_enough).to_dict()

        valid_result = await self.wallet.check_txn(valid_txn )
        no_asset_result = await self.wallet.check_txn(no_asset_txn)
        not_enough_result = await self.wallet.check_txn(not_enough_txn)
        wrong_address_result = await self.wallet.check_txn(wrong_address_txn)
        not_enough_fee_result = await self.wallet.check_txn(not_enough_fee)
        no_asset_transfer_result = await self.wallet.check_txn(no_asset_transfer_txn)
        not_enough_transfer_result = await self.wallet.check_txn(not_enough_transfer_txn)
        valid_transfer_result = await self.wallet.check_txn(valid_transfer_txn)

        self.assertEqual(no_asset_result, {'invalid': no_asset_txn, 'msg': 'Wallet does not have CAKE'})
        self.assertEqual(not_enough_result, {'invalid': not_enough_txn, 'msg': 'Wallet does not have enough ETH'})
        self.assertEqual(wrong_address_result, {'invalid': wrong_address_txn, 'msg': 'cannot sign transaction, sender address does not match wallet address'})
        self.assertEqual(not_enough_fee_result, {'invalid': not_enough_fee, 'msg': "Wallet does not have enough ETH to pay fee and amount"})
        self.assertEqual(valid_result, {'valid': valid_txn, 'msg': 'valid transaction'})
        self.assertEqual(no_asset_transfer_result, {'invalid': no_asset_transfer_txn, 'msg': 'Wallet does not have BTC'})
        self.assertEqual(not_enough_transfer_result, {'invalid': not_enough_transfer_txn, 'msg': 'Wallet does not have enough ETH'})
        self.assertEqual(valid_transfer_result, {'valid': valid_transfer_txn, 'msg': 'valid transaction'})

    async def test_signature_request(self):
        # Mock the crypto_requests and set the signature request status
        txn = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict() 

        # Test requesting a signature for a transaction
        result = await self.wallet.signature_request(txn)
        self.assertEqual(result, {'msg': 'request received'})
        self.assertEqual(self.wallet.signature_requests[0], txn)

    async def test_sign_txn(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 
        txn = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict()
        invalid_txn = MempoolTransaction('CAKE', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict()

        result = await self.wallet.sign_txn(txn, True)
        invalid_result = await self.wallet.sign_txn(invalid_txn, True)
        self.assertEqual(invalid_result, {'decision': False, 'txn': invalid_txn['id']})
        self.assertEqual(result, {'decision': True, 'txn': txn['id']})
        self.assertEqual(txn['id'] in self.wallet.pending_transactions, True)

    async def test_cancel_transaction(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict()
        await self.wallet.update_holdings(seed_txn)
        txn = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1))
        txn_unsigned = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1))
        self.wallet.crypto_requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions = [txn, txn_unsigned]
        sign = await self.wallet.sign_txn(txn.to_dict(), True)
        self.assertEqual(len(self.wallet.crypto_requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions), 2)
        result = await self.wallet.cancel_transaction(txn.id)
        failed_result = await self.wallet.cancel_transaction(txn_unsigned.id)
        self.assertEqual(result, {'msg': 'transaction cancelled'})
        self.assertEqual(failed_result, {'msg': f'wallet does not have a pending transaction with id {txn_unsigned.id}'})
        self.assertEqual(len(self.wallet.crypto_requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions), 1)

    async def test_transaction_confirmed(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 
        txn = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict()
        await self.wallet.sign_txn(txn, True)
        # Test requesting a signature for a transaction
        result = await self.wallet.transaction_confirmed(txn)
        self.assertEqual(result, {'msg': 'transaction confirmed'})
        self.assertEqual(txn['id'] not in self.wallet.pending_transactions, True)
        self.assertEqual(self.wallet.holdings['ETH'], 0)

    async def test_transaction_failed(self):
        await self.wallet.connect('ETH')
        seed_txn = MempoolTransaction('ETH', 0, 1, self.seed_address, self.wallet.address, datetime(2023,1,1)).to_dict() 
        await self.wallet.update_holdings(seed_txn) 
        txn = MempoolTransaction('ETH', 0, 1, self.wallet.address, self.seed_address, datetime(2023,1,1)).to_dict()
        await self.wallet.sign_txn(txn, True)
        self.wallet.pending_transactions[txn['id']] = seed_txn
        result = await self.wallet.transaction_failed(txn)
        self.assertEqual(result, {'msg': 'transaction failed'})
        self.assertEqual(txn['id'] not in self.wallet.pending_transactions, True)
        self.assertEqual(self.wallet.holdings['ETH'], 1)

    async def test_get_fee(self):
        await self.wallet.connect('ETH')
        fee = await self.wallet.get_fee()
        self.assertEqual(fee, Decimal('0.000000000000000001'))

    async def test_set_fee(self):
        await self.wallet.connect('ETH')
        fee = await self.wallet.set_fee(Decimal('0.000000000000000001'))
        auto_fee = await self.wallet.set_fee()
        self.assertEqual(fee, Decimal('0.000000000000000001'))
        self.assertEqual(auto_fee, Decimal('0.000000000000000002'))

if __name__ == '__main__':
    unittest.main()
