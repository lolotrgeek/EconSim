from source.Messaging import Requester
import json
import asyncio


async def RequestBank():
    try:
        requester = Requester(channel=5582)
        await requester.connect()

        account = await requester.request_lazy({"topic": "open_savings_account", "agent": "agent", "initial_balance" :200})
        print( account)

        loan = await requester.request_lazy({"topic": 'apply_for_loan', "borrower":"agent"})
        print( loan)

        get_loan = await requester.request_lazy({"topic": "get_loans", "borrower": "agent"})
        print( get_loan)

        parsed_loan = json.loads(get_loan)

        pay_loan = await requester.request_lazy({"topic": "pay_loan", "id": parsed_loan[0]['id'], "borrower": "agent", "amount": 100})
        print( pay_loan)

        get_credit = await requester.request_lazy({"topic": "get_credit_score", "borrower": "agent"})
        print( get_credit)

        afterpay_loan = await requester.request_lazy({"topic": "get_loans", "borrower": "agent"})
        print( afterpay_loan)
        
        deposit = await requester.request_lazy({"topic": "deposit", "agent": "agent","amount": 100})
        print( deposit)
        
        withdraw = await requester.request_lazy({"topic": "withdraw", "agent": "agent","amount": 100})
        print( withdraw)
        
    except Exception as e:
        print("[Error]", e)

if __name__ == '__main__':
    asyncio.run(RequestBank())