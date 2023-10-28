import logging 
from rich import print
from datetime import datetime

class Logger():
    def __init__(self, name, level=logging.INFO, debug_print=False, mode='w'):
        """
        Create a logger object with a name and a level
        args:
            name: name of the logger
            level: level of the logger (default: logging.INFO - `20`), possible values: ERROR - `40`, WARNING - `30`, INFO - `20`, DEBUG - `10`, NOTSET - `0`
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        if debug_print:
            self.debug_print = True
            self.ch = logging.StreamHandler()
            self.ch.setLevel(level)
            self.ch.setFormatter(self.formatter)
            self.logger.addHandler(self.ch)
        self.fh = logging.FileHandler('logs/' + name + '.log', mode=mode)
        self.fh.setLevel(level)
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)
        self.logger.info("INITIALIZED --------------------------------------------------------------------------------------------------")
        
    def debug(self, message, *args):
        self.logger.debug(self._format_message(message, *args))

    def info(self, message, *args):
        self.logger.info(self._format_message(message, *args))

    def warning(self, message, *args):
        self.logger.warning(self._format_message(message, *args))

    def error(self, message, *args):
        self.logger.error(self._format_message(message, *args))

    def _format_message(self, message, *args):
        if args:
            message += ' ' + ' '.join(str(arg) for arg in args)
        return message
    
    def setLevel(self, level):
        self.logger.setLevel(level)
        if self.debug_print:
            self.ch.setLevel(level)
        self.fh.setLevel(level)

    def clear_log(self):
        with open('logs/' + self.name + '.log', 'w'):
            pass
    
class Null_Logger():
    def __init__(self, debug_print=False):
        self.print = debug_print

    def debug(self, message, *args):
        if self.print: print(message, *args)
        else: pass

    def info(self, message, *args):
        if self.print: print(message, *args)
        else: pass

    def warning(self, message, *args):
        if self.print: print(message, *args)
        else: pass

    def error(self, message, *args):
        if self.print: print(message, *args)
        else: pass