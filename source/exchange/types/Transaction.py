from uuid import uuid4 as UUID

from .Side import Side

class Transaction():
    def __init__(self, cash_flow, ticker, price, qty, dt, side):
        """
        Represents a transaction.
        """
        self.buy = [Side(self, str(UUID()), cash_flow, price, ticker, 'USD', qty, 0, 0, dt, side)]

    def __repr__(self) -> str:
        return f"Transaction({self.id}, {self.cash_flow}, {self.ticker}, {self.qty}, {self.dt}, {self.type})"
    
    def __str__(self) -> str:
        return f"<Transaction({self.ticker} {self.qty} @ {self.dt}>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'cash_flow': self.cash_flow,
            'ticker': self.ticker,
            'price': self.price,
            'qty': self.qty,
            'dt': self.dt,
            'type': self.type,
        }
