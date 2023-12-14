import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils._utils import prec, generate_address, dumps
from source.exchange.DefiExchangeRequests import DefiExchangeRequests

class Wallet():
    def __init__(self, name, requester=None):
        self.requester: DefiExchangeRequests = requester
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
    
    async def signature_request(self, txn):
        self.signature_requests.insert(0,txn)
        return {'msg': 'request received'}

    async def sign_txn(self, txn, decision=False):
        if (await self.check_txn(txn)) == False:
            msg = f'invalid transaction {txn}'
            decision = False
        await self.requester.send_signature(decision=decision, txn=txn)
    
    async def set_fee(self, asset):
        # https://ethereum.stackexchange.com/questions/114743/estimate-transaction-fee-on-bsc
        # from cryptocurrency get the latest fee 
        # set max willing to pay
        # check that wallet has enough to pay fee

        return self.assets[asset]['fee']