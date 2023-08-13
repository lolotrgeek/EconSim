from .Agent import Agent
import random
from time import sleep

class RandomMarketTaker(Agent):
    def __init__(self,name,tickers, aum=10000,prob_buy=.2,prob_sell=.2,qty_per_order=1,seed=None, requester=None):
        Agent.__init__(self, name, aum, requester=requester)
        if  prob_buy + prob_sell> 1:
            raise ValueError("Sum of probabilities cannot be greater than 1.") 
        self.prob_buy = prob_buy
        self.prob_sell = prob_sell
        self.qty_per_order = qty_per_order
        self.assets = {}
        self.tickers = tickers
        self.aum = aum

        # Allows for setting a different independent seed to each instance
        self.random = random
        if seed is not None:
            self.random.seed = seed

    async def next(self) -> bool:
        self.cash = (await self.get_cash())['cash']
        self.assets = (await self.get_assets())['assets']

        if self.cash <= 0 and all(asset == 0 for asset in self.assets.values()) == True:
            print(self.name, "has no cash and no assets. Terminating.", self.cash, self.assets)
            return False

        ticker = random.choice(self.tickers)
        action = None

        if self.cash > 0 and ticker in self.assets and self.assets[ticker] > 0:
            action = random.choices(['buy','close',None], weights=[self.prob_buy, self.prob_sell, 1 - self.prob_buy - self.prob_sell])[0]
        elif self.cash > 0:
            action = 'buy'
        elif ticker in self.assets and self.assets[ticker] > 0:
            action = 'close'
        
        if action == 'buy':
            order = await self.market_buy(ticker,self.qty_per_order)

        elif action == 'close':
            order = await self.market_sell(ticker,(await self.get_position(ticker)))

        # if order is not None:
        #     print(order)
                    
        return True

class LowBidder(Agent):
    def __init__(self, name, tickers, aum, qty_per_order=1, requester=None):
        Agent.__init__(self, name, aum, requester=requester)
        self.qty_per_order = qty_per_order
        self.tickers = tickers
        self.assets = {}
        self.aum = aum

    async def next(self) -> bool:
        self.cash = (await self.get_cash())['cash']
        self.assets = (await self.get_assets())['assets']
        if self.cash <= 0 and all(asset == 0 for asset in self.assets.values()) == True:
            print(self.name, "has no cash and no assets. Terminating.", self.cash, self.assets)
            return False
                
        for ticker in self.tickers:
            latest_trade = await self.get_latest_trade(ticker)
            if latest_trade is None or 'price' not in latest_trade:
                break
            price = latest_trade['price']
            
            if self.cash < price:
                await self.cancel_all_orders(ticker)
                await self.limit_sell(ticker, price-len(self.assets) , qty=self.qty_per_order)
            else:
                await self.limit_buy(ticker, price+len(self.assets), qty=self.qty_per_order)
        return True

class GreedyScalper(Agent):
    '''waits for initial supply to dry up, then starts inserting bids very low and asks very high'''
    def __init__(self, name, tickers, aum, qty_per_order=1, requester=None):
        Agent.__init__(self, name, aum, requester=requester)
        self.qty_per_order = qty_per_order
        self.tickers = tickers
        self.aum = aum

    async def next(self) -> bool:
        get_supply = await self.get_assets('init_seed')

        for ticker in self.tickers:
            if ticker in get_supply and get_supply[ticker] == 0:
                latest_trade = await self.get_latest_trade(ticker)
                if latest_trade is None or 'price' not in latest_trade:
                    break
                price = latest_trade['price'] / 2
                await self.cancel_all_orders(ticker)
                await self.limit_buy(ticker, price, qty=self.qty_per_order)
                await self.limit_sell(ticker, price * 2, qty=self.qty_per_order)
        return True

class NaiveMarketMaker(Agent):
    def __init__(self, name, tickers, aum, spread_pct=.005, qty_per_order=1, requester=None):
        Agent.__init__(self, name, aum, requester=requester)
        self.qty_per_order = qty_per_order
        self.tickers = tickers
        self.spread_pct = spread_pct
        self.aum = aum
        self.assets = None
        self.can_buy = True
        self.can_sell = {ticker: False for ticker in self.tickers}

    async def next(self) -> bool:
        self.cash = (await self.get_cash())['cash']
        self.assets = (await self.get_assets())['assets']
        if self.cash <= 0:
            print(self.name, "is out of cash:", self.cash)
            return False

        for ticker in self.tickers:
            latest_trade = await self.get_latest_trade(ticker)
            if latest_trade is None or 'price' not in latest_trade:
                break
            price = latest_trade['price']
            await self.cancel_all_orders(ticker)
            buy_order = await self.limit_buy(ticker, price * (1-self.spread_pct/2), qty=self.qty_per_order)
            sell_order = await self.limit_sell(ticker, price * (1+self.spread_pct/2), qty=self.qty_per_order)
        return True
