from .MemPool import MemPool, MempoolTransaction
import random
import pandas as pd

class Blockchain():
    def __init__(self, datetime=None):
        seed = MempoolTransaction('init_seed', 0, 0, 'init_seed', 'init_seed', datetime)
        seed.confirmed = True
        self.chain = [seed]
        self.mempool = MemPool()
        self.datetime = datetime
        self.total_transactions = 0
        # self.new_block(transactions=[], previous_hash=1)

    async def new_block(self, transactions, previous_hash=None, dt=None) -> dict:
        block = {
            'index': len(self.chain) + 1, 
            'timestamp': dt, 
            'transactions': transactions, 
            'previous_hash': previous_hash or hash(self.chain[-1]),
        }
        block['hash'] = lambda: hash((block['index'], block['timestamp'], block['transactions'], block['previous_hash']))
        self.chain.append(block)
        return block
    
    async def add_transaction(self, asset:str, fee:float, amount:float, sender:str, recipient:str, dt) -> MempoolTransaction:
        if(fee <= 0.0): return MempoolTransaction("error", 0, 0, "error", "error", dt)
        self.total_transactions += 1
        mempool_transaction = MempoolTransaction(asset, fee, amount, sender, recipient, dt)
        self.mempool.transactions.append(mempool_transaction)
        return mempool_transaction

    async def process_transactions(self, dt=None) -> None:
        unconfirmed_transactions = self.mempool.get_pending_transactions()
        unconfirmed_transactions.sort(key=lambda x: x.fee, reverse=True)
        num_unconfirmed = len(unconfirmed_transactions)
        for index, transaction in enumerate(unconfirmed_transactions):
            # create a probablity distribution for confirmation based on the length of the mempool
            confirmation_odds = .9 - (index / num_unconfirmed)
            if random.random() < confirmation_odds:
                transaction.confirmed = True
                transaction.timestamp = dt # when the transaction was confirmed
                num_unconfirmed -= 1
                self.chain.append(transaction)
        # self.new_block(self.mempool.get_confirmed_transactions(), hash(self.chain[-1]), dt=self.datetime)
        
        self.mempool.transactions = self.mempool.get_pending_transactions() # clear the mempool of confirmed transactions
    
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
        return None
    
    async def get_mempool(self):
        return self.mempool.transactions

    @property
    def last_block(self) -> dict:
        return self.chain[-1]

