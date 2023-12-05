import unittest
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils._utils import dumps, get_pandas_time, get_timedelta, get_datetime_range, get_random_string, format_dataframe_rows_to_dict, prec, non_zero_prec

class TestUtilsTest(unittest.TestCase):
    def test_dumps(self):
        data = {'key': 'value'}
        expected_output = '{\n    "key": "value"\n}'
        self.assertEqual(dumps(data), expected_output)

    def test_get_pandas_time(self):
        self.assertEqual(get_pandas_time('second'), '1s')
        self.assertEqual(get_pandas_time('minute'), '1Min')
        self.assertEqual(get_pandas_time('hour'), '1H')
        self.assertEqual(get_pandas_time('day'), '1Day')

    def test_get_timedelta(self):
        self.assertEqual(get_timedelta('second'), timedelta(seconds=1))
        self.assertEqual(get_timedelta('minute'), timedelta(minutes=1))
        self.assertEqual(get_timedelta('hour'), timedelta(hours=1))
        self.assertEqual(get_timedelta('day'), timedelta(days=1))

    def test_get_datetime_range(self):
        start_date = datetime(2023, 6, 1)
        end_date = datetime(2023, 6, 5)
        expected_output = [
            datetime(2023, 6, 1),
            datetime(2023, 6, 2),
            datetime(2023, 6, 3),
            datetime(2023, 6, 4),
        ]
        self.assertEqual(get_datetime_range(start_date, end_date), expected_output)

    def test_get_random_string(self):
        random_string = get_random_string()
        self.assertEqual(len(random_string), 9)

    def test_format_dataframe_rows_to_dict(self):
        import pandas as pd
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
        })
        expected_output = [
            {'col1': 1, 'col2': 'a'},
            {'col1': 2, 'col2': 'b'},
            {'col1': 3, 'col2': 'c'},
        ]
        self.assertEqual(format_dataframe_rows_to_dict(df), expected_output)

    def test_prec(self):
        self.assertEqual( prec('0.1234567890123456789') , Decimal('0.123456789012345679'))
        self.assertEqual( prec(Decimal('0.1234567890123456789')) , Decimal('0.123456789012345679'))
        self.assertEqual( len(str(prec('0.1234567890123456789')).split('.')[1]), 18)
        self.assertEqual( prec('10000.1234567890123456789'), Decimal('10000.123456789012345679'))
        self.assertEqual( prec('10000.1234567890123456789') , Decimal('10000.123456789012345679'))
        self.assertEqual( len(str(prec('10000.1234567890123456789')).split('.')[1]), 18)
        max = '999999999999999999.999999999999999999'
        self.assertEqual(prec(max), Decimal(max))
        self.assertEqual( len(str(prec(max)).split('.')[1]), 18)
        self.assertEqual( len(str(prec(max)).split('.')[0]), 18)
        # double prec
        self.assertEqual( prec(prec('0.123456789012345678')) , Decimal('0.123456789012345678'))
        # rounding up
        self.assertEqual( prec(Decimal('1.10504461') * Decimal('0.97'), 2, 'up') , Decimal('1.08'))
        # rounding down
        self.assertEqual( prec(Decimal('1.10504461') * Decimal('0.97'), 2, 'down') , Decimal('1.07'))
        # to minimum
        self.assertEqual( prec(Decimal('0.00000000000000000001'), 2, 'up') , Decimal('0.01'))

    def test_non_zero_prec(self):
        self.assertEqual(prec((Decimal('0.009366410557787348') * Decimal('0.52')), 2, 'down'), Decimal('0.00'))
        self.assertEqual(non_zero_prec((Decimal('0.009366410557787348') * Decimal('0.52')), 2), Decimal('0.01'))
        
if __name__ == '__main__':
    unittest.main()
