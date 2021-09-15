# logger.py -
#   simple functions for logging
#

import sys
from ambvis.config import Config

cfg = Config()


def log(msg):
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()


def debug(msg):
    if cfg.get('debug'):
        sys.stderr.write(msg + '\n')
        sys.stderr.flush()
