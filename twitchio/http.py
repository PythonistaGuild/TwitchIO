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
from typing import TYPE_CHECKING, Any

import aiohttp

from . import __version__
from .exceptions import TwichioHTTPException
from .utils import _from_json


if TYPE_CHECKING:
    from typing_extensions import Unpack

    from .types_ import APIRequest, HTTPMethod


logger: logging.Logger = logging.getLogger(__name__)


async def json_or_text(resp: aiohttp.ClientResponse) -> dict[str, Any] | str:
    text: str = await resp.text()

    try:
        if resp.headers["Content-Type"] == "application/json":
            return _from_json(text)  # type: ignore
    except KeyError:
        pass

    return text


class Route:
    # TODO: Document this class.

    BASE: str = "https://api.twitch.tv/helix/"
    ID_BASE: str = "https://id.twitch.tv/"

    def __init__(self, method: HTTPMethod, endpoint: str, *, use_id: bool = False, **kwargs: Unpack[APIRequest]) -> None:
        self.method = method

        endpoint = endpoint.removeprefix("/")
        self.endpoint = endpoint

        if use_id:
            self.url: str = self.ID_BASE + endpoint
        else:
            self.url: str = self.BASE + endpoint

        self.params: dict[str, str] = kwargs.pop("params", {})
        self.data: dict[str, Any] = kwargs.pop("data", {})
        self.json: dict[str, Any] = kwargs.pop("json", {})
        self.headers: dict[str, str] = kwargs.pop("headers", {})

    def __str__(self) -> str:
        return f"{self.method} /{self.endpoint}"


class HTTPClient:

    __slots__ = ("__session", "user_agent")

    def __init__(self) -> None:
        self.__session: aiohttp.ClientSession | None = None  # should be set on the first request

        # User Agent...
        pyver = f"{sys.version_info[0]}.{sys.version_info[1]}"
        ua = "TwitchioClient (https://github.com/PythonistaGuild/TwitchIO {0}) Python/{1} aiohttp/{2}"
        self.user_agent: str = ua.format(__version__, pyver, aiohttp.__version__)

    async def _init_session(self) -> None:
        if self.__session and not self.__session.closed:
            return

        logger.debug("Initialising a new session on HTTPClient.")
        self.__session = aiohttp.ClientSession()

    def clear(self) -> None:
        if self.__session and self.__session.closed:
            logger.debug("Clearing HTTPClient session. A new session will be created on the next request.")
            self.__session = None

    async def close(self) -> None:
        if self.__session and not self.__session.closed:
            try:
                await self.__session.close()
            except Exception as e:
                logger.debug("Ignoring exception caught while closing HTTPClient session: %s.", e)

            self.clear()
            logger.debug("HTTPClient session closed successfully.")

    async def request(self, method: HTTPMethod, endpoint: str, *, use_id: bool = False, **kwargs: Unpack[APIRequest]) -> dict[str, Any] | str:
        await self._init_session()
        assert self.__session is not None

        headers_ = kwargs.pop("headers", {})
        headers_.setdefault("User-Agent", self.user_agent)
        kwargs["headers"] = headers_

        route: Route = Route(method, endpoint, use_id=use_id, **kwargs)
        async with self.__session.request(method, route.url, **kwargs) as resp:
            data: dict[str, Any] | str = await json_or_text(resp)

            if resp.status >= 400:
                logger.error('Request %s failed with status %s: %s', route, resp.status, data)
                raise TwichioHTTPException(f"Request {route} failed with status {resp.status}: {data}", route=route)

        # TODO: This method is not complete. This is purely for testing purposes.
        return data
