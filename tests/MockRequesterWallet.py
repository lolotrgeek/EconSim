import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decimal import Decimal
from datetime import datetime
from source.runners.run_trader_defi import DefiTraderRunner
from source.agents.TraderDefi import TraderDefi
from source.crypto.MemPool import MempoolTransaction
from .MockRequester import MockRequester, MockResponder
from .MockRequesterCrypto import MockRequesterCrypto as MockRequesterCrypto
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


class MockResponderWallet(DefiTraderRunner):
    """
    Sets up a mock trader and gives them a wallet to make mocked responses with
    """
    def __init__(self) -> None:
        super().__init__()
        self.responder = MockResponder()
        self.requester = MockRequesterCrypto()
        self.exchange_requester = MockRequester()
        self.trader = TraderDefi('test_trader', self.exchange_requester, self.requester)
        self.traders[self.trader.wallet.address] = self.trader

    async def init(self):
        trader = self.traders[self.trader.wallet.address]
        await trader.wallet.connect('ETH')
        self.seed_address = self.requester.responder.currencies['ETH'].burn_address
        seed_txn = MempoolTransaction('ETH', 0, Decimal('2.01'), self.seed_address, self.trader.wallet.address, datetime(2023,1,1)).to_dict() 
        await trader.wallet.update_holdings(seed_txn)
        transfers_in = [
            {'asset': 'ETH', 'address': '0x0', 'from': self.trader.wallet.address, 'to': self.seed_address, 'for': 1, 'decimals': 8},
            {'asset': 'CAKE', 'address': '0x01', 'from': self.seed_address, 'to': self.trader.wallet.address, 'for': 1, 'decimals': 8}
        ]
        defi_txn = MempoolTransaction('ETH', Decimal('.01'), 0, self.trader.wallet.address, self.seed_address, datetime(2023,1,1), transfers=transfers_in).to_dict()
        await trader.wallet.update_holdings(defi_txn)
        

    async def respond(self, msg):
        return await self.callback(msg)
    
    async def lazy_respond(self, msg):
        return await self.callback(msg)

    async def connect(self):
        self.connected = True
        pass          
