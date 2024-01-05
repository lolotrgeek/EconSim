import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from decimal import Decimal
from typing import List
from source.utils._utils import generate_address, validate_address

class MempoolTransaction:
    __slots__ = ['id', 'asset', 'fee', 'amount', 'sender', 'recipient', 'confirmed', 'timestamp', 'dt', 'transfers']
    def __init__(self, asset, fee, amount, sender, recipient, dt=None, id=None, transfers=[]):
        self.id: str = id if id and validate_address(id) else generate_address()
        self.asset:str = asset
        self.fee: Decimal = fee
        self.amount: Decimal = amount
        self.sender: str = sender
        self.recipient: str = recipient
        self.confirmed: bool = False
        self.timestamp: int = None
        self.dt: datetime = dt
        self.transfers: list = transfers
        
    def to_dict(self) -> dict:
        return {
            'id': self.id, #TODO: rename to hash?
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

    async def get_pending_transactions(self, to_dicts=False) -> List[MempoolTransaction]:
        if to_dicts: return [transaction.to_dict() for transaction in self.transactions if not transaction.confirmed]
        return [transaction for transaction in self.transactions if not transaction.confirmed]
    
    async def get_confirmed_transactions(self, to_dicts=False) -> List[MempoolTransaction]:
        if to_dicts: return [transaction.to_dict() for transaction in self.transactions if transaction.confirmed]
        return [transaction for transaction in self.transactions if transaction.confirmed]
    

