import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from decimal import Decimal
from .OrderSide import OrderSide
from .OrderType import OrderType
from source.utils._utils import get_random_string

class CryptoOrder():
    def __init__(self, base, quote, price, qty, creator, order_type, side, dt=None, exchange_fee=0, network_fee=0, status='open', accounting='FIFO', position_id=None, fills =[]):
        self.id = get_random_string()
        self.creator: str = creator
        self.dt: datetime = dt if dt else datetime.now()
        self.base: str = base
        self.quote: str = quote   
        self.ticker: str = base+quote
        self.side: OrderSide = side
        self.type:OrderType = order_type        
        self.price: Decimal = price
        self.qty: Decimal = qty
        self.minimum_match_qty: Decimal = 0
        self.total_possible_matches: Decimal = 0
        self.total_price: Decimal = 0
        self.min_price_per_match: Decimal = 0
        self.total_filled_price: Decimal = 0
        self.network_fee: Decimal = network_fee # base currency for sell, quote currency for buy
        self.network_fee_per_txn: Decimal = 0
        self.remaining_network_fee = self.network_fee        
        self.exchange_fee: Decimal = exchange_fee #NOTE: the fee is assessed in base currency for sell, quote currency for buy to match the network fee
        self.exchange_fee_per_txn: Decimal = 0
        self.exchange_fees_due: Decimal = 0
        self.unfilled_qty = qty
        self.position_id: str = position_id
        self.accounting :str = accounting
        self.fills: list = fills
        self.status:str = status # open, filled, cancelled, error, partial, unconfirmed

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price': self.price,
            'qty': self.qty,
            'type': self.type,
            'side': self.side,
            'dt': self.dt,
        }
    
    def to_dict_full(self) -> dict:
        return {
            'id': self.id,
            'ticker': self.ticker,
            'base' : self.base,
            'quote': self.quote,
            'price': self.price,
            'qty': self.qty,
            'creator': self.creator,
            'type': self.type.value,
            'side': self.side.value,
            'dt': self.dt,
            'exchange_fee': self.exchange_fee,
            'network_fee': self.network_fee,
            'network_fee_per_txn': self.network_fee_per_txn,
            'remaining_network_fee': self.remaining_network_fee,
            'exchange_fees_due': self.exchange_fees_due,
            'unfilled_qty': self.unfilled_qty,
            'total_price': self.total_price,
            'total_filled_price': self.total_filled_price,
            'accounting': self.accounting,
            'position_id': self.position_id,
            'fills': self.fills,
            'status': self.status
        }

    def __repr__(self) -> str:
        return f'<CryptoOrder: {self.ticker} {self.type} {self.side} {self.qty}@{self.price}>'

    def __str__(self) -> str:
        return f'<CryptoOrder: {self.ticker} {self.type} {self.side} {self.qty}@{self.price}>'