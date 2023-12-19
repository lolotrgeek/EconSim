import unittest
from decimal import Decimal, getcontext
from datetime import datetime
import sys, os, random
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils.logger import Null_Logger
from source.utils._utils import prec
from source.exchange.DefiExchange import DefiExchange as Exchange
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests as Requests
from .MockRequesterDefi import MockRequesterDefiExchange as MockRequester

async def standard_asyncSetUp(self):
    self.mock_requester = MockRequester()
    self.requests = Requests(self.mock_requester)
    self.exchange = Exchange(datetime=datetime(2023, 1, 1), requester=self.requests)
    # self.exchange.logger = Null_Logger(debug_print=True)
    await self.exchange.list_asset("USD", 2)
    await self.exchange.list_asset("BTC")
    await self.exchange.next()
    return self.exchange

