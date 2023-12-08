from .TraderCrypto import CryptoTrader as Trader
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from time import sleep
from source.utils._utils import prec, dumps
from source.utils.logger import Logger
from decimal import Decimal
from source.crypto.Wallet import Wallet
from source.Messaging import Responder, Requester

class RandomSwapper():
    def __init__(self, name):
        self.wallet = Wallet(name)

    # loops through wallet signature requests, randomly approves or rejects them
    async def sign_txns(self):
        for idx, request in enumerate(self.wallet.signature_requests):
            decision = random.choice([True, False])
            txn = self.wallet.signature_requests.pop(idx)
            await self.wallet.sign_txn(txn, decision)

class RandomLiquidityProvider():
    pass
