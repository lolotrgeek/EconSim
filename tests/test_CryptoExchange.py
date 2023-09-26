import unittest
from decimal import Decimal
from datetime import datetime
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.exchange.CryptoExchange import CryptoExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from .MockRequesterCrypto import MockRequesterCrypto as MockRequester

async def standard_asyncSetUp(self):
    self.mock_requester = MockRequester()
    self.requests = Requests(self.mock_requester)
    self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
    await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
    self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
    self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
    await self.exchange.next()
    return self.exchange      

class CreateAssetTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)

    async def test_create_asset(self):
        asset = await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}])

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        # print(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].to_dict())
        # print(self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].to_dict())
        await self.exchange.next()

        self.assertEqual("BTC" in self.exchange.assets, True )
        self.assertEqual(self.exchange.assets['BTC']['type'], "crypto")
        book = self.exchange.books["BTCUSD"]
        self.assertEqual(book.bids[0].price, 99.0)
        self.assertEqual(book.asks[0].price, 101)

    async def test_create_duplicate_asset(self):
        asset = await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()        
        asset = await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.assertEqual(asset, {"error": "asset BTC already exists"})        

class GetOrderBookTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_order_book(self):
        order_book = await self.exchange.get_order_book("BTCUSD")
        self.assertEqual(order_book.ticker, "BTCUSD")
        self.assertEqual(len(order_book.bids), 1)
        self.assertEqual(len(order_book.asks), 1)    

class GetLatestTradeTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_latest_trade(self):
        await self.exchange.next()
        latest_trade = await self.exchange.get_latest_trade("BTC", "USD")
        print(latest_trade)
        self.assertEqual(latest_trade["base"], "BTC")
        self.assertEqual(latest_trade["quote"], "USD")
        self.assertEqual(latest_trade["price"], 150)
        self.assertEqual(latest_trade["buyer"], "init_seed_BTCUSD")
        self.assertEqual(latest_trade["seller"], "init_seed_BTCUSD")

    async def test_get_latest_trade_error(self):
        self.exchange.trade_log.clear()
        latest_trade = await self.exchange.get_latest_trade("BTC", "USD")
        self.assertEqual(latest_trade, {"error": "no trades found"})

class GetQuotesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_quotes(self):
        quotes = await self.exchange.get_quotes("BTCUSD")
        self.assertEqual(quotes["ticker"], "BTCUSD")
        self.assertEqual(quotes["bid_qty"], 1)
        self.assertEqual(quotes["bid_p"], 148.5)
        self.assertEqual(quotes["ask_qty"], Decimal('997.999999999')) # this is not 1000 because it has accounted for fees
        self.assertEqual(quotes["ask_p"], 151.5)

class GetMidpriceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_midprice(self):
        midprice = await self.exchange.get_midprice("BTCUSD")
        self.assertEqual(midprice, 150)

class RegisterAgentTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_register_agent(self):
        agent = await self.exchange.register_agent("agent1", initial_assets={"BTC": 10000, "USD" : 10000})
        result = agent['registered_agent']
        self.assertEqual(result[:6], "agent1")
        self.assertEqual(len(self.exchange.agents), 2)
        self.assertEqual(self.exchange.agents[1]['name'], result)
        self.assertEqual(self.exchange.agents[1]['assets'], {"BTC": 10000, "USD" : 10000})
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 0)
        
class GetBestAskTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_best_ask(self):
        best_ask = await self.exchange.get_best_ask("BTCUSD")
        self.assertEqual(best_ask.price, 151.5)
        self.assertEqual(best_ask.qty, Decimal('997.999999999')) # not 1000 because it has accounted for fees

class GetBestBidTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_best_bid(self):
        best_bid = await self.exchange.get_best_bid("BTCUSD")
        self.assertEqual(best_bid.price, 148.5)
        self.assertEqual(best_bid.qty, 1)

    async def test_get_best_bid_error(self):
        self.exchange.books["BTCUSD"].bids.clear()
        best_bid = await self.exchange.get_best_bid("BTCUSD")
        self.assertEqual(best_bid.ticker, "BTCUSD")
        self.assertEqual(best_bid.price, 0)
        self.assertEqual(best_bid.qty, 0)
        self.assertEqual(best_bid.creator, "null_quote")

class LimitBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.insufficient_agent = (await self.exchange.register_agent("insufficient_buyer", initial_assets={"USD": 1}))['registered_agent']
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.seller = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.match_buyer = (await self.exchange.register_agent("match_buyer", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
    
    async def test_limit_buy_sufficient_funds(self):
        new_order = await self.exchange.limit_buy('BTC', 'USD', 148, 3, self.buyer, fee=0)

        self.assertEqual(len(self.exchange.books['BTCUSD'].bids), 2)
        self.assertEqual(self.exchange.books['BTCUSD'].bids[1].price, 148)
        self.assertEqual(self.exchange.books['BTCUSD'].bids[1].qty, 3)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 148)
        self.assertEqual(new_order.qty, 3)
        self.assertEqual(new_order.creator, self.buyer)

    async def test_limit_buy_insufficient_funds(self):
        result = await self.exchange.limit_buy('BTC', 'USD', 220, 3, self.insufficient_agent, fee=0)

        self.assertEqual(result.creator, self.insufficient_agent)
        self.assertEqual(result.accounting, 'insufficient_funds')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['BTCUSD'].bids), 1)

class LimitSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.insufficient_seller = (await self.exchange.register_agent("insufficient_seller", initial_assets={"USD" : 10000}))['registered_agent']
        self.agent = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_limit_sell_sufficient_assets(self):
        await self.exchange.limit_buy("BTC" , "USD", price=152, qty=4, creator=self.agent)
        new_order = await self.exchange.limit_sell('BTC', "USD", 180, 4,self.agent , fee=0)
        
        self.assertEqual(len(self.exchange.books['BTCUSD'].asks), 2)
        self.assertEqual(self.exchange.books['BTCUSD'].asks[1].price, 180)
        self.assertEqual(self.exchange.books['BTCUSD'].asks[1].qty, 4)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 180)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.agent)

    async def test_limit_sell_insufficient_assets(self):
        # self.exchange.agent_has_assets = MagicMock(return_value=False)

        result = await self.exchange.limit_sell('BTC', 'USD', 180, 4, self.insufficient_seller, fee=0)

        self.assertEqual(result.creator, self.insufficient_seller)
        self.assertEqual(result.accounting, 'insufficient_assets')
        self.assertEqual(result.status, 'error')        
        self.assertEqual(len(self.exchange.books['BTCUSD'].asks), 1)

class LimitOrderMatchingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.seller = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.match_buyer = (await self.exchange.register_agent("match_buyer", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_limit_order_match_trades(self):
        await self.exchange.limit_sell("BTC", "USD", price=145, qty=5, creator=self.seller, fee=0.001)
        new_order = await self.exchange.limit_buy('BTC', 'USD', 145, 4, self.match_buyer, fee=0.001)

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()

        agent = await self.exchange.get_agent(self.match_buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        # check that assets are unfrozen 
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 145)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.match_buyer)
        self.assertEqual(agent['assets'], {"BTC": Decimal('10004'), "USD": Decimal('9418.839')})
        self.assertEqual(agent_seller['assets'], {"BTC": Decimal('9994.122'), "USD": Decimal('10728.5')})
        self.assertEqual(agent['frozen_assets'], {'USD': 0})
        self.assertEqual(agent_seller['frozen_assets'], {'BTC': 0,})  

    async def test_limit_matching_add_fails(self):
        async def add_transaction(asset, fee, amount, sender, recipient): return {"error": "messaging error, blockchain unreachable"}
        self.requests.add_transaction = add_transaction

        sell_order = await self.exchange.limit_sell("BTC", "USD", price=145, qty=5, creator=self.seller, fee=0.001)
        new_order = await self.exchange.limit_buy('BTC', 'USD', 145, 4, self.match_buyer, fee=0.001)

        print(sell_order.to_dict())
        print(new_order)
        books = self.exchange.books['BTCUSD']
        await self.exchange.next()

        print (self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print (self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        print(books.bids)
        print(books.asks)

        agent = await self.exchange.get_agent(self.match_buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(len(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions), 1)
        self.assertEqual(len(self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions), 1)
        # NOTE: normally the sell order would process, at least partially, as a taker order, in this case it cannot process at all so it becomes a maker order
        self.assertEqual(len(books.bids), 2)
        self.assertEqual(len(books.asks), 2) 
        self.assertEqual(agent['assets'], {"BTC": 10000, "USD": Decimal('9419.999')}) 
        self.assertEqual(agent_seller['assets'], {"BTC": Decimal('9994.999'), "USD": 10000}) 
        #NOTE: assets will stay frozen for maker orders 
        self.assertEqual(agent['frozen_assets'], {'USD': Decimal('580.001')}) 
        self.assertEqual(agent_seller['frozen_assets'], {'BTC': Decimal('5.001'),})

    async def test_limit_matching_get_fails(self):
        async def get_transaction (asset, id): return {"error": "messaging error, blockchain unreachable"}
        self.requests.get_transaction = get_transaction

        sell_order = await self.exchange.limit_sell("BTC", "USD", price=145, qty=5, creator=self.seller, fee=0.001)
        new_order = await self.exchange.limit_buy('BTC', 'USD', 150, 4, self.match_buyer, fee=0.001)
        print(new_order)
        books = self.exchange.books['BTCUSD']
        await self.exchange.next()

        print (self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print (self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        print(books.bids)
        print(books.asks)

        agent = await self.exchange.get_agent(self.match_buyer)
        #NOTE: the transactions all get added to the chain, but now the chain has gone offline or is unreachable
        # we simply have to wait for the chain to come back online and then the transactions will be processed
        self.assertEqual(len(self.exchange.pending_transactions), 2)
        self.assertEqual(len(books.bids), 0) # NOTE: the orders are still going to match even if the transaction cannot be retrieved or confirmed yet
        self.assertEqual(len(books.asks), 1) 
        self.assertEqual(agent['assets'], {"BTC": 10000, "USD": Decimal('9419.999')}) 
        #NOTE: assets will stay frozen for maker orders 
        self.assertEqual(agent['frozen_assets'], {'USD': 580})         

class MarketBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.insufficient_buyer = (await self.exchange.register_agent("insufficient_buyer", initial_assets={"USD": 1}))['registered_agent']
        self.agent = (await self.exchange.register_agent("buyer1", initial_assets={"USD" : 500000}))['registered_agent']
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])

    async def test_market_buy(self):
        result = await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(result, {'market_buy': 'BTCUSD', 'buyer': self.agent, 'qty': 4, 'fills': [{'qty': 4, 'price': Decimal('151.5'), 'fee': Decimal('0.008')}]})
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)
        self.assertEqual(self.exchange.books["BTCUSD"].asks[0].qty, Decimal('993.999999999'))
        self.assertEqual(agent['assets'], {"BTC": 4, "USD":Decimal('499393.982')} )
        self.assertEqual(agent['frozen_assets'], {"USD":0.0} )

    async def test_insufficient_funds(self):
        result = await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.insufficient_buyer, fee=0.01)
        agent = await self.exchange.get_agent(self.insufficient_buyer)
        self.assertEqual(result, {"market_buy": "insufficient funds", "buyer": self.insufficient_buyer})
        self.assertEqual(agent['assets'], {'USD': 1}  )
        self.assertEqual(agent['frozen_assets'], {}  )
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)

    async def test_no_fills(self):
        book = self.exchange.books["BTCUSD"]
        for bid in book.bids:
            buyup = await self.exchange.market_buy("BTC", "USD", qty=bid.qty, buyer=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        self.exchange.books["BTCUSD"].asks.clear()
        agent = await self.exchange.get_agent(self.agent)
        result = await self.exchange.market_buy("BTC","USD", qty=3, buyer=self.agent, fee=0.02)
        self.assertEqual(result, {"market_buy": "no fills"})
        self.assertEqual(agent['frozen_assets'], {'USD': 0.0}  )

class MarketSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.no_asset_seller = (await self.exchange.register_agent("no_asset_seller", initial_assets={}))['registered_agent']
        self.insufficient_seller = (await self.exchange.register_agent("insufficient_seller", initial_assets={"BTC": 1}))['registered_agent']
        self.seller1 = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 500000}))['registered_agent']
        self.buyer1 = (await self.exchange.register_agent("buyer1", initial_assets={"USD":500000}))['registered_agent']

    async def test_market_sell(self):
        buy = await self.exchange.limit_buy("BTC" , "USD", price=145, qty=3, creator=self.buyer1, fee=0.01)
        # print(buy.to_dict_full())
        books = self.exchange.books["BTCUSD"]
        # print(books.bids)
        result = await self.exchange.market_sell("BTC","USD", qty=3, seller=self.seller1, fee=0.02)
        print(result)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()

        print((await self.exchange.get_agent(self.seller1))['frozen_assets'])


        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()

        print(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print(self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        agent = await self.exchange.get_agent(self.seller1)
        buyer_agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(agent['frozen_assets'], {"BTC":0.0} )
        self.assertEqual(result['market_sell'], 'BTCUSD')
        self.assertEqual(result['seller'], self.seller1)
        self.assertEqual(result['qty'], Decimal(str(3))) 
        self.assertEqual(result['fills'], [
            {'qty': Decimal('1'), 'price': Decimal('148.5'), 'fee': Decimal('0.002')}, 
            {'qty': Decimal('2'), 'price': Decimal('145'), 'fee': Decimal('0.004') }
        ])
        
        self.assertEqual(agent['assets'], {"BTC": Decimal('499996.974'), "USD": Decimal('438.5')})
        self.assertEqual(buyer_agent['assets'], {"BTC": Decimal('2'), "USD": Decimal('499564.987')})
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(self.exchange.books["BTCUSD"].bids[0].qty, 1)
        

    async def test_insufficient_assets(self):
        await self.exchange.market_buy("BTC", "USD", qty=1, buyer=self.insufficient_seller, fee=0.01)
        result = await self.exchange.market_sell("BTC", "USD", qty=3, seller=self.insufficient_seller, fee=0.02)

        insufficient_seller = await self.exchange.get_agent(self.insufficient_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets", "seller": self.insufficient_seller})
        self.assertEqual(insufficient_seller['assets'], {"BTC": 1} )
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)

    async def test_no_assets(self):
        result = await self.exchange.market_sell("BTC", "USD", qty=3, seller=self.no_asset_seller, fee=0.02)

        no_asset_seller = await self.exchange.get_agent(self.no_asset_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets", "seller": self.no_asset_seller})
        self.assertEqual(no_asset_seller['assets'], {} )
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)

    async def test_no_fills(self):
        book = self.exchange.books["BTCUSD"]
        for ask in book.asks:
            await self.exchange.market_buy("BTC", "USD", qty=ask.qty, buyer=self.seller1, fee=0.01)
        
        self.exchange.books["BTCUSD"].bids.clear()
        result = await self.exchange.market_sell("BTC", "USD", qty=3, seller=self.seller1, fee=0.02)
        self.assertEqual(result, {"market_sell": "no fills"})

class MarketMatchingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.hoarder = (await self.exchange.register_agent("hoarder", initial_assets={"USD": 10_000_000}))['registered_agent']
        self.buyer1 = (await self.exchange.register_agent("buyer1", initial_assets={"USD":500000}))['registered_agent']   

    async def test_market_partial_matching(self):
        """
        the goal here is to see if a market order will partially fill and still resolve: closing the order and unfreezing the assets
        """
        hoard = await self.exchange.market_buy("BTC", "USD", qty=999, buyer=self.hoarder, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        await self.exchange.limit_sell("BTC", "USD", price=200, qty=1, creator=self.hoarder, fee=0.01)        
        result = await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.buyer1, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()
        print(result)
        print(self.exchange.books["BTCUSD"].bids[0])
        agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(result, {'market_buy': 'BTCUSD', 'buyer': self.buyer1, 'qty': 2, 'fills': [{'qty': 1, 'price': Decimal('200'), 'fee': Decimal('0.002')}]})
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 0)
        self.assertEqual(agent['assets'], {"BTC": 1, "USD":Decimal('499799.993')} )
        self.assertEqual(agent['frozen_assets'], {"USD":0.0} )

class FractionalOrdersTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.seller1 = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 5}))['registered_agent']
        self.buyer1 = (await self.exchange.register_agent("buyer1", initial_assets={"USD":500000}))['registered_agent']
        self.generous = (await self.exchange.register_agent("generous", initial_assets={"USD":10_000_000}))['registered_agent']

    async def test_fractional_buy(self):
        new_order = await self.exchange.market_buy('BTC', 'USD', 0.00005, self.buyer1, fee=0.01)
        print(new_order)
        books = self.exchange.books["BTCUSD"]
        print(books.bids)
        print(books.asks)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(agent['assets'], {"BTC": Decimal('0.00005'), "USD":Decimal('499999.98242490')} )
        self.assertEqual(agent['frozen_assets'], {"USD":0.0} )        

    async def test_fractional_sell(self):
        result = await self.exchange.market_sell("BTC", "USD", qty=0.00005, seller=self.seller1, fee=0.02)
        print(result)
        books = self.exchange.books["BTCUSD"]
        print(books.bids)
        print(books.asks)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.seller1)
        buyer_agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(agent['assets'],{'BTC': Decimal('4.97994990'), 'USD': Decimal('0.0074250')} )
        self.assertEqual(agent['frozen_assets'], {"BTC":0.0} )

    async def test_fractional_price(self):
        generous = await self.exchange.market_buy("BTC", "USD", qty=999, buyer=self.generous, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()        
        print(generous)
        await self.exchange.limit_sell("BTC", "USD", price=0.00005, qty=997, creator=self.generous, fee=0.01)
        buy_single = await self.exchange.limit_buy("BTC", "USD", price=0.00015, qty=1, creator=self.buyer1, fee=0.01)
        await self.exchange.limit_buy("BTC", "USD", price=0.00015, qty=0.01234, creator=self.buyer1, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[4].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[4].confirmed = True

        await self.exchange.next()
        books = self.exchange.books["BTCUSD"]
        agent = await self.exchange.get_agent(self.buyer1)
        print('buy single', buy_single.to_dict_full())
        self.assertEqual(books.asks[0].price, Decimal('0.00005'))
        self.assertEqual(agent['assets'], {'BTC': Decimal('1.01234'), 'USD': Decimal('499999.979949281766')} )
        
    async def test_large_fractional_qty(self):
        generous = await self.exchange.market_buy("BTC", "USD", qty=999, buyer=self.generous, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()        
        print(generous)
        await self.exchange.limit_sell("BTC", "USD", price=0.00005, qty=997, creator=self.generous, fee=0.01)
        buy_single = await self.exchange.limit_buy("BTC", "USD", price=0.00015, qty=1, creator=self.buyer1, fee=0.01)
        await self.exchange.limit_buy("BTC", "USD", price=0.00015, qty=0.000000000001234, creator=self.buyer1, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[4].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[4].confirmed = True

        await self.exchange.next()
        books = self.exchange.books["BTCUSD"]
        agent = await self.exchange.get_agent(self.buyer1)
        print('buy single', buy_single.to_dict_full())
        self.assertEqual(books.asks[0].price, Decimal('0.00005'))
        self.assertEqual(agent['assets'], {'BTC': Decimal('1.000000000001234'), 'USD': Decimal('499999.979949900000')} )

class GetTradesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.trader1 = (await self.exchange.register_agent("trader1", initial_assets={"USD":10000}))['registered_agent']
        self.trader2 = (await self.exchange.register_agent("trader2", initial_assets={"BTC": 1000, "USD":10000}))['registered_agent']
        await self.exchange.limit_buy("BTC", "USD", price=152, qty=2, creator=self.trader1, fee=0)
        await self.exchange.limit_sell("BTC", "USD", price=152, qty=2, creator=self.trader2, fee=0) #NOTE this one is meant to be ignored
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.trader2, fee=0.01)  
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True

        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()

    async def test_get_trades(self):
        trades = await self.exchange.get_trades("BTC", "USD", limit=10)
        self.assertEqual(len(trades), 2)
        for trade in trades:
            self.assertEqual(trade["base"], "BTC")
            if trade['buyer'] == 'init_seed_BTCUSD':
                self.assertEqual(trade["price"], 150)
            else:
                self.assertNotEqual(trade["buyer"], trade["seller"])

class CancelOrderTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        agent = await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000})
        self.agent = agent['registered_agent']

    async def test_cancel_order(self):
        order = await self.exchange.limit_buy("BTC" , "USD", price=149, qty=2, creator=self.agent)
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 2)
        cancel = await self.exchange.cancel_order("BTC", "USD", order.id)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(cancel["cancelled_order"]['id'], order.id)
        self.assertEqual(cancel["cancelled_order"]['creator'], self.agent)
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(await self.exchange.get_order("BTCUSD", order.id), {'error': 'order not found'})       
        self.assertEqual(agent['frozen_assets'], {'USD': 0})

    async def test_cancel_order_error(self):
        cancel = await self.exchange.cancel_order('BTC', 'USD', "error")
        self.assertEqual(cancel, {"cancelled_order": "order not found"})

class CancelAllOrdersTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent1 = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("buyer2", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_cancel_all_orders(self):
        await self.exchange.limit_buy("BTC", "USD", price=150, qty=10, creator=self.agent1, tif="TEST")
        await self.exchange.limit_buy("BTC", "USD", price=149, qty=10, creator=self.agent1, tif="TEST")
        await self.exchange.limit_buy("BTC", "USD", price=153, qty=10, creator=self.agent2, tif="TEST")        
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 4)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)

        canceled = await self.exchange.cancel_all_orders("BTC", "USD", self.agent1 )
        agent = await self.exchange.get_agent(self.agent1)
        print(canceled)    

        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 2)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)
        self.assertEqual(len(canceled['cancelled_orders']), 2)
        self.assertEqual(agent['frozen_assets'], {'USD': 0})

class GetCashTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent2", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_cash(self):
        result = await self.exchange.get_cash(self.agent)

        self.assertEqual(result, {"cash": 10000})

class GetAssetsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent = (await self.exchange.register_agent("agent3", initial_assets={"USD" : 10000}))['registered_agent']

    async def test_get_assets(self):
        await self.exchange.limit_buy("BTC" , "USD", price=152, qty=2, creator=self.agent, fee=0.005) 
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        result = await self.exchange.get_assets(self.agent)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(result, {"assets": {"BTC": 2, "USD": Decimal('9696.3890')}})
        self.assertEqual(agent['assets'], {"BTC": 2, "USD": Decimal('9696.3890')})
        self.assertEqual(agent['frozen_assets'], {'USD': 0})

class GetAgentTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent4", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_agent(self):
        result = await self.exchange.get_agent(self.agent)

        self.assertEqual(len(self.exchange.agents), 2)
        self.assertEqual(result['name'], self.agent)
        self.assertEqual(result['_transactions'], [])
        self.assertEqual(len(result['positions']), 2)
        self.assertEqual(result['positions'][0]['qty'], 10000)
        self.assertEqual(result['positions'][0]['enters'][0]['agent'], self.agent)
        self.assertEqual(result['positions'][0]['enters'][0]['qty'], 10000)
        self.assertEqual(result['positions'][0]['enters'][0]['asset'], "BTC")
        self.assertEqual(result['positions'][0]['exits'], [])
        self.assertEqual(result['positions'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(result['assets'], {"BTC": 10000, "USD" : 10000})
        self.assertEqual(result['_transactions'], [])

class GetAgentIndexTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent5", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_agent_index(self):
        result = await self.exchange.get_agent_index(self.agent)
        self.assertEqual(result, 1)

class EnterPositionTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent = (await self.exchange.register_agent("agent6", initial_assets={"USD" : 10000}))['registered_agent']
        self.agent_existing = (await self.exchange.register_agent("existing_agent", initial_assets={"BTC": 2, "USD" : 10000}))['registered_agent']

    async def test_enter_position_new(self):
        transaction = {'agent': self.agent, 'quote_flow': -300, 'price': 150, 'base': 'BTC', 'quote': 'USD', 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent)
        result = await self.exchange.enter_position(transaction, transaction['base'], transaction['qty'], agent_idx, None)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['agent'], self.agent )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis'], {})
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['dt'], datetime(2023, 1, 1))

    async def test_enter_position_existing(self):
        # transaction1 = Transaction(300, "BTC",150, 2, self.exchange.datetime, "buy").to_dict()
        transaction1 = {'agent': self.agent_existing, 'quote_flow': -300, 'price': 150, 'base': 'BTC', 'quote': "USD", 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent_existing)
        await self.exchange.enter_position(transaction1, transaction1['base'], transaction1['qty'], agent_idx, None)
        existing_id = self.exchange.agents[agent_idx]['positions'][0]['id']
        transaction2 = {'agent': self.agent_existing, 'quote_flow': -300, 'price': 150, 'base': 'BTC','quote': "USD", 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        result = await self.exchange.enter_position(transaction2, transaction2['base'], transaction2['qty'], agent_idx, existing_id)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['qty'], 6) # buys 4, started with 2
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][1]['basis'], {})
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][1]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][1]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][1]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][1]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][2]['basis'], {} )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][2]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][2]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][2]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][2]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['dt'], datetime(2023, 1, 1))

    async def test_enter_position_with_basis(self):
        transaction1 = {'agent': self.agent, 'quote_flow': -30, 'price': 15, 'base': 'BTC', 'quote': "ETH", 'initial_qty': 2, 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent)
        await self.exchange.enter_position(transaction1, transaction1['base'], transaction1['qty'], agent_idx, None, basis={'basis_initial_unit': 'ETH', 'basis_per_unit': 0.1, 'basis_date': self.exchange.datetime})
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['agent'], self.agent )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis'], {'basis_initial_unit': 'ETH', 'basis_per_unit': 0.1, 'basis_date': self.exchange.datetime})
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['dt'], datetime(2023, 1, 1))

class ExitPositionTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent = (await self.exchange.register_agent("agent7", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent7", initial_assets={"USD" : 10000}))['registered_agent']
  
    async def test_exit_position(self):
        # enter = Transaction(-300, 'BTC', 150, 2, self.exchange.datetime, "buy").to_dict()
        # enter = {'agent': self.agent, 'quote_flow': -300, 'price': 150, 'base': 'BTC', 'quote': 'USD', 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent)
        # await self.exchange.enter_position(enter, agent_idx, None)
        self.position_id = self.exchange.agents[agent_idx]['positions'][1]['id']
        side = {'agent': self.agent, 'quote_flow': 50, 'price': 50, 'base': 'BTC', 'quote': 'USD',  'qty': -1, 'dt': self.exchange.datetime, 'type': 'sell'}
        result = await self.exchange.exit_position(side, side['base'], side['qty'], agent_idx)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'], [])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['qty'], 9999)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['agent'], self.agent )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['basis']['basis_initial_unit'] , 'USD')
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['basis']['basis_per_unit'], 0)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['basis']['basis_date'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['qty'], 9999)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['initial_qty'], 10000)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['agent'], self.agent)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['basis']['basis_initial_unit'] , 'USD')
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['basis']['basis_per_unit'], 0)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['basis']['basis_date'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['qty'], 1)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['exits'][0]['enter_id'], self.exchange.agents[agent_idx]['positions'][0]['enters'][0]['id'])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][0]['dt'], datetime(2023, 1, 1))

    async def test_partial_exit_position(self):
        transaction1 = {'agent': self.agent2, 'quote_flow': -300, 'price': 150, 'base': 'BTC', 'quote': 'USD', 'qty': 2, 'dt': self.exchange.datetime, 'type': 'buy'}
        transaction2 = {'agent': self.agent2, 'quote_flow': -1200, 'price': 200, 'base': 'BTC', 'quote': 'USD', 'qty': 6, 'dt': self.exchange.datetime, 'type': 'buy'}
        agent_idx = await self.exchange.get_agent_index(self.agent2)
        basis1 = {'basis_initial_unit': 'USD', 'basis_per_unit': 150, 'basis_date': self.exchange.datetime}
        basis2 = {'basis_initial_unit': 'USD', 'basis_per_unit': 200, 'basis_date': self.exchange.datetime}
        await self.exchange.enter_position(transaction1, transaction1['base'], transaction1['qty'], agent_idx, None, basis1)
        await self.exchange.enter_position(transaction2, transaction2['base'], transaction2['qty'], agent_idx, None, basis2)
        exit_side = {'agent': self.agent2, 'quote_flow': 2500, 'price': 500, 'base': 'BTC', 'quote': 'USD',  'qty': -5, 'dt': self.exchange.datetime, 'type': 'sell'}
        exit = await self.exchange.exit_position(exit_side, exit_side['base'], exit_side['qty'], agent_idx)
        print(exit)
        self.assertEqual(len(self.exchange.agents[agent_idx]['positions']), 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['qty'], 5)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['agent'], self.agent2 )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['basis']['basis_per_unit'], 150)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['qty'], 0)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['initial_qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['agent'], self.agent2 )
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['basis']['basis_per_unit'], 200)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['qty'], 3)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['enters'][1]['initial_qty'], 6)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['agent'], self.agent2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['basis']['basis_per_unit'], 150)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['qty'], 2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][0]['enter_id'], self.exchange.agents[agent_idx]['positions'][1]['enters'][0]['id'])
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['agent'], self.agent2)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['basis']['basis_per_unit'], 200)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['asset'], "BTC")
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['qty'], 3)
        self.assertEqual(self.exchange.agents[agent_idx]['positions'][1]['exits'][1]['dt'], datetime(2023, 1, 1))

class GetAgentsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent8", initial_assets={"USD" : 10000}))['registered_agent']

    async def test_get_agents(self):
        result = await self.exchange.get_agents()
        self.assertEqual(len(self.exchange.agents), 2)
        self.assertEqual(result[1]['name'], self.agent)
        self.assertEqual(result[1]['_transactions'], [])
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1))
        self.assertEqual(len(result[1]['positions'][0]['enters']), 1)
        self.assertEqual(result[1]['positions'][0]['exits'], [])
        self.assertEqual(result[1]['positions'][0]['qty'], 10000)
        self.assertEqual(result[1]['positions'][0]['asset'], 'USD')
        self.assertEqual(result[1]['assets'], {"USD": 10000})
        self.assertEqual(result[1]['taxable_events'], [])

class HasAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent = (await self.exchange.register_agent("agent9", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_has_asset(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent)
        result = await self.exchange.agent_has_assets(self.agent, "BTC", 2)
        self.assertEqual(result, True)

class HasCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent = (await self.exchange.register_agent("agent10", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_has_cash(self):
        result = await self.exchange.agent_has_cash(self.agent, 10000, 1)
        self.assertEqual(result, True)

class GetOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent11", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])

    async def test_get_order(self):
        order = await self.exchange.limit_buy("BTC" , "USD", price=150, qty=2, creator=self.agent, fee=0)
        result = await self.exchange.get_order(order.ticker, order.id)
        self.assertEqual(result.id, order.id)

class getTransactionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent12", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])

    async def test_get_transactions(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()        
        result = await self.exchange.get_transactions(self.agent)
        self.assertEqual(len(result['transactions']), 1)
        self.assertEqual(result['transactions'][0]['quote_flow'], -303.0)
        self.assertEqual(result['transactions'][0]['base'], 'BTC')
        self.assertEqual(result['transactions'][0]['qty'], 2)
        self.assertEqual(result['transactions'][0]['type'], 'buy')

class getAgentsCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent13", initial_assets={"BTC": 2, "USD" : 10000}))['registered_agent']
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])

    async def test_get_agents_cash(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent, fee=0.15)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        result = await self.exchange.agents_cash()
        self.assertEqual(result[1][self.agent]['cash'], Decimal('9696.846'))

class totalCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent14", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_total_cash(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent, fee=0.0004)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()          
        result = await self.exchange.total_cash()
        self.assertEqual(result, Decimal('9696.9956'))

class getPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent22", initial_assets={"USD" : 10000}))['registered_agent']

    async def test_get_positions(self):
        await self.exchange.limit_buy("BTC" , "USD", price=152, qty=2, creator=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()   
        result = await self.exchange.get_positions(self.agent)
        self.assertEqual(result['agent'], self.agent)
        self.assertEqual(result['total_positions'] , 2)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['total_pages'], 1)
        self.assertEqual(result['next_page'], None)
        self.assertEqual(result['page_size'], 10)
        self.assertEqual(len(result['positions']), 2)
        self.assertEqual(result['positions'][1]['asset'], 'BTC')
        self.assertEqual(result['positions'][1]['qty'], 2)
        self.assertEqual(result['positions'][1]['dt'], datetime(2023, 1, 1, 0, 0))

class getTaxableEventsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent23", initial_assets={ "USD" : 10000}))['registered_agent']
        self.agent_high_buyer = (await self.exchange.register_agent("agent_high_buyer", initial_assets={ "USD" : 10_000_000}))['registered_agent']

    async def test_get_taxable_events(self):
        initial_buy = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent_index(self.agent)
        buyup = await self.exchange.limit_buy("BTC" , "USD", price=155, qty=9997, creator=self.agent_high_buyer, fee=0.01)

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()  

        high_buy = await self.exchange.limit_buy("BTC" , "USD", price=300, qty=2, creator=self.agent_high_buyer, fee=0.01)
        high_sell = await self.exchange.market_sell("BTC", "USD", qty=2, seller=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()   
        agent = await self.exchange.get_agent_index(self.agent)
        result = await self.exchange.get_taxable_events(self.agent)
        self.assertEqual(result[0]['agent'], self.agent)
        self.assertEqual(len(result[0]['taxable_events']), 1)
        self.assertEqual(result[0]['taxable_events'][0]['enter_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['exit_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['pnl'], Decimal('297.00'))
        self.assertEqual(result[0]['taxable_events'][0]['type'], 'capital_gains')

    async def test_get_taxable_events_all(self):
        initial_buy = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        print(initial_buy)
        agent = await self.exchange.get_agent_index(self.agent)
        buyup = await self.exchange.limit_buy("BTC" , "USD", price=155, qty=9997, creator=self.agent_high_buyer, fee=0.01)

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()  

        high_buy = await self.exchange.limit_buy("BTC" , "USD", price=300, qty=2, creator=self.agent_high_buyer, fee=0.01)
        high_sell = await self.exchange.market_sell("BTC", "USD", qty=2, seller=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()
        print(high_sell)   
        result = await self.exchange.get_taxable_events()
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]['agent'], self.agent)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['taxable_events'][0]['enter_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['exit_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['pnl'], Decimal('297.00'))
        self.assertEqual(result[0]['taxable_events'][0]['type'], 'capital_gains')        

    async def test_basis_chaining(self):
        """
        tests whether basis is chained correctly when there are multiple currencies traded
        """
        await self.exchange.create_asset("ETH", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}, {'asset': 'BTC','market_qty':1000 ,'seed_price':0.5 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True

        initial_buy = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()

        agent = await self.exchange.get_agent_index(self.agent)
        print('initial buy', initial_buy)
        print('assets after initial buy', self.exchange.agents[agent]['assets'])
        print(self.exchange.books['ETHBTC'].bids)
        print(self.exchange.books['ETHBTC'].asks)

        change_asset = await self.exchange.market_buy("ETH", "BTC", qty=3, buyer=self.agent, fee=0.01)
        await self.exchange.next() 
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        print('BTC', len(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions))
        print('ETH', len(self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions))
        await self.exchange.next() 
        print('change asset', change_asset)
        print('assets after change asset', self.exchange.agents[agent]['assets'])
        

        buyup = await self.exchange.limit_buy("ETH" , "USD", price=155, qty=9998, creator=self.agent_high_buyer, fee=0.01)
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()  

        high_buy = await self.exchange.limit_buy("ETH" , "USD", price=300, qty=2, creator=self.agent_high_buyer, fee=0.01)
        high_sell = await self.exchange.market_sell("ETH", "USD", qty=2, seller=self.agent, fee=0.01)
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[4].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[4].confirmed = True
        await self.exchange.next()
       
        print('high buy', high_buy)
        print('high sell', high_sell['market_sell'], high_sell['fills'][0]['qty'], high_sell['fills'][0]['price'])
        print(self.exchange.pending_transactions)

        result = await self.exchange.get_taxable_events()
        self.assertIsInstance(result, list)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['agent'], self.agent)
        self.assertEqual(result[0]['taxable_events'][0]['enter_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['exit_date'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[0]['taxable_events'][0]['pnl'], Decimal('446.98500'))
        self.assertEqual(result[0]['taxable_events'][0]['type'], 'capital_gains')        

class addAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent15", initial_assets={}))['registered_agent']

    async def test_add_asset(self):
        # self.exchange.agents[0]['positions'][0]['exits'].clear()
        result = await self.exchange.add_asset(self.agent, "BTC", 5000)
        agent = await self.exchange.get_agent_index(self.agent)
        print(result)
        self.assertEqual(result, {"BTC" : 5000})
        self.assertEqual(self.exchange.agents[agent]['assets'] , {"BTC": 5000})
        self.assertEqual(self.exchange.agents[agent]['positions'][0]['enters'][0]["qty"], 5000)

class removeAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent15", initial_assets={"BTC": 5000}))['registered_agent']

    async def test_remove_asset(self):
        # self.exchange.agents[0]['positions'][0]['exits'].clear()
        result = await self.exchange.remove_asset(self.agent, "BTC", 2000)
        print(result)
        agent = await self.exchange.get_agent_index(self.agent)
        self.assertEqual(result, {"BTC" : 3000})
        self.assertEqual(self.exchange.agents[agent]['assets'] , {"BTC": 3000})
        self.assertEqual(self.exchange.agents[agent]['positions'][0]['exits'][0]["qty"], 2000)

class addCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent15", initial_assets={}))['registered_agent']

    async def test_add_cash(self):
        # self.exchange.agents[0]['positions'][0]['exits'].clear()
        result = await self.exchange.add_cash(self.agent, 5000)
        print(result)
        agent = await self.exchange.get_agent_index(self.agent)
        self.assertEqual(result, {"USD" : 5000})
        self.assertEqual(self.exchange.agents[agent]['assets'] , {"USD": 5000})
        self.assertEqual(self.exchange.agents[agent]['positions'][0]['enters'][0]["qty"], 5000)

class removeCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent15", initial_assets={"USD": 5000}))['registered_agent']

    async def test_remove_cash(self):
        # self.exchange.agents[0]['positions'][0]['exits'].clear()
        result = await self.exchange.remove_cash(self.agent, 2000)
        print(result)
        agent = await self.exchange.get_agent_index(self.agent)
        self.assertEqual(result, {"USD" : 3000})
        self.assertEqual(self.exchange.agents[agent]['assets'] , {"USD": 3000})
        self.assertEqual(self.exchange.agents[agent]['positions'][0]['exits'][0]["qty"], 2000)

class UpdateAgentsTestCase(unittest.IsolatedAsyncioTestCase):
    #NOTE: This Test has to be run last! It is Leaky! update_agents method is stateful and will insert positions into other tests run after it...
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
    
    async def test_update_agents(self):
        self.exchange.agents.clear()
        self.agent1 = (await self.exchange.register_agent("Agent1", initial_assets={"USD" : 100}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("Agent2", initial_assets={"USD" : 200, "BTC": 1.01}))['registered_agent']
        
        fake_buy_txn = {'agent': self.agent2, 'id': 'fake_enter_id', 'quote_flow': -50, 'price': 50, 'base': 'BTC', 'quote': 'USD', 'initial_qty': 1, 'qty': 1, 'dt': self.exchange.datetime, 'type': 'buy'}
    
        self.exchange.agents[1]['_transactions'].append(fake_buy_txn)

        fake_position = {
            'id':"fake_buy_id",
            'asset': "BTC",
            'price': 50,
            'qty': 1,
            'dt': self.exchange.datetime,
            'enters': [fake_buy_txn],
            'exits': []
        }
        self.exchange.agents[1]['positions'].append(fake_position)
        transaction = [
            {'id': "testbuy",'agent': self.agent1, 'quote_flow': -50, 'price': 50, 'base': 'BTC', 'quote': 'USD', 'initial_qty': 1, 'qty': 1, 'dt': self.exchange.datetime, 'fee': 0.01 ,'type': 'buy'},
            {'id': "testsell",'agent': self.agent2, 'quote_flow': 50,  'price': 50,'base': 'BTC', 'quote': 'USD', 'qty': -1, 'dt': self.exchange.datetime, 'fee': 0.01 ,'type': 'sell'}
        ]

        await self.exchange.freeze_assets(self.agent1, "USD", 50)
        await self.exchange.freeze_assets(self.agent2, "BTC", 1.01)
        
        await self.exchange.update_agents(transaction, "FIFO", "")

        
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 1)
        self.assertEqual(len(self.exchange.agents[1]['_transactions']), 2)
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['quote_flow'], -50)
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['quote_flow'], 50)
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['base'], 'BTC')
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['quote'], 'USD')
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['base'], 'BTC')
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['quote'], 'USD')
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['qty'], 1)
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['qty'], -1)
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['type'], 'buy')
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['type'], 'sell')
        self.assertEqual(self.exchange.agents[0]['_transactions'][0]['dt'], self.exchange.datetime)
        self.assertEqual(self.exchange.agents[1]['_transactions'][1]['dt'], self.exchange.datetime)
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['asset'], self.exchange.agents[0]['_transactions'][0]['base'])
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['dt'], self.exchange.agents[0]['_transactions'][0]['dt'])
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['qty'], self.exchange.agents[0]['_transactions'][0]['qty'])
        self.assertEqual(self.exchange.agents[0]['positions'][1]['enters'][0]['type'], self.exchange.agents[0]['_transactions'][0]['type'])

        self.assertEqual(self.exchange.agents[1]['positions'][0]['enters'][0]['asset'], self.exchange.agents[0]['_transactions'][0]['quote'])
        self.assertEqual(self.exchange.agents[1]['positions'][0]['enters'][1]['asset'], self.exchange.agents[0]['_transactions'][0]['quote'])

        self.assertEqual(self.exchange.agents[1]['positions'][1]['exits'][0]['qty'], 1)
        self.assertEqual(self.exchange.agents[1]['positions'][1]['exits'][0]['asset'], 'BTC')

class getAgentsPositions(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:    
        self.exchange = await standard_asyncSetUp(self)
        self.agent1 = (await self.exchange.register_agent("agent16", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent17", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent18", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_agents_positions_asset(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee=0.001)
        await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee=0.001)
        await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee=0.001)

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True

        await self.exchange.next()

        result = await self.exchange.get_agents_positions('BTC')
        print(result)
        self.assertEqual(result[1]['agent'], self.agent1)
        self.assertEqual(type(result[1]['positions']), list )
        self.assertEqual(result[1]['positions'][0]['asset'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['qty'], 10002)
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['asset'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['enters'][1]['qty'], 2)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['type'], 'buy')
        self.assertEqual(result[1]['positions'][0]['exits'], [])

    async def test_get_agents_positions(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee=0.001)
        await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee=0.001)
        await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee=0.001)

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True

        await self.exchange.next()

        result = await self.exchange.get_agents_positions()
        print(result)
        self.assertEqual(result[1]['agent'], self.agent1)
        self.assertEqual(type(result[1]['positions']), list )
        self.assertEqual(result[1]['positions'][0]['asset'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['qty'], 10002)
        self.assertEqual(result[1]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['asset'], 'BTC')
        self.assertEqual(result[1]['positions'][0]['enters'][1]['qty'], 2)
        self.assertEqual(result[1]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[1]['positions'][0]['enters'][0]['type'], 'buy')
        self.assertEqual(result[1]['positions'][0]['exits'], []) 
        self.assertEqual(result[1]['positions'][1]['asset'], 'USD')
        self.assertEqual(result[1]['positions'][1]['qty'], Decimal('9998'))
        self.assertEqual(result[1]['positions'][1]['dt'], datetime(2023, 1, 1, 0, 0))       

class getAgentsHoldingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent1 = (await self.exchange.register_agent("agent16", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent17", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent18", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_agents_holding(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee=0.001)
        await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee=0.001)
        await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee=0.001)
        
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()

        result = await self.exchange.get_agents_holding("BTC")
        self.assertEqual(result, ['init_seed_BTCUSD', self.agent1, self.agent2, self.agent3 ])

class getSharesOutstandingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agentoutstand", initial_assets={"USD": 200000}))['registered_agent']
        outstander = await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent, fee=0.001)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        print(outstander)

    async def test_get_outstanding_shares(self):
        result = await self.exchange.get_outstanding_shares("BTC")
        self.assertEqual(result, Decimal('997.999999999')) #NOTE this will not be 1000 because of fees and shares still locked in the order book
        print(self.exchange.books['BTCUSD'].asks)
        print(self.exchange.books['BTCUSD'].bids)

