# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2018 TwitchIO

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
import json
import logging
import random
import re
import sys
import traceback
from typing import Union

import async_timeout
import websockets

from .backoff import ExponentialBackoff
from .dataclasses import *
from .errors import WSConnectionFailure, AuthenticationError, ClientError


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class PubSubPool:
    POOL_MAX = 10

    def __init__(self, loop, base):
        self.loop = loop
        self.base = base
        self.connections = {}

        for x in range(1, 11):
            self.connections[x] = PubSub(loop=self.loop, pool=self, node=x)

    async def delegate(self, *topics):
        for x in self.connections.values():
            if len(x._topics) == 50:
                continue
            elif len(x._topics) + len(topics) > 50:
                continue

            if x._websocket:
                return x

            await x.connect()

            if x._websocket.open:
                return x

            raise WSConnectionFailure('Unable to delegate WebSocket. Please try again.')
        raise ClientError('Maximum PubSub connections established.')


class WebsocketConnection:

    def __init__(self, bot, *, loop: asyncio.BaseEventLoop=None, **attrs):
        self._bot = bot
        self.loop = loop or asyncio.get_event_loop()

        self._token = attrs.get('irc_token')
        self._api_token = attrs.get('api_token')
        self.client_id = attrs.get('client_id')
        self._host = 'wss://irc-ws.chat.twitch.tv:443'
        self._websocket = None
        self._last_exec = None

        self._initial_channels = attrs.get('initial_channels')
        self.nick = attrs.get('nick')
        self.extra_listeners = {}

        self.modes = attrs.pop('modes', ("commands", "tags", "membership"))
        self._channel_cache = {}
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
            'code': re.compile(r":tmi\.twitch\.tv\s(?P<code>[0-9]{3}).*?"),
            'badges': re.compile(r"@badges=(?P<moderator>[^;]*);"
                                 r"color=(?P<color>[^;]*);"
                                 r"display-name=(?P<name>[^;]*);"
                                 r"emote-sets=(?P<emotes>[^;]*);"
                                 r"mod=(?P<mod>[^;]*);"
                                 r"subscriber=(?P<subscriber>[^;]*);"
                                 r"user-type=(?P<type>[^\s]+)\s:tmi.twitch.tv\s(?P<action>[A-Z]*)\s"
                                 r"#(?P<channel>[a-z0-9A-Z]+)")}

        self._groups = ('action', 'data', 'content', 'channel', 'author')
        self._http = attrs.get('http')

        self._pubsub_pool = PubSubPool(loop=loop, base=self)

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

    async def send_cap(self, cap: str):
        """|coro|

        Send a CAP REQ to Twitch.

        Valid caps are: commands, tags, membership

        Parameters
        ------------
        cap: str
            The cap request you wish to send to Twitch. Must be either commands, tags or membership.
        """
        await self._websocket.send(f'CAP REQ :twitch.tv/{cap}')

    async def auth_seq(self, channels: Union[list, tuple]=None):
        """|coro|

        Automated Authentication process.

        Attempts to authenticate on the Twitch servers with the provided
        nickname and IRC Token (pass).

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

        for cap in self.modes:
            await self._websocket.send(f'CAP REQ :twitch.tv/{cap}')

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

        .. warning::

            This method is not handled by built-in rate-limits. You risk getting rate limited by twitch,
            which has a 30 minute cooldown.
        """
        content = content.replace("\n", " ")
        channel = re.sub('[#\s]', '', channel).lower()
        await self._websocket.send(f"PRIVMSG #{channel} :{content}\r\n")

    async def join_channels(self, channels: (list, tuple)):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        channels: Union[list, tuple]
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

            self.loop.create_task(self._bot.event_raw_data(data))

            try:
                await self.process_data(data)
            except AuthenticationError:
                raise
            except Exception as e:
                await self.event_error(e, data)

    async def process_ping(self, resp):
            await self._websocket.send(f"PONG {resp}\r\n")

    async def process_data(self, data):
        data = data.strip()

        try:
            code = int(self.regex['code'].match(data).group('code'))
        except AttributeError:
            code = None

        if code == 376 or code == 1:
            await self._dispatch('ready')
            self.is_ready.set()
            log.info('Successfully logged onto Twitch WS | %s', self.nick)
        elif data == ':tmi.twitch.tv NOTICE * :Login authentication failed' or\
                data == ':tmi.twitch.tv NOTICE * :Improperly formatted auth':
            log.warning('Authentication failed | %s', self._token)
            raise AuthenticationError('Websocket Authentication Failure... Check your token and nick.')

        _groupsdict = {}

        if data.startswith("PING"):
            match = self.regex["ping"]
        else:
            match = self.regex["data"]

        result = match.match(data)

        badges = self.regex['badges'].match(data)

        if badges:
            badges = {'name': badges.group('name'), 'mod': badges.group('mod'), 'action': badges.group('action'),
                      'channel': badges.group('channel')}

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

        await self.process_actions(data, _groupsdict, badges, tags)

    async def process_actions(self, raw, groups, badges, tags=None):
        # todo add remaining actions, docs

        action = groups.pop('action', None)
        data = groups.pop('data', None)
        content = groups.pop('content', None)
        channel = groups.pop('channel', None)

        if not action and badges:
            action = badges['action']
        elif not action:
            action = 'PING'

        try:
            author = self.regex["author"].match(data).group("author")
        except Exception:
            author = None

        if channel:
            channel = Channel(name=channel, ws=self, http=self._http)

        try:
            user = User(author=author, channel=channel or None, tags=tags, ws=self._websocket)
        except (TypeError, KeyError):
            user = None

        try:
            message = Message(author=user, content=content, channel=channel, raw_data=data, tags=tags)
        except (TypeError, KeyError):
            message = None

        if action == 'RECONNECT':
            # TODO Disconnection/Reconnection Logic.
            return

        elif action == 'JOIN':
            if author == self.nick:
                self._channel_cache[channel.name] = {'channel': channel, 'bot': user}
                self._channel_token += 1

            await self._dispatch('join', user)

        elif action == 'PART':
            if author == self.nick:
                del self._channel_cache[channel.name]
                self._channel_token -= 1

            await self._dispatch('part', user)

        elif action == 'PING':
            await self.process_ping(content)

        elif action == 'PRIVMSG':
            await self._dispatch('message', message)

        elif action == 'USERSTATE':
            if not user or not user.name:
                if badges:
                    user = User(author=badges['name'],
                                channel=Channel(name=badges['channel'], ws=self, http=self._http)or None,
                                tags=tags,
                                ws=self._websocket,
                                mod=badges['mod'])
                else:
                    return

            if user._name.lower() == self.nick.lower():
                self._channel_cache[channel.name]['bot'] = user

            await self._dispatch('userstate', user)

        elif action == 'MODE':
            mdata = re.match(r':jtv MODE #(?P<channel>.+?[a-z0-9])\s(?P<status>[\+\-]o)\s(?P<user>.*[a-z0-9])', raw)
            mstatus = mdata.group('status')

            user = User(author=mdata.group('user'), channel=channel, tags=tags, ws=self._websocket)

            if user._name.lower() == self.nick.lower():
                await self._token_update(mstatus)
                self._channel_cache[channel.name]['bot'] = user

            await self._dispatch('mode', channel, user, mstatus)

    async def _dispatch(self, event: str, *args, **kwargs):
        func = getattr(self._bot, f'event_{event}')
        self.loop.create_task(func(*args, **kwargs))

        listeners = getattr(self._bot, 'extra_listeners', None)
        if not listeners:
            return

        extras = listeners.get(f'event_{event}', [])
        ret = await asyncio.gather(*[e(*args, **kwargs) for e in extras])

        for e in ret:
            if isinstance(e, Exception):
                self.loop.create_task(self.event_error(e))

    async def event_error(self, error: Exception, data=None):
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


class PubSub:

    __slots__ = ('loop', '_pool', '_node', '_subscriptions', '_topics', '_websocket', '_timeout', '_last_result',
                 '_listener')

    def __init__(self, loop, pool: PubSubPool, node: int):
        self.loop = loop
        self._pool = pool
        self._node = node
        self._topics = []
        self._websocket = None
        self._timeout = asyncio.Event()

        self._last_result = None

        loop.create_task(self.handle_ping())
        self._listener = None

    @property
    def node(self):
        return self._node

    async def reconnection(self):
        backoff = ExponentialBackoff()
        self._listener.cancel()

        while True:
            retry = backoff.delay()
            log.info('PubSub Websocket closed: Retrying connection in %s seconds...', retry)

            await self.connect()

            if self._websocket is not None and self._websocket.open:
                for topic in self._topics:
                    await self.resub(topic[1], topic[0])
                return

            await asyncio.sleep(retry)

    async def connect(self):
        try:
            self._websocket = await websockets.connect('wss://pubsub-edge.twitch.tv')
        except Exception as e:
            self._last_result = e
            log.error('PubSub websocket connection failed | %s', e)

            raise WSConnectionFailure('PubSub websocket connection failed. Check logs for details.')

        log.info('PubSub %s connection successful', self.node)
        self._listener = self.loop.create_task(self.listen())

    async def handle_ping(self):
        while True:
            jitter = random.randint(1, 5)
            await asyncio.sleep(240 + jitter)
            self._timeout.clear()

            if not self._websocket:
                continue
            if self._websocket.open:
                log.debug('PubSub %s Sending PING payload.', self.node)
                await self._websocket.send(json.dumps({"type": "PING"}))
            else:
                continue

            try:
                async with async_timeout.timeout(10):
                    await self._timeout.wait()
            except asyncio.TimeoutError:
                self.loop.create_task(self.reconnection())

    async def listen(self):
        while True:
            try:
                data = json.loads(await self._websocket.recv())
                self.loop.create_task(self._pool.base._dispatch('raw_pubsub', data))
            except websockets.ConnectionClosed:
                return self.loop.create_task(self.reconnection())

            if data['type'] == 'PONG':
                log.debug('PubSub %s received PONG payload.', self.node)
                self._timeout.set()
            elif data['type'] == 'RECONNECT':
                log.debug('PubSub %s received RECONNECT payload... Attempting reconnection', self.node)
                self.loop.create_task(self.reconnection())

            # self.loop.create_task(self._pool.base._dispatch('pubsub', data))

    async def subscribe(self, token: str, nonce: str, *topics: str):
        for t in topics:
            self._topics.append((t, token))

        payload = {"type": "LISTEN",
                   "nonce": nonce,
                   "data": {"topics": [*topics],
                            "auth_token": token}}

        await self._websocket.send(json.dumps(payload))

    async def resub(self, token: str, topic: str):
        payload = {"type": "LISTEN",
                   "data": {"topics": [topic],
                            "auth_token": token}}

        await self._websocket.send(json.dumps(payload))

