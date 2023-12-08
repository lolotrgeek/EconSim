from uuid import uuid4 as UUID
from typing import List


class MempoolTransaction:
    def __init__(self, asset, fee, amount, sender, recipient, dt=None, transfers=[]):
        self.id = str(UUID())
        self.asset = asset
        self.fee = fee
        self.amount = amount
        self.sender = sender
        self.recipient = recipient
        self.confirmed = False
        self.timestamp = None
        self.dt = dt
        self.transfers = transfers
        

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
            'dt': self.dt,
            'transfers': self.transfers
        }


class MemPool:
    def __init__(self) :
        self.transactions: List[MempoolTransaction] = []

    async def get_pending_transactions(self, to_dicts=False) -> list:
        if to_dicts: return [transaction.to_dict() for transaction in self.transactions if not transaction.confirmed]
        return [transaction for transaction in self.transactions if not transaction.confirmed]
    
    async def get_confirmed_transactions(self, to_dicts=False) -> list:
        if to_dicts: return [transaction.to_dict() for transaction in self.transactions if transaction.confirmed]
        return [transaction for transaction in self.transactions if transaction.confirmed]
    

