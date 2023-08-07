import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Puller
from source.agents.Government import Government
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps, string_to_time
from rich import print
from rich.live import Live
from rich.table import Table


async def run_government(government_channel=5580, exchange_channel = 5570, time_channel = 5114) -> None:
    try:
        responder = Responder(government_channel)
        requester = Requester(channel=exchange_channel)
        time_puller = Puller(time_channel)
        await responder.connect()
        await requester.connect()
        government = Government(requester=Requests(requester))

        async def callback(msg) -> str:
            if(msg)['topic'] == 'get_cash': return dumps(await government.get_cash())
            elif msg['topic'] == 'get_date': return dumps(await government.get_date())
            elif msg['topic'] == 'collect_taxes': return dumps(await government.collect_taxes())
            elif msg['topic'] == 'get_last_collected_taxes': return dumps(await government.get_last_collected_taxes())
            else: return f'Invalid topic: {msg["topic"]}'



        def get_time():
            clock = time_puller.pull()
            if clock == None: 
                pass
            elif type(clock) is dict and 'time' not in clock:
                pass
            elif type(clock['time']) is dict:
                pass
            else: 
                government.current_date = string_to_time(clock['time'])

        while True: 
            get_time()
            await government.next()
            msg = await responder.respond(callback)
            if msg is None:
                continue

    except Exception as e:
        print("[Government Error]", e)
        print(traceback.format_exc())
        return None
    except KeyboardInterrupt:
        print("attempting to close government..." )
        return None

if __name__ == '__main__':
    asyncio.run(run_government())