import unittest
from datetime import datetime, timedelta
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.Clock import Clock

class ClockTests(unittest.TestCase):

    def test_tick(self):
        start_dt = datetime(2023, 1, 1)
        time_unit = 'minute'
        clock = Clock(start_dt, time_unit)

        # Perform multiple ticks and verify the updated datetime
        expected_dt = start_dt
        for _ in range(10):
            expected_dt += timedelta(minutes=1)
            self.assertEqual(clock.tick(), expected_dt)

    def test_tick_custom_time_unit(self):
        start_dt = datetime(2023, 1, 1)
        time_unit = 'hour'
        clock = Clock(start_dt, time_unit)

        # Perform multiple ticks and verify the updated datetime
        expected_dt = start_dt
        for _ in range(5):
            expected_dt += timedelta(hours=1)
            self.assertEqual(clock.tick(), expected_dt)

    def test_tick_default_parameters(self):
        clock = Clock()

        # Perform a single tick and verify the updated datetime
        expected_dt = datetime(1700, 1, 1) + timedelta(minutes=1)
        self.assertEqual(clock.tick(), expected_dt)

if __name__ == '__main__':
    unittest.main()
