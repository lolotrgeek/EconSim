import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.types.Fees import Fees

class FeesTests(unittest.TestCase):

    def setUp(self):
        self.fees = Fees()
        self.fees.waive_fees = False

    def test_taker_fee(self):
        volume = 1000
        expected_fee = volume * self.fees.taker_fee_rate
        self.assertEqual(self.fees.taker_fee(volume), expected_fee)

    def test_maker_fee(self):
        volume = 1000
        expected_fee = volume * self.fees.maker_fee_rate
        self.assertEqual(self.fees.maker_fee(volume), expected_fee)

if __name__ == '__main__':
    unittest.main()