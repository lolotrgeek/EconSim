import sys, os
from uuid import uuid4 as UUID
from collections import namedtuple
from decimal import Decimal
from typing import Dict, List
from .types.Defi import *
from .components.ConstantProduct import ConstantProduct
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.WalletRequests import WalletRequests
from source.crypto.MemPool import MempoolTransaction
from source.utils.logger import Logger
from source.utils._utils import prec, non_zero_prec, generate_address
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class DefiExchange():
    """
    A Crypto Exchange that uses an Automated Market Maker (AMM) to match orders.

    It creates pools of assets, wherein agents provide liquidity and receive rewards. 
    Orders move assets from the pool wallet to the user's wallet, every transaction is processed on a single blockchain.

    There are no limit orders, only market orders called "swaps".

    """
    def __init__(self, chain = None, datetime= None, crypto_requester=None, wallet_requester=None):
        self.chain = chain # the blockchain that the exchange is running on
        self.dt = datetime
        self.requester: CryptoCurrencyRequests = crypto_requester
        self.wallet_requester: WalletRequests = wallet_requester
        self.router = generate_address()
        self.default_currency: Currency = None
        self.assets: Dict[Symbol, Asset] = {}
        self.fee_levels = [Decimal('0.01'), Decimal('0.05'), Decimal('0.25'), Decimal('0.1')]
        self.pools: Dict[Pair, Dict[PoolFee, Pool]] = {}        
        self.swaps = []
        self.liquidity_positions: Dict[Address, Liquidity] = {}
        self.unapproved_swaps: Dict[Address, Swap] = {}
        self.unapproved_liquidity: Dict[Address, Liquidity] = {}
        self.unapproved_remove_liquidity: Dict[Address, Liquidity] = {}
        self.unapproved_collect_fees: Dict[Address, CollectFee] = {}
        self.pending_swaps: Dict[Address, Swap] = {}
        self.pending_liquidity: Dict[Address, Liquidity] = {}
        self.pending_remove_liquidity: Dict[Address, Liquidity] = {}        
        self.pending_collect_fees: Dict[Address, CollectFee] = {}
        self.max_pending_transactions = 1_000_000
        self.max_unapproved_unconfirmed = 1_000_000
        self.max_unapproved_swaps = 1_000_000
        self.max_pairs = 10000
        self.max_assets = 10000
        self.logger = Logger('DefiExchange', 30)

    async def start(self):
        self.chain = self.requester.connect(self.chain)
        if 'error' in self.chain:
            self.logger.error(f'cannot connect to chain, error: {self.chain["error"]}')
            return {'error': 'cannot connect to chain'}
        if self.chain is isinstance(dict): 
            self.default_currency = Currency(self.chain['symbol'], decimals= self.chain['decimals'])
            self.assets[self.default_currency.symbol] = Asset(self.router)

        assets = self.requester.get_assets()
        if 'error' in assets:
            self.logger.error(f'cannot get assets, error: {assets["error"]}')
            return {'error': 'cannot get assets'}
        for asset in assets:
            await self.list_asset(asset['symbol'], asset['decimals'])

    async def next(self):
        for address, pending_liquidity in self.pending_liquidity:
            address: Address = str(address)
            pending_liquidity: Liquidity
            transaction = await self.requester.get_transaction(asset=self.default_currency.symbol, id=address)
            if not transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in transaction:
                continue
            if transaction['confirmed']:
                base = pending_liquidity.pair.base
                quote = pending_liquidity.pair.quote
                base_qty = pending_liquidity.txn.transfers[0]['for']
                quote_qty = pending_liquidity.txn.transfers[1]['for']
                pool = self.pools[base+quote][pending_liquidity.pool_fee_pct]
                await self.pool_add_liquidity(pool, base_qty, quote_qty)
                pool.amm.balance(base_qty)                
                self.liquidity_positions[address] = pending_liquidity
                self.pending_liquidity.pop(address) 

        for address, pending_remove_liquidity in self.pending_remove_liquidity:
            address: Address = str(address)
            pending_remove_liquidity: Liquidity
            transaction = await self.requester.get_transaction(asset=self.default_currency.symbol, id=address)
            if not transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in transaction:
                continue
            if transaction['confirmed']:
                base = pending_remove_liquidity.pair.base
                quote = pending_remove_liquidity.pair.quote
                base_qty = pending_remove_liquidity.txn.transfers[0]['for']
                quote_qty = pending_remove_liquidity.txn.transfers[1]['for']
                pool = self.pools[base+quote][pending_remove_liquidity.pool_fee_pct]
                await self.pool_remove_liquidity(pool, base_qty, quote_qty)
                pool.amm.balance(base_qty)
                self.liquidity_positions[pending_remove_liquidity.owner].pop(address) # the `owner` is the address of the liquidity being removed

        for address, pending_swap in self.pending_swaps:
            address: Address = str(address)
            pending_swap: Swap
            transaction = await self.requester.get_transaction(asset=self.default_currency.symbol, id=address)
            if not transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in transaction:
                continue
            if not transaction['confirmed']:
                base = pending_swap.pair.base
                quote = pending_swap.pair.quote
                pool = self.pools[base+quote][pending_swap.pool_fee_pct]
                base_qty = pending_swap.txn.transfers[0]['for']
                quote_qty = pending_swap.txn.transfers[1]['for']
                price = pool.amm.get_price(base_qty)
                slippage = pending_swap.slippage
                if price < quote_qty * (1 - slippage):
                    self.logger.warning(f'price slipped too low, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
                    await self.requester.cancel_transaction(self.default_currency.symbol, transaction['id'])
                if price > quote_qty * (1 + slippage) :
                    self.logger.warning(f'price slipped too high, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
                    await self.requester.cancel_transaction(self.default_currency.symbol, transaction['id'])
                    return {'error': 'slippage, price too high'}            
            if transaction['confirmed']:
                await self.pool_swap_liquidity(base_qty, quote_qty, pending_swap.fee_amount)
                self.swaps.append(pending_swap)
                pool.amm.balance(base_qty)    
                self.pending_swaps.pop(address)

        for address, pending_collect_fees in self.pending_collect_fees:
            address: Address = str(address)
            pending_collect_fees: CollectFee
            transaction = await self.requester.get_transaction(asset=self.default_currency.symbol, id=address)
            if not transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in transaction:
                continue
            if transaction['confirmed']:
                base = pending_collect_fees.txn.transfers[0]['asset']
                quote = pending_collect_fees.txn.transfers[1]['asset']
                pool = self.pools[base+quote][pending_collect_fees.pool_fee_pct]
                await self.pool_remove_liquidity(pool, pending_collect_fees.base_fee, pending_collect_fees.quote_fee)
                pool.amm.balance(pending_collect_fees.base_fee)
                self.pending_collect_fees.pop(address)

        for address, liquidity in self.liquidity_positions:
            address: Address = str(address)
            liquidity:Liquidity
            pool = await self.get_pool(liquidity.pair.base, liquidity.pair.quote, liquidity.pool_fee_pct)
            percent_of_pool = await self.get_percent_of_pool(pool, address)
            if 'error' in percent_of_pool:
                continue
            accumulate_base_fee = prec(pool.amm.reserve_a * percent_of_pool, self.assets[liquidity.pair.base].decimals)
            accumuluate_quote_fee = prec(pool.amm.reserve_b * percent_of_pool, self.assets[liquidity.pair.quote].decimals)
            liquidity.base_fee += accumulate_base_fee
            liquidity.quote_fee += accumuluate_quote_fee

    async def signature_response(self, agent_wallet: Address, decision: bool, id: Address):
        if id in self.unapproved_swaps and self.unapproved_swaps[id].txn.sender == agent_wallet:
            if decision == True:
                await self.approve_swap(id)
                return {'swap_approved': id}
            else:
                self.unapproved_swaps.pop(id)
                return {'swap_rejected': id}
        elif id in self.unapproved_liquidity and self.unapproved_liquidity[id].txn.sender == agent_wallet:
            if decision == True:
                await self.approve_liquidity(id)
                return {'liquidity_approved': id}
            else:
                self.unapproved_liquidity.pop(id)
                return {'liquidity_rejected': id}
        elif id in self.unapproved_remove_liquidity and self.unapproved_remove_liquidity[id].txn.sender == agent_wallet:
            if decision == True:
                await self.approve_remove_liquidity(id)
                return {'remove_liquidity_approved': id}
            else:
                self.unapproved_remove_liquidity.pop(id)
                return {'remove_liquidity_rejected': id}
        elif id in self.unapproved_collect_fees and self.unapproved_collect_fees[id].txn.sender == agent_wallet:
            if decision == True:
                await self.approve_collect_fees(id)
                return {'collect_fees_approved': id}
            else:
                self.unapproved_collect_fees.pop(id)
                return {'collect_fees_rejected': id}
        return {'error': 'transaction not found'}

    async def list_asset(self, symbol: str, decimals=8) -> dict:
        if symbol == self.default_currency.symbol:
            return {'error': 'cannot list default_quote_currency'}
        if len(self.assets) >= self.max_assets:
            return {'error': 'cannot list, max_assets_reached'}
        if symbol in self.assets:
            return {'error': 'cannot list, asset already exists'}        
        minimum = prec('.00000000000000000001', decimals)
        address = generate_address()
        self.assets[symbol] = Asset(address, decimals, minimum, True) 
        return {'asset_listed': symbol}

    async def get_assets(self) -> dict:
        return self.assets

    async def create_pool(self, base:str, quote:str, fee_level=2) -> Pool:
        if base not in self.assets:
            return {'error': 'base asset does not exist'}
        if quote not in self.assets:
            return {'error': 'quote asset does not exist'}
        if len(self.pools) >= self.max_pairs:
            return {'error': 'cannot create, max_pairs_reached'}        
        if base == quote:
            return {'error': 'cannot create, base and quote assets are the same'}
        if fee_level < 0 or fee_level >= len(self.fee_levels):
            return {'error': 'fee level does not exist'}
        
        pool_fee_pct = PoolFee(self.fee_levels[fee_level])
        if base+quote in self.pools:
            if str(pool_fee_pct) in self.pools[base+quote]:
                return {'error': 'cannot create, pool already exists'}
        else:
            self.pools[base+quote] = {}
        new_pool = Pool(str(pool_fee_pct), base, quote, ConstantProduct(0,0))
        self.pools[base+quote][str(pool_fee_pct)] = new_pool
        return new_pool

    async def select_pool_fee_pct(self, base:str, quote:str) -> str:
        """
        Returns the fee from the pool with the most liquidity for a given base and quote pair.

        NOTE: the fee also provides the key to finding pools in the self.pools dict. 

        `i.e. ['BTCUSDT']['.01'] represents a pool with a fee of .01 for the BTC/USDT pair.`
        """
        if base+quote not in self.pools:
            return {'error': 'pool does not exist'}
        max_reserves = 0
        selected_pool_fee_pct = None
        for fee_level, pool in self.pools[base+quote].items():
            if pool.is_active:
                reserves = pool.amm.get_total_reserves()
                if reserves > max_reserves:
                    max_reserves = reserves
                    selected_pool_fee_pct = fee_level
        if selected_pool_fee_pct is None:
            return {'error': 'no active pools found'}
        return selected_pool_fee_pct

    async def pool_swap_liquidity(self, pool: Pool, base_qty: Decimal, quote_qty: Decimal, pool_fee_pct_amount: Decimal):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        pool.amm.reserve_a -= base_qty
        pool.amm.reserve_b += quote_qty
        pool.amm.reserve_a += pool_fee_pct_amount

    async def pool_add_liquidity(self, pool: Pool, base_qty, quote_qty):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        pool.amm.reserve_a += base_qty
        pool.amm.reserve_b += quote_qty

    async def pool_remove_liquidity(self, pool: Pool, base_qty, quote_qty):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        pool.amm.reserve_a -= base_qty
        pool.amm.reserve_b -= quote_qty

    async def get_pools(self):
        pools = {}
        for pair, fee_levels in self.pools.items():
            pools[pair] = {}
            for fee, pool in fee_levels.items():
                if pool.is_active:
                    pools[pair][fee] = pool
        return pools

    async def get_pool(self, base: str, quote: str, pool_fee_pct: PoolFee) -> Pool:
        if base+quote not in self.pools:
            return {'error': 'pool does not exist'}
        if str(pool_fee_pct) not in self.pools[base+quote]:
            return {'error': 'pool fee does not exist'}
        pool = self.pools[base+quote][str(pool_fee_pct)]        
        return pool

    async def get_pool_liquidity(self, base: str, quote: str, pool_fee_pct: PoolFee) -> dict:
        pool = await self.get_pool(base, quote, str(pool_fee_pct))
        if not pool.is_active:
            return {'error': 'pool is inactive'} 
        return {base: pool.amm.reserve_a, quote: pool.amm.reserve_b}

    async def get_liquidity_positions(self) -> dict:
        return self.liquidity_positions
    
    async def get_fee_levels(self) -> list:
        return self.fee_levels

    async def agent_has_funds(self, agent_wallet: Address, asset:str, amount: Decimal) -> bool:
        if asset not in self.assets:
            self.logger.error(f'asset does not exist, asset: {asset}')
            return False
        if amount < self.assets[asset].min_qty:
            self.logger.error(f'amount too small, asset: {asset}, amount: {amount}')
            return False
        if amount > (await self.wallet_requester.get_balance(str(agent_wallet), asset)):
            self.logger.error(f'insufficient funds, agent_wallet: {agent_wallet}, asset: {asset}, amount: {amount}')
            return False
        return True

    async def swap(self, agent_wallet: Address, base: str, quote:str, base_qty: Decimal, slippage='.05') -> dict:
        """
        Swaps a base asset for a quote asset.
        """
        if len(self.pending_swaps) >= self.max_pending_transactions:
            return {'error': 'max_pending_transactions_reached'}

        if len(self.unapproved_swaps) >= self.max_unapproved_swaps:
            self.unapproved_swaps.pop(self.unapproved_swaps[0])

        pool_fee_pct = await self.select_pool_fee_pct(base, quote)
        if 'error' in pool_fee_pct: return pool_fee_pct          
        pool = self.pools[base+quote][pool_fee_pct]      
  
        base_qty = non_zero_prec(base_qty, self.assets[base].decimals)
        fee_amount = prec(prec(pool.fee,3) * base_qty, self.default_currency.decimals)
        amount = non_zero_prec(base_qty, self.assets[base].decimals)
        total_amount = prec(amount + fee_amount, self.default_currency.decimals)
        price = pool.amm.get_price(amount)

        has_funds = await self.agent_has_funds(agent_wallet, base, total_amount)
        if not has_funds: 
            #TODO: block agent from making swaps until they have enough funds
            return {'error': 'agent does not have enough funds'}
            
        #TODO: send a confirmation to agent (not wallet) to confirm the swap
        transfers = [
            {'asset': base, 'address': self.assets[base]['address'], 'from': agent_wallet, 'to': self.router, 'for': total_amount},
            {'asset': quote, 'address': self.assets[quote]['address'], 'from': self.router, 'to': agent_wallet, 'for': price}
        ]
        swap_address = generate_address()
        transaction = MempoolTransaction(id=swap_address, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, transfers=transfers)
        self.unapproved_swaps[swap_address] = Swap(pool_fee_pct, fee_amount, slippage, transaction)
        await self.wallet_requester.request_signature(agent_wallet, transaction.to_dict())
        return {swap_address: self.unapproved_swaps[swap_address]}

    async def approve_swap(self, swap_address: Address, network_fee:str) -> Swap:
        """
        Approves a swap, if the price is within the slippage range.
        """
        swap_address = str(swap_address)
        if swap_address not in self.unapproved_swaps:
            return {'error': 'swap not found'}
        approved_swap = self.unapproved_swaps.pop(swap_address)
        base = approved_swap.txn.transfers[0]['asset']
        quote = approved_swap.txn.transfers[1]['asset']
        base_qty = approved_swap.txn.transfers[0]['for']
        quote_qty = approved_swap.txn.transfers[1]['for']
        slippage = approved_swap.slippage
        pool_fee_pct = approved_swap.pool_fee_pct

        price = self.pools[base+quote][pool_fee_pct].amm.get_price(base_qty)

        if price < quote_qty * (1 - slippage):
            self.logger.error(f'price slipped too low, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            return {'error': 'slippage, price too low'}
        if price > quote_qty * (1 + slippage) :
            self.logger.error(f'price slipped too high, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            return {'error': 'slippage, price too high'}
        
        approved_swap.txn.transfers[1]['for'] = price
        approved_swap.txn.fee = network_fee
        pending_transaction = await self.requester.add_transaction(**approved_swap.txn.to_dict())
        if('error' in pending_transaction or pending_transaction['sender'] == 'error' ):
            self.logger.error('add_transaction_failed', pending_transaction)
            return {'error': 'add_transaction_failed'}
        self.pending_swaps[swap_address] = approved_swap
        return approved_swap

    async def provide_liquidity(self, agent_wallet: Address, base: str, quote: str, amount: Decimal, fee_level=-1, high_range='.8', low_range='.2') -> dict:
        """
        Provides liquidity to a pool, in exchange for LP tokens.
        """
        amount = prec(amount, self.assets[base].decimals)
        agent_wallet = str(agent_wallet)
        has_base_funds = await self.agent_has_funds(agent_wallet, base, amount)
        if not has_base_funds:
            # TODO: block agent from providing liquidity until they have enough funds 
            return {'error': 'agent does not have enough funds'}
        await self.create_pool(base, quote, fee_level)
        if fee_level >= len(self.fee_levels):
            return {'error': 'fee level does not exist'}        
        if fee_level < 0:
            pool_fee_pct = await self.select_pool_fee_pct(base, quote)
            if 'error' in pool_fee_pct: return pool_fee_pct          
            pool = self.pools[base+quote][pool_fee_pct]
        if fee_level > 0:
            fee = self.fee_levels[fee_level]
            pool = self.pools[base+quote][str(fee)]
        if not pool.is_active:
            return {'error': 'pool is inactive'}            

        liquidity_address = generate_address()
        price = prec(pool.amm.get_price(amount), self.assets[quote].decimals)
        has_quote_funds = await self.agent_has_funds(agent_wallet, quote, price)
        if not has_quote_funds:
            # TODO: block agent from providing liquidity until they have enough funds
            return {'error': 'agent does not have enough funds'}
        max_price = price * (1 + high_range)
        min_price = price * (1 - low_range)
        transfers = [
            {'asset': base, 'address': self.assets[base]['address'], 'from': agent_wallet, 'to': self.router, 'for': amount},
            {'asset': quote, 'address': self.assets[quote]['address'], 'from': agent_wallet, 'to': self.router, 'for': price},
            {'asset': liquidity_address, 'address': pool.lp_token, 'from': self.router, 'to': agent_wallet, 'for': 0} #LP token, the `asset` is the address to the Liquidity position address so that the wallet has a record of the liquidity position
        ]
        transaction = MempoolTransaction(id=liquidity_address, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, transfers=transfers)
        self.unapproved_liquidity[liquidity_address] = Liquidity(liquidity_address, max_price, min_price, pool_fee_pct, transaction) # the `owner` is the address of the liquidity being removed
        return {liquidity_address: self.unapproved_liquidity[liquidity_address]}
    
    async def approve_liquidity(self, liquidity_address: Address):
        """
        Approves a liquidity position.
        """
        liquidity_address = str(liquidity_address)
        if liquidity_address not in self.unapproved_liquidity:
            return {'error': 'liquidity not found'}
        approved_liquidity = self.unapproved_liquidity.pop(liquidity_address)

        pending_transaction = await self.requester.add_transaction(**approved_liquidity.txn.to_dict())
        if('error' in pending_transaction or pending_transaction['sender'] == 'error' ):
            self.logger.error('add_transaction_failed', pending_transaction, pending_transaction)
            return {'error': 'add_transaction_failed'}
        
        self.pending_liquidity[liquidity_address] = approved_liquidity
        return approved_liquidity

    async def remove_liquidity(self, base: str, quote: str, agent_wallet: Address, position_address: Address):
        """
        Removes liquidity from a pool, in exchange for the assets in the pool.
        """
        agent_wallet = str(agent_wallet)
        position_address = str(position_address)
        if len(self.pending_liquidity) >= self.max_pending_transactions:
            return {'error': 'max_pending_transactions_reached'}
        if position_address not in self.liquidity_positions:
            return {'error': 'liquidity position does not exist'}
        liquidity_to_remove = self.liquidity_positions[position_address]
        remove_liquidity_address = generate_address()
        transfers = [
            {'asset': base, 'address': self.assets[base]['address'], 'from': self.router, 'to': agent_wallet, 'for': liquidity_to_remove.txn.transfers[0]['for']},
            {'asset': quote, 'address': self.assets[quote]['address'], 'from': self.router, 'to': agent_wallet, 'for': liquidity_to_remove.txn.transfers[1]['for']}
        ]
        transaction = MempoolTransaction(id=remove_liquidity_address, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, transfers=transfers)
        self.unapproved_remove_liquidity[remove_liquidity_address] = Liquidity(agent_wallet, liquidity_to_remove.max_price, liquidity_to_remove.min_price, liquidity_to_remove.pool_fee_pct, transaction)
        return {remove_liquidity_address: self.unapproved_remove_liquidity[remove_liquidity_address]}

    async def approve_remove_liquidity(self, remove_liquidity_address:Address, network_fee: str):
        """
        Approves a remove liquidity transaction.
        """
        remove_liquidity_address = str(remove_liquidity_address)
        if remove_liquidity_address not in self.unapproved_remove_liquidity:
            return {'error': 'liquidity not found'}
        approved_remove_liquidity = self.unapproved_liquidity.pop(remove_liquidity_address)
        approved_remove_liquidity.txn.fee = network_fee
        pending_transaction = await self.requester.add_transaction(**approved_remove_liquidity.txn.to_dict())
        if('error' in pending_transaction or pending_transaction['sender'] == 'error' ):
            self.logger.error('add_transaction_failed', pending_transaction, pending_transaction)
            return {'error': 'add_transaction_failed'}
        
        self.pending_liquidity[approved_remove_liquidity] = approved_remove_liquidity
        return approved_remove_liquidity

    async def get_position(self, liquidity_address:Address) -> Liquidity:
        liquidity_address = str(liquidity_address)
        if liquidity_address not in self.liquidity_positions:
            return {'error': 'liquidity position does not exist'}
        return self.liquidity_positions[liquidity_address]

    async def get_percent_of_pool(self, pool: Pool, position_address: Address) -> Decimal:
        position = await self.get_position(position_address)
        if 'error' in position:
            return position
        total_liquidity = pool.amm.get_total_reserves()
        base_liquidity = position.txn.transfers[0]['for']
        quote_liquidity = position.txn.transfers[1]['for']
        position_liquidity = base_liquidity + quote_liquidity
        percent = prec(position_liquidity / total_liquidity, self.default_currency.decimals)
        return percent
        
    async def get_accumulated_fees(self, liquidity_address: Address) -> dict:
        position = await self.get_position(liquidity_address)
        if 'error' in position:
            return position
        liquidity = self.liquidity_positions[liquidity_address]
        return {"base_fee": liquidity.base_fee, "quote_fee": liquidity.quote_fee}

    async def collect_fees(self, agent_wallet:Address, liquidity_address: Address, base: str, quote: str) -> dict:
        """
        Collects the fees accumulated in a liquidity position.
        """
        liquidity_address = str(liquidity_address)
        agent_wallet = str(agent_wallet)
        if base+quote not in self.pools:
            return {'error': 'pool does not exist'}

        if len(self.pending_liquidity) >= self.max_pending_transactions:
            return {'error': 'max_pending_transactions_reached'}
        if liquidity_address not in self.liquidity_positions:
            return {'error': 'liquidity position does not exist'}
        if agent_wallet != self.liquidity_positions[liquidity_address].owner:
            return {'error': 'agent does not own liquidity position'}

        collect_fees_addess = generate_address()
        liquidity = self.liquidity_positions[liquidity_address]
        transfers = [
            {'asset': base, 'address': self.assets[base]['address'], 'from': self.router, 'to': agent_wallet, 'for': liquidity.base_fee},
            {'asset': quote, 'address': self.assets[quote]['address'], 'from': self.router, 'to': agent_wallet, 'for': liquidity.quote_fee}
        ]
        transaction = MempoolTransaction(id=collect_fees_addess, asset=self.default_currency.symbol, fee=0, amount=0, sender=agent_wallet, recipient=self.router, transfers=transfers)
        self.unapproved_collect_fees[collect_fees_addess] = CollectFee(liquidity.base_fee, liquidity.quote_fee, liquidity.pool_fee_pct, transaction)
        return {collect_fees_addess: self.unapproved_collect_fees[collect_fees_addess]}
    
    async def approve_collect_fees(self, collect_fees_addess:Address, network_fee: str) -> CollectFee:
        """
        Approves a collect fees transaction.
        """
        collect_fees_addess = str(collect_fees_addess)
        if collect_fees_addess not in self.unapproved_collect_fees:
            return {'error': 'liquidity not found'}
        approved_collect_fees = self.unapproved_collect_fees.pop(collect_fees_addess)
        approved_collect_fees.txn.fee = network_fee
        pending_transaction = await self.requester.add_transaction(**approved_collect_fees.txn.to_dict())
        if('error' in pending_transaction or pending_transaction['sender'] == 'error' ):
            self.logger.error('add_transaction_failed', pending_transaction, pending_transaction)
            return {'error': 'add_transaction_failed'}
        
        self.pending_collect_fees[approved_collect_fees] = approved_collect_fees
        return approved_collect_fees
