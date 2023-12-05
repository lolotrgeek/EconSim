from decimal import Decimal
from copy import copy
from datetime import datetime

class TaxableEvent():
    def __init__(self, type: str, enter_date: datetime, exit_date: datetime, pnl: Decimal):
        self.type: str = type
        self.enter_date: datetime = enter_date
        self.exit_date: datetime = exit_date
        self.pnl: Decimal = pnl

    def __repr__(self) -> str:
        return f"TaxableEvent({self.id}, {self.type}, {self.enter_date}, {self.exit_date}, {self.pnl})"
    
    def __str__(self) -> str:
        return f"<TaxableEvent {self.type} {self.enter_date} {self.exit_date} {self.pnl}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'enter_date': self.enter_date,
            'exit_date': self.exit_date,
            'pnl': self.pnl
        }
    
    def copy(self):
        return copy(self)