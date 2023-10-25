import unittest
import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from datetime import datetime
from unittest.mock import MagicMock
from source.agents.Government import Government
from source.exchange.ExchangeRequests import ExchangeRequests
from source.company.PublicCompanyRequests import PublicCompanyRequests
from .MockRequester import MockRequester
from decimal import Decimal

from .MockTaxes import mock_taxes

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

class TestCollectTaxes(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester()
        self.requests = (ExchangeRequests(self.mock_requester))
        self.govnerment = Government(requester = self.requests)
        self.govnerment.current_date = self.mock_requester.responder.time
        await self.mock_requester.responder.init()
        self.mock_requester.responder.exchange.agents[1]['taxable_events'] = [
            {'exit_date': '2023-01-01 00:00:00', 'enter_date': '2023-01-01 00:00:00', 'pnl': Decimal('500')},  # Short-term gain
            {'exit_date': '2023-01-01 00:00:00', 'enter_date': '2021-01-01 00:00:00', 'pnl': Decimal('85000')},  # Long-term gain
            {'exit_date': '2023-01-01 00:00:00', 'enter_date': '2023-01-01 00:00:00', 'pnl': Decimal('-200')},   # Loss (ignored)
            {'exit_date': '2022-01-01 00:00:00', 'enter_date': '2022-01-01 00:00:00', 'pnl': Decimal('300')} #  wrong year (ignored)
        ] 

    async def test_collect_taxes(self):
        taxable_events = await self.mock_requester.responder.exchange.get_taxable_events()
        await self.govnerment.collect_taxes()
        print(self.govnerment.tax_records[0])

        self.assertEqual(self.govnerment.tax_records[0]['long_term'], Decimal('247.5'))
        self.assertEqual(self.govnerment.tax_records[0]['short_term'], 50)
        self.assertEqual(self.govnerment.tax_records[0]['local'], Decimal('4346.16'))        
        self.assertEqual(self.govnerment.taxes_last_collected['amount'], Decimal('4643.66'))

    async def test_collect_many_tax_events(self):
        self.mock_requester.responder.exchange.agents[1]['taxable_events'] = mock_taxes        
        await self.govnerment.collect_taxes()
        self.assertEqual(self.govnerment.tax_records[0]['long_term'], 0)
        self.assertEqual(self.govnerment.tax_records[0]['short_term'], Decimal('227.16'))
        self.assertEqual(self.govnerment.tax_records[0]['local'], Decimal('38.33'))

    async def test_archive_tax_records(self):
        pre_archive_records = self.govnerment.tax_records
        await self.govnerment.collect_taxes()
        self.govnerment.current_date = datetime(2024, 1, 1)
        await self.govnerment.archive_tax_records()
        self.assertEqual(self.govnerment.tax_records_archive.get('2023'), pre_archive_records)
        os.remove('archive/tax_records.bak')
        os.remove('archive/tax_records.dat')
        os.remove('archive/tax_records.dir')

if __name__ == '__main__':
    asyncio.run(unittest.main())
