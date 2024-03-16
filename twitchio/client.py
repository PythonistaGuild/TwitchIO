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

    from .authentication import ClientCredentialsPayload
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

        self._http = ManagedHTTPClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
        )

        adapter: type[WebAdapter] = options.get("adapter", None) or AiohttpAdapter
        self._adapter: WebAdapter = adapter(client=self)

        # TODO: Temp logic for testing...
        self._blocker: asyncio.Event = asyncio.Event()

    async def setup_hook(self) -> None: ...

    async def login(self, *, token: str | None = None) -> None:
        if not token:
            payload: ClientCredentialsPayload = await self._http.client_credentials_token()
            token = payload.access_token

        self._http._app_token = token
        await self.setup_hook()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start(self, token: str | None = None, *, with_adapter: bool = True) -> None:
        await self.login(token=token)

        if with_adapter:
            await self._adapter.run()

        await self._block()

    async def _block(self) -> None:
        # TODO: Temp METHOD for testing...

        try:
            await self._blocker.wait()
        except KeyboardInterrupt:
            await self.close()

    async def close(self) -> None:
        await self._http.close()

        if self._adapter._runner_task is not None:
            try:
                await self._adapter.close()
            except Exception:
                pass

        # TODO: Temp logic for testing...
        self._blocker.set()

    async def add_token(self, token: str, refresh: str) -> None:
        await self._http.add_token(token, refresh)
