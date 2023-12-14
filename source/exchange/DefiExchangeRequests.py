import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Requests import Requests

class DefiExchangeRequests(Requests):
    def __init__(self, requester, cache=False):
        super().__init__(requester, cache)

    async def send_signature(self, agent_wallet, decision, txn):
        return await self.make_request('signature', {'agent_wallet': agent_wallet, 'decision':decision, 'txn': txn}, self.requester)

    async def create_asset(self, asset, decimals):
        return await self.make_request('create_asset', {'asset': asset, 'decimals': decimals }, self.requester)

    async def provide_liquidity(self, agent_wallet, base, quote, amount, fee_level=-1, high_range='.8', low_range='.2'):
        return await self.make_request('provide_liquidity', {'agent_wallet': agent_wallet, 'base': base, 'quote': quote, 'amount': amount, 'fee_level': fee_level, 'high_range': high_range, 'low_range': low_range}, self.requester)
    
    async def remove_liquidity(self, agent_wallet, base, quote, amount, fee_level=-1):
        return await self.make_request('remove_liquidity', {'agent_wallet': agent_wallet, 'base': base, 'quote': quote, 'amount': amount, 'fee_level': fee_level}, self.requester)

    async def swap(self, agent_wallet, base, quote, amount, slippage='.05'):
        return await self.make_request('swap', {'agent_wallet': agent_wallet, 'base': base, 'quote': quote, 'amount': amount, 'wallet': wallet, 'slippage': slippage}, self.requester)

    async def get_fee_levels(self):
        return await self.make_request('get_fee_levels', {}, self.requester)

    async def get_pools(self):
        return await self.make_request('get_pools', {}, self.requester)

    async def get_pool(self, base, quote, fee_level=-1):
        return await self.make_request('get_pool', {'base': base, 'quote': quote, 'fee_level': fee_level}, self.requester)

    async def get_pool_liquidity(self, base, quote, fee_level=-1):
        return await self.make_request('get_pool_liquidity', {'base': base, 'quote': quote, 'fee_level': fee_level}, self.requester)
    
    async def get_assets(self):
        return await self.make_request('get_assets', {}, self.requester)