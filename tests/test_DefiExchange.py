import asyncio,sys,os
import unittest
from datetime import datetime
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from decimal import Decimal
from source.utils.logger import Null_Logger  
from source.exchange.DefiExchange import DefiExchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from source.crypto.WalletRequests import WalletRequests
from .MockRequesterCrypto import MockRequesterCrypto
from .MockRequesterWallet import MockRequesterWallet
from source.exchange.types.Defi import *

async def standard_asyncSetUp(self):
    self.crypto_requester = MockRequesterCrypto()
    self.wallet_requester = MockRequesterWallet()
    self.exchange = DefiExchange('ETH', datetime(2023, 1,1), Requests(self.crypto_requester), WalletRequests(self.wallet_requester))
    self.exchange.logger = Null_Logger(debug_print=True)
    await self.exchange.start()
    return self.exchange

class TestStart(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.crypto_requester = MockRequesterCrypto()
        self.wallet_requester = MockRequesterWallet()
        self.exchange = DefiExchange('ETH', datetime(2023, 1,1), Requests(self.crypto_requester), WalletRequests(self.wallet_requester))

    async def test_start(self):
        await self.exchange.start()
        self.assertTrue('ETH' in self.exchange.assets)
        self.assertEqual(self.exchange.default_currency.symbol , 'ETH')
        self.assertEqual(self.exchange.default_currency.decimals , 18)

class TestListAssets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)

    async def test_list_asset(self):
        await self.exchange.list_asset('CAKE', 18)
        self.assertTrue('CAKE' in self.exchange.assets)

    async def test_list_existing_asset_error(self):
        await self.exchange.list_asset('CAKE', 18)
        duplicate_asset = await self.exchange.list_asset('CAKE', 18)
        self.assertEqual(duplicate_asset['error'], 'cannot list, asset already exists')

    async def test_list_default_asset_error(self):
        duplicate_asset = await self.exchange.list_asset('ETH', 18)
        self.assertEqual(duplicate_asset['error'], 'cannot list, default_quote_currency')

    async def test_max_pairs_error(self):
        self.exchange.max_assets = 1
        new_listing = await self.exchange.list_asset('CAKE', 18)        
        self.assertEqual(new_listing['error'], 'cannot list, max_assets_reached')

class TestGetAssets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_assets(self):
        await self.exchange.list_asset('CAKE', 18)
        assets = await self.exchange.get_assets()
        self.assertTrue('CAKE' in assets)
        self.assertTrue('ETH' in assets)

class TestCreatePool(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)

    async def test_create_pool(self):
        await self.exchange.list_asset('CAKE', 18)
        new_pool = await self.exchange.create_pool('CAKE', 'ETH', 3)
        self.assertTrue('CAKEETH' in self.exchange.pools)
        self.assertEqual(self.exchange.pools['CAKEETH'][str(self.exchange.fee_levels[3])], new_pool)

    async def test_create_new_fee_pool(self):
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('CAKE', 'ETH', 3)
        new_fee_pool = await self.exchange.create_pool('CAKE', 'ETH', 2)
        self.assertTrue('CAKEETH' in self.exchange.pools)
        self.assertEqual(self.exchange.pools['CAKEETH'][str(self.exchange.fee_levels[2])], new_fee_pool)

    async def test_create_existing_pool(self):
        # will simply return the existing pool
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('CAKE', 'ETH', 3)
        duplicate_pool = await self.exchange.create_pool('CAKE', 'ETH', 3)
        self.assertTrue('CAKEETH' in self.exchange.pools)
        self.assertEqual(duplicate_pool.quote , 'ETH')
        self.assertEqual(duplicate_pool.base , 'CAKE')

    async def test_base_asset_not_listed_error(self):
        new_pool = await self.exchange.create_pool('BTC', 'ETH', 3)
        self.assertEqual(new_pool['error'], 'base asset does not exist')

    async def test_quote_asset_not_listed_error(self):
        new_pool = await self.exchange.create_pool('ETH', 'BTC', 3)
        self.assertEqual(new_pool['error'], 'quote asset does not exist')

    async def test_max_pools_error(self):
        self.exchange.max_pairs = 1
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('CAKE', 'ETH', 3)
        new_pool = await self.exchange.create_pool('CAKE', 'ETH', 3)
        self.assertEqual(new_pool['error'], 'cannot create, max_pairs_reached')

class TestSelectPoolFeePct(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)

    async def test_select_pool_fee_pct(self):
        self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_a = 1 
        self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_b = 1
        selected_pool_pct = await self.exchange.select_pool_fee_pct('ETH', 'CAKE')
        self.assertEqual(selected_pool_pct, str(self.exchange.fee_levels[3]) )

    async def test_no_pool_error(self):
        err_pool = await self.exchange.select_pool_fee_pct('CAKE', 'ETH')
        self.assertEqual(err_pool['error'], 'pool does not exist')

    async def test_no_active_pools(self):
        await self.exchange.create_pool('CAKE', 'ETH', 2)
        err_pool = await self.exchange.select_pool_fee_pct('CAKE', 'ETH')
        self.assertEqual(err_pool['error'], 'no active pools found')

class TestPoolAddLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)

    async def test_pool_add_liquidity(self):
        pool_fee_pct = str(self.exchange.fee_levels[3])
        pool = self.exchange.pools['ETHCAKE'][pool_fee_pct]
        await self.exchange.pool_add_liquidity(pool, 1, 1)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_a, 1)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_b, 1)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.k, 1)

    async def test_pool_add_liquidity_multi(self):
        pool_fee_pct = str(self.exchange.fee_levels[3])
        pool = self.exchange.pools['ETHCAKE'][pool_fee_pct]
        await self.exchange.pool_add_liquidity(pool, 1, 1)
        await self.exchange.pool_add_liquidity(pool, 1, 1)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_a, 2)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_b, 2)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.k, 4)

class TestPoolSwapLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)        

    async def test_pool_swap_liquidity(self):
        pool_fee_pct = str(self.exchange.fee_levels[3])
        pool = self.exchange.pools['ETHCAKE'][pool_fee_pct]
        await self.exchange.pool_swap_liquidity(pool, Decimal('.02'), 1, Decimal('0.001'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_a, Decimal('0.98'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_b, 2)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.k, Decimal('1.960000000000000000'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.fees, {datetime(2023, 1, 1, 0, 0): Decimal('0.001')})

class TestPoolRemoveLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)         

    async def test_pool_remove_liquidity(self):
        pool_fee_pct = str(self.exchange.fee_levels[3])
        pool = self.exchange.pools['ETHCAKE'][pool_fee_pct]
        await self.exchange.pool_remove_liquidity(pool, 1, 1)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_a, 0)
        self.assertEqual(self.exchange.pools['ETHCAKE'][pool_fee_pct].amm.reserve_b, 0)

class TestGetPools(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)

    async def test_get_pools(self):
        pools = await self.exchange.get_pools()
        self.assertTrue(type(pools) is dict)
        self.assertTrue('ETHCAKE' in pools)

class TestGetPool(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_get_pool(self):
        fee= await self.exchange.select_pool_fee_pct('ETH', 'CAKE')
        pool = await self.exchange.get_pool('ETH', 'CAKE', fee)
        self.assertEqual(pool.base , 'ETH')
        self.assertEqual(pool.quote , 'CAKE')

    async def test_get_pool_error(self):
        pool = await self.exchange.get_pool('ETH', 'BTC', str(self.exchange.fee_levels[3]))
        self.assertEqual(pool['error'], 'pool does not exist')

class TestGetPoolLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_get_pool_liquidity(self):
        fee= await self.exchange.select_pool_fee_pct('ETH', 'CAKE')
        pool_liquidity = await self.exchange.get_pool_liquidity('ETH', 'CAKE', fee)
        self.assertEqual(pool_liquidity['ETH'] , 1)
        self.assertEqual(pool_liquidity['CAKE'] , 1)

class TestGetFeeLevels(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.exchange = await standard_asyncSetUp(self)

    async def test_get_fee_levels(self):
        fee_levels = await self.exchange.get_fee_levels()
        self.assertTrue(type(fee_levels) is list)
        self.assertTrue(fee_levels == self.exchange.fee_levels)

class TestWalletHasFunds(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_wallet_has_funds(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        has_funds = await self.exchange.wallet_has_funds(wallet_address, 'ETH', 1)
        self.assertTrue(has_funds)

    async def test_wallet_has_funds_error(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        has_funds = await self.exchange.wallet_has_funds(wallet_address, 'ETH', 2)
        self.assertFalse(has_funds)

class TestSwap(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_swap(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'))
        # await self.exchange.wallet_requests.requester.responder.next()
        self.assertFalse(type(swap) is dict)
        self.assertTrue(len(self.exchange.unapproved_swaps.items()) == 1)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id], swap)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.id, swap.txn.id)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[0]['asset'], 'ETH')
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[1]['asset'], 'CAKE')
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[0]['for'], Decimal('0.110000000000000000'))
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[1]['for'], Decimal('0.099099099099099100'))
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[0]['from'], wallet_address)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[0]['to'], self.exchange.router)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[1]['to'], wallet_address)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[1]['from'], self.exchange.router)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[0]['decimals'], 18)
        self.assertEqual(self.exchange.unapproved_swaps[swap.txn.id].txn.transfers[1]['decimals'], 18)

    async def test_swap_no_funds(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('2'))
        self.assertTrue(type(swap) is dict)
        self.assertEqual(swap['error'], 'wallet does not have enough funds')

class TestApprovedSwap(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_approved_swap(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'))
        approved = await self.exchange.approve_swap(swap.txn.id, '.0001')
        self.assertTrue(len(self.exchange.pending_swaps.items()) == 1)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id], swap)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.id, swap.txn.id)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[0]['asset'], 'ETH')
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[1]['asset'], 'CAKE')
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[0]['for'], Decimal('0.110000000000000000'))
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[1]['for'], Decimal('0.099099099099099100'))
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[0]['from'], wallet_address)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[0]['to'], self.exchange.router)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[1]['to'], wallet_address)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[1]['from'], self.exchange.router)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[0]['decimals'], 18)
        self.assertEqual(self.exchange.pending_swaps[swap.txn.id].txn.transfers[1]['decimals'], 18)

    async def test_swap_max_pending_transactions(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        self.exchange.max_pending_transactions = 1
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'))
        await self.exchange.approve_swap(swap.txn.id, '.0001')
        swap_too = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'))
        self.assertTrue(len(self.exchange.pending_swaps.items()) == 1)
        self.assertTrue(type(swap_too) is dict)
        self.assertEqual(swap_too['error'], 'max_pending_transactions_reached') 

    async def test_swap_max_unapproved_swaps(self):
        # will pop last unapproved swap and replace with new swap
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        self.exchange.max_unapproved_swaps = 1
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'))
        await self.exchange.approve_swap(swap.txn.id, '.0001')
        swap_too = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'))
        self.assertTrue(type(swap_too) is not dict)
        self.assertTrue(len(self.exchange.unapproved_swaps.items()) == 1)
        self.assertTrue(swap_too.txn.id in self.exchange.unapproved_swaps)               

    async def test_swap_slippage_too_high(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 100, 100)
        approved_swap = await self.exchange.approve_swap(swap.txn.id, '.0001')
        self.assertTrue(type(approved_swap) is dict)
        self.assertEqual(approved_swap['error'], 'price too high')

    async def test_swap_slippage_too_low(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swap = await self.exchange.swap(wallet_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_remove_liquidity(pool, Decimal('.9'), Decimal('.9'))
        approved_swap = await self.exchange.approve_swap(swap.txn.id, '.0001')
        self.assertTrue(type(approved_swap) is dict)
        self.assertEqual(approved_swap['error'], 'price too low')

class TestConfirmSwap(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        self.wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_confirm_swap(self):
        self.swap = await self.exchange.swap(self.wallet_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        await self.exchange.approve_swap(self.swap.txn.id, '.0001')        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_swaps()
        self.assertTrue(len(self.exchange.pending_swaps.items()) == 0)
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_a, Decimal('0.9'))
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_b, Decimal('1.099099099099099100'))
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.k, Decimal('0.989189189189189189'))
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.fees, Decimal('0.0001'))

class TestProvideLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_provide_liquidity(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')
        self.assertTrue(len(self.exchange.unapproved_liquidity.items()) == 1)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id], liquidity)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.id, liquidity.txn.id)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[0]['asset'], 'ETH')
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[1]['asset'], 'CAKE')
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[0]['for'], Decimal('0.400000000000000000'))
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[1]['for'], Decimal('0.285714285714285715'))
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[0]['from'], wallet_address)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[0]['to'], self.exchange.router)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[1]['to'], self.exchange.router)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[1]['from'], wallet_address)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[0]['decimals'], 18)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[1]['decimals'], 18)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[2]['address'], self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].lp_token)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[2]['for'], 0)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[2]['from'], self.exchange.router)
        self.assertEqual(self.exchange.unapproved_liquidity[liquidity.txn.id].txn.transfers[2]['to'], wallet_address)

    async def test_provide_liquidity_no_funds(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', 2, 3, '.8', '.2')
        self.assertTrue(type(liquidity) is dict)
        self.assertEqual(liquidity['error'], 'wallet does not have enough funds')

class TestApproveLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)


    async def test_approve_liquidity(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        self.liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(self.liquidity.txn.id, '.0001')
        self.assertTrue(len(self.exchange.unapproved_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.pending_liquidity.items()) == 1)
        self.assertEqual(self.exchange.pending_liquidity[approved_liquidity.txn.id], approved_liquidity)
        self.assertEqual(self.exchange.pending_liquidity[approved_liquidity.txn.id].txn.id, approved_liquidity.txn.id)

class TestConfirmLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_confirm_liquidity(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        self.liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(self.liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        self.assertTrue(len(self.exchange.unapproved_liquidity.items()) == 0)
        await self.exchange.update_pending_liquidity()
        self.assertTrue(len(self.exchange.pending_liquidity.items()) == 0)
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_a, Decimal('1.4'))
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_b, Decimal('1.285714285714285715'))
        self.assertTrue(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.k, Decimal('1.999999999999999999'))

class TestRemoveLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_remove_liquidity(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        removed_liquidity = await self.exchange.remove_liquidity('ETH', 'CAKE', wallet_address, approved_liquidity.txn.id)
        self.assertTrue(len(self.exchange.unapproved_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.pending_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.unapproved_swaps.items()) == 0)
        self.assertTrue(len(self.exchange.pending_swaps.items()) == 0)
        self.assertTrue(len(self.exchange.unapproved_remove_liquidity.items()) == 1)
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_a, Decimal('1.400000000000000000'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_b, Decimal('1.285714285714285715'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.k, Decimal('1.800000000000000001'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.fees, {})

class TestApproveRemoveLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_approve_remove_liquidity(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        removed_liquidity = await self.exchange.remove_liquidity('ETH', 'CAKE', wallet_address, approved_liquidity.txn.id)
        approved_removed_liquidity = await self.exchange.approve_remove_liquidity(removed_liquidity.txn.id, '.0001')
        self.assertTrue(len(self.exchange.unapproved_remove_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.pending_remove_liquidity.items()) == 1)
        self.assertEqual(self.exchange.pending_remove_liquidity[approved_removed_liquidity.txn.id], approved_removed_liquidity)
        self.assertEqual(self.exchange.pending_remove_liquidity[approved_removed_liquidity.txn.id].txn.id, approved_removed_liquidity.txn.id)

class TestConfirmRemoveLiquidity(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        self.liquidity = await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_confirm_remove_liquidity(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        removed_liquidity = await self.exchange.remove_liquidity('ETH', 'CAKE', wallet_address, approved_liquidity.txn.id)
        approved_removed_liquidity = await self.exchange.approve_remove_liquidity(removed_liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.update_pending_remove_liquidity()
        self.assertTrue(len(self.exchange.unapproved_remove_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.pending_remove_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.liquidity_positions) == 0)

class TestUpdateLiquidityPosition(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        self.liquidity = await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_update_liquidity_position(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swapper_address = self.exchange.wallet_requests.requester.responder.swapper.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        self.swap = await self.exchange.swap(swapper_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        await self.exchange.approve_swap(self.swap.txn.id, '.0001')        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.update_pending_swaps()
        position = await self.exchange.get_position(liquidity.txn.id)
        await self.exchange.update_liquidity_position(position)
        self.assertTrue(isinstance(position, Liquidity))
        self.assertEqual(position.base_fee, Decimal('0.003100775193798450'))
        self.assertEqual(position.quote_fee, Decimal('0.003307656834233252'))        

class TestGetPosition(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        self.liquidity = await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_get_position(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        position = await self.exchange.get_position(liquidity.txn.id)
        self.assertTrue(isinstance(position, Liquidity))
        self.assertEqual(position.txn.id, liquidity.txn.id)
        self.assertEqual(position.txn.transfers[0]['asset'], 'ETH')
        self.assertEqual(position.txn.transfers[1]['asset'], 'CAKE')
        self.assertEqual(position.txn.transfers[0]['for'], Decimal('0.400000000000000000'))
        self.assertEqual(position.txn.transfers[1]['for'], Decimal('0.285714285714285715'))
        self.assertEqual(position.txn.transfers[0]['from'], wallet_address)
        self.assertEqual(position.txn.transfers[0]['to'], self.exchange.router)
        self.assertEqual(position.txn.transfers[1]['to'], self.exchange.router)
        self.assertEqual(position.txn.transfers[1]['from'], wallet_address)
        self.assertEqual(position.txn.transfers[0]['decimals'], 18)
        self.assertEqual(position.txn.transfers[1]['decimals'], 18)
        self.assertEqual(position.max_price, Decimal('0.514285714285714287000'))
        self.assertEqual(position.min_price, Decimal('0.228571428571428572000'))
        self.assertEqual(position.base_fee, 0)
        self.assertEqual(position.quote_fee, 0)

class TestGetPercentOfPool(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)

    async def test_get_percent_of_pool(self):
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        self.liquidity = await self.exchange.pool_add_liquidity(pool, 1, 1)
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        position = await self.exchange.get_position(liquidity.txn.id)
        percent = await self.exchange.get_percent_of_pool(pool, position)
        self.assertEqual(percent['base_pct'], Decimal('0.285714285714285715'))
        self.assertEqual(percent['quote_pct'], Decimal('0.222222222222222223'))

class TestGetAccumulatedFees(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        self.liquidity = await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_get_accumulated_fees(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swapper_address = self.exchange.wallet_requests.requester.responder.swapper.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        self.swap = await self.exchange.swap(swapper_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        await self.exchange.approve_swap(self.swap.txn.id, '.0001')        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.update_pending_swaps()
        await self.exchange.update_liqudity_positions()
        fees = await self.exchange.get_accumulated_fees(liquidity.txn.id)
        self.assertTrue(isinstance(fees, dict))
        self.assertTrue('error' not in fees)
        self.assertEqual(fees['base_fee'], Decimal('0.003100775193798450'))
        self.assertEqual(fees['quote_fee'], Decimal('0.003307656834233252'))   

class TestCollectFees(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)
        self.wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        self.swapper_address = self.exchange.wallet_requests.requester.responder.swapper.wallet.address
        self.liquidity = await self.exchange.provide_liquidity(self.wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(self.liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        self.swap = await self.exchange.swap(self.swapper_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        await self.exchange.approve_swap(self.swap.txn.id, '.0001')        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.update_pending_swaps()
        await self.exchange.update_liqudity_positions()
    
    async def test_collect_fees(self):
        collect_fees = await self.exchange.collect_fees('ETH', 'CAKE', self.wallet_address, self.liquidity.txn.id)
        position = await self.exchange.get_position(self.liquidity.txn.id)
        self.assertTrue(len(self.exchange.unapproved_collect_fees.items()) == 1)
        self.assertTrue(self.liquidity.txn.id in self.exchange.unapproved_collect_fees)
        self.assertEqual(position.base_fee, Decimal('0.003100775193798450')) #NOTE: will still have fees until the collect_fees txn is confirmed
        self.assertEqual(position.quote_fee, Decimal('0.003307656834233252')) 

    async def test_collect_fees_multi_attempt(self):
        position = await self.exchange.get_position(self.liquidity.txn.id)
        collect_fees = await self.exchange.collect_fees('ETH', 'CAKE', self.wallet_address, self.liquidity.txn.id)
        collect_fees_too = await self.exchange.collect_fees('ETH', 'CAKE', self.wallet_address, self.liquidity.txn.id)
        self.assertTrue(type(collect_fees_too) is dict)
        self.assertEqual(collect_fees_too['error'], 'already collecting fees')

class TestApproveCollectFees(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)

    async def test_approve_collect_fees(self):
        wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        swapper_address = self.exchange.wallet_requests.requester.responder.swapper.wallet.address
        liquidity = await self.exchange.provide_liquidity(wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        self.swap = await self.exchange.swap(swapper_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        await self.exchange.approve_swap(self.swap.txn.id, '.0001')        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.update_pending_swaps()
        await self.exchange.update_liqudity_positions()
        position = await self.exchange.get_position(liquidity.txn.id)
        collect_fees = await self.exchange.collect_fees('ETH', 'CAKE', wallet_address, liquidity.txn.id)
        approved_collect_fees = await self.exchange.approve_collect_fees(collect_fees.liquidity_address, '.0001')
        self.assertTrue(len(self.exchange.unapproved_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.pending_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.unapproved_swaps.items()) == 0)
        self.assertTrue(len(self.exchange.pending_swaps.items()) == 0)
        self.assertTrue(len(self.exchange.unapproved_collect_fees.items()) == 0)
        self.assertTrue(len(self.exchange.pending_collect_fees.items()) == 1)
        self.assertEqual(collect_fees.txn.id, approved_collect_fees.txn.id)
        self.assertTrue(position.base_fee > 0)
        self.assertTrue(position.quote_fee > 0)

class TestConfirmCollectFees(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.exchange = await standard_asyncSetUp(self)
        await self.exchange.wallet_requests.requester.init()
        await self.exchange.list_asset('CAKE', 18)
        await self.exchange.create_pool('ETH', 'CAKE', 3)
        pool = self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])]
        await self.exchange.pool_add_liquidity(pool, 1, 1)
        self.wallet_address = self.exchange.wallet_requests.requester.responder.trader.wallet.address
        self.swapper_address = self.exchange.wallet_requests.requester.responder.swapper.wallet.address
        self.liquidity = await self.exchange.provide_liquidity(self.wallet_address, 'ETH', 'CAKE', Decimal('.4'), 3, '.8', '.2')        
        approved_liquidity = await self.exchange.approve_liquidity(self.liquidity.txn.id, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[0].confirmed = True
        await self.exchange.update_pending_liquidity()
        self.swap = await self.exchange.swap(self.swapper_address, 'ETH', 'CAKE', Decimal('0.1'), Decimal('0.0001'))
        await self.exchange.approve_swap(self.swap.txn.id, '.0001')        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[1].confirmed = True
        await self.exchange.update_pending_swaps()
        await self.exchange.update_liqudity_positions()
        self.collect_fees = await self.exchange.collect_fees('ETH', 'CAKE', self.wallet_address, self.liquidity.txn.id)
        self.approved_collect_fees = await self.exchange.approve_collect_fees(self.collect_fees.liquidity_address, '.0001')
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[2].confirmed = True        
        self.exchange.requests.requester.responder.currencies['ETH'].blockchain.mempool.transactions[2].dt = datetime(2023, 1, 1, 0, 0)        

    async def test_confirm_collect_fees(self):
        await self.exchange.update_pending_collect_fees()
        # await self.exchange.update_liqudity_positions()
        position = await self.exchange.get_position(self.liquidity.txn.id)
        self.assertTrue(len(self.exchange.unapproved_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.pending_liquidity.items()) == 0)
        self.assertTrue(len(self.exchange.unapproved_swaps.items()) == 0)
        self.assertTrue(len(self.exchange.pending_swaps.items()) == 0)
        self.assertTrue(len(self.exchange.unapproved_collect_fees.items()) == 0)
        self.assertTrue(len(self.exchange.pending_collect_fees.items()) == 0)
        self.assertEqual(self.collect_fees.txn.id, self.approved_collect_fees.txn.id)
        self.assertEqual(self.liquidity.txn.id, self.collect_fees.liquidity_address)
        self.assertEqual(position.base_fee, 0)
        self.assertEqual(position.quote_fee, 0)
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.fees, {datetime(2023, 1, 1, 0, 0): Decimal('0.006899224806201550')})  
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_a, Decimal('1.290000000000000000'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.reserve_b, Decimal('1.376067934461887847'))
        self.assertEqual(self.exchange.pools['ETHCAKE'][str(self.exchange.fee_levels[3])].amm.k, Decimal('1.775127635455835322'))

    async def test_confirm_no_fee_to_collect(self):
        await self.exchange.update_pending_collect_fees()
        await self.exchange.update_liqudity_positions()
        position = await self.exchange.get_position(self.liquidity.txn.id)        
        re_collect_fees = await self.exchange.collect_fees('ETH', 'CAKE', self.wallet_address, self.liquidity.txn.id)
        self.assertEqual(position.base_fee, 0)
        self.assertEqual(position.quote_fee, 0)        
        self.assertEqual(re_collect_fees['error'], 'no fees to collect')

    async def test_already_collecting_fees(self):
        await self.exchange.update_pending_collect_fees()
        await self.exchange.update_liqudity_positions()
        position = await self.exchange.get_position(self.liquidity.txn.id)        
        re_collect_fees = await self.exchange.collect_fees('ETH', 'CAKE', self.wallet_address, self.liquidity.txn.id)
        self.assertEqual(position.base_fee, 0)
        self.assertEqual(position.quote_fee, 0)        
        self.assertEqual(re_collect_fees['error'], 'no fees to collect')
