import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from uuid import uuid4 as UUID
from decimal import Decimal
from .components.ConstantProduct import ConstantProduct
from source.Messaging import Responder, Requester
from Channels import Channels
from source.crypto.WalletRequests import WalletRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.utils.logger import Logger
from source.utils._utils import prec, non_zero_prec, generate_address

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class DefiExchange():
    """
    A Crypto Exchange that uses an Automated Market Maker (AMM) to match orders.

    It creates pools of assets, wherein agents provide liquidity and receive rewards. 
    Orders move assets from the pool wallet to the user's wallet, every transaction is processed on a single blockchain.

    There are no limit orders, only market orders called "swaps".

    """
    def __init__(self, datetime= None, crypto_requester=None, wallet_requester=None):
        channels = Channels()
        self.dt = datetime
        self.requester = CryptoCurrencyRequests(Requester(channels.crypto_channel))
        self.wallet_requester = WalletRequests(Requester(channels.wallet_channel))
        self.router = generate_address()
        self.default_currency = {'name': 'DefY', 'symbol': 'DFY', 'id': str(UUID()), 'decimals': 18}
        self.assets = {self.default_currency['symbol']: {'type': 'crypto', 'id' : self.default_currency['id'], 'decimals': self.default_currency['decimals'], 'min_qty': Decimal('0.01'), 'min_qty_percent': Decimal('0.05')}}
        self.fee_levels = [Decimal('0.01'), Decimal('0.05'), Decimal('0.25'), Decimal('0.1')]
        self.pools = {}        
        self.swaps = []
        self.unapproved_swaps = {}
        self.unconfirmed_swaps = {}
        self.unapproved_liquidity = {}
        self.unconfirmed_liquidity = {}
        self.pending_transactions = []
        self.max_unapproved_unconfirmed = 1_000_000
        self.max_pending_transactions = 1_000_000
        self.max_unapproved_swaps = 1_000_000
        self.max_pairs = 10000
        self.max_assets = 10000
        self.logger = Logger('CryptoExchange_DeFi', 30)
        
    async def next(self):
        for pending_transaction in self.pending_transactions: 
            # NOTE: base and quote transactions return a MempoolTransaction, see `source\crypto\MemPool.py`
            transaction = await self.requester.get_transaction(asset=pending_transaction['txn']['asset'], id=pending_transaction['txn']['id'])
            if not transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in transaction:
                continue
            base= transaction['transfers'][0]['asset']
            quote = transaction['transfers'][1]['asset']
            base_amount = transaction['transfers'][0]['for'] 
            pool = self.pools[base+quote][pending_transaction['pool']]
            if transaction['confirmed'] == False and pending_transaction['type'] == 'swap':
                price = pool['amm'].get_price(base_amount)
                quote_qty = pending_transaction['quote_qty']
                slippage = pending_transaction['slippage']
                if price < quote_qty * (1 - slippage):
                    self.logger.warning(f'price slipped too low, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
                    await self.requester.cancel_transaction(self.default_currency['symbol'], transaction['id'])
                if price > quote_qty * (1 + slippage) :
                    self.logger.warning(f'price slipped too high, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
                    await self.requester.cancel_transaction(self.default_currency['symbol'], transaction['id'])
                    return {'error': 'slippage, price too high'}
            if transaction['confirmed']:
                pool['amm'].balance(base_amount)
                if pending_transaction['type'] == 'swap':
                    await self.confirm_swap(transaction)
                elif pending_transaction['type'] == 'liquidity':
                    await self.confirm_liquidity(transaction)
                self.pending_transactions.remove(pending_transaction)
  
    async def create_asset(self, symbol: str, decimals=8, min_qty_percent='0.05') -> dict:
        if symbol == self.default_currency['symbol']:
            return {'error': 'cannot create default_quote_currency'}
        if len(self.assets) >= self.max_assets:
            return {'error': 'cannot create, max_assets_reached'}
        if symbol in self.assets:
            return {'error': 'cannot create, asset already exists'}        

        minimum = prec('.00000000000000000001', decimals)
        address = generate_address()
        self.assets[symbol] = {'address': address, 'decimals': decimals, 'min_qty': minimum, 'is_active': True}

        return {'asset_created': symbol}

    async def create_pool(self, base, quote, fee_level=2):
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
        
        fee = self.fee_levels[fee_level]
        if base+quote in self.pools:
            if str(fee) in self.pools[base+quote]:
                return {'error': 'cannot create, pool already exists'}
        else:
            self.pools[base+quote] = {}

        new_pool = {
            'fee': fee,
            'base': base,
            'quote': quote,
            'amm': ConstantProduct(),
            'liquidity_positions': [],
            'is_active': True
        }
        self.pools[base+quote][str(fee)] = new_pool
        return new_pool
    
    async def select_pool_fee(self, base, quote):
        """
        Returns the fee from the pool with the most liquidity for a given base and quote pair.

        NOTE: the fee also provides the key to finding pools in the self.pools dict. 

        `i.e. ['BTCUSDT']['.01'] represents a pool with a fee of .01 for the BTC/USDT pair.`
        """
        if base+quote not in self.pools:
            return {'error': 'pool does not exist'}
        max_reserves = 0
        selected_pool_fee = None
        for fee, pool in self.pools[base+quote].items():
            if pool['is_active']:
                reserves = pool['amm'].get_total_reserves()
                if reserves > max_reserves:
                    max_reserves = reserves
                    selected_pool_fee = fee
        if selected_pool_fee is None:
            return {'error': 'no active pools found'}
        return selected_pool_fee
    
    async def swap(self, base, quote, base_qty, agent_wallet, slippage='.05'):
        await self.wallet_requester.has_assets(agent_wallet, base, base_qty)

        if len(self.pending_transactions) >= self.max_pending_transactions:
            return {'error': 'max_pending_transactions_reached'}
        if len(self.unapproved_swaps) >= self.max_unapproved_swaps:
            self.unapproved_swaps.remove(self.unapproved_swaps[0])

        pool_fee = await self.select_pool_fee(base, quote)
        if 'error' in pool_fee: return pool_fee          
        pool = self.pools[base+quote][pool_fee]      
  
        #NOTE: all swaps are from base to quote
        amount = non_zero_prec(base_qty, self.assets[base]['decimals'])
        price = pool['amm'].get_price(amount)
        network_fee = prec((await self.requester.get_last_fee()), self.default_currency['decimals'])
        swap_id = generate_address()
        self.unapproved_swaps[swap_id] = {'id': swap_id,'base': base, 'quote': quote, 'base_qty': base_qty, 'quote_qty': price, 'fee': pool_fee, 'agent_wallet': agent_wallet, 'network_fee': network_fee, 'slippage': slippage, 'dt': self.dt}
        await self.wallet_requester.request_signature(agent_wallet, self.unapproved_swaps[swap_id])
        return {swap_id: self.unapproved_swaps[swap_id]}

    async def approve_swap(self, swap_id):
        if swap_id not in self.unapproved_swaps:
            return {'error': 'swap not found'}
        approved_swap = self.unapproved_swaps.pop(swap_id)
        id = approved_swap['id']
        base = approved_swap['base']
        quote = approved_swap['quote']
        base_qty = approved_swap['base_qty']
        quote_qty = approved_swap['quote_qty']
        agent_wallet = approved_swap['agent_wallet']
        network_fee = approved_swap['network_fee']
        slippage = approved_swap['slippage']
        pool_fee = approved_swap['fee']
        
        price = self.pools[base+quote]['amm'].get_price(base_qty)
        if price < quote_qty * (1 - slippage):
            self.logger.error(f'price slipped too low, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            return {'error': 'slippage, price too low'}
        if price > quote_qty * (1 + slippage) :
            self.logger.error(f'price slipped too high, price: {price}, quote_qty: {quote_qty}, slippage: {slippage}')
            return {'error': 'slippage, price too high'}
        
        get_latest_fee = prec(await self.requester.get_last_fee(), self.default_currency['decimals'])
        if network_fee < get_latest_fee * (1- slippage):
            self.logger.error(f'network fee slipped too low, network_fee: {network_fee}, get_latest_fee: {get_latest_fee}, slippage: {slippage}')
            return {'error': 'slippage, network fee too low'}
        if network_fee > get_latest_fee * (1 + slippage) :
            self.logger.error(f'network fee slipped too high, network_fee: {network_fee}, get_latest_fee: {get_latest_fee}, slippage: {slippage}')
            return {'error': 'slippage, network fee too high'}

        transfers = [
            {'asset': base, 'address': self.assets[base]['address'], 'from': agent_wallet, 'to': self.router, 'for': base_qty},
            {'asset': quote, 'address': self.assets[quote]['address'], 'from': self.router, 'to': agent_wallet, 'for': price}
        ]
        pending_transaction = await self.requester.add_transaction(id=id, asset=self.default_currency['symbol'], fee=network_fee, amount=0, sender=self.router, recipient=agent_wallet, transfers=transfers)
        if('error' in pending_transaction or pending_transaction['sender'] == 'error' ):
            self.logger.error('add_transaction_failed', pending_transaction, pending_transaction)
            return {'error': 'add_transaction_failed'}
        self.pending_transactions.append({'type': 'swap', 'pool': pool_fee, 'slippage': slippage, 'quote_qty': quote_qty, 'txn': pending_transaction})
        approved_swap['txn'] = pending_transaction['id']
        self.unconfirmed_swaps[approved_swap['txn']] = approved_swap
        return pending_transaction         

    async def confirm_swap(self, transaction):
        transaction_id = transaction['id']
        if transaction_id not in self.unconfirmed_swaps:
            return {'error': 'swap not found'}
        swap = self.unconfirmed_swaps[transaction_id].copy()
        self.swaps.append(swap)
        self.unconfirmed_swaps.pop(transaction_id)
    
    async def provide_liquidity(self, agent_wallet, base, quote, amount, fee_level=-1, high_range='.8', low_range='.2'):
        #TODO: check that agent has enough funds to provide liquidity
        await self.create_pool(base, quote, fee_level)
        if fee_level >= len(self.fee_levels):
            return {'error': 'fee level does not exist'}        
        if fee_level < 0:
            pool_fee = await self.select_pool_fee(base, quote)
            if 'error' in pool_fee: return pool_fee          
            pool = self.pools[base+quote][pool_fee]
        if fee_level > 0:
            fee = self.fee_levels[fee_level]
            pool = self.pools[base+quote][str(fee)]
        if pool['is_active'] == False:
            return {'error': 'pool is inactive'}            

        liquidity_id = generate_address()
        amount = prec(amount, self.assets[base]['decimals'])
        price = pool['amm'].get_price(amount)
        max_price = price * (1 + high_range)
        min_price = price * (1 - low_range)
        network_fee = prec((await self.requester.get_last_fee()), self.default_currency['decimals'])
        self.unapproved_liquidity[liquidity_id] = {'id': liquidity_id, 'base': base, 'quote': quote, 'fee': pool_fee, 'amount': amount, 'price': price, 'max_price': max_price, 'min_price': min_price, 'network_fee': network_fee, 'agent_wallet': agent_wallet, 'dt': self.dt}
        return {liquidity_id: self.unapproved_liquidity[liquidity_id]}
    
    async def approve_liquidity(self, liqudiity_id):
        if liqudiity_id not in self.unapproved_liquidity:
            return {'error': 'liquidity not found'}
        approved_liquidity = self.unapproved_liquidity.pop(liqudiity_id)
        id = approved_liquidity['id']
        base = approved_liquidity['base']
        quote = approved_liquidity['quote']
        price = approved_liquidity['price']
        agent_wallet = approved_liquidity['agent_wallet']
        base_qty = approved_liquidity['amount']
        pool_fee = approved_liquidity['fee']
        transfers = [
            {'asset': base, 'address': self.assets[base]['address'], 'from': agent_wallet, 'to': self.router, 'for': base_qty},
            {'asset': quote, 'address': self.assets[quote]['address'], 'from': self.router, 'to': agent_wallet, 'for': price}
        ]
        network_fee = prec((await self.requester.get_last_fee()), self.default_currency['decimals'])
        pending_transaction = await self.requester.add_transaction(id=id, asset=self.default_currency['symbol'], fee=network_fee, amount=0, sender=self.router, recipient=agent_wallet, transfers=transfers)
        if('error' in pending_transaction or pending_transaction['sender'] == 'error' ):
            self.logger.error('add_transaction_failed', pending_transaction, pending_transaction)
            return {'error': 'add_transaction_failed'}
        
        self.pending_transactions.append({'type':'liquidity', 'pool': pool_fee, 'txn': pending_transaction})
        approved_liquidity['txn'] = pending_transaction['id']
        self.unconfirmed_liquidity[approved_liquidity['txn']] = approved_liquidity
        return approved_liquidity
    
    async def confirm_liquidity(self, transaction):
        transaction_id = transaction['id']
        if transaction_id not in self.unconfirmed_liquidity:
            return {'error': 'liquidity not found'}
        liquidity = self.unconfirmed_liquidity[transaction_id].copy()
        self.pools[liquidity['base']+liquidity['quote']]['liquidity_positions'].append(liquidity)
        self.unconfirmed_liquidity.pop(transaction_id)
    
    async def callback(self, msg):
        if msg['topic'] == 'signature': 
            id = msg['txn']['id']
            if id not in self.unapproved_swaps and id not in self.unapproved_liquidity:
                return {'error': 'transaction not found'}
            if id in self.unapproved_swaps:
                if msg['decision'] == True:
                    await self.approve_swap(id)
                else:
                    self.unapproved_swaps.pop(id)
            elif id in self.unapproved_liquidity:
                if msg['decision'] == True:
                    await self.approve_liquidity(id)
                else:
                    self.unapproved_liquidity.pop(id)
            return {'msg': 'request received'}