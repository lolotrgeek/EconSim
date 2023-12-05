from uuid import uuid4 as UUID
from decimal import Decimal
from datetime import datetime
from .Fee import Fee
from copy import copy

class Side():
    def __init__(self, agent: str, order_id: str, quote_flow: Decimal, price: Decimal, base: str, quote: str, qty: Decimal, fee: Fee, network_fee: Fee, dt: datetime, type):
        """
        Represents one side of a transaction.
        """
        self.id = str(UUID())
        self.agent: str = agent
        self.order_id: str = order_id
        self.quote_flow: Decimal = quote_flow
        self.price: Decimal = price
        self.base: str = base
        self.quote: str = quote
        self.qty: Decimal = qty
        self.fee: Fee = fee
        self.network_fee: Fee = network_fee
        self.dt: datetime = dt
        self.type: str = type

    def __repr__(self) -> str:
        return f"Side({self.id}, {self.agent}, {self.order_id}, {self.quote_flow}, {self.price}, {self.base}, {self.quote}, {self.qty}, {self.fee}, {self.network_fee}, {self.dt}, {self.type})"
    
    def __str__(self) -> str:
        return f"<Side {self.type} {self.base}/{self.quote} {self.qty} @ {self.price}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'agent': self.agent,
            'order_id': self.order_id,
            'quote_flow': self.quote_flow,
            'price': self.price,
            'base': self.base,
            'quote': self.quote,
            'qty': self.qty,
            'fee': self.fee.to_dict(),
            'network_fee': self.network_fee.to_dict(),
            'dt': self.dt,
            'type': self.type,
        }
    
    def copy(self):
        return copy(self)