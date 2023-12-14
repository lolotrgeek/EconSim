from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Subscriber
from source.exchange.DefiExchange import DefiExchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.WalletRequests import WalletRequests
from source.utils._utils import dumps, string_to_time
from Channels import Channels
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_defi_exchange() -> None:
    try:
        channels = Channels() 
        time_puller = Subscriber(channels.time_channel)
        responder = Responder(channels.defi_channel)
        crypto_requester = Requester(channels.crypto_channel)
        wallet_requester = Requester(channels.wallet_channel)
        await responder.connect()
        await crypto_requester.connect()
        await wallet_requester.connect()

        exchange = DefiExchange(datetime=datetime(1700,1,1), crypto_requester=CryptoCurrencyRequests(crypto_requester), wallet_requester=WalletRequests(wallet_requester))

        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else: 
                exchange.datetime = string_to_time(clock)

        async def callback(msg):
            if msg['topic'] == 'signature': return dumps(await exchange.signature_response(msg['agent_wallet'], msg['decision'], msg['txn']))
            elif msg['topic'] == 'create_asset': return dumps(await exchange.create_asset(msg['asset'], msg['decimals'] ))
            elif msg['topic'] == 'provide_liquidity': return dumps(await exchange.provide_liquidity(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['fee_level'], msg['high_range'], msg['low_range']))
            elif msg['topic'] == 'remove_liquidity': return dumps(await exchange.remove_liquidity(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['fee_level']))
            elif msg['topic'] == 'swap': return dumps(await exchange.swap(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['slippage']))
            elif msg['topic'] == 'get_fee_levels': return dumps(await exchange.get_fee_levels())
            elif msg['topic'] == 'get_pools': return dumps(await exchange.get_pools())
            elif msg['topic'] == 'get_pool': return dumps(await exchange.get_pool(msg['base'], msg['quote'], msg['fee_level']))
            elif msg['topic'] == 'get_pool_liquidity': return dumps(await exchange.get_pool_liquidity(msg['base'], msg['quote'], msg['fee_level']))
            else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})

        while True:
            get_time()
            await exchange.next()
            msg = await responder.respond(callback)
            if msg is None:
                continue

    except Exception as e:
        print("[DefiExchange Error] ", e)
        print(traceback.print_exc())
        return None  
    except KeyboardInterrupt:
        print("attempting to close defi_exchange..." )
        return None
    
if __name__ == '__main__':
    asyncio.run(run_defi_exchange())
    # print('done...')
    # exit(0)