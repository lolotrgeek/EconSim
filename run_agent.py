from random import randint
import traceback
from source.Messaging import Requester
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.agents.Agents import NaiveMarketMaker, RandomMarketTaker, LowBidder
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

tickers = ['XYZ']

async def run_agent(exchange_channel = 5570) -> None:
    try:
        agent = None
        picker = randint(0,3)
        requester = Requester(channel=exchange_channel)
        await requester.connect()
        if picker == 0:
            agent =  NaiveMarketMaker(name='market_maker', tickers=tickers, aum=1_000, spread_pct=0.005, qty_per_order=4, requester=Requests(requester))
        elif picker == 1:
            agent = RandomMarketTaker(name='market_taker', tickers=tickers, aum=1_000, prob_buy=.2, prob_sell=.2, qty_per_order=1, requester=Requests(requester))
        else:
            agent = LowBidder(name='low_bidder', tickers=tickers, aum=1_000, requester=Requests(requester))
        registered = await agent.register()
        if registered is None:
            raise Exception("Agent not registered")
        while True:
            next = await agent.next()
            if not next:
                break
    except Exception as e:
        print("[Agent Error] ", e)
        traceback.print_exc()
        return None
    except KeyboardInterrupt:
        print("attempting to close agent..." )
        agent.requests.requester.close()
        return None
    
if __name__ == '__main__':
    try:
        print('starting agent')
        asyncio.run(run_agent())
    except Exception as e:
        print("[Agent Error] ", e)
        traceback.print_exc()
        exit()