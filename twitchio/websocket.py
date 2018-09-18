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
import aiohttp
import asyncio
import logging
import re
import traceback
import websockets
from typing import Union

from .backoff import ExponentialBackoff
from .dataclasses import *
from .errors import WSConnectionFailure, AuthenticationError
from .http import HttpSession

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class WebsocketConnection:

    def __init__(self, *, token: str, loop: asyncio.BaseEventLoop=None, **attrs):
        self.loop = loop or asyncio.get_event_loop()

        self._token = token
        self._api_token = attrs.get('api_token')
        self._host = 'wss://irc-ws.chat.twitch.tv:443'
        self._websocket = None
        self._last_exec = None

        self._initial_channels = attrs.get('initial_channels')
        self.nick = attrs.get('nick')

        self.modes = attrs.pop('modes', ("commands", "tags", "membership"))
        self._channel_cache = set()
        self._mod_token = 0
        self._channel_token = 0
        self._rate_status = None

        self.is_ready = asyncio.Event()

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
        self._http = HttpSession(session=aiohttp.ClientSession(loop=self.loop))

    async def _update_limit(self):

        while True:
            if self._mod_token == len(self._channel_cache):
                self._rate_status = 1
            else:
                self._rate_status = 0

            await asyncio.sleep(60)

    async def _token_update(self, status):
        if '+o' in status:
            self._mod_token += 1
        else:
            if self._mod_token <= 0:
                return
            self._mod_token -= 1

        if self._mod_token == len(self._channel_cache):
            self._rate_status = 1
        else:
            self._rate_status = 0

    @property
    def is_connected(self):
        return self._websocket is not None and self._websocket.open

    async def _connect(self):
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

    async def wait_until_ready(self):
        await self.is_ready.wait()

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

        if not channels and not self._initial_channels:
            return

        channels = channels or self._initial_channels

        await self.join_channels(channels)

    async def send_nick(self):
        """|coro|

        Sends a NICK request to the Twitch IRC Endpoint.

        This should only be used if :func:`auth_seq` was not used.
        """
        await self._websocket.send(f"NICK {self.nick}\r\n")

    async def send_privmsg(self, channel, content):
        """|coro|

        Sends a PRIVMSG to the Twitch IRC Endpoint.

        This should only be used in rare circumstances where a :class:`twitchio.abcs.Messageable` is not available.
        """
        content = content.replace("\n", " ")
        await self._websocket.send(f"PRIVMSG #{channel} :{content}\r\n")

    async def join_channels(self, channels: (list, tuple)):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        channels: list or tuple
            A list of channels to attempt joining.
        """
        for entry in channels:
            channel = re.sub('[#\s]', '', entry).lower()
            await self._websocket.send(f'JOIN #{channel}\r\n')

    async def _listen(self):
        backoff = ExponentialBackoff()

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
            except AuthenticationError:
                raise
            except Exception as e:
                await self.event_error(data, e)

    async def process_ping(self, resp):
            await self._websocket.send(f"PONG {resp}\r\n")

    async def process_data(self, data):
        data = data.strip()

        try:
            code = int(self.regex['code'].match(data).group('code'))
        except AttributeError:
            code = None

        if code == 376 or code == 1:
            print(code)
            await self.event_ready()
            self.is_ready.set()
            log.info('Successfully logged onto Twitch WS | %s', self.nick)
        elif data == ':tmi.twitch.tv NOTICE * :Login authentication failed':
            log.warning('Authentication failed | %s', self._token)
            raise AuthenticationError('Websocket Authentication Failure... Check your token and nick.')

        _groupsdict = {}

        if data.startswith("PING"):
            match = self.regex["ping"]
        else:
            match = self.regex["data"]

        result = match.match(data)

        try:
            tags = result.group("tags")

            tagdict = {}
            for tag in str(tags).split(";"):
                t = tag.split("=")
                if t[1].isnumeric():
                    t[1] = int(t[1])
                tagdict[t[0]] = t[1]
            tags = tagdict
        except (AttributeError, IndexError, KeyError):
            tags = None

        for group in self._groups:
            try:
                res = result.group(group)
                _groupsdict[group] = res
            except (AttributeError, KeyError, IndexError):
                pass

        await self.process_actions(data, _groupsdict, tags)

    async def process_actions(self, raw, groups, tags=None):
        # todo add remaining actions, docs

        action = groups.pop('action', 'PING')
        data = groups.pop('data', None)
        content = groups.pop('content', None)
        channel = groups.pop('channel', None)

        try:
            author = self.regex["author"].match(data).group("author")
        except Exception:
            author = None

        if channel:
            channel = Channel(name=channel, ws=self._websocket, http=self._http)

        try:
            user = User(author=author, channel=channel, tags=tags, ws=self._websocket)
        except (TypeError, KeyError):
            user = None

        try:
            message = Message(author=user, content=content, channel=channel, raw_data=data, tags=tags)
        except (TypeError, KeyError) as e:
            message = None

        if action == 'RECONNECT':
            # TODO Disconnection/Reconnection Logic.
            return

        elif action == 'JOIN':
            if author == self.nick:
                self._channel_cache.add(channel.name)
                self._channel_token += 1

            await self.event_join(user)

        elif action == 'PART':
            if author == self.nick:
                self._channel_cache.remove(channel.name)
                self._channel_token -= 1

            await self.event_part(user)

        elif action == 'PING':
            await self.process_ping(content)

        elif action == 'PRIVMSG':
            await self.event_message(message)

            await self.process_commands(message, channel, user)

        elif action == 'USERSTATE':
            await self.event_userstate(user)

        elif action == 'MODE':
            mdata = re.match(r':jtv MODE #(?P<channel>.+?[a-z0-9])\s(?P<status>[\+\-]o)\s(?P<user>.*[a-z0-9])', raw)
            mstatus = mdata.group('status')

            user = User(author=mdata.group('user'), channel=channel, tags=tags, ws=self._websocket)

            if user._name.lower() == self.nick.lower():
                await self._token_update(mstatus)

            await self.event_mode(channel, user, mstatus)

    async def process_commands(self, message, channel, user):
        pass

    async def event_raw_data(self, data):
        """|coro|
        Event called with the raw data received by Twitch.

        Parameters
        ------------
        data: str
            The raw data received from Twitch.
        """
        pass

    async def event_ready(self):
        """|coro|
        Event called when the Bot has logged in and is ready.
        """
        pass

    async def event_error(self, data, error: Exception):
        """|coro|
        Event called when an error occurs processing data.

        Parameters
        ------------
        data: str
            The raw data received from Twitch.
        error: Exception
            The exception raised.
        """
        traceback.print_exc()

    async def event_message(self, message):
        """|coro|

        Event called when a PRIVMSG is received from Twitch.

        Parameters
        ------------
        message: :class:`.Message`
            Message object containing relevant information.
        """
        pass

    async def event_join(self, user):
        """|coro|

        Event called when a JOIN is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the JOIN.
        """
        pass

    async def event_part(self, user):
        """|coro|

        Event called when a PART is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the PART.
        """
        pass

    async def event_userstate(self, user):
        """|coro|

        Event called when a USERSTATE is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the USERSTATE.
        """
        pass

    async def event_mode(self, channel, user, status):
        """|coro|

        Event called when a MODE is received from Twitch.

        Parameters
        ------------
        channel: :class:`.Channel`
            Channel object relevant to the MODE event.
        user: :class:`.User`
            User object containing relevant information to the MODE.
        status: str
            The JTV status received by Twitch. Could be either o+ or o-.
            Indicates a moderation promotion/demotion to the :class:`.User`
        """
        pass


