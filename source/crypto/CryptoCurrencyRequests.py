import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class CryptoCurrencyRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def get_transactions(self, asset) -> str:
        return await self.make_request('get_transactions', {'asset': asset}, self.requester)
    
    async def get_transaction(self, asset, id) -> str:
        return await self.make_request('get_transaction', {'asset': asset, 'id': id}, self.requester)
    
    async def add_transaction(self, asset:str, fee:float, amount:float, sender:str, recipient:str) -> str:
        return await self.make_request('add_transaction', {'asset': asset, 'fee': fee, 'amount': amount, 'sender': sender, 'recipient': recipient}, self.requester)

    async def get_mempool(self, asset) -> str:
        return await self.make_request('get_mempool', {'asset', asset}, self.requester)
    
    async def get_pending_transactions(self, asset) -> str:
        return await self.make_request('get_pending_transactions', {'asset': asset}, self.requester)
    
    async def get_confirmed_transactions(self, asset) -> str:
        return await self.make_request('get_confirmed_transactions', {'asset': asset}, self.requester)