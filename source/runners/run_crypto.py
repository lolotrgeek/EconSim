import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from .runner import Runner
from source.crypto.CryptoCurrency import CryptoCurrency
from source.Messaging import Responder, Requester, Subscriber
import asyncio
from rich import print
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from source.utils._utils import dumps, string_to_time
from source.Channels import Channels
from random import random

class CryptoRunner(Runner):
    def __init__(self):
        super().__init__()
        self.channels = Channels()
        self.responder = Responder(self.channels.crypto_channel)
        self.requester = Requester(self.channels.crypto_exchange_channel)        
        self.currencies = {}
        self.time = datetime.now()

    async def generate_cryptos(self, time):
        # create the default currency chain
        fiat = {
            "USD": CryptoCurrency("USD", time, decimals=2)
        }
        cryptos = {
            "ETH": CryptoCurrency("ETH", time, decimals=18),
            "BTC": CryptoCurrency("BTC", time, decimals=8),
            "LTC": CryptoCurrency("LTC", time, decimals=8),
        }
        defi = {
            "BNB": CryptoCurrency("BNB", time, decimals=18),
        }
        for crypto in cryptos:
            await cryptos[crypto].supply(1_000_000_000)

        self.currencies = {**fiat, **cryptos, **defi}

    async def list_cryptos(self):
        # single line loop through all the cryptos, call to_dict() on each, and return as a list of dicts
        return list(map(lambda crypto: crypto.to_dict(), self.currencies.values()))

    async def run_crypto(self) -> None:
        try:
            await self.responder.connect()
            await self.requester.connect()

            time = await self.get_time()
            self.cryptos = await self.generate_cryptos(time)

            async def callback(msg):
                if msg['topic'] == 'get_assets': return dumps(await self.list_cryptos())

                if 'chain' in msg:
                    if msg['chain'] in self.currencies:
                        if msg('topic') == 'connect': return dumps(await self.currencies[msg['chain']].to_dict())
                    else: return f'unknown chain {msg["chain"]}'

                if 'asset' in msg:
                    if msg['asset'] in self.currencies:
                        if msg['topic'] == 'connect': return dumps(await self.currencies[msg['asset']].to_dict())
                        elif msg['topic'] == 'get_transactions': return dumps(await self.currencies[msg['asset']].blockchain.get_transactions())
                        elif msg['topic'] == 'get_transaction': return dumps(await self.currencies[msg['asset']].blockchain.get_transaction(msg['id']))
                        elif msg['topic'] == 'add_transaction': return dumps((await self.currencies[msg['asset']].blockchain.add_transaction(msg['asset'], msg['fee'], msg['amount'], msg['sender'], msg['recipient'])).to_dict())
                        elif msg['topic'] == 'cancel_transaction': return dumps(await self.currencies[msg['asset']].blockchain.cancel_transaction(msg['id']))
                        elif msg['topic'] == 'get_mempool': return dumps(await self.currencies[msg['asset']].blockchain.get_mempool())
                        elif msg['topic'] == 'get_pending_transactions': return dumps(await self.currencies[msg['asset']].blockchain.mempool.get_pending_transactions(to_dicts=True))
                        elif msg['topic'] == 'get_confirmed_transactions': return dumps(await self.currencies[msg['asset']].blockchain.mempool.get_confirmed_transactions(to_dicts=True))
                        elif msg['topic'] == 'get_last_fee': return dumps(await self.currencies[msg['asset']].get_last_fee())
                        elif msg['topic'] == 'get_fees': return dumps(await self.currencies[msg['asset']].get_fees(msg['num']))

                    else: return f'unknown asset {msg["asset"]}'    
                else: return f'unknown topic {msg["topic"]}'

            # for crypto in cryptos:
            #     print("issuing coins", crypto)
            #     result = await cryptos[crypto].issue_coins([{'asset': cryptos[crypto].symbol ,'market_qty':1000 ,'seed_price':100 ,'seed_bid':.99, 'seed_ask':1.01}], 1_000_000_000)
            #     print(result)

            while True:
                time = await self.get_time()
                for crypto in self.currencies:
                    await self.currencies[crypto].next(time)
                msg = await self.responder.lazy_respond(callback)
                if msg == None:
                    continue

        except Exception as e:
            print(e)

if __name__ == '__main__':
    runner = CryptoRunner()
    asyncio.run(runner.run_crypto())
