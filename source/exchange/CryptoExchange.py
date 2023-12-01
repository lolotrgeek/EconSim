import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from uuid import uuid4 as UUID
import random, string
from decimal import Decimal
from source.Archive import Archive
from .Exchange import Exchange
from .types.CryptoOrderBook import CryptoOrderBook
from .types.CryptoTrade import CryptoTrade
from .types.CryptoOrder import CryptoOrder
from .types.OrderSide import OrderSide
from .types.OrderType import OrderType
from .types.CryptoMatchedOrder import CryptoMatchedOrder
from .types.CryptoFees import Fees
from source.utils.logger import Logger
from source.utils._utils import get_random_string, prec, non_zero_prec

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class CryptoExchange(Exchange):
    def __init__(self, datetime= None, requester=None, archiver=None):
        super().__init__(datetime=datetime)
        self.archiver = archiver
        self.requester = requester
        self.default_currency = {'name': 'US Dollar', 'symbol': 'USD', 'id': str(UUID()), 'decimals': 2}
        self.assets = {self.default_currency['symbol']: {'type': 'crypto', 'id' : self.default_currency['id'], 'decimals': self.default_currency['decimals'], 'min_qty': Decimal('0.01'), 'min_qty_percent': Decimal('0.05')}}        
        self.pairs = []
        self.wallets = {}
        self.agents_archive = Archive('crypto_agents')
        self.assets_archive = Archive('crypto_assets')
        self.books_archive = Archive('crypto_books')
        self.trade_log_archive = Archive('crypto_trade_log')        
        self.pairs_archive = Archive('crypto_pairs')
        self.wallets_archive = Archive('crypto_wallets')
        self.fees = Fees()
        self.fees.waive_fees = False
        self.pending_transactions = []
        self.max_pending_transactions = 1_000_000
        self.max_pairs = 10000
        self.logger = Logger('CryptoExchange', 10)
        self.minimum = Decimal('0.00000000000000000001')
        
    async def next(self):
        for transaction in self.pending_transactions: 
            # NOTE: base and quote transactions return a MempoolTransaction, see `source\crypto\MemPool.py`
            base_transaction = await self.requester.get_transaction(asset=transaction['base_txn']['asset'], id=transaction['base_txn']['id'])
            quote_transaction = await self.requester.get_transaction(asset=transaction['quote_txn']['asset'], id=transaction['quote_txn']['id'])
            if not base_transaction and not quote_transaction:
                # NOTE: if transaction is not confirmed, we keep waiting, it will eventually be confirmed
                continue
            elif 'error' in base_transaction or 'error' in quote_transaction:
                continue
            elif base_transaction['confirmed'] and quote_transaction['confirmed']:
                await self._complete_trade(transaction, base_transaction, quote_transaction)
        await self.archive()
        await self.prune_trades()
        # self.logger.debug('next', self.datetime)
  
    async def archive(self):
        await super().archive()
        self.pairs_archive.store(self.pairs)
        self.wallets_archive.store(self.wallets)

    async def list_asset(self, asset, pair, decimals, minimum, min_qty_percent):
        new_pairing = {
                'base': asset, 
                'quote': pair['asset'],
                'ticker': pair['ticker'],
                'base_decimals': decimals,
                'quote_decimals': self.assets[pair['asset']]['decimals'],
                'min_qty': minimum,
                'min_price': prec(minimum, self.assets[pair['asset']]['decimals']),
                'min_qty_percent': min_qty_percent,                
                'is_active': True,
            }
        self.pairs.append(new_pairing)
        ticker = pair['ticker']

        trade = CryptoTrade(asset, pair['asset'], pair['market_qty'], pair['seed_price'], 'init_seed_'+ticker, 'init_seed_'+ticker, self.datetime, network_fee={'base': 0, 'quote': 0}, exchange_fee={'base': 0, 'quote': 0})
        self.trade_log.append(trade)

        self.books[ticker] = CryptoOrderBook(ticker)

        buy = await self.create_new_order(asset, pair['asset'], pair['seed_price'] * pair['seed_bid'], 1, 'init_seed_'+ticker,OrderType.LIMIT, OrderSide.BUY, new_pairing['min_price'], min_qty=new_pairing['min_price'])
        if buy.status == 'error' :
            self.logger.error('error creating initial buy order', buy)
            return {'error': 'error creating initial buy order'}
        buy.exchange_fee = 0      
        added_quote = await self.add_asset('init_seed_'+ticker, pair['asset'], prec(buy.total_price + buy.network_fee, self.assets[pair['asset']]['decimals']) )
        self.logger.info(f'adding initial assets, quote {pair["asset"]} {added_quote}')
        await self.freeze_assets('init_seed_'+ticker, pair['asset'], 'init_seed_'+ticker, qty=buy.total_price, network_fee=buy.network_fee)        
        buy.id = 'init_seed_'+ticker
        self.books[ticker].bids.insert(0, buy)
  
        sell = await self.create_new_order(asset, pair['asset'], pair['seed_price'] * pair['seed_ask'], pair['market_qty'], 'init_seed_'+ticker, OrderType.LIMIT, OrderSide.SELL, minimum, min_qty=minimum)
        if sell.status == 'error':
            self.logger.error('error creating initial sell order', sell)
            return {'error': 'error creating initial sell order'}
        sell.exchange_fee = 0
        added_base = await self.add_asset('init_seed_'+ticker, asset, prec(pair['market_qty'] + sell.network_fee, decimals))
        self.logger.info(f'adding initial assets base {asset} {added_base}') 
        await self.freeze_assets('init_seed_'+ticker, asset, 'init_seed_'+ticker, qty=pair['market_qty'], network_fee=sell.network_fee)       
        sell.id = 'init_seed_'+ticker
        self.books[ticker].asks.insert(0, sell)

        self.wallets[asset] = await self.generate_address()

        for agent in self.agents:
            if 'init_seed_' not in agent['name']:
                agent['wallets'][asset] = await self.generate_address()
        
        self.logger.info('listed asset', asset, pair['asset'], pair['market_qty'], pair['seed_price'], pair['seed_bid'], pair['seed_ask'])
                
    async def create_asset(self, symbol: str, pairs=[], decimals=8, min_qty_percent='0.05') -> dict:
        """_summary_
        Args:
            `symbol` (str): the symbol of the new asset

            `pairs` (str, optional): a list of dicts for aditional quote pairs, beyond the default quote currency, that this asset can be traded against. async defaults to [].

            example pair: `{'asset': "USD" ,'market_qty':1000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}`

            `marekt_qty` (int, optional): the total amount of the asset in circulation. async defaults to 1000.

            `seed_price` (int, optional): Price of an initial trade that is created for ease of use. async defaults to 100.

            `seed_bid` (float, optional): Limit price of an initial buy order, expressed as percentage of the seed_price. async defaults to .99.

            `seed_ask` (float, optional): Limit price of an initial sell order, expressed as percentage of the seed_price. async defaults to 1.01.
        """
        if symbol == self.default_currency['symbol']:
            return {'error': 'cannot create default_quote_currency'}
        if len(self.assets) >= self.max_assets:
            return {'error': 'cannot create, max_assets_reached'}        
        if len(pairs) >= self.max_pairs or len(self.books) >= self.max_pairs:
            return {'error': 'cannot create, max_pairs_reached'}
        if symbol in self.assets:
            return {"error" :f'asset {symbol} already exists'}
        if len(pairs) == 0:
            default_quote_pair = {'asset': self.default_currency['symbol'],'market_qty':1000 ,'seed_price':100 ,'seed_bid':'.99', 'seed_ask':'1.01'}
            pairs.append(default_quote_pair)

        minimum = prec('.00000000000000000001', decimals)

        for pair in pairs:
            ticker = symbol+pair['asset']
            pair['ticker'] = ticker

            pair['seed_price'] = prec(pair['seed_price'], self.assets[pair['asset']]['decimals'])
            pair['seed_bid'] = prec(pair['seed_bid'], self.assets[pair['asset']]['decimals'])
            pair['seed_ask'] = prec(pair['seed_ask'], self.assets[pair['asset']]['decimals'])
            pair['market_qty'] = prec(pair['market_qty'], self.assets[pair['asset']]['decimals'])
            pair['base_fee'] = prec(minimum, decimals)
            pair['quote_fee'] = prec(minimum, self.assets[pair['asset']]['decimals'])
            pair['quote_qty'] = prec(pair['market_qty'] * pair['seed_price'], self.assets[pair['asset']]['decimals'])

            quote_position =  {"id":'init_seed_'+ticker, 'asset': symbol, "price": 0,"qty": pair['quote_qty'], "dt": self.datetime, "enters":[], "exits": [], }
            self.agents.append({
                'name':'init_seed_'+ticker,
                '_transactions':[],
                "taxable_events": [], 
                'positions': [quote_position],
                'wallets':{symbol: (await self.generate_address()), pair['asset']: (await self.generate_address())},
                'assets': {},
                'frozen_assets': {}
            })

            self.assets[symbol] = {'type': 'crypto', 'id' : str(UUID()), 'decimals': decimals, 'min_qty': minimum, 'min_qty_percent': Decimal(min_qty_percent)}

            await self.list_asset(symbol, pair, decimals, minimum, Decimal(min_qty_percent))

        return {'asset_created': symbol, 'pairs': pairs}
        
    async def _process_trade(self, base, quote, qty, price, buyer, seller, seller_order_id, buyer_order_id, accounting='FIFO', exchange_fee={'quote':'0.0', 'base':'0.0'}, network_fee={'quote':'0.0', 'base':'0.0'}, position_id=None):
        try:
            if buyer == 'init_seed_'+base+quote: 
                self.logger.debug('waive exchange fees for init_seed_'+base+quote)
                exchange_fee['quote'] = prec('0.0', self.assets[quote]['decimals'])
            if seller == 'init_seed_'+base+quote:
                self.logger.debug('waive exchange fees for init_seed_'+base+quote)
                exchange_fee['base'] = prec('0.0', self.assets[base]['decimals'])
            
            quote_amount = non_zero_prec(qty*price, self.assets[quote]['decimals'])

            if not (await self.agent_has_assets_frozen(buyer, quote, buyer_order_id, quote_amount, exchange_fee['quote'], network_fee['quote'])):
                self.logger.error(f'Unable to Process buy_order: {buyer_order_id} / sell order: {seller_order_id} ')
                return {'error': 'insufficient funds', 'buyer': buyer}
            if not (await self.agent_has_assets_frozen(seller, base, seller_order_id, qty,exchange_fee['base'], network_fee['base'])):
                self.logger.error(f'Unable to Process sell order: {seller_order_id} / buy_order: {buyer_order_id}')
                return {'error': 'insufficient funds', 'seller': seller}

            seller_wallet = (await self.get_agent(seller))['wallets'][base]
            buyer_wallet = (await self.get_agent(buyer))['wallets'][quote]

            pending_base_transaction = await self.requester.add_transaction(asset=base, fee=network_fee['base'], amount=qty, sender=seller_wallet, recipient=buyer_wallet)
            pending_quote_transaction = await self.requester.add_transaction(asset=quote, fee=network_fee['quote'], amount=quote_amount, sender=buyer_wallet, recipient=seller_wallet)

            if('error' in pending_base_transaction or pending_base_transaction['sender'] == 'error' or 'error' in pending_quote_transaction or pending_quote_transaction['sender'] == 'error'):
                self.logger.error('add_transaction_failed', pending_base_transaction, pending_quote_transaction)
                return {'error': 'add_transaction_failed'}
            
            await self.pay_network_fees(buyer, quote, buyer_order_id, network_fee['quote'])
            await self.pay_network_fees(seller, base, seller_order_id,  network_fee['base'])

            txn_time = self.datetime
            transaction = [
                {'id': str(UUID()), 'agent':buyer, 'order_id':buyer_order_id, 'quote_flow':-quote_amount, 'price': price, 'base': base, 'quote': quote, 'qty': qty, 'fee':exchange_fee['quote'], 'network_fee':network_fee['quote'], 'dt': txn_time, 'type': 'buy'},
                {'id': str(UUID()), 'agent':seller, 'order_id': seller_order_id, 'quote_flow':quote_amount, 'price': price, 'base': base, 'quote': quote, 'qty': -qty, 'fee':exchange_fee['base'], 'network_fee':network_fee['base'], 'dt': txn_time, 'type': 'sell'}
            ]

            self.pending_transactions.append({'base_txn': pending_base_transaction, 'quote_txn': pending_quote_transaction, 'exchange_txn': transaction, 'accounting': accounting, 'position_id': position_id})
            self.logger.debug('processed txn', transaction)
            return transaction 
        except Exception as e:
            return {'error': 'transaction failed'}   

    async def _complete_trade(self, transaction, base_transaction, quote_transaction):
        """
        Completes a trade once the quote and base transactions have been confirmed on their respective blockchains
        """
        base = transaction['exchange_txn'][0]['base']
        quote = transaction['exchange_txn'][0]['quote']
        qty = transaction['exchange_txn'][0]['qty']
        price = transaction['exchange_txn'][0]['price']
        buyer = transaction['exchange_txn'][0]['agent']
        seller = transaction['exchange_txn'][1]['agent']
        network_fee = {'base': prec(base_transaction['fee'], self.assets[base]['decimals']), 'quote': prec(quote_transaction['fee'], self.assets[quote]['decimals'])}
        exchange_fee = {'base': transaction['exchange_txn'][1]['fee'], 'quote': transaction['exchange_txn'][0]['fee']}
        trade = CryptoTrade(base, quote, qty, price, buyer, seller, self.datetime, network_fee=network_fee, exchange_fee=exchange_fee)
        self.trade_log.append(trade)
        await self.update_agents(transaction['exchange_txn'], transaction['accounting'], position_id=transaction['position_id'])
        self.pending_transactions.remove(transaction)
        self.logger.info('completed trade', trade.to_dict())

    async def get_order_book(self, ticker:str) -> CryptoOrderBook:
        """returns the CryptoOrderBook of a given Asset

        Args:
            symbol (str): the symbol of the asset

        returns:
            CryptoOrderBook: the orderbook of the asset.
        """
        if ticker in self.books:
            return self.books[ticker]
        else:
            return CryptoOrderBook("error")    

    async def get_best_ask(self, ticker:str) -> CryptoOrder:
        """retrieves the current best ask in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset.

        returns:
            CryptoOrder
        """
        if self.books[ticker].asks and self.books[ticker].asks[0]:
            return self.books[ticker].asks[0]
        else:
            return CryptoOrder(ticker,'', 0, 0, 'null_quote', OrderSide.SELL, self.datetime)

    async def get_best_bid(self, ticker:str) -> CryptoOrder:
        """retrieves the current best bid in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset.

        returns:
            CryptoOrder
        """
        if self.books[ticker].bids and self.books[ticker].bids[0]:
            return self.books[ticker].bids[0]
        else:
            return CryptoOrder(ticker, '', 0, 0, 'null_quote', OrderSide.BUY, self.datetime)

    async def get_latest_trade(self, base:str, quote: str) -> CryptoTrade:
        """Retrieves the most recent trade of a given asset

        Args:
            ticker (str): the ticker of the trade

        returns:
            Trade
        """
        latest_trade = next((trade for trade in self.trade_log[::-1] if trade.base == base and trade.quote == quote), {'error': 'no trades found'})
        if isinstance(latest_trade, CryptoTrade):
            return latest_trade.to_dict()
        else:
            return {'error': 'no trades found'}
    
    async def get_trades(self, base:str, quote: str, limit=20) -> list:
        """Retrieves the most recent trade of a given asset

        Args:
            ticker (str): the ticker of the trade

        returns:
            Trade
        """
        trades = [trade.to_dict() for trade in self.trade_log[::-1] if trade.base == base and trade.quote == quote][:limit]
        if len(trades) > 0:
            return trades
        else:
            return [{'error': 'no trades found'}]

    async def freeze_assets(self, agent, asset, order_id, qty=0, exchange_fee=0, network_fee=0) -> None:
        """
        Freezes assets, preventing them from being used in other transactions until they are unfrozen 

        `NOTE`: this is used to prevent double spending of assets that are already committed to an order
        
        `WARNING`: This does not overwrite existing frozen assets, If assets are already frozen this will add to the existing frozen assets

        """
        if exchange_fee < 0 or network_fee < 0:
            self.logger.error('cannot freeze negative fees', exchange_fee, network_fee)
            return {'error': 'cannot freeze negative fees'}
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is None:
            self.logger.error('agent not found', agent)
            return {'error': 'agent not found'}        
        if asset not in self.agents[agent_idx]['assets']:
            self.logger.error('no asset available to freeze', asset, qty, agent)
            return {'error': f'no asset {asset} available to freeze'}
        amount_to_freeze = prec(abs(qty)+exchange_fee+network_fee, self.assets[asset]['decimals'])
        if self.agents[agent_idx]['assets'][asset] < amount_to_freeze:
            self.logger.error(f'insufficient funds available to freeze for {agent} {order_id}, {asset} needs: {amount_to_freeze} has: {self.agents[agent_idx]["assets"][asset]} ')
            return {'error': 'insufficient funds available to freeze'}       
        if qty > 0:
            self.agents[agent_idx]['assets'][asset] -= abs(qty)
        if exchange_fee > 0:
            self.logger.debug('deducting exchange fee from assets to freeze', agent, asset, order_id, exchange_fee)
            self.agents[agent_idx]['assets'][asset] -= abs(exchange_fee)
        if network_fee > 0:
            self.agents[agent_idx]['assets'][asset] -= abs(network_fee)

        frozen_assets = {'order_id': order_id, 'frozen_qty': abs(qty), 'frozen_exchange_fee': exchange_fee, 'frozen_network_fee': network_fee}

        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.agents[agent_idx]['frozen_assets'][asset] = [frozen_assets]
            self.logger.debug('freezing assets', agent, asset, order_id, 'qty: ', qty, 'exchange_fee: ', exchange_fee,'network_fee: ', network_fee)
        else:
            for existing_frozen_assets in self.agents[agent_idx]['frozen_assets'][asset]:
                if existing_frozen_assets['order_id'] == order_id:
                    if qty > 0:
                        existing_frozen_assets['frozen_qty'] += qty
                    if exchange_fee > 0:
                        existing_frozen_assets['frozen_exchange_fee'] += exchange_fee
                        self.logger.debug('adding exchange fee to existing frozen assets', agent, asset, order_id, exchange_fee)
                        prec(existing_frozen_assets['frozen_exchange_fee'], self.assets[asset]['decimals'])
                    if network_fee > 0:
                        existing_frozen_assets['frozen_network_fee'] += network_fee
                    self.logger.debug('frozen assets updated', agent, asset, order_id, 'qty:', existing_frozen_assets['frozen_qty'], 'exchange_fee:', existing_frozen_assets['frozen_exchange_fee'],'network_fee:', existing_frozen_assets['frozen_network_fee'])    
                    return {'success': 'frozen assets updated'}
            self.logger.debug('freezing assets', agent, asset, order_id, 'qty: ', qty, 'exchange_fee: ', exchange_fee,'network_fee: ', network_fee)
            self.agents[agent_idx]['frozen_assets'][asset].append(frozen_assets)
        self.logger.debug('froze assets', agent, asset, order_id, 'qty: ', qty, 'exchange_fee: ', exchange_fee,'network_fee: ', network_fee)
        return {'success': 'assets frozen'}

    async def unfreeze_assets(self, agent, asset, order_id, qty=0, exchange_fee=0, network_fee=0) -> None:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is None:
            self.logger.error('unfreezing agent not found', agent)
            return {'error': 'agent not found'}
        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.logger.error('no asset available to unfreeze', asset, qty, agent, order_id)
            return {'error': 'no asset available to unfreeze'}
        status = {'qty': 'frozen', 'exchange_fee': 'frozen', 'network_fee': 'frozen'}
        for frozen_assets in self.agents[agent_idx]['frozen_assets'][asset]:
            if frozen_assets['order_id'] != order_id:
                continue
            if qty > 0:
                if frozen_assets['frozen_qty'] < abs(qty):
                    self.logger.error('frozen qty less than qty', order_id, frozen_assets['frozen_qty'], qty)
                    return {'error': 'frozen qty less than qty'}
                
                if frozen_assets['frozen_qty']:
                    frozen_assets['frozen_qty'] -= abs(qty)
                    self.agents[agent_idx]['assets'][asset] += abs(qty)
                    status['qty'] = 'unfrozen'
                else:
                    self.logger.warning('no qty assets available to unfreeze', asset, qty, agent, order_id)
                    status['qty'] = 'no frozen found'

            if exchange_fee > 0:
                if frozen_assets['frozen_exchange_fee'] < abs(exchange_fee):
                    self.logger.error('frozen exchange fee less than exchange fee', order_id, frozen_assets['frozen_exchange_fee'], exchange_fee)
                    return {'error': 'frozen exchange fee less than exchange fee'}
                
                if frozen_assets['frozen_exchange_fee'] > 0:
                    frozen_assets['frozen_exchange_fee'] -= abs(exchange_fee)   
                    self.agents[agent_idx]['assets'][asset] += abs(exchange_fee)
                    status['exchange_fee'] = 'unfrozen'                        
                else:
                    self.logger.warning('no exchange fee assets available to unfreeze', asset, exchange_fee, agent, order_id)
                    status['exchange_fee'] = 'no frozen found'

            if network_fee > 0:
                if frozen_assets['frozen_network_fee'] < abs(network_fee):
                    self.logger.error('frozen network fee less than network fee', order_id, frozen_assets['frozen_network_fee'], network_fee)
                    return {'error': 'frozen network fee less than network fee'}
                if frozen_assets['frozen_network_fee'] > 0:
                    frozen_assets['frozen_network_fee'] -= abs(network_fee)
                    self.agents[agent_idx]['assets'][asset] += abs(network_fee)
                    status['network_fee'] = 'unfrozen'
                else:
                    self.logger.warning('no network fee assets available to unfreeze', asset, network_fee, agent, order_id)
                    status['network_fee'] = 'no frozen found'

            self.logger.debug(f"unfroze assets {agent} {asset} {order_id} qty {qty} exchange_fee {exchange_fee} network_fee {network_fee}")
            return {'success': status}
        self.logger.error(f'order id {order_id} does not match any frozen order for', asset, qty, agent)
        return {'error': 'order id does not match any frozen order'}

    async def get_frozen_assets(self, agent, asset, order_id) -> dict:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is None:
            self.logger.error('agent not found', agent)
            return {'error': 'agent not found'}
        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.logger.error('no frozen assets found', asset, agent)
            return {'error': 'no frozen assets found'}
        for frozen_assets in self.agents[agent_idx]['frozen_assets'][asset]:
            if frozen_assets['order_id'] == order_id:
                return frozen_assets
        self.logger.error('order id does not match frozen order', asset, agent)
        return {'error': 'order id does not match frozen order'}

    async def pay_network_fees(self, agent, asset, order_id, fee) -> None:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is None:
            self.logger.error('agent not found', agent)
            return {'error': 'agent not found'}           
        if asset in self.agents[agent_idx]['frozen_assets']:
            for frozen_asset_idx, frozen_asset in enumerate(self.agents[agent_idx]['frozen_assets'][asset]):
                if frozen_asset['order_id'] == order_id:
                    if fee > 0 and self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee'] < fee:
                        self.logger.error('frozen fee less than fee', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee'], fee)
                        return {'error': 'frozen fee less than fee'}
                    else:
                        self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee'] -= fee
                        self.logger.debug('paying network fee', agent, asset, order_id, fee)
                    return {'success': 'network fee paid'}

    async def get_network_fees(self, asset, num_txns=10) -> list:
        fees = self.requester.get_fees( asset,num_txns)
        if not fees:
            return {'error': 'no fees found'}
        for fee in fees:
            fee = prec(fee, self.assets[asset]['decimals'])
        
        smallest_fee = min(fees)
        median_fee = prec(sum(fees)/len(fees), self.assets[asset]['decimals'])
        largest_fee = max(fees)
        
        return {'slow': smallest_fee, 'standard': median_fee, 'fast': largest_fee}

    async def set_network_fee(self, price, asset, speed='standard') -> Decimal:
        fees = await self.get_network_fees()
        if 'error' in fees:
            return fees
        if speed == 'budget':
            return prec(fees['slow'] - (fees['slow'] * (price/100)), self.assets[asset]['decimals'])
        elif speed == 'slow':
            return fees['slow']
        elif speed == 'standard':
            return fees['standard']
        elif speed == 'fast':
            return fees['fast']
        elif speed == 'rush':
            return prec(fees['fast'] + (fees['fast'] * (price/100)), self.assets[asset]['decimals'])    

    async def create_new_order(self, base, quote, price, qty, creator, order_type, side, fee, tif=None, position_id=None, min_qty=0) -> CryptoOrder:
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return CryptoOrder(base, quote, 0, 0, creator, order_type, side, self.datetime, status='error', accounting='max_pending_transactions_reached')
        
        qty = prec(qty, self.assets[base]['decimals'])
        price = prec(price, self.assets[quote]['decimals'])
        min_qty = prec(min_qty, self.assets[base]['decimals'])
        if qty <= 0:
            return CryptoOrder(base, quote, 0, 0, creator, order_type, side, self.datetime, status='error', accounting='qty_must_be_greater_than_zero') 
        if order_type == OrderType.LIMIT:
            if price <= 0:
                return CryptoOrder(base, quote, 0, 0, creator, order_type, side, self.datetime, status='error', accounting='price_must_be_greater_than_zero')
            if side == OrderSide.BUY and len(self.books[base+quote].bids) >= self.max_bids:
                return CryptoOrder(base, quote, 0, 0, creator, order_type, side, self.datetime, status='error', accounting='max_bid_depth_reached')
            if side == OrderSide.SELL and len(self.books[base+quote].asks) >= self.max_asks:
                return CryptoOrder(base, quote, 0, 0, creator, order_type, side, self.datetime, status='error', accounting='max_ask_depth_reached')

        if min_qty > 0:
            minimum_match_qty = min_qty
        else:
            minimum_match_qty = prec(qty * self.assets[base]['min_qty_percent'], self.assets[base]['decimals']) 
        total_possible_matches = qty / minimum_match_qty 

        if side == OrderSide.BUY:
            decimals = self.assets[quote]['decimals']
            new_order = CryptoOrder(base, quote, price, qty, creator, order_type, OrderSide.BUY, self.datetime, position_id=position_id, fills=[])
            new_order.min_price_per_match = prec(minimum_match_qty * new_order.price, decimals)
            # this is used when the minimum match qty is set and allows for the order to be partially filled, so we need to adjust the total price willing to pay so it can be frozen
            new_order.total_price = prec(total_possible_matches * new_order.min_price_per_match, self.assets[new_order.quote]['decimals'])            
            new_order.exchange_fee = self.fees.taker_fee(new_order.total_price, decimals)
        else:
            decimals = self.assets[base]['decimals']
            new_order = CryptoOrder(base, quote, price, qty, creator, order_type, OrderSide.SELL, self.datetime, position_id=position_id, fills=[])
            new_order.exchange_fee = self.fees.taker_fee(qty, decimals)

        if new_order.exchange_fee < 0:
            new_order.status='error'
            new_order.accounting ='exchange_fee_cannot_be_negative'
            return new_order

        new_order.total_possible_matches = total_possible_matches
        new_order.minimum_match_qty = minimum_match_qty

        fee = prec(fee, decimals)
        new_order.network_fee = prec(new_order.total_possible_matches * fee, decimals)
        new_order.network_fee_per_txn = fee
        new_order.remaining_network_fee = new_order.network_fee
    
        if new_order.network_fee <= 0:
            new_order.status='error'
            new_order.accounting ='fee_must_be_greater_than_zero'
            return new_order

        self.logger.info(f'created new order: {new_order.id} {new_order.type} {new_order.side} {new_order.base}/{new_order.quote} {new_order.qty}@{new_order.price} total: {new_order.total_price} {new_order.fills}')
        return new_order

    async def convert_to_maker(self, order: CryptoOrder, asset:str, decimals:int, buffer=0) -> CryptoOrder:
        self.logger.info(f'converting to maker: {order.id} amount {order.unfilled_qty} unfreezing exchange fee {order.exchange_fee}')
        await self.unfreeze_assets(order.creator, asset, order.id, exchange_fee=order.exchange_fee)
        order.qty = order.unfilled_qty
        if order.side == OrderSide.BUY:
            order.exchange_fee = self.fees.maker_fee(order.qty * order.price, decimals)
        if order.side == OrderSide.SELL:
            order.exchange_fee = self.fees.maker_fee(order.qty, decimals)
        self.logger.info(f'maker order {order.id} freezing new fee {order.exchange_fee}')                
        await self.freeze_assets(order.creator, asset, order.id, qty=buffer, exchange_fee=order.exchange_fee)
        return order        
    
    async def apply_deductions(self, order: CryptoOrder, amount_expected_to_pay, amount_paid) -> Decimal:
        deductions = prec(amount_expected_to_pay - amount_paid , self.assets[order.quote]['decimals'])
        if deductions > 0:
            self.logger.info(f'limit buy {order.id} got a better total amount of {amount_paid} than expected: {amount_expected_to_pay}, Unfreezing deductions {deductions}')
            await self.unfreeze_assets(order.creator, order.quote, order.id, qty=deductions)

    async def filled_order(self, order: CryptoOrder) -> CryptoOrder:
        if order.side == OrderSide.BUY:
            asset = order.quote
            await self.apply_deductions(order, order.total_price, order.total_filled_price)

        if order.side == OrderSide.SELL:
            asset = order.base
            if order.type == OrderType.MARKET:
                await self.unfreeze_assets(order.creator, asset, order.id, qty=order.unfilled_qty)
        if order.exchange_fee > 0:
            await self.unfreeze_assets(order.creator, asset, order.id, exchange_fee=order.exchange_fee)
        if order.remaining_network_fee > 0:
            await self.unfreeze_assets(order.creator, asset, order.id, network_fee=order.remaining_network_fee)
        order.exchange_fee = order.exchange_fees_due
        order.status = 'filled_unconfirmed'
        #NOTE: the order price here for market and taker orders with multiple fills may not reflect the actual price paid, look at the fills to get the actual price
        self.logger.info(f'{order.type} {order.side} filled {order.id} {order.qty}@{order.price} {order.fills}')        
        return order

    async def update_ask(self, ticker: str, ask: CryptoOrder, index: int, matched_order: CryptoMatchedOrder, buyer:str ) -> None:
            self.books[ticker].asks[index].fills.append({'qty': matched_order.trade_qty, 'price': ask.price, 'fee': matched_order.maker_fee, 'creator': buyer})
            self.books[ticker].asks[index].qty -= matched_order.trade_qty
            self.books[ticker].asks[index].remaining_network_fee -= ask.network_fee_per_txn
            self.books[ticker].asks[index].exchange_fees_due += matched_order.maker_fee
            self.books[ticker].asks[index].exchange_fee -= matched_order.maker_fee

    async def update_bid(self, ticker:str, bid: CryptoOrder, index: int, matched_order: CryptoMatchedOrder, seller: str ) -> None:
            self.books[ticker].bids[index].fills.append({'qty': matched_order.trade_qty, 'price': bid.price, 'fee': matched_order.maker_fee, 'creator': seller})
            self.books[ticker].bids[index].qty -= matched_order.trade_qty
            self.books[ticker].bids[index].exchange_fee -= matched_order.maker_fee
            self.books[ticker].bids[index].exchange_fees_due += matched_order.maker_fee
            self.books[ticker].bids[index].remaining_network_fee -= bid.network_fee_per_txn
            self.books[ticker].bids[index].total_filled_price += matched_order.total_price

    async def update_asks(self, ticker:str) -> None:
        self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0 and ask.qty > ask.minimum_match_qty]

    async def update_bids(self, ticker:str) -> None:
        self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0 and bid.qty > bid.minimum_match_qty]

    async def update_order(self, trade_qty: Decimal, trade_price:Decimal, taker_fee:Decimal, order: CryptoOrder, book_order: CryptoOrder) -> CryptoOrder:
            if order.price == 0: order.price = book_order.price
            order.fills.append({'qty': trade_qty, 'price': book_order.price, 'fee': taker_fee, 'creator': book_order.creator})
            order.unfilled_qty -= trade_qty
            order.remaining_network_fee -= order.network_fee_per_txn
            order.exchange_fee -= taker_fee
            order.exchange_fees_due += taker_fee
            order.total_filled_price += trade_price
            self.logger.debug(f'{order.type} {order.side} {order.id} new fill {order.fills[-1]}')
            return order           

    async def can_match(self, order: CryptoOrder, book_order: CryptoOrder, tif=None) -> bool:
        if tif == 'TEST':
            return False
        if order.qty <=0:
            return False        
        if book_order.creator == 'null_quote': 
            self.logger.debug(f'Cannot match empty book with {order.id}.')
            return False
        if book_order.creator == order.creator:
            return False
 
    async def valid_match(self, matched_order: CryptoMatchedOrder) -> bool:
        if matched_order.book_order.qty < matched_order.trade_qty:
            self.logger.debug(f'Invalid match {matched_order.order.id} with {matched_order.book_order.id} because book qty {matched_order.book_order.qty} < trade qty {matched_order.order.qty}')
            return False
        if matched_order.order.qty < matched_order.trade_qty:
            self.logger.debug(f'Invalid match {matched_order.order.id} with {matched_order.book_order.id} because order qty {matched_order.book_order.qty} < trade qty {matched_order.order.qty}')
            return False           
        if matched_order.trade_qty < self.assets[matched_order.order.base]['min_qty']:
            self.logger.debug(f'Invalid match {matched_order.order.id} with {matched_order.book_order.id} because trade qty {matched_order.order.base} {matched_order.trade_qty} < min qty {self.assets[matched_order.order.base]["min_qty"]}')
            return False
        if matched_order.total_price < self.assets[matched_order.order.quote]['min_qty']:
            self.logger.debug(f'Invalid match {matched_order.order.id} with {matched_order.book_order.id} because total price {matched_order.order.quote} {matched_order.total_price} <  min price {self.assets[matched_order.order.quote]["min_qty"]}')
            return False
        if matched_order.trade_qty < matched_order.book_order.minimum_match_qty:
            self.logger.debug(f'Invalid match {matched_order.order.id} with {matched_order.book_order.id} because trade qty {matched_order.trade_qty} < min match qty {matched_order.book_order.minimum_match_qty}')
            return False
                   
    async def limit_buy(self, base: str, quote:str, price: float, qty: int, creator: str, fee='0.0', tif='GTC', position_id=UUID(), min_qty=0) -> CryptoOrder:
        """
        Creates a limit buy order for a given asset

        Args:

            `base` (str): the symbol of the asset to buy

            `quote` (str): the symbol of the asset to sell

            `price` (float): the price to buy the asset at

            `qty` (int): the quantity of the asset to buy

            `creator` (str): the name of the agent creating the order

            `fee` (float, optional): the network fee to pay for each transaction in this order. async defaults to 0.0.

            `tif` (str, optional): the time in force of the order. async defaults to 'GTC'.

            `position_id` (UUID, optional): the id of the position that this order is associated with. async defaults to UUID().

            `min_qty` (int, optional): the minimum quantity of the asset that can be matched with this order. async defaults to 0.
        """
        new_order = await self.create_new_order(base, quote, price, qty, creator, OrderType.LIMIT, OrderSide.BUY, fee, tif, position_id, min_qty)
        if new_order.status == 'error': return new_order
        has_asset = await self.agent_has_assets(creator, quote, prec(new_order.total_price+new_order.network_fee+new_order.exchange_fee, self.assets[quote]['decimals']))
        if not has_asset:
            new_order.status='error'
            new_order.accounting ='insufficient_funds'
            return new_order
        await self.freeze_assets(creator, quote, new_order.id, new_order.total_price, new_order.exchange_fee, new_order.network_fee)
        ticker = base+quote
        while new_order.unfilled_qty > 0:
            best_ask = await self.get_best_ask(ticker)
            if (await self.can_match(new_order, best_ask, tif)) == False:
                break
            if new_order.price >= best_ask.price:
                matched_order = CryptoMatchedOrder(new_order, best_ask, self.assets[base]['decimals'], self.assets[quote]['decimals'], self.fees, self.logger)
                is_valid_match = await self.valid_match(matched_order)
                if is_valid_match == False:
                    break
                processed = await self._process_trade(base, quote, matched_order.trade_qty, best_ask.price, creator, best_ask.creator, best_ask.id, new_order.id, exchange_fee=matched_order.exchange_fee, network_fee=matched_order.network_fee, position_id=position_id)
                if('error' in processed):
                    break #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                new_order = await self.update_order(matched_order.trade_qty, matched_order.total_price, matched_order.taker_fee, new_order, best_ask)
                await self.update_ask(ticker, best_ask, 0, matched_order, creator)
                await self.update_asks(ticker)
                # amount_expected_to_pay = non_zero_prec(new_order.price*matched_order.trade_qty, self.assets[quote]['decimals'])
                # await self.apply_deductions(new_order, amount_expected_to_pay, matched_order.total_price)
            else:
                break
        queue = len(self.books[ticker].bids)
        for idx, order in enumerate(self.books[ticker].bids):
            if new_order.price > order.price:
                queue = idx
                break            
        if new_order.unfilled_qty > 0:
            maker_order = await self.convert_to_maker(new_order, quote, self.assets[quote]['decimals'])
            self.books[ticker].bids.insert(queue, maker_order)
            self.logger.info(f'limit buy queued {maker_order.id} {maker_order.qty} {maker_order.price} {maker_order.fills}')
            return maker_order
        else:
            filled_order = await self.filled_order(new_order)
            return filled_order
        
    async def limit_sell(self, base: str, quote:str, price: float, qty: int, creator: str, fee='0.0', tif='GTC', accounting='FIFO', min_qty=0) -> CryptoOrder:
        new_order = await self.create_new_order(base, quote, price, qty, creator, OrderType.LIMIT, OrderSide.SELL, fee, tif, None, min_qty)
        if new_order.status == 'error': return new_order        
        ticker = base+quote
        has_asset = await self.agent_has_assets(creator, base, prec(new_order.qty+new_order.network_fee+new_order.exchange_fee, self.assets[base]['decimals']))
        if not has_asset:
            new_order.status='error'
            new_order.accounting ='insufficient_funds'
            return new_order
        await self.freeze_assets(creator, base, new_order.id, new_order.qty, new_order.exchange_fee, new_order.network_fee)
        while new_order.unfilled_qty > 0:
            best_bid = await self.get_best_bid(ticker)
            if (await self.can_match(new_order, best_bid, tif)) == False:
                break
            if new_order.price <= best_bid.price:
                matched_order = CryptoMatchedOrder(new_order, best_bid, self.assets[base]['decimals'], self.assets[quote]['decimals'], self.fees, self.logger)                
                is_valid_match = await self.valid_match(matched_order)
                if is_valid_match == False:
                    break
                processed = await self._process_trade(base, quote, matched_order.trade_qty, best_bid.price, best_bid.creator, creator, new_order.id, best_bid.id, accounting, matched_order.exchange_fee, matched_order.network_fee)
                if('error' in processed):
                    break #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                new_order = await self.update_order(matched_order.trade_qty,matched_order.total_price, matched_order.taker_fee, new_order, best_bid)    
                await self.update_bid(ticker, best_bid, 0, matched_order, creator)
                await self.update_bids(ticker)
            else:
                break
        queue = len(self.books[ticker].asks)
        for idx, order in enumerate(self.books[ticker].asks):
            if new_order.price < order.price:
                queue = idx
                break             
        if new_order.unfilled_qty > 0:
            # buffer = prec(str(1 / (10 ** self.assets[base]['decimals'])), self.assets[base]['decimals'])
            maker_order = await self.convert_to_maker(new_order, base, self.assets[base]['decimals'])
            self.books[ticker].asks.insert(queue, new_order)
            self.logger.info(f'limit sell queued {maker_order.id} qty: {maker_order.qty} exchange fee: {maker_order.exchange_fee} network fee: {maker_order.network_fee} price:{maker_order.price} fills:{maker_order.fills}')
            return new_order
        else:
            filled_order = await self.filled_order(new_order)
            return filled_order

    async def market_buy(self, base: str, quote:str, qty: int, buyer: str, fee='0.0', min_qty=0) -> CryptoOrder:
        new_order = await self.create_new_order(base, quote, 0, qty, buyer, OrderType.MARKET, OrderSide.BUY, fee, position_id=None, min_qty=min_qty)
        if new_order.status == 'error': return new_order
        initial_freeze = await self.freeze_assets(buyer, quote, new_order.id, network_fee=new_order.network_fee)
        if 'error' in initial_freeze:
            new_order.status='error'
            new_order.accounting ='initial_freeze_error'
            return new_order
        for idx, ask in enumerate(self.books[new_order.ticker].asks):
            if (await self.can_match(new_order, ask)) == False:
                continue
            matched_order = CryptoMatchedOrder(new_order, ask, self.assets[base]['decimals'], self.assets[quote]['decimals'],self.fees, self.logger)
            is_valid_match = await self.valid_match(matched_order)
            if is_valid_match == False: continue
            has_assets = await self.agent_has_assets(buyer, quote, matched_order.total_price)
            if not has_assets:
                self.logger.warning('insufficient assets', new_order.id, buyer, quote, matched_order.total_price)
                await self.unfreeze_assets(buyer, quote, new_order.id, network_fee=new_order.remaining_network_fee)
                new_order.status='error'
                new_order.accounting ='insufficient_funds'
                return new_order
            pre_buy_freeze = await self.freeze_assets(buyer, quote, new_order.id, matched_order.total_price, matched_order.taker_fee)
            if 'error' in pre_buy_freeze:
                await self.unfreeze_assets(buyer, quote, new_order.id, network_fee=new_order.remaining_network_fee)
                new_order.status='error'
                new_order.accounting ='pre_buy_freeze_error'
                return new_order
            processed = await self._process_trade(base, quote, matched_order.trade_qty, ask.price, buyer, ask.creator, ask.id, new_order.id, exchange_fee=matched_order.exchange_fee, network_fee=matched_order.network_fee)
            if'error' in processed: 
                await self.unfreeze_assets(buyer, quote, new_order.id, matched_order.total_price, matched_order.taker_fee)
                continue
            new_order = await self.update_order(matched_order.trade_qty,matched_order.total_price, matched_order.taker_fee, new_order, ask)
            await self.update_ask(new_order.ticker, ask, idx, matched_order, buyer)
            if new_order.unfilled_qty == 0:
                break
        await self.update_asks(new_order.ticker)
        if new_order.fills == []:
            new_order.status='error'
            new_order.accounting='no_fills'
            await self.unfreeze_assets(buyer, quote, new_order.id, network_fee=new_order.network_fee)
            return new_order
        filled_order = await self.filled_order(new_order)
        return filled_order

    async def market_sell(self, base: str, quote:str, qty: int, seller: str, fee='0.0', accounting='FIFO') -> CryptoOrder:
        new_order = await self.create_new_order(base, quote, 0, qty, seller, OrderType.MARKET, OrderSide.SELL, fee, position_id=None)
        if new_order.status == 'error': return new_order
        has_assets = await self.agent_has_assets(seller, base, prec(new_order.qty+new_order.network_fee, self.assets[base]['decimals']))
        if not has_assets:
            new_order.status='error'
            new_order.accounting ='insufficient_funds'
            return new_order          
        initial_freeze = await self.freeze_assets(seller, base, new_order.id, qty=new_order.qty, network_fee=new_order.network_fee)
        if 'error' in initial_freeze:
            new_order.status='error'
            new_order.accounting ='initial_freeze_error'
            return new_order              
        for idx, bid in enumerate(self.books[new_order.ticker].bids):
            if (await self.can_match(new_order, bid)) == False:
                continue                         
            matched_order = CryptoMatchedOrder(new_order, bid, self.assets[base]['decimals'], self.assets[quote]['decimals'], self.fees, self.logger)
            is_valid_match = await self.valid_match(matched_order)
            if is_valid_match == False: continue
            pre_sell_freeze = await self.freeze_assets(seller, base, new_order.id, exchange_fee=matched_order.taker_fee)
            if 'error' in pre_sell_freeze:
                self.logger.error('pre_sell_freeze_error', seller, base, new_order.id, matched_order.taker_fee)
                await self.unfreeze_assets(seller, base, new_order.id, qty=new_order.unfilled_qty, network_fee=new_order.remaining_network_fee)
                new_order.status='error'
                new_order.accounting ='pre_sell_freeze_error'
                return new_order        
            processed = await self._process_trade(base, quote, matched_order.trade_qty, bid.price, bid.creator, seller, new_order.id, bid.id, accounting, exchange_fee=matched_order.exchange_fee, network_fee=matched_order.network_fee )
            if'error' in processed:
                await self.unfreeze_assets(seller, base, new_order.id, exchange_fee=matched_order.taker_fee)
                continue
            new_order = await self.update_order(matched_order.trade_qty,matched_order.total_price, matched_order.taker_fee, new_order, bid)
            await self.update_bid(new_order.ticker, bid, idx, matched_order, seller)
            if new_order.unfilled_qty == 0:
                break
        await self.update_bids(new_order.ticker)
        if new_order.fills == []:
            new_order.status='error'
            new_order.accounting='no_fills'
            await self.unfreeze_assets(seller, base, new_order.id, qty=new_order.qty, network_fee=new_order.network_fee)
            return new_order
        filled_order = await self.filled_order(new_order)
        return filled_order

    async def cancel_order(self, base, quote, id) -> dict:
        ticker = base+quote
        canceled = await super().cancel_order(ticker, id)
        if canceled and 'cancelled_order' in canceled and 'creator' in canceled['cancelled_order']:
            creator = canceled['cancelled_order']['creator']
            order_id = canceled['cancelled_order']['id']
            qty = canceled['cancelled_order']['qty']
            price = canceled['cancelled_order']['price']
            exchange_fee = canceled['cancelled_order']['exchange_fee']
            network_fee = canceled['cancelled_order']['network_fee']
            if canceled['cancelled_order']['side'] == 'buy':
                qty_deduction = non_zero_prec(canceled['cancelled_order']['total_price'] - canceled['cancelled_order']['total_filled_price'], self.assets[quote]['decimals'])
                await self.unfreeze_assets(creator, quote, order_id, qty_deduction, exchange_fee , canceled['cancelled_order']['remaining_network_fee'])
            elif canceled['cancelled_order']['side'] == 'sell':
                await self.unfreeze_assets(creator, base, order_id, qty , exchange_fee , canceled['cancelled_order']['remaining_network_fee'])
            else:
                return {'error': 'unable to cancel, order type not recognized', 'id': id}
        return canceled
    
    async def cancel_all_orders(self, base, quote, creator) -> list:
        ticker = base+quote
        canceled = []
        self.logger.debug(f'cancel all orders {creator} {ticker}')
        async def cancel_bid(bid, creator):
            if bid.qty <= 0:
                return False
            if bid.creator == creator:
                await self.unfreeze_assets(creator, quote, bid.id, non_zero_prec(bid.total_price - bid.total_filled_price), bid.exchange_fee , bid.remaining_network_fee)
                canceled.append(bid.id)
                return False
            else:
                return True
            
        async def cancel_ask(ask, creator):
            if ask.qty <= 0:
                return False
            if ask.creator == creator:
                await self.unfreeze_assets(creator, base, ask.id, ask.qty , ask.exchange_fee , ask.remaining_network_fee)
                canceled.append(ask.id)
                return False
            else:
                return True
            
        self.books[ticker].bids[:] = [b for b in self.books[ticker].bids if await cancel_bid(b, creator)]
        self.books[ticker].asks[:] = [a for a in self.books[ticker].asks if await cancel_ask(a, creator)]

        return {'cancelled_orders': canceled}

    async def generate_address(self) -> str:
        """
        Generates a random string of letters and numbers to represent a wallet address
        """
        length = random.randint(26, 35)
        if not isinstance(length, int) or length < 1:
            raise ValueError("Length must be a positive integer")
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))    

    async def register_agent(self, name, initial_assets={}) -> dict:
        """
        `initial_assets`: a dict where the keys are symbols and values are quantities: e.g. {'BTC': 1000, 'ETH': 1000}
        """
        self.logger.info('registering agent', name)
        if(len(self.agents) >= self.max_agents):
            return {'error': 'max agents reached'}
        registered_name = name + str(UUID())[0:8]
        positions = []
        wallets = {
            self.default_currency['symbol']: (await self.generate_address())
        }
        for asset in initial_assets:
            side = {
                'agent': registered_name, 
                'quote_flow': 0, 
                'price': 0, 
                'base': asset, 
                'quote': self.default_currency['symbol'],
                'initial_qty': 0, 
                'qty': prec(initial_assets[asset], self.assets[asset]['decimals']), 
                'dt': self.datetime, 
                'type': 'buy'
            }
            basis ={
                'basis_initial_unit': self.default_currency['symbol'],
                'basis_per_unit': 0,
                'basis_txn_id': 'seed',
                'basis_date': self.datetime
            }
            new_position = await self.new_position(side, asset, side['qty'], basis)
            positions.append(new_position)
            initial_assets[asset] = prec(initial_assets[asset], self.assets[asset]['decimals'])
  
        for asset in self.assets:
            wallets[asset] = (await self.generate_address())            

        self.agents.append({
            'name':registered_name,
            '_transactions':[], 
            'positions': positions, 
            'assets': initial_assets,
            'wallets': wallets,
            'frozen_assets': {},
            "taxable_events": []
        })
        self.logger.debug('registered agent', self.agents[-1])
        return {'registered_agent':registered_name}
    
    async def new_enter(self, agent, asset, qty, dt, type, basis={}) -> dict:
        enter = {
            'id': str(UUID()),
            'agent': agent,
            'asset': asset,
            'initial_qty': prec(qty, self.assets[asset]['decimals']),
            'qty': prec(qty, self.assets[asset]['decimals']),
            'dt': dt,
            'type': type,
            'basis': basis,
        }
        return enter

    async def new_position(self, side, asset, qty, basis={}) -> dict:
        enter = await self.new_enter(side['agent'], asset, qty, side['dt'], side['type'], basis)
        return {
            'id': str(UUID()),
            'asset': asset,
            'qty': prec(qty, self.assets[asset]['decimals']),
            'dt': side['dt'],
            'enters': [enter],
            'exits': []
        }

    async def taxable_event(self, agent, amount, dt, basis_amount, basis_date) -> None:
        self.logger.info('taxable event', amount, basis_amount)
        pnl = amount - basis_amount
        self.logger.info('pnl', pnl)
        if pnl > 0:
            taxable_event = {"type": 'capital_gains', 'enter_date': basis_date, 'exit_date': dt, 'pnl': pnl}
            agent['taxable_events'].append(taxable_event)        

    async def enter_position(self, side, asset, qty, agent_idx, position_id, basis={}) -> dict:
        start_new_position = True
        agent = self.agents[agent_idx]
        positions = agent['positions']
        for position in positions:
            if position['id'] == position_id or position['asset'] == asset:
                start_new_position = False
                position['qty'] += prec(qty, self.assets[side['base']]['decimals'])
                enter = await self.new_enter(side['agent'], asset, qty, side['dt'], side['type'], basis)
                position['enters'].append(enter)
                return {'enter_position': enter}
            
        if start_new_position:
            new_position = await self.new_position(side, asset, qty, basis)
            positions.append(new_position) 
            return {'enter_position': new_position['enters'][0]}
        
    async def exit_position(self, side, asset, qty, agent_idx) -> None:
        exit_transaction = side.copy()
        agent = self.agents[agent_idx]
        positions = agent['positions']
        #NOTE: this should be refactored, the logic is too complex and the use of asset and qty is confusing on the buy side exits, since qty is referring to amount of the quote asset or "quote_flow"
        self.logger.debug(f"exit position {side['agent']} {asset} {qty} {side['type']}")
        exit_transaction['qty'] = abs(qty)
        while exit_transaction['qty'] > 0:
            if len(positions) == 0: break
            self.logger.debug(f"number of positions: {len(positions)}")
            for position in positions:
                if position['asset'] != asset: continue
                if position['qty'] <= 0:
                    self.logger.warning(f"position qty is 0 {position['id']} {side['agent']} {side['type']} {position['asset']} {position['qty']}")
                    continue
                enters = position['enters']
                if len(enters) == 0: 
                    self.logger.warning(f"no enters for {position['id']}")
                    continue
                # self.logger.debug(f"exiting from enters: {position['enters']}")
                for enter in enters:
                    exit = {
                        'id': str(UUID()),
                        'agent': agent['name'],
                        'asset': asset,
                        'dt': exit_transaction['dt'],
                        'enter_id': enter['id'],
                    }
                    if asset == self.default_currency['symbol']:
                        # if this is exiting a quote currency, we calculate it's basis...
                        exit['basis'] = {
                            'basis_initial_unit': side['quote'],
                            'basis_per_unit': abs(exit_transaction['price']),
                            'basis_txn_id': exit_transaction['id'], #NOTE this txn is stored here -> self.agents[agent_idx]['_transactions']
                            'basis_date': exit['dt']
                        }
                    else:
                        # ...otherwise, pass the enter basis along
                        exit['basis'] = enter['basis']
                        if exit['basis']['basis_initial_unit'] != side['quote']:
                            # chain basis and update if needed
                            # e.g. USD (exit, set basis) -> BTC (enter, consume basis) -> BTC (exit, retain basis) -> ETH (enter, pass basis and adjust to ETH)
                            cost_basis_per_unit = prec((enter['basis']['basis_per_unit'] * abs(side['quote_flow'])) / abs(side['qty']), self.assets[side['quote']]['decimals'])
                            exit['basis']['basis_per_unit'] = cost_basis_per_unit

                    if enter['qty'] >= exit_transaction['qty']:
                        exit['qty'] = prec(exit_transaction['qty'], self.assets[asset]['decimals'])
                        enter['qty'] -= prec(exit_transaction['qty'], self.assets[asset]['decimals'])
                        position['qty'] -= prec(exit_transaction['qty'], self.assets[asset]['decimals'])
                        self.logger.info(f'full exit, {position["id"]}: {exit["qty"]} remaining {position["qty"]}')
                        exit_transaction['qty'] = 0
                        position['exits'].append(exit)
                        return {'exit_position': exit}
                    
                    elif enter['qty'] > 0:
                        # partial exit
                        exit_transaction['qty'] -= prec(enter['qty'], self.assets[asset]['decimals'])
                        exit['qty'] = prec(enter['qty'], self.assets[asset]['decimals'])
                        enter['qty'] = 0
                        position['qty'] -= prec(enter['qty'], self.assets[asset]['decimals'])
                        self.logger.info(f'partial exit, {position["id"]}: {exit["qty"]} remaining {position["qty"]}')
                        position['exits'].append(exit)

            self.logger.error(f"no positions to exit for {side['agent']} {side['order_id']} {asset} {qty} {side['type']}")        
            return {'error': 'no positions to exit'}     
        self.logger.error(f"unable to find viable exit {side['agent']} {side['order_id']} {asset} {qty} {side['type']}")        
        return {'error': 'unable to find viable exit'}                            

    async def update_assets(self, asset, amount, agent_idx) -> None:
        if asset in self.agents[agent_idx]['assets']:
            self.agents[agent_idx]['assets'][asset] += prec(amount, self.assets[asset]['decimals'])
        else: 
            self.agents[agent_idx]['assets'][asset] = prec(amount, self.assets[asset]['decimals'])
        self.logger.debug(f"updated assets for {self.agents[agent_idx]['name']}: {asset} {self.agents[agent_idx]['assets'][asset]}")

    async def update_frozen_assets(self, agent_idx, asset, order_id, qty, fee=0) -> None:
        """
        Moves the assets exchanged and pays exchange fees
        """
        if asset not in self.agents[agent_idx]['frozen_assets']:
            return {'error': 'asset not found'}
        for frozen_asset_idx, frozen_asset in enumerate(self.agents[agent_idx]['frozen_assets'][asset]):
            if frozen_asset['order_id'] != order_id:
                continue
            
            qty = prec(abs(qty), self.assets[asset]['decimals'])
            fee = prec(abs(fee), self.assets[asset]['decimals'])

            if self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty'] < qty:
                self.logger.error(f"not enough frozen qty for {order_id} has {self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty']} needs {qty}")
                return {'error': 'not enough frozen'}
            else:
                self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty'] -= qty

            if fee > 0 and self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'] < fee:
                self.logger.error('frozen exchange fee', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'], 'less than fee', fee, 'for', asset, order_id)
                return {'error': 'not enough frozen exchange fee'}
            else:
                self.logger.info(f'paying exchange fee from frozen for {self.agents[agent_idx]["name"]}: ', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'], 'amount:', fee, asset, order_id)
                self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'] -= fee

                # release any fees if the order has been fully filled 
                if self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty'] <= 0: 
                    if self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'] > 0:
                        self.logger.debug('releasing frozen exchange fee', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'], 'for', asset, order_id)
                        self.agents[agent_idx]['assets'][asset] += self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee']
                        self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'] = 0
                    if self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee'] > 0:
                        self.logger.debug('releasing frozen network fee', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee'], 'for', asset, order_id)
                        self.agents[agent_idx]['assets'][asset] += self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee']
                        self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_network_fee'] = 0

                # update the exchange's fees collected
                if asset not in self.fees.fees_collected:
                    self.fees.fees_collected[asset] = fee
                else:
                    self.fees.fees_collected[asset] += fee
                return {'update_frozen_assets': 'updated'}
        self.logger.error(f"order_id {order_id} not found in frozen assets for {asset}")
        return {'error': 'order not found'}
                  
    async def update_agents(self, transaction, accounting, position_id) -> None:
        for side in transaction:
            self.logger.debug('updating', side['type'], 'side')
            if len(self.agents) == 0:
                return {'update_agents': 'no agents'}
            agent_idx = await self.get_agent_index(side['agent'])
            if agent_idx is None:
                self.logger.error('no agents found for', side['agent'], side['type'])
                return {'update_agents': 'agent not found'}
            #TODO: maybe don't need to track transactions... is also in trade_log... check if needed for taxation
            self.agents[agent_idx]['_transactions'].append(side)
            if 'init_seed_' in self.agents[agent_idx]['name']:
                continue
            if side['type'] == 'buy':
                frozen_unlocked = await self.update_frozen_assets(agent_idx, side['quote'], side['order_id'], side['quote_flow'], side['fee'])
                if 'error' in frozen_unlocked:
                    self.logger.error('frozen assets not unlocked', frozen_unlocked)
                    return {'update_agents': 'frozen assets not unlocked'}
                self.logger.debug(f"updating assets for buy: {side['order_id']}, {side['agent']} bought {side['base']} {side['qty']} with {side['quote']} {side['quote_flow']}")                      
                await self.update_assets(side['base'], side['qty'], agent_idx)
                await self.sort_positions(agent_idx, accounting)  
                exit = await self.exit_position(side, side['quote'], side['quote_flow'], agent_idx)
                if 'error' in exit:
                    return {'update_agents': 'unable to exit position'}
                enter = await self.enter_position(side, side['base'], side['qty'], agent_idx, position_id, basis=exit['exit_position']['basis'])

            elif side['type'] == 'sell':
                frozen_unlocked = await self.update_frozen_assets(agent_idx, side['base'], side['order_id'], side['qty'], side['fee'])
                if 'error' in frozen_unlocked:
                    self.logger.error('frozen assets not unlocked', frozen_unlocked)
                    return {'update_agents': 'frozen assets not unlocked'}
                self.logger.debug(f"updating assets for sell: {side['order_id']}, {side['agent']} received {side['quote']} {side['quote_flow']} for {side['base']} {side['qty']}")
                await self.update_assets(side['quote'], side['quote_flow'], agent_idx)
                # we cannot know if it it from this order or a previous order, so we need to track it
                await self.sort_positions(agent_idx, accounting)
                exit = await self.exit_position(side, side['base'], side['qty'], agent_idx)
                if 'error' in exit:
                    return {'update_agents': 'unable to exit position'}
                enter = await self.enter_position(side, side['quote'], side['quote_flow'], agent_idx, None, basis=exit['exit_position']['basis'])
                if side['quote'] == self.default_currency['symbol']:
                    #NOTE: basis represents the initial default quote currency amount (quote_flow) traded for the first enter in the chain
                    # consider the following trade chain:
                    # USD (exit, basis) -> BTC (enter, consume basis) -> BTC (exit, retain basis) -> ETH (enter, passed basis)
                    basis_amount = abs(side['qty']) * exit['exit_position']['basis']['basis_per_unit']
                    await self.taxable_event(self.agents[agent_idx], side['quote_flow'], side['dt'], basis_amount, exit['exit_position']['basis']['basis_date'])
            else:
                self.logger.error('side type not recognized', side['type'])
                return {'update_agents': 'side type not recognized'}
            self.logger.info('updated_agent', side, self.agents[agent_idx]['name'])
            # self.logger.debug('updated_agent', side, self.agents[agent_idx]['name'], self.agents[agent_idx]['assets'], self.agents[agent_idx]['frozen_assets'])

    async def get_agents_holding(self, asset) -> list:
        agents_holding = []
        for agent in self.agents:
            if asset in agent['assets']:
                agents_holding.append(agent['name'])
            elif asset in agent['frozen_assets']:
                agents_holding.append(agent['name'])
        return agents_holding

    async def total_cash(self) -> float:
        """
        returns the total of the default quote currency across all agents
        """
        total = 0
        for agent in self.agents:
            if 'init_seed' not in agent['name']:
                total += agent['assets'][self.default_currency['symbol']]
        return total

    async def agents_assets(self) -> list:
        """
        returns a list of all agents and their assets
        """
        info = []
        for agent in self.agents:
            if agent['name'] != 'init_seed':
                last_action = None
                if len(agent['_transactions']) > 0:
                    last_action =agent['_transactions'][-1]['type']
                info.append({agent['name']: {'assets':agent['assets'], 'last_action': last_action }})
        return info

    async def agent_has_assets(self, agent, asset, qty) -> bool:
        agent_assets = (await self.get_assets(agent))
        if asset not in agent_assets['assets']:
            self.logger.error(f'asset not found for {agent} {asset} {agent_assets["assets"]}')
            return False
        elif agent_assets['assets'][asset] < qty:
            self.logger.warning(f'Not enough {asset}, agent {agent} needs {qty} has {agent_assets["assets"][asset]}')
            return False
        else: 
            return True
    
    async def agent_has_assets_frozen(self, agent, asset, order_id, qty, exchange_fee, network_fee) -> bool:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is None:
            return False
        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.logger.warning(agent, 'asset not found', asset)
            return False
        if len(self.agents[agent_idx]['frozen_assets'][asset]) == 0:
            self.logger.warning(agent, 'no frozen assets', asset)
            return False
        for frozen_asset in self.agents[agent_idx]['frozen_assets'][asset]:
            if frozen_asset['order_id'] == order_id:
                if frozen_asset['frozen_qty'] < qty:
                    self.logger.warning(f"Insufficient Qty: {agent} for {order_id} frozen { frozen_asset['frozen_qty']} needs {qty}")
                    return False
                if frozen_asset['frozen_exchange_fee'] < exchange_fee:
                    self.logger.warning(f"Insufficient Exchange Fee: {agent} {order_id} frozen { frozen_asset['frozen_exchange_fee']} needs {exchange_fee}")
                    self.logger.warning(f"{self.books}")
                    return False
                if frozen_asset['frozen_network_fee'] < network_fee:
                    self.logger.warning(f"Insufficient Network Fee:{agent} {order_id} frozen { frozen_asset['frozen_network_fee']} needs {network_fee}")
                    return False
                self.logger.debug(f"Frozen Qty:{agent} {order_id} frozen {asset} { frozen_asset['frozen_qty']} greater than {qty}")
                return True
        return False
            
    async def agent_has_cash(self, agent, amount, qty) -> bool:
        return await self.agent_has_assets(agent, self.default_currency['symbol'], amount * qty)

    async def agents_cash(self) -> list:
        """
        returns a list of all agents and their cash
        """
        info = []
        for agent in self.agents:
            if agent['name'] != 'init_seed' and self.default_currency['symbol'] in agent['assets']:
                info.append({agent['name']: {'cash':agent['assets'][self.default_currency['symbol']]}})
        return info

    async def get_cash(self, agent_name) -> dict:
        agent_info = await self.get_agent(agent_name)
        return {'cash':agent_info['assets'][self.default_currency['symbol']]}

    async def get_assets(self, agent) -> dict:
        agent_info = await self.get_agent(agent)
        return {'assets': agent_info['assets'], 'frozen_assets': agent_info['frozen_assets']}

    async def add_asset(self, agent, asset, amount, note=''):
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            side = {'id': str(UUID()), 'agent':agent, 'quote_flow':0, 'price': 0, 'base': asset, 'quote': self.default_currency['symbol'], 'qty': amount, 'fee':0, 'dt': self.datetime, 'type': note}
            basis ={
                'basis_initial_unit': self.default_currency['symbol'],
                'basis_per_unit': 0,
                'basis_txn_id': 'seed',
                'basis_date': self.datetime
            }
            await self.enter_position(side, asset, amount, agent_idx, str(UUID()), basis)
            await self.update_assets(asset, amount, agent_idx)
            return {asset: self.agents[agent_idx]['assets'][asset]}
        else:
            return {'error': 'agent not found'}

    async def remove_asset(self, agent, asset, amount, note='') -> dict:
        amount = prec(amount, self.assets[asset]['decimals'])
        if amount < 0:
            return {'error': 'amount must be positive'}
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            qty = prec(amount, self.assets[asset]['decimals'])
            side = {'id': str(UUID()), 'agent':agent,'quote_flow':0, 'order_id':'remove_asset_'+get_random_string(), 'price': 0, 'base':asset, 'quote':self.default_currency['symbol'], 'qty': -qty, 'fee':0, 'dt': self.datetime, 'type': 'sell'}
            exit = await self.exit_position(side, asset, -qty, agent_idx)
            if 'error' in exit:
                return exit
            await self.update_assets(asset, -qty, agent_idx)
            return {asset: self.agents[agent_idx]['assets'][asset]}
        else:
            return {'error': 'agent not found'}

    async def add_cash(self, agent, amount, note='', taxable=False) -> dict:
        return await self.add_asset(agent, self.default_currency['symbol'], amount, note)          
    
    async def remove_cash(self, agent, amount, note='') -> dict:
        return await self.remove_asset(agent, self.default_currency['symbol'], amount, note)

    async def calculate_market_cap(self,base,quote) -> float:
        """
        Calculates the market capitalization of a company
        Args: 
        ticker: the ticker of the asset
        """
        price = 0
        latest_trade = (await self.get_latest_trade(base,quote))
        if "price" in latest_trade:
            price = latest_trade["price"]
        else:
            price = (await self.get_midprice(base+quote))['midprice']

        market_cap = price  * (await self.get_outstanding_shares(base))
        return market_cap
    
    async def get_outstanding_shares(self, asset) -> int:
        """
        Calculates the number of shares outstanding for a given asset
        Args: 
        
        asset: the symbol of the asset
        """
        shares_outstanding = 0
        for agent in self.agents:
            if 'init_seed_' not in agent['name'] and asset in agent['assets']:
                shares_outstanding += agent['assets'][asset]
        return shares_outstanding
  
    async def get_agents_simple(self) -> list:
        """
        Returns a list of agents and their assets
        """
        agents_simple = []
        for agent in self.agents:
            agents_simple.append({'agent':agent['name'],'assets':agent['assets'], 'frozen_assets': agent['frozen_assets']})
        return agents_simple

    async def get_agents_positions(self, asset=None) -> list:
        """
        Returns a list of agents and their positions, optionally for a base quote pair
        """
        agent_positions = []
        for agent in self.agents:
            positions = []
            for position in agent['positions']:
                if asset is None or position['asset'] == asset:
                    positions.append(position)

            agent_positions.append({'agent':agent['name'],'positions':positions})
        return agent_positions
    
    async def get_tickers(self) -> list:
        """
        Returns a list of all asset pairs
        """
        return self.pairs
    
    async def get_pending_transactions(self, limit=100) -> list:
        """
        Returns a list of all pending transactions
        """
        return self.pending_transactions[:limit]
