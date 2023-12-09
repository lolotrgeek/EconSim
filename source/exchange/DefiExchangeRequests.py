import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class DefiExchangeRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def send_signature(self, decision, txn):
        return await self.make_request('signature', {'decision':decision, 'txn': txn}, self.requester)
