import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class ExchangeRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def get_sim_time(self):
        return await self.make_request('sim_time', {}, self.requester)
    
    async def get_tickers(self):
        return await self.make_request('get_tickers', {}, self.requester)

    async def get_price_bars(self, ticker, interval, limit):
        return await self.make_request('candles', {'ticker': ticker, 'interval': interval, 'limit': limit}, self.requester)

    async def create_asset(self, ticker,asset_type='stock', qty=1000, seed_price=100, seed_bid=.99, seed_ask=1.01):
        return await self.make_request('create_asset', {'ticker': ticker, 'asset_type': asset_type, 'qty': qty,'seed_price': seed_price, 'seed_bid': seed_bid, 'seed_ask': seed_ask}, self.requester)

    async def get_mempool(self, limit):
        return await self.make_request('mempool', {'limit': limit}, self.requester)

    async def get_order_book(self, ticker, limit=20):
        return await self.make_request('order_book', {'ticker': ticker, 'limit': limit}, self.requester)

    async def get_latest_trade(self, ticker):
        return await self.make_request('latest_trade', {'ticker': ticker}, self.requester)

    async def get_trades(self, ticker, limit):
        return await self.make_request('trades', {'ticker': ticker, 'limit': limit}, self.requester)

    async def get_quotes(self, ticker):
        return await self.make_request('quotes', {'ticker': ticker}, self.requester)

    async def get_best_bid(self, ticker):
        return await self.make_request('best_bid', {'ticker': ticker}, self.requester)

    async def get_best_ask(self, ticker):
        return await self.make_request('best_ask', {'ticker': ticker}, self.requester)

    async def get_midprice(self, ticker):
        return await self.make_request('midprice', {'ticker': ticker}, self.requester)

    async def limit_buy(self, ticker, price, quantity, creator, fee=0.0):
        return await self.make_request('limit_buy', {'ticker': ticker, 'price': price, 'qty': quantity, 'creator': creator, 'fee': fee}, self.requester) 

    async def limit_sell(self, ticker, price, quantity, creator, fee=0.0):
        return await self.make_request('limit_sell', {'ticker': ticker, 'price': price, 'qty': quantity, 'creator': creator, 'fee': fee}, self.requester)
    
    async def cancel_order(self, id):
        return await self.make_request('cancel_order', {'order_id': id}, self.requester)

    async def cancel_all_orders(self, ticker, agent):
        return await self.make_request('cancel_all_orders', {'ticker': ticker, 'agent': agent}, self.requester)

    async def market_buy(self, ticker, quantity, creator, fee=0.0):
        return await self.make_request('market_buy', {'ticker': ticker, 'qty': quantity, 'buyer': creator, 'fee': fee}, self.requester)
    
    async def market_sell(self, ticker, quantity, creator, fee=0.0):
        return await self.make_request('market_sell', {'ticker': ticker, 'qty': quantity, 'seller': creator, 'fee': fee}, self.requester)
    
    async def get_cash(self, agent):
        return await self.make_request('cash', {'agent': agent}, self.requester)
    
    async def get_assets(self, agent):
        return await self.make_request('assets', {'agent': agent}, self.requester)
    
    async def register_agent(self, name, initial_cash):
        return await self.make_request('register_agent', {'name': name, 'initial_cash': initial_cash}, self.requester)
    
    async def get_agent(self, name):
        return await self.make_request('get_agent', {'name': name}, self.requester)
    
    async def get_agents(self):
        return await self.make_request('get_agents', {}, self.requester)
    
    async def add_cash(self, agent, amount, note):
        return await self.make_request('add_cash', {'agent': agent, 'amount': amount, 'note': note}, self.requester)
    
    async def remove_cash(self, agent, amount, notes=''):
        return await self.make_request('remove_cash', {'agent': agent, 'amount': amount, 'notes': notes}, self.requester)
    
    async def get_agents_holding(self, ticker):
        return await self.make_request('get_agents_holding', {'ticker': ticker}, self.requester)
    
    async def get_agents_positions(self, ticker):
        return await self.make_request('get_agents_positions', {'ticker': ticker}, self.requester)
    
    async def get_agents_simple(self):
        return await self.make_request('get_agents_simple', {}, self.requester)
    
    async def get_positions(self, agent, page_size=10, page=1):
        return await self.make_request('get_positions', {'agent': agent, 'page_size': page_size, "page": page}, self.requester)
    
    async def get_taxable_events(self):
        return await self.make_request('get_taxable_events',{}, self.requester)
    
    async def get_outstanding_shares(self, ticker):
        return await self.make_request('get_outstanding_shares', {'ticker': ticker}, self.requester)