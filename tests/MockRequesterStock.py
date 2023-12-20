import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from source.runners.run_stock_exchange import StockExchangeRunner
from source.exchange.StockExchange import StockExchange as Exchange
from datetime import datetime


class MockRequester():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponder()
        self.connected = False

    async def init(self):
        await self.responder.init()

    async def connect(self):
        self.connected = True
        pass

    async def request(self, msg):
        return await self.responder.callback(msg)

class MockResponder(StockExchangeRunner):
    """
    Mocked run_exchange and run_company callback responder
    """
    def __init__(self):
        super().__init__()
        self.time = datetime(2023, 1, 1)
        self.exchange = Exchange(datetime=self.time)
        self.agent = None
        self.mock_order = None
        self.connected = False

    async def init(self):
        await self.exchange.create_asset("AAPL", seed_price=150, seed_bid=0.99, seed_ask=1.01)
        self.agent = (await self.exchange.register_agent("mock_agent", {'USD': 100000, "AAPL": 100}))['registered_agent']
        self.mock_order = await self.exchange.limit_buy("AAPL", price=149, qty=1, creator=self.agent)
    
    async def respond(self, msg):
        return await self.callback(msg)
    
    async def lazy_respond(self, msg):
        return await self.callback(msg)

    async def connect(self):
        self.connected = True
        pass