import os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.DefiExchange import DefiExchange as Exchange
from source.crypto.WalletRequests import WalletRequests as Requests
from .MockRequesterCrypto import MockRequesterCrypto as MockRequesterCrypto
from source.utils._utils import dumps
from datetime import datetime, timedelta
from source.utils.logger import Null_Logger

class MockTrader():
    def __init__(self) -> None:
        pass

class MockRequesterWallet():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self, exchange=None):
        self.responder = MockResponderWallet(exchange=exchange)

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)
    
class MockResponderWallet():
    def __init__(self) -> None:
        self.wallet = Requests()
        self.wallet.logger =Null_Logger(debug_print=True)
        self.traders = {}
        self.mock_order = None
    
    async def callback(self, msg):
        if 'address' in msg:
            if msg['wallet'] in self.traders:
                if msg['topic'] == 'request_signature': return dumps(await self.traders[msg['wallet']].signature_request(msg['txn']))
                elif msg['topic'] == 'get_balance': return dumps((await self.traders[msg['wallet']].get_balance(msg['asset'])))
            else: return f'unknown asset {msg["asset"]}'    
        else: return f'unknown topic {msg["topic"]}'    