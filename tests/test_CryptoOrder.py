import unittest
from datetime import datetime
import sys
import os
from decimal import Decimal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.exchange.types.CryptoOrder import CryptoOrder

class TestCryptoOrder(unittest.TestCase):
    def setUp(self):
        self.base = 'BTC'
        self.quote = 'USD'
        self.price = Decimal('50000')
        self.qty = Decimal('0.5')
        self.creator = 'John'
        self.order_type = 'limit'
        self.side = 'buy'
        self.dt = datetime.now()
        self.exchange_fee = Decimal('0.01')
        self.network_fee = Decimal('0.001')
        self.status = 'open'
        self.accounting = 'FIFO'
        self.position_id = '12345'
        self.fills = []

    def test_init(self):
        order = CryptoOrder(self.base, self.quote, self.price, self.qty, self.creator, self.order_type, self.side, self.dt, self.exchange_fee, self.network_fee, self.status, self.accounting, self.position_id, self.fills)
        self.assertEqual(order.base, self.base)
        self.assertEqual(order.quote, self.quote)
        self.assertEqual(order.price, self.price)
        self.assertEqual(order.qty, self.qty)
        self.assertEqual(order.creator, self.creator)
        self.assertEqual(order.type, self.order_type)
        self.assertEqual(order.side, self.side)
        self.assertEqual(order.dt, self.dt)
        self.assertEqual(order.exchange_fee, self.exchange_fee)
        self.assertEqual(order.network_fee, self.network_fee)
        self.assertEqual(order.status, self.status)
        self.assertEqual(order.accounting, self.accounting)
        self.assertEqual(order.position_id, self.position_id)
        self.assertEqual(order.fills, self.fills)

    def test_to_dict(self):
        order = CryptoOrder(self.base, self.quote, self.price, self.qty, self.creator, self.order_type, self.side, self.dt, self.exchange_fee, self.network_fee, self.status, self.accounting, self.position_id, self.fills)
        order_dict = order.to_dict()
        # Add assertions to check the correctness of the to_dict() method

    def test_to_dict_full(self):
        order = CryptoOrder(self.base, self.quote, self.price, self.qty, self.creator, self.order_type, self.side, self.dt, self.exchange_fee, self.network_fee, self.status, self.accounting, self.position_id, self.fills)
        order_dict = order.to_dict_full()
        # Add assertions to check the correctness of the to_dict_full() method

    def test_repr(self):
        order = CryptoOrder(self.base, self.quote, self.price, self.qty, self.creator, self.order_type, self.side, self.dt, self.exchange_fee, self.network_fee, self.status, self.accounting, self.position_id, self.fills)
        order_repr = repr(order)
        # Add assertions to check the correctness of the __repr__() method

    def test_str(self):
        order = CryptoOrder(self.base, self.quote, self.price, self.qty, self.creator, self.order_type, self.side, self.dt, self.exchange_fee, self.network_fee, self.status, self.accounting, self.position_id, self.fills)
        order_str = str(order)
        # Add assertions to check the correctness of the __str__() method


