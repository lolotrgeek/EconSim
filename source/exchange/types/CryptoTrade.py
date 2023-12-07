from datetime import datetime
from .Fee import Fee
from decimal import Decimal

class CryptoTrade():
    def __init__(self, base: str, quote: str, qty: Decimal, price: Decimal, buyer: str, seller: str, dt:datetime=None, network_fee={"base": 0, "quote":0}, exchange_fee={"base":0, "quote":0}):
        self.base: str = base
        self.quote: str = quote
        self.ticker = self.base + self.quote
        self.qty: Decimal = qty
        self.price: Decimal = price
        self.buyer: str = buyer
        self.seller: str = seller
        self.dt: datetime = dt
        self.network_fee: Fee = network_fee
        self.exchange_fee: Fee = exchange_fee

    def __repr__(self) -> str:
        return f"CryptoTrade({self.base}, {self.quote}, {self.qty}, {self.price}, {self.buyer}, {self.seller}, {self.dt}, {self.network_fee}, {self.exchange_fee})"
    
    def __str__(self) -> str:
        return f"<CryptoTrade {self.base}/{self.quote} {self.qty} @ {self.price}>"
    
    def to_dict(self) -> dict:
        return {
            'base': self.base,
            'quote': self.quote,
            'ticker': self.ticker,
            'qty': self.qty,
            'price': self.price,
            'buyer': self.buyer,
            'seller': self.seller,
            'dt': self.dt,
            'network_fee': self.network_fee if type(self.network_fee) == dict else self.network_fee.to_dict(),
            'exchange_fee': self.exchange_fee if type(self.exchange_fee) == dict else self.exchange_fee.to_dict()
        }