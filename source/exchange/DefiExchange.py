import sys, os
from datetime import timedelta, datetime
from decimal import Decimal
from typing import Dict
from .types.Defi import *
from .components.ConstantProduct import ConstantProduct
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.WalletRequests import WalletRequests
from source.crypto.MemPool import MempoolTransaction
from source.utils.logger import Logger
from source.utils._utils import prec, generate_address, string_to_time
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
    def __init__(self, chain = None, dt= None, crypto_requests=None, wallet_requests=None):
        self.chain = chain # the blockchain that the exchange is running on
        self.dt: datetime = dt
        self.requests: CryptoCurrencyRequests = crypto_requests
        self.wallet_requests: WalletRequests = wallet_requests
        self.router = '0xDeFiGDWZ2LPsQwWbSSCANRK37qG4N'
        self.default_currency: Currency = None
        self.assets: Dict[Symbol, Asset] = {}
        self.fee_levels = [Decimal('0.01'), Decimal('0.05'), Decimal('0.25'), Decimal('0.1')]
        self.pools: Dict[Pair, Dict[PoolFee, Pool]] = {}        
        self.swaps = []
        self.liquidity_positions: Dict[Address, Liquidity] = {}
        self.pending_swaps: Dict[Address, Swap] = {}
        self.pending_liquidity: Dict[Address, Liquidity] = {}
        self.pending_remove_liquidity: Dict[Address, Liquidity] = {}        
        self.pending_collect_fees: Dict[Address, CollectFee] = {}        
        self.max_pairs = 10000
        self.max_assets = 10000
        self.max_price_impact = Decimal('0.15')
        self.default_deadline = 30_000 #NOTE: by default the sim clock ticks every nano second by a minute, so we have to adjust this to account for simulated seconds
        self.logger = Logger('DefiExchange', 20)

    async def start(self):
        self.chain = await self.requests.connect(self.chain)
        if 'error' in self.chain:
            self.logger.error(f'cannot connect to chain, error: {self.chain["error"]}')
            return {'error': 'cannot connect to chain'}
        if isinstance(self.chain, dict): 
            self.default_currency = Currency(self.chain['symbol'], decimals= self.chain['decimals'])
            self.assets[self.default_currency.symbol] = Asset(self.router, self.chain['decimals'])
        self.logger.info(f'connected to chain, chain: {self.chain}')
        
    async def next(self):
        self.logger.info(f'next tick, dt: {self.dt}')
        await self.update_pending_liquidity()
        await self.update_pending_remove_liquidity()
        await self.update_pending_swaps()
        await self.update_pending_collect_fees()
        await self.update_liqudity_positions()

    async def connect(self):
        """
        Called when a wallet connects to the exchange.
        """
        params = {
            'default_currency': self.default_currency,
            'max_price_impact': self.max_price_impact,
            'max_pending_transactions': self.max_pending_transactions,
            'default_deadline': self.default_deadline,
            'fee_levels': self.fee_levels,
            'max_unapproved_swaps': self.max_unapproved_swaps,
            'max_unapproved_unconfirmed': self.max_unapproved_unconfirmed,
            'max_pairs': self.max_pairs,
            'max_assets': self.max_assets,
        }
        return params

    async def update_pending_liquidity(self):
        for address in list(self.pending_liquidity.keys()):
            address: Address = str(address)
            pending_liquidity: Liquidity = self.pending_liquidity[address]
            transaction = await self.requests.get_transaction(asset=self.default_currency.symbol, id=address)
            if not transaction:
                # TODO: could implement a timeout where txn is cancelled if it is not confirmed within a certain time
                continue
            elif 'error' in transaction:
                continue
            if transaction['confirmed']:
                base = pending_liquidity.pair.base
                quote = pending_liquidity.pair.quote
                base_qty = pending_liquidity.txn.transfers[0]['for']
                quote_qty = pending_liquidity.txn.transfers[1]['for']
                if base+quote not in self.pools or pending_liquidity.pool_fee_pct not in self.pools[base+quote]:
                    self.logger.error(f'Unable to add liquidity for confirmed txn {address}: pool does not exist, base: {base}, quote: {quote}, pool_fee_pct: {pending_liquidity.pool_fee_pct}')
                    continue
                pool = self.pools[base+quote][pending_liquidity.pool_fee_pct]
                await self.pool_add_liquidity(pool, base_qty, quote_qty)
                self.liquidity_positions[address] = pending_liquidity
                await self.wallet_requests.transaction_confirmed(address, transaction)
                self.pending_liquidity.pop(address)
                self.logger.info(f'liquidity confirmed, transaction: {transaction}')
                continue 

    async def update_pending_remove_liquidity(self):
        for address in list(self.pending_remove_liquidity.keys()):
            address: Address = str(address)
            pending_remove_liquidity: Liquidity = self.pending_remove_liquidity[address]
            transaction = await self.requests.get_transaction(asset=self.default_currency.symbol, id=address)
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
                await self.wallet_requests.transaction_confirmed(address, transaction)
                self.liquidity_positions.pop(pending_remove_liquidity.owner) # the `owner` of a pending liquidity removal is the liquidity being removed
                self.pending_remove_liquidity.pop(address)

    async def update_pending_swaps(self):
        for address in list(self.pending_swaps.keys()):
            address: Address = str(address)
            pending_swap: Swap = self.pending_swaps[address]
            transaction = await self.requests.get_transaction(asset=self.default_currency.symbol, id=address)
            if not transaction:
                continue
            elif 'error' in transaction:
                continue
            base = pending_swap.pair.base
            quote = pending_swap.pair.quote
            pool = self.pools[base+quote][pending_swap.pool_fee_pct]
            base_qty = pending_swap.txn.transfers[0]['for']
            quote_qty = pending_swap.txn.transfers[1]['for']
            price = pool.amm.get_price(base_qty)
            slippage = pending_swap.slippage
            
            if not transaction['confirmed']:
                #TODO: if the following conditions are met update on the front-end
                if (self.dt - string_to_time(transaction['dt'])).total_seconds() > pending_swap.deadline:
                    self.logger.warning(f'transaction timed out, transaction: {transaction}, deadline: {pending_swap.deadline}')
                    await self.requests.cancel_transaction(self.default_currency.symbol, transaction['id'])
                    self.pending_swaps.pop(address)
                check_swap = self.check_swap(pending_swap, price)
                if 'error' in check_swap:
                    await self.requests.cancel_transaction(self.default_currency.symbol, transaction['id'])
                    self.pending_swaps.pop(address)   
                       
            if transaction['confirmed']:
                await self.pool_swap_liquidity(pool, base_qty, quote_qty, pending_swap.fee_amount)
                self.swaps.append(pending_swap)
                pool.amm.balance(base_qty)
                await self.wallet_requests.transaction_confirmed(address, transaction)
                self.logger.info(f'swap confirmed, transaction: {transaction}')
                self.pending_swaps.pop(address)

    async def update_pending_collect_fees(self):
        for address in list(self.pending_collect_fees.keys()):
            address: Address = str(address)
            pending_collect_fees: CollectFee = self.pending_collect_fees[address]
            transaction = await self.requests.get_transaction(asset=self.default_currency.symbol, id=pending_collect_fees.txn.id)
            if not transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in transaction:
                continue
            if transaction['confirmed']:
                base = pending_collect_fees.txn.transfers[0]['asset']
                quote = pending_collect_fees.txn.transfers[1]['asset']
                pool = self.pools[base+quote][pending_collect_fees.pool_fee_pct]
                position = await self.get_position(pending_collect_fees.liquidity_address)
                position.base_fee = 0
                position.quote_fee = 0
                position.last_collect_time = string_to_time(transaction['dt'])
                self.liquidity_positions[position.txn.id] = position                
                await self.wallet_requests.transaction_confirmed(address, transaction)
                return self.pending_collect_fees.pop(address)

    async def update_liqudity_positions(self): 
        for address in list(self.liquidity_positions.keys()):
            address: Address = str(address)
            position:Liquidity = self.liquidity_positions[address]
            await self.update_liquidity_position(position)

    async def update_liquidity_position(self, position: Liquidity) -> Liquidity:
        pool = await self.get_pool(position.pair.base, position.pair.quote, position.pool_fee_pct)
        percent_of_pool = await self.get_percent_of_pool(pool, position)
        if 'error' in percent_of_pool:        
            return {'error': 'pool not found'}
        #NOTE: have to accrue fees at the tick of the clock, otherwise the fees will be inaccurate
        accumulated_base_fee = 0
        for time in list(pool.amm.fees.keys()):
            if pool.amm.fees[time] == 0:
                pool.amm.fees.pop(time) # remove empty fee entries
                continue
            if position.last_collect_time and time <= position.last_collect_time:
                continue # skip fees that have already been collected
            accumulated_base_fee += prec(pool.amm.fees[time] * percent_of_pool['base_pct'], self.assets[position.pair.base].decimals)
            pool.amm.fees[time] -= accumulated_base_fee

        if accumulated_base_fee > 0:
            accumuluated_quote_fee = prec(pool.amm.get_price(accumulated_base_fee), self.assets[position.pair.quote].decimals)
            pool.amm.reserve_b -= accumuluated_quote_fee
            pool.amm.balance(accumulated_base_fee)            
            position.base_fee = accumulated_base_fee
            position.quote_fee = accumuluated_quote_fee
        return position

    async def request_signatures(self):
        for swap in list(self.unapproved_swaps.values()):
            if swap.deadline and (self.dt - swap.txn.dt).total_seconds() > swap.deadline:
                self.logger.warning(f'swap timed out, transaction: {swap.txn}, deadline: {swap.deadline}')
                self.unapproved_swaps.pop(swap.txn.id)
                continue
            agent_wallet = swap.txn.sender
            has_funds = await self.wallet_has_funds(agent_wallet, swap.txn.transfers[0]['asset'], swap.txn.transfers[0]['for'])
            if not has_funds: 
                continue
            self.logger.info(f'requesting signature for swap from: {agent_wallet}')
            signed = await self.wallet_requests.request_signature(agent_wallet, swap.txn.to_dict())
            if 'error' in signed:
                self.logger.error(f'error requesting signature for swap: {swap.txn}, error: {signed["error"]}')
                continue
            self.logger.info(f'signature for swap: {signed}')

        for liquidity in list(self.unapproved_liquidity.values()):
            seconds_since_creation = (self.dt - liquidity.txn.dt).total_seconds()
            if self.default_deadline and seconds_since_creation > self.default_deadline:
                self.logger.warning(f'provide liquidity timed out, transaction: {liquidity.txn.id}, deadline: {self.default_deadline} time passed: {seconds_since_creation}')
                self.unapproved_liquidity.pop(liquidity.txn.id)
                continue
            agent_wallet = liquidity.txn.sender
            base = liquidity.txn.transfers[0]['asset']
            quote = liquidity.txn.transfers[1]['asset']
            base_amount = liquidity.txn.transfers[0]['for']
            quote_amount = liquidity.txn.transfers[1]['for']

            has_liquidity = await self.wallet_has_liquidity(agent_wallet, base, quote, base_amount, quote_amount)
            if not has_liquidity: 
                continue
            self.logger.info(f'requesting signature for provide liquidity from: {agent_wallet}')
            signed = await self.wallet_requests.request_signature(agent_wallet, liquidity.txn.to_dict())
            if 'error' in signed:
                self.logger.error(f'error requesting signature for provide liquidity: {liquidity.txn}, error: {signed["error"]}')
                continue
            self.logger.info(f'signature for provide liquidity: {signed}')
        
        for remove_liquidity in list(self.unapproved_remove_liquidity.values()):
            if self.default_deadline and (self.dt - remove_liquidity.txn.dt).total_seconds() > self.default_deadline:
                self.logger.warning(f'transaction timed out, transaction: {remove_liquidity.txn}, deadline: {self.default_deadline}')
                self.unapproved_remove_liquidity.pop(remove_liquidity.txn.id)
                continue
            agent_wallet = remove_liquidity.txn.sender
            await self.wallet_requests.request_signature(agent_wallet, remove_liquidity.txn.to_dict())
        
        for collect_fees in list(self.unapproved_collect_fees.values()):
            if self.default_deadline and (self.dt - collect_fees.txn.dt).total_seconds() > self.default_deadline:
                self.logger.warning(f'transaction timed out, transaction: {collect_fees.txn}, deadline: {self.default_deadline}')
                self.unapproved_collect_fees.pop(collect_fees.txn.id)
                continue
            agent_wallet = collect_fees.txn.sender
            await self.wallet_requests.request_signature(agent_wallet, collect_fees.txn.to_dict())

    async def signature_response(self, agent_wallet: Address, decision: bool, txn: dict):
        if type(txn) != dict or 'error' in txn:
            self.logger.error(f'invalid txn: {txn}')
            return {'error': 'invalid txn'}
        id = txn['id']
        if id in self.unapproved_swaps and self.unapproved_swaps[id].txn.sender == agent_wallet:
            if decision == 'approve':
                await self.approve_swap(id, txn['fee'])
                return {'swap_approved': id}
            else:
                self.unapproved_swaps.pop(id)
                return {'swap_rejected': id}
        elif id in self.unapproved_liquidity and self.unapproved_liquidity[id].txn.sender == agent_wallet:
            if decision == 'approve':
                await self.approve_liquidity(id, txn['fee'])
                return {'liquidity_approved': id}
            else:
                self.unapproved_liquidity.pop(id)
                return {'liquidity_rejected': id}
        elif id in self.unapproved_remove_liquidity and self.unapproved_remove_liquidity[id].txn.sender == agent_wallet:
            if decision == 'approve':
                await self.approve_remove_liquidity(id, txn['fee'])
                return {'remove_liquidity_approved': id}
            else:
                self.unapproved_remove_liquidity.pop(id)
                return {'remove_liquidity_rejected': id}
        elif id in self.unapproved_collect_fees and self.unapproved_collect_fees[id].txn.sender == agent_wallet:
            if decision == 'approve':
                await self.approve_collect_fees(id, txn['fee'])
                return {'collect_fees_approved': id}
            else:
                self.unapproved_collect_fees.pop(id)
                return {'collect_fees_rejected': id}
        self.logger.error(f'cannot find unapproved transaction with id: {id}')
        return {'error': 'transaction not found'}

    async def list_asset(self, symbol: str, decimals=8) -> dict:
        if symbol == self.default_currency.symbol:
            return {'error': 'cannot list, default_quote_currency'}
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

    async def check_assets(self, base:str, quote:str) -> dict:
        if base not in self.assets:
            self.logger.error(f'base asset does not exist, base: {base}')
            return {'error': 'base asset does not exist'}
        if quote not in self.assets:
            self.logger.error(f'quote asset does not exist, quote: {quote}')
            return {'error': 'quote asset does not exist'}
        if len(self.pools) >= self.max_pairs:
            self.logger.error(f'cannot create, max_pairs_reached')
            return {'error': 'cannot create, max_pairs_reached'}        
        if base == quote:
            self.logger.error(f'cannot create, base and quote assets are the same')
            return {'error': 'cannot create, base and quote assets are the same'}
        return {'success': 'assets exist'}
    
    async def find_pool(self, base:str, quote:str, pool_fee_pct:str) -> Pool:
        checked_assets = await self.check_assets(base, quote)
        if 'error' in checked_assets:
            return checked_assets

        if base+quote in self.pools:
            if str(pool_fee_pct) in self.pools[base+quote]:
                # pool already exists, return the existing pool
                return self.pools[base+quote][str(pool_fee_pct)]
        else: 
            self.logger.error(f'pool does not exist, base: {base}, quote: {quote}')
            return {'error': 'pool does not exist'}
        
    async def create_pool(self, base:str, quote:str,fee_level=2, initial_base_amount=0, initial_quote_amount=0 ) -> Pool:
        """
        Creates a new Pool for a given base and quote pair and fee level.
        """
        checked_assets = await self.check_assets(base, quote)
        if 'error' in checked_assets:
            return checked_assets
        
        if fee_level < 0 or fee_level >= len(self.fee_levels):
            return {'error': 'fee level does not exist'}
        
        pool_fee_pct = PoolFee(self.fee_levels[fee_level])
        self.pools[base+quote] = {}
        initial_base_amount = prec(initial_base_amount, self.assets[base].decimals)
        initial_quote_amount = prec(initial_quote_amount, self.assets[quote].decimals)
        new_pool = Pool(str(pool_fee_pct), base, quote, ConstantProduct(initial_base_amount, initial_quote_amount))
        self.pools[base+quote][str(pool_fee_pct)] = new_pool
        return new_pool

    async def get_price(self, base:str, quote:str, pool_fee_pct:str, base_amount: Decimal) -> dict:
        pool = await self.find_pool(base, quote, pool_fee_pct)
        if 'error' in pool:
            return pool
        return {'price': pool.amm.get_price(base_amount)}

    async def pool_swap_liquidity(self, pool: Pool, base_qty: Decimal, quote_qty: Decimal, fee_amount: Decimal):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        pool.amm.reserve_a += base_qty
        pool.amm.reserve_b -= quote_qty
        if self.dt not in pool.amm.fees:
            pool.amm.fees[self.dt] = 0
        pool.amm.fees[self.dt] += fee_amount
        pool.amm.balance(base_qty)

    async def pool_add_liquidity(self, pool: Pool, base_qty, quote_qty):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        pool.amm.reserve_a += base_qty
        pool.amm.reserve_b += quote_qty
        pool.amm.balance(base_qty)

    async def pool_remove_liquidity(self, pool: Pool, base_qty, quote_qty):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        
        #TODO: disallow negative liquidity
        pool.amm.reserve_a -= base_qty
        pool.amm.reserve_b -= quote_qty
        pool.amm.balance(base_qty)

    async def pool_deduct_fees(self, pool: Pool, last_collect_time, base_fees, quote_fees):
        # liquidity fees are paid in each currency of the pool (e.g ETH/DAI, fees are paid in ETH and DAI)
        # liquidity fees are paid to liquidity providers based on the percent of the pool they own (e.g ETH/DAI, if you own 10% of the pool, you get 10% of the fees)
        # swap fees are paid in the base currency to the base reserves (e.g ETH/DAI, if you swap ETH for DAI, the fee is paid in ETH)
        # the pool fee amount, is the fee amount that is paid for a swap, it is not the amount of fees that are paid to liquidity providers
        # the fee is accrued in the pool and can be collected by liquidity providers at any time via a collect transaction.
        
        pool.amm.reserve_b -= quote_fees
        pool.amm.balance(base_fees)            

    async def get_all_pools(self) -> dict:
        pools = {}
        for pair, fee_levels in self.pools.items():
            pools[pair] = {}
            for fee, pool in fee_levels.items():
                if pool.is_active:
                    pools[pair][fee] = pool.to_dict()
        return pools

    async def get_pools(self, base:str, quote:str) -> dict:
        if base+quote not in self.pools:
            return {'error': 'pair does not exist'}
        pools = {}
        for fee, pool in self.pools[base+quote].items():
            if pool.is_active:
                pools[base+quote][str(fee)] = self.pools[base+quote][str(fee)].to_dict()
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

    async def wallet_has_liquidity(self, agent_wallet: Address, base: str, quote: str, base_amount:Decimal, quote_amount:Decimal) -> bool:
        wallet_balance = await self.wallet_requests.get_balance(str(agent_wallet))
        wallet_base_amount = prec(wallet_balance[base], self.assets[base].decimals)
        wallet_quote_amount = prec(wallet_balance[quote], self.assets[quote].decimals)
        if 'error' in wallet_balance:
            self.logger.error(f'wallet balance not found, agent_wallet: {agent_wallet}')
            return False
        if base not in wallet_balance: 
            self.logger.error(f'base amount not found, agent_wallet: {agent_wallet}, base: {base}')
            return False
        if quote not in wallet_balance:
            self.logger.error(f'quote amount not found, agent_wallet: {agent_wallet}, quote: {quote}')
            return False
        if base_amount > wallet_base_amount:
            self.logger.error(f'insufficient base funds, agent_wallet: {agent_wallet}, base: {base} {base_amount} {wallet_base_amount}')
            return False
        if quote_amount > wallet_quote_amount:
            self.logger.error(f'insufficient quote funds, agent_wallet: {agent_wallet}, quote: {quote} {quote_amount} {wallet_quote_amount}')
            return False
        self.logger.info(f'wallet_has_funds, agent_wallet: {agent_wallet}, base_amount: {base_amount}, quote_amount: {quote_amount}')
        return True

    async def wallet_has_funds(self, agent_wallet: Address, asset:str, amount: Decimal) -> bool:
        self.logger.info(f'checking funds, agent_wallet: {agent_wallet}, asset: {asset}, amount: {amount}')
        if asset not in self.assets:
            self.logger.error(f'asset does not exist, asset: {asset}')
            return False
        if amount < self.assets[asset].min_qty:
            self.logger.error(f'amount too small, asset: {asset}, amount: {amount}')
            return False
        wallet_balance = await self.wallet_requests.get_balance(str(agent_wallet), asset)
        if 'error' in wallet_balance:
            self.logger.error(f'wallet balance not found, agent_wallet: {agent_wallet}, asset: {asset}, amount: {amount}')
            return False
        if amount > prec(wallet_balance[asset], self.assets[asset].decimals):
            self.logger.error(f'insufficient funds, agent_wallet: {agent_wallet}, asset: {asset}, amount: {amount}')
            return False
        self.logger.info(f'wallet_has_funds, agent_wallet: {agent_wallet}, asset: {asset}, amount: {wallet_balance}')
        return True

    async def check_swap(self, swap: Swap, price: Decimal) -> dict:
        quote_qty = swap.txn.transfers[1]['for']
        slippage = prec(swap.slippage, 3)
        max_price = quote_qty * (1 + slippage)
        min_price = quote_qty * (1 - slippage)
        if price < min_price:
            self.logger.error(f'price slipped too low, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            await self.wallet_requests.transaction_failed(swap.txn.sender, swap.txn.to_dict())
            return {'error': 'price too low'}
        if price > max_price:
            self.logger.error(f'price slipped too high, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            await self.wallet_requests.transaction_failed(swap.txn.sender, swap.txn.to_dict())
            return {'error': 'price too high'}
        return {'success': 'swap approved'}

    async def get_position(self, liquidity_address:Address) -> Liquidity:
        liquidity_address = str(liquidity_address)
        if liquidity_address not in self.liquidity_positions:
            return {'error': 'liquidity position not found'}
        position = self.liquidity_positions[liquidity_address] 
        if isinstance(position, Liquidity):
            return position
        return {'error': 'liquidity position not found'}

    async def get_percent_of_pool(self, pool: Pool, position: Liquidity) -> Decimal:
        if type(position) is dict and 'error' in position:
            return position
        base_liquidity = position.txn.transfers[0]['for']
        quote_liquidity = position.txn.transfers[1]['for']
        base_percent = prec(base_liquidity / pool.amm.reserve_a, 3)
        quote_percent = prec(quote_liquidity / pool.amm.reserve_b, 3)
        return {"base_pct": base_percent, "quote_pct": quote_percent}
        
    async def swap(self, swap: Swap):
        if type(swap == dict):
            if 'error' in swap:
                return swap
            swap = Swap(**swap)
        self.pending_swaps[swap.txn.id] = swap
        self.logger.info(f'added pending swap, swap: {swap.txn}')

    async def provide_liquidity(self, liquidity: Liquidity):
        if type(liquidity == dict):
            if 'error' in liquidity:
                return liquidity
            liquidity = Liquidity(**liquidity)
        self.pending_liquidity[liquidity.txn.id] = liquidity
        self.logger.info(f'added pending liquidity, liquidity: {liquidity.txn}')

    async def remove_liquidity(self, liquidity: Liquidity):
        if type(liquidity == dict):
            if 'error' in liquidity:
                return liquidity
            liquidity = Liquidity(**liquidity)
        self.pending_remove_liquidity[liquidity.txn.id] = liquidity
        self.logger.info(f'added pending remove liquidity, liquidity: {liquidity.txn}')

    async def collect_fees(self, collect_fees: CollectFee):
        if type(collect_fees == dict):
            if 'error' in collect_fees:
                return collect_fees
            collect_fees = CollectFee(**collect_fees)
        self.pending_collect_fees[collect_fees.txn.id] = collect_fees
        self.logger.info(f'added pending collect fees, collect_fees: {collect_fees.txn}')