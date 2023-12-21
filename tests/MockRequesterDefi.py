import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.exchange.DefiExchange import DefiExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.WalletRequests import WalletRequests
from source.runners.run_defi_exchange import DefiExchangeRunner
from .MockRequester import MockRequester
from .MockRequesterCrypto import MockRequesterCrypto
from .MockRequesterWallet import MockRequesterWallet
from datetime import datetime, timedelta
from source.utils.logger import Null_Logger

class MockRequesterDefiExchange():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self, exchange=None):
        self.responder = MockResponderDefiExchange(exchange=exchange)
        self.connected = False

    async def init(self):
        pass
    
    async def connect(self):
        self.connected = True
        pass        

    async def request(self, msg):
        return await self.responder.callback(msg)
    
class MockDefiExchange(Exchange):
    def __init__(self, datetime=datetime(2023, 1, 1), crypto_requests=None, wallet_requests=None) -> None:
        super().__init__(datetime=datetime, crypto_requests=crypto_requests, wallet_requests=wallet_requests)
        self.logger = Null_Logger(debug_print=True)

    async def signature_response(self, agent_wallet, decision, txn):
        return {'decision': decision, 'txn': txn['id']}

class MockResponderDefiExchange(DefiExchangeRunner):
    def __init__(self, exchange=None, wallet_requests=None, crypto_requests=None) -> None:
        super().__init__()
        self.crypto_requests = MockRequesterCrypto()
        self.wallet_requester = MockRequesterWallet()
        self.crypto_requests = CryptoCurrencyRequests(self.crypto_requests)
        self.wallet_requests = WalletRequests(self.wallet_requester)
        self.exchange = MockDefiExchange(datetime=datetime(2023, 1, 1),crypto_requests=self.crypto_requests, wallet_requests=wallet_requests ) if exchange is None else exchange(datetime=datetime(2023, 1, 1), crypto_requests=self.crypto_requests, wallet_requests=wallet_requests )
        self.exchange.logger =Null_Logger(debug_print=True)
        self.agent = None
        self.mock_order = None
        self.connected = False

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