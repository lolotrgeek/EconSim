import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from uuid import uuid4 as UUID
import random, string, time
from decimal import Decimal, getcontext
from rich import print
from source.Archive import Archive
from .Exchange import Exchange
from .types.CryptoOrderBook import CryptoOrderBook
from .types.CryptoTrade import CryptoTrade
from .types.CryptoLimitOrder import CryptoLimitOrder
from .types.OrderSide import OrderSide
from .types.Fees import Fees

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.


class CryptoExchange(Exchange):
    def __init__(self, datetime= None, requester=None, archiver=None):
        super().__init__(datetime=datetime)
        getcontext().prec = 18 #NOTE: this is the precision of the decimal module, it is set to 18 to match the precision of the blockchain
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

        
    async def archive(self):
        await super().archive()
        self.pairs_archive.store(self.pairs)
        self.wallets_archive.store(self.wallets)

    async def list_asset(self, asset, pair):
        self.pairs.append({'base': asset, 'quote': pair['asset']})
        ticker = asset+pair['asset']

        seed_price = Decimal(str(pair['seed_price']))
        seed_bid = Decimal(str(pair['seed_bid']))
        seed_ask = Decimal(str(pair['seed_ask']))

        trade = CryptoTrade(asset, pair['asset'], pair['market_qty'], seed_price, 'init_seed_'+ticker, 'init_seed_'+ticker, self.datetime, network_fee={'base': 0.0001, 'quote': 0.0001}, exchange_fee={'base': 0.0, 'quote': 0.0})
        self.trade_log.append(trade)
        
        buy = await self.limit_buy(asset, pair['asset'], seed_price * seed_bid, 1, 'init_seed_'+ticker, fee=0.000000001, position_id='init_seed_'+ticker)
        sell_fees = self.fees.taker_fee(pair['market_qty']) + Decimal('0.000000001')
        qty = pair['market_qty'] - Decimal(str(sell_fees))
        sell = await self.limit_sell(asset, pair['asset'],  seed_price * seed_ask, qty,  'init_seed_'+ticker, fee=0.000000001)
        
        self.assets[asset] = {'type': 'crypto', 'id' : str(UUID())}
        self.wallets[asset] = await self.generate_address()

        for agent in self.agents:
            if 'init_seed_' not in agent['name']:
                agent['wallets'][asset] = await self.generate_address()
                
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
        if len(self.assets) >= self.max_assets:
            return {'error': 'cannot create, max_assets_reached'}        
        if len(pairs) >= self.max_pairs or len(self.books) >= self.max_pairs:
            return {'error': 'cannot create, max_pairs_reached'}
        if symbol in self.assets:
            return {"error" :f'asset {symbol} already exists'}
        if len(pairs) == 0:
            default_quote = {'asset': self.default_quote_currency['symbol'],'market_qty':1000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}
            pairs.append(default_quote)

        for pair in pairs:
            ticker = symbol+pair['asset']
            self.books[ticker] = CryptoOrderBook(ticker)
            
            pair['seed_price'] = Decimal(str(pair['seed_price']))
            pair['seed_bid'] = Decimal(str(pair['seed_bid']))
            pair['seed_ask'] = Decimal(str(pair['seed_ask']))
            pair['market_qty'] = Decimal(str(pair['market_qty']))

            quote_position =  {"id":'init_seed_'+ticker, 'asset': symbol, "price": 0,"qty": pair['market_qty'] * pair['seed_price'], "dt": self.datetime, "enters":[], "exits": [], }
            self.agents.append({
                'name':'init_seed_'+ticker,
                '_transactions':[],
                "taxable_events": [], 
                'positions': [quote_position],
                'wallets':{symbol: (await self.generate_address()), pair['asset']: (await self.generate_address())},
                'assets': {symbol: pair['market_qty'], pair['asset']: pair['market_qty'] * pair['seed_price']},
                'frozen_assets': {symbol: Decimal('0.0001'), pair['asset']: Decimal('0.0001')}
            })
            
            # await self.register_agent('init_seed_'+ticker, {symbol: pair['market_qty'], pair['asset']: pair['market_qty'] * pair['seed_price']})

            # buyer = 'init_seed_'+ticker
            # seller = 'init_seed_'+ticker
            # price = Decimal(str(pair['seed_price']))
            # qty = Decimal(str(pair['market_qty']))
            # base = symbol
            # quote = pair['asset']
            # network_fee = {'base': Decimal('0.0001'), 'quote': Decimal('0.0001')}
            # exchange_fee={'quote':0.0, 'base':0.0}
            # txn_time = self.datetime

            await self.list_asset(symbol, pair)

            # await self._process_trade(base, quote, qty, price, buyer, seller, accounting='FIFO', network_fee=network_fee, position_id='init_seed_'+ticker)
            # self.pending_asset_pairs[symbol] = pairs
        return {'asset_created': symbol, 'pairs': pairs}
        
    async def _process_trade(self, base, quote, qty, price, buyer, seller, accounting='FIFO', exchange_fee={'quote':0.0, 'base':0.0}, network_fee={'quote':0.0, 'base':0.0}, position_id=None):
        try:
            if position_id != buyer:
                if not await self.agent_has_assets_frozen(buyer, quote, (price*qty)+network_fee['quote']):
                    print(buyer, ' does not have assets')
                    return {'error': 'insufficient funds', 'buyer': buyer}
                if not await self.agent_has_assets_frozen(seller, base, qty+network_fee['base']):
                    print(seller, ' does not have assets')
                    return {'error': 'insufficient funds', 'seller': seller}

            seller_wallet = (await self.get_agent(seller))['wallets'][base]
            buyer_wallet = (await self.get_agent(buyer))['wallets'][quote]

            pending_base_transaction = await self.requester.add_transaction(asset=base, fee=network_fee['base'], amount=qty, sender=seller_wallet, recipient=buyer_wallet)
            pending_quote_transaction = await self.requester.add_transaction(asset=quote, fee=network_fee['quote'], amount=qty*price, sender=buyer_wallet, recipient=seller_wallet)

            if('error' in pending_base_transaction or pending_base_transaction['sender'] == 'error' or 'error' in pending_quote_transaction or pending_quote_transaction['sender'] == 'error'):
                return {'error': 'add_transaction_failed'}
            
            await self.pay_network_fees(buyer, quote, network_fee['quote'])
            await self.pay_network_fees(seller, base, network_fee['base'])

            txn_time = self.datetime

            transaction = [
                {'id': str(UUID()), 'agent':buyer,'quote_flow':-qty*price, 'price': price, 'base': base, 'quote': quote, 'qty': qty, 'fee':exchange_fee['quote'], 'dt': txn_time, 'type': 'buy'},
                {'id': str(UUID()), 'agent':seller,'quote_flow':qty*price, 'price': price, 'base': base, 'quote': quote, 'qty': -qty, 'fee':exchange_fee['base'], 'dt': txn_time, 'type': 'sell'}
            ]

            self.pending_transactions.append({'base_txn': pending_base_transaction, 'quote_txn': pending_quote_transaction, 'exchange_txn': transaction, 'accounting': accounting, 'position_id': position_id})
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
        network_fee = {'base': base_transaction['fee'], 'quote': quote_transaction['fee']}
        exchange_fee = {'base': transaction['exchange_txn'][1]['fee'], 'quote': transaction['exchange_txn'][0]['fee']}
        trade = CryptoTrade(base, quote, qty, price, buyer, seller, self.datetime, network_fee=network_fee, exchange_fee=exchange_fee)
        self.trade_log.append(trade)
        await self.update_agents(transaction['exchange_txn'], transaction['accounting'], position_id=transaction['position_id'])
        self.pending_transactions.remove(transaction)

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

    async def freeze_assets(self, agent, asset, qty) -> None:
        # print('freezing assets', agent, asset, qty)
        agent_idx = await self.get_agent_index(agent)
        #NOTE if we want to freeze potential exchange fees we need to add an id to frozen assets, pass id to _process_trade, then use id to debt back any remaining frozen assets in update_agents
        if asset not in self.agents[agent_idx]['assets']:
            print('no asset available', asset, qty, agent)
            return {'error': 'no asset available'}
        if self.agents[agent_idx]['assets'][asset] < Decimal(str(abs(qty))):
            print('insufficient funds', asset, qty, agent)
            return {'error': 'insufficient funds'}
        self.agents[agent_idx]['assets'][asset] -= Decimal(str(abs(qty)))
        
        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.agents[agent_idx]['frozen_assets'][asset] = Decimal(str(abs(qty)))
        else:
            self.agents[agent_idx]['frozen_assets'][asset] += Decimal(str(abs(qty)))
        # print('frozen_assets', self.agents[agent_idx]['frozen_assets'])

    async def unfreeze_assets(self, agent, asset, qty) -> None:
        agent_idx = await self.get_agent_index(agent)
        self.agents[agent_idx]['assets'][asset] += Decimal(str(abs(qty)))
        self.agents[agent_idx]['frozen_assets'][asset] -= Decimal(str(abs(qty)))
        # print('unfrozen_assets',Decimal(str(abs(qty))))

    async def pay_network_fees(self, agent, asset, qty) -> None:
        # print('paying network fees', agent, asset, qty)
        agent_idx = await self.get_agent_index(agent)
        self.agents[agent_idx]['frozen_assets'][asset] -= Decimal(str(abs(qty)))
        # print(self.agents[agent_idx]['name'], 'frozen remaining', asset, self.agents[agent_idx]['frozen_assets'][asset])

    async def limit_buy(self, base: str, quote:str, price: float, qty: int, creator: str, fee=0.0, tif='GTC', position_id=UUID()) -> CryptoLimitOrder:
        if len(self.books[base+quote].bids) >= self.max_bids:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='max_bid_depth_reached')
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='max_pending_transactions_reached')
        #NOTE: the fee arg here is the network fee... consider renaming
        qty = Decimal(str(qty))
        price = Decimal(str(price))
        fee = Decimal(str(fee))
        potential_fees = self.fees.taker_fee(qty*price)
        has_asset = await self.agent_has_assets(creator, quote, (qty * price)+fee+potential_fees)      
        ticker = base+quote
        if has_asset:
            await self.freeze_assets(creator, quote, (qty * price)+fee)
            # check if we can match trades before submitting the limit order
            fee_per_unit = fee/qty
            unfilled_qty = qty
            remaining_fee =fee
            fills=[]
            while unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_ask = await self.get_best_ask(ticker)
                if best_ask.creator != 'null_quote' and best_ask.creator != creator and price >= best_ask.price:
                    trade_qty = Decimal(str(min(unfilled_qty, best_ask.qty)))
                    taker_fee = self.fees.taker_fee(trade_qty*best_ask.price)
                    partial_fee = fee_per_unit * trade_qty
                    ask_network_fee = (best_ask.network_fee / best_ask.qty) * trade_qty
                    processed = await self._process_trade(base, quote, trade_qty, best_ask.price, creator, best_ask.creator, exchange_fee={'quote':taker_fee, 'base': best_ask.exchange_fee}, network_fee={'quote': partial_fee, 'base': ask_network_fee}, position_id=position_id)
                    if('error' in processed):
                        #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                        break
                    fills.append({'qty': trade_qty, 'price': best_ask.price, 'fee': taker_fee, 'creator': best_ask.creator})
                    unfilled_qty -= Decimal(str(trade_qty))
                    potential_fees -= Decimal(str(taker_fee))
                    remaining_fee -= Decimal(str(partial_fee))
                    self.books[ticker].asks[0].qty -= Decimal(str(trade_qty))
                    self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
                    deductions = (trade_qty*price) - (trade_qty*best_ask.price)
                    await self.unfreeze_assets(creator, quote, deductions)
                else:
                    break
            queue = len(self.books[ticker].bids)
            for idx, order in enumerate(self.books[ticker].bids):
                if price > order.price:
                    queue = idx
                    break
            if unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(unfilled_qty)
                # print('adjusted maker fee:', maker_fee, 'potential fees:', potential_fees)
                # if maker_fee < potential_fees:
                #     await self.unfreeze_assets(creator, quote, potential_fees - maker_fee)
                maker_order = CryptoLimitOrder(ticker, price, unfilled_qty, creator, OrderSide.BUY, self.datetime, exchange_fee=maker_fee, network_fee=remaining_fee, position_id=position_id, fills=fills)
                self.books[ticker].bids.insert(queue, maker_order)
                return maker_order
            else:
                taker_fee = self.fees.taker_fee(qty*price)
                filled_taker_order = CryptoLimitOrder(ticker, price, qty, creator, OrderSide.BUY, self.datetime, exchange_fee=taker_fee, network_fee=fee, position_id=position_id, fills=fills)
                filled_taker_order.status = 'filled_unconfirmed'
                return filled_taker_order
        else:
            return CryptoLimitOrder(ticker, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='insufficient_funds')
        
    async def limit_sell(self, base: str, quote:str, price: float, qty: int, creator: str, fee=0.0, tif='GTC', accounting='FIFO') -> CryptoLimitOrder:
        if len(self.books[base+quote].asks) >= self.max_asks:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='max_ask_depth_reached')
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return CryptoLimitOrder(base+quote, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='max_pending_transactions_reached')
        #NOTE: the fee arg here is the network fee... consider renaming
        qty = Decimal(str(qty))
        price = Decimal(str(price))
        fee = Decimal(str(fee))
        ticker = base+quote
        potential_fees = self.fees.taker_fee(qty*price)
        has_assets = await self.agent_has_assets(creator, base, qty+fee)
        if has_assets:
            await self.freeze_assets(creator, base, qty+fee)
            fee_per_unit = fee/qty
            unfilled_qty = qty
            remaining_fee = fee
            # check if we can match trades before submitting the limit order
            fills = []
            while unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_bid = await self.get_best_bid(ticker)
                if best_bid.creator != 'null_quote' and best_bid.creator != creator and price <= best_bid.price:
                    trade_qty = Decimal(str(min(unfilled_qty, best_bid.qty)))
                    taker_fee = self.fees.taker_fee(trade_qty*best_bid.price)
                    partial_fee = fee_per_unit * trade_qty
                    bid_network_fee = (best_bid.network_fee / best_bid.qty) * trade_qty
                    processed = await self._process_trade(base, quote, trade_qty, best_bid.price, best_bid.creator, creator, accounting, exchange_fee={'base': taker_fee, 'quote': best_bid.exchange_fee}, network_fee={'base':partial_fee, 'quote': bid_network_fee})
                    if('error' in processed):
                        #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                        break
                    fills.append({'qty': trade_qty, 'price': best_bid.price, 'fee': taker_fee, 'creator': best_bid.creator})
                    unfilled_qty -= Decimal(str(trade_qty))
                    potential_fees -= Decimal(str(taker_fee))
                    remaining_fee -= Decimal(str(partial_fee))
                    self.books[ticker].bids[0].qty -= Decimal(str(trade_qty))
                    self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
                else:
                    break
            queue = len(self.books[ticker].asks)
            for idx, order in enumerate(self.books[ticker].asks):
                if price < order.price:
                    queue = idx
                    break
            if unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(unfilled_qty*price)
                # print('adjusted maker fee:', maker_fee, 'potential fees:', potential_fees)
                # if maker_fee < potential_fees:
                #     await self.unfreeze_assets(creator, base, potential_fees - maker_fee)
                maker_order = CryptoLimitOrder(ticker, price, unfilled_qty, creator, OrderSide.SELL, self.datetime, exchange_fee=maker_fee, network_fee=remaining_fee, accounting=accounting, fills=fills)
                self.books[ticker].asks.insert(queue, maker_order)
                return maker_order
            else:
                taker_fee = self.fees.taker_fee(qty*price)
                filled_taker_order = CryptoLimitOrder(ticker, price, qty, creator, OrderSide.SELL, self.datetime, exchange_fee=taker_fee, network_fee=fee, accounting=accounting, fills=fills)
                filled_taker_order.status = 'filled_unconfirmed'
                return filled_taker_order
        else:
            return CryptoLimitOrder(ticker, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='insufficient_assets')
           
    async def cancel_order(self, base, quote, id) -> dict:
        ticker = base+quote
        canceled = await super().cancel_order(ticker, id)
        if canceled and 'cancelled_order' in canceled and 'creator' in canceled['cancelled_order']:
            creator = canceled['cancelled_order']['creator']
            qty = canceled['cancelled_order']['qty']
            price = canceled['cancelled_order']['price']
            fee = canceled['cancelled_order']['exchange_fee']
            if canceled['cancelled_order']['type'] == 'limit_buy':
                await self.unfreeze_assets(creator, quote, qty*price)
            elif canceled['cancelled_order']['type'] == 'limit_sell':
                await self.unfreeze_assets(creator, base, qty)
            else:
                return {'error': 'unable to cancel, order type not recognized', 'id': id}
        return canceled
    
    async def cancel_all_orders(self, base, quote, creator) -> list:
        ticker = base+quote
        # canceled = await super().cancel_all_orders(creator, ticker)
        canceled = []
        async def cancel_bid(bid, creator):
            if bid.creator == creator:
                await self.unfreeze_assets(creator, quote, bid.qty*bid.price)
                canceled.append(bid.id)
                return False
            else:
                return True
            
        async def cancel_ask(ask, creator):
            if ask.creator == creator:
                await self.unfreeze_assets(creator, base, ask.qty)
                canceled.append(ask.id)
                return False
            else:
                return True
            
        self.books[ticker].bids[:] = [b for b in self.books[ticker].bids if await cancel_bid(b, creator)]
        self.books[ticker].asks[:] = [a for a in self.books[ticker].asks if await cancel_ask(a, creator)]

        return {'cancelled_orders': canceled}

    async def market_buy(self, base: str, quote:str, qty: int, buyer: str, fee=0.0) -> dict:
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return {"market_buy": "max_pending_transactions_reached", "buyer": buyer}
        qty = Decimal(str(qty))
        fee = Decimal(str(fee))
        ticker = base+quote
        best_price = (await self.get_best_ask(ticker)).price
        potential_fees = self.fees.taker_fee(qty)
        has_asset = await self.agent_has_assets(buyer, quote,( qty * best_price)+fee+potential_fees)
        #TODO: tracking unfilled orders for partial fills... still process the order and resolve it, should not need to unfreeze assets... test this though
        if has_asset:
            await self.freeze_assets(buyer, quote, fee)
            fee_per_unit = fee/qty
            remaining_fee = fee
            unfilled_qty = qty
            remaining_frozen = 0
            fills = []
            for idx, ask in enumerate(self.books[ticker].asks):
                if ask.creator == buyer:
                    continue
                trade_qty = Decimal(str(min(ask.qty, unfilled_qty)))
                network_ask_fee = (ask.network_fee / ask.qty) * trade_qty
                taker_fee = self.fees.taker_fee(trade_qty)
                if(type(fee) is str): fee = float(fee)
                partial_fee = fee_per_unit * trade_qty
                await self.freeze_assets(buyer, quote, trade_qty*ask.price)
                remaining_frozen += Decimal(str(trade_qty*ask.price))
                #TODO: how to handle waiting for network to confirm market orders: essentially place as taker limit order and wait for confirmation?
                processed = await self._process_trade(base, quote, trade_qty, ask.price, buyer, ask.creator, exchange_fee={'quote': taker_fee, 'base': ask.exchange_fee}, network_fee={'quote':partial_fee, 'base': network_ask_fee})
                if'error' in processed: 
                    continue
                self.books[ticker].asks[idx].qty -= Decimal(str(trade_qty))
                fills.append({'qty': trade_qty, 'price': ask.price, 'fee': taker_fee})
                remaining_fee -= Decimal(str(partial_fee))
                unfilled_qty -= Decimal(str(trade_qty))
                remaining_frozen -= Decimal(str(trade_qty*ask.price))
                if unfilled_qty == 0:
                    break
            self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
            if remaining_fee > 0.0:
                await self.unfreeze_assets(buyer, quote, remaining_fee)
            if remaining_frozen > 0:
                await self.unfreeze_assets(buyer, quote, remaining_frozen)
            if(fills == []):
                return {"market_buy": "no fills"}                
            return {"market_buy": ticker, "buyer": buyer, 'qty': qty,  "fills": fills}
        else:
            return {"market_buy": "insufficient funds", "buyer": buyer}

    async def market_sell(self, base: str, quote:str, qty: int, seller: str, fee=0.0, accounting='FIFO') -> dict:
        if len(self.pending_transactions) >= self.max_pending_transactions:
            return {"market_sell": "max_pending_transactions_reached", "seller": seller}
        qty = Decimal(str(qty))
        fee = Decimal(str(fee))        
        ticker = base+quote
        potential_fees = self.fees.taker_fee(qty)
        has_assets = await self.agent_has_assets(seller, base, qty+fee+potential_fees)
        if has_assets and qty > 0:
            frozen = 0
            await self.freeze_assets(seller, base, fee)
            frozen += fee
            fee_per_unit = fee/qty
            remaining_fee = fee
            unfilled_qty = qty
            fills = []
            for idx, bid in enumerate(self.books[ticker].bids):
                if bid.creator == seller:
                    continue
                trade_qty = Decimal(str(min(bid.qty, unfilled_qty)))
                network_bid_fee = (bid.network_fee / bid.qty) * trade_qty
                taker_fee = self.fees.taker_fee(trade_qty)
                if(type(fee) is str): fee = float(fee)
                if trade_qty == unfilled_qty:
                    partial_fee = remaining_fee
                else:
                    partial_fee = fee_per_unit * trade_qty
                await self.freeze_assets(seller, base, trade_qty)                                   
                processed = await self._process_trade(base, quote, trade_qty,bid.price, bid.creator, seller, accounting, exchange_fee={'base': taker_fee, 'quote': bid.exchange_fee}, network_fee={'base': partial_fee, 'quote': network_bid_fee} )
                if'error' in processed: 
                    continue
                fills.append({'qty': trade_qty, 'price': bid.price, 'fee': taker_fee})
                remaining_fee -= Decimal(str(partial_fee))
                unfilled_qty -= Decimal(str(trade_qty))
                self.books[ticker].bids[idx].qty -= Decimal(str(trade_qty))
                if unfilled_qty == 0:
                    break
            self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
            # print('remaining_fee', f'{remaining_fee:.20f}' )
            if (remaining_fee > 0):
                await self.unfreeze_assets(seller, base, remaining_fee)
            if (unfilled_qty > 0):
                await self.unfreeze_assets(seller, base, unfilled_qty)
            if(fills == []):
                return {"market_sell": "no fills"}                
            return {"market_sell": ticker, "seller": seller, 'qty': qty, "fills": fills }
        else:
            return {"market_sell": "insufficient assets", "seller": seller}

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
        # print('registering agent', name)
        if(len(self.agents) >= self.max_agents):
            return {'error': 'max agents reached'}
        registered_name = name + str(UUID())[0:8]
        positions = []
        wallets = {
            self.default_quote_currency['symbol']: (await self.generate_address())
        }
        for asset in initial_assets:
            side = {
                'agent': registered_name, 
                'quote_flow': 0, 
                'price': 0, 
                'base': asset, 
                'quote': self.default_quote_currency['symbol'],
                'initial_qty': 0, 
                'qty': Decimal(str(initial_assets[asset])), 
                'dt': self.datetime, 
                'type': 'buy'
            }
            basis ={
                'basis_initial_unit': self.default_quote_currency['symbol'],
                'basis_per_unit': 0,
                'basis_txn_id': 'seed',
                'basis_date': self.datetime
            }
            new_position = await self.new_position(side, asset, side['qty'], basis)
            positions.append(new_position)
            initial_assets[asset] = Decimal(str(initial_assets[asset]))
  
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
        return {'registered_agent':registered_name}
    
    async def new_enter(self, agent, asset, qty, dt, type, basis={}) -> dict:
        enter = {
            'id': str(UUID()),
            'agent': agent,
            'asset': asset,
            'initial_qty': Decimal(str(qty)),
            'qty': Decimal(str(qty)),
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
            'qty': Decimal(str(qty)),
            'dt': side['dt'],
            'enters': [enter],
            'exits': []
        }

    async def taxable_event(self, agent, amount, dt, basis_amount, basis_date) -> None:
        # print('taxable event', amount, basis_amount)
        pnl = amount - basis_amount
        # print('pnl', pnl)
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
                position['qty'] += Decimal(str(qty))
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
        exit_transaction['qty'] = abs(side['qty'])
        while exit_transaction['qty'] > 0:
            for position in positions:
                if position['asset'] != asset or position['qty'] == 0: continue
                enters = position['enters']
                if len(enters) == 0: continue
                
                for enter in enters:
                    exit = {
                        'id': str(UUID()),
                        'agent': agent['name'],
                        'asset': asset,
                        'dt': exit_transaction['dt'],
                        'enter_id': enter['id'],
                    }
                    if asset == self.default_quote_currency['symbol']:
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
                            cost_basis_per_unit = (enter['basis']['basis_per_unit'] * abs(side['quote_flow'])) / abs(side['qty'])
                            # print(f"cost_basis_per_unit: {cost_basis_per_unit:.16f}")
                            exit['basis']['basis_per_unit'] = cost_basis_per_unit

                    if enter['qty'] >= exit_transaction['qty']:
                        exit['qty'] = Decimal(str(exit_transaction['qty']))
                        enter['qty'] -= Decimal(str(exit_transaction['qty']))
                        position['qty'] -= Decimal(str(exit_transaction['qty']))
                        exit_transaction['qty'] = 0
                        # print('full exit', exit_transaction['qty'], position['qty'])
                        position['exits'].append(exit)
                        return {'exit_position': exit}
                    else:
                        # partial exit
                        exit_transaction['qty'] -= Decimal(str(enter['qty']))
                        exit['qty'] = Decimal(str(enter['qty']))
                        enter['qty'] = 0
                        position['qty'] -= Decimal(str(enter['qty']))
                        # print('partial exit', exit_transaction['qty'], position['qty'])
                        position['exits'].append(exit)
        return {'exit_position': 'no position to exit'}                            

    async def update_assets(self, asset, amount, agent_idx) -> None:
        if asset in self.agents[agent_idx]['assets']:
            self.agents[agent_idx]['assets'][asset] += Decimal(str(amount))
        else: 
            self.agents[agent_idx]['assets'][asset] = Decimal(str(amount))

    async def update_agents(self, transaction, accounting, position_id) -> None:
        for side in transaction:
            if len(self.agents) == 0:
                return {'update_agents': 'no agents'}
            agent_idx = await self.get_agent_index(side['agent'])
            if agent_idx is None:
                return {'update_agents': 'agent not found'}
            #TODO: maybe don't need to track transactions... check if needed for taxation
            self.agents[agent_idx]['_transactions'].append(side)
            if 'init_seed_' in self.agents[agent_idx]['name']:
                continue
            if side['type'] == 'buy':
                # print('increasing base by', side['qty'], 'for', side['agent'])
                await self.update_assets(side['base'], side['qty'], agent_idx)

                # print('sending frozen buy asset', side['quote'], side['quote_flow'], 'for', side['agent'])
                self.agents[agent_idx]['frozen_assets'][side['quote']] -= Decimal(str(abs(side['quote_flow'])))

                # print(side['agent'], 'transacting', side['quote'], side['quote_flow'], 'price', side['price'], 'qty', side['qty'])
                # print(f"{self.agents[agent_idx]['name']} frozen remaining {side['quote']} {self.agents[agent_idx]['frozen_assets'][side['quote']]:.16f}")

                if side['fee'] > 0.0: await self.pay_exchange_fees(agent_idx, side['quote'], side['fee'])
                
                
                exit = await self.exit_position(side, side['quote'], side['quote_flow'], agent_idx)
                # print(f" exit basis: {exit['exit_position']['basis']}, asset {exit['exit_position']['asset']} qty {exit['exit_position']['qty']} ")
                enter = await self.enter_position(side, side['base'], side['qty'], agent_idx, position_id, basis=exit['exit_position']['basis'])
                # print(f" enter basis: {enter['enter_position']['basis']}, asset {enter['enter_position']['asset']} qty {enter['enter_position']['qty']} ")

            elif side['type'] == 'sell':
                # print('increasing quote by', side['quote_flow'], 'for', side['agent'])
                await self.update_assets(side['quote'], side['quote_flow'], agent_idx)

                # print('sending frozen sell asset', side['base'], side['qty'], 'for', side['agent'])
                self.agents[agent_idx]['frozen_assets'][side['base']] -= Decimal(str(abs(side['qty'])))

                # print(side['agent'], 'transacting', side['base'], side['qty'])
                # print(f"{self.agents[agent_idx]['name']} frozen remaining {side['base']} {self.agents[agent_idx]['frozen_assets'][side['base']]:.16f}")
                # we cannot know if it it from this order or a previous order, so we need to track it
                if side['fee'] > 0.0: await self.pay_exchange_fees(agent_idx, side['base'], side['fee'])
                await self.sort_positions(agent_idx, accounting)
                exit = await self.exit_position(side, side['base'], side['qty'], agent_idx)
                # print(f" exit basis: {exit['exit_position']['basis']}, asset {exit['exit_position']['asset']} qty {exit['exit_position']['qty']} ")
                enter = await self.enter_position(side, side['quote'], side['quote_flow'], agent_idx, None, basis=exit['exit_position']['basis'])
                # print(f" enter basis: {enter['enter_position']['basis']}, asset {enter['enter_position']['asset']} qty {enter['enter_position']['qty']} ")

                if side['quote'] == self.default_quote_currency['symbol']:
                    #NOTE: basis represents the initial default quote currency amount (quote_flow) traded for the first enter in the chain
                    # consider the following trade chain:
                    # USD (exit, basis) -> BTC (enter, consume basis) -> BTC (exit, retain basis) -> ETH (enter, passed basis)
                    basis_amount = abs(side['qty']) * exit['exit_position']['basis']['basis_per_unit']
                    # print('basis_amount', basis_amount, exit['exit_position']['basis']['basis_per_unit'], 'amount', side['quote_flow'])
                    await self.taxable_event(self.agents[agent_idx], side['quote_flow'], side['dt'], basis_amount, exit['exit_position']['basis']['basis_date'])

    async def pay_exchange_fees(self, agent_idx, asset, amount) -> None:
            # print(f"{self.agents[agent_idx]['name']} assets before {asset} {self.agents[agent_idx]['assets'][asset]:.16f}")
            # print(self.agents[agent_idx]['name'], 'paying exchange fee', asset, amount )
            self.agents[agent_idx]['assets'][asset] -= Decimal(str(abs(amount)))
            # print(f"{self.agents[agent_idx]['name']} assets after {asset} {self.agents[agent_idx]['assets'][asset]:.16f}")
            self.fees.add_fee(asset, amount)        

    async def get_agents_holding(self, asset) -> list:
        return await super().get_agents_holding(asset)

    async def total_cash(self) -> float:
        """
        returns the total of the default quote currency across all agents
        """
        total = 0
        for agent in self.agents:
            if 'init_seed' not in agent['name']:
                total += agent['assets'][self.default_quote_currency['symbol']]
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
        return await super().agent_has_assets(agent, asset, qty)
    
    async def agent_has_assets_frozen(self, agent, asset, qty) -> bool:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            if asset in self.agents[agent_idx]['frozen_assets']:
                # print(agent, 'frozen', asset, 'needed:', qty, 'has:', self.agents[agent_idx]['frozen_assets'][asset])
                return self.agents[agent_idx]['frozen_assets'][asset] >= qty
            else:
                return False
        else:
            return False

    async def agent_has_cash(self, agent, amount, qty) -> bool:
        return await self.agent_has_assets(agent, self.default_quote_currency['symbol'], amount * qty)

    async def agents_cash(self) -> list:
        """
        returns a list of all agents and their cash
        """
        info = []
        for agent in self.agents:
            if agent['name'] != 'init_seed':
                info.append({agent['name']: {'cash':agent['assets'][self.default_quote_currency['symbol']]}})
        return info

    async def get_cash(self, agent_name) -> dict:
        agent_info = await self.get_agent(agent_name)
        return {'cash':agent_info['assets'][self.default_quote_currency['symbol']]}

    async def get_assets(self, agent) -> dict:
        agent_info = await self.get_agent(agent)
        return {'assets': agent_info['assets'], 'frozen_assets': agent_info['frozen_assets']}

    async def add_asset(self, agent, asset, amount, note=''):
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            side = {'id': str(UUID()), 'agent':agent, 'quote_flow':0, 'price': 0, 'base': asset, 'quote': self.default_quote_currency['symbol'], 'qty': amount, 'fee':0, 'dt': self.datetime, 'type': note}
            basis ={
                'basis_initial_unit': self.default_quote_currency['symbol'],
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
            side = {'id': str(UUID()), 'agent':agent,'quote_flow':0, 'price': 0, 'base':asset, 'quote':self.default_quote_currency['symbol'], 'qty': -amount, 'fee':0, 'dt': self.datetime, 'type': 'sell'}
            await self.exit_position(side, asset, -amount, agent_idx)
            await self.update_assets(asset, -amount, agent_idx)
            return {asset: self.agents[agent_idx]['assets'][asset]}
        else:
            return {'error': 'agent not found'}

    async def add_cash(self, agent, amount, note='', taxable=False) -> dict:
        return await self.add_asset(agent, self.default_quote_currency['symbol'], amount, note)          
    
    async def remove_cash(self, agent, amount, note='') -> dict:
        return await self.remove_asset(agent, self.default_quote_currency['symbol'], amount, note)

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
            agents_simple.append({'agent':agent['name'],'assets':agent['assets']})
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