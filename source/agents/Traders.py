from .Trader import Trader
import random

class Fundamental(Trader):
    def __init__(self, name, aum, qty_per_order=1, requests=()):
        Trader.__init__(self, name, aum, requests=requests)
        self.qty_per_order = qty_per_order

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if (await self.has_cash_and_assets()) == False: return False

        for ticker in self.tickers:
            await self.get_income_statement(ticker)
            await self.get_balance_sheet(ticker)
            await self.get_cash_flow(ticker)
            await self.get_dividend_payment_date(ticker)
            await self.get_ex_dividend_date(ticker)
            await self.get_dividends_to_distribute(ticker)
        return True

class RandomMarketTaker(Trader):
    def __init__(self,name , aum=10000,prob_buy=.2,prob_sell=.2,qty_per_order=1,seed=None, requests=()):
        Trader.__init__(self, name, aum, requests=requests)
        if  prob_buy + prob_sell> 1:
            raise ValueError("Sum of probabilities cannot be greater than 1.") 
        self.prob_buy = prob_buy
        self.prob_sell = prob_sell
        self.qty_per_order = qty_per_order

        # Allows for setting a different independent seed to each instance
        self.random = random
        if seed is not None:
            self.random.seed = seed

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if (await self.has_cash_and_assets()) == False: return False

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

class LowBidder(Trader):
    def __init__(self, name, aum, qty_per_order=1, requests=()):
        Trader.__init__(self, name, aum, requests=requests)
        self.qty_per_order = qty_per_order

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if (await self.has_cash_and_assets()) == False: return False
                
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

class GreedyScalper(Trader):
    '''waits for initial supply to dry up, then starts inserting bids very low and asks very high'''
    def __init__(self, name, aum, qty_per_order=1, requests=()):
        Trader.__init__(self, name, aum, requests=requests)
        self.qty_per_order = qty_per_order
        self.aum = aum

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if (await self.has_cash_and_assets()) == False: return False

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

class NaiveMarketMaker(Trader):
    def __init__(self, name, aum, spread_pct=.005, qty_per_order=1, requests=()):
        Trader.__init__(self, name, aum, requests=requests)
        self.qty_per_order = qty_per_order
        self.spread_pct = spread_pct
        self.aum = aum
        self.assets = None
        self.can_buy = True
        self.can_sell = {ticker: False for ticker in self.tickers}

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if (await self.has_cash_and_assets()) == False: return False

        for ticker in self.tickers:
            latest_trade = await self.get_latest_trade(ticker)
            if latest_trade is None or 'price' not in latest_trade:
                break
            price = latest_trade['price']
            await self.cancel_all_orders(ticker)
            buy_order = await self.limit_buy(ticker, price * (1-self.spread_pct/2), qty=self.qty_per_order)
            sell_order = await self.limit_sell(ticker, price * (1+self.spread_pct/2), qty=self.qty_per_order)
        return True
