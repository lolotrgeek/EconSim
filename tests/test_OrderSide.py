import unittest
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.types.OrderSide import OrderSide

class OrderSideTests(unittest.TestCase):

    def test_order_side_values(self):
        self.assertEqual(OrderSide.BUY.value, 'buy')
        self.assertEqual(OrderSide.SELL.value, 'sell')

    def test_order_side_names(self):
        self.assertEqual(OrderSide.BUY.name, 'BUY')
        self.assertEqual(OrderSide.SELL.name, 'SELL')

    def test_order_side_iteration(self):
        order_sides = list(OrderSide)
        self.assertEqual(order_sides[0], OrderSide.BUY)
        self.assertEqual(order_sides[1], OrderSide.SELL)

if __name__ == '__main__':
    unittest.main()
