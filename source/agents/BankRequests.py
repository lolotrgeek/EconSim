import os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class BankRequests(Requests):
    def __init__(self, requester=None, cache=False):
        super().__init__(requester=requester, cache=cache)

    async def get_reserve(self):
        return await self.make_request('get_reserve', {}, self.requester)
    
    async def get_date(self):
        return await self.make_request('get_date', {}, self.requester)
    
    async def get_loans(self):
        return await self.make_request('get_loans', {}, self.requester)
    
    async def get_deposits(self):
        return await self.make_request('get_deposits', {}, self.requester)
    
    async def get_accounts(self):
        return await self.make_request('get_accounts', {}, self.requester)
    
    async def get_prime_rate(self):
        return await self.make_request('get_prime_rate', {}, self.requester)
    
    async def request_loan(self, borrower, amount):
        return await self.make_request('request_loan', {'borrower': borrower, 'amount': amount}, self.requester)
    
    async def open_savings_account(self, agent, initial_balance):
        return await self.make_request('open_savings_account', {'agent': agent, 'initial_balance': initial_balance}, self.requester)
    
    async def update_prime_rate(self):
        return await self.make_request('update_prime_rate', {}, self.requester)
    
    async def deposit_savings(self, agent, amount):
        return await self.make_request('deposit_savings', {'agent': agent, 'amount': amount}, self.requester)
    
    async def withdraw_savings(self, agent, amount):
        return await self.make_request('withdraw_savings', {'agent': agent, 'amount': amount}, self.requester)

