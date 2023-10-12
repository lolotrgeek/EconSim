import unittest
import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Instruments.Tax import Tax 
from decimal import Decimal

class TestTax(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tax_calculator = Tax()

    def test_calculate_tax_ordinary(self):
        income = 40000
        result = asyncio.run(self.tax_calculator.calculate_tax(income, 'ordinary', debug=False))
        self.assertEqual(result['amount'], Decimal('4360.0'))  # Expected tax amount

    def test_calculate_tax_long_term(self):
        income = 1000000
        result = asyncio.run(self.tax_calculator.calculate_tax(income, 'long_term', debug=False))
        self.assertEqual(result['amount'], Decimal('161637.55'))  # Expected tax amount

    def test_calculate_tax_state(self):
        income = 5000
        result = asyncio.run(self.tax_calculator.calculate_tax(income, 'state', debug=False))
        self.assertEqual(result['amount'], Decimal('117.335'))  # Expected tax amount

    def test_calculate_tax_zero_income(self):
        income = 0
        result = asyncio.run(self.tax_calculator.calculate_tax(income, 'ordinary', debug=False))
        self.assertEqual(result['amount'], 0)  # Expected tax amount

    def test_calculate_tax_negative_income(self):
        income = -10000
        result = asyncio.run(self.tax_calculator.calculate_tax(income, 'long_term', debug=False))
        self.assertEqual(result['amount'], 0)  # Expected tax amount (tax on negative income should be zero)

    def test_calculate_tax_invalid_bracket_type(self):
        income = 100000
        with self.assertRaises(KeyError):
            asyncio.run(self.tax_calculator.calculate_tax(income, 'invalid_type', debug=False))

if __name__ == '__main__':
    asyncio.run(unittest.main())