import asyncio
import unittest
import pandas as pd
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.exchange.types.OrderSide import OrderSide
from source.exchange.types.OrderBook import OrderBook
from source.exchange.types.LimitOrder import LimitOrder
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
    asyncio.run(unittest.main())
