import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class DefiExchangeRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def connect(self):
        return await self.make_request('connect', self.requester)

    async def list_asset(self, asset, decimals):
        return await self.make_request('list_asset', {'asset': asset, 'decimals': decimals }, self.requester)

    async def get_fee_levels(self):
        return await self.make_request('get_fee_levels', {}, self.requester)

    async def get_pools(self):
        return await self.make_request('get_pools', {}, self.requester)

    async def get_pool(self, base, quote, fee_pct):
        return await self.make_request('get_pool', {'base': base, 'quote': quote, 'fee_pct': fee_pct}, self.requester)

    async def get_pool_liquidity(self, base, quote, fee_level=-1):
        return await self.make_request('get_pool_liquidity', {'base': base, 'quote': quote, 'fee_level': fee_level}, self.requester)
    
    async def get_assets(self):
        return await self.make_request('get_assets', {}, self.requester)
    
    async def get_price(self, base, quote, pool_fee_pct, base_amount):
        return await self.make_request('get_price', {'base': base, 'quote': quote, 'pool_fee_pct': pool_fee_pct, 'base_amount': base_amount}, self.requester)

    async def get_position(self, position_address):
        return await self.make_request('get_position', {'position_address': position_address}, self.requester)

    async def add_pending_swap(self, swap):
        return await self.make_request('swap', {'swap': swap}, self.requester)        
    
    async def add_pending_liquidity(self, liquidity):
        return await self.make_request('liquidity', {'liquidity': liquidity}, self.requester)
    
    async def add_pending_remove_liquidity(self, liquidity):
        return await self.make_request('remove_liquidity', {'liquidity': liquidity}, self.requester)
    
    async def add_pending_collect_fees(self, liquidity):
        return await self.make_request('collect_fees', {'liquidity': liquidity}, self.requester)