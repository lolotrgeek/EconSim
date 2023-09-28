from datetime import datetime
from source.crypto.CryptoCurrency import CryptoCurrency
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests
from source.Messaging import Responder, Requester, Subscriber
import asyncio
from rich import print
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from source.utils._utils import dumps, string_to_time
from Channels import Channels

names = ['BTC', 'ETH']

async def generate_cryptos(names, requester, time) -> dict:
    cryptos = {"USD": CryptoCurrency("USD", time, requester=requester)}
    await cryptos["USD"].issue_coins([{'asset': cryptos["USD"].symbol ,'market_qty':1000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}], 1_000_000_000)
    for name in names:
        crypto = CryptoCurrency(name, time, requester=requester)
        cryptos[crypto.symbol] = crypto
        await crypto.issue_coins([{'asset': crypto.symbol ,'market_qty':1000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}], 1_000_000_000)
    return cryptos

async def run_crypto() -> None:
    try:
        channels = Channels()
        responder = Responder(channels.crypto_channel)
        requester = Requester(channel=channels.exchange_channel)
        time_puller = Subscriber(channels.time_channel)
        await responder.connect()
        await requester.connect()

        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else:
                return string_to_time(clock) 

        time = get_time()
        cryptos = await generate_cryptos(names, CryptoExchangeRequests(requester), time)

        async def callback(msg):
            print(msg)
            if 'asset' in msg:
                if msg['asset'] in cryptos:
                    if msg['topic'] == 'get_transactions': return dumps(await cryptos[msg['asset']].blockchain.get_transactions())
                    if msg['topic'] == 'get_transaction': return dumps(await cryptos[msg['asset']].blockchain.get_transaction(msg['id']))
                    elif msg['topic'] == 'add_transaction': return dumps(await cryptos[msg['asset']].blockchain.add_transaction(msg['asset'], msg['fee'], msg['amount'], msg['sender'], msg['recipient'], msg['dt']).to_dict())
                    elif msg['topic'] == 'get_mempool': return dumps(await cryptos[msg['asset']].blockchain.get_mempool())
                    elif msg['topic'] == 'get_pending_transactions': return dumps(await cryptos[msg['asset']].blockchain.mempool.get_pending_transactions(to_dicts=True))
                    elif msg['topic'] == 'get_confirmed_transactions': return dumps(await cryptos[msg['asset']].blockchain.mempool.get_confirmed_transactions(to_dicts=True))

                else: return f'unknown asset {msg["asset"]}'    
            else: return f'unknown topic {msg["topic"]}'

        # for crypto in cryptos:
        #     print("issuing coins", crypto)
        #     result = await cryptos[crypto].issue_coins([{'asset': cryptos[crypto].symbol ,'market_qty':1000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}], 1_000_000_000)
        #     print(result)

        while True:
            time = get_time()
            for crypto in cryptos:
                await cryptos[crypto].next(time)
            msg = await responder.lazy_respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(run_crypto())
