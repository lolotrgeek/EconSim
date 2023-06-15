
class Fees():
    def __init__(self):
        self.maker_fee_rate = 0.001  # Maker fee rate as a decimal (e.g., 0.001 = 0.1%)
        self.taker_fee_rate = 0.002  # Taker fee rate as a decimal (e.g., 0.002 = 0.2%)
        self.total_fee_revenue = 0.0  # Total fee revenue collected by the exchange

    def taker_fee(self, volume):
        return volume * self.taker_fee_rate
    
    def maker_fee(self, volume):
        return volume * self.maker_fee_rate
        
