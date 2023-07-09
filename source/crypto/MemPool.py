from datetime import datetime
import pandas as pd

class MempoolTransaction:
    def __init__(self, ticker, fee, amount, sender, recipient, dt=None):
        self.ticker = ticker
        self.fee = fee
        self.amount = amount
        self.sender = sender
        self.recipient = recipient
        self.confirmed = False
        self.timestamp = None
        self.dt = dt if dt else datetime.now()

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'fee': self.fee,
            'amount': self.amount,
            'sender': self.sender,
            'recipient': self.recipient,
            'confirmed': self.confirmed,
            'timestamp': self.timestamp,
            'dt': self.dt
        }


class MemPool:
    def __init__(self):
        self.transactions = []

    def get_pending_transactions(self):
        return [transaction for transaction in self.transactions if not transaction.confirmed]
    
    def get_confirmed_transactions(self):
        return [transaction for transaction in self.transactions if transaction.confirmed]
    
    @property
    def transaction_log(self):
        if(len(self.transactions) == 0):
            return pd.DataFrame()
        else:
            return pd.DataFrame.from_records([t.to_dict() for t in self.transactions]).set_index('dt')

