from datetime import datetime

class CryptoTrade():
    def __init__(self, base, quote, qty, price, buyer, seller, dt=None, fee=0):
        self.base = base
        self.quote = quote
        self.qty = qty
        self.price = price
        self.buyer = buyer
        self.seller = seller
        self.dt = dt
        self.fee = fee

    def __repr__(self) -> str:
        return f'<CryptoTrade: {self.base}/{self.quote} {self.qty}@{self.price} {self.dt}>'

    def to_dict(self) -> dict:
        return {
            'dt': self.dt,
            'base': self.base,
            'quote': self.quote,
            'qty': self.qty,
            'price': self.price,
            'buyer': self.buyer,
            'seller': self.seller,
            'fee': self.fee
        }

