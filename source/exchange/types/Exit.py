from uuid import uuid4 as UUID
from datetime import datetime
from decimal import Decimal
from .Basis import Basis
from copy import copy

class Exit():
    def __init__(self, agent: str, asset: str, dt: datetime, enter_id: str, basis: Basis):
        self.id = str(UUID())
        self.agent: str = agent
        self.asset: str = asset
        self.qty: Decimal = 0
        self.dt: datetime = dt
        self.enter_id: str = enter_id
        self.basis: Basis = basis
        self.error: str = None

    def __repr__(self) -> str:
        return f"Exit({self.id}, {self.agent}, {self.asset}, {self.qty}, {self.dt}, {self.enter_id}, {self.basis})"
    
    def __str__(self) -> str:
        return f"<Exit {self.asset} {self.qty} {self.dt}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'agent': self.agent,
            'asset': self.asset,
            'qty': self.qty,
            'dt': self.dt,
            'enter_id': self.enter_id,
            'basis': self.basis.to_dict()
        }
    
    def copy(self):
        return copy(self)    