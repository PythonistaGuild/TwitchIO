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

import logging
import sys
from typing import TYPE_CHECKING, Any, ClassVar

import aiohttp

from . import __version__
from .exceptions import TwitchioHTTPException
from .utils import _from_json  # type: ignore


if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .types_.requests import APIRequest, APIRequestKwargs, HTTPMethod


logger: logging.Logger = logging.getLogger(__name__)


async def json_or_text(resp: aiohttp.ClientResponse) -> dict[str, Any] | str:
    text: str = await resp.text()

    try:
        if resp.headers["Content-Type"].startswith("application/json"):
            return _from_json(text)  # type: ignore
    except KeyError:
        pass

    return text


class Route:
    # TODO: Document this class.

    BASE: ClassVar[str] = "https://api.twitch.tv/helix/"
    ID_BASE: ClassVar[str] = "https://id.twitch.tv/"

    def __init__(
        self, method: HTTPMethod, path: str, *, use_id: bool = False, **kwargs: Unpack[APIRequestKwargs]
    ) -> None:
        params: dict[str, str] = kwargs.pop("params", {})
        self._url = self.build_url(path, use_id=use_id, params=params)

        self.use_id = use_id
        self.method = method
        self.path = path

        self.params: dict[str, str] = params
        self.data: dict[str, Any] = kwargs.get("data", {})
        self.json: dict[str, Any] = kwargs.get("json", {})
        self.headers: dict[str, str] = kwargs.get("headers", {})

        self.packed: APIRequest = kwargs

    def __str__(self) -> str:
        return str(self._url)

    def __repr__(self) -> str:
        return f"{self.method}({self.path})"

    @classmethod
    def build_url(cls, path: str, use_id: bool = False, params: dict[str, str] = {}) -> str:
        path_: str = path.lstrip("/")

        url: str = f"{cls.ID_BASE if use_id else cls.BASE}{path_}{cls.build_query(params)}"
        return url

    def update_query(self, params: dict[str, str]) -> str:
        self.params.update(params)
        self.build_url(self.path, use_id=self.use_id, params=self.params)

        return self._url

    @property
    def url(self) -> str:
        return str(self._url)

    @classmethod
    def build_query(cls, params: dict[str, str]) -> str:
        joined: str = "&".join(f"{key}={value}" for key, value in params.items())
        return f"?{joined}" if joined else ""


class HTTPClient:
    __slots__ = ("__session", "user_agent")

    def __init__(self) -> None:
        self.__session: aiohttp.ClientSession | None = None  # should be set on the first request

        # User Agent...
        pyver = f"{sys.version_info[0]}.{sys.version_info[1]}"
        ua = "TwitchioClient (https://github.com/PythonistaGuild/TwitchIO {0}) Python/{1} aiohttp/{2}"
        self.user_agent: str = ua.format(__version__, pyver, aiohttp.__version__)

    @property
    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent}

    async def _init_session(self) -> None:
        if self.__session and not self.__session.closed:
            return

        logger.debug("Initialising a new session on %s.", self.__class__.__qualname__)
        self.__session = aiohttp.ClientSession(headers=self.headers)

    def clear(self) -> None:
        if self.__session and self.__session.closed:
            logger.debug(
                "Clearing %s session. A new session will be created on the next request.", self.__class__.__qualname__
            )
            self.__session = None

    async def close(self) -> None:
        if self.__session and not self.__session.closed:
            try:
                await self.__session.close()
            except Exception as e:
                logger.debug("Ignoring exception caught while closing %s session: %s.", self.__class__.__qualname__, e)

            self.clear()
            logger.debug("%s session closed successfully.", self.__class__.__qualname__)

    async def request(self, route: Route) -> Any:
        await self._init_session()
        assert self.__session is not None

        logger.debug("Attempting a request to %r with %s.", route, self.__class__.__qualname__)

        async with self.__session.request(route.method, route.url, **route.packed) as resp:
            data: dict[str, Any] | str = await json_or_text(resp)

            if resp.status >= 400:
                logger.error("Request %r failed with status %s: %s", route, resp.status, data)
                raise TwitchioHTTPException(
                    f"Request {route} failed with status {resp.status}: {data}", route=route, status=resp.status
                )

        # TODO: This method is not complete. This is purely for testing purposes.
        return data

    async def request_json(self, route: Route) -> Any:
        data = await self.request(route)

        if isinstance(data, str):
            # TODO: Add a TwitchioHTTPException here.
            raise TypeError("Expected JSON data, but received text data.")

        return data
