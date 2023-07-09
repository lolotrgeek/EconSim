import pandas as pd
from typing import List
from .LimitOrder import LimitOrder
from ..utils._utils import format_dataframe_rows_to_dict

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

    def __repr__(self):
        return f'<OrderBook: {self.ticker}>'

    def __str__(self):
        return f'<OrderBook: {self.ticker}>'
    


    @property
    def df(self) -> dict:
        """_summary_

        Returns:
            dict: dictionary with two dataframes corresponding to the bids and asks of the OrderBook
        """
        return {
            'bids': pd.DataFrame.from_records([b.to_dict() for b in self.bids]),
            'asks': pd.DataFrame.from_records([a.to_dict() for a in self.asks])
        }
    
    def to_dict(self) -> dict:
        return {
            "bids": [b.to_dict() for b in self.bids], 
            "asks": [a.to_dict() for a in self.asks]
        }
