# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

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
from functools import partial
from typing import Union, Optional, List, TYPE_CHECKING

import aiohttp

from .backoff import ExponentialBackoff
from .channel import Channel
from .errors import AuthenticationError
from .message import Message
from .parse import parser
from .chatter import Chatter, PartialChatter, WhisperChatter

if TYPE_CHECKING:
    from .client import Client
log = logging.getLogger(__name__)
HOST = "wss://irc-ws.chat.twitch.tv:443"


class WSConnection:
    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop,
        heartbeat: Optional[float],
        client: "Client",
        token: str = None,
        modes: tuple = None,
        initial_channels: List[str] = None,
        retain_cache: Optional[bool] = True,
    ):
        self._loop = loop
        self._backoff = ExponentialBackoff()
        self._keeper: Optional[asyncio.Task] = None
        self._websocket = None
        self._heartbeat = heartbeat
        self._ws_ready_event: asyncio.Event = asyncio.Event()
        self.is_ready: asyncio.Event = asyncio.Event()
        self._join_lock: asyncio.Lock = asyncio.Lock()
        self._join_handle = 0
        self._join_tick = 20
        self._join_pending = {}
        self._join_load = {}
        self._init = False

        self._cache = {}
        self._actions = {
            "PING": self._ping,
            "PART": self._part,
            "PRIVMSG": self._privmsg,
            "PRIVMSG(ECHO)": self._privmsg_echo,
            "USERSTATE": self._userstate,
            "USERNOTICE": self._usernotice,
            "JOIN": self._join,
            "MODE": self._mode,
            "RECONNECT": self._reconnect,
            "WHISPER": self._privmsg,
        }

        self.nick = None
        self.user_id = None
        self._token = token
        self.modes = modes or ("commands", "tags", "membership")
        self._initial_channels = initial_channels or []
        self._retain_cache = retain_cache

        if callable(self._initial_channels):
            _temp_initial_channels = self._initial_channels()
            if isinstance(_temp_initial_channels, (list, tuple)):
                self._initial_channels = _temp_initial_channels
            else:
                self._initial_channels = [_temp_initial_channels]
        self._last_ping = 0
        self._reconnect_requested = False

        self._client = client

        # https://docs.python.org/3/library/asyncio-task.html#creating-tasks
        # -> Important: Save a reference to the tasks, to avoid a task disappearing mid-execution.
        self._background_tasks: List[asyncio.Task] = []
        self._task_cleaner: Optional[asyncio.Task] = None

    async def _task_cleanup(self):
        while True:
            # keep all undone tasks
            self._background_tasks = list(filter(lambda task: not task.done(), self._background_tasks))

            # cleanup tasks every 30 seconds
            await asyncio.sleep(30)

    @property
    def is_alive(self) -> bool:
        return self._websocket is not None and not self._websocket.closed

    async def wait_until_ready(self):
        await self.is_ready.wait()

    async def _connect(self):
        """Attempt to connect to Twitch's Websocket."""
        self.is_ready.clear()

        if self._keeper:
            self._keeper.cancel()  # Stop our current keep alive.
        if self.is_alive:
            await self._websocket.close()  # If for some reason we are in a weird state, close it before retrying.
        if not self._client._http.nick:
            try:
                data = await self._client._http.validate(token=self._token)
            except AuthenticationError:
                await self._client._http.session.close()
                self._client._closing.set()  # clean up and error out (this is called to avoid calling Client.close in start()
                raise
            self.nick = data["login"]
            self.user_id = int(data["user_id"])
        else:
            self.nick = self._client._http.nick
        session = self._client._http.session

        try:
            self._websocket = await session.ws_connect(url=HOST, heartbeat=self._heartbeat)
        except Exception as e:
            retry = self._backoff.delay()
            log.error(f"Websocket connection failure: {e}:: Attempting reconnect in {retry} seconds.")

            await asyncio.sleep(retry)
            return await self._connect()

        await self.authenticate(self._initial_channels)

        self._keeper = asyncio.create_task(self._keep_alive())  # Create our keep alive.

        if not self._task_cleaner or self._task_cleaner.done():
            self._task_cleaner = asyncio.create_task(self._task_cleanup())  # Create our task cleaner.

        self._ws_ready_event.set()

    async def _keep_alive(self):
        await self._ws_ready_event.wait()
        self._ws_ready_event.clear()

        if not self._last_ping:
            self._last_ping = time.time()
        while not self._websocket.closed and not self._reconnect_requested:
            msg = await self._websocket.receive()  # Receive data...

            if msg.type is aiohttp.WSMsgType.CLOSED:
                log.error(f"Websocket connection was closed: {msg.extra}")
                break
            data = msg.data
            if data:
                log.debug(f" < {data}")
                self.dispatch("raw_data", data)  # Dispatch our event_raw_data event...

                events = data.split("\r\n")
                for event in events:
                    if not event:
                        continue
                    task = asyncio.create_task(self._process_data(event))
                    task.add_done_callback(partial(self._task_callback, event))  # Process our raw data
                    self._background_tasks.append(task)

        self._background_tasks.append(asyncio.create_task(self._connect()))

    def _task_callback(self, data, task):
        exc = task.exception()

        if isinstance(exc, AuthenticationError):  # Check if we failed to log in...
            log.error("Authentication error. Please check your credentials and try again.")
            self._close()
        elif exc:
            # event_error task need to be shielded to avoid cancelling in self._close() function
            # we need ensure, that the event will print its traceback
            shielded_task = asyncio.shield(asyncio.create_task(self.event_error(exc, data)))
            self._background_tasks.append(shielded_task)

    async def send(self, message: str):
        message = message.strip().replace("\n", "")
        log.debug(f" > {message}")

        if message.startswith("PRIVMSG #"):
            data = message.replace("PRIVMSG #", "", 1).split(" ")
            channel = data.pop(0)
            content = " ".join(data)

            dummy = f"> :{self.nick}!{self.nick}@{self.nick}.tmi.twitch.tv PRIVMSG(ECHO) #{channel} {content}\r\n"

            task = asyncio.create_task(self._process_data(dummy))
            task.add_done_callback(partial(self._task_callback, dummy))  # Process our raw data
            self._background_tasks.append(task)
        await self._websocket.send_str(message + "\r\n")

    async def reply(self, msg_id: str, message: str):
        message = message.strip().replace("\n", "")
        log.debug(f" > {message}")

        if message.startswith("PRIVMSG #"):
            data = message.replace("PRIVMSG #", "", 1).split(" ")
            channel = data.pop(0)
            content = " ".join(data)

            dummy = f"> @reply-parent-msg-id={msg_id} :{self.nick}!{self.nick}@{self.nick}.tmi.twitch.tv PRIVMSG(ECHO) #{channel} {content}\r\n"
            task = asyncio.create_task(self._process_data(dummy))
            task.add_done_callback(partial(self._task_callback, dummy))  # Process our raw data
            self._background_tasks.append(task)
        await self._websocket.send_str(f"@reply-parent-msg-id={msg_id} {message} \r\n")

    async def authenticate(self, channels: Union[list, tuple]):
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
        await self.send(f"PASS oauth:{self._token}\r\n")
        await self.send(f"NICK {self.nick}\r\n")

        for cap in self.modes:
            await self.send(f"CAP REQ :twitch.tv/{cap}")  # Ideally no one should overwrite defaults...
        if not channels and not self._initial_channels:
            return
        channels = channels or self._initial_channels
        await self.join_channels(*channels)

    async def part_channels(self, *channels: str):
        """|coro|

        Attempt to part the provided channels.

        Parameters
        ----------
        *channels: str
            An argument list of channels to attempt parting.
        """

        for channel in channels:
            channel = re.sub("[#]", "", channel).lower()
            await self.send(f"PART #{channel}\r\n")
            if self._retain_cache:
                self._cache.pop(channel, None)

    def _assign_timeout(self, channel_count: int):
        if channel_count <= 40:
            return 30
        elif channel_count <= 60:
            return 40
        elif channel_count <= 80:
            return 50
        else:
            return 60

    async def join_channels(self, *channels: str):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        *channels : str
            An argument list of channels to attempt joining.
        """
        async with self._join_lock:
            channel_count = len(channels)
            if channel_count > 20:
                timeout = self._assign_timeout(channel_count)
                chunks = [channels[i : i + 20] for i in range(0, len(channels), 20)]
                for chunk in chunks:
                    for channel in chunk:
                        task = asyncio.create_task(self._join_channel(channel, timeout))
                        self._background_tasks.append(task)

                    await asyncio.sleep(11)
            else:
                for channel in channels:
                    task = asyncio.create_task(self._join_channel(channel, 11))
                    self._background_tasks.append(task)

    async def _join_channel(self, entry: str, timeout: int):
        channel = re.sub("[#]", "", entry).lower()
        await self.send(f"JOIN #{channel}\r\n")

        self._join_pending[channel] = fut = self._loop.create_future()
        self._background_tasks.append(asyncio.create_task(self._join_future_handle(fut, channel, timeout)))

    async def _join_future_handle(self, fut: asyncio.Future, channel: str, timeout: int):
        try:
            await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self.dispatch("channel_join_failure", channel)
            self._join_pending.pop(channel)

            data = (
                f":{self.nick}.tmi.twitch.tv 353 {self.nick} = #TWITCHIOFAILURE :{channel}\r\n"
                f":{self.nick}.tmi.twitch.tv 366 {self.nick} #TWITCHIOFAILURE :End of /NAMES list"
            )

            await self._process_data(data)

    async def _process_data(self, data: str):
        data = data.rstrip()
        parsed = parser(data, self.nick)

        if parsed["action"] == "PING":
            return await self._ping()
        elif parsed["code"] != 0:
            return await self._code(parsed, parsed["code"])
        elif data.startswith(":tmi.twitch.tv NOTICE * :Login unsuccessful"):
            log.error(
                f'Login unsuccessful with token "{self._token}". ' f'Check your scopes for "chat_login" and try again.'
            )
            return await self._close()
        partial_ = self._actions.get(parsed["action"])
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
        if code == 1:
            log.info(f"Successfully logged onto Twitch WS: {self.nick}")

            await self._await_futures()
            await self.is_ready.wait()
            self.dispatch("ready")
            self._init = True
        elif code == 353:
            if parsed["channel"] == "TWITCHIOFAILURE" and parsed["batches"][0] in self._initial_channels:
                self._initial_channels.remove(parsed["batches"][0])
            if parsed["channel"] in [c.lower().lstrip("#") for c in self._initial_channels] and not self._init:
                self._join_load[parsed["channel"]] = None
            if len(self._join_load) == len(self._initial_channels):
                for channel in self._initial_channels:
                    self._join_load.pop(channel.lower().lstrip("#"))
                    self._cache_add(parsed)
                self.is_ready.set()
            else:
                self._cache_add(parsed)
        elif code in {2, 3, 4, 366, 372, 375}:
            return
        elif code == 376:
            if not self._initial_channels:
                self.is_ready.set()
            return
        elif self.is_ready.is_set():
            return
        else:
            self.is_ready.set()
            # self.dispatch("ready")

    async def _ping(self, _=None):
        log.debug("ACTION: Sending PONG reply.")
        self._last_ping = time.time()
        await self.send("PONG :tmi.twitch.tv\r\n")

    async def _part(self, parsed):  # TODO
        log.debug(f'ACTION: PART:: {parsed["channel"]}')
        channel = parsed["channel"]

        if self._join_pending:
            try:
                self._join_pending[channel].set_result(None)
            except KeyError:
                pass
            else:
                self._join_pending.pop(channel)
        if not self._retain_cache:
            self._cache.pop(channel, None)
        channel = Channel(name=channel, websocket=self)
        user = Chatter(
            name=parsed["user"],
            bot=self._client,
            websocket=self,
            channel=channel,
            tags=parsed["badges"],
        )
        try:
            self._cache[channel.name].discard(user)
        except KeyError:
            pass
        self.dispatch("part", user)

    async def _privmsg(self, parsed):  # TODO(Update Cache properly)
        log.debug(f'ACTION: PRIVMSG:: {parsed["channel"]}')

        if parsed["channel"] is None:
            log.debug(f'ACTION: WHISPER:: {parsed["user"]}')
            channel = None
            user = WhisperChatter(websocket=self, name=parsed["user"])
        else:
            channel = Channel(name=parsed["channel"], websocket=self)
            self._cache_add(parsed)
            user = Chatter(
                tags=parsed["badges"],
                name=parsed["user"],
                channel=channel,
                bot=self._client,
                websocket=self,
            )
        message = Message(
            raw_data=parsed["data"],
            content=parsed["message"],
            author=user,
            channel=channel,
            tags=parsed["badges"],
            echo="echo" in parsed["action"],
        )

        self.dispatch("message", message)

    async def _privmsg_echo(self, parsed):
        log.debug(f'ACTION: PRIVMSG(ECHO):: {parsed["channel"]}')

        channel = Channel(name=parsed["channel"], websocket=self)
        message = Message(
            raw_data=parsed["data"],
            content=parsed["message"],
            author=None,
            channel=channel,
            tags={},
            echo=True,
        )

        self.dispatch("message", message)

    async def _userstate(self, parsed):
        log.debug(f'ACTION: USERSTATE:: {parsed["channel"]}')
        self._cache_add(parsed)

        channel = Channel(name=parsed["channel"], websocket=self)
        name = parsed["user"] or parsed["nick"]
        user = Chatter(
            tags=parsed["badges"],
            name=name,
            channel=channel,
            bot=self._client,
            websocket=self,
        )

        self.dispatch("userstate", user)

    async def _usernotice(self, parsed):
        log.debug(f'ACTION: USERNOTICE:: {parsed["channel"]}')

        channel = Channel(name=parsed["channel"], websocket=self)
        rawData = parsed["groups"][0]
        tags = dict(x.split("=", 1) for x in rawData.split(";"))
        tags["user-type"] = tags["user-type"].split(":tmi.twitch.tv")[0].strip()

        self.dispatch("raw_usernotice", channel, tags)

    async def _join(self, parsed):
        log.debug(f'ACTION: JOIN:: {parsed["channel"]}')
        channel = parsed["channel"]

        if self._join_pending:
            try:
                self._join_pending[channel].set_result(None)
            except KeyError:
                pass
            else:
                self._join_pending.pop(channel)
        if parsed["user"] != self._client.nick:
            self._cache_add(parsed)
        channel = Channel(name=channel, websocket=self)
        user = Chatter(
            name=parsed["user"],
            bot=self._client,
            websocket=self,
            channel=channel,
            tags=parsed["badges"],
        )

        if user.name == self._client.nick:
            self.dispatch("channel_joined", channel)
        self.dispatch("join", channel, user)

    def _cache_add(self, parsed: dict):
        channel = parsed["channel"].lstrip("#")

        if channel not in self._cache:
            self._cache[channel] = set()
        channel_ = Channel(name=channel, websocket=self)

        if parsed["batches"]:
            for u in parsed["batches"]:
                user = PartialChatter(name=u, bot=self._client, websocket=self, channel=channel_)
                self._cache[channel].add(user)
        else:
            name = parsed["user"] or parsed["nick"]
            user = Chatter(
                bot=self._client,
                name=name,
                websocket=self,
                channel=channel_,
                tags=parsed["badges"],
            )
            self._cache[channel].discard(user)
            self._cache[channel].add(user)

    async def _mode(self, parsed):  # TODO
        pass

    async def _reconnect(self, parsed):
        log.debug("ACTION: RECONNECT:: Twitch has gracefully closed the connection and will reconnect.")
        self._reconnect_requested = True
        self._keeper.cancel()
        self._loop.create_task(self._connect())
        self.dispatch("reconnect")

    def dispatch(self, event: str, *args, **kwargs):
        log.debug(f"Dispatching event: {event}")

        self._client.run_event(event, *args, **kwargs)

    async def event_error(self, error: Exception, data: str = None):
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def _fetch_futures(self):
        return [
            fut
            for chan, fut in self._join_pending.items()
            if chan.lower() in [re.sub("[#]", "", c).lower() for c in self._initial_channels]
        ]

    async def _close(self):
        self._keeper.cancel()

        if self._task_cleaner and not self._task_cleaner.done():
            self._task_cleaner.cancel()

        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        self.is_ready.clear()

        futures = self._fetch_futures()

        for fut in futures:
            fut.cancel()
        if self._websocket:
            await self._websocket.close()
        if self._client._http.session:
            await self._client._http.session.close()
