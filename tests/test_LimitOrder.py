import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.types.LimitOrder import LimitOrder
from source.exchange.types.OrderSide import OrderSide
import unittest
from datetime import datetime
from decimal import Decimal

class LimitOrderTests(unittest.TestCase):

    def setUp(self):
        self.limit_order = LimitOrder('AAPL', Decimal('150.0'), 100, 'Creator', OrderSide.BUY)

    def test_limit_order_id(self):
        self.assertIsNotNone(self.limit_order.id)

    def test_limit_order_ticker(self):
        self.assertEqual(self.limit_order.ticker, 'AAPL')

    def test_limit_order_price(self):
        self.assertEqual(self.limit_order.price, Decimal('150.0'))

    def test_limit_order_qty(self):
        self.assertEqual(self.limit_order.qty, 100)

    def test_limit_order_creator(self):
        self.assertEqual(self.limit_order.creator, 'Creator')

    def test_limit_order_dt(self):
        self.assertIsInstance(self.limit_order.dt, datetime)

    def test_limit_order_fee(self):
        self.assertEqual(self.limit_order.fee, 0)

    def test_limit_order_to_dict(self):
        expected_dict = {
            'id': self.limit_order.id,
            'ticker': 'AAPL',
            'price': Decimal('150.0'),
            'qty': 100,
            'type': 'limit_buy',
            'dt': self.limit_order.dt,
        }
        self.assertDictEqual(self.limit_order.to_dict(), expected_dict)

    def test_limit_order_to_dict_full(self):
        expected_dict = {
            'id': self.limit_order.id,
            'ticker': 'AAPL',
            'price': Decimal('150.0'),
            'fee': 0,
            'fills': [ ],
            'qty': 100,
            'creator': 'Creator',
            'type': 'limit_buy',
            'dt': self.limit_order.dt,
            'accounting': 'FIFO',
            'position_id': None
        }
        self.assertDictEqual(self.limit_order.to_dict_full(), expected_dict)

    def test_limit_order_repr(self):
        expected_repr = "<LimitOrder: AAPL 100@150.0>"
        self.assertEqual(repr(self.limit_order), expected_repr)

    def test_limit_order_str(self):
        expected_str = "<LimitOrder: AAPL 100@150.0>"
        self.assertEqual(str(self.limit_order), expected_str)

if __name__ == '__main__':
    asyncio.run(unittest.main())
