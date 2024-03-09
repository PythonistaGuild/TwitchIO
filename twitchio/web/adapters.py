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

import abc
import asyncio
import logging
from typing import TYPE_CHECKING, TypeAlias
from urllib.parse import unquote_plus

import uvicorn
from starlette.applications import Starlette
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route

from ..authentication import Scopes


if TYPE_CHECKING:
    from starlette.requests import Request

    from ..authentication import AuthorizationURLPayload, UserTokenPayload
    from ..client import Client


__all__ = ("WebAdapter", "StarletteAdapter", "AiohttpAdapter")


logger: logging.Logger = logging.getLogger(__name__)


class BaseAdapterMeta(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, host: str | None = None, port: int | None = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def fetch_token(self, request: Request) -> Response:
        raise NotImplementedError

    @abc.abstractmethod
    async def oauth_callback(self, request: Request) -> Response:
        raise NotImplementedError

    @abc.abstractmethod
    async def oauth_redirect(self, request: Request) -> Response:
        raise NotImplementedError


class StarletteAdapter(Starlette, BaseAdapterMeta):
    def __init__(self, *, client: Client) -> None:
        self.client: Client = client

        self._host: str = "localhost"
        self._port: int = 4343
        self._runner: asyncio.Task[None] | None = None
        self._redirect_uri: str = client._http.redirect_uri or f"http://{self._host}:{self._port}/oauth/callback"

        super().__init__(
            routes=[
                Route("/oauth/callback", self.oauth_callback, methods=["GET"]),
                Route("/oauth", self.oauth_redirect, methods=["GET"]),
            ],
            on_shutdown=[self.on_shutdown],
            on_startup=[self.on_startup],
        )

    async def on_startup(self) -> None:
        logger.info("Starting TwitchIO StarletteAdapter on http://%s:%s.", self._host, self._port)

    async def on_shutdown(self) -> None:
        if self._runner is not None:
            try:
                self._runner.cancel()
            except Exception as e:
                logger.debug(
                    "Ignoring exception raised while cancelling runner in <%s>: %s.", self.__class__.__qualname__, e
                )

        self._runner = None
        await self.client.close()

    def run(self, host: str | None = None, port: int | None = None) -> None:
        self._host = host or self._host
        self._port = port or self._port

        config: uvicorn.Config = uvicorn.Config(app=self, host=self._host, port=self._port, log_level="critical")
        server: uvicorn.Server = uvicorn.Server(config)

        self._runner = asyncio.create_task(server.serve(), name=f"twitchio-web-adapter:{self.__class__.__qualname__}")

    async def fetch_token(self, request: Request) -> Response:
        if "code" not in request.query_params:
            return Response(status_code=400)

        try:
            payload: UserTokenPayload = await self.client._http.user_access_token(
                request.query_params["code"],
                redirect_uri=self._redirect_uri,
            )
        except Exception as e:
            logger.error("Exception raised while fetching Token in <%s>: %s", self.__class__.__qualname__, e)
            return Response(status_code=500)

        await self.client.add_token(payload["access_token"], payload["refresh_token"])
        return Response("Success. You can leave this page.", status_code=200)

    async def oauth_callback(self, request: Request) -> Response:
        logger.debug("Received OAuth callback request in <%s>.", self.oauth_callback.__qualname__)

        response: Response = await self.fetch_token(request)
        return response

    async def oauth_redirect(self, request: Request) -> Response:
        scopes: str | None = request.query_params.get("scopes", None) or str(self.client._http.scopes)

        if not scopes:
            logger.warning(
                "No scopes provided in request to <%s>. Scopes are a required parameter that is missing.",
                self.oauth_redirect.__qualname__,
            )
            return Response(status_code=400)

        scopes_: Scopes = Scopes(unquote_plus(scopes).split())

        try:
            payload: AuthorizationURLPayload = self.client._http.get_authorization_url(
                scopes=scopes_,
                redirect_uri=self._redirect_uri,
            )
        except Exception as e:
            logger.error(
                "Exception raised while fetching Authorization URL in <%s>: %s", self.__class__.__qualname__, e
            )
            return Response(status_code=500)

        return RedirectResponse(url=payload["url"], status_code=307)


class AiohttpAdapter(BaseAdapterMeta):
    def __init__(self, client: Client) -> None:
        self.client: Client = client

    def run(self, host: str | None = None, port: int | None = None) -> None: ...

    async def fetch_token(self, request: Request) -> Response: ...

    async def oauth_callback(self, request: Request) -> Response: ...

    async def oauth_redirect(self, request: Request) -> Response: ...


WebAdapter: TypeAlias = StarletteAdapter | AiohttpAdapter
