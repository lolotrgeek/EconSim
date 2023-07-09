from random import randint
import traceback
from source.Messaging import Requester
from source.exchange.API import API
from rich import print
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_api(loop, exchange_channel = 5570):
    try:
        requester = Requester(exchange_channel)
        await requester.connect()
        api = API(requester)
        await api.run_task()
    except Exception as e:
        print("[API Error] ", e)
        return None
    except  KeyboardInterrupt:
        print("attempting to close api..." )
        return None

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop() 
        loop.run_until_complete(run_api(loop))
    except Exception as e:
        print("[API Error] ", e)
        traceback.print_exc()    