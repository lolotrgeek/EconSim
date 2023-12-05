from decimal import Decimal
from uuid import uuid4 as UUID

class Asset():
    def __init__(self, type: str, decimals: int, min_qty: Decimal, min_qty_percent: Decimal, symbol=""):
        """
        Represents an asset.
        """
        self.id: str = str(UUID())
        self.symbol: str = symbol
        self.type: str = type
        self.decimals: int = decimals
        self.min_qty: Decimal = min_qty
        self.min_qty_percent: Decimal = min_qty_percent

    def __repr__(self) -> str:
        return f"Asset({self.type}, {self.id}, {self.decimals}, {self.min_qty}, {self.min_qty_percent})"
    
    def __str__(self) -> str:
        return f"<Asset {self.type} {self.id}>"
    
    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'id': self.id,
            'decimals': self.decimals,
            'min_qty': self.min_qty,
            'min_qty_percent': self.min_qty_percent,
        }