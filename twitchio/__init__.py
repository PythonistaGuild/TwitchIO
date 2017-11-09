# -*- coding: utf-8 -*-

"""
TwitchIO
~~~~~~~~~~~~~~~~~~~
A Twitch IRC Bot and API Wrapper.
:copyright: (c) 2017 MysterialPy
:license: MIT, see LICENSE for more details.
"""

__title__ = 'twitchio'
__author__ = 'MysterialPy'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 MysterialPy'
__version__ = '0.0.1a'

from .abcs import Messageable
from .client import Client
from .dataclasses import Context, Message, User, Channel
from .errors import *
