import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from .Blockchain import Blockchain
from decimal import Decimal
from source.utils._utils import prec

class CryptoCurrency():
    def __init__(self, name:str, startdate, base_unit_name='sats', precision=8, max_supply=0, requester=None) -> None:
        self.name = name
        self.symbol = name[:3].upper()
        self.base_unit = 100_000_000
        self.precision = precision
        self.base_unit_name = base_unit_name 
        self.blockchain = Blockchain(self.symbol, startdate)
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
    
    async def to_base_unit(self, amount:Decimal) -> int:
        amount_decimal = str(amount).split('.') 
        if len(amount_decimal) == 2:
            amount_places = len(amount_decimal[1])
            if amount_places > self.precision:
                return FloatingPointError(f"amount {str(amount)} cannot have more than {self.precision} decimal places") 
        return float(amount) * self.base_unit
    
    async def from_base_unit(self, amount:Decimal) -> Decimal:
        amount_len = len(str(amount))
        if amount_len > 15:
            return(Decimal(str(amount)[:-8]+'.'+str(amount)[-8:]))
        return prec(str(amount / self.base_unit), self.precision)

    async def validate_address(self, address:str) -> bool:
        return type(address) == str and address.isalnum() and len(address) >= 26 and len(address) <= 35

    async def issue_coins(self, pairs:list, amount:Decimal) -> None:
        self.supply += amount
        return await self.requests.create_asset(self.symbol, pairs, self.precision)

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
        self.supply += prec(transactions['confirmed'] * self.block_reward)
        if self.max_supply > 0 and len(self.blockchain.chain) - self.last_halving_block >= self.halving_period:
            await self.halving()