from source.Messaging import Requester
import json
import asyncio

async def RequestCompany():
    try:
        requester = Requester(channel=5572)
        await requester.connect()

        date = await requester.request_lazy({"topic": "get_date"})
        print(date)
        
        raw_companies = await requester.request_lazy({"topic": "get_companies"})
        companies = json.loads(raw_companies)
        print(companies)
        
        company = companies[0]

        income_statement = await requester.request_lazy({"topic": "get_income_statement", "company": company})
        print(income_statement)

        balance_sheet = await requester.request_lazy({"topic": "get_balance_sheet", "company": company})
        print(balance_sheet)

        cash_flow = await requester.request_lazy({"topic": "get_cash_flow", "company": company})
        print(cash_flow)

        dividend_payment_date = await requester.request_lazy({"topic": "get_dividend_payment_date", "company": company})
        print(dividend_payment_date)

    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(RequestCompany())
        