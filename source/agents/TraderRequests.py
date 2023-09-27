import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.exchange.ExchangeRequests import ExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests

class TraderRequests(ExchangeRequests, CryptoCurrencyRequests):
    def __init__(self, exchange_requester, crypto_requester):
        ExchangeRequests.__init__(self=self, requester=exchange_requester)
        CryptoCurrencyRequests.__init__(self=self, requester=crypto_requester)
        