import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class WalletRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def request_signature(self, address, txn) -> str:
        return await self.make_request('request_signature', {'address':address, 'txn': txn}, self.requester)
    
    async def get_balance(self,address, asset) -> str:
        return await self.make_request('get_balance', {'address': address, 'asset': asset}, self.requester)
    