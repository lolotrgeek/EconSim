from uuid import uuid4 as UUID
from decimal import Decimal
from datetime import datetime

class Position():
    def __init__(self, asset, qty, dt, enters=[], exits=[]):
        self.id: str = str(UUID())
        self.asset: str = asset
        self.qty: Decimal = qty
        self.dt: datetime = dt
        self.enters: list = enters 
        self.exits: list = exits 

    def __repr__(self) -> str:
        return f"Position({self.id}, {self.asset}, {self.qty}, {self.dt})"
    
    def __str__(self) -> str:
        return f"<Position({self.asset} {self.qty} @ {self.dt}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'asset': self.asset,
            'qty': self.qty,
            'dt': self.dt,
            'enters': self.enters,
            'exits': self.exits
        }