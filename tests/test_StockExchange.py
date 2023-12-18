import asyncio
import unittest
from datetime import datetime
import sys
import os
import random
from decimal import Decimal
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.exchange.StockExchange import StockExchange as Exchange
from source.exchange.types.LimitOrder import LimitOrder
from source.exchange.types.OrderSide import OrderSide
from source.utils.logger import Null_Logger

class CreateAssetTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()


    async def test_create_asset(self):
        asset = await self.exchange.create_asset("AAPL", 'stock', seed_price=50000)
        book = self.exchange.books["AAPL"]
        self.assertEqual(asset['type'], "stock")
        self.assertEqual(book.bids[0].price, 49500)
        self.assertEqual(book.asks[0].price, 50500)

    async def test_create_duplicate_asset(self):
        await self.exchange.create_asset("AAPL", 'stock', seed_price=50000)
        asset = await self.exchange.create_asset("AAPL", 'stock', seed_price=50000)
        self.assertEqual(asset, {"error": "asset AAPL already exists"})
    
    async def test_create_max_asset(self):
        self.exchange.max_assets = 1
        await self.exchange.create_asset("AAPL", 'stock', seed_price=50000)
        asset = await self.exchange.create_asset("MSFT", 'stock', seed_price=50000)
        self.assertEqual(asset, {"error": "max assets reached"})    

class GetOrderBookTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_order_book(self):
        order_book = await self.exchange.get_order_book("AAPL")
        self.assertEqual(order_book.ticker, "AAPL")
        self.assertEqual(len(order_book.bids), 1)
        self.assertEqual(len(order_book.asks), 1)    

class GetLatestTradeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_latest_trade(self):
        latest_trade = await self.exchange.get_latest_trade("AAPL")
        print(latest_trade)
        self.assertEqual(latest_trade["ticker"], "AAPL")
        self.assertEqual(latest_trade["price"], 150)
        self.assertEqual(latest_trade["buyer"], "init_seed_AAPL")
        self.assertEqual(latest_trade["seller"], "init_seed_AAPL")

    async def test_get_latest_trade_error(self):
        self.exchange.trade_log.clear()
        latest_trade = await self.exchange.get_latest_trade("AAPL")
        self.assertEqual(latest_trade, {"error": "no trades found"})

class GetQuotesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_quotes(self):
        quotes = await self.exchange.get_quotes("AAPL")
        self.assertEqual(quotes["ticker"], "AAPL")
        self.assertEqual(quotes["bid_qty"], 1)
        self.assertEqual(quotes["bid_p"], 148.5)
        self.assertEqual(quotes["ask_qty"], 1000)
        self.assertEqual(quotes["ask_p"], 151.5)

class GetMidpriceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_midprice(self):
        midprice = await self.exchange.get_midprice("AAPL")
        self.assertEqual(midprice, 150)

class GetTradesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        trader1 = await self.exchange.register_agent("trader1", initial_assets={'USD': 10000})
        trader2 = await self.exchange.register_agent("trader2", initial_assets={'USD': 10000})
        self.trader1 = trader1['registered_agent']
        self.trader2 = trader2['registered_agent']
        await self.exchange.limit_buy("AAPL", price=152, qty=2, creator=self.trader1)
        await self.exchange.limit_sell("AAPL", price=152, qty=2, creator=self.trader2) # this one is meant to be ignored
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.trader2)

    async def test_get_trades(self):
        trades = await self.exchange.get_trades("AAPL", limit=10)
        self.assertEqual(len(trades), 3)
        for trade in trades:
            self.assertEqual(trade["ticker"], "AAPL")
            if trade['buyer'] == 'init_seed_AAPL':
                self.assertEqual(trade["price"], 150)
            else:
                self.assertNotEqual(trade["buyer"], trade["seller"])
        
class GetPriceBarsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agent", initial_assets={'USD': 10000}))['registered_agent']

    async def test_get_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10)
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0)})

    async def test_get_minute_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10, bar_size="1T")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})     

    async def test_get_5minute_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10, bar_size="5T")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_week_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10, bar_size="1W")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )}) 

    async def test_get_month_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10, bar_size="1M")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_year_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10, bar_size="1Y")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_price_bars_over_time(self):
        day = 1
        while day < 10:
            self.exchange.datetime = datetime(2023, 1, day)
            await self.exchange.limit_buy("AAPL", price=random.randint(100,180), qty=random.randint(1,10), creator=self.agent)
            await self.exchange.limit_sell("AAPL", price=random.randint(100,180), qty=random.randint(1,10), creator=self.agent)
            day+=1

        get_price_bars = await self.exchange.get_price_bars("AAPL", limit=10)
        print(self.exchange.trade_log)
        print(len(get_price_bars), get_price_bars)
        
class GetBestAskTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_best_ask(self):
        best_ask = await self.exchange.get_best_ask("AAPL")
        self.assertIsInstance(best_ask, LimitOrder)
        self.assertEqual(best_ask.type, OrderSide.SELL)

class GetBestBidTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_best_bid(self):
        best_bid = await self.exchange.get_best_bid("AAPL")
        self.assertIsInstance(best_bid, LimitOrder)
        self.assertEqual(best_bid.type, OrderSide.BUY)

    async def test_get_best_bid_error(self):
        self.exchange.books["AAPL"].bids.clear()
        best_bid = await self.exchange.get_best_bid("AAPL")
        self.assertEqual(best_bid.ticker, "AAPL")
        self.assertEqual(best_bid.price, 0)
        self.assertEqual(best_bid.qty, 0)
        self.assertEqual(best_bid.creator, "null_quote")

class CancelOrderTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("buyer1", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_cancel_order(self):
        order = await self.exchange.limit_buy("AAPL", price=149, qty=2, creator=self.agent)
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 2)
        cancel = await self.exchange.cancel_order("AAPL", order.id)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(cancel, {"cancelled_order": order.to_dict_full()})
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(await self.exchange.get_order("AAPL", order.id), {'error': 'order not found'})
        self.assertEqual(agent['frozen_assets'], {'USD': 0})       

    async def test_cancel_order_error(self):
        cancel = await self.exchange.cancel_order('AAPL',"error")
        self.assertEqual(cancel, {"cancelled_order": "order not found"})

class CancelAllOrdersTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent1 = await self.exchange.register_agent("buyer1", initial_assets={'USD': 10000})
        agent2 = await self.exchange.register_agent("buyer2", initial_assets={'USD': 10000})
        self.agent1 = agent1['registered_agent']
        self.agent2 = agent2['registered_agent']

    async def test_cancel_all_orders(self):
        await self.exchange.limit_buy("AAPL", price=150, qty=10, creator=self.agent1, tif="TEST")
        await self.exchange.limit_buy("AAPL", price=152, qty=10, creator=self.agent1, tif="TEST")
        await self.exchange.limit_buy("AAPL", price=153, qty=10, creator=self.agent2, tif="TEST")        
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 4)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

        canceled = await self.exchange.cancel_all_orders("AAPL", self.agent1)
        agent = await self.exchange.get_agent(self.agent1)

        self.assertEqual(len(self.exchange.books["AAPL"].bids), 2)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)
        self.assertEqual(len(canceled['cancelled_orders']), 2)
        self.assertEqual(agent['frozen_assets'], {'USD': 0})        

class LimitBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        insufficient_agent = await self.exchange.register_agent("insufficient_buyer", initial_assets={'USD': 1})
        self.insufficient_agent = insufficient_agent['registered_agent']
        buyer = await self.exchange.register_agent("buyer1", initial_assets={'USD': 10000})
        self.buyer = buyer['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_limit_buy_max_bids(self):
        self.exchange.max_bids = 1
        maxed_order = await self.exchange.limit_buy("AAPL", price=152, qty=2, creator=self.buyer)
        print(type(maxed_order.status))
        self.assertEqual(maxed_order.status, 'error')
        self.assertEqual(maxed_order.accounting, 'max_bid_depth_reached')

    async def test_limit_buy_sufficient_funds(self):
        new_order = await self.exchange.limit_buy('AAPL', 148, 3, self.buyer)

        self.assertEqual(len(self.exchange.books['AAPL'].bids), 2)
        self.assertEqual(self.exchange.books['AAPL'].bids[1].price, 148)
        self.assertEqual(self.exchange.books['AAPL'].bids[1].qty, 3)
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 148)
        self.assertEqual(new_order.qty, 3)
        self.assertEqual(new_order.creator, self.buyer)
        self.assertEqual(new_order.type, OrderSide.BUY)

    async def test_limit_buy_insufficient_funds(self):
        # self.exchange.agent_has_cash = MagicMock(return_value=False)

        result = await self.exchange.limit_buy('AAPL', 220, 3, self.insufficient_agent)
        self.assertEqual(result.creator, self.insufficient_agent)
        self.assertEqual(result.accounting, 'insufficient_funds')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['AAPL'].bids), 1)

    async def test_limit_buy_match_trades(self):
        new_order = await self.exchange.limit_buy('AAPL', 152, 4, self.buyer)
        print(new_order.to_dict_full())
        agent = await self.exchange.get_agent(self.buyer)
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 152)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.buyer)
        self.assertEqual(new_order.type, OrderSide.BUY)
        self.assertEqual(new_order.fills, [{'qty': 4, 'price': Decimal(151.5), 'fee': Decimal('1.2120'), 'creator': 'init_seed_AAPL'}])
        self.assertEqual(agent['assets'], {'AAPL': Decimal('4'), 'USD': Decimal('9392.7880')})
        self.assertEqual(agent['frozen_assets'], {'USD': 0})

class LimitSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.insufficient_seller = (await self.exchange.register_agent("insufficient_seller", initial_assets={'USD': 10000}))['registered_agent']
        self.agent = (await self.exchange.register_agent("seller1", initial_assets={'USD': 10000}))['registered_agent']
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={'USD': 10000}))['registered_agent']

    async def test_limit_sell_max_bids(self):
        self.exchange.max_asks = 1
        await self.exchange.limit_buy("AAPL", price=152, qty=4, creator=self.agent)
        maxed_order = await self.exchange.limit_sell('AAPL', 180, 4,self.agent )
        print(type(maxed_order.status))
        self.assertEqual(maxed_order.status, 'error')
        self.assertEqual(maxed_order.accounting, 'max_ask_depth_reached')

    async def test_limit_sell_sufficient_assets(self):
        await self.exchange.limit_buy("AAPL", price=152, qty=4, creator=self.agent)
        new_order = await self.exchange.limit_sell('AAPL', 180, 4,self.agent )

        self.assertEqual(len(self.exchange.books['AAPL'].asks), 2)
        self.assertEqual(self.exchange.books['AAPL'].asks[1].price, 180)
        self.assertEqual(self.exchange.books['AAPL'].asks[1].qty, 4)
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 180)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.agent)
        self.assertEqual(new_order.type, OrderSide.SELL)

    async def test_limit_sell_insufficient_assets(self):
        # self.exchange.agent_has_assets = MagicMock(return_value=False)

        result = await self.exchange.limit_sell('AAPL', 180, 4, self.insufficient_seller)
        self.assertEqual(result.creator, self.insufficient_seller)
        self.assertEqual(result.accounting, 'insufficient_assets')
        self.assertEqual(result.status, 'error')        
        self.assertEqual(len(self.exchange.books['AAPL'].asks), 1)

    async def test_limit_sell_match_trades(self):
        await self.exchange.limit_buy("AAPL", price=152, qty=4, creator=self.agent)
        new_order = await self.exchange.limit_sell('AAPL', 80, 4,self.agent )
        await self.exchange.limit_buy("AAPL", price=80, qty=4, creator=self.buyer)

        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 80)
        self.assertEqual(new_order.creator, self.agent)
        self.assertEqual(len(new_order.fills), 1)  
        self.assertEqual(new_order.type, OrderSide.SELL)
        self.assertEqual(agent['assets'], {'AAPL': Decimal('0'), 'USD': Decimal('9780.8880')})
        self.assertEqual(agent['frozen_assets'], {'AAPL': 0, 'USD': 0})

class LimitOrderMatchingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.insufficient_seller = (await self.exchange.register_agent("insufficient_seller", initial_assets={'USD': 10000}))['registered_agent']
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={"AAPL": 10000, "USD" : 10000}))['registered_agent']
        self.seller = (await self.exchange.register_agent("seller1", initial_assets={"AAPL": 10000, "USD" : 10000}))['registered_agent']
        self.match_buyer = (await self.exchange.register_agent("match_buyer", initial_assets={"AAPL": 10000, "USD" : 10000}))['registered_agent']

    async def test_limit_order_match_trades(self):
        await self.exchange.limit_sell("AAPL", price=145, qty=5, creator=self.seller)
        new_order = await self.exchange.limit_buy('AAPL', 145, 4, self.match_buyer)

        agent = await self.exchange.get_agent(self.match_buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        # check that assets are unfrozen 
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 145)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.match_buyer)
        self.assertEqual(agent['assets'], {"AAPL": Decimal('10004'), "USD": Decimal('9418.840')})
        self.assertEqual(agent_seller['assets'], {"AAPL": Decimal('9995'), "USD": Decimal('10727.630')})
        self.assertEqual(agent_seller['frozen_assets'], {'AAPL': Decimal('0'), 'USD': Decimal('0.000')})
        self.assertEqual(agent['frozen_assets'], {'USD': Decimal('0.000')})  

    async def test_limit_sell_partial_match(self):
        # half of the order gets filled, the other half becomes a maker order
        await self.exchange.limit_sell("AAPL", price=145, qty=10, creator=self.seller)
        new_order = await self.exchange.limit_buy('AAPL', 152, 5, self.buyer)
        print(new_order.to_dict_full())
        agent = await self.exchange.get_agent(self.buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 152)
        self.assertEqual(new_order.qty, 5)
        self.assertEqual(new_order.creator, self.buyer)
        self.assertEqual(new_order.type, OrderSide.BUY)
        self.assertEqual(agent['assets'], {"AAPL": Decimal('10005'), "USD": Decimal('9273.550')})
        self.assertEqual(agent_seller['assets'], {'AAPL': Decimal('9990'), 'USD': Decimal('10871.905')})
        self.assertEqual(agent_seller['frozen_assets'], {'AAPL': Decimal('4'), 'USD': Decimal('0.580')}) #NOTE 4 remains in the market order because 1 is sold to the init_seed bid
        self.assertEqual(agent['frozen_assets'], {'USD': Decimal('0.000')})  

    async def test_limit_buy_partial_match(self):
        # half of the order gets filled, the other half becomes a maker order
        await self.exchange.limit_buy("AAPL", price=130, qty=10, creator=self.buyer)
        new_order = await self.exchange.limit_sell('AAPL', 130, 5, self.seller)
        print(new_order.to_dict_full())
        agent = await self.exchange.get_agent(self.buyer)
        seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(new_order.ticker, 'AAPL')
        self.assertEqual(new_order.price, 130)
        self.assertEqual(new_order.qty, 5) 
        self.assertEqual(new_order.creator, self.seller)
        self.assertEqual(new_order.type, OrderSide.SELL)
        self.assertEqual(agent['assets'], {"AAPL": Decimal('10004'), "USD": Decimal('8698.700')}) #NOTE: going to be 10004 because 1 is sold to the init_seed bid
        self.assertEqual(seller['assets'], {'AAPL': Decimal('9995'), 'USD': Decimal('10667.200')})
        self.assertEqual(agent['frozen_assets'], {'USD': Decimal('780.780')})
        self.assertEqual(seller['frozen_assets'], {'AAPL': Decimal('0'), 'USD': Decimal('0.000')})  

class MarketBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.insufficient_buyer = (await self.exchange.register_agent("insufficient_buyer", initial_assets={'USD': 1}))['registered_agent']
        self.agent = (await self.exchange.register_agent("buyer1", initial_assets={'USD': 500000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_market_buy(self):
        result = await self.exchange.market_buy("AAPL", qty=4, buyer=self.agent)
        print(result)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(result, {'market_buy': 'AAPL', 'buyer': self.agent, 'qty': Decimal('4'), 'fills': [{'qty': Decimal('4'), 'price': Decimal('151.5'), 'fee': Decimal('1.2120')}]})
        self.assertEqual(agent['assets'], {"AAPL": 4, 'USD': Decimal('499392.7880')} )
        self.assertEqual(agent['frozen_assets'], {'USD': Decimal('0.000')})
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)
        self.assertEqual(self.exchange.books["AAPL"].asks[0].qty, 996)

    async def test_insufficient_funds(self):
        result = await self.exchange.market_buy("AAPL", qty=4, buyer=self.insufficient_buyer)
        agent = await self.exchange.get_agent(self.insufficient_buyer)
        self.assertEqual(result, {"market_buy": "insufficient assets", "buyer": self.insufficient_buyer})
        self.assertEqual(agent['assets'], {'USD': Decimal('1')})
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)

    async def test_no_fills(self):
        book = self.exchange.books["AAPL"]
        for bid in book.bids:
            await self.exchange.market_buy("AAPL", qty=bid.qty, buyer=self.agent)
        self.exchange.books["AAPL"].asks.clear()
        result = await self.exchange.market_buy("AAPL", qty=3, buyer=self.agent)
        self.assertEqual(result, {"market_buy": "no fills"})

class MarketSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        no_asset_seller = await self.exchange.register_agent("no_asset_seller", initial_assets={'USD': 10000})
        infufficient_seller = await self.exchange.register_agent("insufficient_seller", initial_assets={'USD': 10000})
        seller1 = await self.exchange.register_agent("seller1", initial_assets={'USD': 500000})
        buyer1 = await self.exchange.register_agent("buyer1", initial_assets={'USD': 500000})

        self.no_asset_seller = no_asset_seller['registered_agent']
        self.insufficient_seller = infufficient_seller['registered_agent']
        self.seller1 = seller1['registered_agent']
        self.buyer1 = buyer1['registered_agent']

    async def test_market_sell(self):
        await self.exchange.market_buy("AAPL", qty=4, buyer=self.seller1)
        await self.exchange.limit_buy("AAPL", price=150, qty=3, creator=self.buyer1)
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.seller1)
        agent = await self.exchange.get_agent(self.seller1)
        self.assertEqual(result, {'market_sell': 'AAPL', 'seller': self.seller1, 'qty': 3, 'fills': [{'qty': 3, 'price': 150, 'fee': Decimal('0.900')}]})
        self.assertEqual(agent['assets'], {'USD': Decimal('499841.8880'), 'AAPL': Decimal('1')})
        self.assertEqual(agent['frozen_assets'], {'AAPL': Decimal('0'), 'USD': Decimal('0.000')})
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(self.exchange.books["AAPL"].bids[0].qty, 1)

    async def test_insufficient_assets(self):
        await self.exchange.market_buy("AAPL", qty=1, buyer=self.insufficient_seller)
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.insufficient_seller)

        insufficient_seller = await self.exchange.get_agent(self.insufficient_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets", "seller": self.insufficient_seller})
        self.assertEqual(insufficient_seller['assets'], {'AAPL': Decimal('1'), 'USD': Decimal('9848.1970')} )
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

    async def test_no_assets(self):
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.no_asset_seller)

        no_asset_seller = await self.exchange.get_agent(self.no_asset_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets", "seller": self.no_asset_seller})
        self.assertEqual(no_asset_seller['assets'], {'USD': Decimal('10000')} )
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

    async def test_no_fills(self):
        book = self.exchange.books["AAPL"]
        for ask in book.asks:
            await self.exchange.market_buy("AAPL", qty=ask.qty, buyer=self.seller1)
        self.exchange.books["AAPL"].bids.clear()
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.seller1)
        self.assertEqual(result, {"market_sell": "no fills"})

class RegisterAgentTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()


    async def test_register_agent(self):
        agent = await self.exchange.register_agent("agent1", initial_assets={'USD': 10000})
        result = agent['registered_agent']
        self.assertEqual(result[:6], "agent1")
        self.assertEqual(len(self.exchange.agents), 1)
        self.assertEqual(self.exchange.agents[0]['name'], result)
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 0)
        self.assertEqual(self.exchange.agents[0]['assets'], {'USD': 10000})

    async def test_register_agent_error(self):
        self.exchange.max_agents = 1
        await self.exchange.register_agent("agent1", initial_assets={'USD': 10000})
        agent = await self.exchange.register_agent("agent2", initial_assets={'USD': 10000})
        self.assertEqual(agent, {"error": "max agents reached"})

class GetCashTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        agent = await self.exchange.register_agent("agent2", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_get_cash(self):
        result = await self.exchange.get_cash(self.agent)

        self.assertEqual(result, {"cash": 10000})

class GetAssetsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent3", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_get_assets(self):
        await self.exchange.limit_buy("AAPL", price=152, qty=2, creator=self.agent)
        result = await self.exchange.get_assets(self.agent)
        print(result)
        self.assertEqual(result, {'assets': {'USD': Decimal('9696.3940'), 'AAPL': Decimal('2')}, 'frozen_assets': {'USD': Decimal('0.0000')}})

class GetAgentTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        agent = await self.exchange.register_agent("agent4", initial_assets={"AAPL": 10000,'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_get_agent(self):
        result = await self.exchange.get_agent(self.agent)

        self.assertEqual(len(self.exchange.agents), 1)
        self.assertEqual(result['name'], self.agent)
        self.assertEqual(result['_transactions'], [])
        self.assertEqual(len(result['positions']), 2)
        self.assertEqual(result['positions'][0]['qty'], 10000)
        self.assertEqual(result['positions'][0]['enters'][0]['agent'], self.agent)
        self.assertEqual(result['positions'][0]['enters'][0]['qty'], 10000)
        self.assertEqual(result['positions'][0]['enters'][0]['asset'], "AAPL")
        self.assertEqual(result['positions'][0]['exits'], [])
        self.assertEqual(result['positions'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(result['assets'], {"AAPL": 10000, "USD" : 10000})
        self.assertEqual(result['_transactions'], [])

class GetAgentIndexTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        agent = await self.exchange.register_agent("agent5", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_get_agent_index(self):
        result = await self.exchange.get_agent_index(self.agent)
        self.assertEqual(result, 0)

class EnterPositionTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent6", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_enter_position_new(self):
        transaction = {'agent': self.agent, 'cash_flow': -300, 'price': 150, 'ticker': 'AAPL', 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent)
        result = await self.exchange.enter_position(transaction, transaction['ticker'], transaction['qty'], agent_idx, None)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['agent'], self.agent )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis'], {})
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['dt'], datetime(2023, 1, 1))

    async def test_enter_position_existing(self):
        # transaction1 = Transaction(300, "AAPL",150, 2, self.exchange.datetime, "buy").to_dict()
        transaction1 = {'agent': self.agent, 'cash_flow': -300, 'price': 150, 'ticker': 'AAPL', 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent)
        await self.exchange.enter_position(transaction1, transaction1['ticker'], transaction1['qty'], agent_idx, None)
        existing_id = self.exchange.agents[agent_idx]['positions'][1]['id']
        transaction2 = {'agent': self.agent, 'cash_flow': -300, 'price': 150, 'ticker': 'AAPL', 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        result = await self.exchange.enter_position(transaction2, transaction2['ticker'], transaction2['qty'], agent_idx, None)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 4)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis'], {})
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['basis'], {} )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['dt'], datetime(2023, 1, 1))

    async def test_enter_position_with_basis(self):
        transaction1 = {'agent': self.agent, 'quote_flow': -30, 'price': 15, 'base': 'AAPL', 'quote': "ETH", 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent)
        await self.exchange.enter_position(transaction1, transaction1['base'], transaction1['qty'], agent_idx, None, basis={'basis_initial_unit': 'ETH', 'basis_per_unit': 0.1, 'basis_date': self.exchange.datetime})
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['agent'], self.agent )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis'], {'basis_initial_unit': 'ETH', 'basis_per_unit': 0.1, 'basis_date': self.exchange.datetime})
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['dt'], datetime(2023, 1, 1))

class ExitPositionTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agent7", initial_assets={"AAPL": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent7", initial_assets={"USD" : 10000}))['registered_agent']
  
    async def test_exit_position(self):
        agent_idx = await self.exchange.get_agent_index(self.agent)
        self.position_id = self.exchange.agents[agent_idx]['positions'][1]['id']
        side = {'agent': self.agent, 'cash_flow': 50, 'price': 50, 'ticker': 'AAPL', 'qty': -1, 'dt': self.exchange.datetime, 'type': 'sell'}
        result = await self.exchange.exit_position(side, side['ticker'], side['qty'], agent_idx)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['qty'], 9999)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['agent'], self.agent )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['basis']['basis_initial_unit'] , 'USD')
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['basis']['basis_per_unit'], 0)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['basis']['basis_date'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['qty'], 9999)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['initial_qty'], 10000)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['agent'], self.agent)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['basis']['basis_initial_unit'] , 'USD')
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['basis']['basis_per_unit'], 0)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['basis']['basis_date'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['qty'], 1)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['enter_id'], self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['id'])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['dt'], datetime(2023, 1, 1))

    async def test_partial_exit_position(self):
        transaction1 = {'agent': self.agent2, 'cash_flow': -300, 'price': 150, 'ticker': 'AAPL', 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        transaction2 = {'agent': self.agent2, 'cash_flow': -1200, 'price': 200, 'ticker': 'AAPL', 'qty': 6, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent2)
        basis1 = {'basis_initial_unit': 'USD', 'basis_per_unit': 150, 'basis_date': self.exchange.datetime}
        basis2 = {'basis_initial_unit': 'USD', 'basis_per_unit': 200, 'basis_date': self.exchange.datetime}
        await self.exchange.enter_position(transaction1, transaction1['ticker'], transaction1['qty'], agent_idx, None, basis1)
        await self.exchange.enter_position(transaction2, transaction2['ticker'], transaction2['qty'], agent_idx, None, basis2)
        exit_side = {'agent': self.agent2, 'cash_flow': 2500, 'price': 500, 'ticker': 'AAPL',  'qty': -5, 'dt': self.exchange.datetime, 'type': 'sell'}
        exit = await self.exchange.exit_position(exit_side, exit_side['ticker'], exit_side['qty'], agent_idx)
        print(exit)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 5)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['agent'], self.agent2 )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis']['basis_per_unit'], 150)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 0)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['agent'], self.agent2 )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['basis']['basis_per_unit'], 200)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['qty'], 3)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['initial_qty'], 6)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['agent'], self.agent2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['basis']['basis_per_unit'], 150)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['enter_id'], self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['id'])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['agent'], self.agent2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['basis']['basis_per_unit'], 200)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['asset'], "AAPL")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['qty'], 3)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['dt'], datetime(2023, 1, 1))

class GetAgentsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent8", initial_assets={"USD" : 10000}))['registered_agent']

    async def test_get_agents(self):
        result = await self.exchange.get_agents()
        self.assertEqual(len(self.exchange.agents), 1)
        self.assertEqual(result[0]['name'], self.agent)
        self.assertEqual(result[0]['_transactions'], [])
        self.assertEqual(result[0]['positions'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(len(result[0]['positions'][0]['enters']), 1)
        self.assertEqual(result[0]['positions'][0]['exits'], [])
        self.assertEqual(result[0]['positions'][0]['qty'], 10000)
        self.assertEqual(result[0]['positions'][0]['asset'], 'USD')
        self.assertEqual(result[0]['assets'], {"USD": 10000})
        self.assertEqual(result[0]['taxable_events'], [])

class HasAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent9", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_has_asset(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        result = await self.exchange.agent_has_assets(self.agent, "AAPL", 2)
        self.assertEqual(result, True)

class HasCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent10", initial_assets={'USD': 10000})
        self.agent = agent['registered_agent']

    async def test_has_cash(self):
        best_ask = await self.exchange.get_best_ask("AAPL")
        price = best_ask.price
        result = await self.exchange.agent_has_cash(self.agent, price, 10)
        self.assertEqual(result, True)

class GetOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent11", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_order(self):
        order = await self.exchange.limit_buy("AAPL", price=150, qty=2, creator=self.agent)
        result = await self.exchange.get_order(order.ticker, order.id)
        self.assertEqual(result.id, order.id)

class getTransactionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent12", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_transactions(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        result = await self.exchange.get_transactions(self.agent)
        self.assertEqual(len(result['transactions']), 1)
        self.assertEqual(result['transactions'][0]['cash_flow'], -303.0)
        self.assertEqual(result['transactions'][0]['ticker'], 'AAPL')
        self.assertEqual(result['transactions'][0]['qty'], 2)
        self.assertEqual(result['transactions'][0]['type'], 'buy')

class getAgentsCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent13", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_agents_cash(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        result = await self.exchange.agents_cash()
        self.assertEqual(result[0][self.agent]['cash'], Decimal('9696.3940'))

class totalCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent14", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_total_cash(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        result = await self.exchange.total_cash()
        self.assertEqual(result, Decimal('9696.3940'))

class getSharesOutstandingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agentoutstand", initial_assets={'USD': 200000}))['registered_agent']
        await self.exchange.market_buy("AAPL", qty=1000, buyer=self.agent)

    async def test_get_outstanding_shares(self):
        result = await self.exchange.get_outstanding_shares("AAPL")
        self.assertEqual(result, 1000)

class getAgentsHoldingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent1 = (await self.exchange.register_agent("agent16", initial_assets={'USD': 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent17", initial_assets={'USD': 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent18", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_agents_holding(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent1)
        await self.exchange.market_buy("AAPL", qty=3, buyer=self.agent2)
        await self.exchange.market_buy("AAPL", qty=4, buyer=self.agent3)
        result = await self.exchange.get_agents_holding("AAPL")
        self.assertEqual(result, [self.agent1, self.agent2, self.agent3, 'init_seed_AAPL'])

class getAgentsPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("agent19", initial_assets={'USD': 2000000}))['registered_agent']
        self.buy_exit_agent = (await self.exchange.register_agent("buy_exit", initial_assets={'USD': 2000000}))['registered_agent']

    async def test_get_agents_enter_positions(self):
        await self.exchange.market_buy("AAPL", qty=1000, buyer=self.agent)
        result = await self.exchange.get_agents_positions("AAPL")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]['agent'], self.agent)
        self.assertEqual(result[1]['positions'][0]['asset'], 'AAPL')
        self.assertEqual(result[1]['positions'][0]['qty'], 1000)
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['asset'], 'AAPL')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['qty'], 1000)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['exits'], [])

    async def test_get_agents_exit_positions(self):
        await self.exchange.market_buy("AAPL", qty=1000, buyer=self.agent)
        await self.exchange.limit_buy("AAPL", price=100, qty=1000, creator=self.buy_exit_agent)
        sell_result = await self.exchange.market_sell("AAPL", qty=1000, seller=self.agent)
        agent_idx = await self.exchange.get_agent_index(self.agent)
        result = await self.exchange.get_agents_positions("AAPL")

        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]['agent'], self.agent)
        self.assertEqual(result[1]['positions'][0]['asset'], 'AAPL')
        self.assertEqual(result[1]['positions'][0]['qty'], 0)
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['asset'], 'AAPL')
        self.assertEqual(result[1]['positions'][0]['enters'][0]['qty'], 0)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['exits'][0]['asset'], 'AAPL')
        self.assertEqual(result[1]['positions'][0]['exits'][0]['qty'], 1)
        self.assertEqual(result[1]['positions'][0]['exits'][1]['qty'], 999)
        self.assertEqual(result[1]['positions'][0]['exits'][0]['dt'], datetime(2023, 1, 1, 0, 0))

class calculateMarketCapTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent1 = (await self.exchange.register_agent("agentcap", initial_assets={'USD': 1000000}))['registered_agent']
        await self.exchange.market_buy("AAPL", qty=1000, buyer=self.agent1)

    async def test_calculate_market_cap(self):
        result = await self.exchange.calculate_market_cap("AAPL")
        self.assertEqual(result, 151500.0)

class getAgentsSimpleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent1 = (await self.exchange.register_agent("agent19", initial_assets={'USD': 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent20", initial_assets={'USD': 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent21", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_agents_simple(self):
        result = await self.exchange.get_agents_simple()
        self.assertEqual(result[0], {'agent': self.agent1, 'assets': { 'USD': Decimal('10000')}, 'frozen_assets': {}})
        self.assertEqual(result[1], {'agent': self.agent2, 'assets': { 'USD': Decimal('10000')}, 'frozen_assets': {}})
        self.assertEqual(result[2], {'agent': self.agent3, 'assets': { 'USD': Decimal('10000')}, 'frozen_assets': {}})
        self.assertEqual(result[3], {'agent': 'init_seed_AAPL', 'assets': {'AAPL': Decimal('0'), 'USD': Decimal('149699.8515')}, 'frozen_assets': {'USD': Decimal('300.1485'), 'AAPL': Decimal('1000')}})

class getPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent22", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_positions(self):
        await self.exchange.limit_buy("AAPL", price=152, qty=2, creator=self.agent)
        result = await self.exchange.get_positions(self.agent)
        self.assertEqual(result['agent'], self.agent)
        self.assertEqual(result['total_positions'] , 2)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['total_pages'], 1)
        self.assertEqual(result['next_page'], None)
        self.assertEqual(result['page_size'], 10)
        self.assertEqual(len(result['positions']), 2)
        self.assertEqual(result['positions'][1]['asset'], 'AAPL')
        self.assertEqual(result['positions'][1]['qty'], 2)
        self.assertEqual(result['positions'][1]['dt'], datetime(2023, 1, 1, 0, 0))

class getTaxableEventsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent23", initial_assets={'USD': 10000}))['registered_agent']
        self.agent_high_buyer = (await self.exchange.register_agent("agent_high_buyer", initial_assets={'USD': 10000}))['registered_agent']
        await self.exchange.create_asset("AAPL", market_qty=2, seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_taxable_events(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        await self.exchange.limit_buy("AAPL", price=300, qty=2, creator=self.agent_high_buyer)
        await self.exchange.market_sell("AAPL", qty=2, seller=self.agent)
        result = await self.exchange.get_taxable_events(self.agent)
        self.assertEqual(result[0]['agent'], self.agent)
        self.assertEqual(len(result[0]['taxable_events']), 1)
        self.assertEqual(result[0]['taxable_events'][0]['enter_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['exit_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['pnl'], 297.0)
        self.assertEqual(result[0]['taxable_events'][0]['type'], 'capital_gains')

    async def test_get_taxable_events_all(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        await self.exchange.limit_buy("AAPL", price=300, qty=2, creator=self.agent_high_buyer)
        await self.exchange.market_sell("AAPL", qty=2, seller=self.agent)
        result = await self.exchange.get_taxable_events()
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['agent'], self.agent)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['taxable_events'][0]['enter_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['exit_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['pnl'], 297.0)
        self.assertEqual(result[0]['taxable_events'][0]['type'], 'capital_gains')        

class addCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent15", initial_assets={'USD': 0}))['registered_agent']

    async def test_add_cash(self):
        # self.exchange.agents[0]['positions'][0]['exits'].clear()
        result = await self.exchange.add_cash(self.agent, 5000)
        print(result)
        self.assertEqual(result['USD'], 5000)


class getTickersTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", market_qty=2, seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_tickers(self):
        result = await self.exchange.get_tickers()
        self.assertEqual(result, {'AAPL': {'type': 'stock'}})

class pruneTradesTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        self.agent = (await self.exchange.register_agent("agent24", initial_assets={'USD': 10000}))['registered_agent']
        self.exchange.trade_log = [ 1,2,3,4,5,6,7,8,9]

    async def test_prune_trades(self):
        self.exchange.trade_log_limit = 5
        result = await self.exchange.prune_trades()
        self.assertEqual(self.exchange.trade_log, [5,6,7,8,9])

class UpdateAgentsTestCase(unittest.IsolatedAsyncioTestCase):
    #NOTE: This Test has to be run last! It is Leaky! update_agents method is stateful and will insert positions into other tests run after it...
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        self.exchange.logger = Null_Logger()

        await self.exchange.create_asset("AAPL", market_qty=1000, seed_price=150, seed_bid=0.99, seed_ask=1.01)
    
    async def test_update_agents(self):
        self.exchange.agents.clear()
        self.agent1 = (await self.exchange.register_agent("Agent1", initial_assets={"USD" : 100}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("Agent2", initial_assets={"USD" : 200, "AAPL": 1.01}))['registered_agent']
        
        fake_buy_txn = {'agent': self.agent2, 'id': 'fake_enter_id', 'cash_flow': -50, 'price': 50, 'ticker': 'AAPL', 'initial_qty': 1, 'qty': 1, 'dt': self.exchange.datetime, 'type': 'buy'}
    
        self.exchange.agents[1]['_transactions'].append(fake_buy_txn)

        fake_position = {
            'id':"fake_buy_id",
            'asset': "AAPL",
            'price': 50,
            'qty': 1,
            'dt': self.exchange.datetime,
            'enters': [fake_buy_txn],
            'exits': []
        }
        self.exchange.agents[1]['positions'].append(fake_position)
        transaction = [
            {'id': "testbuy",'agent': self.agent1, 'cash_flow': -50, 'price': 50, 'ticker': 'AAPL', 'initial_qty': 1, 'qty': 1, 'dt': self.exchange.datetime, 'fee': 0.01 ,'type': 'buy'},
            {'id': "testsell",'agent': self.agent2, 'cash_flow': 50,  'price': 50,'ticker': 'AAPL', 'qty': -1, 'dt': self.exchange.datetime, 'fee': 0.01 ,'type': 'sell'}
        ]

        await self.exchange.freeze_assets(self.agent1, "USD", 50.01)
        await self.exchange.freeze_assets(self.agent2, "AAPL", 1)
        await self.exchange.freeze_assets(self.agent2, "USD", 0.01)
        
        await self.exchange.update_agents(transaction, "FIFO", "")

        
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 1)
        self.assertEqual(len(self.exchange.agents[1]['_transactions']), 2)
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['cash_flow'], -50)
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['cash_flow'], 50)
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['ticker'], 'AAPL')
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['ticker'], 'AAPL')
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['qty'], 1)
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['qty'], -1)
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['type'], 'buy')
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['type'], 'sell')
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['dt'], self.exchange.datetime)
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['dt'], self.exchange.datetime)
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['asset'], self.exchange.agents[0]['_transactions'][0]['ticker'])
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['dt'], self.exchange.agents[0]['_transactions'][0]['dt'])
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['qty'], self.exchange.agents[0]['_transactions'][0]['qty'])
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['type'], self.exchange.agents[0]['_transactions'][0]['type'])

        print(self.exchange.agents[0]['_transactions'][0])
        print(self.exchange.agents[1]['positions'][1]['enters'])

        self.assertEqual(self.exchange.agents[1]['positions'][0]['enters'][0]['asset'], self.exchange.default_currency['symbol'])
        self.assertEqual(self.exchange.agents[1]['positions'][1]['enters'][0]['asset'], self.exchange.agents[0]['_transactions'][0]['ticker'])

        self.assertEqual(self.exchange.agents[1]['positions'][1]['exits'][0]['qty'], 1)
        self.assertEqual(self.exchange.agents[1]['positions'][1]['exits'][0]['asset'], 'AAPL')

if __name__ == '__main__':
    asyncio.run(unittest.main())