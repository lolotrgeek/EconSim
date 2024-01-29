import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decimal import Decimal
from datetime import datetime
from source.runners.run_trader_defi import DefiTraderRunner
from source.agents.TraderDefi import TraderDefi
from source.crypto.MemPool import MempoolTransaction
from .MockRequester import MockRequester, MockResponder
from source.runners.run_defi_exchange import DefiExchangeRunner
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests        
from .MockRequesterCrypto import MockRequesterCrypto
from source.utils.logger import Null_Logger

class MockRequesterWallet():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponderWallet()

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)

class MockWalletHolder(TraderDefi):
    def __init__(self, name, exchange_requests, crypto_requests):
        super().__init__(name, exchange_requests, crypto_requests)
        
    async def next(self, time=None):
        for idx, request in enumerate(self.wallet.signature_requests):
            decision = 'approve'
            txn = self.wallet.signature_requests.pop(idx)
            await self.wallet.sign_txn(txn, decision)        

class MockResponderWallet(DefiTraderRunner):
    """
    Sets up a mock trader and gives them a wallet to make mocked responses with
    """
    def __init__(self) -> None:
        super().__init__()
        self.responder = MockResponder()
        self.requester = MockRequesterCrypto()
        self.exchange_requester = MockRequester()
        self.trader = MockWalletHolder('test_trader', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests( self.requester))
        self.swapper = MockWalletHolder('test_swapper', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests( self.requester))

    async def init(self):
        self.seed_address = self.requester.responder.currencies['ETH'].burn_address
        await self.trader.wallet.connect('ETH')
        await self.swapper.wallet.connect('ETH')
        await self.trader.wallet._update_holdings(MempoolTransaction('ETH', 0, Decimal('5.01'), self.seed_address, self.trader.wallet.address, datetime(2023,1,1)).to_dict() )
        await self.swapper.wallet._update_holdings(MempoolTransaction('ETH', 0, Decimal('5.01'), self.seed_address, self.swapper.wallet.address, datetime(2023,1,1)).to_dict() )
        transfers_in = [
            {'asset': 'ETH', 'address': '0x0', 'from': self.trader.wallet.address, 'to': self.seed_address, 'for': 1, 'decimals': 8},
            {'asset': 'CAKE', 'address': '0x01', 'from': self.seed_address, 'to': self.trader.wallet.address, 'for': 1, 'decimals': 8}
        ]
        defi_txn = MempoolTransaction('ETH', Decimal('.01'), 0, self.trader.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_in).to_dict()
        await self.trader.wallet._update_holdings(defi_txn)
        
    async def next(self):
        await self.trader.next()
        await self.swapper.next()

    async def respond(self, msg):
        return await self.callback(msg)
    
    async def lazy_respond(self, msg):
        return await self.callback(msg)

    async def connect(self):
        self.connected = True
        pass          
