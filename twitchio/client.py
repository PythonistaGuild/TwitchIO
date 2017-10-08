from twitchio.connection import *
import asyncio
import inspect

from twitchio.errors import *

import traceback
import sys
import os
import re
import math
import json
import configparser
import time
import subprocess
import functools
import sqlite3
import pathlib


class Client(BaseConnection):

    def __init__(self, nick: str, token: str, initial_channels: (list, tuple, callable), *,
                 host: str='irc.chat.twitch.tv', port: int=6667, loop=None, **attrs):
        modes = attrs.pop('modes', ("commands", "tags", "membership"))
        self._gather_channels = initial_channels
        super().__init__(loop, host, port, nick, token, modes)

    def run(self, pre_run=None):

        if not self.loop:
            self.loop = asyncio.get_event_loop()

        if callable(pre_run):
            ret = pre_run()
            if inspect.isawaitable(ret):
                self.loop.run_until_complete(ret)

        if callable(self._gather_channels):
            channels = self._gather_channels()
            if inspect.isawaitable(channels):
                channels = self.loop.run_until_complete(channels)
        else:
            channels = self._gather_channels

        task = self.loop.create_task(self.keep_alive(channels))

        def end_loop(fut):
            self.loop.stop()

        task.add_done_callback(end_loop)

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            #todo stuff
            print('Terminating TwitchIO Client...')
