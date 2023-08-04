import asyncio
import sys
import os
import json
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import unittest
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from .MockRequester import MockRequester

class CreateAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_create_asset(self):
        response = await self.requests.make_request('create_asset', {'ticker': "AAPL", "asset_type":'stock', 'qty': 1000, 'seed_price': 50000, 'seed_bid': 0.99, 'seed_ask': 1.01}, self.mock_requester)
        book = self.mock_requester.responder.exchange.books['AAPL'].to_dict()
        self.assertEqual(type(response), dict)
        self.assertEqual(response['type'], "stock")
        self.assertEqual(book['bids'][0]['creator'], 'init_seed_AAPL')
        self.assertEqual(type(book['bids'][0]['id']), str)
        self.assertEqual(book['bids'][0]['price'], 49500)
        self.assertEqual(book['bids'][0]['qty'], 1)
        self.assertEqual(book['bids'][0]['ticker'], 'AAPL')
        self.assertEqual(book['asks'][0]['creator'], 'init_seed_AAPL')
        self.assertEqual(type(book['asks'][0]['id']), str)
        self.assertEqual(book['asks'][0]['price'], 50500)
        self.assertEqual(book['asks'][0]['qty'], 1000)
        self.assertEqual(book['asks'][0]['ticker'], 'AAPL')

class GetOrderBookTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_order_book(self):
        response = await self.requests.make_request('order_book', {'ticker': 'AAPL', 'limit': 2}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(len(response['bids']), 2)
        self.assertEqual(len(response['asks']), 1)
        self.assertEqual(response['bids'][0]['creator'], self.mock_requester.responder.agent)
        self.assertEqual(response['bids'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(type(response['bids'][0]['id']), str)
        self.assertEqual(response['bids'][0]['price'], 149)
        self.assertEqual(response['bids'][0]['qty'], 1)
        self.assertEqual(response['bids'][0]['ticker'], 'AAPL')
        self.assertEqual(response['bids'][1]['creator'], 'init_seed_AAPL')

class GetLatestTradeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_latest_trade(self):
        response = await self.requests.make_request('latest_trade', {'ticker': 'AAPL'}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(response['ticker'], 'AAPL')
        self.assertEqual(response['price'], 150)
        self.assertEqual(response['buyer'], 'init_seed_AAPL')
        self.assertEqual(response['seller'], 'init_seed_AAPL')

class GetTradesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_trades(self):
        response = await self.requests.make_request('trades', {'ticker': 'AAPL', 'limit': 10}, self.mock_requester)
        trades = response
        self.assertEqual(type(trades), list)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['ticker'], 'AAPL')
        self.assertEqual(trades[0]['price'], 150)
        self.assertEqual(trades[0]['buyer'], 'init_seed_AAPL')
        self.assertEqual(trades[0]['seller'], 'init_seed_AAPL')

class GetQuotesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_quotes(self):
        response = await self.requests.make_request('quotes', {'ticker': "AAPL"}, self.mock_requester)
        quotes = response
        self.assertEqual(quotes["ticker"], "AAPL")
        self.assertEqual(quotes["bid_qty"], 1)
        self.assertEqual(quotes["bid_p"], 149)
        self.assertEqual(quotes["ask_qty"], 1000)
        self.assertEqual(quotes["ask_p"], 151.5)

class GetBestBidTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_best_bid(self):
        response = await self.requests.make_request('best_bid', {'ticker': 'AAPL'}, self.mock_requester)
        best_bid = response
        self.assertEqual(best_bid['ticker'], 'AAPL')
        self.assertEqual(best_bid['price'], 149)
        self.assertEqual(best_bid['qty'], 1)
        self.assertEqual(best_bid['creator'], self.mock_requester.responder.agent)

class GetBestAskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_best_ask(self):
        response = await self.requests.make_request('best_ask', {'ticker': 'AAPL'}, self.mock_requester)
        best_ask = response
        self.assertEqual(best_ask['ticker'], 'AAPL')
        self.assertEqual(best_ask['price'], 151.5)
        self.assertEqual(best_ask['qty'], 1000)
        self.assertEqual(best_ask['creator'], 'init_seed_AAPL')

class GetMidPriceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_midprice(self):
        response = await self.requests.make_request('midprice', {'ticker': 'AAPL'}, self.mock_requester)
        midprice = response
        self.assertEqual(midprice["midprice"], 150.25)

class LimitBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_limit_buy(self):
        response = await self.requests.make_request('limit_buy', {'ticker': "AAPL", 'price': 149, 'qty': 2, 'creator': self.mock_requester.responder.agent, 'fee': 0.0}, self.mock_requester)
        order = response
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 149)
        self.assertEqual(order['qty'], 2)
        self.assertEqual(order['creator'], self.mock_requester.responder.agent)
        self.assertEqual(order['fee'], 0.0)

class LimitSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_limit_sell(self):
        response = await self.requests.make_request('limit_sell', {'ticker': "AAPL", 'price': 151.5, 'qty': 1, 'creator': 'init_seed_AAPL', 'fee': 0.0}, self.mock_requester)
        order = response
        self.assertEqual(order['ticker'], "AAPL")
        self.assertEqual(order['price'], 151.5)
        self.assertEqual(order['qty'], 1)
        self.assertEqual(order['creator'], "init_seed_AAPL")
        self.assertEqual(order['fee'], 0.0)

class CancelOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_cancel_order(self):
        order = self.mock_requester.responder.mock_order
        response = await self.requests.make_request('cancel_order', {'order_id': order.id}, self.mock_requester)
        self.assertEqual(response, {'cancelled_order': order.id})

class CancelAllOrdersTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_cancel_all_orders(self):
        response = await self.requests.make_request('cancel_all_orders', {'ticker': 'AAPL', 'agent': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response, {'cancelled_all_orders': 'AAPL'})

class GetPriceBarsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_price_bars(self):
        response = await self.requests.make_request('candles', {'ticker': 'AAPL', 'interval': '1h', 'limit': 10}, self.mock_requester)
        candles = response
        self.assertEqual(type(candles), list)
        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0]['open'], 150)
        self.assertEqual(candles[0]['high'], 150)
        self.assertEqual(candles[0]['low'], 150)
        self.assertEqual(candles[0]['close'], 150)
        self.assertEqual(candles[0]['volume'], 1000)
        self.assertEqual(candles[0]['dt'], '01/01/2023, 00:00:00')

class GetCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_cash(self):
        response = await self.requests.make_request('cash', {'agent': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response, {'cash': 100000})

class GetAssetsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_assets(self):
        response = await self.requests.make_request('assets', {'agent': 'init_seed_AAPL'}, self.mock_requester)
        self.assertEqual(response, {'assets': {'AAPL': 1000}})

class RegisterAgentTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_register_agent(self):
        response = await self.requests.make_request('register_agent', {'name': 'buyer1', 'initial_cash': 100000}, self.mock_requester)
        self.assertEqual('registered_agent' in response, True)
        self.assertEqual(response['registered_agent'][:6], 'buyer1')

class MarketBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_market_buy(self):
        response = await self.requests.make_request('market_buy', {'ticker': 'AAPL', 'qty': 1, 'buyer': self.mock_requester.responder.agent, 'fee': 0.0}, self.mock_requester)
        self.assertEqual(response, {'market_buy': 'AAPL', 'buyer': self.mock_requester.responder.agent, 'fills': [{'qty': 1, 'price': 151.5, 'fee': 0.0}]})

class MarketSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_market_sell(self):
        response = await self.requests.make_request('market_sell', {'ticker': 'AAPL', 'qty': 1, 'seller': 'init_seed_AAPL', 'fee': 0.0}, self.mock_requester)
        self.assertEqual(response, {'market_sell': 'AAPL', 'seller': 'init_seed_AAPL', 'fills': [{'qty': 1, 'price': 149, 'fee': 0.0}]})

class GetMempoolTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def get_mempool(self, limit):
        response = await self.requests.make_request('mempool', {'limit': limit}, self.mock_requester)
        #TODO: implement test

class GetAgentTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agent(self):
        response = await self.requests.make_request('get_agent', {'name': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertDictEqual(response, {'name': self.mock_requester.responder.agent, 'cash': 100000,'_transactions': [], 'positions':[], 'assets': {}})

class GetAgentsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agents(self):
        response = await self.requests.make_request('get_agents', {}, self.mock_requester)
        expected = [
            {'_transactions': [{'cash_flow': -150000, 'dt': '2023-01-01 00:00:00', 'id': 'af33c054-c78e-4379-ad03-8ad952d32581', 'pnl': 0, 'qty': 1000, 'ticker': 'AAPL', 'type': 'buy'}, {'cash_flow': 150000, 'dt': '2023-01-01 00:00:00', 'id': 'e4beb9d1-bf1f-46de-8725-140c7c6e1235', 'pnl': 0, 'qty': -1000, 'ticker': 'AAPL', 'type': 'sell'}], 
            'assets': {'AAPL': 1000}, 
            'cash': 150000, 
            'name': 'init_seed_AAPL', 
            'positions': [{'dt': '2023-01-01 00:00:00', 'enters': [{'cash_flow': -150000, 'dt': '2023-01-01 00:00:00', 'id': 'af33c054-c78e-4379-ad03-8ad952d32581', 'pnl': 0, 'qty': 1000, 'ticker': 'AAPL', 'type': 'buy'}], 'exits': [], 'id': '68217929-ac25-42ff-b786-dfe347a0934b', 'qty': 1000, 'ticker': 'AAPL'}]
            }, 
            {'_transactions': [], 'assets': {}, 'cash': 100000, 'name': 'buyer133e61af4', 'positions': []}
            ]
        self.assertEqual(response[0]['cash'], 150000)
        self.assertEqual(response[0]['name'], 'init_seed_AAPL')
        self.assertEqual(response[0]['assets'], {'AAPL': 1000})
        self.assertEqual(len(response[0]['_transactions']), 2)
        self.assertEqual(response[1]['cash'], 100000)
        self.assertEqual(response[1]['assets'], {})

class AddCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_add_cash(self):
        response = await self.requests.make_request('add_cash', {'agent': self.mock_requester.responder.agent, 'amount': 1000}, self.mock_requester)
        self.assertEqual(response, {'cash': 101000})

class RemoveCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_remove_cash(self):
        response = await self.requests.make_request('remove_cash', {'agent': self.mock_requester.responder.agent, 'amount': 1000}, self.mock_requester)
        self.assertEqual(response, {'cash': 99000})

class GetAgentsHoldingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agents_holding(self):
        response = await self.requests.make_request('get_agents_holding', {'ticker': 'AAPL'}, self.mock_requester)
        self.assertEqual(response, ['init_seed_AAPL'])

class GetAgentsPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agents_positions(self):
        result = await self.requests.make_request('get_agents_positions', {'ticker': None}, self.mock_requester)
        self.assertEqual(len(result[0]['positions']), 1)
        self.assertEqual(result[0]['agent'], 'init_seed_AAPL')
        self.assertEqual(result[0]['positions'][0]['ticker'], 'AAPL')
        self.assertEqual(result[0]['positions'][0]['qty'], 1000)
        self.assertEqual(result[0]['positions'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(result[0]['positions'][0]['enters'][0]['cash_flow'], -150000)
        self.assertEqual(result[0]['positions'][0]['enters'][0]['ticker'], 'AAPL')
        self.assertEqual(result[0]['positions'][0]['enters'][0]['qty'], 1000)
        self.assertEqual(result[0]['positions'][0]['enters'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(result[0]['positions'][0]['enters'][0]['type'], 'buy')
        self.assertEqual(result[0]['agent'], 'init_seed_AAPL')
        self.assertEqual(result[0]['positions'][0]['ticker'], 'AAPL')
        self.assertEqual(result[0]['positions'][0]['qty'], 1000)
        self.assertEqual(result[0]['positions'][0]['dt'], '2023-01-01 00:00:00')

class GetAgentSimpleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)
    
    async def test_get_agent_simple(self):
        result = await self.requests.make_request('get_agents_simple', {'name': 'init_seed_AAPL'}, self.mock_requester)
        print(result)
        self.assertCountEqual(result, [{'agent': 'init_seed_AAPL', 'assets': {'AAPL': 1000}, 'cash': 150000}, {'agent': self.mock_requester.responder.agent, 'assets': {}, 'cash': 100000}])

class GetPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_positions(self):
        result = await self.requests.make_request('get_positions', {'agent': self.mock_requester.responder.agent, 'page_size': 10, 'page': 1}, self.mock_requester)
        self.assertEqual(result['agent'], self.mock_requester.responder.agent)
        self.assertEqual(result['positions'] , [])
        self.assertEqual(result['total_positions'] , 0)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['total_pages'], 0)
        self.assertEqual(result['next_page'], None)
        self.assertEqual(result['page_size'], 10)

if __name__ == '__main__':
    asyncio.run(unittest.main())