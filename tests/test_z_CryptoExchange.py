import unittest
from decimal import Decimal, getcontext
from datetime import datetime
import sys, os, random
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils.logger import Null_Logger
from source.utils._utils import prec
from source.exchange.CryptoExchange import CryptoExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from .MockRequesterCrypto import MockRequesterCrypto as MockRequester

async def standard_asyncSetUp(self):
    self.mock_requester = MockRequester()
    self.requests = Requests(self.mock_requester)
    self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
    self.exchange.logger = Null_Logger(debug_print=True)
    await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
    await self.exchange.next()
    return self.exchange      

class CreateAssetTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)

    async def test_create_asset(self):
        asset = await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.assertEqual("BTC" in self.exchange.assets, True )
        self.assertEqual(self.exchange.assets['BTC']['type'], "crypto")
        book = self.exchange.books["BTCUSD"]
        self.assertEqual(book.bids[0].price, Decimal('99.0'))
        self.assertEqual(book.asks[0].price, 101)

    async def test_create_asset_pairs(self):
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        asset = await self.exchange.create_asset("ETH", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}, {'asset': 'BTC','market_qty':1000 ,'seed_price':'0.5' ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        print(asset)
        self.assertEqual("ETH" in self.exchange.assets, True )
        self.assertEqual(self.exchange.assets['ETH']['type'], "crypto")
        book = self.exchange.books["ETHUSD"]
        self.assertEqual(book.bids[0].price, Decimal('148.50'))
        self.assertEqual(book.asks[0].price, Decimal('151.50'))
        book = self.exchange.books["ETHBTC"]
        self.assertEqual(book.bids[0].price, Decimal('0.495'))
        self.assertEqual(book.asks[0].price, Decimal('0.505'))

    async def test_create_duplicate_asset(self):
        asset = await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}])      
        asset = await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.assertEqual(asset, {"error": "asset BTC already exists"})

    async def test_create_max_asset(self):
        self.exchange.max_assets = 1
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}])        
        asset = await self.exchange.create_asset("LTC", pairs=[{'asset': 'USD','market_qty':50000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}])      
        self.assertEqual(asset, {'error': 'cannot create, max_assets_reached'})                   

class FreezeAssetsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_freeze_asset(self):
        await self.exchange.freeze_assets(self.agent, "BTC", "test_order", 100, Decimal('0.01'), Decimal('0.01'))
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['order_id'],"test_order" )
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_qty'],100)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_exchange_fee'], Decimal('0.01'))
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_network_fee'], Decimal('0.01'))

    async def test_freeze_no_asset(self):
        freeze = await self.exchange.freeze_assets(self.agent, "ETH", "test_order", 100, Decimal('0.01'), Decimal('0.01'))
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(freeze, {'error': f'no asset ETH available to freeze'})
        self.assertEqual(agent['frozen_assets'], {})

    async def test_freeze_insufficient_assets(self):
        freeze = await self.exchange.freeze_assets(self.agent, "BTC", "test_order", 100000, Decimal('0.01'), Decimal('0.01'))
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(freeze, {'error': 'insufficient funds available to freeze'})
        self.assertEqual(agent['frozen_assets'], {})   

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
        self.assertEqual(quotes["ask_qty"], Decimal('1000')) # this is not 1000 because it has accounted for fees
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
        result = (await self.exchange.register_agent("agent1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.assertEqual(result[:6], "agent1")
        self.assertEqual(len(self.exchange.agents), 2)
        self.assertEqual(self.exchange.agents[1]['name'], result)
        self.assertEqual(self.exchange.agents[1]['assets'], {"BTC": 10000, "USD" : 10000})
        self.assertEqual(len(self.exchange.agents[0]['_transactions']), 0)

    async def test_register_agent_error(self):
        self.exchange.max_agents = 1
        await self.exchange.register_agent("agent1", initial_assets={"BTC": 10000, "USD" : 10000})
        agent = await self.exchange.register_agent("agent2", initial_assets={"BTC": 10000, "USD" : 10000})
        self.assertEqual(agent, {"error": "max agents reached"})        
        
class GetBestAskTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_best_ask(self):
        best_ask = await self.exchange.get_best_ask("BTCUSD")
        self.assertEqual(best_ask.price, 151.5)
        self.assertEqual(best_ask.qty, Decimal('1000'))

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

    async def test_limit_buy_zero_price(self):
        result = await self.exchange.limit_buy('BTC', 'USD', 0, 100, self.buyer, fee='1')
        self.assertEqual(result.creator, self.buyer)
        self.assertEqual(result.accounting, 'price_must_be_greater_than_zero')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['BTCUSD'].bids), 1)

    async def test_limit_buy_zero_qty(self):
        result = await self.exchange.limit_buy('BTC', 'USD', 148, 0, self.buyer, fee='1')
        self.assertEqual(result.creator, self.buyer)
        self.assertEqual(result.accounting, 'qty_must_be_greater_than_zero')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['BTCUSD'].bids), 1)

    async def test_limit_buy_max_bids(self):
        self.exchange.max_bids = 1
        maxed_order = await self.exchange.limit_buy("BTC", "USD", price=152, qty=2, creator=self.buyer, fee='0.01')
        print(type(maxed_order.status))
        self.assertEqual(maxed_order.status, 'error')
        self.assertEqual(maxed_order.accounting, 'max_bid_depth_reached')    

    async def test_limit_buy_sufficient_funds(self):
        new_order = await self.exchange.limit_buy('BTC', 'USD', 148, 3, self.buyer, fee='0.03')
        print(new_order)
        agent = await self.exchange.get_agent(self.buyer)
        print(agent['frozen_assets'])
        self.assertEqual(len(self.exchange.books['BTCUSD'].bids), 2)
        self.assertEqual(self.exchange.books['BTCUSD'].bids[1].price, 148)
        self.assertEqual(self.exchange.books['BTCUSD'].bids[1].qty, 3)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 148)
        self.assertEqual(new_order.qty, 3)
        self.assertEqual(new_order.creator, self.buyer)
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],new_order.qty * new_order.price)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], new_order.exchange_fee)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], new_order.network_fee)
        
    async def test_limit_buy_insufficient_funds(self):
        result = await self.exchange.limit_buy('BTC', 'USD', 220, 3, self.insufficient_agent, fee='0.03')

        self.assertEqual(result.creator, self.insufficient_agent)
        self.assertEqual(result.accounting, 'insufficient_assets')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['BTCUSD'].bids), 1)

class LimitSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.insufficient_seller = (await self.exchange.register_agent("insufficient_seller", initial_assets={"USD" : 10000}))['registered_agent']
        self.agent = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_limit_sell_zero_price(self):
        result = await self.exchange.limit_sell('BTC', 'USD', 0, 100, self.agent, fee='0.01')
        self.assertEqual(result.creator, self.agent)
        self.assertEqual(result.accounting, 'price_must_be_greater_than_zero')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['BTCUSD'].asks), 1)

    async def test_limit_sell_zero_qty(self):
        result = await self.exchange.limit_sell('BTC', 'USD', 148, 0, self.agent, fee='0.01')
        self.assertEqual(result.creator, self.agent)
        self.assertEqual(result.accounting, 'qty_must_be_greater_than_zero')
        self.assertEqual(result.status, 'error')
        self.assertEqual(len(self.exchange.books['BTCUSD'].asks), 1)

    async def test_limit_sell_max_bids(self):
        self.exchange.max_asks = 1
        await self.exchange.limit_buy("BTC" , "USD", price=152, qty=4, creator=self.agent)
        maxed_order = await self.exchange.limit_sell('BTC', "USD", 180, 4,self.agent , fee='0.01')
        print(type(maxed_order.status))
        self.assertEqual(maxed_order.status, 'error')
        self.assertEqual(maxed_order.accounting, 'max_ask_depth_reached')

    async def test_limit_sell_sufficient_assets(self):
        new_order = await self.exchange.limit_sell('BTC', "USD", 180, 4,self.agent , fee='0.01')
        agent = await self.exchange.get_agent(self.agent)
        print(agent['frozen_assets'])
        self.assertEqual(len(self.exchange.books['BTCUSD'].asks), 2)
        self.assertEqual(self.exchange.books['BTCUSD'].asks[1].price, 180)
        self.assertEqual(self.exchange.books['BTCUSD'].asks[1].qty, 4)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 180)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.agent)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_qty'],new_order.qty)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_exchange_fee'], new_order.exchange_fee)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_network_fee'], new_order.network_fee)

    async def test_limit_sell_insufficient_assets(self):
        # self.exchange.agent_has_assets = MagicMock(return_value=False)

        result = await self.exchange.limit_sell('BTC', 'USD', 180, 4, self.insufficient_seller, fee='0.01')

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
        new_sell = await self.exchange.limit_sell("BTC", "USD", price=145, qty=5, creator=self.seller, fee='0.001')
        new_order = await self.exchange.limit_buy('BTC', 'USD', 145, 4, self.match_buyer, fee='0.04')

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()

        agent = await self.exchange.get_agent(self.match_buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        print(agent['frozen_assets'])
        print(agent_seller['frozen_assets'])
        # check that assets are unfrozen 
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 145)
        self.assertEqual(new_order.qty, 4)
        self.assertEqual(new_order.creator, self.match_buyer)
        trade_payment_USD = prec(new_order.fills[0]['qty'] * new_order.fills[0]['price'] + new_order.fills[0]['fee'] + self.exchange.trade_log[2].network_fee['quote'])
        self.assertEqual(agent['assets'], {'BTC': Decimal('10004.000000000000000000'), 'USD': prec(10000 - trade_payment_USD)})
        trade_BTC_earned = new_order.fills[0]['qty'] + self.exchange.trade_log[1].qty + self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[1].exchange_fee['base'] + self.exchange.trade_log[2].network_fee['base'] + self.exchange.trade_log[2].exchange_fee['base']
        self.assertEqual(agent_seller['assets'], {'BTC': 10000 - trade_BTC_earned, 'USD': 10000 + new_order.fills[0]['qty'] * new_order.fills[0]['price'] + self.exchange.trade_log[1].price})
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'],0 )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],new_sell.id )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], 0)

        #NOTE: except for the network fees, all the funds in the above trade should still be in the exchange, just in different accounts
        BTC_in_trade = self.exchange.trade_log[1].qty + self.exchange.fees.fees_collected['BTC'] + agent['assets']['BTC'] + agent_seller['assets']['BTC'] + agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee']
        USD_in_trade = self.exchange.fees.fees_collected['USD'] + agent['assets']['USD'] + agent_seller['assets']['USD'] 
        BTC_network_fees = self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[2].network_fee['base']
        USD_network_fees = self.exchange.trade_log[2].network_fee['quote'] #NOTE: do not include the network fee from the init_seed bid because the init_seed pays the network fee
        USD_from_init = self.exchange.trade_log[1].qty*self.exchange.trade_log[1].price + self.exchange.trade_log[1].exchange_fee['quote'] #NOTE: we have to include this because the seller receives monies from the init_seed bid
        self.assertEqual(BTC_in_trade, Decimal('20000') - BTC_network_fees)
        self.assertEqual(USD_in_trade, Decimal('20000') - USD_network_fees+USD_from_init)

    async def test_limit_matching_add_fails(self):
        async def add_transaction(asset, fee, amount, sender, recipient): return {"error": "messaging error, blockchain unreachable"}
        self.requests.add_transaction = add_transaction

        sell_order = await self.exchange.limit_sell("BTC", "USD", price=145, qty=5, creator=self.seller, fee='0.001')
        new_order = await self.exchange.limit_buy('BTC', 'USD', 145, 4, self.match_buyer, fee='0.04')

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
        self.assertEqual(len(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions), 0)
        self.assertEqual(len(self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions), 0)
        # NOTE: normally the sell order would process, at least partially, as a taker order, in this case it cannot process at all so it becomes a maker order
        self.assertEqual(len(books.bids), 2)
        self.assertEqual(len(books.asks), 2)
        trade_USD_inBook = prec(books.bids[1].qty * books.bids[1].price + books.bids[1].exchange_fee + books.bids[1].network_fee,2)
        self.assertEqual(agent['assets'], {'BTC': Decimal('10000'), 'USD': 10000 - trade_USD_inBook}) 
        trade_BTC_inBook = books.asks[0].qty + books.asks[0].exchange_fee + books.asks[0].network_fee
        self.assertEqual(agent_seller['assets'], {"BTC": 10000-trade_BTC_inBook, "USD": 10000}) 
        #NOTE: assets will stay frozen for maker orders 
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],new_order.qty * new_order.price)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], new_order.exchange_fee)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], new_order.network_fee)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],sell_order.id )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],sell_order.qty)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], sell_order.exchange_fee)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], sell_order.network_fee)
        # assert that the assets frozen total + remaining assert are equal to 10000
        total_seller_assets = agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'] + agent_seller['assets']['BTC']
        total_buyer_assets = agent['frozen_assets']['USD'][0]['frozen_qty'] + agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] + agent['frozen_assets']['USD'][0]['frozen_network_fee'] + agent['assets']['USD']
        self.assertEqual(total_seller_assets, 10000)
        self.assertEqual(total_buyer_assets, 10000)
        self.assertTrue('BTC' not in self.exchange.fees.fees_collected)
        self.assertTrue('USD' not in self.exchange.fees.fees_collected)

    async def test_limit_matching_get_fails(self):
        async def get_transaction (asset, id): return {"error": "messaging error, blockchain unreachable"}
        self.requests.get_transaction = get_transaction

        initial_sell_qty = 5
        sell_fee = Decimal('0.001')
        buy_fee = Decimal('0.01')
        sell_order = await self.exchange.limit_sell("BTC", "USD", price=145, qty=initial_sell_qty, creator=self.seller, fee=sell_fee)
        new_order = await self.exchange.limit_buy('BTC', 'USD', 150, 4, self.match_buyer, fee=buy_fee)
        books = self.exchange.books['BTCUSD']
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()

        print (self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print (self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        print(books.bids)
        print(books.asks)

        agent = await self.exchange.get_agent(self.match_buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        #NOTE: the transactions all get added to the chain, but now the chain has gone offline or is unreachable
        # we simply have to wait for the chain to come back online and then the transactions will be processed
        self.assertEqual(len(self.exchange.pending_transactions), 2)
        self.assertEqual(len(books.bids), 0) # NOTE: the orders are still going to match even if the transaction cannot be retrieved or confirmed yet
        self.assertEqual(len(books.asks), 1) 
        trade_payment_USD = prec(new_order.fills[0]['qty'] * new_order.fills[0]['price'] + new_order.fills[0]['fee'] + new_order.network_fee, 2) #NOTE: this will be higher because the network fee cannot be deducted since the blockchain is unreachable
        self.assertEqual(agent['assets'], {'BTC': Decimal('10000'), 'USD': Decimal('10000') - trade_payment_USD})
        buffer_fee = Decimal('.00000001')
        trade_BTC_earned = prec(new_order.fills[0]['qty'] + sell_order.fills[0]['qty'] +sell_order.fills[0]['fee'] + sell_order.network_fee + self.exchange.fees.maker_fee(initial_sell_qty - sell_order.fills[0]['qty'])+buffer_fee, 8)
        self.assertEqual(agent_seller['assets'], {'BTC': 10000 - trade_BTC_earned, 'USD': 10000})
        #NOTE: assets will stay frozen for unconfirmed taker orders
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],new_order.fills[0]['qty'] * new_order.fills[0]['price']) #NOTE: the order will get "filled" it just won't be confirmed yet
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], new_order.exchange_fee) #NOTE: because we matched to a "better" trade the difference between placed exchange fee and cheaper exchange fee will be deducted from the frozen assets, so it will be different from the original frozen 
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], new_order.remaining_network_fee) # NOTE: the network fee is still frozen because the transaction did get sent to the chain and was confirmed, it just can't be retrieved yet
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],sell_order.id )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],initial_sell_qty) #NOTE: the sell_order.qty will be 0 because this order was completely filled, have to check the fill, but assets remain frozen until confirmed
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], self.exchange.pending_transactions[0]['exchange_txn'][1]['fee'] + self.exchange.pending_transactions[1]['exchange_txn'][1]['fee']+buffer_fee)  #NOTE: assets are still frozen for pending sell transactions
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], sell_order.remaining_network_fee) #NOTE: the network fee is still frozen because the transaction did get sent to the chain and was confirmed, it just can't be retrieved yet
        # assert that the assets frozen total + remaining assert are equal to 10000
        total_seller_assets = agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'] + agent_seller['assets']['BTC']
        total_buyer_assets = agent['frozen_assets']['USD'][0]['frozen_qty'] + agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] + agent['frozen_assets']['USD'][0]['frozen_network_fee'] + agent['assets']['USD']
        #NOTE: neither below is 10000 because we paid out fees
        self.assertEqual(total_seller_assets, Decimal('10000') - (sell_order.network_fee-sell_order.remaining_network_fee)) 
        self.assertEqual(total_buyer_assets, 10000 - (new_order.network_fee - new_order.remaining_network_fee)) 

    async def test_limit_sell_partial_match(self):
        # half of the order gets filled, the other half becomes a maker order
        sell_qty = 10
        sell_fee = Decimal('0.001')
        sell_order = await self.exchange.limit_sell("BTC", "USD", price=145, qty=sell_qty, creator=self.seller, fee=sell_fee)
        print(sell_order.fills)
        new_order = await self.exchange.limit_buy('BTC', "USD", 152, 5, self.buyer, fee='0.01')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 152)
        self.assertEqual(new_order.qty, 5)
        self.assertEqual(new_order.creator, self.buyer)

        trade_payment_USD = prec(new_order.fills[0]['qty'] * new_order.fills[0]['price'] + new_order.fills[0]['fee'] + self.exchange.trade_log[2].network_fee['quote'], 2)
        self.assertEqual(agent['assets'], {
            'BTC': Decimal('10005'), 
            'USD': Decimal('10000') - trade_payment_USD
        })

        trade_BTC_earned = self.exchange.trade_log[1].qty +self.exchange.trade_log[2].qty + self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[1].exchange_fee['base'] + self.exchange.trade_log[2].network_fee['base'] + self.exchange.trade_log[2].exchange_fee['base']
        self.assertEqual(agent_seller['assets'], {
            'BTC': 10000 - trade_BTC_earned - agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] - agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] - agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], 
            'USD': 10000 + new_order.fills[0]['qty'] * new_order.fills[0]['price'] + self.exchange.trade_log[1].price
        })
        
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],sell_order.id )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],sell_order.qty)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], self.exchange.books['BTCUSD'].asks[0].exchange_fee-self.exchange.books['BTCUSD'].asks[0].exchange_fees_due)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], sell_order.remaining_network_fee) #NOTE: we add 1 because the sell order fills the init_seed bid
        #NOTE: except for the network fees, all the funds in the above trade should still be in the exchange, just in different accounts
        BTC_in_trade = self.exchange.trade_log[1].qty + self.exchange.fees.fees_collected['BTC'] + agent['assets']['BTC'] + agent_seller['assets']['BTC'] + agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee']
        USD_in_trade = self.exchange.fees.fees_collected['USD'] + agent['assets']['USD'] + agent_seller['assets']['USD'] 
        BTC_network_fees = self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[2].network_fee['base']
        USD_network_fees = self.exchange.trade_log[2].network_fee['quote'] #NOTE: do not include the network fee from the init_seed bid because the init_seed pays the network fee
        USD_from_init = self.exchange.trade_log[1].qty*self.exchange.trade_log[1].price + self.exchange.trade_log[1].exchange_fee['quote'] #NOTE: we have to include this because the seller receives monies from the init_seed bid
        self.assertEqual(BTC_in_trade, Decimal('20000') - BTC_network_fees)
        self.assertEqual(USD_in_trade, Decimal('20000') - USD_network_fees+USD_from_init)

    async def test_limit_buy_partial_match(self):
        # half of the order gets filled, the other half becomes a maker order
        buy_qty = 10
        buy_fee = Decimal('0.01')
        sell_fee = Decimal('0.001')
        buy_order = await self.exchange.limit_buy("BTC", "USD", price=130, qty=buy_qty, creator=self.buyer, fee=buy_fee)
        new_order = await self.exchange.limit_sell('BTC', "USD",130, 5, self.seller, fee=sell_fee)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.buyer)
        seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 130)
        self.assertEqual(new_order.qty, 5) 
        self.assertEqual(new_order.creator, self.seller)
        self.assertEqual(buy_order.ticker, 'BTCUSD')
        self.assertEqual(buy_order.price, 130)
        self.assertEqual(buy_order.qty, 6) 
        self.assertEqual(buy_order.creator, self.buyer)

        trade_payment_USD = self.exchange.trade_log[2].qty * self.exchange.trade_log[2].price + self.exchange.trade_log[2].network_fee['quote'] + self.exchange.trade_log[2].exchange_fee['quote']
        self.assertEqual(agent['assets'], {
            'BTC': Decimal('10004'), 
            'USD': Decimal('10000') - trade_payment_USD - agent['frozen_assets']['USD'][0]['frozen_qty'] - agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] - agent['frozen_assets']['USD'][0]['frozen_network_fee']
        })

        #NOTE: BTC going to be 10004 because 1 is sold to the init_seed bid
        trade_BTC_earned = new_order.fills[0]['qty'] + new_order.fills[0]['fee'] + new_order.fills[1]['qty'] + new_order.fills[1]['fee'] + self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[2].network_fee['base']
        self.assertEqual(seller['assets'], {
            'BTC': 10000 - trade_BTC_earned, 
            'USD': 10000 + new_order.fills[0]['qty'] * new_order.fills[0]['price'] + new_order.fills[1]['qty'] * new_order.fills[1]['price']
        })
        self.assertEqual(seller['frozen_assets']['BTC'][0]['order_id'],new_order.id )
        self.assertEqual(seller['frozen_assets']['BTC'][0]['frozen_qty'],0)
        self.assertEqual(seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(seller['frozen_assets']['BTC'][0]['frozen_network_fee'], 0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],buy_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],buy_qty*buy_order.price - new_order.fills[1]['qty'] * new_order.fills[1]['price'] )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], self.exchange.books['BTCUSD'].bids[0].exchange_fee)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], buy_order.remaining_network_fee)
        self.assertEqual(self.exchange.trade_log[2].network_fee['base'], sell_fee)
        self.assertEqual(self.exchange.fees.fees_collected['BTC'], self.exchange.trade_log[1].exchange_fee['base'] + self.exchange.trade_log[2].exchange_fee['base'])   
        self.assertEqual(self.exchange.fees.fees_collected['USD'], self.exchange.trade_log[1].exchange_fee['quote'] + self.exchange.trade_log[2].exchange_fee['quote'])   
        #NOTE: except for the network fees, all the funds in the above trade should still be in the exchange, just in different accounts
        USD_in_trade =  + self.exchange.fees.fees_collected['USD'] + agent['assets']['USD'] + seller['assets']['USD'] + agent['frozen_assets']['USD'][0]['frozen_qty'] + agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] + agent['frozen_assets']['USD'][0]['frozen_network_fee']
        BTC_in_trade = self.exchange.trade_log[1].qty + self.exchange.fees.fees_collected['BTC'] + agent['assets']['BTC'] + seller['assets']['BTC'] 
        BTC_network_fees = self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[2].network_fee['base']
        USD_network_fees = self.exchange.trade_log[2].network_fee['quote'] #NOTE: do not include the network fee from the init_seed bid because the init_seed pays the network fee
        USD_from_init = self.exchange.trade_log[1].qty*self.exchange.trade_log[1].price + self.exchange.trade_log[1].exchange_fee['quote'] #NOTE: we have to include this because the seller receives monies from the init_seed bid
        self.assertEqual(BTC_in_trade, Decimal('20000') - BTC_network_fees)
        self.assertEqual(USD_in_trade, Decimal('20000') - USD_network_fees+USD_from_init)

class LimitOrderMarketMakingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.buyer = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.seller = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.match_buyer = (await self.exchange.register_agent("match_buyer", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']      
      
    async def test_market_make_complete(self):
        sell_qty = 11
        sell_fee = Decimal('0.00100001')
        sell_order = await self.exchange.limit_sell("BTC", "USD", price=145, qty=sell_qty, creator=self.seller, fee=sell_fee)
        print(sell_order.fills)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        new_order = await self.exchange.limit_buy('BTC', "USD", 152, 5, self.buyer, fee='0.05')
        complete_order = await self.exchange.limit_buy('BTC', "USD", 152, 5, self.buyer, fee='0.05')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()        
        agent = await self.exchange.get_agent(self.buyer)
        agent_seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(new_order.ticker, 'BTCUSD')
        self.assertEqual(new_order.price, 152)
        self.assertEqual(new_order.qty, 5)
        self.assertEqual(new_order.creator, self.buyer)

        new_order_payment_USD = new_order.fills[0]['qty'] * new_order.fills[0]['price'] + new_order.fills[0]['fee'] + self.exchange.trade_log[2].network_fee['quote']
        complete_order_payment_USD = complete_order.fills[0]['qty'] * complete_order.fills[0]['price'] + complete_order.fills[0]['fee'] + self.exchange.trade_log[3].network_fee['quote']
        self.assertEqual(agent['assets'], {
            'BTC': Decimal('10010'), 
            'USD': Decimal('10000') - new_order_payment_USD - complete_order_payment_USD
        })

        new_order_BTC_earned = self.exchange.trade_log[1].qty +self.exchange.trade_log[2].qty + self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[1].exchange_fee['base'] + self.exchange.trade_log[2].network_fee['base'] + self.exchange.trade_log[2].exchange_fee['base']
        complete_order_BTC_earned = self.exchange.trade_log[3].qty + self.exchange.trade_log[3].network_fee['base'] + self.exchange.trade_log[3].exchange_fee['base']
        self.assertEqual(agent_seller['assets'], {
            'BTC': 10000 - new_order_BTC_earned - complete_order_BTC_earned, 
            'USD': 10000 + (new_order.fills[0]['qty'] * new_order.fills[0]['price'] + self.exchange.trade_log[1].price) + (complete_order.fills[0]['qty'] * complete_order.fills[0]['price'])
        })
        
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order.id )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],sell_order.id )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], 0) #NOTE: we add 1 because the sell order fills the init_seed bid
        #NOTE: except for the network fees, all the funds in the above trade should still be in the exchange, just in different accounts
        BTC_in_trade = self.exchange.trade_log[1].qty + self.exchange.fees.fees_collected['BTC'] + agent['assets']['BTC'] + agent_seller['assets']['BTC'] + agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee']
        USD_in_trade = self.exchange.fees.fees_collected['USD'] + agent['assets']['USD'] + agent_seller['assets']['USD'] 
        BTC_network_fees = self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[2].network_fee['base'] + self.exchange.trade_log[3].network_fee['base']
        USD_network_fees = self.exchange.trade_log[2].network_fee['quote'] + self.exchange.trade_log[3].network_fee['quote'] #NOTE: do not include the network fee from the init_seed bid because the init_seed pays the network fee
        USD_from_init = self.exchange.trade_log[1].qty*self.exchange.trade_log[1].price + self.exchange.trade_log[1].exchange_fee['quote'] #NOTE: we have to include this because the seller receives monies from the init_seed bid
        self.assertEqual(BTC_in_trade, Decimal('20000') - BTC_network_fees)
        self.assertEqual(USD_in_trade, Decimal('20000') - USD_network_fees+USD_from_init) 

class MarketBuyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.insufficient_buyer = (await self.exchange.register_agent("insufficient_buyer", initial_assets={"USD": 1}))['registered_agent']
        self.agent = (await self.exchange.register_agent("buyer1", initial_assets={"USD" : 500000}))['registered_agent']

    async def test_market_buy_zero_qty(self):
        result = await self.exchange.market_buy("BTC", "USD", qty=0, buyer=self.agent, fee='0.01')
        self.assertEqual(result, {'market_buy': 'qty_must_be_greater_than_zero', 'buyer': self.agent})

    async def test_market_buy_max_pending(self):
        self.exchange.max_pending_transactions = 0
        maxed_order = await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent, fee='0.01')
        self.assertEqual(maxed_order, {'market_buy': 'max_pending_transactions_reached', 'buyer': self.agent})

    async def test_market_buy(self):
        result = await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent, fee='0.04')
        print(result)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        agent = await self.exchange.get_agent(self.agent)
        await self.exchange.next()
        print(agent['frozen_assets'])
        self.assertEqual(result['market_buy'], 'BTCUSD')
        self.assertEqual(result['buyer'], self.agent)
        self.assertEqual(result['qty'], 4)
        self.assertEqual(result['fills'], [{'qty': 4, 'price': Decimal('151.5'), 'fee': Decimal('1.22')}])
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)
        self.assertEqual(self.exchange.books["BTCUSD"].asks[0].qty, Decimal('996'))
        self.assertEqual(agent['assets'], {'BTC': Decimal('4'), 'USD': Decimal('499392.74')})
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],result['id'] )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'],0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], 0)             

    async def test_insufficient_funds(self):
        result = await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.insufficient_buyer, fee='0.01')
        agent = await self.exchange.get_agent(self.insufficient_buyer)
        self.assertEqual(result, {"market_buy": "initial_freeze_error", "id":result['id'], "buyer": self.insufficient_buyer})
        self.assertEqual(agent['assets'], {'USD': 1}  )
        self.assertEqual('USD' not in agent['frozen_assets'], True )
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)

    async def test_no_fills(self):
        book = self.exchange.books["BTCUSD"]
        for bid in book.bids:
            buyup = await self.exchange.market_buy("BTC", "USD", qty=bid.qty, buyer=self.agent, fee='.01')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.exchange.books["BTCUSD"].asks.clear()
        agent = await self.exchange.get_agent(self.agent)
        result = await self.exchange.market_buy("BTC","USD", qty=3, buyer=self.agent, fee='0.03')
        self.assertEqual(result['market_buy'],  "no fills")
        self.assertEqual(agent['frozen_assets']['USD'][1]['order_id'],result['id'] )
        self.assertEqual(agent['frozen_assets']['USD'][1]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['USD'][1]['frozen_exchange_fee'],0)
        self.assertEqual(agent['frozen_assets']['USD'][1]['frozen_network_fee'], 0)   

class MarketSellTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.no_asset_seller = (await self.exchange.register_agent("no_asset_seller", initial_assets={}))['registered_agent']
        self.insufficient_seller = (await self.exchange.register_agent("insufficient_seller", initial_assets={"BTC": 1}))['registered_agent']
        self.seller1 = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 500000}))['registered_agent']
        self.buyer1 = (await self.exchange.register_agent("buyer1", initial_assets={"USD":500000}))['registered_agent']

    async def test_market_sell_zero_qty(self):
        result = await self.exchange.market_sell("BTC", "USD", qty=0, seller=self.seller1, fee='0.01')
        self.assertEqual(result, {'market_sell': 'qty_must_be_greater_than_zero', 'seller': self.seller1})

    async def test_market_sell_max_pending(self):
        self.exchange.max_pending_transactions = 0
        maxed_order = await self.exchange.market_sell("BTC", "USD", qty=4, seller=self.seller1, fee='0.01')
        self.assertEqual(maxed_order, {'market_sell': 'max_pending_transactions_reached', 'seller': self.seller1})

    async def test_market_sell(self):
        buy = await self.exchange.limit_buy("BTC" , "USD", price=145, qty=3, creator=self.buyer1, fee='0.03')
        # print(buy.to_dict_full())
        books = self.exchange.books["BTCUSD"]
        # print(books.bids)
        result = await self.exchange.market_sell("BTC","USD", qty=3, seller=self.seller1, fee='0.02000001')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()

        print(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print(self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        agent = await self.exchange.get_agent(self.seller1)
        buyer_agent = await self.exchange.get_agent(self.buyer1)

        self.assertEqual(result['market_sell'], 'BTCUSD')
        self.assertEqual(result['seller'], self.seller1)
        self.assertEqual(result['qty'], Decimal(str(3))) 
        self.assertEqual(result['fills'], [
            {'qty': Decimal('1'), 'price': Decimal('148.5'), 'fee': Decimal('0.002')}, 
            {'qty': Decimal('2'), 'price': Decimal('145'), 'fee': Decimal('0.004') }
        ])
        USD_from_trade = prec(self.exchange.trade_log[1].qty*self.exchange.trade_log[1].price + self.exchange.trade_log[2].qty*self.exchange.trade_log[2].price)
        BTC_sold = prec(self.exchange.trade_log[1].qty + self.exchange.trade_log[2].qty + self.exchange.trade_log[1].exchange_fee['base'] + self.exchange.trade_log[2].exchange_fee['base'] + self.exchange.trade_log[1].network_fee['base'] + self.exchange.trade_log[2].network_fee['base'])
        self.assertEqual(agent['assets'], {"BTC": 500000-BTC_sold, "USD": USD_from_trade})
        USD_To_Buy = prec(self.exchange.trade_log[2].qty*self.exchange.trade_log[2].price + self.exchange.trade_log[2].exchange_fee['quote'] + self.exchange.trade_log[2].network_fee['quote'])
        USD_Buy_Frozen = prec(buyer_agent['frozen_assets']['USD'][0]['frozen_qty'] + buyer_agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] + buyer_agent['frozen_assets']['USD'][0]['frozen_network_fee'])
        self.assertEqual(buyer_agent['assets'], {"BTC": prec('2'), "USD": prec(500000 - USD_To_Buy - USD_Buy_Frozen)}) #NOTE: this will be 2 because the market sell order will match to the init_seed bid
        self.assertEqual(agent['frozen_assets']['BTC'][0]['order_id'],result['id'] )
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_exchange_fee'],0)
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_network_fee'], 0)          
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(self.exchange.books["BTCUSD"].bids[0].qty, 1)
        
    async def test_insufficient_assets(self):
        await self.exchange.market_buy("BTC", "USD", qty=1, buyer=self.insufficient_seller, fee='0.01')
        result = await self.exchange.market_sell("BTC", "USD", qty=3, seller=self.insufficient_seller, fee='0.02000001')

        insufficient_seller = await self.exchange.get_agent(self.insufficient_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets", 'id':result['id'], "seller": self.insufficient_seller})
        self.assertEqual(insufficient_seller['assets'], {"BTC": 1} )
        self.assertEqual(insufficient_seller['frozen_assets'], {} )        
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)

    async def test_no_assets(self):
        result = await self.exchange.market_sell("BTC", "USD", qty=3, seller=self.no_asset_seller, fee='0.02000001')

        no_asset_seller = await self.exchange.get_agent(self.no_asset_seller)
        self.assertEqual(result, {"market_sell": "insufficient assets", 'id':result['id'], "seller": self.no_asset_seller})
        self.assertEqual(no_asset_seller['assets'], {} )
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)

    async def test_no_fills(self):
        book = self.exchange.books["BTCUSD"]
        for ask in book.asks:
            await self.exchange.market_buy("BTC", "USD", qty=ask.qty, buyer=self.seller1, fee='0.01')
        
        self.exchange.books["BTCUSD"].bids.clear()
        result = await self.exchange.market_sell("BTC", "USD", qty=3, seller=self.seller1, fee='0.02000001')
        self.assertEqual(result["market_sell"], "no fills")

class MarketMatchingTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.hoarder = (await self.exchange.register_agent("hoarder", initial_assets={"USD": 10_000_000}))['registered_agent']
        self.initial_buyer1_USD = 500000
        self.buyer1 = (await self.exchange.register_agent("buyer1", initial_assets={"USD":self.initial_buyer1_USD }))['registered_agent']
        self.seller = (await self.exchange.register_agent("seller1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']   

    async def test_market_matching_add_fails(self):
        async def add_transaction(asset, fee, amount, sender, recipient): return {"error": "messaging error, blockchain unreachable"}
        self.requests.add_transaction = add_transaction

        buy_order = await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.buyer1, fee='10')
        sell_order = await self.exchange.market_sell("BTC", "USD", qty=1000, seller=self.seller, fee='0.01')
        
        books = self.exchange.books['BTCUSD']
        await self.exchange.next()

        print (self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print (self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        print(books.bids)
        print(books.asks)

        agent = await self.exchange.get_agent(self.buyer1)
        agent_seller = await self.exchange.get_agent(self.seller)
        self.assertEqual(len(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions), 0)
        self.assertEqual(len(self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions), 0)
        # NOTE: normally the sell order would process, at least partially, as a taker order, in this case it cannot process at all so it becomes a maker order
        self.assertEqual(len(books.bids), 1)
        self.assertEqual(len(books.asks), 1)
        self.assertEqual(agent['assets'], {'USD': 500000 }) 
        self.assertEqual(agent_seller['assets'], {"BTC": 10000, "USD": 10000}) 
        #NOTE: assets will stay frozen for maker orders 
        self.assertEqual(buy_order['market_buy'], 'no fills')
        self.assertEqual(sell_order['market_sell'], 'no fills')
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],buy_order['id'] )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],sell_order['id'] )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], 0)
        # assert that the assets frozen total + remaining assert are equal to starting asset amount
        total_seller_assets = agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'] + agent_seller['assets']['BTC']
        total_buyer_assets = agent['frozen_assets']['USD'][0]['frozen_qty'] + agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] + agent['frozen_assets']['USD'][0]['frozen_network_fee'] + agent['assets']['USD']
        self.assertEqual(total_seller_assets, 10000)
        self.assertEqual(total_buyer_assets, 500000)
        self.assertTrue('BTC' not in self.exchange.fees.fees_collected)
        self.assertTrue('USD' not in self.exchange.fees.fees_collected)

    async def test_market_matching_get_fails(self):
        async def get_transaction (asset, id): return {"error": "messaging error, blockchain unreachable"}
        self.requests.get_transaction = get_transaction

        initial_sell_qty = 5
        sell_fee = Decimal('0.001')
        buy_fee = Decimal('0.04')
        sell_order = await self.exchange.market_sell("BTC", "USD", qty=initial_sell_qty, seller=self.seller, fee=sell_fee)
        new_order = await self.exchange.market_buy('BTC', 'USD', 4, buyer=self.buyer1, fee=buy_fee)
        books = self.exchange.books['BTCUSD']
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()

        print (self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions)
        print (self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions)

        print(books.bids)
        print(books.asks)

        agent = await self.exchange.get_agent(self.buyer1)
        agent_seller = await self.exchange.get_agent(self.seller)
        #NOTE: the transactions all get added to the chain, but now the chain has gone offline or is unreachable
        # we simply have to wait for the chain to come back online and then the transactions will be processed
        self.assertEqual(len(self.exchange.pending_transactions), 2)
        self.assertEqual(len(books.bids), 0) # NOTE: the orders are still going to match even if the transaction cannot be retrieved or confirmed yet
        self.assertEqual(len(books.asks), 1) 
        trade_payment_USD = prec(new_order['fills'][0]['qty'] * new_order['fills'][0]['price'] + new_order['fills'][0]['fee'] + new_order['network_fee'], 2)
        self.assertEqual(agent['assets'], {'USD': Decimal('500000') - trade_payment_USD})
        trade_BTC_earned = prec(sell_order['fills'][0]['qty'] +sell_order['fills'][0]['fee']+ sell_order['network_fee'], 8)
        self.assertEqual(agent_seller['assets'], {'BTC': 10000 - trade_BTC_earned, 'USD': 10000})
        #NOTE: assets will stay frozen for unconfirmed taker orders
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'],new_order['id'] )
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'],new_order['fills'][0]['qty'] * new_order['fills'][0]['price']) #NOTE: the order will get "filled" it just won't be confirmed yet
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], new_order['exchange_fee'])
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], new_order['remaining_network_fee']) # NOTE: the network fee is going be 0 because the transaction did get sent to the chain and was confirmed, it just can't be retrieved yet
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['order_id'],sell_order['id'] )
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_qty'],sell_order['fills'][0]['qty'])
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'], self.exchange.pending_transactions[0]['exchange_txn'][1]['fee'])  #NOTE: assets are still frozen for pending sell transactions
        self.assertEqual(agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'], 0) #NOTE: pays the network fee when the transaction is sent, not when it is confirmed
        # assert that the assets frozen total + remaining assert are equal to 10000
        total_seller_assets = agent_seller['frozen_assets']['BTC'][0]['frozen_qty'] + agent_seller['frozen_assets']['BTC'][0]['frozen_exchange_fee'] + agent_seller['frozen_assets']['BTC'][0]['frozen_network_fee'] + agent_seller['assets']['BTC']
        total_buyer_assets = agent['frozen_assets']['USD'][0]['frozen_qty'] + agent['frozen_assets']['USD'][0]['frozen_exchange_fee'] + agent['frozen_assets']['USD'][0]['frozen_network_fee'] + agent['assets']['USD']
        # NOTE: the only assets resolved are the network fees, everything else stays frozen until the transaction is confirmed
        self.assertEqual(total_seller_assets, prec(Decimal('10000') - sell_order['network_fee']), 8) 
        self.assertEqual(total_buyer_assets, prec(500000 - (new_order['network_fee'] - new_order['remaining_network_fee']), 2 ))         

    async def test_market_partial_matching(self):
        """
        the goal here is to see if a market order will partially fill and still resolve: closing the order and unfreezing the assets
        """
        hoard = await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.hoarder, fee='10')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        await self.exchange.limit_sell("BTC", "USD", price=200, qty=1, creator=self.hoarder, fee='0.01')
        market_buy_fee = Decimal('0.02')
        result = await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.buyer1, fee=market_buy_fee)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        print(result)
        print(self.exchange.books["BTCUSD"].bids[0])
        agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(result['market_buy'], 'BTCUSD')
        self.assertEqual(result['buyer'], self.buyer1)
        self.assertEqual(result['qty'], 2)
        self.assertEqual(result['fills'], [{'qty': 1, 'price': Decimal('200'), 'fee': Decimal('0.400000000000000000')}])
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 0)
        network_fee = self.exchange.trade_log[2].network_fee['quote']
        exchange_fee =  result['fills'][0]['fee']
        cash_from_trade = result['fills'][0]['qty'] * result['fills'][0]['price'] + network_fee + exchange_fee
        self.assertEqual(agent['assets'], {"BTC": 1, "USD":self.initial_buyer1_USD - cash_from_trade} )
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'], result['id'])
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], Decimal('0.0'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('0.00'))

    async def test_buy_multi_fill(self):
        hoard = await self.exchange.market_buy("BTC", "USD", qty=999, buyer=self.hoarder, fee='9.99')
        print("hoard order", hoard)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        await self.exchange.limit_sell("BTC", "USD", price=200, qty=1, creator=self.hoarder, fee='0.01')
        market_buy_fee = Decimal('0.02')
        result = await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.buyer1, fee=market_buy_fee)
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True        
        await self.exchange.next()
        print(result)
        print(self.exchange.books["BTCUSD"].bids[0])
        agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(result['market_buy'], 'BTCUSD')
        self.assertEqual(result['buyer'], self.buyer1)
        self.assertEqual(result['qty'], 2)
        self.assertEqual(result['fills'], [
            {'fee': Decimal('0.31'), 'price': Decimal('151.5'), 'qty': Decimal('1')}, 
            {'qty': 1, 'price': Decimal('200'), 'fee': Decimal('0.4')}
        ])
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 0)
        network_fee = self.exchange.trade_log[2].network_fee['quote'] + self.exchange.trade_log[3].network_fee['quote']
        exchange_fee =  result['fills'][0]['fee'] + result['fills'][1]['fee']
        cash_from_trade = result['fills'][0]['qty'] * result['fills'][0]['price'] +result['fills'][1]['qty'] * result['fills'][1]['price']+ network_fee + exchange_fee
        self.assertEqual(agent['assets'], {"BTC": 2, "USD":self.initial_buyer1_USD - cash_from_trade} )
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'], result['id'])
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], Decimal('0.0'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('0.00'))

class FractionalOrdersTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.seller_initial_assets = 201
        self.buyer_initial_assets = 500000
        await self.exchange.create_asset("ETH", decimals=18, pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}, {'asset': 'BTC','market_qty':1000 ,'seed_price':'0.5' ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        await self.exchange.next()        
        self.seller1 = (await self.exchange.register_agent("seller1", initial_assets={"ETH" :self.seller_initial_assets}))['registered_agent']
        self.buyer1 = (await self.exchange.register_agent("buyer1", initial_assets={"BTC":self.buyer_initial_assets}))['registered_agent']
        self.generous = (await self.exchange.register_agent("generous", initial_assets={"BTC":10_000_000}))['registered_agent']

    async def test_fractional_buy(self):
        new_order = await self.exchange.market_buy('ETH', 'BTC', '0.00005', self.buyer1, fee='0.01')
        print(new_order)
        books = self.exchange.books["ETHBTC"]
        print(books.bids)
        print(books.asks)
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.buyer1)
        self.assertEqual(agent['assets'], {"ETH": Decimal('0.00005'), "BTC":Decimal('499999.98997469')} )
        self.assertEqual(agent['frozen_assets']['BTC'][0]['order_id'], new_order['id'])
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_qty'], Decimal('0.00'))
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['BTC'][0]['frozen_network_fee'], Decimal('0.0000'))        

    async def test_fractional_sell(self):
        result = await self.exchange.market_sell("ETH", "BTC", qty='0.00005', seller=self.seller1, fee='0.0000001')
        print(result)
        books = self.exchange.books["ETHBTC"]
        print(books.bids)
        print(books.asks)
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent(self.seller1)
        buyer_agent = await self.exchange.get_agent(self.buyer1)
        ETH_traded = prec(self.exchange.trade_log[3].qty + self.exchange.trade_log[3].exchange_fee['base'] + self.exchange.trade_log[3].network_fee['base'], 18)
        BTC_from_trade = prec(self.exchange.trade_log[3].qty*self.exchange.trade_log[3].price, 8)
        self.assertEqual(agent['assets'],{'ETH':self.seller_initial_assets - ETH_traded, 'BTC': BTC_from_trade} )
        self.assertEqual(agent['frozen_assets']['ETH'][0]['order_id'], result['id'])
        self.assertEqual(agent['frozen_assets']['ETH'][0]['frozen_qty'], Decimal('0.00'))
        self.assertEqual(agent['frozen_assets']['ETH'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['ETH'][0]['frozen_network_fee'], Decimal('0.0000'))

    async def test_fractional_price(self):
        generous = await self.exchange.market_buy("ETH", "BTC", qty=999, buyer=self.generous, fee='.01')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()        
        print(generous)
        sell_generous = await self.exchange.limit_sell("ETH", "BTC", price='0.00005', qty=996, creator=self.generous, fee='.000000000000000001', minimum_qty='0.01234')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()        
        buy_single = await self.exchange.limit_buy("ETH", "BTC", price='0.00015', qty=1, creator=self.buyer1, fee='0.01')
        buy_fraction = await self.exchange.limit_buy("ETH", "BTC", price='0.00015', qty='0.01234', creator=self.buyer1, fee='0.01')

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[3].confirmed = True
        await self.exchange.next()
        books = self.exchange.books["ETHBTC"]
        agent = await self.exchange.get_agent(self.buyer1)
        print('buy single', buy_single.to_dict_full())
        self.assertEqual(books.asks[0].price, Decimal('0.00005'))
        ETH_traded = prec(self.exchange.trade_log[5].qty + self.exchange.trade_log[6].qty, 18)
        BTC_from_trade = prec(self.exchange.trade_log[5].qty*self.exchange.trade_log[5].price + self.exchange.trade_log[5].exchange_fee['quote'] + self.exchange.trade_log[5].network_fee['quote']  + self.exchange.trade_log[6].qty*self.exchange.trade_log[6].price + self.exchange.trade_log[6].exchange_fee['quote'] + self.exchange.trade_log[6].network_fee['quote'], 8)
        self.assertEqual(agent['assets'],{'ETH':ETH_traded, 'BTC': self.buyer_initial_assets - BTC_from_trade} )
        
    async def test_large_fractional_qty(self):
        generous = await self.exchange.market_buy("ETH", "BTC", qty=999, buyer=self.generous, fee='9.99')
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()        
        print(generous)
        market_made= await self.exchange.limit_sell("ETH", "BTC", price='0.00005', qty=996, creator=self.generous, fee='0.000000000000000001', minimum_qty='0.000000000001234')
        print('market_made', market_made.to_dict_full())
        print("books:" , self.exchange.books["ETHBTC"].asks)
        buy_single = await self.exchange.limit_buy("ETH", "BTC", price='0.00015', qty=1, creator=self.buyer1, fee='0.01')
        print('buy single', buy_single.to_dict_full())
        await self.exchange.limit_buy("ETH", "BTC", price='0.00015', qty='0.000000000001234', creator=self.buyer1, fee='0.01')
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[3].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[3].confirmed = True

        await self.exchange.next()
        books = self.exchange.books["ETHBTC"]
        agent = await self.exchange.get_agent(self.buyer1)
        
        self.assertEqual(books.asks[0].price, Decimal('0.00005'))
        ETH_traded = prec(self.exchange.trade_log[5].qty + self.exchange.trade_log[6].qty, 18)
        BTC_from_trade = prec(self.exchange.trade_log[5].qty*self.exchange.trade_log[5].price + self.exchange.trade_log[5].exchange_fee['quote'] + self.exchange.trade_log[5].network_fee['quote']  + self.exchange.trade_log[6].qty*self.exchange.trade_log[6].price + self.exchange.trade_log[6].exchange_fee['quote'] + self.exchange.trade_log[6].network_fee['quote'], 8)
        self.assertEqual(agent['assets'],{'ETH':ETH_traded, 'BTC': self.buyer_initial_assets - BTC_from_trade} )

class GetTradesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.trader1 = (await self.exchange.register_agent("trader1", initial_assets={"USD":10000}))['registered_agent']
        self.trader2 = (await self.exchange.register_agent("trader2", initial_assets={"BTC": 1000, "USD":10000}))['registered_agent']
        await self.exchange.limit_buy("BTC", "USD", price=152, qty=2, creator=self.trader1, fee='0.02')
        await self.exchange.limit_sell("BTC", "USD", price=152, qty=2, creator=self.trader2, fee='0.02000002') #NOTE this one is meant to be ignored
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.trader2, fee='0.02')  
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True

        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
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
        agent = await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000})
        self.agent = agent['registered_agent']

    async def test_cancel_order(self):
        order = await self.exchange.limit_buy("BTC" , "USD", price=149, qty=2, creator=self.agent, fee='0.02')
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 2)
        cancel = await self.exchange.cancel_order("BTC", "USD", order.id)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(cancel["cancelled_order"]['id'], order.id)
        self.assertEqual(cancel["cancelled_order"]['creator'], self.agent)
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 1)
        self.assertEqual(await self.exchange.get_order("BTCUSD", order.id), {'error': 'order not found'})       
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], Decimal('0.00'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('0.0000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'], order.id)

    async def test_cancel_order_error(self):
        cancel = await self.exchange.cancel_order('BTC', 'USD', "error")
        self.assertEqual(cancel, {"cancelled_order": "order not found"})

class CancelAllOrdersTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent1 = (await self.exchange.register_agent("buyer1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("buyer2", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_cancel_all_orders(self):
        order = await self.exchange.limit_buy("BTC", "USD", price=150, qty=10, creator=self.agent1, tif="TEST", fee='.10')
        await self.exchange.limit_buy("BTC", "USD", price=149, qty=10, creator=self.agent1, tif="TEST", fee='.10')
        await self.exchange.limit_buy("BTC", "USD", price=153, qty=10, creator=self.agent2, tif="TEST", fee='.10')        
        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 4)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)

        canceled = await self.exchange.cancel_all_orders("BTC", "USD", self.agent1 )
        agent = await self.exchange.get_agent(self.agent1)
        print(canceled)    

        self.assertEqual(len(self.exchange.books["BTCUSD"].bids), 2)
        self.assertEqual(len(self.exchange.books["BTCUSD"].asks), 1)
        self.assertEqual(len(canceled['cancelled_orders']), 2)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], Decimal('0.00'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('0.0000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'], order.id)

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
        self.agent = (await self.exchange.register_agent("agent3", initial_assets={"USD" : 10000}))['registered_agent']

    async def test_get_assets(self):
        order= await self.exchange.limit_buy("BTC" , "USD", price=152, qty=2, creator=self.agent, fee='0.2') 
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        result = await self.exchange.get_assets(self.agent)
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(result['assets']['BTC'],2 )
        self.assertEqual(result['assets']['USD'], Decimal('9696.19'))
        self.assertEqual(agent['assets'], {"BTC": Decimal('2'), "USD": Decimal('9696.19')})      
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], Decimal('0.00'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.00000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('0.0000'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['order_id'], order.id)

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
        self.agent = (await self.exchange.register_agent("agent9", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_has_asset(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent)
        result = await self.exchange.agent_has_assets(self.agent, "BTC", 2)
        self.assertEqual(result, True)

class FreezeAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent10", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_freeze_asset(self):
        await self.exchange.freeze_assets(self.agent, "USD", "test_id", 1000, prec('0.0001'), prec('0.0001'))
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], Decimal('1000.00'))   
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.00010'))
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('0.0001'))

class UnFreezeAssetTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent10", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_unfreeze_asset(self):
        await self.exchange.freeze_assets(self.agent, "USD", "test_id", 1000, prec('0.0001'), prec('0.0001'))
        await self.exchange.unfreeze_assets(self.agent, "USD", "test_id", 1000, prec('0.0001'), prec('0.0001'))
        agent = await self.exchange.get_agent(self.agent)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_exchange_fee'], 0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_network_fee'], 0)
        self.assertEqual(agent['frozen_assets']['USD'][0]['frozen_qty'], 0)

class HasCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        
        self.agent = (await self.exchange.register_agent("agent10", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_has_cash(self):
        result = await self.exchange.agent_has_cash(self.agent, 10000, 1)
        self.assertEqual(result, True)

class GetOrderTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent11", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        

    async def test_get_order(self):
        order = await self.exchange.limit_buy("BTC" , "USD", price=150, qty=2, creator=self.agent, fee='0.2')
        result = await self.exchange.get_order(order.ticker, order.id)
        self.assertEqual(result.id, order.id)

class getTransactionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent12", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        

    async def test_get_transactions(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent, fee='0.2')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
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

    async def test_get_agents_cash(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent, fee='0.16')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        result = await self.exchange.agents_cash()
        self.assertEqual(result[1][self.agent]['cash'], Decimal('9696.23'))

class totalCashTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent14", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_total_cash(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent, fee='0.2')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()          
        result = await self.exchange.total_cash()
        self.assertEqual(result, Decimal('9696.19'))

class getPositionsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agent22", initial_assets={"USD" : 10000}))['registered_agent']

    async def test_get_positions(self):
        await self.exchange.limit_buy("BTC" , "USD", price=152, qty=2, creator=self.agent, fee='0.2')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
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
        initial_buy = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent, fee='0.01')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        agent = await self.exchange.get_agent_index(self.agent)
        buyup = await self.exchange.limit_buy("BTC" , "USD", price=155, qty=9997, creator=self.agent_high_buyer, fee='.01')

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()  

        high_buy = await self.exchange.limit_buy("BTC" , "USD", price=300, qty=2, creator=self.agent_high_buyer, fee='0.01')
        high_sell = await self.exchange.market_sell("BTC", "USD", qty=2, seller=self.agent, fee='0.00000001')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
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
        initial_buy = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent, fee='0.01')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        print(initial_buy)
        agent = await self.exchange.get_agent_index(self.agent)
        buyup = await self.exchange.limit_buy("BTC" , "USD", price=155, qty=9997, creator=self.agent_high_buyer, fee='.01')

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()  

        high_buy = await self.exchange.limit_buy("BTC" , "USD", price=300, qty=2, creator=self.agent_high_buyer, fee='0.01')
        high_sell = await self.exchange.market_sell("BTC", "USD", qty=2, seller=self.agent, fee='0.00001')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
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
        await self.exchange.create_asset("ETH", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}, {'asset': 'BTC','market_qty':1000 ,'seed_price':'0.5' ,'seed_bid':'.99', 'seed_ask':'1.01'}])

        print('assets', (await self.exchange.get_agent('init_seed_ETHUSD')))

        initial_buy = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent, fee='0.01')
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()

        agent = await self.exchange.get_agent_index(self.agent)
        print('initial buy', initial_buy)
        print('assets after initial buy', self.exchange.agents[agent]['assets'])
        print(self.exchange.books['ETHBTC'].bids)
        print(self.exchange.books['ETHBTC'].asks)

        change_asset = await self.exchange.market_buy("ETH", "BTC", qty=3, buyer=self.agent, fee='0.0000001')
        await self.exchange.next() 
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        print('BTC', len(self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions))
        print('ETH', len(self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions))
        await self.exchange.next() 
        print('change asset', change_asset)
        print('assets after change asset', self.exchange.agents[agent]['assets'])
        

        buyup = await self.exchange.limit_buy("ETH" , "USD", price=155, qty=9998, creator=self.agent_high_buyer, fee='.01')
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()  

        high_buy = await self.exchange.limit_buy("ETH" , "USD", price=300, qty=2, creator=self.agent_high_buyer, fee='0.01')
        high_sell = await self.exchange.market_sell("ETH", "USD", qty=2, seller=self.agent, fee='0.00000001')
        self.mock_requester.responder.cryptos['ETH'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
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
        self.agent2 = (await self.exchange.register_agent("Agent2", initial_assets={"USD" : 200, "BTC": '1.02'}))['registered_agent']
        
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
            {'id': "testbuy",'agent': self.agent1, 'order_id':'buyer_order_id','quote_flow': -50, 'price': 50, 'base': 'BTC', 'quote': 'USD', 'initial_qty': 1, 'qty': 1, 'dt': self.exchange.datetime, 'fee': Decimal('0.01') ,'type': 'buy'},
            {'id': "testsell",'agent': self.agent2, 'order_id': 'seller_order_id', 'quote_flow': 50,  'price': 50,'base': 'BTC', 'quote': 'USD', 'qty': -1, 'dt': self.exchange.datetime, 'fee': Decimal('0.01') ,'type': 'sell'}
        ]

        await self.exchange.freeze_assets(self.agent1, "USD", transaction[0]['order_id'], 50, Decimal('0.01'), Decimal('0.01'))
        await self.exchange.freeze_assets(self.agent2, "BTC", transaction[1]['order_id'], 1, Decimal('0.01'), Decimal('0.01'))
        
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
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee='0.02')
        await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee='0.03')
        await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee='0.04')

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True

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
        buy_1 = await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee='0.02')
        buy_2 = await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee='0.03')
        buy_3 = await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee='0.04')

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.next()
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True

        await self.exchange.next()
        result = await self.exchange.get_agents_positions()
        for position in result:
            print('-------------------------------------------')
            print(position)
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
        self.assertEqual(result[1]['positions'][1]['qty'], prec(10000- buy_1['qty']*buy_1['fills'][0]['price']))
        self.assertEqual(result[1]['positions'][1]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(type(result[2]['positions']), list )
        self.assertEqual(result[2]['positions'][0]['asset'], 'BTC')
        self.assertEqual(result[2]['positions'][0]['qty'], 10003)
        self.assertEqual(result[2]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[2]['positions'][0]['enters'][0]['asset'], 'BTC')
        self.assertEqual(result[2]['positions'][0]['enters'][1]['qty'], 3)
        self.assertEqual(result[2]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[2]['positions'][0]['enters'][0]['type'], 'buy')
        self.assertEqual(result[2]['positions'][0]['exits'], []) 
        self.assertEqual(result[2]['positions'][1]['asset'], 'USD')
        self.assertEqual(result[2]['positions'][1]['qty'], prec(10000- buy_2['qty']*buy_2['fills'][0]['price']))
        self.assertEqual(result[2]['positions'][1]['dt'], datetime(2023, 1, 1, 0, 0))       
        self.assertEqual(type(result[3]['positions']), list )
        self.assertEqual(result[3]['positions'][0]['asset'], 'BTC')
        self.assertEqual(result[3]['positions'][0]['qty'], 10004)
        self.assertEqual(result[3]['positions'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[3]['positions'][0]['enters'][0]['asset'], 'BTC')
        self.assertEqual(result[3]['positions'][0]['enters'][1]['qty'], 4)
        self.assertEqual(result[3]['positions'][0]['enters'][0]['dt'], datetime(2023, 1, 1, 0, 0))
        self.assertEqual(result[3]['positions'][0]['enters'][0]['type'], 'buy')
        self.assertEqual(result[3]['positions'][0]['exits'], []) 
        self.assertEqual(result[3]['positions'][1]['asset'], 'USD')
        self.assertEqual(result[3]['positions'][1]['qty'], prec(10000- buy_3['qty']*buy_3['fills'][0]['price']))
        self.assertEqual(result[3]['positions'][1]['dt'], datetime(2023, 1, 1, 0, 0))

class getAgentsHoldingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent1 = (await self.exchange.register_agent("agent16", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent17", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent18", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_agents_holding(self):
        await self.exchange.market_buy("BTC", "USD", qty=2, buyer=self.agent1, fee='0.02')
        await self.exchange.market_buy("BTC", "USD", qty=3, buyer=self.agent2, fee='0.03')
        await self.exchange.market_buy("BTC", "USD", qty=4, buyer=self.agent3, fee='0.04')
        
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[1].confirmed = True
        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[2].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[2].confirmed = True
        await self.exchange.next()

        result = await self.exchange.get_agents_holding("BTC")
        self.assertEqual(result, ['init_seed_BTCUSD', self.agent1, self.agent2, self.agent3 ])

class getSharesOutstandingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)
        self.agent = (await self.exchange.register_agent("agentoutstand", initial_assets={"USD": 200000}))['registered_agent']
        outstander = await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent, fee='.01')
        print(outstander)

        self.mock_requester.responder.cryptos['BTC'].blockchain.mempool.transactions[0].confirmed = True
        self.mock_requester.responder.cryptos['USD'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.next()

    async def test_get_outstanding_shares(self):
        result = await self.exchange.get_outstanding_shares("BTC")
        self.assertEqual(result, Decimal('1000')) 
        print(self.exchange.books['BTCUSD'].asks)
        print(self.exchange.books['BTCUSD'].bids)

class getAgentsSimpleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.agent1 = (await self.exchange.register_agent("agent1", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent2 = (await self.exchange.register_agent("agent2", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        self.agent3 = (await self.exchange.register_agent("agent3", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_agents_simple(self):
        result = await self.exchange.get_agents_simple()
        print(result)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['agent'], 'init_seed_BTCUSD')
        self.assertEqual(result[0]['assets'], {'BTC': Decimal('0'), 'USD': Decimal('0')})
        self.assertEqual(result[0]['frozen_assets']['BTC'][0]['order_id'], 'init_seed_BTCUSD')
        self.assertEqual(result[0]['frozen_assets']['BTC'][0]['frozen_qty'], Decimal('1000'))
        self.assertEqual(result[0]['frozen_assets']['BTC'][0]['frozen_exchange_fee'], Decimal('0.0'))
        self.assertEqual(result[0]['frozen_assets']['BTC'][0]['frozen_network_fee'], Decimal('1000.00000000'))
        self.assertEqual(result[0]['frozen_assets']['USD'][0]['order_id'], 'init_seed_BTCUSD')
        self.assertEqual(result[0]['frozen_assets']['USD'][0]['frozen_qty'], Decimal('148.5'))
        self.assertEqual(result[0]['frozen_assets']['USD'][0]['frozen_exchange_fee'], Decimal('0.0'))
        self.assertEqual(result[0]['frozen_assets']['USD'][0]['frozen_network_fee'], Decimal('1000000.00'))

        self.assertEqual(result[1], {'agent': self.agent1, 'assets': { 'BTC': Decimal('10000'), 'USD': Decimal('10000')}, 'frozen_assets': {}})
        self.assertEqual(result[2], {'agent': self.agent2, 'assets': { 'BTC': Decimal('10000'), 'USD': Decimal('10000')}, 'frozen_assets': {}})
        self.assertEqual(result[3], {'agent': self.agent3, 'assets': { 'BTC': Decimal('10000'), 'USD': Decimal('10000')}, 'frozen_assets': {}})

class GetPriceBarsTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.agent = (await self.exchange.register_agent("agent", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']

    async def test_get_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10)
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0)})

    async def test_get_minute_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1T")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})     

    async def test_get_5minute_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="5T")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_week_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1W")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )}) 

    async def test_get_month_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1M")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_year_price_bars(self):
        price_bars = await self.exchange.get_price_bars("BTCUSD", limit=10, bar_size="1Y")
        self.assertEqual(len(price_bars), 1)
        self.assertEqual(price_bars[0], {'open': 150, 'high': 150, 'low': 150, 'close': 150, 'volume': 1000, 'dt': datetime(2023, 1, 1, 0, 0, )})

    async def test_get_price_bars_over_time(self):
        day = 1
        while day < 10:
            self.exchange.datetime = datetime(2023, 1, day)
            await self.exchange.limit_buy("BTC", "USD", price=random.randint(100,180), qty=random.randint(1,10), creator=self.agent, fee='0.01')
            await self.exchange.limit_sell("BTC", "USD", price=random.randint(100,180), qty=random.randint(1,10), creator=self.agent, fee='0.01')
            day+=1

        get_price_bars = await self.exchange.get_price_bars("BTC", limit=10)
        print(self.exchange.trade_log)
        print(len(get_price_bars), get_price_bars)

class calculateMarketCapTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.mock_requester = MockRequester()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
        await self.exchange.create_asset("BTC", pairs=[{'asset': 'USD','market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.agent1 = (await self.exchange.register_agent("agentcap", initial_assets={"BTC": 10000, "USD" : 10000}))['registered_agent']
        await self.exchange.market_buy("BTC", "USD", qty=1000, buyer=self.agent1, fee='0.01')

    # @unittest.skip("Run manually to test")
    async def test_calculate_market_cap(self):
        result = await self.exchange.calculate_market_cap("BTC", "USD")
        self.assertEqual(result, 1500000)