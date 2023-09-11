from random import randint
import traceback
from source.Messaging import Requester
from source.agents.Traders import NaiveMarketMaker, RandomMarketTaker, LowBidder, Fundamental
from rich import print
import asyncio
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompanyRequests import PublicCompanyRequests
from Channels import Channels
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_trader() -> None:
    try:
        trader = None
        picker = randint(0,4)
        channels = Channels()
        exchange_requester = Requester(channel=channels.exchange_channel)
        company_requester = Requester(channel=channels.company_channel)
        await exchange_requester.connect()
        await company_requester.connect()
        exchange_requests = ExchangeRequests(requester=exchange_requester)
        company_requests = PublicCompanyRequests(requester=company_requester)
        if picker == 0:
            trader =  NaiveMarketMaker(name='market_maker', aum=1_000, spread_pct=0.005, qty_per_order=4, requests=(exchange_requests, company_requests))
        elif picker == 1:
            trader = RandomMarketTaker(name='market_taker', aum=1_000, prob_buy=.2, prob_sell=.2, qty_per_order=1 , requests=(exchange_requests, company_requests))
        elif picker == 2:
            trader = LowBidder(name='low_bidder', aum=1_000, qty_per_order=1, requests=(exchange_requests, company_requests)) 
        else:
            trader = Fundamental(name='fundamental', aum=1_000, requests=(exchange_requests, company_requests))

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