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
from .types.CryptoLimitOrder import CryptoLimitOrder
from .types.OrderSide import OrderSide
from .types.CryptoFees import Fees
from source.utils.logger import Logger
from source.utils._utils import get_random_string, prec

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class CryptoExchange(Exchange):
    def __init__(self, datetime= None, requester=None, archiver=None):
        super().__init__(datetime=datetime)
        self.archiver = archiver
        self.requester = requester
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
        self.logger.debug('next', self.datetime)
  
    async def archive(self):
        await super().archive()
        self.pairs_archive.store(self.pairs)
        self.wallets_archive.store(self.wallets)

    async def list_asset(self, asset, pair):
        self.pairs.append({'base': asset, 'quote': pair['asset']})
        ticker = pair['ticker']

        seed_price = prec(pair['seed_price'])
        seed_bid = prec(pair['seed_bid'])
        seed_ask = prec(pair['seed_ask'])
        
        trade = CryptoTrade(asset, pair['asset'], pair['market_qty'], seed_price, 'init_seed_'+ticker, 'init_seed_'+ticker, self.datetime, network_fee={'base': 0, 'quote': 0}, exchange_fee={'base': 0, 'quote': 0})
        self.trade_log.append(trade)

        self.books[ticker] = CryptoOrderBook(ticker)

        buy = CryptoLimitOrder(ticker, prec(seed_price * seed_bid), Decimal('1'), 'init_seed_'+ticker, OrderSide.BUY, self.datetime, exchange_fee=0, network_fee=pair['quote_fee'])
        buy.id = 'init_seed_'+ticker
        await self.freeze_assets('init_seed_'+ticker, pair['asset'], buy.id, pair['quote_qty'], 0, prec(str(buy.network_fee_per_qty*1)))
        self.books[ticker].bids.insert(0, buy)
  
        sell = CryptoLimitOrder(ticker, prec(seed_price * seed_ask), pair['market_qty'], 'init_seed_'+ticker, OrderSide.SELL, self.datetime, exchange_fee=0, network_fee=pair['base_fee'])
        sell.id = 'init_seed_'+ticker
        await self.freeze_assets('init_seed_'+ticker, asset, sell.id, pair['market_qty'], 0, prec(str(sell.network_fee_per_qty*pair['market_qty'])))
        self.books[ticker].asks.insert(0, sell)
        
        self.assets[asset] = {'type': 'crypto', 'id' : str(UUID())}
        self.wallets[asset] = await self.generate_address()

        for agent in self.agents:
            if 'init_seed_' not in agent['name']:
                agent['wallets'][asset] = await self.generate_address()
        
        self.logger.info('listed asset', asset, pair['asset'], pair['market_qty'], seed_price, seed_bid, seed_ask)
                
    async def create_asset(self, symbol: str, pairs=[]) -> dict:
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

        for pair in pairs:
            ticker = symbol+pair['asset']
            pair['ticker'] = ticker

            pair['seed_price'] = prec(pair['seed_price'])
            pair['seed_bid'] = prec(pair['seed_bid'])
            pair['seed_ask'] = prec(pair['seed_ask'])
            pair['market_qty'] = prec(pair['market_qty'])
            pair['base_fee'] = prec(prec('.001') * pair['market_qty'])
            pair['quote_fee'] = prec('.001')
            pair['quote_qty'] = prec(pair['market_qty'] * pair['seed_price'])

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
            added_base = await self.add_asset('init_seed_'+ticker, symbol, prec(pair['market_qty'] + pair['base_fee']))
            added_quote = await self.add_asset('init_seed_'+ticker, pair['asset'], prec(pair['quote_qty'] + pair['quote_fee']))
                        
            self.logger.info(f'adding initial assets {added_base}, quote {added_quote}')
            await self.list_asset(symbol, pair)

        return {'asset_created': symbol, 'pairs': pairs}
        
    async def _process_trade(self, base, quote, qty, price, buyer, seller, seller_order_id, buyer_order_id, accounting='FIFO', exchange_fee={'quote':'0.0', 'base':'0.0'}, network_fee={'quote':'0.0', 'base':'0.0'}, position_id=None):
        try:
            if buyer == 'init_seed_'+base+quote: 
                self.logger.debug('waive exchange fees for init_seed_'+base+quote)
                exchange_fee['quote'] = prec('0.0')
            if seller == 'init_seed_'+base+quote:
                self.logger.debug('waive exchange fees for init_seed_'+base+quote)
                exchange_fee['base'] = prec('0.0')
            
            if not (await self.agent_has_assets_frozen(buyer, quote, buyer_order_id, prec(price*qty), exchange_fee['quote'], network_fee['quote'])):
                self.logger.error(f'Unable to Process buy_order: {buyer_order_id} / sell order: {seller_order_id} ')
                return {'error': 'insufficient funds', 'buyer': buyer}
            if not (await self.agent_has_assets_frozen(seller, base, seller_order_id, qty,exchange_fee['base'], network_fee['base'])):
                self.logger.error(f'Unable to Process sell order: {seller_order_id} / buy_order: {buyer_order_id}')
                return {'error': 'insufficient funds', 'seller': seller}

            seller_wallet = (await self.get_agent(seller))['wallets'][base]
            buyer_wallet = (await self.get_agent(buyer))['wallets'][quote]

            pending_base_transaction = await self.requester.add_transaction(asset=base, fee=network_fee['base'], amount=qty, sender=seller_wallet, recipient=buyer_wallet)
            pending_quote_transaction = await self.requester.add_transaction(asset=quote, fee=network_fee['quote'], amount=prec(qty*price), sender=buyer_wallet, recipient=seller_wallet)

            if('error' in pending_base_transaction or pending_base_transaction['sender'] == 'error' or 'error' in pending_quote_transaction or pending_quote_transaction['sender'] == 'error'):
                return {'error': 'add_transaction_failed'}
            
            await self.pay_network_fees(buyer, quote, buyer_order_id, network_fee['quote'])
            await self.pay_network_fees(seller, base, seller_order_id,  network_fee['base'])

            txn_time = self.datetime
            transaction = [
                {'id': str(UUID()), 'agent':buyer, 'order_id':buyer_order_id, 'quote_flow':prec(-qty*price), 'price': price, 'base': base, 'quote': quote, 'qty': qty, 'fee':exchange_fee['quote'], 'network_fee':network_fee['quote'], 'dt': txn_time, 'type': 'buy'},
                {'id': str(UUID()), 'agent':seller, 'order_id': seller_order_id, 'quote_flow':prec(qty*price), 'price': price, 'base': base, 'quote': quote, 'qty': -qty, 'fee':exchange_fee['base'], 'network_fee':network_fee['base'], 'dt': txn_time, 'type': 'sell'}
            ]

            self.pending_transactions.append({'base_txn': pending_base_transaction, 'quote_txn': pending_quote_transaction, 'exchange_txn': transaction, 'accounting': accounting, 'position_id': position_id})
            self.logger.debug('processing trade', transaction)
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
        network_fee = {'base': prec(base_transaction['fee']), 'quote': prec(quote_transaction['fee'])}
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

    async def get_best_ask(self, ticker:str) -> CryptoLimitOrder:
        """retrieves the current best ask in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset.

        returns:
            CryptoLimitOrder
        """
        if self.books[ticker].asks and self.books[ticker].asks[0]:
            return self.books[ticker].asks[0]
        else:
            return CryptoLimitOrder(ticker, 0, 0, 'null_quote', OrderSide.SELL, self.datetime)

    async def get_best_bid(self, ticker:str) -> CryptoLimitOrder:
        """retrieves the current best bid in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset.

        returns:
            CryptoLimitOrder
        """
        if self.books[ticker].bids and self.books[ticker].bids[0]:
            return self.books[ticker].bids[0]
        else:
            return CryptoLimitOrder(ticker, 0, 0, 'null_quote', OrderSide.BUY, self.datetime)

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
        amount_to_freeze = prec(abs(qty)+exchange_fee+network_fee)
        if self.agents[agent_idx]['assets'][asset] < amount_to_freeze:
            self.logger.error(f'insufficient funds available to freeze for {agent}, {asset} needs: {amount_to_freeze} has: {self.agents[agent_idx]["assets"][asset]} ')
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
                        prec(existing_frozen_assets['frozen_exchange_fee'])
                    if network_fee > 0:
                        existing_frozen_assets['frozen_network_fee'] += network_fee
                    self.logger.debug('frozen assets updated', agent, asset, order_id, 'qty:', existing_frozen_assets['frozen_qty'], 'exchange_fee:', existing_frozen_assets['frozen_exchange_fee'],'network_fee:', existing_frozen_assets['frozen_network_fee'])    
                    return {'success': 'frozen assets updated'}
            self.logger.debug('freezing assets', agent, asset, order_id, 'qty: ', qty, 'exchange_fee: ', exchange_fee,'network_fee: ', network_fee)
            self.agents[agent_idx]['frozen_assets'][asset].append(frozen_assets)
        return {'success': 'assets frozen'}

    async def unfreeze_assets(self, agent, asset, order_id, qty=0, exchange_fee=0, network_fee=0) -> None:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is None:
            self.logger.error('unfreezing agent not found', agent)
            return {'error': 'agent not found'}
        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.logger.error('no asset available to unfreeze', asset, qty, agent, order_id)
            return {'error': 'no asset available to unfreeze'}
        for frozen_assets in self.agents[agent_idx]['frozen_assets'][asset]:
            if frozen_assets['order_id'] != order_id:
                continue
            if qty > 0:
                if frozen_assets['frozen_qty'] <= 0:
                    self.logger.error('no qty assets available to unfreeze', asset, qty, agent, order_id)
                    return {'error': 'no asset available to unfreeze'}
                frozen_assets['frozen_qty'] -= abs(qty)
                self.agents[agent_idx]['assets'][asset] += abs(qty)
            if exchange_fee > 0:
                if frozen_assets['frozen_exchange_fee'] <= 0:
                    self.logger.error('no exchange fee assets available to unfreeze', asset, exchange_fee, agent, order_id)
                    return {'error': 'no asset available to unfreeze'}
                frozen_assets['frozen_exchange_fee'] -= abs(exchange_fee)
                self.agents[agent_idx]['assets'][asset] += abs(exchange_fee)
            if network_fee > 0:
                if frozen_assets['frozen_network_fee'] <= 0:
                    self.logger.error('no network fee assets available to unfreeze', asset, network_fee, agent, order_id)
                    return {'error': 'no asset available to unfreeze'}
                frozen_assets['frozen_network_fee'] -= abs(network_fee)
                self.agents[agent_idx]['assets'][asset] += abs(network_fee)
            self.logger.debug(f"unfreezing assets {agent} {asset} {order_id} qty {qty} exchange_fee {exchange_fee} network_fee {network_fee}")
            return {'success': 'assets unfrozen'}
        self.logger.error('order id does not match frozen order', asset, qty, agent)
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
            fee = prec(fee)
        
        smallest_fee = min(fees)
        median_fee = prec(sum(fees)/len(fees))
        largest_fee = max(fees)
        
        return {'slow': smallest_fee, 'standard': median_fee, 'fast': largest_fee}

    async def set_network_fee(self, price, speed='standard') -> Decimal:
        fees = await self.get_network_fees()
        if 'error' in fees:
            return fees
        if speed == 'budget':
            return prec(fees['slow'] - (fees['slow'] * (price/100)))
        elif speed == 'slow':
            return fees['slow']
        elif speed == 'standard':
            return fees['standard']
        elif speed == 'fast':
            return fees['fast']
        elif speed == 'rush':
            return prec(fees['fast'] + (fees['fast'] * (price/100)))

    async def create_new_order(self, base, quote, price, qty, creator, side, fee, tif, position_id) -> CryptoLimitOrder:
        qty = prec(qty)
        price = prec(price)
        fee = prec(fee)
        if side == OrderSide.BUY:   
            new_order = CryptoLimitOrder(base+quote, price, qty, creator, OrderSide.BUY, self.datetime, exchange_fee=prec(self.fees.taker_fee(qty*price)), network_fee=fee, position_id=position_id, fills=[])
        else:
            new_order = CryptoLimitOrder(base+quote, price, qty, creator, OrderSide.SELL, self.datetime, exchange_fee=prec(self.fees.taker_fee(qty)), network_fee=fee, position_id=position_id, fills=[])
        if price <= 0:
            new_order.status='error' 
            new_order.accounting ='price_must_be_greater_than_zero'
            return new_order     
        if(qty <= 0):
            new_order.status='error' 
            new_order.accounting ='qty_must_be_greater_than_zero'
            return new_order
        if fee <= 0:
            new_order.status='error'
            new_order.accounting ='fee_must_be_greater_than_zero'
            return new_order
        else:
            new_order.base = base
            new_order.quote = quote
            new_order.exchange_fees_due = 0
            new_order.unfilled_qty = qty 
            new_order.network_fee_per_qty = prec(fee/qty)
            old_fee = fee
            new_fee = prec(new_order.network_fee_per_qty * qty)
            if new_fee != old_fee:
                self.logger.debug(f"network fee changed: {new_order.id} new fee: {new_fee} old fee: {old_fee} new fee per qty: {new_order.network_fee_per_qty} qty:{qty}")
                new_order.network_fee = new_fee
                new_order.remaining_network_fee = new_fee
                #TODO: maybe do a ping back to user to confirm order before executing?
            self.logger.info(f'created new order: {new_order.id} {new_order.type} {new_order.base} qty:{new_order.qty} price: {new_order.price} {new_order.fills}')            
            return new_order

    async def limit_buy(self, base: str, quote:str, price: float, qty: int, creator: str, fee='0.0', tif='GTC', position_id=UUID()) -> CryptoLimitOrder:
        if len(self.books[base+quote].bids) >= self.max_bids:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='max_bid_depth_reached')
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='max_pending_transactions_reached')
        #NOTE: the fee arg here is the network fee... consider renaming
        new_order = await self.create_new_order(base, quote, price, qty, creator, OrderSide.BUY, fee, tif, position_id)
        if new_order.status == 'error': return new_order
        has_asset = await self.agent_has_assets(creator, quote, prec((new_order.qty * new_order.price)+new_order.network_fee+new_order.exchange_fee))      
        ticker = base+quote
        if has_asset:
            await self.freeze_assets(creator, quote, new_order.id, prec(new_order.qty * new_order.price), new_order.exchange_fee, new_order.network_fee)
            while new_order.unfilled_qty > 0:
                self.logger.debug(f'limit buy unfilled {new_order.unfilled_qty}' )
                if tif == 'TEST':
                    break
                best_ask = await self.get_best_ask(ticker)
                if best_ask.creator != 'null_quote' and best_ask.creator != creator and new_order.price >= best_ask.price:
                    trade_qty = prec(min((new_order.unfilled_qty, best_ask.qty)))
                    taker_fee = prec(self.fees.taker_fee(trade_qty*best_ask.price))
                    partial_network_fee = prec(new_order.network_fee_per_qty * trade_qty)
                    seller_network_fee = best_ask.network_fee_per_qty * trade_qty 
                    seller_exchange_fee = prec(best_ask.exchange_fee_per_qty * trade_qty)
                    self.logger.debug(f"best ask {best_ask.qty} {best_ask.network_fee} {seller_network_fee} trade_qty: {trade_qty}")
                    processed = await self._process_trade(base, quote, trade_qty, best_ask.price, creator, best_ask.creator, best_ask.id, new_order.id, exchange_fee={'quote':taker_fee, 'base': seller_exchange_fee}, network_fee={'quote': partial_network_fee, 'base': seller_network_fee}, position_id=position_id)
                    if('error' in processed):
                        #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                        break
                    new_order.fills.append({'qty': trade_qty, 'price': best_ask.price, 'fee': taker_fee, 'creator': best_ask.creator})
                    new_order.unfilled_qty -= trade_qty
                    new_order.remaining_network_fee -= partial_network_fee
                    new_order.exchange_fees_due += taker_fee
                    self.books[ticker].asks[0].qty -= trade_qty
                    self.books[ticker].asks[0].exchange_fee -= seller_exchange_fee
                    self.books[ticker].asks[0].remaining_network_fee -= seller_network_fee
                    self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
                    deductions = prec((trade_qty* new_order.price) - (trade_qty*best_ask.price))
                    if deductions > 0:
                        self.logger.debug(f'Unfreezing deductions {deductions} from {creator} {quote} {new_order.id}')
                        await self.unfreeze_assets(creator, quote, new_order.id, qty=deductions)
                    self.logger.debug(f'limit buy new fill {new_order.fills[-1]}')
                else:
                    break
            queue = len(self.books[ticker].bids)
            for idx, order in enumerate(self.books[ticker].bids):
                if new_order.price > order.price:
                    queue = idx
                    break            
            if new_order.unfilled_qty > 0:
                new_amount = prec(new_order.network_fee_per_qty * new_order.unfilled_qty)
                maker_fee = prec(self.fees.maker_fee(new_amount))
                self.logger.info(f'converting to maker: {new_order.id}, amount: {new_amount} unfreezing {new_order.exchange_fee} and freezing: new fee {maker_fee} + fees due {new_order.exchange_fees_due}')
                await self.unfreeze_assets(creator, quote, new_order.id, exchange_fee=new_order.exchange_fee)
                new_exchange_fee = prec(maker_fee+new_order.exchange_fees_due)
                await self.freeze_assets(creator, quote, new_order.id, exchange_fee=new_exchange_fee)
                new_order.qty = new_order.unfilled_qty
                new_order.exchange_fee = maker_fee
                new_order.exchange_fee_per_qty = prec(maker_fee/new_order.qty)                
                self.books[ticker].bids.insert(queue, new_order)
                self.logger.info(f'limit buy queued {new_order.id} {new_order.qty} {new_order.price} {new_order.fills}')
                return new_order
            else:
                if new_order.exchange_fee > new_order.exchange_fees_due:
                    refund_amount = prec(new_order.exchange_fee - new_order.exchange_fees_due)
                    self.logger.debug(f'Unfreezing Fees {refund_amount} from {creator} {quote} {new_order.id}')
                    await self.unfreeze_assets(creator, quote, new_order.id, exchange_fee=refund_amount)
                new_order.status = 'filled_unconfirmed'
                new_order.exchange_fee = new_order.exchange_fees_due
                self.logger.info(f'limit buy filled {new_order.id} {new_order.qty} {new_order.price} {new_order.fills}')
                return new_order
        else:
            new_order.status='error'
            new_order.accounting ='insufficient_assets'
            return new_order
        
    async def limit_sell(self, base: str, quote:str, price: float, qty: int, creator: str, fee='0.0', tif='GTC', accounting='FIFO') -> CryptoLimitOrder:
        if len(self.books[base+quote].asks) >= self.max_asks:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='max_ask_depth_reached')
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='max_pending_transactions_reached')
        #NOTE: the fee arg here is the network fee... consider renaming
        new_order = await self.create_new_order(base, quote, price, qty, creator, OrderSide.SELL, fee, tif, None)
        if new_order.status == 'error': return new_order        
        ticker = base+quote
        has_assets = await self.agent_has_assets(creator, base, prec(new_order.qty+new_order.network_fee+new_order.exchange_fee))
        if has_assets:
            await self.freeze_assets(creator, base, new_order.id, new_order.qty, new_order.exchange_fee, new_order.network_fee)
            # check if we can match trades before submitting the limit order
            while new_order.unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_bid = await self.get_best_bid(ticker)
                if best_bid.creator != 'null_quote' and best_bid.creator != creator and new_order.price <= best_bid.price:
                    trade_qty = prec(min((new_order.unfilled_qty, best_bid.qty)))
                    taker_fee = prec(self.fees.taker_fee(trade_qty))
                    partial_network_fee = prec(new_order.network_fee_per_qty * trade_qty)
                    buyer_network_fee = best_bid.network_fee_per_qty * trade_qty
                    buyer_exchange_fee = prec(best_bid.exchange_fee_per_qty * trade_qty)
                    processed = await self._process_trade(base, quote, trade_qty, best_bid.price, best_bid.creator, creator, new_order.id, best_bid.id, accounting, exchange_fee={'quote': buyer_exchange_fee, 'base': taker_fee}, network_fee={'base':partial_network_fee, 'quote': buyer_network_fee})
                    if('error' in processed):
                        #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                        break
                    new_order.fills.append({'qty': trade_qty, 'price': best_bid.price, 'fee': taker_fee, 'creator': best_bid.creator})
                    new_order.unfilled_qty -= trade_qty
                    new_order.remaining_network_fee -= partial_network_fee
                    new_order.exchange_fees_due += taker_fee
                    self.books[ticker].bids[0].qty -= trade_qty
                    self.books[ticker].bids[0].exchange_fee -= buyer_exchange_fee
                    self.books[ticker].bids[0].remaining_network_fee -= buyer_network_fee
                    self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
                else:
                    break
            queue = len(self.books[ticker].asks)
            for idx, order in enumerate(self.books[ticker].asks):
                if new_order.price < order.price:
                    queue = idx
                    break             
            if new_order.unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(new_order.unfilled_qty)
                
                self.logger.info(f'converting to maker: {new_order.id} amount {new_order.unfilled_qty} unfreezing exchange fee {new_order.exchange_fee} and freezing: new fee {maker_fee} + fees due {new_order.exchange_fees_due}')
                await self.unfreeze_assets(creator, base, new_order.id, exchange_fee=new_order.exchange_fee)
                new_exchange_fee = prec(maker_fee+new_order.exchange_fees_due)
                await self.freeze_assets(creator, base, new_order.id, exchange_fee=new_exchange_fee)
                new_order.qty = new_order.unfilled_qty
                new_order.exchange_fee = maker_fee
                new_order.exchange_fee_per_qty = prec(maker_fee/new_order.qty)
                self.books[ticker].asks.insert(queue, new_order)
                self.logger.info(f'limit sell queued {new_order.id} qty: {new_order.qty} exchange fee: {new_order.exchange_fee} network fee: {new_order.network_fee} price:{new_order.price} fills:{new_order.fills}')
                return new_order
            else:
                if new_order.exchange_fee > new_order.exchange_fees_due:
                    refund_amount = prec(new_order.exchange_fee - new_order.exchange_fees_due)
                    self.logger.debug(f'Unfreezing Fees {refund_amount} from {creator} {base} {new_order.id}')
                    await self.unfreeze_assets(creator, base, new_order.id, exchange_fee=refund_amount)                
                new_order.exchange_fee = new_order.exchange_fees_due
                new_order.status = 'filled_unconfirmed'
                self.logger.info(f'limit sell filled {new_order.id} {new_order.qty} {new_order.price} {new_order.fills}')
                return new_order
        else:
            return CryptoLimitOrder(ticker, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='insufficient_assets')
           
    async def market_buy(self, base: str, quote:str, qty: int, buyer: str, fee='0.0') -> dict:
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return {"market_buy": "max_pending_transactions_reached", "buyer": buyer}
        qty = prec(qty)
        fee = prec(fee)
        if fee <= 0:
            return {"market_buy": "fee_must_be_greater_than_zero", "buyer": buyer}
        if qty <= 0:
            return {"market_buy": "qty_must_be_greater_than_zero", "buyer": buyer}
        order_id = get_random_string()
        ticker = base+quote
        network_fee_per_unit = prec(fee/qty)
        old_fee = fee
        fee = prec(network_fee_per_unit * qty)
        if fee != old_fee:
            self.logger.debug(f"market buy network fee changed: {fee} {old_fee} {network_fee_per_unit} {qty}")
            #TODO: maybe do a ping back to user to confirm order before executing?
        remaining_network_fee =fee
        unfilled_qty = qty
        exchange_fees_paid = 0
        fills = []
        initial_freeze = await self.freeze_assets(buyer, quote, order_id, network_fee=fee)
        if 'error' in initial_freeze:
            return {"market_buy": "initial_freeze_error", "id":order_id, "buyer": buyer}
        for idx, ask in enumerate(self.books[ticker].asks):
            if ask.creator == buyer:
                continue
            trade_qty = prec(min((ask.qty, unfilled_qty)))
            if ask.qty <=0:
                self.logger.debug('ask qty: ', '{0:.18f}'.format(ask.qty), ask.creator, ask.ticker, ask.price, ask.status, ask.accounting)
                continue
            seller_network_fee = ask.network_fee_per_qty * trade_qty
            taker_fee = self.fees.taker_fee(prec(ask.price*trade_qty))
            partial_network_fee = prec(network_fee_per_unit * trade_qty)
            self.logger.debug(f"partial network fee: {partial_network_fee}  per unit: {network_fee_per_unit} units: {trade_qty}")
            order_total = prec((trade_qty*ask.price)+taker_fee)
            has_assets = await self.agent_has_assets(buyer, quote, order_total)
            if has_assets == False: 
                self.logger.warning('insufficient assets', buyer, quote, order_total)
                await self.unfreeze_assets(buyer, quote, order_id, network_fee=remaining_network_fee)
                return {"market_buy": "insufficient assets", "id":order_id, "buyer": buyer}
            buy_total = prec(trade_qty*ask.price)
            self.logger.debug(f"market buy freezing {buy_total} + {taker_fee} ")
            pre_buy_freeze = await self.freeze_assets(buyer, quote, order_id, buy_total, taker_fee)
            if 'error' in pre_buy_freeze:
                await self.unfreeze_assets(buyer, quote, order_id, network_fee=remaining_network_fee)
                return {"market_buy": "pre_buy_freeze_error", "id":order_id, "buyer": buyer}
            if trade_qty == ask.qty:
                seller_exchange_fee = ask.exchange_fee
            else:
                seller_exchange_fee = prec(ask.exchange_fee_per_qty * trade_qty)
            self.logger.debug(f"market buy processing {ticker} qty: {trade_qty} seller exchange fee:{seller_exchange_fee} seller network fee: {seller_network_fee}")
            processed = await self._process_trade(base, quote, trade_qty, ask.price, buyer, ask.creator, ask.id, order_id, exchange_fee={'quote': taker_fee, 'base': seller_exchange_fee}, network_fee={'quote':partial_network_fee, 'base': seller_network_fee})
            if'error' in processed: 
                await self.unfreeze_assets(buyer, quote, order_id, prec(trade_qty*ask.price), taker_fee)
                continue
            self.books[ticker].asks[idx].qty -= trade_qty
            self.books[ticker].asks[idx].exchange_fee -= seller_exchange_fee
            self.books[ticker].asks[idx].remaining_network_fee -= seller_network_fee
            fills.append({'qty': trade_qty, 'price': ask.price, 'fee': taker_fee})
            unfilled_qty -= trade_qty
            exchange_fees_paid += taker_fee
            remaining_network_fee -= partial_network_fee
            if unfilled_qty == 0:
                break
        
        self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
        if unfilled_qty > 0:
            self.logger.debug(f"unfreezing unfilled {unfilled_qty} {quote} {order_id} network fee: {remaining_network_fee}")
            await self.unfreeze_assets(buyer, quote, order_id, network_fee=remaining_network_fee)
        if fills == []:
            return {"market_buy": "no fills", "id": order_id, "buyer": buyer}
        return {"market_buy": ticker, "id": order_id, "buyer": buyer, 'qty': qty, 'exchange_fee':exchange_fees_paid, "network_fee":prec((qty-unfilled_qty) * network_fee_per_unit), "fills": fills}

    async def market_sell(self, base: str, quote:str, qty: int, seller: str, fee='0.0', accounting='FIFO') -> dict:
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return {"market_sell": "max_pending_transactions_reached", "seller": seller}
        qty = prec(qty)
        fee = prec(fee)
        if fee <= 0:
            return {"market_sell": "fee_must_be_greater_than_zero", "seller": seller}
        if qty <= 0:
            return {"market_sell": "qty_must_be_greater_than_zero", "seller": seller}
        order_id = get_random_string()     
        ticker = base+quote
        network_fee_per_unit = prec(fee/qty)
        old_fee = fee
        fee = prec(network_fee_per_unit * qty)
        if fee != old_fee:
            self.logger.debug(f"market sell network fee changed from {old_fee} to {fee} per unit: {network_fee_per_unit} qty: {qty}")
            #TODO: maybe do a ping back to user to confirm order before executing?
        remaining_network_fee =fee
        unfilled_qty = qty
        exchange_fees_paid = 0
        fills = []
        has_assets = await self.agent_has_assets(seller, base, prec(qty+fee))
        if has_assets == False:
            return {"market_sell": "insufficient assets", 'id': order_id, "seller": seller}           
        initial_freeze = await self.freeze_assets(seller, base, order_id, qty=qty, network_fee=fee)
        if 'error' in initial_freeze:
            return {"market_buy": "initial_freeze_error", "id":order_id, "seller": seller}
        for idx, bid in enumerate(self.books[ticker].bids):
            if bid.creator == seller:
                continue
            trade_qty = prec(min((bid.qty, unfilled_qty)))
            buyer_network_fee = bid.network_fee_per_qty * trade_qty
            partial_network_fee = prec(network_fee_per_unit * trade_qty)
            partial_exchange_fee = prec(self.fees.taker_fee(trade_qty))
            if trade_qty == bid.qty:
                buyer_exchange_fee = bid.exchange_fee
            else:
                buyer_exchange_fee = prec(bid.exchange_fee_per_qty * trade_qty)
            self.logger.debug(f"market sell freezing exchange fee {partial_exchange_fee} ")
            pre_sell_freeze = await self.freeze_assets(seller, base, order_id, exchange_fee=partial_exchange_fee)
            if 'error' in pre_sell_freeze:
                self.logger.error('pre_sell_freeze_error', seller, base, order_id, partial_exchange_fee)
                await self.unfreeze_assets(seller, base, order_id, qty=unfilled_qty, network_fee=remaining_network_fee)
                return {"market_sell": "pre_sell_freeze_error", "id":order_id, "seller": seller}                            
            processed = await self._process_trade(base, quote, trade_qty,bid.price, bid.creator, seller, order_id, bid.id, accounting, exchange_fee={'base': partial_exchange_fee, 'quote': buyer_exchange_fee}, network_fee={'base': partial_network_fee, 'quote': buyer_network_fee} )
            if'error' in processed:
                await self.unfreeze_assets(seller, base, order_id, exchange_fee=partial_exchange_fee)
                continue
            fills.append({'qty': trade_qty, 'price': bid.price, 'fee': partial_exchange_fee})
            unfilled_qty -= trade_qty
            exchange_fees_paid += partial_exchange_fee
            remaining_network_fee -= partial_network_fee
            self.books[ticker].bids[idx].qty -= prec(trade_qty)
            self.books[ticker].bids[idx].exchange_fee -= buyer_exchange_fee
            if unfilled_qty == 0:
                break
        self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
        if unfilled_qty > 0 :
            refund_network_fee = prec(network_fee_per_unit*unfilled_qty)
            await self.unfreeze_assets(seller, base, order_id, qty=unfilled_qty, network_fee=refund_network_fee)
        if fills == []:
            return {"market_sell": "no fills", "id": order_id, "seller": seller}                       
        return {"market_sell": ticker, "id": order_id, "seller": seller, 'qty': qty, 'exchange_fee':exchange_fees_paid, "network_fee":prec((qty-unfilled_qty) * network_fee_per_unit), "fills": fills }

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
            if canceled['cancelled_order']['type'] == 'limit_buy':
                await self.unfreeze_assets(creator, quote, order_id, qty*price, exchange_fee , network_fee)
            elif canceled['cancelled_order']['type'] == 'limit_sell':
                await self.unfreeze_assets(creator, base, order_id, qty , exchange_fee , network_fee)
            else:
                return {'error': 'unable to cancel, order type not recognized', 'id': id}
        return canceled
    
    async def cancel_all_orders(self, base, quote, creator) -> list:
        ticker = base+quote
        # canceled = await super().cancel_all_orders(creator, ticker)
        canceled = []
        async def cancel_bid(bid, creator):
            if bid.creator == creator:
                await self.unfreeze_assets(creator, quote, bid.id, prec(bid.qty*bid.price) , bid.exchange_fee , bid.network_fee)
                canceled.append(bid.id)
                return False
            else:
                return True
            
        async def cancel_ask(ask, creator):
            if ask.creator == creator:
                await self.unfreeze_assets(creator, base, ask.id, ask.qty , ask.exchange_fee , ask.network_fee)
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
                'qty': prec(initial_assets[asset]), 
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
            initial_assets[asset] = prec(initial_assets[asset])
  
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
            'initial_qty': prec(qty),
            'qty': prec(qty),
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
            'qty': prec(qty),
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
                position['qty'] += prec(qty)
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
        self.logger.debug(f"exit position {side['agent']} {asset} {side['qty']} {side['type']}")
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
                            cost_basis_per_unit = prec((enter['basis']['basis_per_unit'] * abs(side['quote_flow'])) / abs(side['qty']))
                            self.logger.info(f"cost_basis_per_unit: {cost_basis_per_unit:.16f}")
                            exit['basis']['basis_per_unit'] = cost_basis_per_unit

                    if enter['qty'] >= exit_transaction['qty']:
                        exit['qty'] = prec(exit_transaction['qty'])
                        enter['qty'] -= prec(exit_transaction['qty'])
                        position['qty'] -= prec(exit_transaction['qty'])
                        self.logger.info(f'full exit, {position["id"]}: {exit["qty"]} remaining {position["qty"]}')
                        exit_transaction['qty'] = 0
                        position['exits'].append(exit)
                        return {'exit_position': exit}
                    
                    elif enter['qty'] > 0:
                        # partial exit
                        exit_transaction['qty'] -= prec(enter['qty'])
                        exit['qty'] = prec(enter['qty'])
                        enter['qty'] = 0
                        position['qty'] -= prec(enter['qty'])
                        self.logger.info(f'partial exit, {position["id"]}: {exit["qty"]} remaining {position["qty"]}')
                        position['exits'].append(exit)

            self.logger.error(f"no positions to exit for {side['agent']} {side['order_id']} {asset} {qty} {side['type']}")        
            return {'error': 'no positions to exit'}     
        self.logger.error(f"unable to find viable exit {side['agent']} {side['order_id']} {asset} {qty} {side['type']}")        
        return {'error': 'unable to find viable exit'}                            

    async def update_assets(self, asset, amount, agent_idx) -> None:
        if asset in self.agents[agent_idx]['assets']:
            self.agents[agent_idx]['assets'][asset] += prec(amount)
        else: 
            self.agents[agent_idx]['assets'][asset] = prec(amount)
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
            
            qty = prec(abs(qty))
            fee = prec(abs(fee))

            if self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty'] < qty:
                self.logger.error(f"not enough frozen for {order_id} has {self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty']} needs {qty}")
                return {'error': 'not enough frozen'}
            else:
                self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_qty'] -= qty

            if fee > 0 and self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'] < fee:
                self.logger.error('frozen exchange fee', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'], 'less than fee', fee, 'for', asset, order_id)
                return {'error': 'not enough frozen exchange fee'}
            else:
                self.logger.info('paying exchange fee from frozen:', self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'], 'amount:', fee, asset, order_id)
                self.agents[agent_idx]['frozen_assets'][asset][frozen_asset_idx]['frozen_exchange_fee'] -= fee
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
                self.logger.debug(f"updating assets for buy: {side['order_id']} {side['base']} {side['qty']} for {side['agent']}")                      
                await self.update_assets(side['base'], side['qty'], agent_idx)
                await self.sort_positions(agent_idx, accounting)  
                exit = await self.exit_position(side, side['quote'], side['quote_flow'], agent_idx)
                if 'error' in exit:
                    return {'update_agents': 'unable to exit position'}
                enter = await self.enter_position(side, side['base'], side['qty'], agent_idx, position_id, basis=exit['exit_position']['basis'])

            elif side['type'] == 'sell':
                self.logger.debug(f"updating Sell Side {side['order_id']} {side['base']} {side['qty']} for {side['agent']}")
                frozen_unlocked = await self.update_frozen_assets(agent_idx, side['base'], side['order_id'], side['qty'], side['fee'])
                if 'error' in frozen_unlocked:
                    self.logger.error('frozen assets not unlocked', frozen_unlocked)
                    return {'update_agents': 'frozen assets not unlocked'}
                self.logger.debug(f"updating assets for sell: {side['order_id']} {side['quote']} {side['quote_flow']} for {side['agent']}")
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
        if asset not  in self.agents[agent_idx]['frozen_assets']:
            self.logger.warning(agent, 'asset not found', asset)
            return False
        if len(self.agents[agent_idx]['frozen_assets'][asset]) == 0:
            self.logger.warning(agent, 'no frozen assets', asset)
            return False
        for frozen_asset in self.agents[agent_idx]['frozen_assets'][asset]:
            if frozen_asset['order_id'] == order_id:
                if frozen_asset['frozen_qty'] < qty:
                    self.logger.warning(f"Insufficient Qty: {agent} frozen { frozen_asset['frozen_qty']} needs {qty}")
                    return False
                if frozen_asset['frozen_exchange_fee'] < exchange_fee:
                    self.logger.warning(f"Insufficient Exchange Fee: {agent} frozen { frozen_asset['frozen_exchange_fee']} needs {exchange_fee}")
                    return False
                if frozen_asset['frozen_network_fee'] < network_fee:
                    self.logger.warning(f"Insufficient Network Fee:{agent} frozen { frozen_asset['frozen_network_fee']} needs {network_fee}")
                    return False
                self.logger.debug(f"Frozen Qty:{agent} frozen {asset} { frozen_asset['frozen_qty']} greater than {qty}")
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
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            qty = prec(amount)
            side = {'id': str(UUID()), 'agent':agent,'quote_flow':0, 'price': 0, 'base':asset, 'quote':self.default_currency['symbol'], 'qty': -qty, 'fee':0, 'dt': self.datetime, 'type': 'sell'}
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
