import pandas as pd
from typing import List
from .LimitOrder import LimitOrder
from .OrderBook import OrderBook

class CryptoOrderBook(OrderBook):
    """An OrderBook contains all the relevant trading data of a given asset. It contains the list of bids and asks, ordered by their place in the queue.
    """
    def __init__(self, base:str, quote:str):
        """_summary_

        Args:
            ticker (str): the corresponding asset that is going to be traded in the OrderBook.
        """
        self.base = base
        self.quote = quote
        self.bids: List[LimitOrder] = []
        self.asks: List[LimitOrder] = []

    def __repr__(self) -> str:
        return f'<CryptoOrderBook: {self.base}/{self.quote}>'

    def __str__(self) -> str:
        return f'<CryptoOrderBook: {self.base}/{self.quote}>'
    
    def to_dict(self, limit=20) -> dict:
        return {
            "base": self.base,
            "quote": self.quote,
            "bids": [b.to_dict() for b in self.bids][:limit], 
            "asks": [a.to_dict() for a in self.asks][:limit]
        }
