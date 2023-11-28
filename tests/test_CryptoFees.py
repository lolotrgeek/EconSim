import asyncio
import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.types.CryptoFees import Fees

class FeesTests(unittest.TestCase):

    def setUp(self):
        self.fees = Fees()
        self.fees.waive_fees = False

    def test_taker_fee(self):
        volume = 1000
        expected_fee = volume * self.fees.taker_fee_rate
        self.assertEqual(self.fees.taker_fee(volume, 2), expected_fee)

    def test_maker_fee(self):
        volume = 1000
        expected_fee = volume * self.fees.maker_fee_rate
        self.assertEqual(self.fees.maker_fee(volume, 2), expected_fee)

    def test_add_fee(self):
        asset = 'USD'
        fee = 100
        self.assertEqual(self.fees.add_fee(asset, fee), {asset: fee})
        self.assertEqual(self.fees.fees_collected, {asset: fee})

if __name__ == '__main__':
    unittest.main()