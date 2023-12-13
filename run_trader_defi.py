import traceback
from source.Messaging import Responder, Requester, Subscriber
from source.Messaging import Requester, Responder
from rich import print
import asyncio
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.agents.TradersCryptoDefi import RandomSwapper
from source.utils._utils import dumps, string_to_time
from Channels import Channels
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_defi_trader() -> None:
    try:
        channels = Channels()
        responder = Responder(channels.wallet_channel)
        exchange_requester = Requester(channel=channels.defi_channel)
        requester = Requester(channel=channels.crypto_channel)
        exchange_messenger = DefiExchangeRequests(exchange_requester)
        crypto_messenger = CryptoCurrencyRequests(requester)        
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

        traders = {}
        random_swapper = RandomSwapper('random_swapper', exchange_messenger, crypto_messenger)
        traders[random_swapper.wallet.address] = random_swapper

        async def callback(msg):
            if 'address' in msg:
                if msg['wallet'] in traders:
                    if msg['topic'] == 'request_signature': return dumps(await traders[msg['wallet']].signature_request(msg['txn']))
                    elif msg['topic'] == 'get_balance': return dumps((await traders[msg['wallet']].get_balance(msg['asset'])))
                else: return f'unknown asset {msg["asset"]}'    
            else: return f'unknown topic {msg["topic"]}'

        while True:
            time = get_time()
            for wallet, trader in traders:
                await trader.next(time)
            msg = await responder.lazy_respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        return None
    except KeyboardInterrupt:
        print("attempting to close trader..." )
        return None
    
if __name__ == '__main__':
    try:
        print('starting trader')
        asyncio.run(run_defi_trader())
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        exit()