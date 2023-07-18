from uuid import uuid4 as UUID
class Transaction():
    def __init__(self, cash_flow, ticker, qty, dt, side, pnl=0, enter_id=None):
        """
        Represents one side of a transaction.
        """
        self.id = str(UUID())
        self.cash_flow = cash_flow
        self.ticker = ticker
        self.qty = qty
        self.dt = dt
        self.type = side
        self.pnl = pnl
        self.enter_id = enter_id

    def __repr__(self):
        return f"Transaction({self.id}, {self.cash_flow}, {self.ticker}, {self.qty}, {self.dt}, {self.type})"
    
    def __str__(self):
        return f"<Transaction({self.ticker} {self.qty} @ {self.dt}>"

    def to_dict(self):
        return {
            'id': self.id,
            'cash_flow': self.cash_flow,
            'ticker': self.ticker,
            'qty': self.qty,
            'dt': self.dt,
            'type': self.type,
            'pnl': self.pnl
        }

