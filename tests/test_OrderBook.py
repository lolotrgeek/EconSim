
import unittest
import pandas as pd
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.types.OrderSide import OrderSide
from source.types.OrderBook import OrderBook
from source.types.LimitOrder import LimitOrder
class OrderBookTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.maxDiff = None

    def setUp(self):
        self.order_book = OrderBook("AAPL")

    def test_order_book_ticker(self):
        self.assertEqual(self.order_book.ticker, "AAPL")

    def test_order_book_repr(self):
        expected_repr = "<OrderBook: AAPL>"
        self.assertEqual(repr(self.order_book), expected_repr)

    def test_order_book_str(self):
        expected_str = "<OrderBook: AAPL>"
        self.assertEqual(str(self.order_book), expected_str)

    def test_order_book_df(self):
        test_order1 = LimitOrder("AAPL", 150.0, 100, "Creator1", OrderSide.BUY)
        test_order1.id = "id1"
        test_order1.dt = "dt1"
        test_order2 = LimitOrder("AAPL", 140.0, 200, "Creator2", OrderSide.BUY)
        test_order2.id = "id2"
        test_order2.dt = "dt2"
        test_order3 = LimitOrder("AAPL", 160.0, 50, "Creator3", OrderSide.SELL)
        test_order3.id = "id3"
        test_order3.dt = "dt3"
        test_order4 = LimitOrder("AAPL", 170.0, 75, "Creator4", OrderSide.SELL)
        test_order4.id = "id4"
        test_order4.dt = "dt4"
        self.order_book.bids = [
            test_order1,
            test_order2
        ]
        self.order_book.asks = [
            test_order3,
            test_order4
        ]
        print(self.order_book.df)
        expected_df = {
            'bids': pd.DataFrame({
                'id': ['id1', 'id2'],
                'ticker': ['AAPL', 'AAPL'],
                'price': [150.0, 140.0],
                'fee' : [0, 0],
                'qty': [100, 200],
                'creator': ['Creator1', 'Creator2'],
                'dt': ['dt1', 'dt2'],
                'type': ['limit_buy', 'limit_buy']
            }),
            'asks': pd.DataFrame({
                'id': ['id3', 'id4'],
                'ticker': ['AAPL', 'AAPL'],
                'price': [160.0, 170.0],
                'fee' : [0, 0],
                'qty': [50, 75],
                'creator': ['Creator3', 'Creator4'],
                'dt': ['dt3', 'dt4'],
                'type': ['limit_sell', 'limit_sell']
            })
        }
        self.assertDictEqual(self.order_book.df['bids'].to_dict(), expected_df['bids'].to_dict())
        self.assertDictEqual(self.order_book.df['asks'].to_dict(), expected_df['asks'].to_dict())

    def test_order_book_to_dict(self):
        self.order_book.bids = [
            LimitOrder("AAPL",  150.0, 100, "Creator1", OrderSide.BUY),
            LimitOrder("AAPL",  140.0, 200, "Creator2", OrderSide.BUY)
        ]
        self.order_book.asks = [
            LimitOrder("AAPL", 160.0, 50, "Creator3", OrderSide.SELL),
            LimitOrder("AAPL", 170.0, 75, "Creator4", OrderSide.SELL)
        ]
        expected_dict = {
            "bids": [
                {'ticker': 'AAPL', 'qty': 100,
                    'price': 150.0, 'creator': 'Creator1', },
                {'ticker': 'AAPL', 'qty': 200,
                    'price': 140.0, 'creator': 'Creator2', }
            ],
            "asks": [
                {'ticker': 'AAPL', 'qty': 50, 'price': 160.0, 'creator': 'Creator3', },
                {'ticker': 'AAPL', 'qty': 75, 'price': 170.0, 'creator': 'Creator4', }
            ]
        }
        # check if the expected_dict has the same keys of the objects in the bids and asks lists, does not need to be perfectlly equal
        orderbook_dict = self.order_book.to_dict()
        for index, bid in enumerate(expected_dict['bids']):
            self.assertEqual(
                bid['ticker'], orderbook_dict['bids'][index]['ticker'])
            self.assertEqual(bid['qty'], orderbook_dict['bids'][index]['qty'])
            self.assertEqual(
                bid['price'], orderbook_dict['bids'][index]['price'])
            self.assertEqual(
                bid['creator'], orderbook_dict['bids'][index]['creator'])
            self.assertIn('id', orderbook_dict['bids'][index].keys())
            self.assertIn('dt', orderbook_dict['bids'][index].keys())
        for index, ask in enumerate(expected_dict['asks']):
            self.assertEqual(
                ask['ticker'], orderbook_dict['asks'][index]['ticker'])
            self.assertEqual(ask['qty'], orderbook_dict['asks'][index]['qty'])
            self.assertEqual(
                ask['price'], orderbook_dict['asks'][index]['price'])
            self.assertEqual(
                ask['creator'], orderbook_dict['asks'][index]['creator'])
            self.assertIn('id', orderbook_dict['asks'][index].keys())
            self.assertIn('dt', orderbook_dict['asks'][index].keys())


if __name__ == '__main__':
    unittest.main()
