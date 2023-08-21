import unittest
import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from unittest.mock import MagicMock
from source.agents.Government import Government

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

class TestCollectTaxes(unittest.TestCase):
    def setUp(self):
        self.requests = AsyncMock()
        self.govnerment = Government(requester = self.requests)

    def test_collect_taxes_long_term(self):
        # Prepare test data
        agents = [
            {
                'name': 'Agent1',
                'taxable_events':  [
                    {'exit_date': '2022-06-01 00:00:00', 'enter_date': '2022-01-01 00:00:00', 'pnl': 500},  # Short-term gain
                    {'exit_date': '2023-06-01 00:00:00', 'enter_date': '2021-01-01 00:00:00', 'pnl': 1000},  # Long-term gain
                    {'exit_date': '2023-06-02 00:00:00', 'enter_date': '2021-01-02 00:00:00', 'pnl': -200}   # Loss (ignored)
                ]
            }
        ]

        # Mock the requests.get_agents() method to return the test data
        self.requests.get_agents.return_value = agents

        asyncio.run(self.govnerment.collect_taxes())

        # Assertions
        self.requests.get_agents.assert_called_once()
        self.requests.remove_cash.assert_called_once_with('Agent1', 50, 'taxes')

    def test_collect_taxes_short_term(self):
        # Prepare test data
        agents = [
            {
                'name': 'Agent2',
                'taxable_events': [
                    {'exit_date': '2022-06-01 00:00:00', 'enter_date': '2022-01-01 00:00:00', 'pnl': 500},  # Short-term gain
                    {'exit_date': '2023-06-01 00:00:00', 'enter_date': '2023-01-01 00:00:00', 'pnl': 1000},  # Long-term gain (ignored)
                    {'exit_date': '2023-06-02 00:00:00', 'enter_date': '2023-01-02 00:00:00', 'pnl': -200}   # Loss (ignored)
                ]
            }
        ]

        # Mock the requests.get_agents() method to return the test data
        self.requests.get_agents.return_value = agents

        # Run the method
        asyncio.run(self.govnerment.collect_taxes())

        # Assertions
        self.requests.get_agents.assert_called_once()
        self.requests.remove_cash.assert_called_once_with('Agent2', 150, 'taxes')

if __name__ == '__main__':
    unittest.main()
