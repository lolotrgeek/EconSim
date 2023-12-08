from datetime import datetime
from source.crypto.CryptoCurrency import CryptoCurrency
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests
from source.Messaging import Responder, Requester, Subscriber
import asyncio
from rich import print
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from source.utils._utils import dumps, string_to_time
from Channels import Channels
from source.crypto.Wallet import Wallet


async def run_wallets() -> None:
    try:
        channels = Channels()
        responder = Responder(channels.crypto_channel)
        requester = Requester(channel=channels.crypto_exchange_channel)
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

        wallets = []
        #TODO: each agent registers a wallet with the wallet service

        async def callback(msg):
            if 'asset' in msg:
                if msg['address'] in wallets:
                    if msg['topic'] == 'get_balance': return dumps(await wallets[msg['address']].get_balance(msg['asset']))
                    elif msg['topic'] == 'request_signature': return dumps(await wallets[msg['address']].request_signature(msg['txn']))
                else: return f'unknown asset {msg["asset"]}'    
            else: return f'unknown topic {msg["topic"]}'

        while True:
            time = get_time()
            for wallet in wallets:
                await wallets[wallet].next(time)
            msg = await responder.lazy_respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(run_wallets())
