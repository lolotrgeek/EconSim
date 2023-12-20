import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import traceback
import sys, os
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
from runner import Runner
from source.Messaging import Responder, Requester, Subscriber, Pusher
from source.agents.Bank import Bank
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps
from source.Channels import Channels
from rich import print

class BankRunner(Runner):
    def __init__(self):
        self.channels = Channels()
        self.pusher = Pusher(self.channels.bank_channel)
        self.responder = Responder(self.channels.bank_response_channel)
        self.requester = Requester(self.channels.exchange_channel)
        self.time_puller = Subscriber(self.channels.time_channel)
        self.bank = None
        self.companies = []

    async def callback(self, msg) -> str:
        if msg['topic'] == 'apply_for_loan': return  dumps(await self.bank.apply_for_loan(msg['borrower']))
        elif msg['topic'] == 'pay_loan': return dumps(await self.bank.pay_loan(msg ['id'], msg['borrower'], msg['amount']))
        elif msg['topic'] == 'get_loans': return dumps(await self.bank.get_loans(msg['borrower']))
        elif msg['topic'] == 'get_credit_score': return dumps(await self.bank.get_credit(msg['borrower']))
        elif msg['topic'] == 'open_savings_account': return dumps(await self.bank.open_savings_account(msg['agent'], msg['initial_balance']))
        elif msg['topic'] == 'update_prime_rate': return dumps(await self.bank.update_prime_rate())
        elif msg['topic'] == 'deposit': return dumps(await self.bank.deposit_savings(msg['agent'], msg['amount']))
        elif msg['topic'] == 'withdraw': return dumps(await self.bank.withdraw_savings(msg['agent'], msg['amount']))
        else: return f"Unknown topic: {msg['topic']}"

    async def run(self) -> None:
        try: 
            await self.responder.connect()
            await self.requester.connect()
            self.bank = Bank(requests=Requests(self.requester))

            while True:
                self.bank.current_date = (await self.get_time())
                await self.bank.next()
                msg = {
                    "get_reserve": dumps(self.bank.reserve),
                    "get_date": dumps(self.bank.current_date),
                    "get_loans": dumps(await self.bank.get_loans()),
                    "get_deposits": dumps(self.bank.deposits),
                    "get_accounts": dumps(await self.bank.get_accounts()),
                    "get_prime_rate": dumps(self.bank.prime_rate),
                    "get_credit": dumps(await self.bank.get_credit_scores()),
                }
                await self.pusher.push(msg)
                msg = await self.responder.lazy_respond(callback=self.callback)
                if msg == 'STOP':
                    break

        except Exception as e:
            print("[Bank Error]", e)
            print(traceback.format_exc())
            return None
        except KeyboardInterrupt:
            print("attempting to close Bank..." )
            return None

if __name__ == '__main__':
    runner = BankRunner()
    asyncio.run(runner.run())