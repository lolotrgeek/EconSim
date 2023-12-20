import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import traceback
from source.Messaging import Responder, Requester, Subscriber
from source.Messaging import Requester, Responder
from rich import print
import asyncio
from typing import Dict
from .runner import Runner
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.agents.TradersCryptoDefi import RandomSwapper
from source.utils._utils import dumps
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class DefiTraderRunner(Runner):
    def __init__(self):
        super().__init__()
        self.responder = Responder(self.channels.wallet_channel)
        self.requester = Requester(self.channels.crypto_channel)
        self.exchange_requester = Requester(self.channels.defi_channel)
        self.traders: Dict[str, RandomSwapper] = {}

    async def callback(self, msg):
        if 'address' in msg:
            if msg['wallet'] in self.traders:
                if msg['topic'] == 'request_signature': return dumps(await self.traders[msg['wallet']].signature_request(msg['txn']))
                elif msg['topic'] == 'get_balance': return dumps((await self.traders[msg['wallet']].get_balance(msg['asset'])))
            else: return f'unknown asset {msg["asset"]}'    
        else: return f'unknown topic {msg["topic"]}'

    async def run(self) -> None:
        try:
            await self.responder.connect()
            await self.requester.connect()
            await self.exchange_requester.connect()

            random_swapper = RandomSwapper('random_swapper', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests(self.requester))
            self.traders[random_swapper.wallet.address] = random_swapper

            while True:
                time = await self.get_time()
                for wallet, trader in self.traders.items():
                    await trader.next(time)
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