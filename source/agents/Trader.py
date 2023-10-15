import pandas as pd
from typing import List, Union
from .Agent import Agent
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils.logger import Logger, Null_Logger


class Trader(Agent):
    def __init__(self, name:str, aum:int=10_000, requests=None):
        super().__init__(name, aum, requester=None)
        self.exchange_requests = requests
        self.assets = {}
        self.tickers = []
        self.aum = aum
        self.logger = Null_Logger() #NOTE: updates to Logger if added during registration

    def __repr__(self):
        return f'<Trader: {self.name}>'

    def __str__(self):
        return f'<Trader: {self.name}>'

    async def get_tickers(self) -> list:
        """returns a list of all tickers in the market

        returns:
            list: a list of all tickers in the market
        """
        return await self.exchange_requests.get_tickers()

    async def get_latest_trade(self, ticker:str) -> dict:
        """returns the most recent trade of a given asset

        Args:
            ticker (str): the ticker of the corresponding asset

        returns:
            Trade: the most recent trade
        """
        return await self.exchange_requests.get_latest_trade(ticker)

    async def get_best_bid(self, ticker:str) -> dict:
        """returns the current best limit buy order

        Args:
            ticker (str): the ticker of the asset

        returns:
            LimitOrder: the current best limit buy order
        """
        return await self.exchange_requests.get_best_bid(ticker)

    async def get_best_ask(self, ticker:str) -> dict:
        """returns the current best limit sell order

        Args:
            ticker (str): the ticker of the asset

        returns:
            LimitOrder: the current best limit sell order
        """
        return await self.exchange_requests.get_best_ask(ticker)
        
    async def get_midprice(self, ticker:str) -> float:
        """returns the current midprice of the best bid and ask orders in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset

        returns:
            float: the current midprice
        """
        return await self.exchange_requests.get_midprice(ticker)

    async def get_order_book(self,ticker) -> dict:
        return await self.exchange_requests.get_order_book(ticker)

    async def get_quotes(self,ticker) -> dict:
        return await self.exchange_requests.get_quotes(ticker)

    async def get_trades(self, ticker, limit=20) -> List[dict]:
        return await self.exchange_requests.get_trades(ticker, limit=limit)

    async def market_buy(self, ticker:str, qty:int, fee=0.0) -> Union[dict,None]:
        """Places a market buy order. The order executes automatically at the best sell price if ask quotes are available.

        Args:
            ticker (str): the ticker of the asset.
            qty (int): the quantity of the asset to be acquired (in units)

        """
        order = await self.exchange_requests.market_buy(ticker, qty, self.name, fee)
        return order

    async def market_sell(self, ticker:str, qty:int, fee=0.0) -> Union[dict,None]:
        """Places a market sell order. The order executes automatically at the best buy price if bid quotes are available.

        Args:
            ticker (str): the ticker of the asset.
            qty (int): the quantity of the asset to be sold (in units)

        """
        order = await self.exchange_requests.market_sell(ticker, qty, self.name, fee)
        return order

    async def limit_buy(self, ticker:str, price:float, qty:int, fee=0.0) -> Union[dict,None]:
        """Creates a limit buy order for a given asset and quantity at a certain price.

        Args:
            ticker (str): the ticker of the asset
            price (float): the limit price
            qty (int): the quantity to be acquired

        returns:
            LimitOrder
        """
        order = await self.exchange_requests.limit_buy(ticker,price,qty,self.name, fee)
        return order

    async def limit_sell(self, ticker:str, price:float, qty:int, fee=0.0) -> Union[dict,None]:
        """Creates a limit sell order for a given asset and quantity at a certain price.

        Args:
            ticker (str): the ticker of the asset
            price (float): the limit price
            qty (int): the quantity to be sold

        returns:
            LimitOrder
        """
        order = await self.exchange_requests.limit_sell(ticker,price,qty,self.name, fee)
        return order

    async def get_position(self,ticker) -> dict:
        agent = (await self.exchange_requests.get_agent(self.name))
        _transactions = agent['_transactions']
        return sum(t['qty'] for t in _transactions if t['ticker'] == ticker)

    async def cancel_order(self, ticker:str, id:str) -> Union[dict,None]:
        """Cancels the order with a given id (if it exists)

        Args:
            id (str): the id of the limit order

        returns:
            Union[LimitOrder,None]: the cancelled order if it is still pending. None if it does not exists or has already been filled/cancelled
        """
        return await self.exchange_requests.cancel_order(ticker, id)

    async def cancel_all_orders(self, ticker:str) -> dict:
        """Cancels all remaining orders that the agent has on an asset.

        Args:
            ticker (str): the ticker of the asset.
        """
        return await self.exchange_requests.cancel_all_orders(ticker, self.name)

    async def get_price_bars(self,ticker, bar_size='1D', limit=20) -> pd.DataFrame:
        return await self.exchange_requests.get_price_bars(ticker, bar_size, limit=limit)
    
    async def get_cash(self) -> float:
        """
        returns: {cash: float}
        """
        return await self.exchange_requests.get_cash(self.name)
    
    async def get_assets(self) -> dict:
        """
        returns: {assets: {ticker, amount}}"""
        return await self.exchange_requests.get_assets(self.name)
    
    async def register(self, logger=False) -> dict:
        agent = await self.exchange_requests.register_agent(self.name, self.initial_cash)
        if 'registered_agent' in agent:
            self.name = agent['registered_agent']
            if logger:
                self.logger = Logger(agent['registered_agent'])
            return agent
        else:
            return None

    async def send_cash(self, amount, recipient) -> dict:
        await self.exchange_requests.remove_cash(self.name, amount)
        return await self.exchange_requests.add_cash(recipient, amount)

    async def has_cash_and_assets(self) -> bool:
        self.cash = (await self.get_cash())['cash']
        self.assets = (await self.get_assets())['assets']
        if self.cash <= 0 and all(asset == 0 for asset in self.assets.values()) == True:
            print(self.name, "has no cash and no assets. Terminating.", self.cash, self.assets)
            return False
        else: return True

    async def next(self) -> None:  
        pass
