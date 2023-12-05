from decimal import Decimal

class Pair():
    def __init__(self, base: str, quote: str, ticker: str, base_decimals: int, quote_decimals: int, min_qty: Decimal, min_price: Decimal, min_qty_percent: Decimal, is_active: bool):
        """
        Represents a pairing of two assets.
        """
        self.base: str = base
        self.quote: str = quote
        self.ticker: str = ticker
        self.base_decimals: int = base_decimals
        self.quote_decimals: int = quote_decimals
        self.min_qty: Decimal = min_qty
        self.min_price: Decimal = min_price
        self.min_qty_percent: Decimal = min_qty_percent
        self.is_active: bool = is_active

    def __repr__(self) -> str:
        return f"Pair({self.base}, {self.quote}, {self.ticker}, {self.base_decimals}, {self.quote_decimals}, {self.min_qty}, {self.min_price}, {self.min_qty_percent}, {self.is_active})"
    
    def __str__(self) -> str:
        return f"<Pair {self.base}/{self.quote}>"
    
    def to_dict(self) -> dict:
        return {
            'base': self.base,
            'quote': self.quote,
            'ticker': self.ticker,
            'base_decimals': self.base_decimals,
            'quote_decimals': self.quote_decimals,
            'min_qty': self.min_qty,
            'min_price': self.min_price,
            'min_qty_percent': self.min_qty_percent,
            'is_active': self.is_active,
        }