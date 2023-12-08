import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decimal import Decimal
from .MemPool import MemPool, MempoolTransaction
from source.utils._utils import prec, get_minimum, validate_address
from source.Archive import Archive
import random
import pandas as pd

class Blockchain():
    def __init__(self, asset="", datetime=None, decimals=8):
        seed = MempoolTransaction(asset, get_minimum(decimals), 0, 'init_seed', 'init_seed', datetime)
        self.decimals = decimals
        self.no_fee = False
        seed.confirmed = True
        self.chain = [seed]
        self.mempool = MemPool()
        self.datetime = datetime
        self.total_transactions = 0
        self.accumulated_fees = 0
        self.max_transactions=100_000
        self.pruned_chain = Archive(asset+"chain")
        # self.new_block(transactions=[], previous_hash=1)

    async def new_block(self, transactions, previous_hash=None) -> dict:
        block = {
            'index': len(self.chain) + 1, 
            'timestamp': self.datetime, 
            'transactions': transactions, 
            'previous_hash': previous_hash or hash(self.chain[-1]),
        }
        block['hash'] = lambda: hash((block['index'], block['timestamp'], block['transactions'], block['previous_hash']))
        self.chain.append(block)
        return block
    
    async def add_transaction(self, asset:str, fee:Decimal, amount:Decimal, sender:str, recipient:str, id=None, transfers=[]) -> MempoolTransaction:
        if id and not validate_address(id):
            return MempoolTransaction(asset, 0, 0, "error", "refusing transaction: invalid id", dt=self.datetime)
        fee = prec(fee, self.decimals)
        amount = prec(amount, self.decimals)
        if(fee <= 0): return MempoolTransaction(asset, 0, 0, "error", "refusing transaction: no fee", id=id, dt=self.datetime)
        self.total_transactions += 1
        mempool_transaction = MempoolTransaction(asset, fee, amount, sender, recipient, dt=self.datetime, id=id, transfers=transfers)
        self.mempool.transactions.append(mempool_transaction)
        return mempool_transaction
    
    async def confirmation_odds(self, index, num_unconfirmed) -> float:
        return 1 - (index / num_unconfirmed)

    async def process_transactions(self) -> None:
        unconfirmed_transactions = await self.mempool.get_pending_transactions()
        unconfirmed_transactions.sort(key=lambda x: x.fee, reverse=True)
        num_unconfirmed = len(unconfirmed_transactions)
        confirmed = 0
        for index, transaction in enumerate(unconfirmed_transactions):
            # create a probablity distribution for confirmation based on the length of the mempool
            # increase confirmation odds for transactions with higher fees
            confirmation_odds = await self.confirmation_odds(index, num_unconfirmed)
            if random.random() < confirmation_odds:
                confirmed += 1
                transaction.confirmed = True
                transaction.timestamp = self.datetime # when the transaction was confirmed
                self.accumulated_fees += transaction.fee
                num_unconfirmed -= 1
                self.chain.append(transaction)
        self.mempool.transactions = await self.mempool.get_pending_transactions() # clear the mempool of confirmed transactions
        return {'confirmed': confirmed, 'unconfirmed': len(self.mempool.transactions) }
    
    async def prune(self, ) -> None:
        if len(self.chain) >= self.max_transactions:
            amount_to_prune = int(self.max_transactions/2)
            self.pruned_chain.put(str(self.chain[amount_to_prune].dt), self.chain[:amount_to_prune])
            self.chain = self.chain[amount_to_prune:]

    async def get_transactions_df(self) -> pd.DataFrame:
        return pd.DataFrame.from_records([t.to_dict() for t in self.chain]).set_index('dt')

    async def get_transactions (self) -> list:
        return [t.to_dict() for t in self.chain]
    
    async def get_transaction(self, id) -> dict:
        for transaction in self.chain:
            if transaction.id == id:
                return transaction.to_dict()
        for transaction in self.mempool.transactions:
            if transaction.id == id:
                return transaction.to_dict()
        return {"error": "transaction not found"}
    
    async def cancel_transaction(self, id:str) -> dict:
        unconfirmed_transactions = await self.mempool.get_pending_transactions()
        for transaction in unconfirmed_transactions:
            if transaction.id == id:
                unconfirmed_transactions.remove(transaction)
                return transaction.to_dict()
        return {"error": "transaction not found"}
    
    async def get_mempool(self):
        return self.mempool.transactions

    @property
    def last_block(self) -> dict:
        return self.chain[-1]

