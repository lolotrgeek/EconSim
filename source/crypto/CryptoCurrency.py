
from Blockchain import Blockchain
import random, string, math

class CryptoCurrency():
    def __init__(self, name:str, startdate, requester) -> None:
        self.name = name
        self.symbol = name[:3].upper()
        self.blockchain = Blockchain()
        self.supply = 1
        self.max_supply = 0
        self.burn_address = '0x0'
        self.halving_schedule = (math.log(self.max_supply / self.supply) / math.log(2))        
        self.startdate = startdate
        self.currentdate = startdate        
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

    async def issue_coins(self, fee:float, amount:float) -> None:
        self.supply += amount
        self.requests.create_asset(self.symbol, qty=amount, seed_price=fee, seed_bid=fee * 0.99, seed_ask=fee * 1.01)

    async def next(self) -> None:
        self.blockchain.process_transactions()
        if self.max_supply > 0:
            # add coins to the supply on a halving schedule, asymptotically approaching the max supply
            self.supply += (self.max_supply - self.supply) / self.halving_schedule
        pass