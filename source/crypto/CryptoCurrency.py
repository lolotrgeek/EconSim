import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .Blockchain import Blockchain
from decimal import Decimal
from source.utils._utils import prec

class CryptoCurrency():
    def __init__(self, name:str, startdate, max_supply=0, decimals=8) -> None:
        self.name = name
        self.symbol = name[:3].upper()
        self.decimals = decimals
        self.blockchain = Blockchain(self.symbol, startdate, decimals)
        self.supply = 1
        self.block_reward = 50
        self.max_supply = max_supply # 0 means no max supply 
        self.burn_address = '0x00000000000000000000000000'
        self.startdate = startdate
        self.currentdate = startdate
        self.halving_period = 210_000 # halve the block reward every 210,000 blocks
        self.last_halving_block = 0   

    def __str__(self) -> str:
        return f"<CryptoCurrency {self.name}, {self.symbol}, {self.blockchain}>"
    
    def __repr__(self) -> str:
        return f"<CryptoCurrency {self.name}, {self.symbol}, {self.blockchain}>"
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "decimals": self.decimals,
            "startdate": self.startdate,
            "currentdate": self.currentdate,
            "supply": self.supply,
            "block_reward": self.block_reward,
            "max_supply": self.max_supply,
            "burn_address": self.burn_address,
            "halving_period": self.halving_period,
            "last_halving_block": self.last_halving_block,
        }

    async def validate_address(self, address:str) -> bool:
        return type(address) == str and address.isalnum() and len(address) >= 26 and len(address) <= 35

    async def halving(self):
        # reduce the block reward on a halving schedule, asymptotically approaching the max supply
        self.last_halving_block = len(self.blockchain.chain)
        self.block_reward = prec(str(self.block_reward / 2))

    async def get_last_fee(self) -> Decimal:
        return self.blockchain.chain[-1].fee
    
    async def get_fees(self, num) -> list:
        return list(map(lambda block: str(block.fee), self.blockchain.chain[-num:]))

    async def next(self, currentdate) -> None:
        self.currentdate = currentdate
        self.blockchain.datetime = currentdate
        transactions = await self.blockchain.process_transactions()
        self.supply += transactions['confirmed'] * self.block_reward
        if self.max_supply > 0 and len(self.blockchain.chain) - self.last_halving_block >= self.halving_period:
            await self.halving()