from uuid import uuid4 as UUID
class Transaction():
    def __init__(self, cash_flow, ticker, price, qty, dt, side):
        """
        Represents one side of a transaction.
        """
        self.id = str(UUID())
        self.cash_flow = cash_flow
        self.price = price
        self.ticker = ticker
        self.qty = qty
        self.dt = dt
        self.type = side

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

class Exit(Transaction):
    def __init__(self, cash_flow, ticker,price, qty, dt, side, pnl, enter_id, enter_date):
        super().__init__(cash_flow, ticker,price, qty, dt, side)
        self.pnl = pnl
        self.enter_id = enter_id
        self.enter_date = enter_date

    def __repr__(self) -> str:
        return f"Exit({self.id}, {self.cash_flow}, {self.ticker}, {self.qty}, {self.dt}, {self.type}, {self.pnl}, {self.enter_id}, {self.enter_date})"
    
    def __str__(self) -> str:
        return f"<Exit({self.ticker} {self.qty} @ {self.dt}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'cash_flow': self.cash_flow,
            'ticker': self.ticker,
            'qty': self.qty,
            'dt': self.dt,
            'type': self.type,
            'pnl': self.pnl,
            'enter_id': self.enter_id,
            'enter_date': self.enter_date
        }
    