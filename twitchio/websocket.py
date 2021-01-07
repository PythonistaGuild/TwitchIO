# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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
import async_timeout
import copy
import functools
import itertools
import json
import logging
import re
import secrets
import sys
import traceback
import websockets
from typing import Union

from .backoff import ExponentialBackoff
from .dataclasses import *
from .errors import WSConnectionFailure, AuthenticationError, ClientError


log = logging.getLogger(__name__)


class PubSubPool:

    POOL_MAX = 10

    def __init__(self, loop: asyncio.BaseEventLoop, base):
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

        self._channel_cache = {}
        self._initial_channels = attrs.get('initial_channels')

        self.nick = attrs.get('nick').lower()
        self.extra_listeners = {}

        self.modes = attrs.pop('modes', ("commands", "tags", "membership"))
        self._mod_token = 0
        self._channel_token = 0
        self._rate_status = None

        self._pending_joins = {}
        self._pending_parts = {}
        self._authentication_error = False

        self.is_ready = asyncio.Event()

        self.regex = {
            "data": re.compile(
                r"^(?:@(?P<tags>\S+)\s)?:(?P<data>\S+)(?:\s)"
                r"(?P<action>[A-Z()-]+)(?:\s#)(?P<channel>\S+)"
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
                                 r"#(?P<channel>[a-z0-9A-Z]+)"),
            "batches": re.compile(r":(?P<author>[a-zA-Z0-9_]+)!(?P=author)@(?P=author).tmi.twitch.tv"
                                  r"\s(?P<action>[A-Z()-]+)(?:\s#)(?P<channel>\S+)"),
            "nameslist": re.compile(r"(?P<author>[a-zA-Z0-9_]+).tmi.twitch.tv\s(?P<code>\S+)\s(?P=author)"
                                 r"\s=\s#(?P<channel>\S+)\s:(?P<names>.+)")}

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

    async def _token_update(self, status: str):
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
    def is_connected(self) -> bool:
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
            log.debug('Sending authentication sequence payload to Twitch.')
            self.loop.create_task(self.auth_seq())

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
        log.debug('Sending CAP REQ: %s', cap)
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
        await self.join_channels(*channels)

    async def send_nick(self):
        """|coro|

        Sends a NICK request to the Twitch IRC Endpoint.

        This should only be used if :func:`auth_seq` was not used.
        """
        await self._websocket.send(f"NICK {self.nick}\r\n")

    async def send_privmsg(self, channel: str, content: str):
        """|coro|

        Sends a PRIVMSG to the Twitch IRC Endpoint.

        This should only be used directly in rare circumstances where a :class:`twitchio.abcs.Messageable` is not available.

        .. warning::

            This method is not directly handled by built-in rate-limits. You risk getting rate limited by twitch,
            which has a 30 minute cooldown.
        """

        content = content.replace("\n", " ")
        channel = re.sub('[#\s]', '', channel).lower()
        await self._websocket.send(f"PRIVMSG #{channel} :{content}\r\n")

        # Create a dummy message, used as a fake echo-message...
        data = f':{self.nick}!{self.nick}@{self.nick}.tmi.twitch.tv PRIVMSG(ECHO-MESSAGE) #{channel} :{content}\r\n'
        self.loop.create_task(self.process_data(data))

    async def join_channels(self, *channels: str):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        *channels : str
            An argument list of channels to attempt joining.
        """

        await asyncio.gather(*[self._join_channel(x) for x in channels])

    async def _join_channel(self, entry):
        channel = re.sub('[#\s]', '', entry).lower()
        await self._websocket.send(f'JOIN #{channel}\r\n')

        self._pending_joins[channel] = fut = self.loop.create_future()

        try:
            await asyncio.wait_for(fut, timeout=10)
        except asyncio.TimeoutError:
            self._pending_joins.pop(channel)

            raise asyncio.TimeoutError(
                f'Request to join the "{channel}" channel has timed out. Make sure the channel exists.')

    async def part_channels(self, *channels: str):
        """|coro|

        Attempt to part the provided channels.

        Parameters
        ------------
        *channels : str
            An argument list of channels to attempt parting.
        """

        await asyncio.gather(*[self._part_channel(x) for x in channels])

    async def _part_channel(self, entry):
        channel = re.sub('[#\s]', '', entry).lower()

        if channel not in self._channel_cache:
            raise ClientError(f'Request to leave the channel "{channel}" failed.')

        await self._websocket.send(f'PART #{channel}\r\n')

        self._pending_parts[channel] = fut = self.loop.create_future()

        try:
            await asyncio.wait_for(fut, timeout=10)
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                f'Request to leave the channel "{channel}" has timed out.')

    async def _listen(self):
        backoff = ExponentialBackoff()

        if not self.is_connected and self._last_exec:
            raise WSConnectionFailure(f'Websocket connection failure:\n\n{self._last_exec}')

        while True:
            if self._authentication_error:
                log.error('AUTHENTICATION ERROR:: Incorrect IRC Token passed.')
                raise AuthenticationError

            try:
                data = await self._websocket.recv()
            except websockets.ConnectionClosed:
                retry = backoff.delay()
                log.info('Websocket closed: Retrying connection in %s seconds...', retry)

                await asyncio.sleep(retry)
                await self._connect()
                continue

            await self._dispatch('raw_data', data)

            _task = self.loop.create_task(self.process_data(data))
            _task.add_done_callback(functools.partial(self._task_callback, data))

    def _task_callback(self, data, task):
        exc = task.exception()

        if isinstance(exc, AuthenticationError):
            self._authentication_error = True
        elif exc:
            self.loop.create_task(self.event_error(exc, data))

    async def process_ping(self, resp: str):
        await self._websocket.send(f"PONG {resp}\r\n")

    async def process_data(self, data):
        data = data.strip()

        try:
            code = int(self.regex['code'].match(data).group('code'))
        except AttributeError:
            code = None

        if code == 376 or code == 1:
            log.info('Successfully logged onto Twitch WS | %s', self.nick)

            futures = [fut for chan, fut in self._pending_joins.items() if chan.lower() in
                       [re.sub('[#\s]', '', c).lower() for c in self._initial_channels]]

            for fut in futures:
                try:
                    fut.exception()
                except asyncio.InvalidStateError:
                    pass

                if fut.done():
                    futures.remove(fut)

            if futures:
                await asyncio.wait(futures)

            await self._dispatch('ready')
            self.is_ready.set()

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
                if t[1].isdecimal():
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

    async def process_actions(self, raw: str, groups: dict, badges: dict, tags: dict=None):
        # todo add remaining actions, docs

        # Make sure the batched JOIN and PART events get sent...
        for match in self.regex['batches'].finditer(raw):
            if match.groups()[1] == 'JOIN':
                self.loop.create_task(self.join_action(match.groups()[2], match.groups()[0], tags))
            elif match.groups()[1] == 'PART':
                self.loop.create_task(self.part_action(match.groups()[2], match.groups()[0], tags))

        # Fill the channel cache with initial viewers...
        names = self.regex['nameslist'].finditer(raw)
        for match in names:
            if match.group('code') == '353':
                for name in match.group('names').split(' '):
                    self.loop.create_task(self.join_action(match.groups()[2], name, tags))

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
            try:
                channel = self._channel_cache[channel]['channel']
            except KeyError:
                channel = Channel(name=channel, ws=self, http=self._http)

        try:
            user = User(author=author, channel=channel or None, tags=tags, ws=self._websocket)
        except (TypeError, KeyError):
            user = None

        try:
            message = Message(author=user, content=content, channel=channel, raw_data=raw, tags=tags)
        except (TypeError, KeyError):
            message = None

        if action == 'RECONNECT':
            # TODO Disconnection/Reconnection Logic.
            return

        elif action == 'JOIN':
            pass

        elif action == 'PART':
            pass

        elif action == 'PING':
            log.debug('ACTION:: PING')
            await self.process_ping(content)

        elif action == 'PRIVMSG':
            await self._dispatch('message', message)
        elif action == 'PRIVMSG(ECHO-MESSAGE)':
            message.echo = True
            message._channel = copy.copy(message.channel)
            message.channel._echo = True

            await self._dispatch('raw_data', raw)
            await self._dispatch('message', message)

        elif action == 'USERNOTICE':
            await self._dispatch('raw_usernotice', channel, tags)

            if tags['msg-id'] in ('sub', 'resub'):
                user = User(author=tags['login'], channel=channel, tags=tags, ws=self._websocket)
                notice = NoticeSubscription(channel=channel, user=user, tags=tags)

                await self._dispatch('usernotice_subscription', notice)

        elif action == 'USERSTATE':
            log.debug('ACTION:: USERSTATE')

            if not user or not user.name:
                if badges:
                    user = User(author=badges['name'],
                                channel=Channel(name=badges['channel'], ws=self, http=self._http) or None,
                                tags=tags,
                                ws=self._websocket,
                                mod=badges['mod'])
                else:
                    return

            if user._name.lower() == self.nick.lower():
                try:
                    self._channel_cache[channel.name]['bot'] = user
                except KeyError:
                    self._channel_cache[channel.name] = {'channel': channel, 'bot': user}

            await self._dispatch('userstate', user)

        elif action == 'MODE':
            log.debug('ACTION:: MODE')

            mdata = re.match(r':jtv MODE #(?P<channel>.+?[a-z0-9])\s(?P<status>[\+\-]o)\s(?P<user>.*[a-z0-9])', raw)
            mstatus = mdata.group('status')

            user = User(author=mdata.group('user'), channel=channel, tags=tags, ws=self._websocket)

            if user._name.lower() == self.nick.lower():
                await self._token_update(mstatus)
                try:
                    self._channel_cache[channel.name]['bot'] = user
                except KeyError:
                    self._channel_cache[channel.name] = {'channel': channel, 'bot': user}

            await self._dispatch('mode', channel, user, mstatus)

        elif action == 'CLEARCHAT': #新增 被ban事件
            log.debug('ACTION:: CLEARCHAT')

            user = User(author=content, channel=channel, tags=tags, ws=self._websocket)
            notice = ClearChat(channel=channel, user=user, tags=tags)

            await self._dispatch('clearchat', notice)

    async def join_action(self, channel: str, author: str, tags):
        log.debug('ACTION:: JOIN: %s', channel)

        if author == self.nick:
            chan_ = Channel(name=channel, ws=self, http=self._http)
            user = User(author=author, channel=chan_, tags=tags, ws=self._websocket)

            self._channel_cache[channel] = {'channel': chan_, 'bot': user}

            if channel in self._pending_joins:
                self._pending_joins[channel].set_result(None)
                self._pending_joins.pop(channel)

            self._channel_token += 1

        try:
            cache = self._channel_cache[channel]['channel']._users
        except KeyError as e:
            raise ClientError("The \"nick\" value passed to the constructor does not match the user we are logged in as") from e

        try:
            user = cache[author.lower()]
        except KeyError:
            channel = self._channel_cache[channel]['channel']
            user = User(author=author, channel=channel, tags=tags, ws=self._websocket)

            cache[author.lower()] = user

        await self._dispatch('join', user)

    async def part_action(self, channel: str, author: str, tags):
        log.debug('ACTION:: PART: %s', channel)

        if author == self.nick:
            self._channel_cache.pop(channel)
            self._channel_token -= 1

            if self._pending_parts:
                self._pending_parts[channel].set_result(None)
                self._pending_parts.pop(channel)
        try:
            cache = self._channel_cache[channel]['channel']._users
        except KeyError:
            channel = Channel(name=channel, ws=self, http=self._http)
            user = User(author=author, channel=channel or None, tags=tags, ws=self._websocket)
        else:
            try:
                user = cache.pop(author.lower())
            except KeyError:
                channel = Channel(name=channel, ws=self, http=self._http)
                user = User(author=author, channel=channel or None, tags=tags, ws=self._websocket)

        await self._dispatch('part', user)

    async def _dispatch(self, event: str, *args, **kwargs):
        log.debug('Dispatching event: %s', event)

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

    async def event_error(self, error: Exception, data: str=None):
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def teardown(self):
        if self._bot._webhook_server:
            self._bot._webhook_server.stop()

        self._websocket.close()


class PubSub:

    __slots__ = ('loop', '_pool', '_node', '_subscriptions', '_topics', '_websocket', '_timeout', '_last_result',
                 '_listener')

    def __init__(self, loop: asyncio.BaseEventLoop, pool: PubSubPool, node: int):
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
    def node(self) -> int:
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

    @staticmethod
    def generate_jitter():
        # Generates a random number between around 1 and 10
        jitter = 0

        while jitter == 11 or jitter == 0:
            bites = secrets.token_bytes(2)
            number = itertools.accumulate(bites)
            jitter = int(sum(number) / 2 ** 6)

        return jitter

    async def handle_ping(self):
        while True:
            jitter = self.generate_jitter()
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

