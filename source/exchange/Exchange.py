import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import pandas as pd
import math
from typing import List
from .types.OrderBook import OrderBook
from .types.Trade import Trade
from .types.LimitOrder import LimitOrder
from .types.OrderSide import OrderSide
from .types.Fees import Fees
from source.utils._utils import format_dataframe_rows_to_dict
from source.Archive import Archive
from uuid import uuid4 as UUID
from datetime import timedelta
from source.utils.logger import Logger

class Exchange():
    def __init__(self, datetime= None):
        self.agents = []
        self.assets = {}
        self.books = {}
        self.trade_log: List[Trade] = [] #TODO: this is going to get to big to hold in memory, need a DB
        self.datetime = datetime
        self.default_quote_currency = {'name': 'US Dollar', 'symbol': 'USD', 'id': str(UUID())}
        self.fees = Fees()
        self.agents_archive = Archive('agents')
        self.assets_archive = Archive('assets')
        self.books_archive = Archive('books')
        self.trade_log_archive = Archive('trade_log')
        self.max_agents = 100000
        self.max_assets = 1000
        self.trade_log_limit = 100000
        self.max_asks = 100000
        self.max_bids = 100000
        self.logger = Logger('Exchange')

    async def __str__(self):
        return ', '.join(ob for ob in self.books)

    async def next(self):
        await self.archive()
        await self.prune_trades()
        
    async def archive(self):
        self.agents_archive.store(self.agents)
        self.assets_archive.store(self.assets)
        self.books_archive.store(self.books)
        self.trade_log_archive.store(self.trade_log)

    async def prune_trades(self):
        """
        Removes old trades from memory, if archiving can still be retrieved from the archive
        """
        if len(self.trade_log) >= self.trade_log_limit:
            trades_to_prune = int(len(self.trade_log)/2)
            self.trade_log = self.trade_log[trades_to_prune:]

    async def create_asset(self, ticker: str, asset_type='stock', market_qty=1000, seed_price=100, seed_bid=.99, seed_ask=1.01) -> OrderBook:
        """_summary_

        Args:
            ticker (str): the ticker of the new asset
            asset_type (str, optional): the type of asset, default: 'stock', 'crypto', 'currency', 'bond', 'cash'
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
        cash_position =  {"id":self.default_quote_currency['id'],"ticker": "CASH", "price": 1,"qty": market_qty * seed_price, "dt": self.datetime, "enters":[], "exits": [], }
        self.agents.append({'name':'init_seed_'+ticker,'cash':market_qty * seed_price,'_transactions':[], "taxable_events": [], 'positions': [cash_position],  'assets': {ticker: market_qty}})
        await self._process_trade(ticker, market_qty, seed_price, 'init_seed_'+ticker, 'init_seed_'+ticker, position_id='init_seed_'+ticker)
        await self.limit_buy(ticker, seed_price * seed_bid, 1, 'init_seed_'+ticker)
        await self.limit_sell(ticker, seed_price * seed_ask, market_qty, 'init_seed_'+ticker)
        return self.assets[ticker]
   
    async def _process_trade(self, ticker, qty, price, buyer, seller, accounting='FIFO', fee=0.0, position_id=None):
        if not await self.agent_has_cash(buyer, price, qty):
            return None
        if not await self.agent_has_assets(seller, ticker, qty):
            return None
        
        trade = Trade(ticker, qty, price, buyer, seller, self.datetime, fee=fee)
        self.trade_log.append(trade)

        txn_time = self.datetime

        transaction = [
            {'id': str(UUID()), 'agent':buyer,'cash_flow':-qty*price, 'price': price, 'ticker':ticker, 'qty': qty, 'fee':fee, 'dt': txn_time, 'type': 'buy'},
            {'id': str(UUID()), 'agent':seller,'cash_flow':qty*price, 'price': price, 'ticker':ticker, 'qty': -qty, 'fee':fee, 'dt': txn_time, 'type': 'sell'}
        ]
        await self.update_agents(transaction, accounting, position_id=position_id)
        return transaction

    async def get_order_book(self, ticker: str) -> OrderBook:
        """returns the OrderBook of a given Asset

        Args:
            ticker (str): the ticker of the asset

        returns:
            OrderBook: the orderbook of the asset.
        """
        if ticker in self.books:
            return self.books[ticker]
        else:
            return OrderBook("error")
     
    async def get_latest_trade(self, ticker:str) -> Trade:
        """Retrieves the most recent trade of a given asset

        Args:
            ticker (str): the ticker of the trade

        returns:
            Trade
        """
        latest_trade = next((trade for trade in self.trade_log[::-1] if trade.ticker == ticker), {'error': 'no trades found'})
        if isinstance(latest_trade, Trade):
            return latest_trade.to_dict()
        else:
            return {'error': 'no trades found'}

    async def get_quotes(self, ticker) -> dict:
        if ticker not in self.books: return {"error" : "ticker not found"}
        try:
            # TODO: if more than one order has the best price, add the quantities.
            best_bid = self.books[ticker].bids[0]
            best_ask = self.books[ticker].asks[0]
        except IndexError :
            best_bid = LimitOrder(ticker, 0, 0, 'null_quote', OrderSide.BUY, self.datetime)
            best_ask = LimitOrder(ticker, 0, 0, 'null_quote', OrderSide.SELL, self.datetime)

        quotes = {
            'ticker': ticker,
            'bid_qty': best_bid.qty,
            'bid_p': best_bid.price,
            'ask_qty': best_ask.qty,
            'ask_p': best_ask.price,
        }
        return quotes

    async def get_midprice(self, ticker:str) -> float:
        """returns the current midprice of the best bid and ask quotes.

        Args:
            ticker (str): the ticker of the asset

        returns:
            float: the current midprice
        """
        quotes = await self.get_quotes(ticker)
        return (quotes['bid_p'] + quotes['ask_p']) / 2

    async def get_trades(self, ticker:str, limit=20) -> list:
        """Retrieves all past trades of a given asset

        Args:
            ticker (str): the ticker of the asset

        returns:
            pd.DataFrame: a dataframe containing all trades
        """
        if ticker not in self.books: return ["error ticker not found"]
        trades = pd.DataFrame.from_records([t.to_dict() for t in self.trade_log if t.ticker == ticker]).tail(limit)
        return format_dataframe_rows_to_dict(trades)
    
    async def get_price_bars(self, ticker, limit=20, bar_size='1D') -> list:
        ''' returns a list of price bars for a given asset
        Args:
            ticker (str): the ticker of the asset
            limit (int): the number of bars to return
            bar_size (str): the size of the bars to return. default is 1 day. `Year = Y`, `Month = M`, `Week = W`, `Day = D`, `Hour = H`, `Minute = T`, `Second = S`
        
        '''
        trades = self.trade_log
        if len(trades) == 0:
            return []
        trades = sorted(trades, key=lambda x: x.dt)
        start_time = trades[0].dt
        end_time = trades[-1].dt

        def interval_key (length, period): 
            key = {
                'Y': timedelta(days=365 * length),
                'M': timedelta(days=30 * length),
                'W': timedelta(days=7 * length),
                'D': timedelta(days=length),
                'H': timedelta(hours=length),
                'T': timedelta(minutes=length),
                'S': timedelta(seconds=length),
            }
            return key[period]

        bar_length = int(bar_size[:-1])

        if type(bar_length) is not int:
            raise ValueError(f'bar_length {bar_length} must be an integer')
        if bar_length <= 0:
            raise ValueError('bar_size must be greater than 0')

        interval = interval_key(bar_length, bar_size[-1])

        ohlcv_data = []

        prev_candle = None

        while start_time <= end_time:
            interval_trades = [trade for trade in trades if start_time <= trade.dt < start_time + interval]
            
            if ticker is not None:
                interval_trades = [trade for trade in interval_trades if trade.ticker == ticker]
            
            if interval_trades:
                open_price = interval_trades[0].price
                high_price = max(trade.price for trade in interval_trades)
                low_price = min(trade.price for trade in interval_trades)
                close_price = interval_trades[-1].price
                volume = sum(trade.qty for trade in interval_trades)

                ohlcv_entry = {
                    'dt': start_time,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                }
                ohlcv_data.append(ohlcv_entry)
                prev_candle = ohlcv_entry
            else:
                if prev_candle:
                    prev_candle_copy = prev_candle.copy()
                    prev_candle_copy['dt'] = start_time
                    ohlcv_data.append(prev_candle_copy)

            start_time += interval
            
            if limit is not None and len(ohlcv_data) >= limit:
                break

        return ohlcv_data
    
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

    async def limit_buy(self, ticker: str, price: float, qty: int, creator: str, fee=0, tif='GTC', position_id=UUID()) -> LimitOrder:
        if len(self.books[ticker].bids) >= self.max_bids:
            return LimitOrder(ticker, 0, 0, creator, OrderSide.BUY, self.datetime, status='error', accounting='max_bid_depth_reached')        
        has_cash = await self.agent_has_cash(creator, price, qty)
        if has_cash:
            if not self.assets[ticker]['type'] == 'crypto':
                price = round(price,2)
            # check if we can match trades before submitting the limit order
            unfilled_qty = qty
            fills=[]
            while unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_ask = await self.get_best_ask(ticker)
                if best_ask.creator != 'null_quote' and best_ask.creator != creator and price >= best_ask.price:
                    trade_qty = min(unfilled_qty, best_ask.qty)
                    taker_fee = self.fees.taker_fee(trade_qty)
                    self.fees.total_fee_revenue += taker_fee
                    if(type(fee) is str): fee = float(fee)
                    fills.append({'qty': trade_qty, 'price': best_ask.price, 'fee': fee+taker_fee, 'creator': best_ask.creator})
                    await self._process_trade(ticker, trade_qty, best_ask.price, creator, best_ask.creator, fee=fee+taker_fee, position_id=position_id)
                    unfilled_qty -= trade_qty
                    self.books[ticker].asks[0].qty -= trade_qty
                    self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
                else:
                    break
            queue = len(self.books[ticker].bids)
            for idx, order in enumerate(self.books[ticker].bids):
                if price > order.price:
                    queue = idx
                    break
            maker_fee = 0
            if unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(unfilled_qty)
                self.fees.total_fee_revenue += maker_fee
                maker_order = LimitOrder(ticker, price, unfilled_qty, creator, OrderSide.BUY, self.datetime,fee=fee+maker_fee, position_id=position_id, fills=fills)
                self.books[ticker].bids.insert(queue, maker_order)
                return maker_order
            else:
                filled_taker_order = LimitOrder(ticker, price, qty, creator, OrderSide.BUY, self.datetime,fee=fee+maker_fee, position_id=position_id, fills=fills)
                return filled_taker_order
        else:
            return LimitOrder("error", 0, 0, 'insufficient_funds', OrderSide.BUY, self.datetime)

    async def limit_sell(self, ticker: str, price: float, qty: int, creator: str, fee=0, tif='GTC', accounting='FIFO') -> LimitOrder:
        if len(self.books[ticker].asks) >= self.max_asks:
            return LimitOrder(ticker, 0, 0, creator, OrderSide.SELL, self.datetime, status='error', accounting='max_ask_depth_reached')        
        has_assets = await self.agent_has_assets(creator, ticker, qty)
        if has_assets:
            if not self.assets[ticker]['type'] == 'crypto':
                price = round(price,2)
            unfilled_qty = qty
            # check if we can match trades before submitting the limit order
            fills = []
            while unfilled_qty > 0:
                if tif == 'TEST':
                    break
                best_bid = await self.get_best_bid(ticker)
                if best_bid.creator != 'null_quote' and best_bid.creator != creator and price <= best_bid.price:
                    trade_qty = min(unfilled_qty, best_bid.qty)
                    taker_fee = self.fees.taker_fee(trade_qty)
                    self.fees.total_fee_revenue += taker_fee
                    if(type(fee) is str): fee = float(fee)
                    fills.append({'qty': trade_qty, 'price': best_bid.price, 'fee': fee+taker_fee, 'creator': best_bid.creator})
                    await self._process_trade(ticker, trade_qty, best_bid.price, best_bid.creator, creator, accounting, fee=fee+taker_fee)
                    unfilled_qty -= trade_qty
                    self.books[ticker].bids[0].qty -= trade_qty
                    self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
                else:
                    break
            queue = len(self.books[ticker].asks)
            for idx, order in enumerate(self.books[ticker].asks):
                if price < order.price:
                    queue = idx
                    break
            maker_fee = 0
            if unfilled_qty > 0:
                maker_fee = self.fees.maker_fee(unfilled_qty)
                self.fees.total_fee_revenue += maker_fee
                maker_order = LimitOrder(ticker, price, unfilled_qty, creator, OrderSide.SELL, self.datetime, fee=fee+maker_fee, accounting=accounting, fills=fills)
                self.books[ticker].asks.insert(queue, maker_order)
                return maker_order
            else:
                filled_taker_order = LimitOrder(ticker, price, qty, creator, OrderSide.SELL, self.datetime, fee=fee+maker_fee, accounting=accounting, fills=fills)
                return filled_taker_order
        else:
            return LimitOrder("error", 0, 0, 'insufficient_assets', OrderSide.SELL, self.datetime)

    async def get_order(self, ticker, id) -> LimitOrder:
        if ticker in self.books:
            bid = next(([idx,o] for idx, o in enumerate(self.books[ticker].bids) if o.id == id),None)
            if bid:
                return bid[1]
            ask = next(([idx,o] for idx, o in enumerate(self.books[ticker].asks) if o.id == id),None)
            if ask:
                return ask[1]
        return {'error': 'order not found'}

    async def cancel_order(self, ticker, id) -> dict:
        if ticker in self.books:
            bid = next(([idx,o] for idx, o in enumerate(self.books[ticker].bids) if o.id == id),None)
            if bid:
                cancel_order = self.books[ticker].bids[bid[0]]
                self.books[ticker].bids.pop(bid[0])
                return {"cancelled_order": cancel_order.to_dict_full()}
            ask = next(([idx,o] for idx, o in enumerate(self.books[ticker].asks) if o.id == id),None)
            if ask:
                cancel_order = self.books[ticker].asks[ask[0]]
                self.books[ticker].asks.pop(ask[0])
                return {"cancelled_order": cancel_order.to_dict_full()}
        return {"cancelled_order": "order not found"}

    async def cancel_all_orders(self, agent, ticker) -> dict:
        self.books[ticker].bids[:] = [b for b in self.books[ticker].bids if b.creator != agent]
        self.books[ticker].asks[:] = [a for a in self.books[ticker].asks if a.creator != agent]
        return {"cancelled_all_orders": ticker}

    async def market_buy(self, ticker: str, qty: int, buyer: str, fee=0.0) -> dict:
        best_price = (await self.get_best_ask(ticker)).price
        has_cash = (await self.agent_has_cash(buyer, best_price, qty))
        if has_cash:
            fills = []
            for idx, ask in enumerate(self.books[ticker].asks):
                if ask.creator == buyer:
                    continue
                trade_qty = min(ask.qty, qty)
                self.books[ticker].asks[idx].qty -= trade_qty
                qty -= trade_qty
                taker_fee = self.fees.taker_fee(qty)
                self.fees.total_fee_revenue += taker_fee
                if(type(fee) is str): fee = float(fee)
                fills.append({'qty': trade_qty, 'price': ask.price, 'fee': fee+taker_fee})
                await self._process_trade(ticker, trade_qty,ask.price, buyer, ask.creator, fee=fee+taker_fee)
                if qty == 0:
                    break
            self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
            if(fills == []):
                return {"market_buy": "no fills"}
            return {"market_buy": ticker, "buyer": buyer, "fills": fills}
        else:
            return {"market_buy": "insufficient funds"}

    async def market_sell(self, ticker: str, qty: int, seller: str, fee=0.0, accounting='FIFO') -> dict:
        if await self.agent_has_assets(seller, ticker, qty):
            fills = []
            for idx, bid in enumerate(self.books[ticker].bids):
                if bid.creator == seller:
                    continue
                trade_qty = min(bid.qty, qty)
                self.books[ticker].bids[idx].qty -= trade_qty
                qty -= trade_qty
                taker_fee = self.fees.taker_fee(qty)
                self.fees.total_fee_revenue += taker_fee
                if(type(fee) is str): fee = float(fee)
                fills.append({'qty': trade_qty, 'price': bid.price, 'fee': fee+taker_fee})
                await self._process_trade(ticker, trade_qty,bid.price, bid.creator, seller, accounting, fee=fee+taker_fee)
                if qty == 0:
                    break
            self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
            if(fills == []):
                return {"market_sell": "no fills"}
            return {"market_sell": ticker, "seller": seller, "fills": fills }
        else:
            return {"market_sell": "insufficient assets"}

    async def agent_has_cash(self, agent, price, qty) -> bool:
        agent_cash = (await self.get_cash(agent))
        return agent_cash['cash'] >= price * qty
    
    async def agent_has_assets(self, agent, ticker, qty) -> bool:
        agent_assets = (await self.get_assets(agent))
        if ticker in agent_assets['assets']:
            return agent_assets['assets'][ticker] >= qty
        else: 
            return False
        
    @property
    async def trades(self) -> pd.DataFrame:
        return pd.DataFrame.from_records([t.to_dict() for t in self.trade_log]).set_index('dt')

    async def _set_datetime(self, dt) -> None:
        self.datetime = dt

    async def get_transactions(self, agent) -> dict:
        #TODO: paginate this
        return {'transactions':(await self.get_agent(agent))['_transactions']}

    async def register_agent(self, name, initial_cash) -> dict:
        #TODO: use an agent class???
        if(len(self.agents) >= self.max_agents):
            return {'error': 'max agents reached'}
        registered_name = name + str(UUID())[0:8]
        self.agents.append({
            'name':registered_name,
            'cash':initial_cash,
            '_transactions':[], 
            'positions': [ {"id":self.default_quote_currency['id'],"ticker": "CASH", "price": 1,"qty": initial_cash, "dt": self.datetime, "enters":[], "exits": []}], 
            'assets': {},
            "taxable_events": []
        })
        return {'registered_agent':registered_name}
    
    async def get_assets(self, agent) -> dict:
        agent_info = await self.get_agent(agent)
        return {'assets': agent_info['assets']}
    
    async def get_position(self, agent, position_id) -> dict:
        agent_info = await self.get_agent(agent)
        for position in agent_info['positions']:
            if position['id'] == position_id:
                return position
        return None

    async def enter_position(self, side, agent_idx, position_id) -> dict:
        buy = side.copy()
        start_new_position = True
        agent = self.agents[agent_idx]
        positions = agent['positions']
        for position in positions:
            if position['id'] == position_id:
                start_new_position = False
                position['qty'] += buy['qty']
                position['enters'].append(buy)
                return {'enter_position': 'existing success'}
            
        if start_new_position:
            # new_position = Position(UUID(), buy['ticker'], buy['price'], buy['qty'], buy['dt'], enters=[buy]).to_dict()
            enter = side.copy()
            enter['initial_qty'] = side['qty']
            enter['id'] = str(UUID())
            new_position = {
                'id': str(UUID()),
                'ticker': side['ticker'],
                'price': side['price'],
                'qty': side['qty'],
                'dt': side['dt'],
                'enters': [enter],
                'exits': []
            }
            positions.append(new_position)        
            return {'enter_position': 'new success'}
    
    async def exit_position(self, side, agent_idx) -> None:
        sell = side.copy()
        agent = self.agents[agent_idx]
        positions = agent['positions']
        viable_positions = [position for position in positions if position['ticker'] == sell['ticker'] and position['qty'] > 0]
        if len(viable_positions) == 0: 
            return {'exit_position': 'no viable positions'}
        #NOTE: sell sell['qty'] comes in negative, so we need to flip the sign and add the quantity flow to the sell['qty'] as we pull from enters 
        while sell['qty'] < 0:
            for position in viable_positions:
                enters = position['enters']
                if len(enters) == 0:
                    return {'exit_position': 'no enters'}
                for enter in enters:
                    normalised_qty = sell['qty'] * -1
                    exit = {
                        'id': str(UUID()),
                        'agent': agent['name'],
                        'cash_flow': sell['cash_flow'],
                        'ticker': sell['ticker'],
                        'qty': normalised_qty,
                        'dt': sell['dt'],
                        'type': sell['type'],
                        'pnl': (sell['price']*normalised_qty)-(enter['price']*normalised_qty), 
                        'enter_id': enter['id'],
                        'enter_date': enter['dt']
                    }
                    if exit['pnl'] > 0:
                        taxable_event = {"type": 'capital_gains', 'exit_id': exit['id'], 'enter_id':enter['id'], 'enter_date': enter['dt'], 'exit_date': exit['dt'], 'pnl': exit['pnl']}
                        agent['taxable_events'].append(taxable_event)
                        
                    if enter['qty'] >= normalised_qty:
                        position['qty'] += sell['qty']
                        enter['qty'] += sell['qty']
                        position['exits'].append(exit)
                        sell['qty'] = 0
                        return {'exit_position': 'success'}
                    else:
                        position['exits'].append(exit)
                        sell['qty'] += position['qty']
                        enter['qty'] += sell['qty']
                        position['qty'] = 0
        return {'exit_position': 'no position to exit'}                            

    async def sort_positions(self, agent_idx, accounting) -> None:
        """Sorts the positions of an agent by date"""
        if accounting == 'FIFO':
            self.agents[agent_idx]['positions'].sort(key=lambda x: x['dt'])
        if accounting == 'LIFO':
            self.agents[agent_idx]['positions'].sort(key=lambda x: x['dt'], reverse=True)

    async def update_assets(self, side, agent_idx) -> None:
        if side['ticker'] in self.agents[agent_idx]['assets']: 
            self.agents[agent_idx]['assets'][side['ticker']] += side['qty']
        else: 
            self.agents[agent_idx]['assets'][side['ticker']] = side['qty']        

    async def update_agents(self, transaction, accounting, position_id) -> None:
        for side in transaction:
            agent_idx = await self.get_agent_index(side['agent'])
            if agent_idx is None:
                return {'update_agents': 'agent not found'}
            self.agents[agent_idx]['_transactions'].append(side)
             # NOTE: this will "remove" cash on the sell side of the transaction
            await self.update_assets(side, agent_idx)
            if side['type'] == 'buy':
                await self.remove_cash(agent_idx, -side['cash_flow'])
                await self.enter_position(side, agent_idx, position_id)
            elif side['type'] == 'sell':
                await self.add_cash(agent_idx, side['cash_flow'])
                await self.sort_positions(agent_idx, accounting)
                await self.exit_position(side, agent_idx)
      
    async def get_agent(self, agent_name)  -> dict:
        return next((d for (index, d) in enumerate(self.agents) if d['name'] == agent_name), {'error': 'agent not found'})

    async def get_agent_index(self,agent_name) -> dict:
        return next((index for (index, d) in enumerate(self.agents) if d['name'] == agent_name), None)
    
    async def get_agents(self) -> dict:
        return self.agents
    
    async def total_cash(self) -> float:
        return sum(agent['cash'] for agent in self.agents if 'init_seed' not in agent['name'])
    
    async def agents_cash(self) -> dict:
        info = []
        for agent in self.agents:
            if agent['name'] != 'init_seed':
                last_action = None
                if len(agent['_transactions']) > 0:
                    last_action =agent['_transactions'][-1]['type']
                info.append({agent['name']: {'cash':agent['cash'],'assets':agent['assets'], 'last_action': last_action }})
        return info

    async def get_cash(self, agent_name) -> dict:
        agent_info = await self.get_agent(agent_name)
        return {'cash':agent_info['cash']}

    async def add_cash(self, agent, amount, note='', taxable=False) -> dict:
        """Adds cash to an agent's account
        
        Arguments:
            agent {str | int} -- name of the agent or index of the agent
            amount {float} -- amount of cash to add
            """
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            side = {'id': str(UUID()), 'agent':agent,'cash_flow':amount, 'price': 1, 'ticker':'CASH', 'qty': amount, 'fee':0, 'dt': self.datetime, 'type': note}
            await self.enter_position(side, agent_idx, self.default_quote_currency['id'])
            self.agents[agent_idx]['cash'] += amount
            if taxable == True:
                taxable_event = {"type": note, 'exit_id': side['id'], 'enter_id':side['id'], 'enter_date': self.datetime, 'exit_date': self.datetime, 'pnl': amount}
                self.agents[agent_idx]['taxable_events'].append(taxable_event)
            return {'cash':self.agents[agent_idx]['cash']}
        else:
            return {'error': 'agent not found'}

    async def remove_cash(self, agent, amount, note='') -> dict:
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            side = {'id': str(UUID()), 'agent':agent,'cash_flow':-amount, 'price': 1, 'ticker':'CASH', 'qty': -amount, 'fee':0, 'dt': self.datetime, 'type': 'sell'}
            await self.exit_position(side, agent_idx)
            self.agents[agent_idx]['cash'] -= amount
            return {'cash':self.agents[agent_idx]['cash']}
        else:
            return {'error': 'agent not found'}

    async def calculate_market_cap(self,ticker) -> float:
        """
        Calculates the market capitalization of a company
        Args: 
        ticker: the ticker of the asset
        """
        price = 0
        latest_trade = (await self.get_latest_trade(ticker))
        if "price" in latest_trade:
            price = latest_trade["price"]
        else:
            price = (await self.get_midprice(ticker))['midprice']

        market_cap = price  * (await self.get_outstanding_shares(ticker))
        return market_cap
    
    async def get_outstanding_shares(self, ticker) -> int:
        """
        Calculates the number of shares outstanding for a given ticker
        Args: 
        
        ticker: the ticker of the asset
        """
        shares_outstanding = 0
        for agent in self.agents:
            if agent['name'] != 'init_seed_'+ticker and ticker in agent['assets']:
                shares_outstanding += agent['assets'][ticker]
        return shares_outstanding
    
    async def get_agents_holding(self, ticker) -> list:
        """
        Returns a list of agents holding a given ticker
        Args: 
        
        ticker: the ticker of the asset
        """
        agents_holding = []
        for agent in self.agents:
            if ticker in agent['assets']:
                agents_holding.append(agent['name'])
        return agents_holding
    
    async def get_agents_positions(self,ticker) -> list:
        """
        Returns a list of agents positions of a given ticker
        """
        agent_positions = []
        for agent in self.agents:
            positions = []
            for position in agent['positions']:
                if ticker is None or position['ticker'] == ticker:
                    positions.append(position)
            agent_positions.append({'agent':agent['name'],'positions':positions})
        return agent_positions
    
    async def get_agents_simple(self) -> list:
        """
        Returns a list of agents and their cash and assets
        """
        agents_simple = []
        for agent in self.agents:
            agents_simple.append({'agent':agent['name'],'cash':agent['cash'],'assets':agent['assets']})
        return agents_simple
    
    async def get_positions(self, agent, page_size=10, page=1) -> dict:
        agent_info = await self.get_agent(agent)
        if "error" in agent_info:
            return agent_info
        
        positions = agent_info['positions']
        positions.sort(key=lambda position: position['dt'], reverse=True)

        positions = agent_info['positions']
        total_positions = len(positions)
        total_pages = math.ceil(total_positions / page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_positions = positions[start_idx:end_idx]

        next_page = page + 1 if end_idx < total_positions else None

        return {
            'agent': agent,
            'total_positions': total_positions,
            'page': page,
            'total_pages': total_pages,
            'page_size': page_size,
            'positions': paginated_positions,
            'next_page': next_page
        }

    async def get_taxable_events(self, agent=None) -> list:
        if agent is None:
            taxable_events = []
            for agent in self.agents:
                if "init_seed" in agent['name']:
                    continue
                if len(agent['taxable_events']) > 0:
                    taxable_events.append( {"agent": agent['name'], "taxable_events": agent['taxable_events']})
            return taxable_events
        elif type(agent) == str:
            agent_info = await self.get_agent(agent)
            if "error" in agent_info:
                return agent_info
            return [{"agent": agent, "taxable_events": agent_info['taxable_events']}]
        else:
            return {'error': 'agent(s) or taxable events not found'}

    async def get_tickers(self) -> list:
        """
        Returns a list of tickers
        """
        return list(self.assets.keys())