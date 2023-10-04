import sys
import os
import unittest
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from source.utils.logger import Logger

class LoggerTest(unittest.TestCase):
    def test_logger(self):
        logger = Logger('test_logger', level=0)
        logger.info('test')
        logger.debug('test')
        logger.error('test')
        
        # read the log and check if the message is there
        with open('logs/test_logger_info.log', 'r') as f:
            log = f.read()
            self.assertIn('test', log)
            f.close()

        logger.ch.close()
        logger.fh.close()

        logger.logger.removeHandler(logger.ch)
        logger.logger.removeHandler(logger.fh)
        logger.logger.removeFilter(logger.formatter)

        logger.logger = None

        os.remove('logs/test_logger_info.log')