import asyncio,sys,os
from decimal import Decimal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import unittest
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests as Requests
from .MockRequesterCrypto import MockRequesterCryptoExchange as MockRequester

class CreateAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_create_asset(self):
        response = await self.requests.make_request('create_asset', {'symbol': "ETH", 'pairs': [{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}]}, self.mock_requester)
       
     
        print (response)
        await self.mock_requester.responder.exchange.next()
        
        book = self.mock_requester.responder.exchange.books['ETHUSD'].to_dict()
        self.assertEqual(type(response), dict)
        self.assertEqual(response['asset_created'], 'ETH')
        self.assertEqual(response['pairs'][0]['asset'], 'USD')
        self.assertEqual(type(book['bids'][0]['id']), str)
        self.assertEqual(book['bids'][0]['price'], Decimal('99.00'))
        self.assertEqual(book['bids'][0]['qty'],Decimal('1')) 
        self.assertEqual(book['bids'][0]['ticker'], 'ETHUSD')
        self.assertEqual(type(book['asks'][0]['id']), str)
        self.assertEqual(book['asks'][0]['price'], Decimal('101.00') )
        self.assertEqual(book['asks'][0]['qty'], Decimal('49899.999999999'))
        self.assertEqual(book['asks'][0]['ticker'], 'ETHUSD')

class GetOrderBookTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_order_book(self):
        response = await self.requests.make_request('order_book', {'ticker': 'BTCUSD', 'limit': 2}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(len(response['bids']), 2) # NOTE: this is 2 because we have a mock_order in the self.mock_requester_init() method called here in the asyncSetUp() method
        self.assertEqual(len(response['asks']), 1)
        self.assertEqual(response['bids'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(type(response['bids'][0]['id']), str)
        self.assertEqual(response['bids'][0]['price'], '151')
        self.assertEqual(response['bids'][0]['qty'], '1')
        self.assertEqual(response['bids'][0]['ticker'], 'BTCUSD')

class GetLatestTradeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_latest_trade(self):
        response = await self.requests.make_request('latest_trade', {'base': 'BTC', 'quote': 'USD'}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(response['base'], 'BTC')
        self.assertEqual(response['quote'], 'USD')
        self.assertEqual(response['price'], '150')
        self.assertEqual(response['buyer'], 'init_seed_BTCUSD')
        self.assertEqual(response['seller'], 'init_seed_BTCUSD')

class GetTradesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_trades(self):
        response = await self.requests.make_request('trades', {'base': 'BTC', 'quote': 'USD', 'limit': 10}, self.mock_requester)
        trades = response
        self.assertEqual(type(trades), list)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['base'], 'BTC')
        self.assertEqual(trades[0]['quote'], 'USD')
        self.assertEqual(trades[0]['price'], '150')
        self.assertEqual(trades[0]['buyer'], 'init_seed_BTCUSD')
        self.assertEqual(trades[0]['seller'], 'init_seed_BTCUSD')

class GetQuotesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_quotes(self):
        response = await self.requests.make_request('quotes', {'ticker': "BTCUSD"}, self.mock_requester)
        quotes = response
        self.assertEqual(quotes["ticker"], "BTCUSD")
        self.assertEqual(quotes["bid_qty"], 1)
        self.assertEqual(quotes["bid_p"], 151)
        self.assertEqual(quotes["ask_qty"], Decimal('997.999999999'))
        self.assertEqual(quotes["ask_p"], 151.5)

class GetBestBidTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_best_bid(self):
        response = await self.requests.make_request('best_bid', {'ticker': "BTCUSD"}, self.mock_requester)
        best_bid = response
        self.assertEqual(best_bid['ticker'], 'BTCUSD')
        self.assertEqual(best_bid['price'], '151')
        self.assertEqual(best_bid['qty'], '1')

class GetBestAskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_best_ask(self):
        response = await self.requests.make_request('best_ask', {'ticker': "BTCUSD"}, self.mock_requester)
        best_ask = response
        self.assertEqual(best_ask['ticker'], 'BTCUSD')
        self.assertEqual(best_ask['price'], '151.50')
        self.assertEqual(best_ask['qty'], '997.999999999')

class GetMidPriceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_midprice(self):
        response = await self.requests.make_request('midprice', {'ticker': "BTCUSD"}, self.mock_requester)
        midprice = response
        self.assertEqual(midprice, '151.25')

class LimitBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_limit_buy(self):
        response = await self.requests.make_request('limit_buy', {'base': "BTC", 'quote': "USD", 'price': 149, 'qty': 2, 'creator': self.mock_requester.responder.agent, 'fee': 0.001}, self.mock_requester)
        order = response
        self.assertEqual(order['ticker'], "BTCUSD")
        self.assertEqual(order['price'], '149')
        self.assertEqual(order['qty'], '2')
        self.assertEqual(order['creator'], self.mock_requester.responder.agent)
        self.assertEqual(order['network_fee'], '0.001')
        self.assertEqual(order['exchange_fee'], '0.002')
        self.assertEqual(order['status'], 'open')

class LimitSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_limit_sell(self):
        response = await self.requests.make_request('limit_sell', {'base': "BTC", 'quote': "USD", 'price': 151.5, 'qty': 1, 'creator': 'init_seed_BTCUSD', 'fee': 0.001}, self.mock_requester)
        order = response
        print(response)
        self.assertEqual(order['ticker'], "BTCUSD")
        self.assertEqual(order['price'], '151.5')
        self.assertEqual(order['qty'], '1')
        self.assertEqual(order['creator'], 'init_seed_BTCUSD')
        self.assertEqual(order['network_fee'], '0.001')
        self.assertEqual(order['exchange_fee'], '0.1515')
        self.assertEqual(order['status'], 'open')

class CancelOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_cancel_order(self):
        order = self.mock_requester.responder.mock_order
        response = await self.requests.make_request('cancel_order', {'base': "BTC", 'quote': "USD", 'order_id': order.id}, self.mock_requester)
        self.assertEqual(type(response), dict)
        self.assertEqual(type(response['cancelled_order']), dict)
        self.assertEqual(response['cancelled_order'], order.to_dict_full())

class CancelAllOrdersTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_cancel_all_orders(self):
        order = self.mock_requester.responder.mock_order
        response = await self.requests.make_request('cancel_all_orders', {'base': "BTC", 'quote': "USD", 'agent': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response, {'cancelled_orders': [order.id]})

class GetPriceBarsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_price_bars(self):
        response = await self.requests.make_request('candles', {'ticker': "BTCUSD", 'interval': '1H', 'limit': 10}, self.mock_requester)
        candles = response
        self.assertEqual(type(candles), list)
        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0]['open'], '150')
        self.assertEqual(candles[0]['high'], '150')
        self.assertEqual(candles[0]['low'], '150')
        self.assertEqual(candles[0]['close'], '150')
        self.assertEqual(candles[0]['volume'], '1000')
        self.assertEqual(candles[0]['dt'], '2023-01-01 00:00:00')

class GetCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_cash(self):
        response = await self.requests.make_request('cash', {'agent': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response, {'cash': Decimal('99848.9999')}) #NOTE: this is 99848.9999 because we have assets frozen in our mock_order

class GetAssetsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_assets(self):
        response = await self.requests.make_request('assets', {'agent': 'init_seed_BTCUSD'}, self.mock_requester)
        self.assertEqual(response, {'assets': {'BTC': Decimal('2.000000000'), 'USD': Decimal('149851.499999999')}, 'frozen_assets': {'BTC': Decimal('998.000100000'),'USD': Decimal('148.500100001')}})

class RegisterAgentTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_register_agent(self):
        response = await self.requests.make_request('register_agent', {'name': 'buyer1', 'initial_assets':{"USD": 100000}}, self.mock_requester)
        self.assertEqual('registered_agent' in response, True)
        self.assertEqual(response['registered_agent'][:6], 'buyer1')

class MarketBuyTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_market_buy(self):
        response = await self.requests.make_request('market_buy', {'base': "BTC", 'quote': "USD", 'qty': 1, 'buyer': self.mock_requester.responder.agent, 'fee': 0.001}, self.mock_requester)
        print(response)
        self.assertEqual(response, {'market_buy': 'BTCUSD', 'buyer': self.mock_requester.responder.agent, 'qty': Decimal('1'), 'fills': [{'qty': Decimal('1'), 'price': Decimal('151.50'), 'fee': Decimal('0.002')}]})

class MarketSellTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_market_sell(self):
        response = await self.requests.make_request('market_sell', {'base': "BTC", 'quote': "USD", 'qty': 1, 'seller': 'init_seed_BTCUSD', 'fee': 0.001}, self.mock_requester)
        print(response)
        self.assertEqual(response, {'market_sell': 'BTCUSD', 'seller': 'init_seed_BTCUSD', 'qty': Decimal('1'), 'fills': [{'qty': Decimal('1'), 'price': Decimal('151'), 'fee': Decimal('0.002')}]})

class GetAgentTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agent(self):
        response = await self.requests.make_request('get_agent', {'name': self.mock_requester.responder.agent}, self.mock_requester)
        self.assertEqual(response['name'], self.mock_requester.responder.agent)
        self.assertEqual(response['_transactions'], [])
        self.assertEqual(len(response['positions']), 1)
        self.assertEqual(response['positions'][0]['qty'], '100000')
        self.assertEqual(len (response['positions'][0]['enters']), 1)
        self.assertEqual(response['positions'][0]['exits'], [])
        self.assertEqual(response['positions'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(response['assets'], {'USD' : '99848.9999'})
        self.assertEqual(response['frozen_assets'], {'USD': '151.0001'})
        self.assertEqual(response['_transactions'], [])

class GetAgentsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agents(self):
        response = await self.requests.make_request('get_agents', {}, self.mock_requester)
        print(response)
        self.assertEqual(response[0]['name'], 'init_seed_BTCUSD')
        self.assertEqual(len(response[0]['_transactions']), 0)
        self.assertEqual(response[1]['assets'], {'USD': '99848.9999'})

class AddCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_add_cash(self):
        response = await self.requests.make_request('add_cash', {'agent': self.mock_requester.responder.agent, 'amount': 1000, 'note': 'test'}, self.mock_requester)
        self.assertEqual(response, {'USD': '100848.9999'})

class RemoveCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_remove_cash(self):
        response = await self.requests.make_request('remove_cash', {'agent': self.mock_requester.responder.agent, 'amount': 1000}, self.mock_requester)
        self.assertEqual(response, {'USD': '98848.9999'})

class GetAgentsHoldingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agents_holding(self):
        response = await self.requests.make_request('get_agents_holding', {'asset': "BTC"}, self.mock_requester)
        for agent in self.mock_requester.responder.exchange.agents: 
            print("-----------------------")
            print(agent['name'], agent['assets'])
        self.assertEqual(response, ['init_seed_BTCUSD'])

class GetAgentsPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_agents_positions(self):
        result = await self.requests.make_request('get_agents_positions', {'ticker': None}, self.mock_requester)
        for position in result:
            print("-----------------------")
            print(position)
        self.assertEqual(len(result[0]['positions']), 1)
        self.assertEqual(result[0]['agent'], 'init_seed_BTCUSD')
        self.assertEqual(result[0]['positions'][0]['asset'], 'BTC')
        self.assertEqual(result[0]['positions'][0]['qty'], '150000')
        self.assertEqual(result[0]['positions'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(result[0]['positions'][0]['enters'], [])
        self.assertEqual(result[0]['positions'][0]['exits'], [])
        self.assertEqual(result[1]['agent'], self.mock_requester.responder.agent)
        self.assertEqual(result[1]['positions'][0]['asset'], 'USD')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['initial_qty'], '100000')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['qty'], '100000')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(result[1]['positions'][0]['exits'], [])
        self.assertEqual(result[0]['positions'][0]['dt'], '2023-01-01 00:00:00')

class GetAgentSimpleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)
    
    async def test_get_agent_simple(self):
        result = await self.requests.make_request('get_agents_simple', {'name': 'init_seed_BTCUSD'}, self.mock_requester)
        self.assertCountEqual(result, [{'agent': 'init_seed_BTCUSD', 'assets': {'BTC': '2.000000000', 'USD': '149851.499999999'}}, {'agent': self.mock_requester.responder.agent, 'assets': {'USD': '99848.9999'}}])

class getTaxableEventsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_taxable_events(self):
        result = await self.requests.make_request('get_taxable_events', {}, self.mock_requester)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)       

class GetPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        await self.mock_requester.init()
        self.requests = Requests(self.mock_requester)

    async def test_get_positions(self):
        result = await self.requests.make_request('get_positions', {'agent': self.mock_requester.responder.agent, 'page_size': 10, 'page': 1}, self.mock_requester)
        self.assertEqual(result['agent'], self.mock_requester.responder.agent)
        self.assertEqual(result['positions'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(result['positions'][0]['asset'], 'USD')
        self.assertEqual(result['positions'][0]['qty'], '100000')
        self.assertEqual(result['positions'][0]['enters'][0]['asset'], 'USD' )
        self.assertEqual(result['positions'][0]['enters'][0]['qty'], '100000')
        self.assertEqual(result['positions'][0]['enters'][0]['initial_qty'], '100000')
        self.assertEqual(result['positions'][0]['enters'][0]['dt'], '2023-01-01 00:00:00')
        self.assertEqual(result['positions'][0]['exits'], [])
        self.assertEqual(result['total_positions'] , 1)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['total_pages'], 1)
        self.assertEqual(result['next_page'], None)
        self.assertEqual(result['page_size'], 10)

if __name__ == '__main__':
    asyncio.run(unittest.main())