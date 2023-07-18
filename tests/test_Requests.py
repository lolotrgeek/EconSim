import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import unittest
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from .MockRequester import MockRequester

class RequestsTests(unittest.TestCase):

    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def tearDown(self) -> None:
        self.mock_requester = None
        self.requests = None

    def test_make_request_success(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        response = {"result": "success"}
        self.mock_requester.request = lambda msg : response

        result = self.requests.make_request(topic, message, None)
        self.assertEqual(result, response)

    def test_make_request_string_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        response = '{"result": "success"}'
        self.mock_requester.request = lambda msg : response

        result = self.requests.make_request(topic, message, None)

        self.assertEqual(result, {"result": "success"})

    def test_make_request_list_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        response = ["result1", "result2"]
        self.mock_requester.request = lambda msg : response

        result = self.requests.make_request(topic, message, None)

        self.assertEqual(result, response)

    def test_make_request_error_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        response = {"error": "request failed"}
        self.mock_requester.request = lambda msg : response

        with self.assertRaises(Exception) as context:
            result = self.requests.make_request(topic, message, None)
            self.assertEqual(result, response)

    def test_make_request_none_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        self.mock_requester.request = lambda msg : None

        with self.assertRaises(Exception) as context:
            result = self.requests.make_request(topic, message, None)
            self.assertEqual(result, '[Request Error] test_topic is None, None')

    def test_make_request_no_dict_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        self.mock_requester.request = lambda msg : float(1)

        with self.assertRaises(Exception) as context:
            result = self.requests.make_request(topic, message, None)
            self.assertEqual(result, '[Request Error] test_topic got type float expected dict. 1')

    def test_make_request_returns_dict(self):
        topic = 'candles'
        message = {'ticker': 'BTC', 'interval': '1h', 'limit': 10}
        factory = self.mock_requester.request = lambda msg: {'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5, 'timestamp': 6}

        result = self.requests.make_request(topic, message, factory)

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5, 'timestamp': 6})

class CreateAssetTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_create_asset(self):
        response = self.requests.make_request('create_asset', {'ticker': "AAPL", 'qty': 1000, 'seed_price': 50000, 'seed_bid': 0.99, 'seed_ask': 1.01}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(response['bids'][0]['creator'], 'init_seed')
        self.assertEqual(response['bids'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(type(response['bids'][0]['id']), str)
        self.assertEqual(response['bids'][0]['price'], 49500)
        self.assertEqual(response['bids'][0]['qty'], 1)
        self.assertEqual(response['bids'][0]['ticker'], 'AAPL')
        self.assertEqual(response['asks'][0]['creator'], 'init_seed')
        self.assertEqual(response['asks'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(type(response['asks'][0]['id']), str)
        self.assertEqual(response['asks'][0]['price'], 50500)
        self.assertEqual(response['asks'][0]['qty'], 1000)
        self.assertEqual(response['asks'][0]['ticker'], 'AAPL')


class GetOrderBookTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_order_book(self):
        response = self.requests.make_request('order_book', {'ticker': 'AAPL'}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(len(response['bids']), 2)
        self.assertEqual(len(response['asks']), 1)
        self.assertEqual(response['bids'][0]['creator'], self.mock_requester.responder.agent)
        self.assertEqual(response['bids'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(type(response['bids'][0]['id']), str)
        self.assertEqual(response['bids'][0]['price'], 149)
        self.assertEqual(response['bids'][0]['qty'], 1)
        self.assertEqual(response['bids'][0]['ticker'], 'AAPL')
        self.assertEqual(response['bids'][1]['creator'], 'init_seed')

class GetLatestTradeTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_latest_trade(self):
        response = self.requests.make_request('latest_trade', {'ticker': 'AAPL'}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(response['ticker'], 'AAPL')
        self.assertEqual(response['price'], 150)
        self.assertEqual(response['buyer'], 'init_seed')
        self.assertEqual(response['seller'], 'init_seed')

class GetTradesTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_trades(self):
        response = self.requests.make_request('trades', {'ticker': 'AAPL', 'limit': 10}, self.mock_requester)
        trades = response
        self.assertEqual(type(trades), list)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['ticker'], 'AAPL')
        self.assertEqual(trades[0]['price'], 150)
        self.assertEqual(trades[0]['buyer'], 'init_seed')
        self.assertEqual(trades[0]['seller'], 'init_seed')

class GetQuotesTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_quotes(self):
        response = self.requests.make_request('quotes', {'ticker': "AAPL"}, self.mock_requester)
        quotes = response
        self.assertEqual(quotes["ticker"], "AAPL")
        self.assertEqual(quotes["bid_qty"], 1)
        self.assertEqual(quotes["bid_p"], 149)
        self.assertEqual(quotes["ask_qty"], 1000)
        self.assertEqual(quotes["ask_p"], 151.5)

class GetBestBidTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_best_bid(self):
        response = self.requests.make_request('best_bid', {'ticker': 'AAPL'}, self.mock_requester)
        best_bid = response
        self.assertEqual(best_bid['ticker'], 'AAPL')
        self.assertEqual(best_bid['price'], 149)
        self.assertEqual(best_bid['qty'], 1)
        self.assertEqual(best_bid['creator'], self.mock_requester.responder.agent)

class GetBestAskTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_best_ask(self):
        response = self.requests.make_request('best_ask', {'ticker': 'AAPL'}, self.mock_requester)
        best_ask = response
        self.assertEqual(best_ask['ticker'], 'AAPL')
        self.assertEqual(best_ask['price'], 151.5)
        self.assertEqual(best_ask['qty'], 1000)
        self.assertEqual(best_ask['creator'], 'init_seed')

class GetMidPriceTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_midprice(self):
        response = self.requests.make_request('midprice', {'ticker': 'AAPL'}, self.mock_requester)
        midprice = response
        self.assertEqual(midprice["midprice"], 150.25)

class LimitBuyTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_limit_buy(self):
        response = self.requests.make_request('limit_buy', {'ticker': "AAPL", 'price': 149, 'qty': 2, 'creator': self.mock_requester.responder.agent, 'fee': 0.0}, self.mock_requester)
        order = response
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 149)
        self.assertEqual(order['qty'], 2)
        self.assertEqual(order['creator'], self.mock_requester.responder.agent)
        self.assertEqual(order['fee'], 0.0)

class LimitSellTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_limit_sell(self):
        response = self.requests.make_request('limit_sell', {'ticker': "AAPL", 'price': 151.5, 'qty': 1000, 'creator': 'init_seed', 'fee': 0.0}, self.mock_requester)
        order = response
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 151.5)
        self.assertEqual(order['qty'], 1000)
        self.assertEqual(order['creator'], "init_seed")
        self.assertEqual(order['fee'], 0.0)

class CancelOrderTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_cancel_order(self):
        order = self.mock_requester.responder.mock_order
        response = self.requests.make_request('cancel_order', {'order_id': order.id}, self.mock_requester)
        self.assertEqual(response, {'cancelled_order': order.id})

class CancelAllOrdersTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_cancel_all_orders(self):
        response = self.requests.make_request('cancel_all_orders', {'ticker': 'AAPL', 'agent': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response, {'cancelled_all_orders': 'AAPL'})

class GetPriceBarsTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_price_bars(self):
        response = self.requests.make_request('candles', {'ticker': 'AAPL', 'interval': '1h', 'limit': 10}, self.mock_requester)
        candles = response
        self.assertEqual(type(candles), list)
        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0]['open'], 150)
        self.assertEqual(candles[0]['high'], 150)
        self.assertEqual(candles[0]['low'], 150)
        self.assertEqual(candles[0]['close'], 150)
        self.assertEqual(candles[0]['volume'], 1000)
        self.assertEqual(candles[0]['dt'], '01/01/2023, 00:00:00')

class GetCashTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_cash(self):
        response = self.requests.make_request('cash', {'agent': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response, {'cash': 100000})

class GetAssetsTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_assets(self):
        response = self.requests.make_request('assets', {'agent': 'init_seed'}, self.mock_requester)
        self.assertEqual(response, {'assets': {'AAPL': 1000}})

class RegisterAgentTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_register_agent(self):
        response = self.requests.make_request('register_agent', {'name': 'buyer1', 'initial_cash': 100000}, self.mock_requester)
        self.assertEqual('registered_agent' in response, True)
        self.assertEqual(response['registered_agent'][:6], 'buyer1')

class MarketBuyTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_market_buy(self):
        response = self.requests.make_request('market_buy', {'ticker': 'AAPL', 'qty': 1, 'buyer': self.mock_requester.responder.agent, 'fee': 0.0}, self.mock_requester)
        self.assertEqual(response, {'market_buy': 'AAPL', 'buyer': self.mock_requester.responder.agent, 'fills': [{'qty': 1, 'price': 151.5, 'fee': 0.0}]})

class MarketSellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_market_sell(self):
        response = self.requests.make_request('market_sell', {'ticker': 'AAPL', 'qty': 1, 'seller': 'init_seed', 'fee': 0.0}, self.mock_requester)
        self.assertEqual(response, {'market_sell': 'AAPL', 'seller': 'init_seed', 'fills': [{'qty': 1, 'price': 149, 'fee': 0.0}]})

class GetMempoolTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def get_mempool(self, limit):
        response = self.requests.make_request('mempool', {'limit': limit}, self.mock_requester)
        #TODO: implement test
        print(response)

class GetAgentTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_agent(self):
        response = self.requests.make_request('get_agent', {'name': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertDictEqual(response, {'name': self.mock_requester.responder.agent, 'cash': 100000,'_transactions': [], 'assets': {}})

class GetAgentsTest(unittest.TestCase):
    def setUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)

    def test_get_agents(self):
        response = self.requests.make_request('get_agents', {}, self.mock_requester)
        expected = [
            {
                '_transactions': 
                    [
                        {'cash_flow': -150000, 'dt': '2023-01-01 00:00:00', 'qty': 1000, 'ticker': 'AAPL', 'type': 'buy'}, 
                        {'cash_flow': 150000, 'dt': '2023-01-01 00:00:00', 'qty': -1000, 'ticker': 'AAPL', 'type': 'sell'}
                    ],
                'assets': {'AAPL': 1000}, 'cash': 150000, 'name': 'init_seed'
            }, 
            {'_transactions': [], 'assets': {}, 'cash': 100000, 'name': self.mock_requester.responder.agent}
        ]
        self.assertEqual(response, expected)        

if __name__ == '__main__':
    unittest.main()