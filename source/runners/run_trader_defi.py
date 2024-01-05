import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
import traceback
from source.Messaging import Responder, Requester
from rich import print
from random import randint
import asyncio
from runner import Runner
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.agents.TradersDefi import RandomSwapper, RandomLiquidityProvider
from source.utils._utils import dumps
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class DefiTraderRunner(Runner):
    def __init__(self):
        super().__init__()
        self.responder = Responder(self.channels.wallet_channel)
        self.requester = Requester(self.channels.crypto_channel)
        self.exchange_requester = Requester(self.channels.defi_channel)
        self.trader = None

    async def callback(self, msg):
        if 'address' in msg:
            if msg['address'] == self.trader.wallet.address:
                if msg['topic'] == 'request_signature': return dumps(await self.trader.wallet.signature_request(msg['txn']))
                elif msg['topic'] == 'get_balance': return dumps((await self.trader.wallet.get_balance(msg['asset'])))
                elif msg['topic'] == 'transaction_confirmed': return dumps(await self.trader.wallet.transaction_confirmed(msg['txn']))
                elif msg['topic'] == 'transaction_failed': return dumps(await self.trader.wallet.transaction_failed(msg['txn']))
            else: return dumps({"error": f'unknown address {msg["address"]}'})
        else: return dumps({"error": f'unknown topic {msg["topic"]}'})

    async def pick_trader(self):
        picker = randint(0,2)
        if picker == 0:
            self.trader =  RandomLiquidityProvider('random_liquidity_provider', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests(self.requester))
        elif picker == 1:
            self.trader = RandomSwapper('random_swapper', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests(self.requester))
        elif picker == 2:
            self.trader = RandomSwapper('random_swapper', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests(self.requester))

    async def run(self) -> None:
        try:
            await self.responder.connect()
            await self.requester.connect()
            await self.exchange_requester.connect()

            await self.pick_trader()
            await self.trader.wallet.connect('ETH')
            time = await self.get_time()

            while True:
                time = await self.get_time()
                msg = await self.responder.lazy_respond(self.callback)
                await self.trader.next(time)
                msg = await self.responder.lazy_respond(self.callback)
                if msg == 'STOP':
                    break

        except Exception as e:
            print("[Trader Error] ", e)
            print(traceback.print_exc())
            return None
        except KeyboardInterrupt:
            print("attempting to close trader..." )
            return None

if __name__ == '__main__':
    try:
        runner = DefiTraderRunner()
        asyncio.run(runner.run())
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        exit()