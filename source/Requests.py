from time import sleep
import json
import traceback
import asyncio

class Requests():
    """
    Creates an API for for making requests to the exchange process.
    """
    def __init__(self, requester):
        self.requester = requester
        self.timeout = 5
        self.max_tries = 1
        self.debug = True
        
    async def make_request(self, topic: str, message: dict, factory, tries=0):
        try:
            message['topic'] = topic
            msg = await self.requester.request(message)
            if msg is None:
                raise Exception(f'{topic} is None, {msg}')
            elif isinstance(msg, str):
                return json.loads(msg)
            elif isinstance(msg, list):
                return msg
            elif not isinstance(msg, dict):
                raise Exception(f'{topic} got type {type(msg)}, expected dict. Message: {msg}')
            elif 'error' in msg:
                raise Exception(f'{topic} error, {msg}')
            else:
                return msg
        except Exception as e:
            tries += 1
            if tries >= self.max_tries:
                error = {}
                error[topic] = f"[Request Error] {e}"
                if self.debug:
                    print("[Request Error]", e)
                    print(traceback.format_exc())
                return error
            await asyncio.sleep(0.1)
            return await self.make_request(topic, message, factory, tries)

    async def get_price_bars(self, ticker, interval, limit):
        return await self.make_request('candles', {'ticker': ticker, 'interval': interval, 'limit': limit}, self.requester)

    async def create_asset(self, ticker, qty, seed_price, seed_bid, seed_ask):
        return await self.make_request('create_asset', {'ticker': ticker, 'qty': qty,'seed_price': seed_price, 'seed_bid': seed_bid, 'seed_ask': seed_ask}, self.requester)

    async def get_mempool(self, limit):
        return await self.make_request('mempool', {'limit': limit}, self.requester)

    async def get_order_book(self, ticker):
        return await self.make_request('order_book', {'ticker': ticker}, self.requester)

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
    
    async def add_cash(self, agent, amount):
        return await self.make_request('add_cash', {'agent': agent, 'amount': amount}, self.requester)
    
    async def get_agents_holding(self, ticker):
        return await self.make_request('get_agents_holding', {'ticker': ticker}, self.requester)
    
    async def get_agents_positions(self, ticker):
        return await self.make_request('get_agents_positions', {'ticker': ticker}, self.requester)