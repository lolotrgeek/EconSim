from source.agents.BankRequests import BankRequests
from source.Messaging import Requester
import asyncio


async def RequestBank():
    try:
        requester = Requester(channel=5582)
        await requester.connect()
        bank_requests = BankRequests(requester=requester)

        assert bank_requests != None

        loan = await requester.request_lazy({"topic": 'request_loan', "borrower":"borrower", "amount": 100})
        print("loan", loan)
        

        account = await requester.request_lazy({"topic": "open_savings_account", "agent": "agent", "initial_balance" :100})
        print("account", account)
        

        deposit = await requester.request_lazy({"topic": "deposit", "agent": "agent","amount": 100})
        print("deposit", deposit)
        

        withdraw = await requester.request_lazy({"topic": "withdraw", "agent": "agent","amount": 100})
        print("withdraw", withdraw)
        
    except Exception as e:
        print("[Error]", e)

if __name__ == '__main__':
    asyncio.run(RequestBank())