from .Trader import Trader
import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)


class StockTrader(Trader):
    def __init__(self, name:str, aum:int=10_000, exchange_requests=None, public_company_requests=None):
        super().__init__(name, aum, requests=exchange_requests)
        self.public_company_requests = public_company_requests

    def __repr__(self):
        return f'<StockTrader: {self.name}>'

    def __str__(self):
        return f'<StockTrader: {self.name}>'
    
    async def get_income_statement(self, company) -> str:
        return await self.public_company_requests.get_income_statement(company)
    
    async def get_balance_sheet(self, company) -> str:
        return await self.public_company_requests.get_balance_sheet(company)

    async def get_cash_flow(self, company) -> str:
        return await self.public_company_requests.get_cash_flow(company)
    
    async def get_dividend_payment_date(self, company) -> str:
        return await self.public_company_requests.get_dividend_payment_date(company)
    
    async def get_ex_dividend_date(self, company) -> str:
        return await self.public_company_requests.get_ex_dividend_date(company)
    
    async def get_dividends_to_distribute(self, company) -> str:
        return await self.public_company_requests.get_dividends_to_distribute(company)

   