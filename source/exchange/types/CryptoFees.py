from decimal import Decimal
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from source.utils._utils import prec

class Fees():
    def __init__(self):
        self.waive_fees = True
        self.maker_fee_rate = prec('0.001')  # Maker fee rate as a decimal (e.g., 0.001 = 0.1%)
        self.taker_fee_rate = prec('0.002')  # Taker fee rate as a decimal (e.g., 0.002 = 0.2%)
        self.total_fee_revenue = 0  # Total fee revenue collected by the exchange
        self.fees_collected = {}

    def taker_fee(self, volume, decimal) -> Decimal:
        if self.waive_fees:
            return 0
        return prec(volume * self.taker_fee_rate, decimal)

    
    def maker_fee(self, volume, decimal) -> Decimal:
        if self.waive_fees:
            return 0
        return prec(volume * self.maker_fee_rate, decimal)
        
    def add_fee(self, asset: str, fee: Decimal) -> dict:
        if asset in self.fees_collected: 
            self.fees_collected[asset] += fee
        else: 
            self.fees_collected[asset] = fee
        return {asset: fee}
    
    def remove_fee(self, asset: str, fee: Decimal) -> dict:
        if asset in self.fees_collected: 
            self.fees_collected[asset] -= fee
        else: 
            self.fees_collected[asset] = -fee
        return {asset: fee}