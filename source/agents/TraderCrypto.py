import pandas as pd
from typing import List, Union
from .Trader import Trader
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)


class CryptoTrader(Trader):
    def __init__(self, name:str, aum:int=10_000, exchange_requests=None, crypto_requests=None):
        super().__init__(name, aum, requests=exchange_requests)
        self.exchange_requests = exchange_requests
        self.crypto_requests = crypto_requests
        self.assets = {}
        self.tickers = []
        self.aum = aum

    def __repr__(self):
        return f'<CryptoTrader: {self.name}>'

    def __str__(self):
        return f'<CryptoTrader: {self.name}>'

    async def get_latest_trade(self, base:str, quote:str) -> dict:
        """returns the most recent trade of a given asset

        Args:
            ticker (str): the ticker of the corresponding asset

        returns:
            Trade: the most recent trade
        """
        return await self.exchange_requests.get_latest_trade(base, quote)

    async def get_trades(self, base:str, quote:str, limit=20) -> List[dict]:
        return await self.exchange_requests.get_trades(base, quote, limit=limit)

    async def market_buy(self, base:str, quote:str, qty:int, fee=0.0) -> Union[dict,None]:
        """Places a market buy order. The order executes automatically at the best sell price if ask quotes are available.

        Args:
            ticker (str): the ticker of the asset.
            qty (int): the quantity of the asset to be acquired (in units)

        """
        order = await self.exchange_requests.market_buy(base, quote, qty, self.name, fee)
        return order

    async def market_sell(self, base:str, quote:str, qty:int, fee=0.0) -> Union[dict,None]:
        """Places a market sell order. The order executes automatically at the best buy price if bid quotes are available.

        Args:
            ticker (str): the ticker of the asset.
            qty (int): the quantity of the asset to be sold (in units)

        """
        order = await self.exchange_requests.market_sell(base, quote, qty, self.name, fee)
        return order

    async def limit_buy(self, base:str, quote:str, price:float, qty:int, fee=0.0) -> Union[dict,None]:
        """Creates a limit buy order for a given asset and quantity at a certain price.

        Args:
            ticker (str): the ticker of the asset
            price (float): the limit price
            qty (int): the quantity to be acquired

        returns:
            LimitOrder
        """
        order = await self.exchange_requests.limit_buy(base, quote,price,qty,self.name, fee)
        return order

    async def limit_sell(self, base:str, quote:str, price:float, qty:int, fee=0.0) -> Union[dict,None]:
        """Creates a limit sell order for a given asset and quantity at a certain price.

        Args:
            ticker (str): the ticker of the asset
            price (float): the limit price
            qty (int): the quantity to be sold

        returns:
            LimitOrder
        """
        order = await self.exchange_requests.limit_sell(base, quote,price,qty,self.name, fee)
        return order

    async def get_position(self, asset):
        agent = (await self.exchange_requests.get_agent(self.name))
        for position in agent['positions']:
            if position['asset'] == asset:
                return position

    async def get_simple_position(self,asset) -> dict:
        agent = (await self.exchange_requests.get_agent(self.name))
        _transactions = agent['_transactions']
        return sum(t['qty'] for t in _transactions if t['asset'] == asset)

    async def cancel_order(self, base:str, quote:str, id:str) -> Union[dict,None]:
        """Cancels the order with a given id (if it exists)

        Args:
            id (str): the id of the limit order

        returns:
            Union[LimitOrder,None]: the cancelled order if it is still pending. None if it does not exists or has already been filled/cancelled
        """
        return await self.exchange_requests.cancel_order(base, quote, id)

    async def cancel_all_orders(self, base:str, quote:str,) -> dict:
        """Cancels all remaining orders that the agent has on an asset.

        Args:
            ticker (str): the ticker of the asset.
        """
        return await self.exchange_requests.cancel_all_orders(base, quote, self.name)

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
    
    async def register(self) -> dict:
        agent = await self.exchange_requests.register_agent(self.name, {"USD": self.initial_cash})
        if 'registered_agent' in agent:
            self.name = agent['registered_agent']
            return agent
        else:
            return 'UnRegistered Agent'

    async def get_mempool(self, asset) -> dict:
        return await self.crypto_requests.get_mempool(asset)
    
    async def get_transactions(self,asset) -> dict:
        return await self.crypto_requests.get_transactions(asset)
    
    async def get_transaction(self,asset, id) -> dict:
        return await self.crypto_requests.get_transaction(asset,id)
    