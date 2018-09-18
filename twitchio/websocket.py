# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2018 EvieePy

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import asyncio
import logging
import re
import websockets
from typing import Union

from .backoff import ExponentialBackoff
from .errors import WSConnectionFailure

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class WebsocketConnection:

    def __init__(self, *, token: str, loop: asyncio.BaseEventLoop=None, **attrs):
        self.loop = loop or asyncio.get_event_loop()

        self._token = token
        self._host = 'wss://irc-ws.chat.twitch.tv:443'
        self._websocket = None
        self._connecting = asyncio.Event()
        self._last_exec = None

        self.initial_channels = attrs.get('initial_channels')
        self.nick = attrs.get('nick')

        self.regex = {
            "data": re.compile(
                r"^(?:@(?P<tags>\S+)\s)?:(?P<data>\S+)(?:\s)"
                r"(?P<action>[A-Z]+)(?:\s#)(?P<channel>\S+)"
                r"(?:\s(?::)?(?P<content>.+))?"),
            "ping": re.compile("PING (?P<content>.+)"),
            "author": re.compile(
                "(?P<author>[a-zA-Z0-9_]+)!(?P=author)"
                "@(?P=author).tmi.twitch.tv"),
            "mode": re.compile("(?P<mode>[\+\-])o (?P<user>.+)"),
            "host": re.compile(
                "(?P<channel>[a-zA-Z0-9_]+) "
                "(?P<count>[0-9\-]+)"),
            'code': re.compile(r":tmi\.twitch\.tv\s(?P<code>[0-9]{3}).*?"), }

        self._groups = ('action', 'data', 'content', 'channel', 'author')

    @property
    def is_connected(self):
        return self._websocket is not None and self._websocket.open

    async def _connect(self):
        self._connecting.clear()

        try:
            self._websocket = await websockets.connect(self._host, timeout=30)
        except Exception as e:
            self._last_exec = e
            log.error('Websocket connection failed | %s', e)
            return

        if self.is_connected:
            # Make sure we are 100% connected
            log.debug('Sending authentication sequence payload to Twitch')
            await self.auth_seq()

        self._connecting.set()

    async def auth_seq(self, channels: Union[list, tuple]=None):
        """|coro|

        Automated Authentication process.

        Attempts to authenticate on the Twitch servers with the provided
        nickname and IRC Token(pass).

        On successful authentication, an attempt to join the provided channels is made.

        Parameters
        ------------
        channels: Union[list, tuple]
            A list or tuple of channels to attempt joining.
        """
        if not self.is_connected:
            return

        await self._websocket.send(f'PASS {self._token}\r\n')
        await self._websocket.send(f'NICK {self.nick}\r\n')

        if not channels and not self.initial_channels:
            return

        channels = channels or self.initial_channels

        await self.join_channels(channels)

    async def join_channels(self, channels: (list, tuple)):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        channels: list or tuple
            A list of channels to attempt joining.
        """
        for entry in channels:
            channel = re.sub('[#\s]', '', entry)
            self._websocket.send(f'JOIN #{channel}\r\n')

    async def _listen(self):
        backoff = ExponentialBackoff()

        await self._connecting.wait()

        if not self.is_connected and self._last_exec:
            raise WSConnectionFailure(f'Websocket connection failure:\n\n{self._last_exec}')

        while True:
            try:
                data = await self._websocket.recv()
            except websockets.ConnectionClosed:
                retry = backoff.delay()
                log.info('Websocket closed: Retrying connection in %s seconds...', retry)

                await self._connect()
                await asyncio.sleep(retry)
                continue

            self.loop.create_task(self.event_raw_data(data))

            try:
                await self.process_data(data)
            except Exception as e:
                print(e)
                # TODO
                pass

    async def process_data(self, data):
        print(data)

        try:
            code = int(self.regex['code'].match(data).group('code'))
        except AttributeError:
            code = None

        if code == 376:
            await self.event_ready()
            log.info('Successfully logged onto Twitch WS | %s', self.nick)

        elif data == ':tmi.twitch.tv NOTICE * :Login authentication failed':
            print('Fail')
            # todo Disconnection/Reconnection Logic.
            return

        return print('RETURN PROCESS EVENTS')

    async def event_raw_data(self, data):
        pass

    async def event_ready(self):
        pass

    def run(self):
        # Initial connection task...
        self.loop.create_task(self._connect())

        # Blocking event loop...
        try:
            self.loop.run_until_complete(self._listen())
        except KeyboardInterrupt:
            self.teardown()

    def teardown(self):
        # TODO
        pass
