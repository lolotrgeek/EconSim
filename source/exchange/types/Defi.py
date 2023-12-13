from typing import Dict, List
from decimal import Decimal
from uuid import uuid4 as UUID
import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from components.ConstantProduct import ConstantProduct
from crypto.MemPool import MempoolTransaction
from source.utils._utils import get_minimum, generate_address

#NOTE: https://wiki.python.org/moin/UsingSlots
# https://tommyseattle.com/python-class-dict-named-tuple-performance-and-memory-usage/

class Symbol():
    __slots__ = ["value"]
    def __init__(self, value:str = '') -> None:
        self.value:str = value
    def __repr__(self) -> str:
        return self.value
    def __str__(self) -> str:
        return self.value         

class Pair():
    __slots__ = ['base', 'quote']
    def __init__(self, base: Symbol, quote: Symbol) -> None:
        self.base: Symbol = base
        self.quote: Symbol = quote
        self.value = f'{base.value}{quote.value}'
    def __repr__(self) -> str:
        return self.value
    def __str__(self) -> str:
        return self.value
    def to_dict(self):
        return {
            'base': self.base,
            'quote': self.quote,
        }

class Address():
    __slots__ = ['value']
    def __init__(self, value:str='') -> None:
        self.value: str = value
    def __repr__(self) -> str:
        return self.value
    def __str__(self) -> str:
        return self.value

class PoolFee():
    __slots__ = ['value']
    def __init__(self, value:Decimal = 0) -> None:
        self.value: str = str(value)
    def __repr__(self) -> str:
        return self.value
    def __str__(self) -> str:
        return self.value        

class Pool():
    __slots__ = ['fee', 'base', 'quote', 'amm', 'total_liquidity', 'lp_token', 'is_active']
    def __init__(self, fee: Decimal, base: str, quote: str, amm: ConstantProduct, is_active: bool= True):
        self.fee: str = fee
        self.base: str = base
        self.quote: str = quote
        self.amm: ConstantProduct = amm
        self.lp_token: Address = Address(generate_address())
        self.is_active: bool = is_active

    def to_dict(self):
        return {
            'fee': self.fee,
            'base': self.base,
            'quote': self.quote,
            'amm': self.amm.to_dict(),
            'total_liquidity': self.total_liquidity,
            'lp_token': Address(generate_address()),
            'is_active': self.is_active,
        }

class Currency():
    __slots__ = ['name', 'symbol', 'id', 'decimals']
    def __init__(self, symbol: Symbol, name: str='', id:str = str(UUID()), decimals: int= 8):
        self.name: str = name
        self.symbol: Symbol = symbol.value
        self.id: str = id
        self.decimals: int = decimals

    def to_dict(self):
        return {
            'name': self.name,
            'symbol': self.symbol,
            'id': self.id,
            'decimals': self.decimals,
        }

class Asset():
    __slots__ = ['address', 'decimals', 'min_qty', 'is_active']
    def __init__(self, address: str, decimals: int, min_qty: Decimal = -1, is_active: bool = True):
        self.address: str = address
        self.decimals: int = decimals
        self.min_qty: Decimal = get_minimum(decimals) if min_qty == -1 else min_qty
        self.is_active: bool = is_active

    def to_dict(self):
        return {
            'address': self.address,
            'decimals': self.decimals,
            'min_qty': self.min_qty,
            'is_active': self.is_active,
        }

class Swap():
    __slots__ = ['pair', 'pool_fee', 'fee_amount' 'slippage', 'txn']
    def __init__(self, pool_fee_pct: PoolFee, fee_amount: Decimal, slippage: Decimal, txn: MempoolTransaction):
        self.pair: Pair = Pair(Symbol(txn.transfers[0]['asset']), Symbol(txn.transfers[1]['asset']))
        self.pool_fee_pct: PoolFee = pool_fee_pct.value
        self.fee_amount: Decimal = fee_amount
        self.slippage: Decimal = slippage
        self.txn: MempoolTransaction = txn

    def to_dict(self):
        return {
            'pair': self.pair.to_dict(),
            'pool_fee_pct': self.pool_fee_pct,
            'fee_amount': self.fee_amount,
            'slippage': self.slippage,
            'txn': self.txn.to_dict(),
        }

class Liquidity():
    __slots__ = ['pair', 'owner', 'max_price', 'min_price', 'pool_fee_pct', 'base_fee', 'quote_fee', 'txn']
    def __init__(self, owner: Address, max_price: Decimal, min_price: Decimal, pool_fee_pct: PoolFee, txn: MempoolTransaction):
        """
        owner: the address of the liquidity provider
        pair: the pair of the liquidity pool
        max_price: the maximum price of the liquidity pool
        min_price: the minimum price of the liquidity pool
        pool_fee_pct: the pool fee percentage
        quote_fee: the quote fee accumulated
        base_fee: the base fee accumulated
        txn: the transaction that created the liquidity position
        """
        self.pair: Pair = Pair(Symbol(txn.transfers[0]['asset']), Symbol(txn.transfers[1]['asset']))
        self.owner: Address = owner
        self.max_price: Decimal = max_price
        self.min_price: Decimal = min_price
        self.pool_fee_pct: PoolFee = pool_fee_pct
        self.quote_fee: Decimal = 0
        self.base_fee: Decimal = 0
        self.txn: MempoolTransaction = txn

    def to_dict(self):
        return {
            'owner': self.owner,
            'pair': self.pair.to_dict(),
            'max_price': self.max_price,
            'min_price': self.min_price,
            'pool_fee_pct': self.pool_fee_pct,
            'quote_fee': self.quote_fee,
            'base_fee': self.base_fee,
            'txn': self.txn.to_dict(),
        }

class CollectFee():
    __slots__ = ['base_fee', 'quote_fee',' pool_fee_pct', 'txn']
    def __init__(self, base_fee: Decimal, quote_fee: Decimal, pool_fee_pct: Decimal, txn:MempoolTransaction ):
        self.base_fee: Decimal = base_fee
        self.quote_fee: Decimal = quote_fee
        self. pool_fee_pct: Decimal = pool_fee_pct
        self.txn: MempoolTransaction = txn

    def to_dict(self):
        return {
            'base_fee': self.base_fee,
            'quote_fee': self.quote_fee,
            'pool_fee_pct': self.pool_fee_pct,
            'txn': self.txn.to_dict(),
        }