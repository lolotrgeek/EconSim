import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from .OrderSide import OrderSide
from .CryptoFees import Fees
from .CryptoOrder import CryptoOrder
from decimal import Decimal
from source.utils._utils import non_zero_prec, prec
from source.utils.logger import Null_Logger

class CryptoMatchedOrder():
    def __init__(self, order:CryptoOrder, book_order: CryptoOrder, base_decimals: int, quote_decimals: int, fees: Fees, logger=Null_Logger) -> None:
        self.fees: Fees = fees
        self.order:CryptoOrder = order
        self.book_order:CryptoOrder = book_order
        self.trade_qty: Decimal = non_zero_prec(min((book_order.qty, order.unfilled_qty)), base_decimals)
        self.total_price: Decimal = prec(self.trade_qty * book_order.price, quote_decimals)
        self.taker_fee: Decimal = 0
        self.maker_fee: Decimal = 0

        if order.side == OrderSide.BUY:
            self.taker_fee = self.fees.taker_fee(self.total_price, quote_decimals)
            self.exchange_fee = {'quote': self.taker_fee, 'base': book_order.exchange_fee_per_txn}
            self.network_fee = {'quote': order.network_fee_per_txn, 'base': book_order.network_fee_per_txn}

        if order.side == OrderSide.SELL:
            self.taker_fee = self.fees.taker_fee(self.trade_qty, base_decimals)
            self.exchange_fee = {'quote': book_order.exchange_fee_per_txn, 'base': self.taker_fee}
            self.network_fee = {'quote': book_order.network_fee_per_txn, 'base': order.network_fee_per_txn}

        logger.debug(f'{order.type.value} {order.side.value} {order.id}/{book_order.id} exchange fees: {self.exchange_fee}')
        logger.debug(f'{order.type.value} {order.side.value} {order.id}/{book_order.id} network fees: {self.network_fee}')
        logger.debug(f"matched {order.ticker} {order.id} {order.type.value} {order.side.value} with book order {book_order.id} for {self.trade_qty}@{book_order.price} total {self.total_price}")


        


