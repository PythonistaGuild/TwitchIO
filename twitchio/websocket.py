# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2019 TwitchIO

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
import sys
import time
import traceback
import typing
import websockets
from functools import partial
from .backoff import ExponentialBackoff
from .channel import Channel
from .errors import AuthenticationError
from .message import Message
from .parse import parser
from .user import User, PartialUser

log = logging.getLogger(__name__)
HOST = 'wss://irc-ws.chat.twitch.tv:443'


class WSConnection:

    def __init__(self, **kwargs):
        self._loop: asyncio.AbstractEventLoop = kwargs.get('loop', asyncio.get_event_loop())
        self._backoff = ExponentialBackoff()
        self._keeper: asyncio.Task = None
        self._websocket = None
        self._ws_ready_event: asyncio.Event = asyncio.Event()
        self.is_ready: asyncio.Event = asyncio.Event()
        self._join_lock: asyncio.Lock = asyncio.Lock()
        self._join_handle = 0
        self._join_tick = 50
        self._join_pending = {}
        self._join_load = {}
        self._init = False

        self._channel_cache = {}
        self._actions = {'PING': self._ping,
                         'PART': self._part,
                         'PRIVMSG': self._privmsg,
                         'PRIVMSG(ECHO)': self._privmsg_echo,
                         'USERSTATE': self._userstate,
                         'USERNOTICE': self._usernotice,
                         'JOIN': self._join,
                         'MODE': self._mode,
                         'RECONNECT': self._reconnect}

        self._token = kwargs.get('token')
        self.nick = kwargs.get('nick').lower()
        self.modes = kwargs.pop('modes', ("commands", "tags", "membership"))
        self._initial_channels = kwargs.get('initial_channels')

        self._last_ping = 0

        self._bot = kwargs.get('bot')

    @property
    def is_alive(self) -> bool:
        return self._websocket and self._websocket.open

    async def wait_until_ready(self):
        await self.is_ready.wait()

    async def _connect(self):
        self.is_ready.clear()

        if self._keeper:
            self._keeper.cancel()

        if self.is_alive:
            await self._websocket.close()

        try:
            self._websocket = await websockets.connect(HOST)
        except Exception as e:
            retry = self._backoff.delay()
            log.error(f'Websocket connection failure: {e}:: Attempting reconnect in {retry} seconds.')

            await asyncio.sleep(retry)
            return asyncio.create_task(self._connect())

        if time.time() > self._last_ping + 240:
            await self.authenticate(self._initial_channels)

        self._keeper = asyncio.create_task(self._keep_alive())
        self._ws_ready_event.set()

    async def _keep_alive(self):
        await self._ws_ready_event.wait()
        self._ws_ready_event.clear()

        if not self._last_ping:
            self._last_ping = time.time()

        while not self._websocket.closed:
            try:
                data = await self._websocket.recv()   # Receive data...
            except websockets.ConnectionClosed as e:
                log.error(f'Websocket connection was closed: {e}')
                return asyncio.create_task(self._connect())

            if data:
                await self.dispatch('raw_data', data)   # Dispatch our event_raw_data event...

                task = asyncio.create_task(self._process_data(data))
                task.add_done_callback(partial(self._task_callback, data))   # Process our raw data

        asyncio.create_task(self._connect())

    def _task_callback(self, data, task):
        exc = task.exception()

        if isinstance(exc, AuthenticationError):   # Check if we failed to log in...
            log.error('Authentication error. Please check your credentials and try again.')
            self._close()
        elif exc:
            asyncio.create_task(self.event_error(exc, data))

    async def authenticate(self, channels: typing.Union[list, tuple]):
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
        if not self.is_alive:
            return

        await self._websocket.send(f'PASS {self._token}\r\n')
        await self._websocket.send(f'NICK {self.nick}\r\n')

        for cap in self.modes:
            await self._websocket.send(f'CAP REQ :twitch.tv/{cap}')   # Ideally no one should overwrite defaults...

        if not channels and not self._initial_channels:
            return

        channels = channels or self._initial_channels
        await self.join_channels(*channels)

    async def join_channels(self, *channels: str):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        *channels : str
            An argument list of channels to attempt joining.
        """
        async with self._join_lock as lock:   # acquire a lock, allowing only one join_channels at once...
            for channel in channels:
                if self._join_handle < time.time():   # Handle is less than the current time
                    self._join_tick = 50              # So lets start a new rate limit bucket..
                    self._join_handle = time.time() + 15   # Set the handle timeout time

                if self._join_tick == 0:   # We have exhausted the bucket, wait so we can make a new one...
                    await asyncio.sleep(self._join_handle - time.time())
                    continue

                asyncio.create_task(self._join_channel(channel))
                self._join_tick -= 1

    async def _join_channel(self, entry):
        channel = re.sub('[#]', '', entry).lower()
        await self._websocket.send(f'JOIN #{channel}\r\n')

        self._join_pending[channel] = fut = self._loop.create_future()
        asyncio.create_task(self._join_future_handle(fut, channel))

    async def _join_future_handle(self, fut: asyncio.Future, channel: str):
        try:
            await asyncio.wait_for(fut, timeout=10)
        except asyncio.TimeoutError:
            log.error(f'The channel "{channel}" was unable to be joined. Check the channel is valid.')
            self._join_pending.pop(channel)

            data = f':{self.nick}.tmi.twitch.tv 353 {self.nick} = #TWITCHIOFAILURE :{channel}\r\n' \
                   f':{self.nick}.tmi.twitch.tv 366 {self.nick} #TWITCHIOFAILURE :End of /NAMES list'

            await self._process_data(data)

    async def _process_data(self, data: str):
        data = data.rstrip()
        parsed = parser(data, self.nick)

        if parsed['action'] == 'PING':
            return await self._ping()
        elif parsed['code'] != 0:
            return await self._code(parsed, parsed['code'])
        elif data == ':tmi.twitch.tv NOTICE * :Login authentication failed' or\
             data == ':tmi.twitch.tv NOTICE * :Improperly formatted auth':

            log.error(f'Authentication failed with | {self._token} | {self.nick}')
            return await self._close()

        partial_ = self._actions.get(parsed['action'])
        if partial_:
            await partial_(parsed)

    async def _await_futures(self):
        futures = self._fetch_futures()

        for fut in futures:
            try:
                fut.exception()
            except asyncio.InvalidStateError:
                pass

            if fut.done():
                futures.remove(fut)

        if futures:
            await asyncio.wait(futures)

    async def _code(self, parsed, code: int):
        if code == 1 or code == 376:
            log.info(f'Successfully logged onto Twitch WS: {self.nick}')

            await self._await_futures()
            await self.is_ready.wait()
            await self.dispatch('ready')
            self._init = True

        elif code == 353:
            if parsed['channel'] == 'TWITCHIOFAILURE':
                self._initial_channels.remove(parsed['batches'][0])

            if parsed['channel'] in self._initial_channels and not self._init:
                self._join_load[parsed['channel']] = None

            if len(self._join_load) == len(self._initial_channels):
                for channel in self._initial_channels:
                    self._join_load.pop(channel)
                    asyncio.create_task(self._update_cache(parsed))
                self.is_ready.set()
            else:
                asyncio.create_task(self._update_cache(parsed))

    async def _ping(self):
        log.debug('ACTION: Sending PONG reply.')
        await self._websocket.send('PONG :tmi.twitch.tv\r\n')

    async def _part(self, parsed):   # TODO
        log.debug(f'ACTION: PART:: {parsed["channel"]}')
        pass

    async def _privmsg(self, parsed):   # TODO(Update Cache)
        log.debug(f'ACTION: PRIVMSG:: {parsed["channel"]}')

        try:
            channel = self._channel_cache[parsed['channel']]
        except KeyError:
            channel = Channel(name=parsed['channel'], echo=False, websocket=self, bot=self)
            await self._update_cache(parsed)

        user = User(tags=parsed['badges'], name=parsed['user'], channel=channel,
                    bot=self._bot, websocket=self)

        message = Message(raw_data=parsed['data'], content=parsed['message'],
                          author=user, channel='Test', tags=parsed['badges'], )

        await self.dispatch('message', message)

    async def _privmsg_echo(self, parsed):   # TODO
        log.debug(f'ACTION: PRIVMSG(ECHO):: {parsed["channel"]}')
        pass

    async def _userstate(self, parsed):   # TODO
        log.debug(f'ACTION: USERSTATE:: {parsed["channel"]}')
        pass

    async def _usernotice(self, parsed):   # TODO
        log.debug(f'ACTION: USERNOTICE:: {parsed["channel"]}')
        pass

    async def _join(self, parsed):
        log.debug(f'ACTION: JOIN:: {parsed["channel"]}')
        channel = parsed['channel']

        if self._join_pending:
            try:
                self._join_pending[channel].set_result(None)
            except KeyError:
                pass
            else:
                self._join_pending.pop(channel)

        await self._update_cache(parsed)

        users = self._channel_cache[channel]

        user = PartialUser(name=parsed['user'], bot=self._bot, websocket=self, channel=channel)
        channel = Channel(name=channel, bot=self._bot, users=users, websocket=self)

        await self.dispatch('join', channel, user)

    async def _update_cache(self, parsed: dict):
        channel = parsed['channel'].lstrip('#')

        if channel not in self._channel_cache:
            self._channel_cache[channel] = set()

        if parsed['batches']:
            for u in parsed['batches']:
                user = PartialUser(name=u, bot=self._bot, websocket=self, channel=channel)
                self._channel_cache[channel].add(user)
        else:
            user = PartialUser(bot=self._bot, name=parsed['user'], websocket=self, channel=channel)
            self._channel_cache[channel].add(user)

    async def _mode(self, parsed):   # TODO
        pass

    async def _reconnect(self, parsed):  # TODO
        pass

    async def dispatch(self, event: str, *args, **kwargs):
        log.debug(f'Dispatching event: {event}')

        func = getattr(self._bot, f'event_{event}')
        asyncio.create_task(func(*args, **kwargs))

        listeners = getattr(self._bot, 'extra_listeners', None)
        if not listeners:
            return

        extras = listeners.get(f'event_{event}', [])
        ret = await asyncio.gather(*[e(*args, **kwargs) for e in extras])

        for e in ret:
            if isinstance(e, Exception):
                asyncio.create_task(self.event_error(e))

    async def event_error(self, error: Exception, data: str=None):
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def _fetch_futures(self):
        return [fut for chan, fut in self._join_pending.items() if chan.lower() in
                [re.sub('[#]', '', c).lower() for c in self._initial_channels]]

    def _close(self):
        self._keeper.cancel()
        self.is_ready.clear()

        futures = self._fetch_futures()

        for fut in futures:
            fut.cancel()

        self._websocket.close()
        self._loop.stop()
