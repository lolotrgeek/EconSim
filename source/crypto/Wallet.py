import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils._utils import prec, generate_address, dumps
from source.Messaging import Responder, Requester
from source.exchange.CryptoExchangeDeFiRequests import CryptoExchangeDefiRequests
from Channels import Channels

class Wallet():
    def __init__(self, name, requester=None):
        channels = Channels()
        self.exchange_listener = Responder(channels.wallet_channel)
        self.requester = Requester(channels.defi_channel)
        self.exchange_messenger = CryptoExchangeDefiRequests(self.requester)
        self.address = generate_address()
        self.name = name
        self.signature_requests = []
        self.assets = {}

    async def get_balance(self, asset):
        if asset not in self.assets:
            return 0
        return self.assets[asset]['amount']

    async def check_txn(self, txn):
        if txn['sender'] != self.address:
            return {'invalid': txn, 'msg': ('cannot sign transaction, sender address does not match wallet address')}
        if txn['asset'] not in self.assets:
            return {'invalid': txn, 'msg': (f"Wallet does not have {txn['asset']}")}
        if self.assets[txn['asset']] < txn['amount']:
            return {'invalid': txn, 'msg': (f"Wallet does not have enough {txn['asset']}")}
        
        decimals = self.assets[txn['asset']]['decimals']
        fee = prec(txn['fee'], decimals)
        amount = prec(txn['amount'], decimals)
        total = prec(fee + amount, decimals)

        if self.assets[txn['asset']]['amount'] < total:
            return {'invalid': txn, 'msg': (f"Wallet does not have enough {txn['asset']} to pay fee and amount")}
        return {'valid': txn, 'msg': 'valid transaction'}
    
    async def sign_txn(self, txn, decision=False):
        if (await self.check_txn(txn)) == False:
            msg = f'invalid transaction {txn}'
            decision = False
        await self.exchange_messenger.send_signature(decision=decision, txn=txn)
        
    async def callback(self, msg) -> str:
        if msg['topic'] == 'request_signature':
            #TODO: need to handle routing to the correct wallet
            if msg['wallet'] != self.address: return dumps({'error': 'wrong address'}) 
            self.signature_requests.append(msg['txn'])
            return dumps({'msg': 'request received'}) 
            # option 1 - forward request with a requester to the agent
            # option 2 - have agent subscribe to wallet channel and respond to requests
            # option 3 - have agent directly holding wallet object, and have agent call wallet.sign_txn(txn) <-- trying this first
        elif msg['topic'] == 'get_balance': return dumps((await self.get_balance(msg['asset'])))
        else: return dumps({"warning":  f'unknown topic {msg["topic"]}'})
        

        