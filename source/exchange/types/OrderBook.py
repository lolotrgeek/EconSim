import pandas as pd
from typing import List
from .LimitOrder import LimitOrder

class OrderBook():
    """An OrderBook contains all the relevant trading data of a given asset. It contains the list of bids and asks, ordered by their place in the queue.
    """
    def __init__(self, ticker:str):
        """_summary_

        Args:
            ticker (str): the corresponding asset that is going to be traded in the OrderBook.
        """
        self.ticker = ticker
        self.bids: List[LimitOrder] = []
        self.asks: List[LimitOrder] = []

    def __repr__(self) -> str:
        return f'<OrderBook: {self.ticker}>'

    def __str__(self) -> str:
        return f'<OrderBook: {self.ticker}>'
    
    def to_dict(self, limit=20) -> dict:
        return {
            "ticker": self.ticker,
            "bids": [b.to_dict() for b in self.bids][:limit], 
            "asks": [a.to_dict() for a in self.asks][:limit]
        }
