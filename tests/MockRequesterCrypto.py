import random, string, os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange
from source.utils._utils import dumps
from datetime import datetime


class MockRequesterCrypto():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponderCrypto()

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)

class MockResponderCrypto():
    """
    Mocked run_exchange and run_company callback responder
    """
    def __init__(self):
        self.time = datetime(2023, 1, 1)
        self.exchange = Exchange(datetime=self.time)
        self.agent = None
        self.mock_order = None


    async def init(self):
        await self.exchange.create_asset("BTC", pairs = [], seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("buyer1", {"USD": 100000}))['registered_agent']
        self.mock_order = await self.exchange.limit_buy("BTC", "USD", price=151, qty=1, creator=self.agent)
                
    async def callback(self, msg):
        if msg['topic'] == 'create_asset': return dumps((await self.exchange.create_asset(msg['symbol'], msg['pairs'] ,msg['qty'], msg['seed_price'], msg['seed_bid'], msg['seed_ask'])))
        elif msg['topic'] == 'sim_time': return dumps(self.exchange.datetime)
        elif msg['topic'] == 'get_tickers': return dumps((await self.exchange.get_tickers()))
        elif msg['topic'] == 'limit_buy': return dumps((await self.exchange.limit_buy(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'limit_sell': return dumps((await self.exchange.limit_sell(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'market_buy': return await self.exchange.market_buy(msg['base'] , msg['quote'], msg['qty'], msg['buyer'], msg['fee'])
        elif msg['topic'] == 'market_sell': return await self.exchange.market_sell(msg['base'] , msg['quote'], msg['qty'], msg['seller'], msg['fee'])
        elif msg['topic'] == 'cancel_order': return await self.exchange.cancel_order(msg['base'] , msg['quote'], msg['order_id'])
        elif msg['topic'] == 'cancel_all_orders': return await self.exchange.cancel_all_orders(msg['base'] , msg['quote'], msg['agent'])
        elif msg['topic'] == 'candles': return dumps(await self.exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit']))
        # elif msg['topic'] == 'mempool': return await self.exchange.mempool(msg['limit'])
        elif msg['topic'] == 'order_book': return dumps( (await self.exchange.get_order_book(msg['ticker'])).to_dict(msg['limit']))
        elif msg['topic'] == 'latest_trade': return dumps(await self.exchange.get_latest_trade(msg['base'] , msg['quote']))
        elif msg['topic'] == 'trades': return dumps( await self.exchange.get_trades(msg['base'] , msg['quote'], msg['limit']))
        elif msg['topic'] == 'quotes': return await self.exchange.get_quotes(msg['ticker'])
        elif msg['topic'] == 'best_bid': return dumps((await self.exchange.get_best_bid(msg['ticker'])).to_dict())
        elif msg['topic'] == 'best_ask': return dumps((await self.exchange.get_best_ask(msg['ticker'])).to_dict())
        elif msg['topic'] == 'midprice': return dumps(await self.exchange.get_midprice(msg['ticker']))
        elif msg['topic'] == 'cash': return await self.exchange.get_cash(msg['agent'])
        elif msg['topic'] == 'assets': return await self.exchange.get_assets(msg['agent'])
        elif msg['topic'] == 'register_agent': return await self.exchange.register_agent(msg['name'], msg['initial_assets'])
        elif msg['topic'] == 'get_agent': return dumps(await self.exchange.get_agent(msg['name']))
        elif msg['topic'] == 'get_agents': return dumps(await self.exchange.get_agents())
        elif msg['topic'] == 'add_cash': return dumps(await self.exchange.add_cash(msg['agent'], msg['amount'], msg['note']))
        elif msg['topic'] == 'remove_cash': return dumps(await self.exchange.remove_cash(msg['agent'], msg['amount']))
        elif msg['topic'] == 'get_cash': return dumps(await self.exchange.get_cash(msg['agent']))
        elif msg['topic'] == 'get_assets': return dumps(await self.exchange.get_assets(msg['agent']))
        elif msg['topic'] == 'get_agents_holding': return dumps(await self.exchange.get_agents_holding(msg['asset']))
        elif msg['topic'] == 'get_agents_positions': return dumps(await self.exchange.get_agents_positions(msg['ticker']))
        elif msg['topic'] == 'get_agents_simple': return dumps(await self.exchange.get_agents_simple())
        elif msg['topic'] == 'get_positions': return dumps(await self.exchange.get_positions(msg['agent'], msg['page_size'], msg['page']))
        elif msg['topic'] == 'get_outstanding_shares': return dumps(await self.exchange.get_outstanding_shares(msg['ticker']))
        elif msg['topic'] == 'get_taxable_events': return dumps(await self.exchange.get_taxable_events())
        #TODO: exchange topic to get general exchange data
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})