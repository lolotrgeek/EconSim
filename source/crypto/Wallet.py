import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils._utils import prec, generate_address, dumps
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests

class Wallet():
    def __init__(self, name, requester=None, crypto_requester=None):
        self.requester: DefiExchangeRequests = requester
        self.crypto_requester: CryptoCurrencyRequests = crypto_requester
        self.address = generate_address()
        self.name = name
        self.signature_requests = []
        self.chain: dict = {}
        self.assets = {}
        self.holdings = {}

    async def connect(self, chain:str):
        """
        Connect to a cryptocurrency chain
        
        "connecting" to a chain loads the rules of the chain into the wallet, the rules are defined in the CryptoCurrency class __init__ method

        Parameters
        
        chain: str - the symbol of the chain to connect to
        """
        self.chain = (await self.crypto_requester.connect(chain))
        if 'error' in self.chain:
            return {'msg': self.chain['error']}

    async def is_connected(self):
        return self.chain != None and self.chain['symbol'] != None and self.chain['decimals'] != None

    async def get_balance(self, asset):
        if asset not in self.assets:
            return 0
        return self.assets[asset]['amount']
    
    async def get_assets(self):
        return await self.requester.get_assets()
        
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

    async def update_holdings(self, txn):
        if txn['asset'] not in self.holdings:
            self.holdings[txn['asset']] = {'amount': 0}
        decimals = self.assets[txn['asset']]['decimals']

        if txn['sender'] == self.address:
            self.holdings[txn['asset']]['amount'] = prec(self.assets[txn['asset']]['amount'] - txn['amount'] - txn['fee'], decimals)

        if txn['recipient'] == self.address:
            self.holdings[txn['asset']]['amount'] = prec(self.assets[txn['asset']]['amount'] + txn['amount'], decimals)

    async def sign_txn(self, txn, decision=False):
        if (await self.check_txn(txn)) == False:
            msg = f'invalid transaction {txn}'
            decision = False

        if decision == True:
            await self.update_holdings(txn)
        
        await self.requester.send_signature(decision=decision, txn=txn)
    
    async def set_fee(self):
        # https://ethereum.stackexchange.com/questions/114743/estimate-transaction-fee-on-bsc
        # from cryptocurrency get the latest fee 
        # set max willing to pay
        # check that wallet has enough to pay fee
        if not (await self.is_connected()):
            return {'msg': 'wallet is not connected to a chain'}

        max_fee = prec(network_fee * 2, self.chain['decimals'])
        network_fee = prec((await self.crypto_requester.get_last_fee()), self.chain['decimals'])
        return network_fee