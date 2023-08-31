import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from decimal import Decimal
from .OrderSide import OrderSide
from source.utils._utils import get_random_string

class LimitOrder():

    def __init__(self, ticker, price, qty, creator, side, dt=None, fee=0, accounting='FIFO', position_id=None, fills =[]):
        self.id = get_random_string()
        self.ticker: str = ticker
        self.price: Decimal = price
        self.type: OrderSide = side
        self.qty: int = qty
        self.creator: str = creator
        self.dt: datetime = dt if dt else datetime.now()
        self.fee = fee
        self.position_id = position_id
        self.accounting = accounting
        self.fills = fills

    def to_dict(self) -> dict:
        if self.ticker == 'error' and self.type == OrderSide.BUY: 
            return {'limit_buy': "insufficient funds", 'id': self.id}
        elif self.ticker == 'error' and self.type == OrderSide.SELL:
            return {'limit_sell': "insufficient assets", 'id': self.id}
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price': self.price,
            'qty': self.qty,
            'type': 'limit_buy' if self.type == OrderSide.BUY else 'limit_sell',
            'dt': self.dt,
        }
    
    def to_dict_full(self) -> dict:
        if self.ticker == 'error' and self.type == OrderSide.BUY: 
            return {'limit_buy': "insufficient funds", 'id': self.id}
        elif self.ticker == 'error' and self.type == OrderSide.SELL:
            return {'limit_sell': "insufficient assets", 'id': self.id}
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price': self.price,
            'qty': self.qty,
            'creator': self.creator,
            'type': 'limit_buy' if self.type == OrderSide.BUY else 'limit_sell',
            'dt': self.dt,
            'fee': self.fee,
            'accounting': self.accounting,
            'position_id': self.position_id,
            'fills': self.fills
        }    

    def __repr__(self) -> str:
        return f'<LimitOrder: {self.ticker} {self.qty}@{self.price}>'

    def __str__(self) -> str:
        return f'<LimitOrder: {self.ticker} {self.qty}@{self.price}>'