import os, sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.DefiExchange import DefiExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from .MockRequesterCrypto import MockRequesterCrypto as MockRequesterCrypto
from source.utils._utils import dumps
from datetime import datetime, timedelta
from source.utils.logger import Null_Logger

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
    def __init__(self, exchange=None, wallet_requester=None, crypto_requester=None) -> None:
        self.crypto_requester = MockRequesterCrypto() if crypto_requester is None else crypto_requester
        self.exchange = Exchange(datetime=datetime(2023, 1, 1),crypto_requester=self.crypto_requester, wallet_requester=wallet_requester ) if exchange is None else exchange(datetime=datetime(2023, 1, 1), crypto_requester=self.crypto_requester, wallet_requester=wallet_requester )
        self.exchange.logger =Null_Logger(debug_print=True)
        self.agent = None
        self.mock_order = None

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