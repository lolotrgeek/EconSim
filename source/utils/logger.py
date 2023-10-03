import logging 

class Logger():
    def __init__(self, name, level=logging.ERROR):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.ch = logging.StreamHandler()
        self.ch.setLevel(level)
        self.ch.setFormatter(self.formatter)
        self.logger.addHandler(self.ch)
        self.fh = logging.FileHandler('logs/' + name + '_info.log')
        self.fh.setLevel(logging.INFO)
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)
        
    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def error(self, message):
        self.logger.error(message)