import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
import traceback
from runner import Runner
from source.Messaging import Requester, Publisher
from source.agents.Government import Government
from source.exchange.CryptoExchangeRequests import CryptoExchangeRequests as Requests
from source.utils._utils import dumps
from rich import print

class GovernmentRunner(Runner):
    def __init__(self):
        super().__init__()
        self.requester = Requester(self.channels.crypto_exchange_channel)
        self.publisher = Publisher(self.channels.government_channel)
        self.government = None

    async def set_government(self):
        self.government = Government(requests=Requests(self.requester))

    async def run(self) -> None:
        try:
            await self.requester.connect()
            await self.set_government()
            while True: 
                self.government.current_date = await self.get_time()
                next = await self.government.next()
                if not next:
                    break
                await self.publisher.publish("get_cash", dumps(self.government.cash))
                await self.publisher.publish("get_date", dumps(self.government.current_date))
                await self.publisher.publish("get_last_collected_taxes", dumps(self.government.taxes_last_collected))
                await self.publisher.publish("get_taxes_collected", dumps(self.government.tax_records))
                await self.publisher.publish("get_back_taxes", dumps(self.government.back_taxes))

        except Exception as e:
            print("[Government Error]", e)
            print(traceback.format_exc())
            return None
        except KeyboardInterrupt:
            print("attempting to close government..." )
            return None

if __name__ == '__main__':
    runner = GovernmentRunner()
    asyncio.run(runner.run())