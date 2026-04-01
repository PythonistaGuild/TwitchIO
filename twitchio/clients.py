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

import asyncio
from typing import Any, Self

from .dispatcher import EventDispatcher
from .http import HTTPClient
from .websockets import WebsocketManager


class Client:
    def __init__(self) -> None:
        self._http = HTTPClient()
        self._events = EventDispatcher()
        self._sockets = WebsocketManager(http=self._http)

        self.__stop_event = asyncio.Event()
        self._closed: bool = False

    @property
    def dispatcher(self) -> EventDispatcher:
        return self._events

    @property
    def http(self) -> HTTPClient:
        return self._http

    def __repr__(self) -> str:
        return "Client()"

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    def run(self) -> None:
        async def runner() -> None:
            async with self:
                await self.start()

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass

    async def start(self) -> None:
        await self.__stop_event.wait()

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True


class ManagedClient(Client): ...
