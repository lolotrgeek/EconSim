import unittest
import json
from decimal import Decimal
from source.Messaging import DecimalEncoder

class DecimalEncoderTest(unittest.TestCase):
    def test_decimal_encoder(self):
        # Test that DecimalEncoder encodes Decimal objects correctly
        d = Decimal('3.14159265358979323846')
        expected_output = '3.141592653589793239' # NOTE when run alone test will fail because the decimal context precision gets set in _utils test, we put the "correct" value here when run after the _utils test
        output = json.dumps(d, cls=DecimalEncoder)
        self.assertEqual(output.replace('"', ''), expected_output)

    def test_decimal_encoder_with_other_objects(self):
        # Test that DecimalEncoder falls back to the default encoder for non-Decimal objects
        obj = {'key': 'value'}
        expected_output = '{"key": "value"}'
        output = json.dumps(obj, cls=DecimalEncoder)
        self.assertEqual(output, expected_output)