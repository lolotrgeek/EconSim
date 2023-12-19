import pandas as pd
from typing import List, Union
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decimal import Decimal
from source.utils.logger import Logger
from source.utils._utils import prec
from source.crypto.Wallet import Wallet

class TraderDefi():
    def __init__(self, name:str, aum:int=10_000, exchange_requests=None, crypto_requests=None):
        self.name = name
        self.exchange_requests = exchange_requests
        self.crypto_requests = crypto_requests
        self.wallet = Wallet(name, exchange_requests)
        self.current_date = None

    def __repr__(self):
        return f'<TraderDefi: {self.name}>'

    def __str__(self):
        return f'<TraderDefi: {self.name}>'
    
    async def provide_liquidity(self, agent_wallet, base, quote, amount, fee_level=-1, high_range='.8', low_range='.2') -> dict:
        liquidity_provided = await self.exchange_requests.provide_liquidity(self, agent_wallet, base, quote, amount, fee_level, high_range, low_range)
        return liquidity_provided
    
    async def remove_liquidity(self, agent_wallet, base, quote, amount, fee_level=-1) -> dict:
        liquidity_removed = await self.exchange_requests.remove_liquidity(self, agent_wallet, base, quote, amount, fee_level)
        return liquidity_removed
    
    async def swap(self, agent_wallet, base, quote, amount, slippage='.05') -> dict:
        swap = await self.exchange_requests.swap(self, agent_wallet, base, quote, amount, slippage)
        return swap
    
    async def get_fee_levels(self) -> dict:
        fee_levels = await self.exchange_requests.get_fee_levels()
        return fee_levels
    
    async def get_pools(self) -> dict:
        pools = await self.exchange_requests.get_pools()
        return pools
    
    async def get_pool(self, base, quote, fee_level=-1) -> dict:
        pool = await self.exchange_requests.get_pool(base, quote, fee_level)
        return pool