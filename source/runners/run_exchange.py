import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
from datetime import datetime
import traceback
from runner import Runner
from source.Messaging import Responder, Requester, Subscriber
from source.exchange.Exchange import Exchange
from source.utils._utils import dumps
from source.Channels import Channels
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class ExchangeRunner(Runner):
    def __init__(self):
        self.channels = Channels()
        self.responder = Responder(self.channels.exchange_channel)
        self.requester = Requester(channel=self.channels.company_channel)
        self.time_puller = Subscriber(self.channels.time_channel)
        self.exchange = None
        self.companies = []

    async def callback(self, msg) -> str:
        if msg['topic'] == 'create_asset': return dumps((await self.exchange.create_asset(msg['ticker'],msg['asset_type'],msg['qty'], msg['seed_price'], msg['seed_bid'], msg['seed_ask'])))
        elif msg['topic'] == 'sim_time': return dumps(self.exchange.datetime)
        elif msg['topic'] == 'get_tickers': return dumps((await self.exchange.get_tickers()))
        elif msg['topic'] == 'limit_buy': return dumps((await self.exchange.limit_buy(msg['ticker'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'limit_sell': return dumps((await self.exchange.limit_sell(msg['ticker'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'market_buy': return await self.exchange.market_buy(msg['ticker'], msg['qty'], msg['buyer'], msg['fee'])
        elif msg['topic'] == 'market_sell': return await self.exchange.market_sell(msg['ticker'], msg['qty'], msg['seller'], msg['fee'])
        elif msg['topic'] == 'cancel_order': return await self.exchange.cancel_order(msg['ticker'], msg['order_id'])
        elif msg['topic'] == 'cancel_all_orders': return await self.exchange.cancel_all_orders(msg['agent'], msg['ticker'])
        elif msg['topic'] == 'candles': return dumps(await self.exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit']))
        elif msg['topic'] == 'order_book': return dumps( (await self.exchange.get_order_book(msg['ticker'])).to_dict(msg['limit']))
        elif msg['topic'] == 'latest_trade': return dumps(await self.exchange.get_latest_trade(msg['ticker']))
        elif msg['topic'] == 'trades': return dumps( await self.exchange.get_trades(msg['ticker']))
        elif msg['topic'] == 'quotes': return await self.exchange.get_quotes(msg['ticker'])
        elif msg['topic'] == 'best_bid': return dumps((await self.exchange.get_best_bid(msg['ticker'])).to_dict())
        elif msg['topic'] == 'best_ask': return dumps((await self.exchange.get_best_ask(msg['ticker'])).to_dict())
        elif msg['topic'] == 'midprice': return dumps(await self.exchange.get_midprice(msg['ticker']))
        elif msg['topic'] == 'cash': return await self.exchange.get_cash(msg['agent'])
        elif msg['topic'] == 'assets': return await self.exchange.get_assets(msg['agent'])
        elif msg['topic'] == 'register_agent': return await self.exchange.register_agent(msg['name'], msg['initial_cash'])
        elif msg['topic'] == 'get_agent': return dumps(await self.exchange.get_agent(msg['name']))
        elif msg['topic'] == 'get_agents': return dumps(await self.exchange.get_agents())
        elif msg['topic'] == 'add_cash': return dumps(await self.exchange.add_cash(msg['agent'], msg['amount'], msg['note']))
        elif msg['topic'] == 'remove_cash': return dumps(await self.exchange.remove_cash(msg['agent'], msg['amount']))
        elif msg['topic'] == 'get_cash': return dumps(await self.exchange.get_cash(msg['agent']))
        elif msg['topic'] == 'get_assets': return dumps(await self.exchange.get_assets(msg['agent']))
        elif msg['topic'] == 'get_agents_holding': return dumps(await self.exchange.get_agents_holding(msg['ticker']))
        elif msg['topic'] == 'get_agents_positions': return dumps(await self.exchange.get_agents_positions(msg['ticker']))
        elif msg['topic'] == 'get_agents_simple': return dumps(await self.exchange.get_agents_simple())
        elif msg['topic'] == 'get_positions': return dumps(await self.exchange.get_positions(msg['agent'], msg['page_size'], msg['page']))
        elif msg['topic'] == 'get_outstanding_shares': return dumps(await self.exchange.get_outstanding_shares(msg['ticker']))
        elif msg['topic'] == 'get_taxable_events': return dumps(await self.exchange.get_taxable_events())
        #TODO: exchange topic to get general exchange data
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})        
        
    async def run(self) -> None:
        try: 
            await self.responder.connect()
            self.exchange = Exchange(datetime=datetime(1700,1,1))
            while True:
                self.exchange.datetime = (await self.get_time())
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
    runner = ExchangeRunner()
    asyncio.run(runner.run())
    # print('done...')
    # exit(0)