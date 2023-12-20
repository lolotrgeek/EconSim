import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from random import randint
import traceback
from source.Messaging import Requester
from source.agents.TradersCrypto import NaiveMarketMaker, SimpleMarketTaker, LowBidder
from rich import print
import asyncio
from .runner import Runner
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.Channels import Channels
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class TraderRunner(Runner):
    def __init__(self):
        super().__init__()
        self.exchange_requester = Requester(channel=self.channels.crypto_exchange_channel)
        self.crypto_requester = Requester(channel=self.channels.crypto_channel)
        self.trader = None

    async def pick_trader(self):
        picker = randint(0,2)
        exchange_requests = CryptoExchangeRequests(requester=self.exchange_requester)
        crypto_requests = CryptoCurrencyRequests(requester=self.crypto_requester)
        if picker == 0:
            self.trader =  NaiveMarketMaker(name='market_maker', aum=1_000_000, spread_pct='0.005', requests=(exchange_requests, crypto_requests))
        elif picker == 1:
            self.trader = SimpleMarketTaker(name='poor_taker', aum=1_000, requests=(exchange_requests, crypto_requests))
        elif picker == 2:
            self.trader = SimpleMarketTaker(name='rich_taker', aum=10_000, requests=(exchange_requests, crypto_requests))        

    async def run(self) -> None:
        try:
            await self.exchange_requester.connect()
            await self.crypto_requester.connect()
            await self.pick_trader()
            registered = await self.trader.register(logger=True)
            if registered is None:
                raise Exception("Trader not registered")
            while True:
                next = await self.trader.next()
                if not next:
                    break
        except Exception as e:
            print("[Trader Error] ", e)
            traceback.print_exc()
            return None
        except KeyboardInterrupt:
            print("attempting to close trader..." )
            self.trader.requests.requester.close()
            return None

if __name__ == '__main__':
    try:
        print('starting trader')
        runner = TraderRunner()
        asyncio.run(runner.run())
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        exit()