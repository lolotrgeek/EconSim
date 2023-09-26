
from .Blockchain import Blockchain
import random, string, math

class CryptoCurrency():
    def __init__(self, name:str, startdate, max_supply=0, requester=None) -> None:
        self.name = name
        self.symbol = name[:3].upper()
        self.blockchain = Blockchain(startdate)
        self.supply = 1
        self.block_reward = 50
        self.max_supply = max_supply
        self.burn_address = '0x0'        
        self.startdate = startdate
        self.currentdate = startdate
        self.halving_period = 210_000 # halve the block reward every 210,000 blocks
        self.last_halving_block = 0        
        self.requests = requester

    def __str__(self) -> str:
        return f"<CryptoCurrency {self.name}, {self.symbol}, {self.blockchain}>"
    
    def __repr__(self) -> str:
        return f"<CryptoCurrency {self.name}, {self.symbol}, {self.blockchain}>"
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "symbol": self.symbol,
            "startdate": self.startdate,
            "currentdate": self.currentdate,            
        }

    async def validate_address(self, address:str) -> bool:
        return type(address) == str and address.isalnum() and len(address) >= 26 and len(address) <= 35

    async def issue_coins(self, pairs:list, amount:float) -> None:
        self.supply += amount
        await self.requests.create_asset(self.symbol, pairs)

    async def halving(self):
        # reduce the block reward on a halving schedule, asymptotically approaching the max supply
        self.last_halving_block = len(self.blockchain.chain)
        self.block_reward = self.block_reward / 2

    async def next(self, currentdate) -> None:
        self.currentdate = currentdate
        self.blockchain.datetime = currentdate
        transactions = await self.blockchain.process_transactions()
        self.supply += transactions['confirmed'] * self.block_reward
        if self.max_supply > 0 and len(self.blockchain.chain) - self.last_halving_block >= self.halving_period:
            await self.halving()