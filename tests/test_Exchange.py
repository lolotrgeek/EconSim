import asyncio
import pytest
import unittest
from datetime import datetime
from unittest.mock import MagicMock
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.exchange.Exchange import Exchange
from source.exchange.types.LimitOrder import LimitOrder
from source.exchange.types.OrderSide import OrderSide

class CreateAssetTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))

    async def test_create_asset(self):
        asset = await self.exchange.create_asset("BTC", 'stock', seed_price=50000)
        book = self.exchange.books["BTC"]
        self.assertEqual(asset['type'], "stock")
        self.assertEqual(book.bids[0].price, 49500)
        self.assertEqual(book.asks[0].price, 50500)

class GetOrderBookTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_order_book(self):
        order_book = await self.exchange.get_order_book("AAPL")
        self.assertEqual(order_book.ticker, "AAPL")
        self.assertEqual(len(order_book.bids), 1)
        self.assertEqual(len(order_book.asks), 1)    

class GetLatestTradeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_latest_trade(self):
        latest_trade = await self.exchange.get_latest_trade("AAPL")
        self.assertEqual(latest_trade["ticker"], "AAPL")
        self.assertEqual(latest_trade["price"], 150)
        self.assertEqual(latest_trade["buyer"], "init_seed_AAPL")
        self.assertEqual(latest_trade["seller"], "init_seed_AAPL")

class GetQuotesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
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
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_midprice(self):
        midprice = await self.exchange.get_midprice("AAPL")
        self.assertEqual(midprice["midprice"], 150)

class GetTradesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        trader1 = await self.exchange.register_agent("trader1", initial_cash=10000)
        trader2 = await self.exchange.register_agent("trader2", initial_cash=10000)
        self.trader1 = trader1['registered_agent']
        self.trader2 = trader2['registered_agent']
        await self.exchange.limit_buy("AAPL", price=152, qty=2, creator=self.trader1, fee=0)
        await self.exchange.limit_sell("AAPL", price=152, qty=2, creator=self.trader2, fee=0) # this one is meant to be ignored
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.trader2, fee=0)

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
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_price_bars(self):
        price_bars = await self.exchange.get_price_bars("AAPL", limit=10)
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': '01/01/2023, 00:00:00'})

class GetBestAskTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_best_ask(self):
        best_ask = await self.exchange.get_best_ask("AAPL")
        self.assertIsInstance(best_ask, LimitOrder)
        self.assertEqual(best_ask.type, OrderSide.SELL)

class GetBestBidTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_get_best_bid(self):
        best_bid = await self.exchange.get_best_bid("AAPL")
        self.assertIsInstance(best_bid, LimitOrder)
        self.assertEqual(best_bid.type, OrderSide.BUY)

#TODO: move register agent test here
#TODO: move limit buy test here
#TODO: move get_order test here

class CancelOrderTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("buyer1", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_cancel_order(self):
        order = await self.exchange.limit_buy("AAPL", price=149, qty=2, creator=self.agent)
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 2)
        cancel = await self.exchange.cancel_order(order.id)
        self.assertEqual(cancel, {"cancelled_order": order.id})
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(await self.exchange.get_order(order.id), None)       

class CancelAllOrdersTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent1 = await self.exchange.register_agent("buyer1", initial_cash=10000)
        agent2 = await self.exchange.register_agent("buyer2", initial_cash=10000)
        self.agent1 = agent1['registered_agent']
        self.agent2 = agent2['registered_agent']

    async def test_cancel_all_orders(self):
        await self.exchange.limit_buy("AAPL", price=150, qty=10, creator=self.agent1, tif="TEST")
        await self.exchange.limit_buy("AAPL", price=152, qty=10, creator=self.agent1, tif="TEST")
        await self.exchange.limit_buy("AAPL", price=153, qty=10, creator=self.agent2, tif="TEST")        
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 4)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

        await self.exchange.cancel_all_orders(self.agent1, "AAPL")

        self.assertEqual(len(self.exchange.books["AAPL"].bids), 2)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

class LimitBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        insufficient_agent = await self.exchange.register_agent("insufficient_buyer", initial_cash=1)
        self.insufficient_agent = insufficient_agent['registered_agent']
        buyer = await self.exchange.register_agent("buyer1", initial_cash=10000)
        self.buyer = buyer['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_limit_buy_sufficient_funds(self):
        new_order = await self.exchange.limit_buy('AAPL', 148, 3, self.buyer, fee=0)

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

        result = await self.exchange.limit_buy('AAPL', 220, 3, self.insufficient_agent, fee=0)

        self.assertEqual(result.creator, 'insufficient_funds')
        self.assertEqual(len(self.exchange.books['AAPL'].bids), 1)

class LimitSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        insufficient_seller = await self.exchange.register_agent("insufficient_seller", initial_cash=10000)
        self.insufficient_seller = insufficient_seller['registered_agent']
        agent = await self.exchange.register_agent("seller1", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_limit_sell_sufficient_assets(self):
        await self.exchange.limit_buy("AAPL", price=152, qty=4, creator=self.agent)
        new_order = await self.exchange.limit_sell('AAPL', 180, 4,self.agent , fee=0)

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

        result = await self.exchange.limit_sell('AAPL', 180, 4, self.insufficient_seller, fee=0)

        self.assertEqual(result.creator, "insufficient_assets")
        self.assertEqual(len(self.exchange.books['AAPL'].asks), 1)

class MarketBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        insufficient_buyer = await self.exchange.register_agent("insufficient_buyer", initial_cash=1)
        self.insufficient_buyer = insufficient_buyer['registered_agent']
        agent = await self.exchange.register_agent("buyer1", initial_cash=10000)
        self.agent = agent['registered_agent']
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)

    async def test_market_buy(self):
        result = await self.exchange.market_buy("AAPL", qty=4, buyer=self.agent, fee=0.01)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(result, {'market_buy': 'AAPL', 'buyer': self.agent, 'fills': [{'qty': 4, 'price': 151.5, 'fee': 0.01}]})
        self.assertEqual(agent['assets'], {"AAPL": 4} )
        self.assertEqual(agent['cash'], 9394.0 )
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)
        self.assertEqual(self.exchange.books["AAPL"].asks[0].qty, 996)

    async def test_insufficient_funds(self):
        # self.exchange.agent_has_cash = MagicMock(return_value=False)

        result = await self.exchange.market_buy("AAPL", qty=4, buyer=self.insufficient_buyer, fee=0.01)
        agent = await self.exchange.get_agent(self.insufficient_buyer)
        self.assertEqual(result, {"market_buy": "insufficient funds"})
        self.assertEqual(agent['assets'], {} )
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)

class MarketSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        no_asset_seller = await self.exchange.register_agent("no_asset_seller", initial_cash=10000)
        infufficient_seller = await self.exchange.register_agent("insufficient_seller", initial_cash=10000)
        seller1 = await self.exchange.register_agent("seller1", initial_cash=10000)
        buyer1 = await self.exchange.register_agent("buyer1", initial_cash=10000)

        self.no_asset_seller = no_asset_seller['registered_agent']
        self.insufficient_seller = infufficient_seller['registered_agent']
        self.seller1 = seller1['registered_agent']
        self.buyer1 = buyer1['registered_agent']

    async def test_market_sell(self):
        await self.exchange.market_buy("AAPL", qty=4, buyer=self.seller1, fee=0.01)

        await self.exchange.limit_buy("AAPL", price=150, qty=3, creator=self.buyer1, fee=0.01)
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.seller1, fee=0.02)

        agent = await self.exchange.get_agent(self.seller1)
        self.assertEqual(result, {'market_sell': 'AAPL', 'seller': self.seller1, 'fills': [{'qty': 3, 'price': 150, 'fee': 0.02}]})
        self.assertEqual(agent['assets'], {"AAPL": 1})
        self.assertEqual(agent['cash'], 9844.0)
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(self.exchange.books["AAPL"].bids[0].qty, 1)

    async def test_insufficient_assets(self):
        await self.exchange.market_buy("AAPL", qty=1, buyer=self.insufficient_seller, fee=0.01)
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.insufficient_seller, fee=0.02)

        insufficient_seller = await self.exchange.get_agent(self.insufficient_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets"})
        self.assertEqual(insufficient_seller['assets'], {"AAPL": 1} )
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

    async def test_no_assets(self):
        result = await self.exchange.market_sell("AAPL", qty=3, seller=self.no_asset_seller, fee=0.02)

        no_asset_seller = await self.exchange.get_agent(self.no_asset_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets"})
        self.assertEqual(no_asset_seller['assets'], {} )
        self.assertEqual(len(self.exchange.books["AAPL"].bids), 1)
        self.assertEqual(len(self.exchange.books["AAPL"].asks), 1)

class RegisterAgentTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))

    async def test_register_agent(self):
        agent = await self.exchange.register_agent("agent1", initial_cash=10000)
        result = agent['registered_agent']
        self.assertEqual(result[:6], "agent1")
        self.assertEqual(len(self.exchange.agents), 1)
        self.assertEqual(self.exchange.agents[0]['name'], result)
        self.assertEqual(self.exchange.agents[0]['cash'], 10000)
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 0)

class GetCashTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        agent = await self.exchange.register_agent("agent2", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_get_cash(self):
        result = await self.exchange.get_cash(self.agent)

        self.assertEqual(result, {"cash": 10000})

class GetAssetsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent3", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_get_assets(self):
        await self.exchange.limit_buy("AAPL", price=152, qty=2, creator=self.agent)
        result = await self.exchange.get_assets(self.agent)
        self.assertEqual(result, {"assets": {"AAPL": 2}})

class GetAgentTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        agent = await self.exchange.register_agent("agent4", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_get_agent(self):
        result = await self.exchange.get_agent(self.agent)
        self.assertEqual(result, {"name": self.agent, "cash": 10000, "_transactions": [], "positions": [], "assets": {}})

class GetAgentIndexTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        agent = await self.exchange.register_agent("agent5", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_get_agent_index(self):
        result = await self.exchange._Exchange__get_agent_index(self.agent)
        self.assertEqual(result, 0)

class UpdateAgentsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        agent = await self.exchange.register_agent("agent6", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_update_agents(self):
        self.exchange.agents.clear()
        agent1 = await self.exchange.register_agent("Agent1", initial_cash=100)
        agent2 = await self.exchange.register_agent("Agent2", initial_cash=200)
        self.agent1 = agent1['registered_agent']
        self.agent2 = agent2['registered_agent']
        transaction = [
            {'agent': self.agent1, 'cash_flow': -50, 'ticker': 'AAPL', 'qty': 1, 'dt': self.exchange.datetime, 'type': 'buy'},
            {'agent': self.agent2, 'cash_flow': 50, 'ticker': 'AAPL', 'qty': 1, 'dt': self.exchange.datetime, 'type': 'sell'}
        ]
        #TODO: positioning    
        await self.exchange._Exchange__update_agents(transaction, "FIFO", "")

        self.assertEqual(self.exchange.agents[0]['cash'], 50)
        self.assertEqual(self.exchange.agents[1]['cash'], 250)
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 1)
        self.assertEqual(len(self.exchange.agents[1]['_transactions']), 1)

class UpdateAgentsCurrencyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        agent = await self.exchange.register_agent("agent7", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_update_agents_currency(self):
        self.exchange.agents.clear()
        agent1 = await self.exchange.register_agent("Agent1", initial_cash=100)
        agent2 = await self.exchange.register_agent("Agent2", initial_cash=200)
        self.agent1 = agent1['registered_agent']
        self.agent2 = agent2['registered_agent']

        class MockTransaction:
            def __init__(self, recipient, sender, amount, fee, confirmed):
                self.recipient = recipient
                self.sender = sender
                self.amount = amount
                self.fee = fee
                self.confirmed = confirmed
                self.ticker = 'AAPL'

        transaction = MockTransaction(self.agent2, self.agent1, 100, 5, True)

        await self.exchange._Exchange__update_agents_currency(transaction)

        self.assertEqual(self.exchange.agents[0]['cash'], 200)
        self.assertEqual(self.exchange.agents[1]['cash'], 95)
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 1)
        self.assertEqual(len(self.exchange.agents[1]['_transactions']), 1)

class GetAgentsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        agent = await self.exchange.register_agent("agent8", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_get_agents(self):
        result = await self.exchange.get_agents()
        print(result)
        self.assertEqual(result, [{'name': self.agent, 'cash': 10000, '_transactions': [], "positions":[], 'assets': {}}])

class HasAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent9", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_has_asset(self):
        await self.exchange.market_buy("AAPL", qty=2, buyer=self.agent)
        result = await self.exchange.agent_has_assets(self.agent, "AAPL", 2)
        self.assertEqual(result, True)

class HasCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = Exchange(datetime=datetime(2023, 1, 1))
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        agent = await self.exchange.register_agent("agent10", initial_cash=10000)
        self.agent = agent['registered_agent']

    async def test_has_cash(self):
        best_ask = await self.exchange.get_best_ask("AAPL")
        price = best_ask.price
        result = await self.exchange.agent_has_cash(self.agent, price, 10)
        self.assertEqual(result, True)

if __name__ == '__main__':
    asyncio.run(unittest.main())