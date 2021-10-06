# logger.py -
#   simple functions for logging
#

import sys

from cherrypy import log as cherrypy_log

from ambvis.config import cfg


def log(msg):
    cherrypy_log(msg)


def debug(msg):
    if cfg.get('debug'):
        cherrypy_log(msg)
