import pandas as pd
from typing import Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from decimal import Decimal
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.MemPool import MempoolTransaction
from source.exchange.types.Defi import *
from source.utils.logger import Logger
from source.utils._utils import prec, non_zero_prec, generate_address, string_to_time
from source.crypto.Wallet import Wallet

class TraderDefi():
    def __init__(self, name:str, exchange_requests=None, crypto_requests=None):
        self.name = name
        self.exchange_requests: DefiExchangeRequests = exchange_requests
        self.crypto_requests: CryptoCurrencyRequests = crypto_requests
        self.wallet = Wallet(name, exchange_requests, crypto_requests)
        self.router = '0xDeFiGDWZ2LPsQwWbSSCANRK37qG4N' # the address of the router contract
        self.default_currency = None
        self.fee_levels = None
        self.max_pending_transactions = None
        self.max_price_impact = None
        self.default_deadline = None
        self.current_date = None
        self.assets: Dict[Symbol, Asset] = {}
        self.unapproved_swaps: Dict[Address, Swap] = {}
        self.unapproved_liquidity: Dict[Address, Liquidity] = {}
        self.unapproved_remove_liquidity: Dict[Address, Liquidity] = {}
        self.unapproved_collect_fees: Dict[Address, CollectFee] = {}
        self.max_pending_transactions = 1_000_000
        self.max_unapproved_unconfirmed = 1_000_000
        self.max_unapproved_swaps = 1_000_000                
        self.logger = Logger(name, 20)

    def __repr__(self):
        return f'<TraderDefi: {self.name}>'

    def __str__(self):
        return f'<TraderDefi: {self.name}>'
    
    async def get_fee_levels(self) -> list:
        fee_levels = await self.exchange_requests.get_fee_levels()
        return fee_levels
    
    async def get_pools(self) -> dict:
        pools = await self.exchange_requests.get_pools()
        return pools
    
    async def get_pool(self, base, quote, fee_pct) -> Pool:
        pool = await self.exchange_requests.get_pool(base, quote, fee_pct)
        return Pool(**pool)

    async def get_price(self, base, quote, pool_fee_pct, base_amount) -> Decimal:
        price = await self.exchange_requests.get_price(base, quote, pool_fee_pct, base_amount)
        return price

    async def get_assets(self) -> dict:
        assets = await self.exchange_requests.get_assets()
        if 'error' in assets:
            return assets
        for symbol, asset in assets.items():
            self.assets[symbol] = Asset(**asset)
        return self.assets

    async def connect(self):
        """
        Connects to the DeFi exchange.
        """
        self.logger.info('connecting...')
        params = await self.exchange_requests.connect()
        if 'error' in params:
            return params
        self.default_currency = Currency(**params['default_currency'])
        self.fee_levels = params['fee_levels']
        self.max_pending_transactions = params['max_pending_transactions']
        self.max_price_impact = params['max_price_impact']
        self.default_deadline = params['default_deadline']
        self.logger.info('connected')

    async def check_assets(self, base:str, quote:str) -> dict:
        if base not in self.assets:
            self.logger.error(f'base asset does not exist, base: {base}')
            return {'error': 'base asset does not exist'}
        if quote not in self.assets:
            self.logger.error(f'quote asset does not exist, quote: {quote}')
            return {'error': 'quote asset does not exist'}
        if base == quote:
            self.logger.error(f'cannot create, base and quote assets are the same')
            return {'error': 'cannot create, base and quote assets are the same'}
        return {'success': 'assets exist'}

    async def find_pool(self, base:str, quote:str, fee_level=2) -> Pool:
        checked_assets = await self.check_assets(base, quote)
        if 'error' in checked_assets:
            return checked_assets

        if fee_level < 0 or fee_level >= len(self.fee_levels):
            self.logger.error(f'fee level does not exist, fee_level: {fee_level}')
            return {'error': 'fee level does not exist'}
        
        pool_fee_pct = PoolFee(self.fee_levels[fee_level])
        if base+quote in self.pools:
            if str(pool_fee_pct) in self.pools[base+quote]:
                # pool already exists, return the existing pool
                return self.pools[base+quote][str(pool_fee_pct)]
        else: 
            self.logger.error(f'pool does not exist, base: {base}, quote: {quote}')
            return {'error': 'pool does not exist'}
      
    async def select_pool(self, base:str, quote:str) -> Pool:
        """
        Returns the pool with the most liquidity for a given base and quote pair.
        """
        pools = await self.get_pools(base, quote)
        checked_assets = await self.check_assets(base, quote)
        if 'error' in checked_assets:
            return checked_assets
        
        if base+quote not in pools:
            self.logger.error(f'pool does not exist, base: {base}, quote: {quote}')
            return {'error': 'pool does not exist'}
        
        max_reserves = 0
        selected_pool = None
        for pool in pools[base+quote].values():
            reserves = pool['amm']['reserve_a'] + pool['amm']['reserve_b']
            if reserves > max_reserves:
                max_reserves = reserves
                selected_pool = pool
        if selected_pool is None:
            self.logger.error(f'no active pools found, base: {base}, quote: {quote}')
            return {'error': 'no active pools found'}
        return Pool(**selected_pool)

    async def check_swap(self, swap: Swap, price: Decimal) -> dict:
        quote_qty = swap.txn.transfers[1]['for']
        slippage = prec(swap.slippage, 3)
        max_price = quote_qty * (1 + slippage)
        min_price = quote_qty * (1 - slippage)
        if price < min_price:
            self.logger.error(f'price slipped too low, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            return {'error': 'price too low'}
        if price > max_price:
            self.logger.error(f'price slipped too high, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            return {'error': 'price too high'}
        return {'success': 'swap approved'}

    async def swap(self, base: str, quote:str, base_qty: Decimal, slippage='.05', deadline=30_000) -> Swap:
        """
        Swaps a base asset for a quote asset.
        
        deadline is number of seconds to wait before cancelling the transaction.
        """
        self.logger.info(f'swap, base: {base}, quote: {quote}, base_qty: {base_qty}, slippage: {slippage}, deadline: {deadline}')

        pool = await self.select_pool(base, quote)
        if isinstance(pool, dict) and 'error' in pool: 
            return pool          
        
        base_qty = non_zero_prec(base_qty, self.assets[base].decimals)
        fee_amount = prec(prec(pool.fee,3) * base_qty, self.wallet.chain['decimals'])
        amount = non_zero_prec(base_qty, self.assets[base].decimals)
        total_amount = prec(amount + fee_amount, self.assets[base].decimals)
        quote_qty = await self.get_price(base, quote, pool.fee, total_amount)
        if type(quote_qty) is dict and 'error' in quote_qty:    
            return quote_qty
        price = prec(quote_qty, self.assets[quote].decimals)

        # get the price of the pool after the swap takes place (ie copy the pool amt, add the base_qty to the and remove the quote qty, balance and recalulate the price)
        future_reserve_a = prec(pool.amm['reserve_a'] + base_qty, self.assets[base].decimals)
        future_reserve_b = prec(pool.amm['reserve_b'] - price, self.assets[quote].decimals) 
        k = non_zero_prec(future_reserve_a * future_reserve_b)
        new_reserve_a = non_zero_prec(future_reserve_a + base_qty)
        new_reserve_b = non_zero_prec(k /new_reserve_a) 
        future_price = prec(future_reserve_b - new_reserve_b, self.assets[quote].decimals)
        price_impact = prec(abs(future_price - price) / price, 3)
        if price_impact > self.max_price_impact:
            self.logger.error(f'price impact too high, price_impact: {price_impact}, max_price_impact: {self.max_price_impact}')
            return {'error': 'price impact too high'}
        agent_wallet = str(self.wallet.address)
        transfers = [
            {'asset': base, 'address': self.assets[base].address, 'from': agent_wallet, 'to': self.router, 'for': total_amount, 'decimals': self.assets[base].decimals},
            {'asset': quote, 'address': self.assets[quote].address, 'from': self.router, 'to': agent_wallet, 'for': price, 'decimals': self.assets[quote].decimals}
        ]
        swap_address = generate_address()
        transaction = MempoolTransaction(id=swap_address, asset=self.wallet.chain['symbol'], fee=0, amount=0, sender=agent_wallet, recipient=self.router, dt=self.dt, transfers=transfers)
        swap = Swap(pool.fee, fee_amount, slippage, deadline, transaction)
        self.unapproved_swaps[swap_address] = swap
        #TODO: send the transaction directly to the wallet for signing?
        # self.wallet.signature_requests.append(transaction.to_dict())
        return swap

    async def send_approved_swap(self, txn) -> Swap:
        """
        If the criteria is met, send an approved swap to the exchange.
        """
        #NOTE: may be able to remove upapproved swaps dict, if we directly call methods from the trader... need to think of the cases for keeping and removing
        swap_address = str(txn['id'])
        if swap_address not in self.unapproved_swaps:
            self.logger.error(f'swap not found, swap_address: {swap_address}')
            return {'error': 'swap not found'}
        approved_swap = self.unapproved_swaps.pop(swap_address)
        base = approved_swap.txn.transfers[0]['asset']
        quote = approved_swap.txn.transfers[1]['asset']
        base_qty = approved_swap.txn.transfers[0]['for']
        pool_fee_pct = approved_swap.pool_fee_pct
        approved_swap.txn.fee = prec(txn['fee'], self.wallet.chain['decimals'])
        pool = await self.get_pool(base, quote, pool_fee_pct)
        price = prec(pool['amm']['get_price'](base_qty), self.assets[quote].decimals)
        check_swap = await self.check_swap(approved_swap, price)
        if 'error' in check_swap:
            self.crypto_requests.cancel_transaction(approved_swap.txn.id)
        
        #NOTE: once signed and checked, send the swap to the exchange, this allows it to be re-checked and cancelled without wallet needing to be connected
        self.exchange_requests.add_pending_swap(approved_swap.to_dict())

        # exchange and wallet both listen for confirmation
        return approved_swap

    async def provide_liquidity(self, agent_wallet: Address, base: str, quote: str, amount: Decimal, fee_level=-1, high_range='.8', low_range='.2') -> Liquidity:
        """
        Provides liquidity to a pool, in exchange for LP tokens.
        """
        self.logger.info(f'provide_liquidity, agent_wallet: {agent_wallet}, base: {base}, quote: {quote}, amount: {amount}, fee_level: {fee_level}, high_range: {high_range}, low_range: {low_range}')
        amount = prec(amount, self.assets[base].decimals)
        agent_wallet = str(agent_wallet)

        if fee_level < 0:
            pool = await self.select_pool(base, quote)
        else:
            pool = await self.find_pool(base, quote, fee_level)

        if isinstance(pool, dict) and 'error' in pool:
            return pool    

        if not pool.is_active:
            return {'error': 'pool is inactive'}

        liquidity_address = generate_address()
        price = non_zero_prec(pool['amm']['get_price'](amount), self.assets[quote].decimals)
        max_price = price * (1 + prec(high_range, 3))
        min_price = price * (1 - prec(low_range, 3))
        transfers = [
            {'asset': base, 'address': self.assets[base].address, 'from': agent_wallet, 'to': self.router, 'for': amount, 'decimals': self.assets[base].decimals},
            {'asset': quote, 'address': self.assets[quote].address, 'from': agent_wallet, 'to': self.router, 'for': price, 'decimals': self.assets[quote].decimals},
            {'asset': liquidity_address, 'address': pool.lp_token, 'from': self.router, 'to': agent_wallet, 'for': 0, 'decimals': 1} #LP token, the `asset` is the address to the Liquidity position address so that the wallet has a record of the liquidity position
        ]
        transaction = MempoolTransaction(id=liquidity_address, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, dt=self.dt, transfers=transfers)
        self.unapproved_liquidity[liquidity_address] = Liquidity(agent_wallet, max_price, min_price, pool.fee, transaction) 
        self.logger.info(f'provide_liquidity, unapproved_liquidity: {self.unapproved_liquidity}')
        return self.unapproved_liquidity[liquidity_address]

    async def send_approved_liquidity(self, txn) -> Liquidity:
        """
        Send an approved liquidity transaction to the exchange.
        """
        liquidity_address = str(txn['id'])
        self.logger.info(f'send_approved_liquidity, liquidity_address: {liquidity_address}')
        if liquidity_address not in self.unapproved_liquidity:
            self.logger.error(f'liquidity not found, liquidity_address: {liquidity_address}')
            return {'error': 'liquidity not found'}
        approved_liquidity = self.unapproved_liquidity.pop(liquidity_address)
        approved_liquidity.txn.fee = prec(txn['fee'], self.wallet.chain['decimals'])
        
        self.exchange_requests.add_pending_liquidity(approved_liquidity.to_dict())
        return approved_liquidity

    async def remove_liquidity(self, base: str, quote: str, agent_wallet: Address, position_address: Address) -> Liquidity:
        """
        Removes liquidity from a pool.
        """
        agent_wallet = str(agent_wallet)
        position_address = str(position_address)
        position = await self.exchange_requests.get_position(position_address)
        if type(position) is dict and 'error' in position:
            return {'error': 'liquidity position does not exist'}
        position = Liquidity(**position)
        remove_liquidity_address = generate_address()
        transfers = [
            {'asset': base, 'address': self.assets[base].address, 'from': self.router, 'to': agent_wallet, 'for': position.txn.transfers[0]['for'], 'decimals': self.assets[base].decimals},
            {'asset': quote, 'address': self.assets[quote].address, 'from': self.router, 'to': agent_wallet, 'for': position.txn.transfers[1]['for'], 'decimals': self.assets[quote].decimals }
        ]
        transaction = MempoolTransaction(id=remove_liquidity_address, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, dt=self.dt, transfers=transfers)
        self.unapproved_remove_liquidity[remove_liquidity_address] = Liquidity(position_address, position.max_price, position.min_price, position.pool_fee_pct, transaction) # the `owner` is the address of the liquidity being removed
        return self.unapproved_remove_liquidity[remove_liquidity_address]

    async def approve_remove_liquidity(self, txn) -> Liquidity:
        """
        Send an approved remove liquidity transaction to the exchange.
        """
        remove_liquidity_address = str(txn['id'])
        self.logger.info(f'send_approved_liquidity, remove_liquidity_address: {remove_liquidity_address}')
        if remove_liquidity_address not in self.unapproved_remove_liquidity:
            self.logger.error(f'remove_liquidity not found, remove_liquidity_address: {remove_liquidity_address}')
            return {'error': 'liquidity not found'}
        approved_remove_liquidity = self.unapproved_liquidity.pop(remove_liquidity_address)
        approved_remove_liquidity.txn.fee = prec(txn['fee'], self.wallet.chain['decimals'])
        
        self.exchange_requests.add_pending_remove_liquidity(approved_remove_liquidity.to_dict())
        return approved_remove_liquidity

    async def get_accumulated_fees(self, liquidity_address: Address) -> dict:
        position = await self.exchange_requests.get_position(liquidity_address)
        if type(position) is dict and 'error' in position:
            return position
        return {"base_fee": position['base_fee'], "quote_fee": position['quote_fee']}

    async def collect_fees(self, base: str, quote: str, agent_wallet:Address, liquidity_address: Address) -> CollectFee:
        """
        Collects the fees accumulated in a liquidity position.

         NOTE: uses the liquidity_address as the id for the collect fees transaction. This way we can quickly look up if a multi-collect on the same liquidity position has been attempted.
        """
        liquidity_address = str(liquidity_address)
        agent_wallet = str(agent_wallet)
        position = await self.exchange_requests.get_position(liquidity_address)
        if type(position) is dict and 'error' in position:
            return {'error': 'liquidity position does not exist'}
        position = Liquidity(**position)

        
        collect_fees_address = generate_address()

        if position.base_fee == 0 and position.quote_fee == 0:
            return {'error': 'no fees to collect'}

        transfers = [
            {'asset': base, 'address': self.assets[base].address, 'from': self.router, 'to': agent_wallet, 'for': position.base_fee, 'decimals': self.assets[base].decimals},
            {'asset': quote, 'address': self.assets[quote].address, 'from': self.router, 'to': agent_wallet, 'for': position.quote_fee, 'decimals': self.assets[quote].decimals}
        ]
        transaction = MempoolTransaction(id=collect_fees_address, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, dt=self.dt, transfers=transfers)
        self.unapproved_collect_fees[liquidity_address] = CollectFee(liquidity_address, position.base_fee, position.quote_fee, position.pool_fee_pct, transaction)
        return self.unapproved_collect_fees[liquidity_address]
    
    async def approve_collect_fees(self, txn) -> CollectFee:
        """
        Approves a collect fees transaction.
        """
        collect_fees_address = str(txn['id'])
        self.logger.info(f'send_approved_collect_fees, collect_fees_address: {collect_fees_address}')
        if collect_fees_address not in self.unapproved_collect_fees:
            self.logger.error(f'collect_fees not found, collect_fees_address: {collect_fees_address}')
            return {'error': 'collect_fees not found'}
        approved_collect_fees = self.unapproved_collect_fees.pop(collect_fees_address)
        approved_collect_fees.txn.fee = prec(txn['fee'], self.wallet.chain['decimals'])
        self.exchange_requests.add_pending_collect_fees(approved_collect_fees.to_dict())
        return approved_collect_fees

    async def next():
        pass