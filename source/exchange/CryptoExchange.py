from uuid import uuid4 as UUID

from source.exchange.types.LimitOrder import LimitOrder
from .Exchange import Exchange
from .types.OrderBook import OrderBook
from .types.CryptoTrade import CryptoTrade
from .types.LimitOrder import LimitOrder
from .types.OrderSide import OrderSide

#NOTE: symbols are the letters that represent a given asset, e.g. BTC, ETH, etc.
#NOTE: tickers are the combination of the symbol and the quote currency, e.g. BTC/USD, ETH/USD, etc.

class CryptoExchange(Exchange):
    def __init__(self, datetime= None):
        super().__init__(datetime=datetime)

    async def create_asset(self, symbol: str, pairs=[], market_qty=1000, seed_price=100, seed_bid=.99, seed_ask=1.01) -> dict:
        """_summary_
        Args:
            symbol (str): the symbol of the new asset
            pairs (str, optional): a list of symbols for aditional quote pairs, beyond the default quote currency, that this asset can be traded against. async defaults to [].
            marekt_qty (int, optional): the total amount of the asset in circulation. async defaults to 1000.
            seed_price (int, optional): Price of an initial trade that is created for ease of use. async defaults to 100.
            seed_bid (float, optional): Limit price of an initial buy order, expressed as percentage of the seed_price. async defaults to .99.
            seed_ask (float, optional): Limit price of an initial sell order, expressed as percentage of the seed_price. async defaults to 1.01.
        """
        if symbol in self.assets:
            return {"error" :f'asset {symbol} already exists'}
        pairs.append(self.default_quote_currency['symbol'])
        self.assets[symbol] = {'type': 'crypto', 'id' : str(UUID())}
        for pair in pairs:
            ticker = symbol+pair
            self.books[ticker] = OrderBook(ticker)
            quote_position =  {"id":'init_seed_'+ticker, 'asset': symbol, "price": 0,"qty": market_qty * seed_price, "dt": self.datetime, "enters":[], "exits": [], }
            self.agents.append({'name':'init_seed_'+ticker,'_transactions':[], "taxable_events": [], 'positions': [quote_position],  'assets': {symbol: market_qty, pair: market_qty * seed_price}})
            await self._process_trade(symbol, pair, market_qty, seed_price, 'init_seed_'+ticker, 'init_seed_'+ticker, position_id='init_seed_'+ticker)
            await self.limit_buy(symbol, pair, seed_price * seed_bid, 1, 'init_seed_'+ticker, position_id='init_seed_'+ticker)
            await self.limit_sell(symbol, pair,  seed_price * seed_ask, market_qty, 'init_seed_'+ticker)
        return self.assets[symbol]
    
    async def _process_trade(self, base, quote, qty, price, buyer, seller, accounting='FIFO', fee=0.0, position_id=None):
        if not await self.agent_has_assets(buyer, quote, qty):
            return None
        if not await self.agent_has_assets(seller, base, qty):
            return None
        
        trade = CryptoTrade(base, quote, qty, price, buyer, seller, self.datetime, fee=fee)
        self.trade_log.append(trade)

        txn_time = self.datetime

        transaction = [
            {'id': str(UUID()), 'agent':buyer,'quote_flow':-qty*price, 'price': price, 'base': base, 'quote': quote, 'qty': qty, 'fee':fee, 'dt': txn_time, 'type': 'buy'},
            {'id': str(UUID()), 'agent':seller,'quote_flow':qty*price, 'price': price, 'base': base, 'quote': quote, 'qty': -qty, 'fee':fee, 'dt': txn_time, 'type': 'sell'}
        ]
        await self.update_agents(transaction, accounting, position_id=position_id)
        return transaction    
    
    async def get_order_book(self, ticker:str) -> OrderBook:
        """returns the OrderBook of a given Asset

        Args:
            symbol (str): the symbol of the asset

        returns:
            OrderBook: the orderbook of the asset.
        """
        if ticker in self.books:
            return self.books[ticker]
        else:
            return OrderBook("error")    

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

    async def limit_buy(self, base: str, quote:str, price: float, qty: int, creator: str, fee=0, tif='GTC', position_id=UUID()) -> LimitOrder:
        has_asset = await self.agent_has_assets(creator, quote, qty * price)
        ticker = base+quote
        if has_asset:
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
                    await self._process_trade(base, quote, trade_qty, best_ask.price, creator, best_ask.creator, fee=fee+taker_fee, position_id=position_id)
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
        
    async def limit_sell(self, base: str, quote:str, price: float, qty: int, creator: str, fee=0, tif='GTC', accounting='FIFO') -> LimitOrder:
        ticker = base+quote
        has_assets = await self.agent_has_assets(creator, base, qty)
        if has_assets:
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
                    await self._process_trade(base, quote, trade_qty, best_bid.price, best_bid.creator, creator, accounting, fee=fee+taker_fee)
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
           
    async def cancel_order(self, base, quote, id) -> LimitOrder:
        ticker = base+quote
        return await super().cancel_order(ticker, id)
    
    async def cancel_all_orders(self, base, quote, creator) -> list:
        ticker = base+quote
        return await super().cancel_all_orders(creator, ticker)
    
    async def market_buy(self, base: str, quote:str, qty: int, buyer: str, fee=0.0) -> dict:
        ticker = base+quote
        best_price = (await self.get_best_ask(ticker)).price
        has_asset = await self.agent_has_assets(buyer, quote, qty * best_price)
        if has_asset:
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
                await self._process_trade(base, quote, trade_qty,ask.price, buyer, ask.creator, fee=fee+taker_fee)
                if qty == 0:
                    break
            self.books[ticker].asks = [ask for ask in self.books[ticker].asks if ask.qty > 0]
            if(fills == []):
                return {"market_buy": "no fills"}
            return {"market_buy": ticker, "buyer": buyer, "fills": fills}
        else:
            return {"market_buy": "insufficient funds"}

    async def market_sell(self, base: str, quote:str, qty: int, seller: str, fee=0.0, accounting='FIFO') -> dict:
        ticker = base+quote
        if await self.agent_has_assets(seller, base, qty):
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
                await self._process_trade(base, quote, trade_qty,bid.price, bid.creator, seller, accounting, fee=fee+taker_fee)
                if qty == 0:
                    break
            self.books[ticker].bids = [bid for bid in self.books[ticker].bids if bid.qty > 0]
            if(fills == []):
                return {"market_sell": "no fills"}
            return {"market_sell": ticker, "seller": seller, "fills": fills }
        else:
            return {"market_sell": "insufficient assets"}

    async def register_agent(self, name, initial_assets={}) -> dict:
        """
        `initial_assets`: a dict where the keys are symbols and values are quantities: e.g. {'BTC': 1000, 'ETH': 1000}
        """
        registered_name = name + str(UUID())[0:8]
        positions = []
        for asset in initial_assets:
            side = {'agent': registered_name, 'quote_flow': 0, 'price': 0, 'base': asset, 'quote': self.default_quote_currency['symbol'], 'initial_qty': 0, 'qty': initial_assets[asset], 'dt': self.datetime, 'type': 'buy'}
            new_position = await self.new_position(side, side['base'], side['qty'])
            positions.append(new_position)

        self.agents.append({
            'name':registered_name,
            '_transactions':[], 
            'positions': positions, 
            'assets': initial_assets,
            "taxable_events": []
        })
        return {'registered_agent':registered_name}
    
    async def new_position(self, side, asset, qty) -> dict:
        enter = side.copy()
        enter['initial_qty'] = qty
        enter['id'] = str(UUID())
        return {
            'id': str(UUID()),
            'asset': asset,
            'price': side['price'],
            'qty': qty,
            'dt': side['dt'],
            'enters': [enter],
            'exits': []
        }
    
    async def enter_position(self, side, asset, qty, agent_idx, position_id) -> dict:
        buy = side.copy()
        start_new_position = True
        agent = self.agents[agent_idx]
        positions = agent['positions']
        for position in positions:
            if position['id'] == position_id or position['asset'] == asset:
                start_new_position = False
                position['qty'] += qty
                position['enters'].append(buy)
                return {'enter_position': 'existing success'}
            
        if start_new_position:
            new_position = await self.new_position(side, asset, qty)
            positions.append(new_position)        
            return {'enter_position': 'new success'}
    
    async def exit_position(self, side, asset, qty, agent_idx) -> None:
        sell = side.copy()
        agent = self.agents[agent_idx]
        positions = agent['positions']
        viable_positions = [position for position in positions if position['asset'] == asset and position['qty'] > 0]
        if len(viable_positions) == 0: 
            return {'exit_position': 'no viable positions'}
        #NOTE: sell sell['qty'] comes in negative, so we need to flip the sign and add the quantity flow to the sell['qty'] as we pull from enters 
        while sell['qty'] < 0:
            for position in viable_positions:
                enters = position['enters']
                if len(enters) == 0:
                    return {'exit_position': 'no enters'}
                for enter in enters:
                    normalised_qty = qty * -1
                    exit = {
                        'id': str(UUID()),
                        'agent': agent['name'],
                        'base': enter['base'],
                        'quote': enter['quote'],
                        'quote_flow': sell['quote_flow'],
                        'qty': normalised_qty,
                        'dt': sell['dt'],
                        'type': sell['type'],
                        'pnl': (sell['price']*normalised_qty)-(enter['price']*normalised_qty), 
                        'enter_id': enter['id'],
                        'enter_date': enter['dt']
                    }
                    if exit['pnl'] > 0 and (exit['quote'] == self.default_quote_currency['symbol']):
                        taxable_event = {"type": 'capital_gains', 'exit_id': exit['id'], 'enter_id':enter['id'], 'enter_date': enter['dt'], 'exit_date': exit['dt'], 'pnl': exit['pnl']}
                        agent['taxable_events'].append(taxable_event)
                        
                    if enter['qty'] >= normalised_qty:
                        position['qty'] += qty
                        enter['qty'] += qty
                        position['exits'].append(exit)
                        sell['qty'] = 0
                        return {'exit_position': 'success'}
                    else:
                        position['exits'].append(exit)
                        sell['qty'] += position['qty']
                        enter['qty'] += qty
                        position['qty'] = 0
        return {'exit_position': 'no position to exit'}                            

    async def update_assets(self, asset, amount, agent_idx) -> None:
        if asset in self.agents[agent_idx]['assets']:
            self.agents[agent_idx]['assets'][asset] += amount
        else: 
            self.agents[agent_idx]['assets'][asset] = amount        

    async def update_agents(self, transaction, accounting, position_id) -> None:
        for side in transaction:
            if len(self.agents) == 0:
                return {'update_agents': 'no agents'}
            agent_idx = await self.get_agent_index(side['agent'])
            if agent_idx is None:
                return {'update_agents': 'agent not found'}
            self.agents[agent_idx]['_transactions'].append(side)
            await self.update_assets(side['base'], side['qty'], agent_idx)
            await self.update_assets(side['quote'], side['quote_flow'], agent_idx)
            if side['type'] == 'buy':
                await self.enter_position(side, side['base'], side['qty'], agent_idx, position_id)
                await self.exit_position(side, side['quote'], side['quote_flow'], agent_idx)
            elif side['type'] == 'sell':
                await self.sort_positions(agent_idx, accounting)
                await self.exit_position(side, side['base'], side['qty'], agent_idx)
                await self.enter_position(side, side['quote'], side['quote_flow'], agent_idx, None)

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

    async def add_asset(self, agent, asset, amount, note=''):
        if type(agent) == int:
            agent_idx = agent
        else:
            agent_idx = await self.get_agent_index(agent)
        if agent_idx is not None:
            side = {'id': str(UUID()), 'agent':agent, 'quote_flow':0, 'price': 0, 'base': asset, 'quote': self.default_quote_currency['symbol'], 'qty': amount, 'fee':0, 'dt': self.datetime, 'type': note}
            await self.enter_position(side, asset, amount, agent_idx, str(UUID()))
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

    async def get_agents_positions(self, base=None, quote=None) -> list:
        """
        Returns a list of agents and their positions, optionally for a base quote pair
        """
        agent_positions = []
        for agent in self.agents:
            positions = []
            for position in agent['positions']:
                if base is None and quote is None:
                    positions.append(position)
                elif position['base'] == base and position['quote'] == quote:
                    positions.append(position)
                else:
                    continue
            agent_positions.append({'agent':agent['name'],'positions':positions})
        return agent_positions

    async def get_tickers(self) -> list:
        """
        Returns a list of tickers
        """
        tickers = []
        for book in self.books:
            tickers.append(book.base+book.quote)
        return tickers