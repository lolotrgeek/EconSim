import random, string, os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.DefiExchange import DefiExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from source.crypto.CryptoCurrency import CryptoCurrency
from source.utils._utils import dumps
from datetime import datetime, timedelta
from source.utils.logger import Null_Logger

class MockRequesterCrypto():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponderCrypto()

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)

class MockResponderCrypto():
    """
    Mocked run_exchange and run_company callback responder
    """
    def __init__(self, requests=None):
        self.time = datetime(2023, 1, 1)
        self.cryptos = {
            'USD': CryptoCurrency("USD", self.time, decimals=2),
            'BTC': CryptoCurrency("BTC", self.time, decimals=8),
            'ETH': CryptoCurrency("ETH", self.time, decimals=18),  
        }

    async def next(self):
        self.time = self.time + timedelta(days=1)
        self.exchange.datetime = self.time
        for crypto in self.cryptos:
            await self.cryptos[crypto].next(self.time)

    async def list_cryptos(self):
        # single line loop through all the cryptos, call to_dict() on each, and return as a list of dicts
        return list(map(lambda crypto: crypto.to_dict(), self.cryptos.values()))            
                
    async def callback(self, msg):
        if msg['topic'] == 'get_assets': return dumps(await self.list_cryptos())

        if 'chain' in msg:
            if msg['chain'] in self.cryptos:
                if msg('topic') == 'connect': return dumps(await self.cryptos[msg['chain']].to_dict())
            else: return f'unknown chain {msg["chain"]}'        
        if 'asset' in msg:
            if msg['asset'] in self.cryptos:
                if msg['topic'] == 'get_transactions': return dumps(await self.cryptos[msg['asset']].blockchain.get_transactions())
                if msg['topic'] == 'get_transaction': return dumps(await self.cryptos[msg['asset']].blockchain.get_transaction(msg['id']))
                elif msg['topic'] == 'add_transaction': return dumps((await self.cryptos[msg['asset']].blockchain.add_transaction(msg['asset'], msg['fee'], msg['amount'], msg['sender'], msg['recipient'])).to_dict())
                elif msg['topic'] == 'cancel_transaction': return dumps(await self.cryptos[msg['asset']].blockchain.cancel_transaction(msg['id']))
                elif msg['topic'] == 'get_mempool': return dumps(await self.cryptos[msg['asset']].blockchain.get_mempool())
                elif msg['topic'] == 'get_pending_transactions': return dumps(await self.cryptos[msg['asset']].blockchain.mempool.get_pending_transactions(to_dicts=True))
                elif msg['topic'] == 'get_confirmed_transactions': return dumps(await self.cryptos[msg['asset']].blockchain.mempool.get_confirmed_transactions(to_dicts=True))
                elif msg['topic'] == 'get_last_fee': return dumps(await self.cryptos[msg['asset']].get_last_fee())
                elif msg['topic'] == 'get_fees': return dumps(await self.cryptos[msg['asset']].get_fees(msg['num']))
            else: return f'unknown asset {msg["asset"]}'    
        
class MockRequesterDefiExchange():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self, exchange=None):
        self.responder = MockResponderDefiExchange(exchange=exchange)

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)
    
class MockResponderDefiExchange():
    def __init__(self, exchange=None) -> None:
        self.mock_requester = MockRequesterCrypto()
        self.requests = Requests(self.mock_requester)
        self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests) if exchange is None else exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
        self.exchange.logger =Null_Logger(debug_print=True)
        self.agent = None
        self.mock_order = None

    async def init(self):
        await self.exchange.create_asset("BTC", pairs = [{'asset': "USD" ,'market_qty':1000 ,'seed_price':150 ,'seed_bid':'.99', 'seed_ask':'1.01'}])
        self.agent = (await self.exchange.register_agent("buyer1", {"BTC":2, "USD": 100000}))['registered_agent']
        self.mock_order = await self.exchange.limit_buy("BTC", "USD", price=151, qty=1, fee='0.0001', creator=self.agent)        

    async def next(self):
        self.time = self.time + timedelta(days=1)
        self.exchange.datetime = self.time
        await self.exchange.next()

    async def callback(self, msg):
        if msg['topic'] == 'signature': return dumps(await self.exchange.signature_response(msg['agent_wallet'], msg['decision'], msg['txn']))
        elif msg['topic'] == 'create_asset': return dumps(await self.exchange.create_asset(msg['asset'], msg['decimals'] ))
        elif msg['topic'] == 'provide_liquidity': return dumps(await self.exchange.provide_liquidity(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['fee_level'], msg['high_range'], msg['low_range']))
        elif msg['topic'] == 'remove_liquidity': return dumps(await self.exchange.remove_liquidity(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['fee_level']))
        elif msg['topic'] == 'swap': return dumps(await self.exchange.swap(msg['agent_wallet'], msg['base'], msg['quote'], msg['amount'], msg['slippage']))
        elif msg['topic'] == 'get_fee_levels': return dumps(await self.exchange.get_fee_levels())
        elif msg['topic'] == 'get_pools': return dumps(await self.exchange.get_pools())
        elif msg['topic'] == 'get_pool': return dumps(await self.exchange.get_pool(msg['base'], msg['quote'], msg['fee_level']))
        elif msg['topic'] == 'get_pool_liquidity': return dumps(await self.exchange.get_pool_liquidity(msg['base'], msg['quote'], msg['fee_level']))
        elif msg['topic'] == 'get_assets': return dumps(await self.exchange.get_assets())
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})