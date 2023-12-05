from decimal import Decimal

class Fee():
    def __init__(self, fee_type: str, base_fee: Decimal, quote_fee: Decimal):
        self.fee_type: str = fee_type
        self.base: Decimal = base_fee
        self.quote: Decimal = quote_fee

    def __repr__(self) -> str:
        return f"Fee({self.fee_type}, {self.base}, {self.quote})"
    
    def __str__(self) -> str:
        return f"<Fee {self.fee_type} {self.base} {self.quote}>"
    
    def to_dict(self) -> dict:
        return {
            'fee_type': self.fee_type,
            'base': self.base,
            'quote': self.quote,
        }