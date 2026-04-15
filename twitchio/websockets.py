"""MIT License

Copyright (c) 2025 - Present Evie. P., Chillymosh and TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import sys
import threading
import time
from collections import deque
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict, no_type_check

from picows import WSCloseCode, WSFrame, WSListener, WSMsgType, WSTransport, ws_connect  # type: ignore

from .backoff import Backoff
from .utils import JSON_LOADS, MISSING


if TYPE_CHECKING:
    from .http import HTTPClient
    from .types_.eventsub import (
        KeepAliveMessage,
        MessageTypes,
        MetaData,
        NotificationMessage,
        ReconnectMessage,
        RevocationMessage,
        WelcomeMessage,
    )


__all__ = ("FrameListener", "Websocket", "WebsocketManager", "WebsocketWatcher")


LOGGER: logging.Logger = logging.getLogger(__name__)
PY_314: bool = sys.version_info >= (3, 14)
WSS_URL: str = "wss://eventsub.wss.twitch.tv/ws"


class Thing(TypedDict):
    notfication: NotificationMessage
    session_keepalive: KeepAliveMessage
    session_reconnect: ReconnectMessage
    session_welcome: WelcomeMessage
    revocation: RevocationMessage


class WebsocketManager:
    def __init__(self, http: HTTPClient, *, max_retries: int | None = None) -> None:
        self._http = http
        self._max_retries = max_retries
        self._sockets: dict[str | int, Websocket] = {}

    @property
    def sockets(self) -> MappingProxyType[str | int, Websocket]:
        return MappingProxyType(self._sockets)

    def get_socket(self) -> WebsocketWatcher: ...

    async def reconnect_socket(self, socket: Websocket) -> ...:
        # TODO: Handle subscriptions...
        shard_id = socket.shard_id
        socket._watcher.stop()
        await socket.close()

        if not socket._can_reconnect:
            self._sockets.pop(str(socket._shard_id or socket.session_id), None)
            return

        backoff = Backoff()
        tries = 0

        while self._max_retries is None or tries < self._max_retries:
            try:
                await self.open_socket(shard_id=shard_id)
            except Exception as e:
                LOGGER.debug("An error occurred reconnecting %r. %s", socket, e)
            else:
                LOGGER.info("%r was successfully reconnected.", socket)
                break

            tries += 1
            delay = backoff.calculate()

            await asyncio.sleep(delay)

    async def open_socket(self, *, shard_id: int | None = None) -> ...:
        watcher = WebsocketWatcher(self)
        ws = Websocket(watcher, shard_id=shard_id)
        watcher._socket = ws

        await ws.connect()
        await ws.wait_for_welcome()
        watcher.start()

        self._sockets[str(shard_id or ws.session_id)] = ws

    async def batch_open(self) -> ...: ...

    async def close_socket(self) -> ...: ...

    async def batch_close(self) -> ...: ...

    async def shutdown(self) -> ...: ...


class WebsocketWatcher(threading.Thread):
    _socket: Websocket
    DAEMON: ClassVar[bool] = True
    MIN_KEEP_ALIVE: ClassVar[int] = 10

    BEHIND_MSG: ClassVar[str] = "%r can't keep up. Average %.1fs behind in the past %d RTT rounds."
    BLOCK_MSG: ClassVar[str] = "%r has been blocked for %.1fs. Consider checking your application for synchronous blocking."
    FAILED_MSG: ClassVar[str] = "%r is not responding. Attempting to recover connection."

    def __init__(self, manager: WebsocketManager) -> None:
        super().__init__(daemon=self.DAEMON)

        self._manager = manager
        self._interval: int = 3
        self._last_update: int = time.perf_counter_ns()
        self._should_stop = threading.Event()
        self._last_log: datetime.datetime | None = None
        self._recent_rtt: deque[float] = deque(maxlen=5)

    def __repr__(self) -> str: ...

    def run(self) -> None:
        keep_alive = self._socket._keep_alive + 0.1

        while not self._should_stop.wait(self._interval):
            dist = (time.perf_counter_ns() - self._last_update) / 1e9

            if dist > keep_alive:
                self.notify(self.FAILED_MSG, self._socket, force=True)
                self.reconnect_socket()
                continue

            if self._recent_rtt:
                avg_rtt = sum(self._recent_rtt) / len(self._recent_rtt)
                if avg_rtt > 3:
                    self.notify(self.BEHIND_MSG, self._socket, avg_rtt, len(self._recent_rtt))

            total = 0
            while True:
                if total > keep_alive:
                    self.notify(self.FAILED_MSG, self._socket, force=True)
                    self.reconnect_socket()
                    break

                elif total > 0:
                    self.notify(self.BLOCK_MSG, self._socket, total)

                try:
                    future = asyncio.run_coroutine_threadsafe(self._socket.poll(), self._socket._loop)
                    result = future.result(self._interval)
                    self._recent_rtt.append(result)
                    break
                except TimeoutError:
                    total += self._interval
                    continue
                except asyncio.CancelledError:
                    # TODO
                    continue
                except Exception:
                    self.stop()
                    break

    def reconnect_socket(self) -> None:
        asyncio.run_coroutine_threadsafe(self._manager.reconnect_socket(self._socket), self._socket._loop)
        self.stop()

    def stop(self) -> None:
        self._should_stop.set()

    def update(self) -> None:
        now = time.perf_counter_ns()
        self._last_ack = now
        self._last_update = now

    def notify(self, msg: str, /, *args: Any, **kwargs: Any) -> None:
        now = datetime.datetime.now()

        level = kwargs.get("level", logging.WARNING)
        force = kwargs.get("force", False)

        if not force and self._last_log is not None and self._last_log >= (now - datetime.timedelta(seconds=5)):
            return

        self._last_log = now
        LOGGER.log(level, msg, *args)


class FrameListener(WSListener):
    def __init__(self, socket: Websocket, /) -> None:
        self._socket = socket
        self._watcher = socket._watcher
        self._loop = socket._loop
        self._eager = self.has_eager()

        self._tasks: set[asyncio.Task[None]] = set()

    def has_eager(self) -> bool:
        if PY_314:
            return True

        return self._loop.get_task_factory() == asyncio.eager_task_factory

    @no_type_check  # asyncio has bad typing for the tasks in 3.14
    def on_ws_frame(self, transport: WSTransport, frame: WSFrame) -> None:
        if frame.msg_type is WSMsgType.PING:
            transport.send_pong(frame.get_payload_as_bytes())
            return

        if not self._eager:
            return self._on_ws_frame(transport, frame)

        eager = self._eager_on_ws_frame(transport, frame)
        t = asyncio.create_task(eager, eager_start=True) if PY_314 else asyncio.create_task(eager)

        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def _eager_on_ws_frame(self, transport: WSTransport, frame: WSFrame) -> None:
        # NOTE: It would be faster to NOT create an eager task and await here, however;
        # if we dispatch events as an eager task the user would need to ensure they await
        # in each subscribed event at some point, otherwise the websocket will block the event loop.
        if frame.msg_type is WSMsgType.TEXT:
            self._watcher.update()

            data = JSON_LOADS(frame.get_payload_as_bytes())
            await self._socket.receive_message(data)

        elif frame.msg_type is WSMsgType.CLOSE:
            await self.on_close_code(transport, frame.get_close_code())

    def _on_ws_frame(self, transport: WSTransport, frame: WSFrame) -> None:
        t: asyncio.Task[None] | None = None

        if frame.msg_type is WSMsgType.TEXT:
            self._watcher.update()

            data = JSON_LOADS(frame.get_payload_as_bytes())
            t = asyncio.create_task(self._socket.receive_message(data))

        elif frame.msg_type is WSMsgType.CLOSE:
            t = asyncio.create_task(self.on_close_code(transport, frame.get_close_code()))

        if t is None:
            return

        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    async def on_close_code(self, transport: WSTransport, code: WSCloseCode) -> ...:
        print(code.value)


class Websocket:
    _listener: FrameListener
    _transport: WSTransport

    MIN_KEEP_ALIVE: ClassVar[int] = 10
    MAX_KEEP_ALIVE: ClassVar[int] = 600

    def __init__(self, watcher: WebsocketWatcher, /, *, shard_id: int | None = None, keep_alive_timeout: int = 10) -> None:
        self._watcher = watcher
        self._loop = asyncio.get_event_loop()
        self._welcomed = asyncio.Event()

        self._keep_alive = max(self.MIN_KEEP_ALIVE, min(keep_alive_timeout, self.MAX_KEEP_ALIVE))
        if self._keep_alive != keep_alive_timeout:
            LOGGER.warning("'keep_alive_timeout' for %r was out of bounds. Setting timeout to: %s", self, self._keep_alive)

        self._shard_id = shard_id
        self._is_conduit = shard_id is not None
        self._session_id: str = MISSING

        self._can_reconnect: bool = True

    def __repr__(self) -> str:
        return f"Websocket(shard_id={self._shard_id})"

    def __str__(self) -> str: ...

    @property
    def watcher(self) -> WebsocketWatcher:
        return self._watcher

    @property
    def shard_id(self) -> int | None:
        return self._shard_id

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def keep_alive_timeout(self) -> int:
        return self._keep_alive

    def listener_factory(self) -> FrameListener:
        listener = FrameListener(self)
        return listener

    async def connect(self) -> ...:
        transport, listener = await ws_connect(self.listener_factory, WSS_URL, enable_auto_pong=False)

        self._listener = listener  # type: ignore
        self._transport = transport

    async def close(self) -> ...: ...

    async def receive_message(self, data: Any) -> ...:
        metadata: MetaData = data["metadata"]
        message_type: MessageTypes = metadata["message_type"]

        if message_type == "notification":
            notification: NotificationMessage = data
            LOGGER.debug("%r received notification message: %s", self, notification)

        elif message_type == "session_keepalive":
            keepalive: KeepAliveMessage = data
            LOGGER.debug("%r received keepalive message: %s", self, keepalive)
            self._watcher.update()

        elif message_type == "session_reconnect":
            reconnect: ReconnectMessage = data
            LOGGER.debug("%r received reconnect message: %s", self, reconnect)

        elif message_type == "session_welcome":
            welcome: WelcomeMessage = data
            LOGGER.debug("%r received welcome message: %s", self, welcome)
            self._welcomed.set()

        elif message_type == "revocation":
            revocation: RevocationMessage = data
            LOGGER.debug("%r received revocation message: %s", self, revocation)

    async def wait_for_welcome(self) -> None:
        await self._welcomed.wait()

    async def poll(self) -> float:
        rts = await self._transport.measure_roundtrip_time(1)
        return rts[0]
