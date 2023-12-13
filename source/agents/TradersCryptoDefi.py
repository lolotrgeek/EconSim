from .TraderCrypto import CryptoTrader as Trader
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from time import sleep
from source.utils._utils import prec, dumps
from source.utils.logger import Logger
from decimal import Decimal
from TraderDefi import TraderDefi

class RandomSwapper(TraderDefi):
    def __init__(self, name, exchange_messenger=None, crypto_messenger=None):
        super().__init__(name, requests=exchange_messenger, crypto_requests=crypto_messenger)

    # loops through wallet signature requests, randomly approves or rejects them
    async def sign_txns(self):
        for idx, request in enumerate(self.wallet.signature_requests):
            decision = random.choice([True, False])
            txn = self.wallet.signature_requests.pop(idx)
            await self.wallet.sign_txn(txn, decision)

    async def next(self, time):
        await self.sign_txns()
        self.swap(self.wallet.address, 'ETH', 'DAI', 1, '.05')

class RandomLiquidityProvider():
    pass
