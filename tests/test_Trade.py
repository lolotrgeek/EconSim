import unittest
from datetime import datetime
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.types.Trade import Trade

class TradeTests(unittest.TestCase):

    def test_trade_representation(self):
        trade = Trade('AAPL', 100, 150.0, 'Buyer', 'Seller')
        expected_repr = "<Trade: AAPL 100@150.0 None>"
        self.assertEqual(repr(trade), expected_repr)

    def test_trade_to_dict(self):
        trade = Trade('AAPL', 100, 150.0, 'Buyer', 'Seller')
        expected_dict = {
            'dt': None,
            'ticker': 'AAPL',
            'qty': 100,
            'price': 150.0,
            'buyer': 'Buyer',
            'seller': 'Seller',
            'fee': 0
        }
        self.assertEqual(trade.to_dict(), expected_dict)

    def test_trade_with_datetime(self):
        now = datetime.now()
        trade = Trade('AAPL', 100, 150.0, 'Buyer', 'Seller', dt=now)
        self.assertEqual(trade.dt, now)

    def test_trade_with_fee(self):
        trade = Trade('AAPL', 100, 150.0, 'Buyer', 'Seller', fee=10.0)
        self.assertEqual(trade.fee, 10.0)

if __name__ == '__main__':
    unittest.main()