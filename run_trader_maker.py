from random import randint
import traceback
from source.Messaging import Requester
from source.agents.TradersCrypto import NaiveMarketMaker, SimpleMarketTaker, LowBidder
from rich import print
import asyncio
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from Channels import Channels
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_trader() -> None:
    try:
        channels = Channels()
        exchange_requester = Requester(channel=channels.crypto_exchange_channel)
        crypto_requester = Requester(channel=channels.crypto_channel)
        await exchange_requester.connect()
        await crypto_requester.connect()
        exchange_requests = CryptoExchangeRequests(requester=exchange_requester)
        crypto_requests = CryptoCurrencyRequests(requester=crypto_requester)
        trader =  NaiveMarketMaker(name='market_maker', aum=1_000_000, spread_pct='0.005', requests=(exchange_requests, crypto_requests))
        registered = await trader.register()
        if registered is None:
            raise Exception("Trader not registered")
        while True:
            next = await trader.next()
            if not next:
                break
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        return None
    except KeyboardInterrupt:
        print("attempting to close trader..." )
        trader.requests.requester.close()
        return None
    
if __name__ == '__main__':
    try:
        print('starting trader')
        asyncio.run(run_trader())
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        exit()