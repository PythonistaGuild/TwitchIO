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
import logging
import sys
import threading
import time
from types import MappingProxyType
from typing import Any, ClassVar, no_type_check

from picows import WSCloseCode, WSFrame, WSListener, WSMsgType, WSTransport, ws_connect

from .utils import JSON_LOADS


__all__ = ("FrameListener", "Websocket", "WebsocketManager", "WebsocketWatcher")


LOGGER: logging.Logger = logging.getLogger(__name__)
PY_314: bool = sys.version_info >= (3, 14)
WSS_URL: str = "wss://eventsub.wss.twitch.tv/ws"


class WebsocketManager:
    def __init__(self) -> None:
        self._sockets: dict[str | int, Websocket] = {}

    @property
    def sockets(self) -> MappingProxyType[str | int, Websocket]:
        return MappingProxyType(self._sockets)

    def get_socket(self) -> WebsocketWatcher: ...

    async def open_socket(self, *, shard_id: int | None = None) -> ...:
        watcher = WebsocketWatcher()
        ws = Websocket(watcher, shard_id=shard_id)
        watcher._socket = ws

        try:
            await ws.connect()
        except Exception:
            return

        watcher.start()

    async def batch_open(self) -> ...: ...

    async def close_socket(self) -> ...: ...

    async def batch_close(self) -> ...: ...

    async def shutdown(self) -> ...: ...


class WebsocketWatcher(threading.Thread):
    _socket: Websocket
    DAEMON: ClassVar[bool] = True
    MIN_KEEP_ALIVE: ClassVar[int] = 10

    SLOW_MSG: ClassVar[str] = "%r performance is degraded. RTT took %s seconds. Check your network for degradation."
    BEHIND_MSG: ClassVar[str] = (
        "%r can't keep up. %s seconds behind. Check your network; and your application for synchronous blocking."
    )
    FAILED_MSG: ClassVar[str] = "%r failed: Too Far Behind (%s seconds behind). Attempting to recover connection."

    def __init__(self) -> None:
        super().__init__(daemon=self.DAEMON)

        self._last_ack: int = time.perf_counter_ns()
        self._last_update: int = time.perf_counter_ns()
        self._should_stop = threading.Event()

    def __repr__(self) -> str: ...

    def run(self) -> None:
        keep_alive = self._socket._keep_alive + 1

        while not self._should_stop.is_set():
            dist = (time.perf_counter_ns() - self._last_update) / 1e9
            if dist > keep_alive:
                self.notify(self.FAILED_MSG, self._socket, dist)
                self.stop()
                continue

            try:
                future = asyncio.run_coroutine_threadsafe(self._socket.poll(), self._socket._loop)
                result = future.result(self.MIN_KEEP_ALIVE)
            except TimeoutError:
                continue

            if not self.ack(update=False) and result >= 0.5:
                self.notify(self.SLOW_MSG, self._socket, result)

            self.ack()

    def stop(self) -> None:
        self._should_stop.set()

    def ack(self, update: bool = True) -> None | bool:
        if update:
            self._last_ack = time.perf_counter_ns()
            return

        dist = (time.perf_counter_ns() - self._last_ack) / 1e9
        if dist >= 1:
            self.notify(self.BEHIND_MSG, self._socket, dist)
            return True

    def update(self) -> None:
        now = time.perf_counter_ns()
        self._last_ack = now
        self._last_update = now

    def notify(self, msg: str, /, *args: Any, **kwargs: Any) -> None:
        level = kwargs.get("level", logging.WARNING)
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
        self._watcher.ack()

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

        self._keep_alive = max(self.MIN_KEEP_ALIVE, min(keep_alive_timeout, self.MAX_KEEP_ALIVE))
        if self._keep_alive != keep_alive_timeout:
            LOGGER.warning("'keep_alive_timeout' for %r was out of bounds. Setting timeout to: %s", self, self._keep_alive)

        self._shard_id = shard_id
        self._is_conduit = shard_id is not None

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
    def keep_alive(self) -> int:
        return self._keep_alive

    def listener_factory(self) -> FrameListener:
        listener = FrameListener(self)
        return listener

    async def connect(self) -> ...:
        transport, listener = await ws_connect(self.listener_factory, WSS_URL, enable_auto_pong=False)

        self._listener = listener  # type: ignore
        self._transport = transport

    async def close(self) -> ...: ...

    async def receive_message(self, data: ...) -> ...:
        print(f"MESSAGE: {data}")

    async def poll(self) -> float:
        rts = await self._transport.measure_roundtrip_time(1)
        return rts[0]
