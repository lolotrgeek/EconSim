import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from datetime import datetime
import traceback
from source.Messaging import Responder, Requester, Puller
from source.agents.Government import Government
from source.utils._utils import dumps
from rich import print
from rich.live import Live
from rich.table import Table


async def run_government(exchange_channel = 5570, time_channel = 5114):
    try:
        requester = Requester(channel=exchange_channel)
        time_puller = Puller(time_channel)
        await requester.connect()
        government = Government(requester=requester)


        def get_time():
            clock = time_puller.pull()
            if clock == None: 
                pass
            elif type(clock) is dict and 'time' not in clock:
                pass
            elif type(clock['time']) is dict:
                pass
            else: 
                government.current_date = datetime.strptime(clock['time'], '%Y-%m-%d %H:%M:%S')
                print(government.current_date)

        while True: 
            get_time()
            await government.next()
            await asyncio.sleep(0.1)

    except Exception as e:
        print("[Government Error]", e)
        print(traceback.format_exc())
        return None
    except KeyboardInterrupt:
        print("attempting to close government..." )
        return None

if __name__ == '__main__':
    asyncio.run(run_government())