import logging
import sys

class Logger:
    def __init__(self, name, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        self.logger.addHandler(stdout_handler)
        self.logger.propagate = False

    def __getattr__(self, item):
        return getattr(self.logger, item)