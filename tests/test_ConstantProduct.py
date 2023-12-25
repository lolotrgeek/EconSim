import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import unittest
from decimal import Decimal
from source.exchange.components.ConstantProduct import ConstantProduct

class TestConstantProduct(unittest.TestCase):
    def setUp(self):
        self.cp = ConstantProduct(Decimal(100), Decimal(200))

    def test_init(self):
        self.assertEqual(self.cp.reserve_a, 100)
        self.assertEqual(self.cp.reserve_b, 200)
        self.assertEqual(self.cp.k, 20000)

    def test_get_price(self):
        price = self.cp.get_price(10)
        self.assertEqual(price, Decimal('18.181818181818181818'))

    def test_balance(self):
        balance = self.cp.balance(10)
        self.assertEqual(balance, Decimal('18.181818181818181818'))
        self.assertEqual(self.cp.reserve_a, 110)
        self.assertEqual(self.cp.reserve_b, Decimal('181.818181818181818182'))
        self.assertEqual(self.cp.k, Decimal('20000.000000000000000020'))

    def test_get_total_reserves(self):
        total_reserves = self.cp.get_total_reserves()
        self.assertEqual(total_reserves, 300)

    def test_to_dict(self):
        cp_dict = self.cp.to_dict()
        self.assertEqual(cp_dict, {'reserve_a': 100, 'reserve_b': 200, 'k': 20000})

if __name__ == '__main__':
    unittest.main()