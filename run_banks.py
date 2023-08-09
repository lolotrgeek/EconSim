import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import traceback
from source.Messaging import Responder, Requester, Subscriber, Pusher
from source.agents.Bank import Bank
from source.exchange.ExchangeRequests import ExchangeRequests as Requests
from source.utils._utils import dumps, string_to_time
from rich import print


async def run_banks(bank_channel=5581, bank_response_channel = 5582, exchange_channel = 5570, time_channel = 5114) -> None:
    try:
        pusher = Pusher(bank_channel)
        responder = Responder(bank_response_channel)
        requester = Requester(channel=exchange_channel)
        time_puller = Subscriber(time_channel)
        await responder.connect()
        await requester.connect()
        bank = Bank(requester=Requests(requester))
        
        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else:
                bank.current_date = string_to_time(clock)

        async def callback(msg):
            if msg['topic'] == 'request_loan': return  dumps(await bank.issue_loan(msg['borrower'], msg['amount']))
            elif msg['topic'] == 'open_savings_account': return dumps(await bank.open_savings_account(msg['agent'], msg['initial_balance']))
            elif msg['topic'] == 'update_prime_rate': return dumps(await bank.update_prime_rate())
            elif msg['topic'] == 'deposit': return dumps(await bank.deposit_savings(msg['agent'], msg['amount']))
            elif msg['topic'] == 'withdraw': return dumps(await bank.withdraw_savings(msg['agent'], msg['amount']))
            else: return f"Unknown topic: {msg['topic']}"

        while True: 
            get_time()
            await bank.next()
            
            msg = {
                "get_reserve": dumps(bank.reserve),
                "get_date": dumps(bank.current_date),
                "get_loans": dumps(bank.loans),
                "get_deposits": dumps(bank.deposits),
                "get_accounts": dumps(bank.accounts),
                "get_prime_rate": dumps(bank.prime_rate),
            }
            await pusher.push(msg)
            await responder.lazy_respond(callback=callback)

    except Exception as e:
        print("[Bank Error]", e)
        print(traceback.format_exc())
        return None
    except KeyboardInterrupt:
        print("attempting to close Bank..." )
        return None

if __name__ == '__main__':
    asyncio.run(run_banks())