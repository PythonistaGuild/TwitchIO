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

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from .authentication import ManagedHTTPClient, Scopes
from .web import AiohttpAdapter, WebAdapter


if TYPE_CHECKING:
    import aiohttp
    from typing_extensions import Self, Unpack

    from .types_.options import ClientOptions


class Client:
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        **options: Unpack[ClientOptions],
    ) -> None:
        redirect_uri: str | None = options.get("redirect_uri", None)
        scopes: Scopes | None = options.get("scopes", None)
        session: aiohttp.ClientSession | None = options.get("session", None)
        app_token: str | None = options.get("app_token", None)

        self._http = ManagedHTTPClient(
            client_id=client_id,
            client_secret=client_secret,
            app_token=app_token,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
        )

        adapter: type[WebAdapter] = options.get("adapter", None) or AiohttpAdapter
        self._adapter: WebAdapter = adapter(client=self)

        # TODO: Temp logic for testing...
        self._blocker: asyncio.Event = asyncio.Event()

    async def setup_hook(self) -> None: ...

    async def __aenter__(self) -> Self:
        if not self._http._app_token:
            payload = await self._http.client_credentials_token()
            self._http._app_token = payload.access_token

        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start(self, with_adapter: bool = True) -> None:
        # TODO: Temp logic for testing...
        await self.setup_hook()

        if with_adapter:
            self._adapter.run()

    async def block(self) -> None:
        # TODO: Temp METHOD for testing...

        await self._blocker.wait()

    async def close(self) -> None:
        await self._http.close()

        # TODO: Temp logic for testing...
        self._blocker.set()

    async def add_token(self, token: str, refresh: str) -> None:
        await self._http.add_token(token, refresh)
