
from uuid import uuid4 as UUID
from decimal import Decimal
from datetime import datetime
from .Basis import Basis
from copy import copy

class Enter():
    def __init__(self, agent: str, asset: str, qty: Decimal, dt: datetime, type: str, basis: Basis):
        self.id = str(UUID())
        self.agent: str = agent
        self.asset: str = asset
        self.initial_qty: Decimal = qty
        self.qty: Decimal = qty
        self.dt: datetime = dt
        self.type: str = type
        self.basis: Basis = basis
        self.error: str = None

    def __repr__(self) -> str:
        return f"Enter({self.id}, {self.agent}, {self.asset}, {self.initial_qty}, {self.qty}, {self.dt}, {self.type}, {self.basis})"
    
    def __str__(self) -> str:
        return f"<Enter {self.asset} {self.qty} {self.dt}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'agent': self.agent,
            'asset': self.asset,
            'initial_qty': self.initial_qty,
            'qty': self.qty,
            'dt': self.dt,
            'type': self.type,
            'basis': self.basis.to_dict()
        }
    def copy(self):
        return copy(self)