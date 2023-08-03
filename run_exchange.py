from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Puller
from source.exchange.Exchange import Exchange
from source.company.PublicCompany import PublicCompany
from source.utils._utils import dumps, string_to_time
from rich import print
from rich.live import Live
from rich.table import Table
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_exchange(exchange_channel = 5570, time_channel = 5114):
    try: 
        exchange = Exchange(datetime=datetime(1700,1,1))
        await exchange.create_asset("XYZ", 'stock')
        time_puller = Puller(time_channel)
        responder = Responder(exchange_channel)
        requester = Requester(exchange_channel)
        await responder.connect()
        await requester.connect()

        def get_time():
            clock = time_puller.pull()
            if clock == None: 
                pass
            elif type(clock) is dict and 'time' not in clock:
                pass
            elif type(clock['time']) is dict:
                pass
            else: 
                exchange.datetime = string_to_time(clock['time'])

        async def callback(msg):
            if msg['topic'] == 'create_asset': return dumps((await exchange.create_asset(msg['ticker'],msg['asset_type'],msg['qty'], msg['seed_price'], msg['seed_bid'], msg['seed_ask'])))
            elif msg['topic'] == 'sim_time': return dumps(exchange.datetime)
            elif msg['topic'] == 'limit_buy': return dumps((await exchange.limit_buy(msg['ticker'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict())
            elif msg['topic'] == 'limit_sell': return dumps((await exchange.limit_sell(msg['ticker'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict())
            elif msg['topic'] == 'market_buy': return await exchange.market_buy(msg['ticker'], msg['qty'], msg['buyer'], msg['fee'])
            elif msg['topic'] == 'market_sell': return await exchange.market_sell(msg['ticker'], msg['qty'], msg['seller'], msg['fee'])
            elif msg['topic'] == 'cancel_order': return await exchange.cancel_order(msg['order_id'])
            elif msg['topic'] == 'cancel_all_orders': return await exchange.cancel_all_orders(msg['agent'], msg['ticker'])
            elif msg['topic'] == 'candles': return await exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit'])
            # elif msg['topic'] == 'mempool': return await exchange.mempool(msg['limit'])
            elif msg['topic'] == 'order_book': return dumps( (await exchange.get_order_book(msg['ticker'])).to_dict())
            elif msg['topic'] == 'latest_trade': return dumps(await exchange.get_latest_trade(msg['ticker']))
            elif msg['topic'] == 'trades': return dumps( await exchange.get_trades(msg['ticker']))
            elif msg['topic'] == 'quotes': return await exchange.get_quotes(msg['ticker'])
            elif msg['topic'] == 'best_bid': return dumps((await exchange.get_best_bid(msg['ticker'])).to_dict())
            elif msg['topic'] == 'best_ask': return dumps((await exchange.get_best_ask(msg['ticker'])).to_dict())
            elif msg['topic'] == 'midprice': return await exchange.get_midprice(msg['ticker'])
            elif msg['topic'] == 'cash': return await exchange.get_cash(msg['agent'])
            elif msg['topic'] == 'assets': return await exchange.get_assets(msg['agent'])
            elif msg['topic'] == 'register_agent': return await exchange.register_agent(msg['name'], msg['initial_cash'])
            elif msg['topic'] == 'get_agent': return dumps(await exchange.get_agent(msg['name']))
            elif msg['topic'] == 'get_agents': return dumps(await exchange.get_agents())
            elif msg['topic'] == 'add_cash': return dumps(await exchange.add_cash(msg['agent'], msg['amount']))
            elif msg['topic'] == 'remove_cash': return dumps(await exchange.remove_cash(msg['agent'], msg['amount']))
            elif msg['topic'] == 'get_cash': return dumps(await exchange.get_cash(msg['agent']))
            elif msg['topic'] == 'get_assets': return dumps(await exchange.get_assets(msg['agent']))
            elif msg['topic'] == 'get_agents_holding': return dumps(await exchange.get_agents_holding(msg['ticker']))
            elif msg['topic'] == 'get_agents_positions': return dumps(await exchange.get_agents_positions(msg['ticker']))
            elif msg['topic'] == 'get_agents_simple': return dumps(await exchange.get_agents_simple())
            #TODO: exchange topic to get general exchange data
            else: return f'unknown topic {msg["topic"]}'

        while True:
            get_time()
            msg = await responder.respond(callback)
            if msg == None:
                continue
    except Exception as e:
        print("[Exchange Error] ", e)
        print(traceback.print_exc())
        return None  
    except KeyboardInterrupt:
        print("attempting to close exchange..." )
        return None
    
if __name__ == '__main__':
    asyncio.run(run_exchange())
    # print('done...')
    # exit(0)