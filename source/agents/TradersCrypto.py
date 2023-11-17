from .TraderCrypto import CryptoTrader as Trader
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.utils._utils import prec
from source.utils.logger import Logger
from decimal import Decimal

class RandomMarketTaker(Trader):
    def __init__(self,name , aum=10000,prob_buy=.2,prob_sell=.2,seed=None, requests=()):
        Trader.__init__(self, name, aum, exchange_requests=requests[0], crypto_requests=requests[1])
        if  prob_buy + prob_sell > 1:
            raise ValueError("Sum of probabilities cannot be greater than 1.") 
        self.prob_buy = prob_buy
        self.prob_sell = prob_sell
        self.qty_per_order = prec(str(random.uniform(0.00000000001, 1.9)))

        # Allows for setting a different independent seed to each instance
        self.random = random
        if seed is not None:
            self.random.seed = seed

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if len(self.tickers) == 0: return True
        if (await self.has_assets()) == False: return False

        ticker = random.choice(self.tickers)
        action = None

        if self.cash > 0 and ticker['base'] in self.assets and self.assets[ticker['base']] > 0:
            action = random.choices(['open','close',None], weights=[self.prob_buy, self.prob_sell, 1 - self.prob_buy - self.prob_sell])[0]
        elif self.cash > 0:
            action = 'open'
        elif ticker['base'] in self.assets and self.assets[ticker['base']] > 0:
            action = 'close'
        
        if action == 'open':
            order = await self.market_buy(ticker['base'], ticker['quote'], self.qty_per_order, '0.01')
            if order is None or order['market_buy'] == "insufficient funds":
                return False

        elif action == 'close':
            qty = (await self.get_assets())['assets'][ticker['base']]
            order = await self.market_sell(ticker['base'],ticker['quote'], qty, '0.01')
            self.logger.info(f"Random Market Taker {self.name} sold {qty} {ticker['base']} with {order['market_sell']}")
            if order is None or order['market_sell'] == "insufficient assets":
                return False
        return True
    
class SimpleMarketTaker(Trader):
    def __init__(self,name , aum=10000, requests=()):
        Trader.__init__(self, name, aum, exchange_requests=requests[0], crypto_requests=requests[1])
        self.asset_to_trade = prec('0.8')
        self.last_trade_time = None
        self.current_time = None
        self.logger = Logger('SimpleMarketTaker', mode='w')

    async def spend_cash(self):
        ticker = random.choice(self.tickers)
        self.logger.info(f"{self.name} spending {self.assets['USD']} on {ticker['base']}")
        latest_trade = await self.get_latest_trade(ticker['base'], ticker['quote'])
        self.logger.info(f"{self.name} latest trade: {latest_trade}")
        if latest_trade is None or 'price' not in latest_trade or latest_trade['price'] <= 0:
            return False
        cash_to_trade = prec(self.asset_to_trade * self.assets['USD'], self.assets['USD']['decimals'])
        fee = prec('0.01', self.assets['USD']['decimals'])
        qty = prec(str((cash_to_trade) / latest_trade['price']), self.assets[ticker['base']]['decimals'])
        if prec(cash_to_trade + fee, self.assets['USD']['decimals']) > self.assets['USD']:
            self.logger.info(f"{self.name} not enough cash to buy {qty} {ticker['base']} at {latest_trade['price']}")
            return False
        self.logger.info(f"{self.name} buying {qty} {ticker['base']} at {latest_trade['price']}")
        order = await self.market_buy(ticker['base'], 'USD', qty, fee )
        if order['market_buy'] == "max_pending_transactions_reached":
            self.logger.info(order)
            return False
        if order['market_buy'] == "insufficient assets":
            self.logger.info(order)
            return False
        if order['market_buy'] == "no fills":
            self.logger.info(order)
            return False        
        else:
            self.last_trade_time = self.current_time
            self.logger.info(f"{self.name} bought {qty} {ticker['base']} at {latest_trade['price']}")

    async def dump_assets(self):
        for asset in self.assets:
            qty = prec(self.assets[asset] * self.asset_to_trade, self.assets[asset]['decimals'])
            self.logger.info(f"{self.name}, has {self.assets[asset]} {asset}, dumping {qty}")
            if asset != 'USD' and qty > 0:
                fee = prec('0.01', self.assets[asset]['decimals'])
                if prec(qty + fee, self.assets[asset]['decimals']) > self.assets[asset]:
                    self.logger.info(f"{self.name} not enough {asset} to sell {qty}")
                    return False
                self.logger.info(f"{self.name} selling {qty} {asset}")
                order = await self.market_sell(asset, 'USD', qty, fee)
                if order['market_sell'] == "max_pending_transactions_reached":
                    self.logger.info(order)
                    return False
                if order['market_sell'] == "insufficient assets":
                    self.logger.info(order)
                    return False
                if order['market_sell'] == "no fills":
                    self.logger.info(order)
                    return False
                else:
                    self.last_trade_time = self.current_time
                    self.logger.info(f"{self.name} sold {order}")
                    break        

    async def next(self) -> bool:
        self.current_time = await self.get_sim_time()
        if self.last_trade_time == None: self.last_trade_time = self.current_time
        # if current_time.day > self.last_trade_time.day:
        #     return True
        self.tickers = await self.get_tickers()
        self.assets = (await self.get_assets())['assets']
        if 'USD' not in self.assets:
            return False
        self.cash = self.assets['USD']
        if len(self.tickers) == 0: return True
        if (await self.has_assets()) == False: return False

        
        await self.spend_cash()
        await self.dump_assets()
    
        return True    

class LowBidder(Trader):
    def __init__(self, name, aum, qty_per_order=1, requests=()):
        Trader.__init__(self, name, aum, exchange_requests=requests[0], crypto_requests=requests[1])
        self.qty_per_order = qty_per_order

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if len(self.tickers) == 0: return True
        if (await self.has_assets()) == False: return False
                
        for ticker in self.tickers:
            latest_trade = await self.get_latest_trade(ticker['base'], ticker['quote'])
            if latest_trade is None or 'price' not in latest_trade:
                break
            price = latest_trade['price']
            
            if self.cash < price:
                await self.cancel_all_orders(ticker['base'], ticker['quote'])
                await self.limit_sell(ticker['base'], ticker['quote'], prec(str(price-len(self.assets)), self.assets[ticker['quote']]['decimals']) , qty=self.qty_per_order, fee='0.01')
            else:
                await self.limit_buy(ticker['base'], ticker['quote'], prec(str(price+len(self.assets)), self.assets[ticker['quote']]['decimals']), qty=self.qty_per_order, fee='0.01')
        return True

class GreedyScalper(Trader):
    '''waits for initial supply to dry up, then starts inserting bids very low and asks very high'''
    def __init__(self, name, aum, qty_per_order=1, requests=()):
        Trader.__init__(self, name, aum, exchange_requests=requests[0], crypto_requests=requests[1])
        self.qty_per_order = qty_per_order
        self.aum = aum

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if len(self.tickers) == 0: return True
        if (await self.has_assets()) == False: return False

        get_supply = await self.get_assets('init_seed')

        for ticker in self.tickers:
            if ticker['base'] in get_supply and get_supply[ticker['base']] == 0:
                latest_trade = await self.get_latest_trade(ticker['base'], ticker['quote'])
                if latest_trade is None or 'price' not in latest_trade:
                    break
                price = latest_trade['price'] / 2
                await self.cancel_all_orders(ticker['base'], ticker['quote'])
                await self.limit_buy(ticker['base'], ticker['quote'], price, qty=self.qty_per_order, fee='0.01')
                await self.limit_sell(ticker['base'], ticker['quote'], price * 2, qty=self.qty_per_order, fee='0.01')
        return True

class NaiveMarketMaker(Trader):
    def __init__(self, name, aum, spread_pct='.005', qty_pct_per_order='.01', requests=()):
        Trader.__init__(self, name, aum, exchange_requests=requests[0], crypto_requests=requests[1])
        self.spread_pct = prec(spread_pct)
        self.sell_spread = prec(str(1+self.spread_pct/2))
        self.buy_spread = prec(str(1-self.spread_pct/2))
        self.qty_pct_per_order = prec(qty_pct_per_order, 2)
        self.fee_reserve = prec(str(aum * 0.02), 2) # the amount of cash to reserve for fees
        self.asset_reserve = prec(str(aum * 0.02), 2)
        self.cash_per_ticker = 0
        self.cash_to_trade = aum - self.fee_reserve
        self.aum = aum
        self.assets = None
        self.can_buy = True
        self.can_sell = {ticker: False for ticker in self.tickers}
        self.logger = Logger('NaiveMarketMaker', level=10)


    async def make_market(self, ticker, price):
        await self.cancel_all_orders(ticker['base'], ticker['quote'])
        buy_price = prec(price * self.buy_spread, self.assets[ticker['quote']]['decimals'])
        sell_price = prec(price * self.sell_spread, self.assets[ticker['quote']]['decimals'])
        fee = prec('0.01', self.assets[ticker['quote']]['decimals'])
        qty = prec(str(self.assets[ticker['base']] * self.qty_pct_per_order), self.assets[ticker['base']]['decimals'])
        if qty <= 0:
            self.logger.error(f'Naive Market Maker {self.name} {qty} below 0') 
            return False
        if prec(qty + fee, self.assets[ticker['base']]['decimals']) > self.assets[ticker['base']]:
            self.logger.warning(f' {self.name} not enough assets needs: {qty+fee} has {self.assets[ticker["base"]]}') 
            return False
        if prec(qty * buy_price + fee, self.assets[ticker['quote']]['decimals'])  > self.cash_to_trade:
            self.logger.warning(f' {self.name} not enough cash needs: {qty * buy_price + fee} has {self.cash_to_trade}') 
            return False
        buy_order = await self.limit_buy(ticker['base'], ticker['quote'], buy_price, qty=qty, fee=fee)
        self.logger.debug(f"Making Market {self.name} buy order: {buy_order}")
        sell_order = await self.limit_sell(ticker['base'], ticker['quote'], sell_price, qty=qty, fee=fee)
        self.logger.debug(f"Making Market {self.name} sell order: {sell_order}")

    async def acquire_assets(self, ticker):
        # Calculate the amount of crypto to buy for this ticker
        best_ask = await self.get_best_ask(ticker['base']+ticker['quote'])
        if best_ask is not None and 'price' in best_ask:
            price = prec(best_ask['price'], self.assets[ticker['quote']]['decimals'])
        if price <= 0:
            latest_trade = await self.get_latest_trade(ticker['base'], ticker['quote'])
            if latest_trade is not None and 'price' in latest_trade:
                price = prec(latest_trade['price'], self.assets[ticker['quote']]['decimals'])
            if price <= 0:
                return False
            
        qty = prec(str(self.cash_per_ticker / price), self.assets[ticker['base']]['decimals'])
        if qty <= 0:
            self.logger.error(f'Naive Market Maker {self.name} {qty} below 0') 
            return False
        initial_buy = await self.limit_buy(ticker['base'], ticker['quote'], price, qty=qty, fee='0.01')
        if initial_buy['status'] == "error":
            self.logger.error(f'Naive Market Maker {self.name} could not buy {qty} {ticker["base"]} at {price} {initial_buy["accounting"]}')
            return False
        elif initial_buy is None:
            self.logger.error(f'Naive Market Maker {self.name} could not buy {qty} {ticker["base"]} at {price}')
            return False
        # elif initial_buy['status'] == 'open':
        #     await self.cancel_all_orders(ticker['base'], ticker['quote'])
        #     self.logger.warning(f'Naive Market Maker {self.name} failed to get order filled and acquire initial assets.')
        #     return False
        else:
            self.logger.info(f"Naive Market Maker {self.name} placed order for {qty} {ticker['base']} at {price}") 
            return True

    async def set_tradable_cash(self):
        self.cash = await self.get_cash() 
        self.fee_reserve = prec(str(self.cash * Decimal('0.02')), self.assets['USD']['decimals']) 
        self.cash_to_trade = prec(str(self.cash - self.fee_reserve), self.assets['USD']['decimals'])
        self.cash_per_ticker = prec(str(self.cash_to_trade / (len(self.tickers)+1)), self.assets['USD']['decimals'])

    async def next(self) -> bool:
        self.tickers = await self.get_tickers()
        if len(self.tickers) == 0: return True
        if (await self.has_assets()) == False: return False

        await self.set_tradable_cash()

        for ticker in self.tickers:
            latest_trade = await self.get_latest_trade(ticker['base'], ticker['quote'])
            self.assets = (await self.get_assets())['assets']
            self.logger.debug(f"Naive Market Maker {self.name} assets: {self.assets}")
            # check if the ticker base is in the assets
            if ticker['base'] in self.assets:
                # Make a market for this ticker
                await self.make_market(ticker, latest_trade['price'])
            else:
                await self.acquire_assets(ticker)
        
        return True

