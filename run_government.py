import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Subscriber, Pusher
from source.agents.Government import Government
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps, string_to_time
from rich import print
from rich.live import Live
from rich.table import Table


async def run_government(government_channel=5580, exchange_channel = 5570, time_channel = 5114) -> None:
    try:
        pusher = Pusher(government_channel)
        requester = Requester(channel=exchange_channel)
        time_puller = Subscriber(time_channel)
        await requester.connect()
        government = Government(requester=Requests(requester))
        
        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else:
                government.current_date = string_to_time(clock)

        while True: 
            get_time()
            await government.next()
            msg = {
                "get_cash": dumps(government.cash),
                "get_date": dumps(government.current_date),
                "get_last_collected_taxes": dumps(government.taxes_last_collected),
            }
            await pusher.push(msg)

    except Exception as e:
        print("[Government Error]", e)
        print(traceback.format_exc())
        return None
    except KeyboardInterrupt:
        print("attempting to close government..." )
        return None

if __name__ == '__main__':
    asyncio.run(run_government())