from typing import List, Dict
from .Position import Position
from .Asset import Asset
from .FrozenAssets import FrozenAssets
from .TaxableEvent import TaxableEvent
from .Side import Side

class Agent():
    def __init__(self, name: str, positions: list, assets: dict, wallets: dict, frozen_assets={}, taxable_events= [], _transactions=[]):
        """
        Represents an agent in an Exchange.
        """
        self.name: str = name
        self.positions: List[Position] = positions
        self.assets: Dict[str, Asset] = assets
        self.wallets: Dict[str, str] = wallets
        self.frozen_assets: Dict[str, List[FrozenAssets]] = frozen_assets
        self.taxable_events: List[TaxableEvent] = taxable_events
        self._transactions: List[Side] = _transactions

    def __repr__(self) -> str:
        return f"Agent({self.name}, {self.positions}, {self.assets}, {self.wallets}, {self.frozen_assets}, {self.taxable_events}, {self._transactions})"
    
    def __str__(self) -> str:
        return f"<Agent {self.name}>"
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'positions': [position.to_dict() for position in self.positions],
            'assets': {asset: asset.to_dict() for asset, asset in self.assets.items() },
            'wallets': self.wallets,
            'frozen_assets': {asset: [frozen_asset.to_dict() for frozen_asset in frozen_assets] for asset, frozen_assets in self.frozen_assets.items()},
            'taxable_events': [taxable_event.to_dict() for taxable_event in self.taxable_events],
            '_transactions': [transaction.to_dict() for transaction in self._transactions],
        }
