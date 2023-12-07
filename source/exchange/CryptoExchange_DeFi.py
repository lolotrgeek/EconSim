import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from uuid import uuid4 as UUID
import random, string
from decimal import Decimal
from source.Archive import Archive
from .Exchange import Exchange
from .types.CryptoOrderBook import CryptoOrderBook
from .types.CryptoTrade import CryptoTrade
from .types.CryptoOrder import CryptoOrder
from .types.OrderSide import OrderSide
from .types.OrderType import OrderType
from .types.CryptoMatchedOrder import CryptoMatchedOrder
from .types.CryptoFees import Fees
from source.utils.logger import Logger
from source.utils._utils import get_random_string, prec, non_zero_prec

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class CryptoDeFiExchange():
    """
    A Crypto Exchange that uses an Automated Market Maker (AMM) to match orders.

    It creates pools of assets, wherein agents provide liquidity and receive rewards. 
    Orders move assets from the pool wallet to the user's wallet, every transaction is processed on a single blockchain.

    There are no limit orders, only market orders called "swaps".

    """
    def __init__(self, datetime= None, requester=None, archiver=None):
        super().__init__(datetime=datetime)
        self.archiver = archiver
        self.requester = requester
        self.default_currency = {'name': 'DefY', 'symbol': 'DFY', 'id': str(UUID()), 'decimals': 18}
        self.assets = {self.default_currency['symbol']: {'type': 'crypto', 'id' : self.default_currency['id'], 'decimals': self.default_currency['decimals'], 'min_qty': Decimal('0.01'), 'min_qty_percent': Decimal('0.05')}}        
        self.pairs = []
        self.wallets = {}
        self.agents_archive = Archive('crypto_agents')
        self.assets_archive = Archive('crypto_assets')
        self.books_archive = Archive('crypto_books')
        self.trade_log_archive = Archive('crypto_trade_log')        
        self.pairs_archive = Archive('crypto_pairs')
        self.wallets_archive = Archive('crypto_wallets')
        self.fees = Fees()
        self.fees.waive_fees = False
        self.pending_transactions = []
        self.max_pending_transactions = 1_000_000
        self.max_pairs = 10000
        self.logger = Logger('CryptoExchange', 30)
        self.minimum = Decimal('0.00000000000000000001')
        
    async def next(self):
        for transaction in self.pending_transactions: 
            # NOTE: base and quote transactions return a MempoolTransaction, see `source\crypto\MemPool.py`
            base_transaction = await self.requester.get_transaction(asset=transaction['base_txn']['asset'], id=transaction['base_txn']['id'])
            quote_transaction = await self.requester.get_transaction(asset=transaction['quote_txn']['asset'], id=transaction['quote_txn']['id'])
            if not base_transaction and not quote_transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in base_transaction or 'error' in quote_transaction:
                continue
            elif base_transaction['confirmed'] and quote_transaction['confirmed']:
                await self._complete_trade(transaction, base_transaction, quote_transaction)
        await self.archive()
        await self.prune_trades()
        # self.logger.debug('next', self.datetime)
  
    async def archive(self):
        await super().archive()
        self.pairs_archive.store(self.pairs)
        self.wallets_archive.store(self.wallets)

   