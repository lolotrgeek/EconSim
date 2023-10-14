import sys
import os
import unittest
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.utils.logger import Logger

class LoggerTest(unittest.TestCase):
    def test_logger(self):
        logger = Logger('test_logger', level=3, debug_print=True)
        logger.info('info')
        logger.debug('debug')
        logger.error('error')
        
        # read the log and check if the message is there
        with open('logs/test_logger.log', 'r') as f:
            log = f.read()
            self.assertIn('info', log)
            self.assertIn('debug', log)
            self.assertIn('error', log)
            f.close()

        logger.ch.close()
        logger.fh.close()

        logger.logger.removeHandler(logger.ch)
        logger.logger.removeHandler(logger.fh)
        logger.logger.removeFilter(logger.formatter)

        logger.logger = None

        os.remove('logs/test_logger.log')