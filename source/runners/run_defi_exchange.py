import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
from datetime import datetime
import traceback
from runner import Runner
from source.Messaging import Responder, Requester
from source.exchange.DefiExchange import DefiExchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.WalletRequests import WalletRequests
from source.utils._utils import dumps
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class DefiExchangeRunner(Runner):
    def __init__(self):
        super().__init__()
        self.responder = Responder(self.channels.defi_channel)
        self.crypto_requester = Requester(self.channels.crypto_channel)
        self.wallet_requester = Requester(self.channels.wallet_channel)            
        self.exchange = None

    async def callback(self, msg):
        if msg['topic'] == 'signature': return dumps(await self.exchange.signature_response(msg['agent_wallet'], msg['decision'], msg['txn']))
        elif msg['topic'] == 'list_asset': return dumps(await self.exchange.list_asset(msg['asset'], msg['decimals'] ))
        elif msg['topic'] == 'provide_liquidity': return dumps(await self.exchange.provide_liquidity(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['fee_level'], msg['high_range'], msg['low_range']))
        elif msg['topic'] == 'remove_liquidity': return dumps(await self.exchange.remove_liquidity(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['fee_level']))
        elif msg['topic'] == 'collect_fees': return dumps(await self.exchange.collect_fees(msg['agent_wallet'], msg['base'], msg['quote'], msg['fee_level']))
        elif msg['topic'] == 'swap': return dumps(await self.exchange.swap( msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['slippage']))
        elif msg['topic'] == 'get_fee_levels': return dumps(await self.exchange.get_fee_levels())
        elif msg['topic'] == 'get_pools': return dumps(await self.exchange.get_pools())
        elif msg['topic'] == 'get_pool': return dumps(await self.exchange.get_pool(msg['base'], msg['quote'], msg['fee_level']))
        elif msg['topic'] == 'get_pool_liquidity': return dumps(await self.exchange.get_pool_liquidity(msg['base'], msg['quote'], msg['fee_level']))
        elif msg['topic'] == 'get_assets': return dumps(await self.exchange.get_assets())
        elif msg['topic'] == 'get_price': return dumps(await self.exchange.get_price(msg['base'], msg['quote'], msg['pool_fee_pct'], msg['base_amount']))
        elif msg['topic'] == 'get_position': return dumps(await self.exchange.get_position(msg['position_address']))
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})

    async def run(self) -> None:
        try:
            await self.responder.connect()
            await self.crypto_requester.connect()
            await self.wallet_requester.connect()
            self.exchange = DefiExchange('ETH', dt=datetime(1700,1,1), crypto_requests=CryptoCurrencyRequests(self.crypto_requester), wallet_requests=WalletRequests(self.wallet_requester))
            
            await self.exchange.start()
            await self.exchange.list_asset('BTC', 8)
            await self.exchange.list_asset('LTC', 8)
            await self.exchange.list_asset('USD', 2)

            await self.exchange.create_pool('ETH', 'BTC', 1, 1, 1)
            await self.exchange.create_pool('ETH', 'LTC', 1, 1, 1)
            await self.exchange.create_pool('ETH', 'USD', 1, 1, 1)

            while True:
                self.exchange.dt = await self.get_time()
                await self.exchange.next()
                msg = await self.responder.respond(self.callback)
                if msg == 'STOP':
                    break

        except Exception as e:
            print("[DefiExchange Error] ", e)
            print(traceback.print_exc())
            return None  
        except KeyboardInterrupt:
            print("attempting to close defi_exchange..." )
            return None
    
if __name__ == '__main__':
    runner = DefiExchangeRunner()
    asyncio.run(runner.run())
    # print('done...')
    # exit(0)