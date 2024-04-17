"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

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

import asyncio
import logging

import aiohttp


logger: logging.Logger = logging.getLogger(__name__)


WSS: str = "wss://eventsub.wss.twitch.tv/ws"


class Websocket:
    def __init__(self, *, keep_alive_timeout: float = 60, session: aiohttp.ClientSession | None = None) -> None:
        self._keep_alive_timeout: int = max(10, min(int(keep_alive_timeout), 600))
        self._session: aiohttp.ClientSession | None = session
        self._reconnect: bool = True

        self._socket: aiohttp.ClientWebSocketResponse | None = None

        self._listen_task: asyncio.Task[None] | None = None

        self._id: str | None = None

    @property
    def keep_alive_timeout(self) -> int:
        return self._keep_alive_timeout

    @property
    def connected(self) -> bool:
        return bool(self._socket and not self._socket.closed)

    async def connect(self) -> None:
        url: str = f"{WSS}?keepalive_timeout_seconds={self._keep_alive_timeout}"

        if self.connected:
            logger.warning("Trying to connect to an already running conduit websocket with ID: %s.", self._id)
            return

        if not self._session:
            self._session = aiohttp.ClientSession()

        async with self._session as session:
            # TODO: Error handling...
            self._socket = await session.ws_connect(url)

        logger.debug("Successfully connected to conduit websocket... Preparing to assign to shard.")
        self._listen_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        assert self._socket

        while True:
            try:
                message = await self._socket.receive()
            except Exception:
                # TODO: Proper error handling...
                return await self.close()

            print(message)

    async def close(self) -> None:
        if self._socket:
            try:
                await self._socket.close()
            except Exception:
                ...

        if self._session:
            try:
                await self._session.close()
            except Exception:
                ...
