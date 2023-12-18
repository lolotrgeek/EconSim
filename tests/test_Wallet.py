import unittest
from unittest.mock import MagicMock, patch
from source.crypto.Wallet import Wallet
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from .MockRequesterDefi import MockRequesterDefiExchange as MockRequester
from .MockRequesterCrypto import MockRequesterCrypto

class TestWallet(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.wallet = Wallet("MyWallet")
        self.wallet.crypto_requester = CryptoCurrencyRequests( MockRequesterCrypto())
        self.wallet.requester = DefiExchangeRequests( MockRequester())
        
    async def test_connect(self):
        # Test connecting to a chain
        chain = "ETH"
        await self.wallet.connect(chain)
        self.assertEqual(self.wallet.chain['symbol'], "ETH")

    async def test_is_connected(self):
        # Test checking if wallet is connected to a chain
        self.assertFalse(self.wallet.is_connected())

        # Connect the wallet to a chain
        chain = "ETH"
        self.wallet.connect(chain)
        self.assertTrue(self.wallet.is_connected())

    async def test_get_balance(self):
        # Mock the crypto_requester and set the balance
        balance = 100.0
        self.wallet.crypto_requester = MagicMock()
        self.wallet.crypto_requester.get_balance.return_value = balance

        # Test getting the balance of an asset
        asset = "ETH"
        result = self.wallet.get_balance(asset)
        self.assertEqual(result, balance)

    async def test_get_assets(self):
        # Mock the crypto_requester and set the assets
        assets = ["ETH", "BTC", "LTC"]
        self.wallet.crypto_requester = MagicMock()
        self.wallet.crypto_requester.get_assets.return_value = assets

        # Test getting the assets in the wallet
        result = self.wallet.get_assets()
        self.assertEqual(result, assets)

    async def test_check_txn(self):
        # Mock the crypto_requester and set the transaction status
        txn = "0x1234567890"
        status = "confirmed"
        self.wallet.crypto_requester = MagicMock()
        self.wallet.crypto_requester.check_txn.return_value = status

        # Test checking the status of a transaction
        result = self.wallet.check_txn(txn)
        self.assertEqual(result, status)

    async def test_signature_request(self):
        # Mock the crypto_requester and set the signature request status
        txn = "0x1234567890"
        status = "pending"
        self.wallet.crypto_requester = MagicMock()
        self.wallet.crypto_requester.signature_request.return_value = status

        # Test requesting a signature for a transaction
        result = self.wallet.signature_request(txn)
        self.assertEqual(result, status)

    async def test_sign_txn(self):
        # Mock the crypto_requester and set the transaction status
        txn = "0x1234567890"
        status = "signed"
        self.wallet.crypto_requester = MagicMock()
        self.wallet.crypto_requester.sign_txn.return_value = status

        # Test signing a transaction
        result = self.wallet.sign_txn(txn)
        self.assertEqual(result, status)

    @patch('source.crypto.CryptoCurrencyRequests.CryptoCurrencyRequests.get_last_fee')
    async def test_set_fee(self, mock_get_last_fee):
        # Mock the crypto_requester and set the last fee
        network_fee = 0.01
        mock_get_last_fee.return_value = network_fee

        # Mock the is_connected method
        self.wallet.is_connected = MagicMock(return_value=True)

        # Test setting the fee
        result = self.wallet.set_fee()
        expected_fee = network_fee * 2
        self.assertEqual(result, expected_fee)

if __name__ == '__main__':
    unittest.main()
