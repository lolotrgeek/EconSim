from datetime import datetime

class Trade():
    def __init__(self, ticker, qty, price, buyer, seller, dt=None):
        self.ticker = ticker
        self.qty = qty
        self.price = price
        self.buyer = buyer
        self.seller = seller
        self.dt = dt if dt else datetime.now()

    def __repr__(self):
        return f'<Trade: {self.ticker} {self.qty}@{self.price} {self.dt}>'

    def to_dict(self):
        return {
            'dt': self.dt,
            'ticker': self.ticker,
            'qty': self.qty,
            'price': self.price,
            'buyer': self.buyer,
            'seller': self.seller
        }

