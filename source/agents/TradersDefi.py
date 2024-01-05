from .TraderCrypto import CryptoTrader as Trader
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from time import sleep
from source.utils._utils import prec, dumps
from source.utils.logger import Logger
from .TraderDefi import TraderDefi

class RandomSwapper(TraderDefi):
    def __init__(self, name, exchange_messenger=None, crypto_messenger=None):
        super().__init__(name, exchange_requests=exchange_messenger, crypto_requests=crypto_messenger)
        self.wallet.holdings['ETH'] = 50

    async def next(self, time):
        self.logger.info(f'RandomSwapper - current holdings: {self.wallet.holdings}, chain: {self.wallet.chain}')
        self.current_date = time
        swap = await self.swap(self.wallet.address, 'ETH', 'BTC', 1, '.05')
        self.logger.info(f'swapped: {swap}')
        signed = await self.wallet.approve_transaction(swap.txn.to_dict())
        if signed['decision'] == 'reject':
            self.logger.info(f'rejected txn: {signed}')
        await self.send_approved_swap(signed['txn'])

class RandomLiquidityProvider(TraderDefi):
    def __init__(self, name, exchange_messenger=None, crypto_messenger=None):
        super().__init__(name, exchange_requests=exchange_messenger, crypto_requests=crypto_messenger)
        self.wallet.holdings['ETH'] = 1000
        self.wallet.holdings['BTC'] = 1000
        self.logger.info(f'starting liquidity: {self.wallet.holdings}')
        self.lock_next = False

    async def sign_txns(self):
        for idx, request in enumerate(self.wallet.signature_requests):
            decision = 'approve'
            txn = self.wallet.signature_requests.pop(idx)
            fee = await self.wallet.get_fee()
            if fee < 0:
                self.logger.info(f'fee is negative: {fee}')
                return
            txn['fee'] = fee
            signed = await self.wallet.sign_txn(txn, decision)
            if signed and 'error' not in signed:
                self.logger.info(f'signed txn: {signed}')
                self.lock_next = False
        
    async def next(self, time):
        self.logger.info(f'LiquidityProvider - current holdings: {self.wallet.holdings}, chain: {self.wallet.chain}')
        self.current_date = time
        await self.sign_txns()
        if self.lock_next: return
        provided_liquidity = await self.provide_liquidity(self.wallet.address, 'ETH', 'BTC', 10)
        self.lock_next = True
        self.logger.info(f'provided liquidity: {provided_liquidity}')