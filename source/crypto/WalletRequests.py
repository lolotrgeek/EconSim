import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class WalletRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def new_wallet(self, name:str):
        return await self.make_request('new_wallet', {'name': name}, self.requester)

    async def connect(self, chain:str):
        return await self.make_request('connect', {'chain': chain}, self.requester)
    
    async def sign_txn(self, txn, decision) -> str:
        return await self.make_request('sign_txn', {'txn': txn, 'decision': decision}, self.requester)

    async def cancel_transaction(self, txn_id) -> str:
        return await self.make_request('cancel_transaction', {'txn_id': txn_id}, self.requester)

    async def request_signature(self, address, txn) -> str:
        return await self.make_request('request_signature', {'address':address, 'txn': txn}, self.requester)
    
    async def get_signature_requests(self, address) -> str:
        return await self.make_request('get_signature_requests', {'address': address}, self.requester)
    
    async def get_balance(self,address, asset=None) -> str:
        return await self.make_request('get_balance', {'address': address, 'asset': asset}, self.requester)
    
    async def transaction_confirmed(self, address, txn) -> str:
        return await self.make_request('transaction_confirmed', {'address': address, 'txn': txn}, self.requester)
    
    async def transaction_failed(self, address, txn) -> str:
        return await self.make_request('transaction_failed', {'address': address, 'txn': txn}, self.requester)
    