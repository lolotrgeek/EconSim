from decimal import Decimal
from copy import copy

class FrozenAssets():
    def __init__(self, order_id: str, qty: Decimal, exchange_fee: Decimal, network_fee: Decimal):
        self.order_id: str = order_id
        self.frozen_qty: Decimal = qty
        self.frozen_exchange_fee: Decimal = exchange_fee
        self.frozen_network_fee: Decimal = network_fee

    def __repr__(self) -> str:
        return f"FrozenAssets({self.order_id}, {self.frozen_qty}, {self.frozen_exchange_fee}, {self.frozen_network_fee})"
    
    def __str__(self) -> str:
        return f"<FrozenAssets {self.order_id} {self.frozen_qty} {self.frozen_exchange_fee} {self.frozen_network_fee}>"
    
    def to_dict(self) -> dict:
        return {
            'order_id': self.order_id,
            'frozen_qty': self.frozen_qty,
            'frozen_exchange_fee': self.frozen_exchange_fee,
            'frozen_network_fee': self.frozen_network_fee,
        }
    
    def copy(self):
        return copy(self)
