from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Subscriber
from source.exchange.CryptoExchange import CryptoExchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.utils._utils import dumps, string_to_time
from Channels import Channels
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_crypto_exchange() -> None:
    try:
        channels = Channels() 
        time_puller = Subscriber(channels.time_channel)
        responder = Responder(channels.crypto_exchange_channel)
        requester = Requester(channels.crypto_channel)
        await responder.connect()
        await requester.connect()

        exchange = CryptoExchange(datetime=datetime(1700,1,1), requester=CryptoCurrencyRequests(requester))

        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else: 
                exchange.datetime = string_to_time(clock)

        async def callback(msg) -> str:
            if msg['topic'] == 'create_asset': return dumps((await exchange.create_asset(msg['symbol'], msg['pairs'])))
            elif msg['topic'] == 'sim_time': return dumps(exchange.datetime)
            elif msg['topic'] == 'get_tickers': return dumps((await exchange.get_tickers()))
            elif msg['topic'] == 'limit_buy': return dumps((await exchange.limit_buy(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
            elif msg['topic'] == 'limit_sell': return dumps((await exchange.limit_sell(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
            elif msg['topic'] == 'market_buy': return await exchange.market_buy(msg['base'] , msg['quote'], msg['qty'], msg['buyer'], msg['fee'])
            elif msg['topic'] == 'market_sell': return await exchange.market_sell(msg['base'] , msg['quote'], msg['qty'], msg['seller'], msg['fee'])
            elif msg['topic'] == 'cancel_order': return await exchange.cancel_order(msg['base'] , msg['quote'], msg['order_id'])
            elif msg['topic'] == 'cancel_all_orders': return await exchange.cancel_all_orders(msg['base'] , msg['quote'], msg['agent'])
            elif msg['topic'] == 'candles': return dumps(await exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit']))
            elif msg['topic'] == 'order_book': return dumps( (await exchange.get_order_book(msg['ticker'])).to_dict(msg['limit']))
            elif msg['topic'] == 'latest_trade': return dumps(await exchange.get_latest_trade(msg['base'] , msg['quote']))
            elif msg['topic'] == 'trades': return dumps( await exchange.get_trades(msg['base'] , msg['quote'], msg['limit']))
            elif msg['topic'] == 'quotes': return await exchange.get_quotes(msg['ticker'])
            elif msg['topic'] == 'best_bid': return dumps((await exchange.get_best_bid(msg['ticker'])).to_dict())
            elif msg['topic'] == 'best_ask': return dumps((await exchange.get_best_ask(msg['ticker'])).to_dict())
            elif msg['topic'] == 'midprice': return dumps(await exchange.get_midprice(msg['ticker']))
            elif msg['topic'] == 'cash': return await exchange.get_cash(msg['agent'])
            elif msg['topic'] == 'assets': return await exchange.get_assets(msg['agent'])
            elif msg['topic'] == 'register_agent': return await exchange.register_agent(msg['name'], msg['initial_assets'])
            elif msg['topic'] == 'get_agent': return dumps(await exchange.get_agent(msg['name']))
            elif msg['topic'] == 'get_agents': return dumps(await exchange.get_agents())
            elif msg['topic'] == 'add_cash': return dumps(await exchange.add_cash(msg['agent'], msg['amount'], msg['note']))
            elif msg['topic'] == 'remove_cash': return dumps(await exchange.remove_cash(msg['agent'], msg['amount']))
            elif msg['topic'] == 'get_cash': return dumps(await exchange.get_cash(msg['agent']))
            elif msg['topic'] == 'get_assets': return dumps(await exchange.get_assets(msg['agent']))
            elif msg['topic'] == 'get_agents_holding': return dumps(await exchange.get_agents_holding(msg['asset']))
            elif msg['topic'] == 'get_agents_positions': return dumps(await exchange.get_agents_positions(msg['ticker']))
            elif msg['topic'] == 'get_agents_simple': return dumps(await exchange.get_agents_simple())
            elif msg['topic'] == 'get_positions': return dumps(await exchange.get_positions(msg['agent'], msg['page_size'], msg['page']))
            elif msg['topic'] == 'get_outstanding_shares': return dumps(await exchange.get_outstanding_shares(msg['ticker']))
            elif msg['topic'] == 'get_taxable_events': return dumps(await exchange.get_taxable_events())
            #TODO: exchange topic to get general exchange data
            else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})

        while True:
            get_time()
            await exchange.next()
            msg = await responder.respond(callback)
            if msg is None:
                continue

    except Exception as e:
        print("[Exchange Error] ", e)
        print(traceback.print_exc())
        return None  
    except KeyboardInterrupt:
        print("attempting to close exchange..." )
        return None
    
if __name__ == '__main__':
    asyncio.run(run_crypto_exchange())
    # print('done...')
    # exit(0)