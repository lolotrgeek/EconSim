import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class PublicCompanyRequests(Requests):
    def __init__(self, requester):
        super().__init__(requester)

    async def get_price_bars(self, ticker, interval, limit) -> str:
        return await self.make_request('candles', {'ticker': ticker, 'interval': interval, 'limit': limit}, self.requester)

    async def get_income_statement(self, company) -> str:
        return await self.make_request('get_income_statement', {'company': company}, self.requester)
    
    async def get_balance_sheet(self, company) -> str:
        return await self.make_request('get_balance_sheet', {'company': company}, self.requester)
    
    async def get_cash_flow(self, company) -> str:
        return await self.make_request('get_cash_flow', {'company': company}, self.requester)
    
    async def get_dividend_payment_date(self, company) -> str:
        return await self.make_request('get_dividend_payment_date', {'company': company}, self.requester)
    
    async def get_ex_dividend_date(self, company) -> str:
        return await self.make_request('get_ex_dividend_date', {'company': company}, self.requester)
    
    async def get_dividends_to_distribute(self, company) -> str:
        return await self.make_request('get_dividends_to_distribute', {'company': company}, self.requester)