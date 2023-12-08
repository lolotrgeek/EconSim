import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from uuid import uuid4 as UUID
import random, string, time
from decimal import Decimal
from source.Archive import Archive
from .Exchange import Exchange
from .types.OrderBook import OrderBook
from .types.Trade import Trade
from .types.LimitOrder import LimitOrder
from .types.OrderSide import OrderSide
from .types.Fees import Fees
from source.utils.logger import Logger

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class StockExchange(Exchange):
    def __init__(self, datetime= None, archiver=None):
        super().__init__(datetime=datetime)
        self.archiver = archiver
        self.agents_archive = Archive('stock_agents')
        self.assets_archive = Archive('stock_assets')
        self.books_archive = Archive('stock_books')
        self.trade_log_archive = Archive('stock_trade_log')        
        self.fees = Fees()
        self.fees.waive_fees = False
        self.pending_transactions = []
        self.max_pending_transactions = 1_000_000
        self.max_pairs = 10000
        self.logger = Logger('StockExchange', debug_print=False) 
        
    async def next(self):
        await self.archive()
        await self.prune_trades()
  
    async def archive(self):
        await super().archive()
        self.pairs_archive.store(self.pairs)

    async def create_asset(self, ticker: str, asset_type='stock', market_qty=1000, seed_price=100, seed_bid=.99, seed_ask=1.01) -> OrderBook:
        """_summary_

        Args:
            ticker (str): the ticker of the new asset
            asset_type (str, optional): the type of asset, default: 'stock', 'cash', 'fund' 
            marekt_qty (int, optional): the total amount of the asset in circulation. async defaults to 1000.
            seed_price (int, optional): Price of an initial trade that is created for ease of use. async defaults to 100.
            seed_bid (float, optional): Limit price of an initial buy order, expressed as percentage of the seed_price. async defaults to .99.
            seed_ask (float, optional): Limit price of an initial sell order, expressed as percentage of the seed_price. async defaults to 1.01.
        """
        if len(self.assets) >= self.max_assets:
            return {"error" : "max assets reached"}
        if ticker in self.assets:
            return {"error" :f'asset {ticker} already exists'}
        self.assets[ticker] = {'type':asset_type}
        self.books[ticker] = OrderBook(ticker)

        quote_position =  {"id":'init_seed_'+ticker, 'asset': ticker, "price": 0,"qty": Decimal(str(market_qty)) * Decimal(str(seed_price)), "dt": self.datetime, "enters":[], "exits": [], }
        self.agents.append({
            'name':'init_seed_'+ticker,
            '_transactions':[],
            "taxable_events": [], 
            'positions': [quote_position],
            'assets': {ticker: Decimal(market_qty), self.default_currency['symbol']: Decimal(market_qty * seed_price)},
            'frozen_assets': {}
        })

        await self._process_trade(ticker, market_qty, seed_price, 'init_seed_'+ticker, 'init_seed_'+ticker, position_id='init_seed_'+ticker)
        await self.limit_buy(ticker, seed_price * seed_bid, 1, 'init_seed_'+ticker)
        await self.limit_sell(ticker, seed_price * seed_ask, market_qty, 'init_seed_'+ticker)
        return self.assets[ticker]

    async def _process_trade(self, ticker, qty, price, buyer, seller, accounting='FIFO', fee={'buyer_fee':0, 'seller_fee':0}, position_id=None):
        try:
            if position_id != buyer:
                if not await self.agent_has_assets_frozen(buyer, self.default_currency['symbol'], (price*qty)):
                    self.logger.info(f'{buyer} does not have assets')
                    return {'error': 'insufficient funds', 'buyer': buyer}
                if not await self.agent_has_assets_frozen(seller, ticker, qty):
                    self.logger.info(seller, ' does not have assets')
                    return {'error': 'insufficient funds', 'seller': seller}
                
            trade = Trade(ticker, qty, price, buyer, seller, self.datetime, fee=fee)
            self.trade_log.append(trade)
            txn_time = self.datetime
                
            transaction = [
                {'id': str(UUID()), 'agent':buyer,'cash_flow':-qty*price, 'price': price, 'ticker':ticker, 'qty': qty, 'fee':fee['buyer_fee'], 'dt': txn_time, 'type': 'buy'},
                {'id': str(UUID()), 'agent':seller,'cash_flow':qty*price, 'price': price, 'ticker':ticker, 'qty': -qty, 'fee':fee['seller_fee'], 'dt': txn_time, 'type': 'sell'}
            ]

            await self.update_agents(transaction, accounting, position_id)
            return transaction 
        except Exception as e:
            return {'error': 'transaction failed'}   
          
    async def get_best_ask(self, ticker:str) -> LimitOrder:
        """retrieves the current best ask in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset.

        returns:
            LimitOrder
        """
        if self.books[ticker].asks and self.books[ticker].asks[0]:
            return self.books[ticker].asks[0]
        else:
            return LimitOrder(ticker, 0, 0, 'null_quote', OrderSide.SELL, self.datetime)

    async def get_best_bid(self, ticker:str) -> LimitOrder:
        """retrieves the current best bid in the orderbook of an asset

        Args:
            ticker (str): the ticker of the asset.

        returns:
            LimitOrder
        """
        if self.books[ticker].bids and self.books[ticker].bids[0]:
            return self.books[ticker].bids[0]
        else:
            return LimitOrder(ticker, 0, 0, 'null_quote', OrderSide.BUY, self.datetime)
    
    async def freeze_assets(self, agent, asset, qty) -> None:
        self.logger.info('freezing assets', agent, asset, qty)
        agent_idx = await self.get_agent_index(agent)
        #NOTE if we want to freeze potential exchange fees we need to add an id to frozen assets, pass id to _process_trade, then use id to debt back any remaining frozen assets in update_agents
        if asset not in self.agents[agent_idx]['assets']:
            self.logger.info('no asset available', asset, qty, agent)
            return {'error': 'no asset available'}
        if self.agents[agent_idx]['assets'][asset] < Decimal(str(abs(qty))):
            self.logger.info('insufficient funds', asset, qty, agent)
            return {'error': 'insufficient funds'}
        self.agents[agent_idx]['assets'][asset] -= Decimal(str(abs(qty)))
        
        if asset not in self.agents[agent_idx]['frozen_assets']:
            self.agents[agent_idx]['frozen_assets'][asset] = Decimal(str(abs(qty)))
        else:
            self.agents[agent_idx]['frozen_assets'][asset] += Decimal(str(abs(qty)))
        self.logger.info('frozen_assets', self.agents[agent_idx]['frozen_assets'])

    async def unfreeze_assets(self, agent, asset, qty) -> None:
        agent_idx = await self.get_agent_index(agent)
        # if the qty is greater than the frozen assets, unfreeze all assets
        if self.agents[agent_idx]['frozen_assets'][asset] < Decimal(str(abs(qty))):
            self.agents[agent_idx]['assets'][asset] += self.agents[agent_idx]['frozen_assets'][asset]
            self.agents[agent_idx]['frozen_assets'][asset] = Decimal('0.0')
            self.logger.info('unfrozen_assets', self.agents[agent_idx]['frozen_assets'][asset])
            return

        self.agents[agent_idx]['assets'][asset] += Decimal(str(abs(qty)))
        self.agents[agent_idx]['frozen_assets'][asset] -= Decimal(str(abs(qty)))
        self.logger.info('unfrozen_assets',Decimal(str(abs(qty))))

    async def limit_buy(self, ticker: str, price: float, qty: int, creator: str, tif='GTC', fee={'buyer_fee':0, 'seller_fee':0}, position_id=UUID()) -> LimitOrder:
        if len(self.books[ticker].bids) >= self.max_bids:
            return LimitOrder(ticker, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='max_bid_depth_reached')
        qty = Decimal(str(qty))
        price = Decimal(str(price))
        if(qty <= 0):
            return LimitOrder(ticker, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='qty_must_be_greater_than_zero')        
        potential_fees = self.fees.taker_fee(qty*price)
        has_asset = await self.agent_has_assets(creator, self.default_currency['symbol'], (qty * price)+potential_fees)      
        if has_asset:
            await self.freeze_assets(creator, self.default_currency['symbol'], (qty * price))
            await self.freeze_assets(creator, self.default_currency['symbol'], potential_fees)
            # check if we can match trades before submitting the limit order
            unfilled_qty = qty
            fills=[]
            while unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_ask = await self.get_best_ask(ticker)
                if best_ask.creator != 'null_quote' and best_ask.creator != creator and price >= best_ask.price:
                    trade_qty = Decimal(str(min(unfilled_qty, best_ask.qty)))
                    taker_fee = self.fees.taker_fee(trade_qty*best_ask.price)
                    seller_fee = (best_ask.fee / best_ask.qty) * trade_qty
                    self.logger.info('seller: ', best_ask.creator, 'seller fee: ', seller_fee)
                    processed = await self._process_trade(ticker, trade_qty, best_ask.price, creator, best_ask.creator, fee={'buyer_fee':taker_fee, 'seller_fee':seller_fee}, position_id=position_id)
                    if('error' in processed):
                        #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                        break
                    fills.append({'qty': trade_qty, 'price': best_ask.price, 'fee': taker_fee, 'creator': best_ask.creator})
                    unfilled_qty -= Decimal(str(trade_qty))
                    potential_fees -= taker_fee
                    self.books[ticker].asks[0].qty -= Decimal(str(trade_qty))
                    self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
                    deductions = (trade_qty*price) - (trade_qty*best_ask.price)
                    if deductions > 0:
                        await self.unfreeze_assets(creator, self.default_currency['symbol'], deductions)
                else:
                    break
            queue = len(self.books[ticker].bids)
            for idx, order in enumerate(self.books[ticker].bids):
                if price > order.price:
                    queue = idx
                    break
            if potential_fees > 0:
                await self.unfreeze_assets(creator, self.default_currency['symbol'], potential_fees)
            if unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(unfilled_qty*price)
                await self.freeze_assets(creator, self.default_currency['symbol'], maker_fee)
                self.logger.info('adjusted maker fee:', maker_fee, 'potential fees:', potential_fees)
                maker_order = LimitOrder(ticker, price, unfilled_qty, creator, OrderSide.BUY, self.datetime, fee=maker_fee, position_id=position_id, fills=fills)
                self.books[ticker].bids.insert(queue, maker_order)
                return maker_order
            else:
                taker_fee = self.fees.taker_fee(qty*price)
                filled_taker_order = LimitOrder(ticker, price, qty, creator, OrderSide.BUY, self.datetime, fee=taker_fee, position_id=position_id, fills=fills)
                filled_taker_order.status = 'filled'
                return filled_taker_order
        else:
            return LimitOrder(ticker, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='insufficient_funds')
        
    async def limit_sell(self, ticker: str, price: float, qty: int, creator: str, tif='GTC', fee={'buyer_fee':0, 'seller_fee':0}, accounting='FIFO') -> LimitOrder:
        if len(self.books[ticker].asks) >= self.max_asks:
            return LimitOrder(ticker, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='max_ask_depth_reached')
        qty = Decimal(str(qty))
        price = Decimal(str(price))
        if(qty <= 0):
            return LimitOrder(ticker, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='qty_must_be_greater_than_zero')        
        potential_fees = self.fees.taker_fee(qty*price)
        has_assets = await self.agent_has_assets(creator, ticker, qty)
        if has_assets:
            await self.freeze_assets(creator, ticker, qty)
            await self.freeze_assets(creator, self.default_currency['symbol'], potential_fees)
            unfilled_qty = qty
            # check if we can match trades before submitting the limit order
            fills = []
            while unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_bid = await self.get_best_bid(ticker)
                if best_bid.creator != 'null_quote' and best_bid.creator != creator and price <= best_bid.price:
                    trade_qty = Decimal(str(min(unfilled_qty, best_bid.qty)))
                    taker_fee = self.fees.taker_fee(trade_qty*price)
                    buyer_fee = (best_bid.fee / best_bid.qty) * trade_qty
                    processed = await self._process_trade(ticker, trade_qty, best_bid.price, best_bid.creator, creator, accounting, fee={'buyer_fee': buyer_fee, 'seller_fee': taker_fee})
                    if('error' in processed):
                        #NOTE: instead of canceling, unfreezing assets, and attempting to handle a partial fill, push the rest of this order into the book
                        break
                    fills.append({'qty': trade_qty, 'price': best_bid.price, 'fee': taker_fee, 'creator': best_bid.creator})
                    unfilled_qty -= Decimal(str(trade_qty))
                    potential_fees -= Decimal(str(taker_fee))
                    self.books[ticker].bids[0].qty -= Decimal(str(trade_qty))
                    self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
                else:
                    break
            queue = len(self.books[ticker].asks)
            for idx, order in enumerate(self.books[ticker].asks):
                if price < order.price:
                    queue = idx
                    break
            if potential_fees > 0:
                await self.unfreeze_assets(creator, self.default_currency['symbol'], potential_fees)
            if unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(unfilled_qty*price)
                await self.freeze_assets(creator, self.default_currency['symbol'], maker_fee)
                self.logger.info('adjusted maker fee:', maker_fee, 'potential fees:', potential_fees)
                maker_order = LimitOrder(ticker, price, unfilled_qty, creator, OrderSide.SELL, self.datetime, fee=maker_fee, accounting=accounting, fills=fills)
                self.books[ticker].asks.insert(queue, maker_order)
                return maker_order
            else:
                taker_fee = self.fees.taker_fee(qty*price)
                filled_taker_order = LimitOrder(ticker, price, qty, creator, OrderSide.SELL, self.datetime, fee=taker_fee, accounting=accounting, fills=fills)
                filled_taker_order.status = 'filled'
                return filled_taker_order
        else:
            return LimitOrder(ticker, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='insufficient_assets')
           
    async def cancel_order(self, ticker, id) -> dict:
        canceled = await super().cancel_order(ticker, id)
        if canceled and 'cancelled_order' in canceled and 'creator' in canceled['cancelled_order']:
            creator = canceled['cancelled_order']['creator']
            qty = canceled['cancelled_order']['qty']
            price = canceled['cancelled_order']['price']
            fee = canceled['cancelled_order']['fee']
            await self.unfreeze_assets(creator, self.default_currency['symbol'], fee)
            if canceled['cancelled_order']['type'] == 'limit_buy':
                await self.unfreeze_assets(creator, self.default_currency['symbol'], qty*price)
            elif canceled['cancelled_order']['type'] == 'limit_sell':
                await self.unfreeze_assets(creator, ticker, qty)
            else:
                return {'error': 'unable to cancel, order type not recognized', 'id': id}
        return canceled
    
    async def cancel_all_orders(self, ticker, creator) -> list:
        # canceled = await super().cancel_all_orders(creator, ticker)
        canceled = []
        async def cancel_bid(bid, creator):
            if bid.creator == creator:
                await self.unfreeze_assets(creator, self.default_currency['symbol'], bid.qty*bid.price + bid.fee)
                canceled.append(bid.id)
                return False
            else:
                return True
            
        async def cancel_ask(ask, creator):
            if ask.creator == creator:
                await self.unfreeze_assets(creator, ask.ticker, ask.qty)
                await self.unfreeze_assets(creator, self.default_currency['symbol'], ask.fee)
                canceled.append(ask.id)
                return False
            else:
                return True
            
        self.books[ticker].bids[:] = [b for b in self.books[ticker].bids if await cancel_bid(b, creator)]
        self.books[ticker].asks[:] = [a for a in self.books[ticker].asks if await cancel_ask(a, creator)]

        return {'cancelled_orders': canceled}

    async def market_buy(self, ticker:str, qty: int, buyer: str, fee={'buyer_fee':0, 'seller_fee':0}) -> dict:
        qty = Decimal(str(qty))
        if qty <= 0:
            return {"market_buy": "qty_must_be_greater_than_zero", "buyer": buyer}
        unfilled_qty = qty
        fills = []
        for idx, ask in enumerate(self.books[ticker].asks):
            if ask.creator == buyer:
                continue
            trade_qty = Decimal(str(min(ask.qty, unfilled_qty)))
            taker_fee = self.fees.taker_fee(trade_qty*ask.price)
            has_assets = await self.agent_has_assets(buyer, self.default_currency['symbol'], (trade_qty*ask.price)+taker_fee)
            if has_assets == False:
                return {"market_buy": "insufficient assets", "buyer": buyer}
            await self.freeze_assets(buyer, self.default_currency['symbol'], trade_qty*ask.price)
            await self.freeze_assets(buyer, self.default_currency['symbol'], taker_fee)
            seller_fee = (ask.fee / ask.qty) * trade_qty
            processed = await self._process_trade(ticker, trade_qty, ask.price, buyer, ask.creator, fee={'buyer_fee': taker_fee, 'seller_fee': seller_fee})
            if'error' in processed: 
                continue
            self.books[ticker].asks[idx].qty -= Decimal(str(trade_qty))
            fills.append({'qty': trade_qty, 'price': ask.price, 'fee': taker_fee})
            unfilled_qty -= Decimal(str(trade_qty))
            if unfilled_qty == 0:
                break
        self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
        if(fills == []):
            return {"market_buy": "no fills"}                
        return {"market_buy": ticker, "buyer": buyer, 'qty': qty,  "fills": fills}

    async def market_sell(self, ticker:str, qty: int, seller: str, fee={'buyer_fee':0, 'seller_fee':0}, accounting='FIFO') -> dict:
        qty = Decimal(str(qty))
        if qty <= 0:
            return {"market_sell": "qty_must_be_greater_than_zero", "seller": seller}        
        unfilled_qty = qty
        fills = []
        has_assets = await self.agent_has_assets(seller, ticker, qty)
        if has_assets == False:
            return {"market_sell": "insufficient assets", "seller": seller}
        for idx, bid in enumerate(self.books[ticker].bids):
            if bid.creator == seller:
                continue
            trade_qty = Decimal(str(min(bid.qty, unfilled_qty)))
            taker_fee = self.fees.taker_fee(trade_qty*bid.price)
            has_assets = await self.agent_has_assets(seller, ticker, trade_qty)
            if has_assets == False:
                return {"market_sell": "insufficient assets", "seller": seller}
            has_cash = await self.agent_has_assets(seller, self.default_currency['symbol'], taker_fee)
            if has_cash == False:
                return {"market_sell": "insufficient assets", "seller": seller}
            await self.freeze_assets(seller, ticker, trade_qty)
            await self.freeze_assets(seller, self.default_currency['symbol'], taker_fee)
            buyer_fee = (bid.fee / bid.qty) * trade_qty
            processed = await self._process_trade(ticker, trade_qty,bid.price, bid.creator, seller, accounting, fee={'buyer_fee': buyer_fee, 'seller_fee': taker_fee})
            if'error' in processed: 
                continue
            fills.append({'qty': trade_qty, 'price': bid.price, 'fee': taker_fee})
            unfilled_qty -= Decimal(str(trade_qty))
            self.books[ticker].bids[idx].qty -= Decimal(str(trade_qty))
            if unfilled_qty == 0:
                break
        self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
        if(fills == []):
            return {"market_sell": "no fills"}                
        return {"market_sell": ticker, "seller": seller, 'qty': qty, "fills": fills }

    async def register_agent(self, name, initial_assets={}) -> dict:
        """
        `initial_assets`: a dict where the keys are symbols and values are quantities: e.g. {'BTC': 1000, 'ETH': 1000}
        """
        self.logger.info('registering agent', name)
        if(len(self.agents) >= self.max_agents):
            return {'error': 'max agents reached'}
        registered_name = name + str(UUID())[0:8]
        positions = []
        for asset in initial_assets:
            side = {
                'agent': registered_name, 
                'cash_flow': 0, 
                'price': 0, 
                'ticker': asset, 
                'initial_qty': 0, 
                'qty': Decimal(str(initial_assets[asset])), 
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
            initial_assets[asset] = Decimal(str(initial_assets[asset]))

        self.agents.append({
            'name':registered_name,
            '_transactions':[], 
            'positions': positions, 
            'assets': initial_assets,
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
                    if asset == self.default_currency['symbol']:
                        # if this is exiting a quote currency, we calculate it's basis...
                        exit['basis'] = {
                            'basis_initial_unit': self.default_currency['symbol'],
                            'basis_per_unit': abs(exit_transaction['price']),
                            'basis_txn_id': exit_transaction['id'], #NOTE this txn is stored here -> self.agents[agent_idx]['_transactions']
                            'basis_date': exit['dt']
                        }
                    else:
                        # ...otherwise, pass the enter basis along
                        exit['basis'] = enter['basis']
                        if exit['basis']['basis_initial_unit'] != self.default_currency['symbol']:
                            # chain basis and update if needed
                            # e.g. USD (exit, set basis) -> BTC (enter, consume basis) -> BTC (exit, retain basis) -> ETH (enter, pass basis and adjust to ETH)
                            cost_basis_per_unit = (enter['basis']['basis_per_unit'] * abs(side['cash_flow'])) / abs(side['qty'])
                            self.logger.info(f"cost_basis_per_unit: {cost_basis_per_unit:.16f}")
                            exit['basis']['basis_per_unit'] = cost_basis_per_unit

                    if enter['qty'] >= exit_transaction['qty']:
                        exit['qty'] = Decimal(str(exit_transaction['qty']))
                        enter['qty'] -= Decimal(str(exit_transaction['qty']))
                        position['qty'] -= Decimal(str(exit_transaction['qty']))
                        exit_transaction['qty'] = 0
                        self.logger.info('full exit', exit_transaction['qty'], position['qty'])
                        position['exits'].append(exit)
                        return {'exit_position': exit}
                    elif enter['qty'] > 0:
                        # partial exit
                        exit_transaction['qty'] -= Decimal(str(enter['qty']))
                        exit['qty'] = Decimal(str(enter['qty']))
                        enter['qty'] = 0
                        position['qty'] -= Decimal(str(enter['qty']))
                        self.logger.info('partial exit', exit_transaction['qty'], position['qty'])
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
                await self.update_assets(side['ticker'], side['qty'], agent_idx)
                self.agents[agent_idx]['frozen_assets'][self.default_currency['symbol']] -= Decimal(str(abs(side['cash_flow'])))
                if side['fee'] > 0: await self.pay_exchange_fees(agent_idx, self.default_currency['symbol'], side['fee'])
                exit = await self.exit_position(side, self.default_currency['symbol'], side['cash_flow'], agent_idx)
                enter = await self.enter_position(side, side['ticker'], side['qty'], agent_idx, position_id, basis=exit['exit_position']['basis'])

            elif side['type'] == 'sell':
                await self.update_assets(self.default_currency['symbol'], side['cash_flow'], agent_idx)
                self.agents[agent_idx]['frozen_assets'][side['ticker']] -= Decimal(str(abs(side['qty'])))
                self.logger.info(f"{self.agents[agent_idx]['name']} frozen remaining {side['ticker']} {self.agents[agent_idx]['frozen_assets'][side['ticker']]:.16f}")
                if side['fee'] > 0: await self.pay_exchange_fees(agent_idx, self.default_currency['symbol'], side['fee'])
                await self.sort_positions(agent_idx, accounting)
                exit = await self.exit_position(side, side['ticker'], side['qty'], agent_idx)
                self.logger.info(f" exit basis: {exit['exit_position']['basis']}, asset {exit['exit_position']['asset']} qty {exit['exit_position']['qty']} ")
                enter = await self.enter_position(side, self.default_currency['symbol'], side['cash_flow'], agent_idx, None, basis=exit['exit_position']['basis'])
                self.logger.info(f" enter basis: {enter['enter_position']['basis']}, asset {enter['enter_position']['asset']} qty {enter['enter_position']['qty']} ")

                if self.default_currency['symbol'] == self.default_currency['symbol']:
                    #NOTE: basis represents the initial default quote currency amount (cash_flow) traded for the first enter in the chain
                    # consider the following trade chain:
                    # USD (exit, basis) -> BTC (enter, consume basis) -> BTC (exit, retain basis) -> ETH (enter, passed basis)
                    basis_amount = abs(side['qty']) * exit['exit_position']['basis']['basis_per_unit']
                    self.logger.info('basis_amount', basis_amount, exit['exit_position']['basis']['basis_per_unit'], 'amount', side['cash_flow'])
                    await self.taxable_event(self.agents[agent_idx], side['cash_flow'], side['dt'], basis_amount, exit['exit_position']['basis']['basis_date'])

    async def pay_exchange_fees(self, agent_idx, asset, amount) -> None:
        self.logger.info(f"{self.agents[agent_idx]['name']} assets before {asset} {self.agents[agent_idx]['frozen_assets'][asset]:.16f}")
        self.logger.info(self.agents[agent_idx]['name'], 'paying exchange fee', asset, amount )
        self.agents[agent_idx]['frozen_assets'][asset] -= Decimal(str(abs(amount)))
        self.logger.info(f"{self.agents[agent_idx]['name']} assets after {asset} {self.agents[agent_idx]['frozen_assets'][asset]:.16f}")
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
        return await super().agent_has_assets(agent, asset, qty)
    
    async def agent_has_assets_frozen(self, agent, asset, qty) -> bool:
        agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            if asset in self.agents[agent_idx]['frozen_assets']:
                self.logger.info(agent, 'frozen', asset, 'needed:', qty, 'has:', self.agents[agent_idx]['frozen_assets'][asset])
                return self.agents[agent_idx]['frozen_assets'][asset] >= qty
            else:
                return False
        else:
            return False

    async def agent_has_cash(self, agent, amount, qty) -> bool:
        return await self.agent_has_assets(agent, self.default_currency['symbol'], amount * qty)

    async def agents_cash(self) -> list:
        """
        returns a list of all agents and their cash
        """
        info = []
        for agent in self.agents:
            if agent['name'] != 'init_seed':
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
            side = {'id': str(UUID()), 'agent':agent, 'cash_flow':0, 'price': 0, 'ticker': asset, 'qty': amount, 'fee':0, 'dt': self.datetime, 'type': note}
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
            qty = Decimal(amount)
            side = {'id': str(UUID()), 'agent':agent,'cash_flow':0, 'price': 0, 'ticker':asset, 'qty': -qty, 'fee':0, 'dt': self.datetime, 'type': 'sell'}
            exit = await self.exit_position(side, asset, -qty, agent_idx)
            if 'error' in exit:
                return exit
            await self.update_assets(asset, -qty, agent_idx)
            return {asset: self.agents[agent_idx]['assets'][asset]}
        else:
            return {'error': 'agent not found'}

    async def add_cash(self, agent, amount, note='') -> dict:
        return await self.add_asset(agent, self.default_currency['symbol'], amount, note)          
    
    async def remove_cash(self, agent, amount, note='') -> dict:
        return await self.remove_asset(agent, self.default_currency['symbol'], amount, note)

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
        Returns a list of agents and their positions
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
        Returns a list of all tickers
        """
        return self.assets
    