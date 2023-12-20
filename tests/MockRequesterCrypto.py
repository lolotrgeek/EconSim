import os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.runners.run_crypto_exchange import CryptoExchangeRunner
from source.runners.run_crypto import CryptoRunner
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
        self.connected = False

    async def init(self):
        await self.responder.init()

    async def connect(self):
        self.connected = True
        pass
    
    async def request(self, msg):
        return await self.responder.callback(msg)

class MockResponderCrypto(CryptoRunner):
    """
    Mocks a responder for Crypto by wrapping the CryptoRunner with response methods
    """
    def __init__(self):
        super().__init__()
        self.time = datetime(2023, 1, 1)
        self.currencies = {
            'USD': CryptoCurrency("USD", self.time, decimals=2),
            'BTC': CryptoCurrency("BTC", self.time, decimals=8),
            'ETH': CryptoCurrency("ETH", self.time, decimals=18),  
        }
        self.connected = False

    async def next(self):
        self.time = self.time + timedelta(days=1)
        for crypto in self.currencies:
            await self.currencies[crypto].next(self.time)  

    async def respond(self, msg):
        return await self.callback(msg)
    
    async def lazy_respond(self, msg):
        return await self.callback(msg)
    
    async def connect(self):
        self.connected = True
        pass

class MockRequesterCryptoExchange():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self, exchange=None):
        self.responder = MockResponderCryptoExchange(exchange=exchange)
        self.connected = False

    async def init(self):
        await self.responder.init()
    
    async def connect(self):
        self.connected = True
        pass    

    async def request(self, msg):
        return await self.responder.callback(msg)
    
class MockResponderCryptoExchange(CryptoExchangeRunner):
    def __init__(self, exchange=None) -> None:
        super().__init__()
        self.mock_requester = MockRequesterCrypto()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), crypto_requests=self.requests) if exchange is None else exchange(datetime=datetime(2023, 1, 1), crypto_requests=self.requests)
        self.exchange.logger = Null_Logger(debug_print=True)
        self.agent = None
        self.mock_order = None
        self.connected = False

    async def init(self):
        await self.exchange.create_asset("BTC", pairs = [{'asset': "USD" ,'market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.agent = (await self.exchange.register_agent("buyer1", {"BTC":2, "USD": 100000}))['registered_agent']
        self.mock_order = await self.exchange.limit_buy("BTC", "USD", price=151, qty=1, fee='0.0001', creator=self.agent)        

    async def next(self):
        self.time = self.time + timedelta(days=1)
        self.exchange.datetime = self.time
        await self.exchange.next()

    async def respond(self, msg):
        return await self.callback(msg)
    
    async def lazy_respond(self, msg):
        return await self.callback(msg)
    
    async def connect(self):
        self.connected = True
        pass