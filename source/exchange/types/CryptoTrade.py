from datetime import datetime

class CryptoTrade():
    def __init__(self, base, quote, qty, price, buyer, seller, dt=None, network_fee=0.0, exchange_fee=0.0):
        self.base = base
        self.quote = quote
        self.ticker=base+quote
        self.qty = qty
        self.price = price
        self.buyer = buyer
        self.seller = seller
        self.dt = dt
        self.network_fee = network_fee
        self.exchange_fee = exchange_fee

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
            'network_fee': self.network_fee,
            'exchange_fee': self.exchange_fee,
        }

