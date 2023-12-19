import os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.DefiExchange import DefiExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from source.runners.run_defi_exchange import DefiExchangeRunner
from .MockRequesterCrypto import MockRequesterCrypto as MockRequesterCrypto
from source.utils._utils import dumps
from datetime import datetime, timedelta
from source.utils.logger import Null_Logger

class MockRequesterDefiExchange():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self, exchange=None):
        self.responder = MockResponderDefiExchange(exchange=exchange)

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)
    
class MockResponderDefiExchange(DefiExchangeRunner):
    def __init__(self, exchange=None, wallet_requester=None, crypto_requester=None) -> None:
        super().__init__()
        self.crypto_requester = MockRequesterCrypto() if crypto_requester is None else crypto_requester
        self.exchange = Exchange(datetime=datetime(2023, 1, 1),crypto_requester=self.crypto_requester, wallet_requester=wallet_requester ) if exchange is None else exchange(datetime=datetime(2023, 1, 1), crypto_requester=self.crypto_requester, wallet_requester=wallet_requester )
        self.exchange.logger =Null_Logger(debug_print=True)
        self.agent = None
        self.mock_order = None

    async def next(self):
        self.time = self.time + timedelta(days=1)
        self.exchange.datetime = self.time
        await self.exchange.next()