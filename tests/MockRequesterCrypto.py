import random, string, os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.CryptoExchange import CryptoExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from source.crypto.CryptoCurrency import CryptoCurrency
from source.utils._utils import dumps
from datetime import datetime, timedelta
from source.utils.logger import Null_Logger

class MockRequesterCrypto():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponderCrypto()

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)

class MockResponderCrypto():
    """
    Mocked run_exchange and run_company callback responder
    """
    def __init__(self, requests=None):
        self.time = datetime(2023, 1, 1)
        self.cryptos = {
            'USD': CryptoCurrency("USD", self.time, requester=MockRequesterCryptoExchange),
            'BTC': CryptoCurrency("BTC", self.time, requester=MockRequesterCryptoExchange),
            'ETH': CryptoCurrency("ETH", self.time, requester=MockRequesterCryptoExchange),  
        }

    async def next(self):
        self.time = self.time + timedelta(days=1)
        self.exchange.datetime = self.time
        for crypto in self.cryptos:
            await self.cryptos[crypto].next(self.time)
                
    async def callback(self, msg):
        if 'asset' in msg:
            if msg['asset'] in self.cryptos:
                if msg['topic'] == 'get_transactions': return dumps(await self.cryptos[msg['asset']].blockchain.get_transactions())
                if msg['topic'] == 'get_transaction': return dumps(await self.cryptos[msg['asset']].blockchain.get_transaction(msg['id']))
                elif msg['topic'] == 'add_transaction': return dumps((await self.cryptos[msg['asset']].blockchain.add_transaction(msg['asset'], msg['fee'], msg['amount'], msg['sender'], msg['recipient'])).to_dict())
                elif msg['topic'] == 'get_mempool': return dumps(await self.cryptos[msg['asset']].blockchain.get_mempool())
                elif msg['topic'] == 'get_pending_transactions': return dumps(await self.cryptos[msg['asset']].blockchain.mempool.get_pending_transactions(to_dicts=True))
                elif msg['topic'] == 'get_confirmed_transactions': return dumps(await self.cryptos[msg['asset']].blockchain.mempool.get_confirmed_transactions(to_dicts=True))

            else: return f'unknown asset {msg["asset"]}'    
        
class MockRequesterCryptoExchange():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponderCryptoExchange()

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)
    
class MockResponderCryptoExchange():
    def __init__(self) -> None:
        self.mock_requester = MockRequesterCrypto()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
        self.exchange.logger =Null_Logger()
        self.agent = None
        self.mock_order = None

    async def init(self):
        await self.exchange.create_asset("BTC", pairs = [{'asset': "USD" ,'market_qty':1000 ,'seed_price':150 ,'seed_bid':.99, 'seed_ask':1.01}])
        self.agent = (await self.exchange.register_agent("buyer1", {"USD": 100000}))['registered_agent']
        self.mock_order = await self.exchange.limit_buy("BTC", "USD", price=151, qty=1, fee=0.0001, creator=self.agent)        

    async def next(self):
        self.time = self.time + timedelta(days=1)
        self.exchange.datetime = self.time
        await self.exchange.next()

    async def callback(self, msg):
        if msg['topic'] == 'create_asset': return dumps((await self.exchange.create_asset(msg['symbol'], msg['pairs'])))
        elif msg['topic'] == 'get_tickers': return dumps((await self.exchange.get_tickers()))
        elif msg['topic'] == 'limit_buy': return dumps((await self.exchange.limit_buy(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'limit_sell': return dumps((await self.exchange.limit_sell(msg['base'] , msg['quote'], msg['price'], msg['qty'], msg['creator'], msg['fee'])).to_dict_full())
        elif msg['topic'] == 'market_buy': return await self.exchange.market_buy(msg['base'] , msg['quote'], msg['qty'], msg['buyer'], msg['fee'])
        elif msg['topic'] == 'market_sell': return await self.exchange.market_sell(msg['base'] , msg['quote'], msg['qty'], msg['seller'], msg['fee'])
        elif msg['topic'] == 'cancel_order': return await self.exchange.cancel_order(msg['base'] , msg['quote'], msg['order_id'])
        elif msg['topic'] == 'cancel_all_orders': return await self.exchange.cancel_all_orders(msg['base'] , msg['quote'], msg['agent'])
        elif msg['topic'] == 'candles': return dumps(await self.exchange.get_price_bars(ticker=msg['ticker'], bar_size=msg['interval'], limit=msg['limit']))
        # elif msg['topic'] == 'mempool': return await self.exchange.mempool(msg['limit'])
        elif msg['topic'] == 'order_book': return dumps( (await self.exchange.get_order_book(msg['ticker'])).to_dict(msg['limit']))
        elif msg['topic'] == 'latest_trade': return dumps(await self.exchange.get_latest_trade(msg['base'] , msg['quote']))
        elif msg['topic'] == 'trades': return dumps( await self.exchange.get_trades(msg['base'] , msg['quote'], msg['limit']))
        elif msg['topic'] == 'quotes': return await self.exchange.get_quotes(msg['ticker'])
        elif msg['topic'] == 'best_bid': return dumps((await self.exchange.get_best_bid(msg['ticker'])).to_dict())
        elif msg['topic'] == 'best_ask': return dumps((await self.exchange.get_best_ask(msg['ticker'])).to_dict())
        elif msg['topic'] == 'midprice': return dumps(await self.exchange.get_midprice(msg['ticker']))
        elif msg['topic'] == 'cash': return await self.exchange.get_cash(msg['agent'])
        elif msg['topic'] == 'assets': return await self.exchange.get_assets(msg['agent'])
        elif msg['topic'] == 'register_agent': return await self.exchange.register_agent(msg['name'], msg['initial_assets'])
        elif msg['topic'] == 'get_agent': return dumps(await self.exchange.get_agent(msg['name']))
        elif msg['topic'] == 'get_agents': return dumps(await self.exchange.get_agents())
        elif msg['topic'] == 'add_cash': return dumps(await self.exchange.add_cash(msg['agent'], msg['amount'], msg['note']))
        elif msg['topic'] == 'remove_cash': return dumps(await self.exchange.remove_cash(msg['agent'], msg['amount']))
        elif msg['topic'] == 'get_cash': return dumps(await self.exchange.get_cash(msg['agent']))
        elif msg['topic'] == 'get_assets': return dumps(await self.exchange.get_assets(msg['agent']))
        elif msg['topic'] == 'get_agents_holding': return dumps(await self.exchange.get_agents_holding(msg['asset']))
        elif msg['topic'] == 'get_agents_positions': return dumps(await self.exchange.get_agents_positions(msg['ticker']))
        elif msg['topic'] == 'get_agents_simple': return dumps(await self.exchange.get_agents_simple())
        elif msg['topic'] == 'get_positions': return dumps(await self.exchange.get_positions(msg['agent'], msg['page_size'], msg['page']))
        elif msg['topic'] == 'get_outstanding_shares': return dumps(await self.exchange.get_outstanding_shares(msg['ticker']))
        elif msg['topic'] == 'get_taxable_events': return dumps(await self.exchange.get_taxable_events())
        elif msg['topic'] == 'get_pending_transactions': return dumps(await self.exchange.get_pending_transactions(msg['limit']))
        #TODO: exchange topic to get general exchange data
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})        
    