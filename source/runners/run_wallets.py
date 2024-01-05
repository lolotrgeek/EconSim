import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
import traceback
from source.Messaging import Responder, Requester
from rich import print
import asyncio
from typing import Dict
from runner import Runner
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.crypto.Wallet import Wallet
from source.utils._utils import dumps
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class WalletRunner(Runner):
    def __init__(self):
        super().__init__()
        self.responder = Responder(self.channels.wallet_channel)
        self.crypto_requester = Requester(self.channels.crypto_channel)
        self.exchange_requester = Requester(self.channels.defi_channel)
        self.wallets: Dict[str, Wallet] = {}

    async def new_wallet(self, name):
        wallet = Wallet(name, DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests(self.crypto_requester))
        self.wallets[wallet.address] = wallet
        return wallet.address

    async def callback(self, msg):
        #TODO: may want to add a private key encryption layer here
        if msg['topic'] == 'new_wallet': return dumps(await self.new_wallet(msg['name']))
        elif 'address' in msg:
            if msg['address'] in self.wallets:
                if msg['topic'] == 'connect': return dumps(await self.wallets[msg['address']].connect(msg['chain']))
                elif msg['topic'] == 'sign_txn': return dumps(await self.wallets[msg['address']].sign_txn(msg['txn'], msg['decision']))
                elif msg['topic'] == 'request_signature': return dumps(await self.wallets[msg['address']].signature_request(msg['txn']))
                elif msg['topic'] == 'get_signature_requests': return dumps(self.wallets[msg['address']].signature_requests)
                elif msg['topic'] == 'get_balance': return dumps((await self.wallets[msg['address']].get_balance(msg['asset'])))
                elif msg['topic'] == 'transaction_confirmed': return dumps(await self.wallets[msg['address']].transaction_confirmed(msg['txn']))
                elif msg['topic'] == 'transaction_failed': return dumps(await self.wallets[msg['address']].transaction_failed(msg['txn']))
            else: return dumps({"error": f'unknown address {msg["address"]}'})
        else: return dumps({"error": f'unknown topic {msg["topic"]}'})

    async def run(self) -> None:
        try:
            await self.responder.connect()
            await self.crypto_requester.connect()
            await self.exchange_requester.connect()

            while True:
                msg = await self.responder.lazy_respond(self.callback)
                if msg == 'STOP':
                    break

        except Exception as e:
            print("[Trader Error] ", e)
            print(traceback.print_exc())
            return None
        except KeyboardInterrupt:
            print("attempting to close trader..." )
            return None

if __name__ == '__main__':
    try:
        runner = WalletRunner()
        asyncio.run(runner.run())
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        exit()