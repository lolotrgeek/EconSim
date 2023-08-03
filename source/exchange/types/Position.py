
class Position():
    def __init__(self, id, ticker, qty, dt, enters=[], exits=[]):
        self.id = str(id)
        self.ticker = ticker
        self.qty = qty
        self.dt = dt
        self.enters = enters # enters is a list of transactions
        self.exits = exits # exits is a list of transactions

    def __repr__(self) -> str:
        return f"Position({self.id}, {self.ticker}, {self.qty}, {self.dt}, {self.transactions})"
    
    def __str__(self) -> str:
        return f"<Position({self.ticker} {self.qty} @ {self.dt}>"
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'ticker': self.ticker,
            'qty': self.qty,
            'dt': self.dt,
            'enters': self.enters,
            'exits': self.exits
        }