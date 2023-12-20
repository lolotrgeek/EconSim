import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Subscriber
from source.exchange.CryptoExchange import CryptoExchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.utils._utils import dumps
from source.Channels import Channels
from .runner import Runner
from random import random
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class CryptoExchangeRunner(Runner):
    def __init__(self):
        super().__init__()
        self.channels = Channels()
        self.responder = Responder(self.channels.crypto_exchange_channel)
        self.requester = Requester(channel=self.channels.crypto_channel)
        self.crypto_currency_requests = CryptoCurrencyRequests(self.requester)
        self.exchange = None
        self.cryptos = []

    async def callback(self, msg) -> str:
        if msg['topic'] == 'create_asset': return dumps((await self.exchange.create_asset(msg['symbol'], msg['pairs'], msg['decimals'], msg['min_qty_percent'])))
        elif msg['topic'] == 'sim_time': return dumps(self.exchange.datetime)
        elif msg['topic'] == 'get_tickers': return dumps((await self.exchange.get_tickers()))
        elif msg['topic'] == 'limit_buy': return dumps((await self.exchange.limit_buy(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'], msg['min_qty'])).to_dict_full())
        elif msg['topic'] == 'limit_sell': return dumps((await self.exchange.limit_sell(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'], msg['min_qty'])).to_dict_full())
        elif msg['topic'] == 'market_buy': return dumps((await self.exchange.market_buy(msg['base'] , msg['quote'], msg['qty'], msg['buyer'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'market_sell': return dumps((await self.exchange.market_sell(msg['base'] , msg['quote'], msg['qty'], msg['seller'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'cancel_order': return await self.exchange.cancel_order(msg['base'] , msg['quote'], msg['order_id'])
        elif msg['topic'] == 'cancel_all_orders': return await self.exchange.cancel_all_orders(msg['base'] , msg['quote'], msg['agent'])
        elif msg['topic'] == 'candles': return dumps(await self.exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit']))
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
        elif msg['topic'] == 'get_pending_transactions': return dumps(await self.exchange.get_pending_transactions(msg['limit']))
        #TODO: exchange topic to get general exchange data
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})

    async def create_initial_assets(self):
        cryptos = await self.crypto_currency_requests.get_assets()
        
        found_base = [crypto for crypto in cryptos if crypto.get('symbol') == 'ETH']
        if len(found_base) == 0:
            #TODO: retry if this fails
            return None
        pairs = [{'asset': 'USD' ,'market_qty':1000 ,'seed_price':str(random()) ,'seed_bid':'.99', 'seed_ask':'1.01'}]
        await self.exchange.create_asset(found_base[0]['symbol'], pairs, decimals=found_base[0]['decimals'], min_qty_percent='0.05')

        for crypto in cryptos:
            if crypto['symbol'] != 'ETH':
                pairs = [
                    {'asset': 'USD' ,'market_qty':1000 ,'seed_price':str(random()) ,'seed_bid':'.99', 'seed_ask':'1.01'}, 
                    {'asset': 'ETH' ,'market_qty':1000 ,'seed_price':str(random()) ,'seed_bid':'.99', 'seed_ask':'1.01'}
                ]
            await self.exchange.create_asset(crypto['symbol'], pairs, decimals=crypto['decimals'], min_qty_percent='0.05') 

    async def run(self) -> None:
        try:
            await self.responder.connect()
            await self.requester.connect()
            self.exchange = CryptoExchange(datetime=datetime(1700,1,1), crypto_requests=self.crypto_currency_requests, )

            await self.create_initial_assets()
            
            while True:
                self.exchange.datetime = (await self.get_time())
                await self.exchange.next()
                msg = await self.responder.respond(self.callback)
                if msg == 'STOP':
                    break

        except Exception as e:
            print("[Exchange Error] ", e)
            print(traceback.print_exc())
            return None  
        except KeyboardInterrupt:
            print("attempting to close exchange..." )
            return None
    
if __name__ == '__main__':
    runner = CryptoExchangeRunner()
    asyncio.run(runner.run())
    # print('done...')
    # exit(0)