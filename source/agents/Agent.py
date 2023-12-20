from uuid import uuid4 as UUID

class Agent():
    """
    Agent class is the base class for developing different actors that participate in the simulated economy.
    """
    def __init__(self, name:str, aum:int=10_000, requests=None):
        self.id = UUID()
        self.name = name 
        self.tickers = []
        self.requests = requests
        self.cash = aum
        self.initial_cash = aum

    def __repr__(self):
        return f'<Agent: {self.name}>'

    def __str__(self):
        return f'<Agent: {self.name}>'

    async def next(self) -> None:  
        pass
