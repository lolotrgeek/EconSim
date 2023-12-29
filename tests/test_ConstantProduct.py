import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import unittest
from decimal import Decimal
from source.exchange.components.ConstantProduct import ConstantProduct
from source.utils._utils import non_zero_prec

class TestConstantProduct(unittest.TestCase):
    def setUp(self):
        self.cp = ConstantProduct(Decimal(100), Decimal(200))

    def test_init(self):
        self.assertEqual(self.cp.reserve_a, 100)
        self.assertEqual(self.cp.reserve_b, 200)
        self.assertEqual(self.cp.k, 20000)

    def test_get_price(self):
        price = self.cp.get_price(10)
        self.assertEqual(price, Decimal('18.181818181818181819'))

    def test_balance(self):
        self.cp.reserve_a = 110
        new_price = self.cp.balance(10)
        self.assertEqual(new_price, Decimal('16.666666666666666667'))
        self.assertEqual(self.cp.k, Decimal('22000.000000000000000000'))

    def test_get_total_reserves(self):
        total_reserves = self.cp.get_total_reserves()
        self.assertEqual(total_reserves, 300)

    def test_to_dict(self):
        cp_dict = self.cp.to_dict()
        self.assertEqual(cp_dict, {'reserve_a': 100, 'reserve_b': 200, 'k': 20000})

class TestConstantProductBehavior(unittest.TestCase):
    def setUp(self):
        self.cp = ConstantProduct(Decimal(100), Decimal(200)) 

    def test_adding_to_reserves(self):
        asset_a = 10
        # provide liquidity
        asset_b = self.cp.get_price(asset_a)
        self.cp.reserve_a += asset_a
        self.cp.reserve_b += asset_b
        new_price = self.cp.balance(asset_a)
        self.assertTrue(asset_b == new_price)
    
    def test_removing_one_reserve(self):
        asset_a = 10        
        #swap
        asset_b = self.cp.get_price(asset_a)
        self.cp.reserve_a += asset_a
        self.cp.reserve_b -= asset_b
        new_price = self.cp.balance(asset_a)
        self.assertTrue(asset_b > new_price)

    def test_removing_reserves(self):
        asset_a = 10
        #remove liquidity
        asset_b = self.cp.get_price(asset_a)
        self.cp.reserve_a -= asset_a
        self.cp.reserve_b -= asset_b
        new_price = self.cp.balance(asset_a)
        self.assertTrue(asset_b == new_price)

    @unittest.skip("This test is being ignored")
    def test_collecing_fees(self):
        #add liquidity
        position_1_a = 10
        position_1_b = self.cp.get_price(position_1_a)
        self.cp.reserve_a += position_1_a
        self.cp.reserve_b += position_1_b
        new_price = self.cp.balance(position_1_a)
        self.assertTrue(position_1_b == new_price)

        #add liquidity
        position_2_a = 20
        position_2_b = self.cp.get_price(position_2_a)
        self.cp.reserve_a += position_2_a
        self.cp.reserve_b += position_2_b
        new_price = self.cp.balance(position_2_a)
        self.assertTrue(position_2_b == new_price)

        # swap
        swap_a = 5
        swap_b = self.cp.get_price(swap_a)
        fee= swap_a * Decimal('.003')
        self.cp.reserve_a += swap_a
        self.cp.reserve_b -= swap_b
        self.cp.fees += fee
        new_price = self.cp.balance(swap_a)
        self.assertTrue(swap_b > new_price)

        # calculate % of pool for positions
        position_1_a_pct = non_zero_prec(position_1_a / self.cp.reserve_a)
        position_2_a_pct = non_zero_prec(position_2_a / self.cp.reserve_a)

        # calculate fees
        position_1_a_fees = non_zero_prec(position_1_a_pct * self.cp.fees)
        position_1_b_fees = self.cp.get_price(position_1_a_fees)

        position_2_a_fees = non_zero_prec(position_2_a_pct * self.cp.fees)
        position_2_b_fees = self.cp.get_price(position_2_a_fees)

        # calculate fees collected
        self.cp.fees -= position_1_a_fees
        self.cp.reserve_b -= position_1_b_fees
        self.cp.balance(position_1_a_fees)

        self.cp.fees -= position_2_a_fees
        self.cp.reserve_b -= position_2_b_fees
        old_price = Decimal(new_price)
        new_price = self.cp.balance(position_1_b_fees)

        self.assertTrue(old_price > new_price)




if __name__ == '__main__':
    unittest.main()