"""MIT License

Copyright (c) 2017-2022 TwitchIO

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
import enum
import logging
from typing import Optional, Union

import aiohttp
import yarl
from aiohttp import web

from twitchio import Client, Channel


__all__ = ('EventSubClient', 'EventSubType')


class _EventSubTypeMeta(enum.Enum):

    @classmethod
    def all(cls) -> list:
        return [e.value for e in cls]


class EventSubType(_EventSubTypeMeta):

    ChannelFollows = {'topic': 'channel.follow', 'version': 1}


class EventSubClient(web.Application):

    def __init__(self,
                 *,
                 client_id: str,
                 client_secret: str,
                 host: Optional[str] = 'https://0.0.0.0',
                 port: Optional[int] = 4000,
                 webhook_callback: Optional[str] = '/callback',
                 ):
        super().__init__()

        callback = f'/{webhook_callback.removeprefix("/")}'

        host = yarl.URL(f'{host}:{port}')
        if host.scheme != 'https':
            raise RuntimeError('EventSubClient host parameter must use https, not http.')

        self._host = host

        routes = [web.post(callback, self._callback)]
        self.add_routes(routes)

        self._client_id = client_id
        self._client_secret = client_secret

        self._client: Client = None  # type: ignore
        self._client_ready = asyncio.Event()

    async def subscribe(self,
                        topics: Union[EventSubType, list[EventSubType]],
                        channels: list[Union[str, int, Channel]]
                        ) -> None:
        pass

    async def _callback(self, request: web.Request):
        pass

    async def _run(self) -> None:
        await self._client_ready.wait()

        runner = web.AppRunner(self)
        await runner.setup()

        site = web.TCPSite(runner, host=self._host.host, port=self._host.port)
        await site.start()
