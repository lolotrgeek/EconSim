import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from decimal import Decimal
from .OrderSide import OrderSide
from source.utils._utils import get_random_string

class CryptoLimitOrder():

    def __init__(self, ticker, price, qty, creator, side, dt=None, exchange_fee=0.0, network_fee=0.0, status='open', accounting='FIFO', position_id=None, fills =[]):
        self.id = get_random_string()
        self.ticker: str = ticker
        self.price: Decimal = price
        self.type: OrderSide = side
        self.qty: Decimal = qty
        self.creator: str = creator
        self.dt: datetime = dt if dt else datetime.now()
        self.exchange_fee = exchange_fee
        self.network_fee = network_fee
        self.position_id = position_id
        self.accounting = accounting
        self.fills = fills
        self.status = status # open, filled, cancelled, error, partial, unconfirmed

    def to_dict(self) -> dict:
        if self.status == 'error' and self.type == OrderSide.BUY: 
            return {'limit_buy': self.accounting, 'id': self.id, 'creator': self.creator}
        elif self.status == 'error' and self.type == OrderSide.SELL:
            return {'limit_sell': self.accounting, 'id': self.id, 'creator': self.creator}
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price': self.price,
            'qty': self.qty,
            'type': 'limit_buy' if self.type == OrderSide.BUY else 'limit_sell',
            'dt': self.dt,
        }
    
    def to_dict_full(self) -> dict:
        if self.status == 'error' and self.type == OrderSide.BUY: 
            return {'limit_buy': self.accounting, 'id': self.id, 'creator': self.creator}
        elif self.status == 'error' and self.type == OrderSide.SELL:
            return {'limit_sell': self.accounting, 'id': self.id, 'creator': self.creator}
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price': self.price,
            'qty': self.qty,
            'creator': self.creator,
            'type': 'limit_buy' if self.type == OrderSide.BUY else 'limit_sell',
            'dt': self.dt,
            'exchange_fee': self.exchange_fee,
            'network_fee': self.network_fee,
            'accounting': self.accounting,
            'position_id': self.position_id,
            'fills': self.fills,
            'status': self.status
        }    

    def __repr__(self) -> str:
        return f'<CryptoLimitOrder: {self.ticker} {self.type} {self.qty}@{self.price}>'

    def __str__(self) -> str:
        return f'<CryptoLimitOrder: {self.ticker} {self.type} {self.qty}@{self.price}>'