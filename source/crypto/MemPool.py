import pandas as pd
from uuid import uuid4 as UUID


class MempoolTransaction:
    def __init__(self, asset, fee, amount, sender, recipient, dt=None):
        self.id = str(UUID())
        self.asset = asset
        self.fee = fee
        self.amount = amount
        self.sender = sender
        self.recipient = recipient
        self.confirmed = False
        self.timestamp = None
        self.dt = dt
        

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'asset': self.asset,
            'fee': self.fee,
            'amount': self.amount,
            'sender': self.sender,
            'recipient': self.recipient,
            'confirmed': self.confirmed,
            'timestamp': self.timestamp,
            'dt': self.dt
        }


class MemPool:
    def __init__(self) :
        self.transactions = []

    def get_pending_transactions(self, to_dicts=False) -> str:
        if to_dicts: return [transaction.to_dict() for transaction in self.transactions if not transaction.confirmed]
        return [transaction for transaction in self.transactions if not transaction.confirmed]
    
    def get_confirmed_transactions(self, to_dicts=False) -> str:
        if to_dicts: return [transaction.to_dict() for transaction in self.transactions if transaction.confirmed]
        return [transaction for transaction in self.transactions if transaction.confirmed]
    

