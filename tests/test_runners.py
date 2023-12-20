import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from datetime import datetime
from source.runners.run_banks import BankRunner
from source.runners.run_companies import CompaniesRunner
from source.runners.run_crypto import CryptoRunner
from source.runners.run_crypto_exchange import CryptoExchangeRunner
from source.runners.run_defi_exchange import DefiExchangeRunner
from source.runners.run_exchange import ExchangeRunner
from source.runners.run_government import GovernmentRunner
from source.runners.run_stock_exchange import StockExchangeRunner
from source.runners.run_trader_defi import DefiTraderRunner
from source.runners.run_trader import TraderRunner

from .MockClock import get_time as mock_get_time
from .MockRequester import MockRequester, MockResponder, MockPusher
from .MockRequesterExchange import MockRequester as MockRequesterExchange
from .MockRequesterDefi import MockRequesterDefiExchange
from .MockRequesterCrypto import MockRequesterCrypto, MockRequesterCryptoExchange
from .MockRequesterStock import MockRequester as MockRequesterStock
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests

class TestRunners(unittest.IsolatedAsyncioTestCase):
    async def test_run_banks(self):
        runner = BankRunner()
        runner.pusher = MockPusher()
        runner.requester = MockRequester()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        self.assertEqual(runner.bank.current_date, datetime(1700,1,1,0,1))

    async def test_run_companies(self):
        runner = CompaniesRunner()
        runner.requester = MockRequesterExchange()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        self.assertEqual(runner.requester.connected, True)
        for company in runner.companies.values():
            self.assertEqual(company.currentdate, datetime(1700,1,1,0,1))

    async def test_run_crypto(self):
        runner = CryptoRunner()
        runner.requester = MockRequester()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        for currency in runner.currencies.values():
            self.assertEqual(currency.currentdate, datetime(1700,1,1,0,1))

    async def test_run_crypto_exchange(self):
        runner = CryptoExchangeRunner()
        runner.requester = MockRequesterCrypto()
        runner.responder = MockResponder()
        runner.crypto_currency_requests = CryptoCurrencyRequests(runner.requester)
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        self.assertEqual(runner.exchange.datetime, datetime(1700,1,1,0,1))

    async def test_run_defi_exchange(self):
        runner = DefiExchangeRunner()
        runner.crypto_requester = MockRequesterCrypto()
        runner.wallet_requester = MockRequester()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        self.assertEqual(runner.exchange.dt, datetime(1700,1,1,0,1))

    async def test_run_exchange(self):
        runner = ExchangeRunner()
        runner.requester = MockRequester()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        self.assertEqual(runner.exchange.datetime, datetime(1700,1,1,0,1))

    async def test_run_government(self):
        runner = GovernmentRunner()
        runner.requester = MockRequesterCrypto()
        runner.pusher = MockPusher()
        class MockGovernment():
            def __init__(self):
                self.requests = None
                self.current_date = None
            async def register(self, logger=False):
                return True
            async def next(self):
                return False
            
        async def mock_set_government():
            runner.government = MockGovernment()

        runner.set_government = mock_set_government
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.requester.connected, True)
        self.assertEqual(runner.government.current_date, datetime(1700,1,1,0,1))

    async def test_run_stock_exchange(self):
        runner = StockExchangeRunner()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.responder.connected, True)
        self.assertEqual(runner.exchange.datetime, datetime(1700,1,1,0,1))

    async def test_run_trader_defi(self):
        runner = DefiTraderRunner()
        runner.requester = MockRequesterCrypto()
        runner.exchange_requester = MockRequesterDefiExchange()
        runner.responder = MockResponder()
        runner.get_time = mock_get_time
        await runner.run()
        self.assertEqual(runner.requester.connected, True)
        self.assertEqual(runner.exchange_requester.connected, True)
        self.assertEqual(runner.responder.connected, True)
        for wallet, trader in runner.traders.items():
            self.assertEqual(trader.current_date, datetime(1700,1,1,0,1))

    async def test_run_trader(self):
        runner = TraderRunner()
        runner.exchange_requester = MockRequesterCryptoExchange()
        runner.crypto_requester = MockRequesterCrypto()
        class MockTrader():
            def __init__(self):
                self.requests = None
            async def register(self, logger=False):
                return True
            async def next(self):
                return False
        
        async def mock_pick_trader():
            runner.trader = MockTrader()

        runner.get_time = mock_get_time
        runner.pick_trader = mock_pick_trader
        await runner.run()
        self.assertEqual(runner.exchange_requester.connected, True)
        self.assertEqual(runner.crypto_requester.connected, True)