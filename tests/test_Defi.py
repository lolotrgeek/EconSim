import unittest
from uuid import uuid4 as UUID
import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.exchange.types.Defi import *
from source.exchange.components.ConstantProduct import ConstantProduct
from source.crypto.MemPool import MempoolTransaction

class TestDefi(unittest.TestCase):

    def test_symbol(self):
        symbol = Symbol("ETH")
        self.assertEqual(symbol.value, "ETH")
        self.assertEqual(str(symbol), 'ETH')

    def test_pair(self):
        base = Symbol("ETH")
        quote = Symbol("USDT")
        pair = Pair(base, quote)
        self.assertEqual(pair.base, base)
        self.assertEqual(pair.quote, quote)

    def test_address(self):
        address = Address("0x1234567890abcdef")
        self.assertEqual(address.value, "0x1234567890abcdef")

    def test_pool_fee(self):
        fee = PoolFee(0.01)
        self.assertEqual(fee.value, '0.01')

    def test_pool(self):
        fee = PoolFee(0.01)
        base = "ETH"
        quote = "USDT"
        pool = Pool(fee, base, quote, amm=None)
        self.assertEqual(pool.fee, fee)
        self.assertEqual(pool.base, base)
        self.assertEqual(pool.quote, quote)

    def test_pool_to_dict(self):
        fee = PoolFee(0.01)
        base = "ETH"
        quote = "USDT"
        lp_token = Address(generate_address())
        pool = Pool(fee, base, quote, lp_token=lp_token)
        self.assertEqual(pool.to_dict(), {
            'fee': str(fee),
            'base': base,
            'quote': quote,
            'amm': {'reserve_a': 0, 'reserve_b': 0, 'k': 0},
            'is_active': True,
            'lp_token': str(lp_token),
        })

    def test_dict_to_pool(self):
        fee = PoolFee(0.01)
        base = "ETH"
        quote = "USDT"
        pool = Pool(fee, base, quote)
        dict_pool = pool.to_dict()
        re_pool = Pool(**dict_pool)
        self.assertEqual(re_pool.fee, str(pool.fee))
        self.assertEqual(re_pool.base, pool.base)
        self.assertEqual(re_pool.quote, pool.quote)
        self.assertEqual(re_pool.amm['reserve_a'], pool.amm.reserve_a)
        self.assertEqual(re_pool.amm['reserve_b'], pool.amm.reserve_b)
        self.assertEqual(re_pool.amm['k'], pool.amm.k)
        self.assertEqual(re_pool.is_active, pool.is_active)
        self.assertEqual(re_pool.lp_token, str(pool.lp_token))


    def test_currency(self):
        symbol = Symbol("ETH")
        name = "Ethereum"
        currency = Currency(symbol, name)
        self.assertEqual(currency.symbol, symbol)
        self.assertEqual(currency.name, name)

    def test_asset(self):
        address = "0x1234567890abcdef"
        decimals = 18
        asset = Asset(address, decimals)
        self.assertEqual(asset.address, address)
        self.assertEqual(asset.decimals, decimals)

    def test_swap(self):
        pool_fee_pct = PoolFee(0.01)
        fee_amount = 0.1
        slippage = 0.05
        deadline = 30
        txn = MempoolTransaction('test',0,0,'test', 'test', transfers=[{'asset': 'ETH'}, {'asset': 'USDT'}])
        swap = Swap(pool_fee_pct, fee_amount, slippage, deadline, txn)
        self.assertEqual(swap.pool_fee_pct, pool_fee_pct)
        self.assertEqual(swap.fee_amount, fee_amount)
        self.assertEqual(swap.slippage, slippage)
        self.assertEqual(swap.txn, txn)

    def test_liquidity(self):
        owner = Address("0x1234567890abcdef")
        max_price = 1000
        min_price = 900
        pool_fee_pct = PoolFee(0.01)
        txn = MempoolTransaction('test',0,0,'test', 'test', transfers=[{'asset': 'ETH'}, {'asset': 'USDT'}])
        liquidity = Liquidity(owner, max_price, min_price, pool_fee_pct, txn)
        self.assertEqual(liquidity.owner, owner)
        self.assertEqual(liquidity.max_price, max_price)
        self.assertEqual(liquidity.min_price, min_price)
        self.assertEqual(liquidity.pool_fee_pct, pool_fee_pct)
        self.assertEqual(liquidity.txn, txn)

    def test_collect_fee(self):
        base_fee = 0.1
        quote_fee = 0.2
        pool_fee_pct = 0.01
        liquidity_txn = MempoolTransaction('test',0,0,'test', 'test', transfers=[{'asset': 'ETH'}, {'asset': 'USDT'}])
        txn = MempoolTransaction('test',0,0,'test', 'test')
        collect_fee = CollectFee(liquidity_txn.id, base_fee, quote_fee, pool_fee_pct, txn)
        self.assertEqual(collect_fee.base_fee, base_fee)
        self.assertEqual(collect_fee.quote_fee, quote_fee)
        self.assertEqual(collect_fee.pool_fee_pct, pool_fee_pct)
        self.assertEqual(collect_fee.txn, txn)

if __name__ == '__main__':
    unittest.main()
