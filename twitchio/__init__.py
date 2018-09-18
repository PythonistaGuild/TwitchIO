# -*- coding: utf-8 -*-

__title__ = 'twitchio'
__author__ = 'EvieePy'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017-2018 EvieePy'
__version__ = '0.0.1a'

import logging

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

from .websocket import WebsocketConnection