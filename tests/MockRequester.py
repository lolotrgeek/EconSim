import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Exchange import Exchange
from source.utils._utils import dumps
from datetime import datetime


class MockRequester():
    def __init__(self):
        self.responder = MockResponder()
    
    def request(self, msg):
        return self.responder.callback(msg)

class MockResponder():
    def __init__(self):
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = self.exchange.register_agent("buyer1", 100000)['registered_agent']
        self.mock_order = self.exchange.limit_buy("AAPL", price=149, qty=1, creator=self.agent)


    def callback(self, msg):
        if msg['topic'] == 'create_asset': return dumps(self.exchange.create_asset(msg['ticker'], msg['qty'], msg['seed_price'], msg['seed_bid'], msg['seed_ask']).to_dict())
        elif msg['topic'] == 'limit_buy': return dumps(self.exchange.limit_buy(msg['ticker'], msg['price'], msg['qty'], msg['creator'], msg['fee']).to_dict())
        elif msg['topic'] == 'limit_sell': return dumps(self.exchange.limit_sell(msg['ticker'], msg['price'], msg['qty'], msg['creator'], msg['fee']).to_dict())
        elif msg['topic'] == 'market_buy': return self.exchange.market_buy(msg['ticker'], msg['qty'], msg['buyer'], msg['fee'])
        elif msg['topic'] == 'market_sell': return self.exchange.market_sell(msg['ticker'], msg['qty'], msg['seller'], msg['fee'])
        elif msg['topic'] == 'cancel_order': return self.exchange.cancel_order(msg['order_id'])
        elif msg['topic'] == 'cancel_all_orders': return self.exchange.cancel_all_orders(msg['agent'], msg['ticker'])
        elif msg['topic'] == 'candles': return self.exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit'])
        # elif msg['topic'] == 'mempool': return self.exchange.mempool(msg['limit'])
        elif msg['topic'] == 'order_book': return dumps(self.exchange.get_order_book(msg['ticker']).to_dict())
        elif msg['topic'] == 'latest_trade': return dumps(self.exchange.get_latest_trade(msg['ticker']))
        elif msg['topic'] == 'trades': return dumps(self.exchange.get_trades(msg['ticker']))
        elif msg['topic'] == 'quotes': return self.exchange.get_quotes(msg['ticker'])
        elif msg['topic'] == 'best_bid': return dumps(self.exchange.get_best_bid(msg['ticker']).to_dict())
        elif msg['topic'] == 'best_ask': return dumps(self.exchange.get_best_ask(msg['ticker']).to_dict())
        elif msg['topic'] == 'midprice': return self.exchange.get_midprice(msg['ticker'])
        elif msg['topic'] == 'cash': return self.exchange.get_cash(msg['agent'])
        elif msg['topic'] == 'assets': return self.exchange.get_assets(msg['agent'])
        elif msg['topic'] == 'register_agent': return self.exchange.register_agent(msg['name'], msg['initial_cash'])
        elif msg['topic'] == 'get_agent': return self.exchange.get_agent(msg['name'])
        elif msg['topic'] == 'get_agents': return dumps(self.exchange.get_agents())
        elif msg['topic'] == 'add_cash': return dumps(self.exchange.add_cash(msg['agent'], msg['amount']))
        else: return f'unknown topic {msg["topic"]}'