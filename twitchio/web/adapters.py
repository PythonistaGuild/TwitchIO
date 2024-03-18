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
import logging
from typing import TYPE_CHECKING, TypeAlias
from urllib.parse import unquote_plus

import uvicorn
from aiohttp import web
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


class StarletteAdapter(Starlette):
    def __init__(self, client: Client, *, host: str | None = None, port: int | None = None) -> None:
        self.client: Client = client

        self._host: str = host or "localhost"
        self._port: int = port or 4343

        self._runner_task: asyncio.Task[None] | None = None
        self._redirect_uri: str = client._http.redirect_uri or f"http://{self._host}:{self._port}/oauth/callback"

        super().__init__(
            routes=[
                Route("/oauth/callback", self.oauth_callback, methods=["GET"]),
                Route("/oauth", self.oauth_redirect, methods=["GET"]),
            ],
            on_shutdown=[self.event_shutdown],
            on_startup=[self.event_startup],
        )

    async def event_startup(self) -> None:
        logger.info("Starting TwitchIO StarletteAdapter on http://%s:%s.", self._host, self._port)

    async def event_shutdown(self) -> None:
        await self.close()

    async def close(self) -> None:
        if self._runner_task is not None:
            try:
                self._runner_task.cancel()
            except Exception as e:
                logger.debug(
                    "Ignoring exception raised while cancelling runner in <%s>: %s.",
                    self.__class__.__qualname__,
                    e,
                )

        self._runner_task = None
        await self.client.close()

        logger.info("Successfully shutdown TwitchIO <%s>.", self.__class__.__qualname__)

    async def run(self, host: str | None = None, port: int | None = None) -> None:
        self._host = host or self._host
        self._port = port or self._port

        config: uvicorn.Config = uvicorn.Config(app=self, host=self._host, port=self._port, log_level="critical")
        server: uvicorn.Server = uvicorn.Server(config)

        self._runner_task = asyncio.create_task(
            server.serve(), name=f"twitchio-web-adapter:{self.__class__.__qualname__}"
        )

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
        scopes: str | None = request.query_params.get("scopes", None)
        force_verify: bool = request.query_params.get("force_verify", "false").lower() == "true"

        if not scopes:
            scopes = str(self.client._http.scopes) if self.client._http.scopes else None

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
                force_verify=force_verify,
            )
        except Exception as e:
            logger.error(
                "Exception raised while fetching Authorization URL in <%s>: %s", self.__class__.__qualname__, e
            )
            return Response(status_code=500)

        return RedirectResponse(url=payload["url"], status_code=307)


class AiohttpAdapter(web.Application):
    def __init__(self, client: Client, *, host: str | None = None, port: int | None = None) -> None:
        super().__init__()
        self._runner: web.AppRunner | None = None

        self.client: Client = client

        self._host: str = host or "localhost"
        self._port: int = port or 4343

        self._runner_task: asyncio.Task[None] | None = None
        self._redirect_uri: str = client._http.redirect_uri or f"http://{self._host}:{self._port}/oauth/callback"

        self.startup = self.event_startup
        self.shutdown = self.event_shutdown

        self.router.add_route("GET", "/oauth/callback", self.oauth_callback)
        self.router.add_route("GET", "/oauth", self.oauth_redirect)

    def __init_subclass__(cls: type[AiohttpAdapter]) -> None:
        return

    async def event_startup(self) -> None:
        logger.info("Starting TwitchIO AiohttpAdapter on http://%s:%s.", self._host, self._port)

    async def event_shutdown(self) -> None:
        logger.info("Successfully shutdown TwitchIO <%s>.", self.__class__.__qualname__)

    async def close(self) -> None:
        if self._runner_task is not None:
            try:
                self._runner_task.cancel()
            except Exception as e:
                logger.debug(
                    "Ignoring exception raised while cancelling runner in <%s>: %s.",
                    self.__class__.__qualname__,
                    e,
                )

        if self._runner is not None:
            await self._runner.cleanup()

        self._runner = None
        self._runner_task = None

    async def run(self, host: str | None = None, port: int | None = None) -> None:
        self._runner = web.AppRunner(self, access_log=None, handle_signals=True)
        await self._runner.setup()

        site: web.TCPSite = web.TCPSite(self._runner, host or self._host, port or self._port)
        self._runner_task = asyncio.create_task(
            site.start(), name=f"twitchio-web-adapter:{self.__class__.__qualname__}"
        )

    async def fetch_token(self, request: web.Request) -> web.Response:
        if "code" not in request.query:
            return web.Response(status=400)

        try:
            payload: UserTokenPayload = await self.client._http.user_access_token(
                request.query["code"],
                redirect_uri=self._redirect_uri,
            )
        except Exception as e:
            logger.error("Exception raised while fetching Token in <%s>: %s", self.__class__.__qualname__, e)
            return web.Response(status=500)

        await self.client.add_token(payload["access_token"], payload["refresh_token"])
        return web.Response(body="Success. You can leave this page.", status=200)

    async def oauth_callback(self, request: web.Request) -> web.Response:
        logger.debug("Received OAuth callback request in <%s>.", self.oauth_callback.__qualname__)

        response: web.Response = await self.fetch_token(request)
        return response

    async def oauth_redirect(self, request: web.Request) -> web.Response:
        scopes: str | None = request.query.get("scopes", None)
        force_verify: bool = request.query.get("force_verify", "false").lower() == "true"

        if not scopes:
            scopes = str(self.client._http.scopes) if self.client._http.scopes else None

        if not scopes:
            logger.warning(
                "No scopes provided in request to <%s>. Scopes are a required parameter that is missing.",
                self.oauth_redirect.__qualname__,
            )
            return web.Response(status=400)

        scopes_: Scopes = Scopes(unquote_plus(scopes).split())

        try:
            payload: AuthorizationURLPayload = self.client._http.get_authorization_url(
                scopes=scopes_,
                redirect_uri=self._redirect_uri,
                force_verify=force_verify,
            )
        except Exception as e:
            logger.error(
                "Exception raised while fetching Authorization URL in <%s>: %s", self.__class__.__qualname__, e
            )
            return web.Response(status=500)

        raise web.HTTPPermanentRedirect(payload["url"])


WebAdapter: TypeAlias = StarletteAdapter | AiohttpAdapter
