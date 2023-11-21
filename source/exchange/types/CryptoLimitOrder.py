import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from decimal import Decimal
from .OrderSide import OrderSide
from source.utils._utils import get_random_string, prec

class CryptoLimitOrder():
    def __init__(self, base, quote, price, qty, creator, side, dt=None, exchange_fee=0, network_fee=0, status='open', accounting='FIFO', position_id=None, fills =[]):
        self.id = get_random_string()
        self.base: str = base
        self.quote: str = quote   
        self.ticker: str = base+quote
        self.price: Decimal = price
        self.type: OrderSide = side
        self.qty: Decimal = qty
        self.creator: str = creator
        self.dt: datetime = dt if dt else datetime.now()
        self.minimum_match_percent: Decimal = Decimal('0.05')
        self.minimum_match_qty: Decimal = 0
        self.network_fee: Decimal = network_fee # base currency for sell, quote currency for buy
        self.network_fee_per_txn: Decimal = 0
        self.remaining_network_fee = self.network_fee        
        self.exchange_fee: Decimal = exchange_fee #NOTE: the fee is assessed in base currency for sell, quote currency for buy to match the network fee
        self.exchange_fee_per_qty: Decimal = 0
        self.exchange_fees_due = 0
        self.unfilled_qty = qty
        self.position_id: str = position_id
        self.accounting :str = accounting
        self.fills: list = fills
        self.status:str = status # open, filled, cancelled, error, partial, unconfirmed

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
            'base' : self.base,
            'quote': self.quote,
            'price': self.price,
            'qty': self.qty,
            'creator': self.creator,
            'type': 'limit_buy' if self.type == OrderSide.BUY else 'limit_sell',
            'dt': self.dt,
            'exchange_fee': self.exchange_fee,
            'network_fee': self.network_fee,
            'network_fee_per_txn': self.network_fee_per_txn,
            'remaining_network_fee': self.remaining_network_fee,
            'exchange_fees_due': self.exchange_fees_due,
            'unfilled_qty': self.unfilled_qty,
            'accounting': self.accounting,
            'position_id': self.position_id,
            'fills': self.fills,
            'status': self.status
        }    

    def __repr__(self) -> str:
        return f'<CryptoLimitOrder: {self.ticker} {self.type} {self.qty}@{self.price}>'

    def __str__(self) -> str:
        return f'<CryptoLimitOrder: {self.ticker} {self.type} {self.qty}@{self.price}>'