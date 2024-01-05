import sys, os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils._utils import prec, generate_address, get_minimum, convert_sci_to_str
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests

class Wallet():
    def __init__(self, name, requests=None, crypto_requests=None):
        self.crypto_requests: CryptoCurrencyRequests = crypto_requests
        self.address = generate_address()
        self.name = name
        self.chain: dict = {}
        self.assets = {}
        self.holdings = {}        
        self.signature_requests = []
        self.pending_transactions = {}
 
    async def connect(self, chain:str):
        """
        Connect to a cryptocurrency chain
        
        "connecting" to a chain loads the rules of the chain into the wallet, the rules are defined in the CryptoCurrency class __init__ method

        Parameters
        
        chain: str - the symbol of the chain to connect to
        """
        self.chain = (await self.crypto_requests.connect(chain))
        if 'error' in self.chain:
            return {'msg': self.chain['error']}

    async def _is_connected(self):
        return self.chain != None and 'symbol' in self.chain and 'decimals' in self.chain

    async def get_balance(self, asset=None):
        if asset == None or asset == 'None':
            return self.holdings
        if asset not in self.holdings:
            return {asset: 0}
        return {asset: self.holdings[asset]}
        
    async def _check_txn(self, txn):
        if txn['sender'] != self.address:
            return {'invalid': txn, 'msg': ('cannot sign transaction, sender address does not match wallet address')}
        if txn['asset'] not in self.holdings:
            return {'invalid': txn, 'msg': (f"Wallet does not have {txn['asset']}")}
        if self.holdings[txn['asset']] < txn['amount']:
            return {'invalid': txn, 'msg': (f"Wallet does not have enough {txn['asset']}")}
        
        decimals = self.chain['decimals']
        fee = prec(txn['fee'], decimals)
        amount = prec(txn['amount'], decimals)
        total = prec(fee + amount, decimals)
        if self.holdings[txn['asset']] < total:
            return {'invalid': txn, 'msg': (f"Wallet does not have enough {txn['asset']} to pay fee and amount")}

        for transfer in txn['transfers']:
            if transfer['from'] == self.address:
                if transfer['asset'] not in self.holdings:
                    return {'invalid': txn, 'msg': (f"Wallet does not have {transfer['asset']}")}
                if self.holdings[transfer['asset']] < prec(transfer['for'], transfer['decimals']):
                    return {'invalid': txn, 'msg': (f"Wallet does not have enough {transfer['asset']}")}

        return {'valid': txn, 'msg': 'valid transaction'}
    
    async def signature_request(self, txn):
        """
        Request a signature from this wallet for a transaction
        """
        self.signature_requests.insert(0,txn)
        return {'msg': 'request received'}

    async def _update_holdings(self, txn):
        """
        Update holdings if a transaction is accepted
        """
        if txn['asset'] not in self.holdings:
            self.holdings[txn['asset']] = 0        
        if txn['recipient'] == self.address:                
            self.holdings[txn['asset']] += prec(txn['amount'], self.chain['decimals'])
        if txn['sender'] == self.address:
            self.holdings[txn['asset']] -= prec(txn['amount']  + txn['fee'], self.chain['decimals'])

        for transfer in txn['transfers']:
            if transfer['asset'] not in self.holdings:
                self.holdings[transfer['asset']] = 0
            if transfer['to'] == self.address:
                self.holdings[transfer['asset']] += prec(transfer['for'], transfer['decimals'])  
            if transfer['from'] == self.address:
                self.holdings[transfer['asset']] -= prec(transfer['for'], transfer['decimals'])

    async def _revert_holdings(self, txn):
        """
        Revert holdings if a transaction is rejected or fails
        
        """
        if txn['recipient'] == self.address:
            self.holdings[txn['asset']] -= prec(txn['amount'] , self.chain['decimals'])
        if txn['sender'] == self.address:
            self.holdings[txn['asset']] += prec(txn['amount']+ txn['fee'], self.chain['decimals'])

        for transfer in txn['transfers']:
            if transfer['asset'] not in self.holdings:
                self.holdings[transfer['asset']] = 0
            if transfer['to'] == self.address:
                self.holdings[transfer['asset']] -= prec(transfer['for'], transfer['decimals'])  
            if transfer['from'] == self.address:
                self.holdings[transfer['asset']] += prec(transfer['for'], transfer['decimals'])

    async def sign_txn(self, txn, decision='reject'):
        """
        Sign a transaction that was requested by another agent
        """
        reason = 'reject transaction'
        checked_txn = await self._check_txn(txn)
        if 'invalid' in checked_txn:
            reason = 'invalid transaction'
            decision = 'reject'

        elif decision == 'approve':
            await self._update_holdings(txn)
            reason = 'approved transaction'
            pending_transaction = await self.crypto_requests.add_transaction(txn['asset'], txn['fee'], txn['amount'], txn['sender'], txn['recipient'], txn['id'], txn['transfers'])
            if 'error' in pending_transaction:
                decision = 'reject'
                reason = pending_transaction['error']
            self.pending_transactions[txn['id']] = pending_transaction
        return {'decision': decision, 'reason': reason, 'txn': pending_transaction}

    async def cancel_transaction(self, txn_id):
        """
        Cancel a transaction that was signed by this wallet, revert the holdings and remove the transaction from pending
        """
        if txn_id not in self.pending_transactions:
            return {'msg': f'wallet does not have a pending transaction with id {txn_id}'}
        
        cancel_request = await self.crypto_requests.cancel_transaction(self.chain['symbol'], txn_id)
        if 'error' in cancel_request:
            return cancel_request
        if 'id' not in cancel_request or cancel_request['id'] != txn_id:
            return {'msg': f'wallet does not have a pending transaction with id {txn_id}'}
        elif cancel_request['id'] == txn_id:
            await self._revert_holdings(cancel_request)
            self.pending_transactions.pop(txn_id)
            return {'msg': 'transaction cancelled'}
        
    async def transaction_confirmed(self, txn):
        """
        When a transaction has been confirmed that was signed by this wallet, update the holdings and remove the transaction from pending
        """
        if txn['id'] not in self.pending_transactions:
            return {'msg': f'wallet does not have a pending transaction with id {txn["id"]}'}
        
        self.pending_transactions.pop(txn['id'])
        return {'msg': 'transaction confirmed'}
    
    async def transaction_failed(self, txn):
        """
        When a transaction has failed or been cancelled that was signed by this wallet, revert the holdings and remove the transaction from pending
        """
        if txn['id'] not in self.pending_transactions:
            return {'msg': f'wallet does not have a pending transaction with id {txn["id"]}'}
        
        await self._revert_holdings(txn)
        self.pending_transactions.pop(txn['id'])
        return {'msg': 'transaction failed'}

    async def get_fee(self):
        if not (await self._is_connected()):
            return {'msg': 'wallet is not connected to a chain'}

        #TODO: set max fee willing to pay
        get_fee = await self.crypto_requests.get_last_fee(self.chain['symbol'])
        if not get_fee:
            return -1
        network_fee = prec(str(get_fee), self.chain['decimals'])
        return network_fee
        
    async def set_fee(self, fee_limit=-1):
        # https://ethereum.stackexchange.com/questions/114743/estimate-transaction-fee-on-bsc
        # from cryptocurrency get the latest fee 
        # set max willing to pay
        # check that wallet has enough to pay fee
        if not (await self._is_connected()):
            return {'msg': 'wallet is not connected to a chain'}
        
        #TODO: could use "get_fees" to create a sample of fees for txns that were confirmed and use the median
        network_fee = prec(str(await self.crypto_requests.get_last_fee(self.chain['symbol'])), self.chain['decimals'])

        if fee_limit == -1:
            fee_limit = network_fee + get_minimum(self.chain['decimals'])

        if fee_limit > 0 and fee_limit < network_fee:
            return {'msg': f'fee limit {fee_limit} is less than network fee {network_fee}'}
    

        return 
    
    async def approve_transaction(self, txn):
        fee = await self.get_fee()
        if fee < 0:
            self.logger.info(f'fee is negative: {fee}')
            return
        txn['fee'] = fee
        signed = await self.sign_txn(txn, decision='approve')
        return signed