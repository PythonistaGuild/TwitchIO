"""MIT License

Copyright (c) 2017-2021 TwitchIO

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
import typing

import aiohttp
import logging


logger = logging.getLogger(__name__)

HOST = 'wss://irc-ws.chat.twitch.tv:443'


class Websocket:

    def __init__(self,
                 heartbeat: typing.Optional[float] = 30.0
                 ):
        self.ws: aiohttp.ClientWebSocketResponse = None  # type: ignore
        self.heartbeat: float = heartbeat

        self._keep_alive_task: asyncio.Task = None  # type: ignore

    def is_connected(self) -> bool:
        return self.ws is not None and not self.ws.closed

    async def _connect(self):
        if self.is_connected():
            await self.ws.close()

        if self._keep_alive_task:
            try:
                self._keep_alive_task.cancel()
            except Exception as e:
                logger.debug(e)

            self._keep_alive_task = None

        async with aiohttp.ClientSession() as session:
            self.ws = await session.ws_connect(url=HOST, heartbeat=self.heartbeat)
            session.detach()

        self._keep_alive_task = asyncio.create_task(self._keep_alive())

    async def _keep_alive(self):
        pass