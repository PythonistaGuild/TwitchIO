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

import copy
import logging
import sys
import urllib.parse
from collections import deque
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeAlias, TypeVar

import aiohttp

from . import __version__
from .exceptions import HTTPException
from .utils import _from_json  # type: ignore


if TYPE_CHECKING:
    from collections.abc import Generator

    from typing_extensions import Self, Unpack

    from .types_.requests import APIRequestKwargs, HTTPMethod, ParamMapping
    from .types_.responses import RawResponse


logger: logging.Logger = logging.getLogger(__name__)


T = TypeVar("T")
PaginatedConverter: TypeAlias = Callable[[Any], Awaitable[T]] | None


async def json_or_text(resp: aiohttp.ClientResponse) -> dict[str, Any] | str:
    text: str = await resp.text()

    try:
        if resp.headers["Content-Type"].startswith("application/json"):
            return _from_json(text)  # type: ignore
    except KeyError:
        pass

    return text


class Route:
    __slots__ = ("params", "data", "json", "headers", "use_id", "method", "path", "packed", "_base_url", "_url")

    BASE: ClassVar[str] = "https://api.twitch.tv/helix/"
    ID_BASE: ClassVar[str] = "https://id.twitch.tv/"

    def __init__(
        self,
        method: HTTPMethod,
        path: str,
        *,
        use_id: bool = False,
        **kwargs: Unpack[APIRequestKwargs],
    ) -> None:
        self.params: ParamMapping = kwargs.pop("params", {})
        self.json: dict[str, Any] = kwargs.get("json", {})
        self.headers: dict[str, str] = kwargs.get("headers", {})

        self.use_id = use_id
        self.method = method
        self.path = path

        self._base_url: str = ""
        self._url: str = self.build_url()

    def __str__(self) -> str:
        return str(self._url)

    def __repr__(self) -> str:
        return f"{self.method}[{self.base_url}]"

    def build_url(self, *, remove_none: bool = True) -> str:
        base = self.ID_BASE if self.use_id else self.BASE
        self.path = self.path.lstrip("/").rstrip("/")

        url: str = f"{base}{self.path}"
        self._base_url = url

        if not self.params:
            return url

        url += "?"

        # We expect a dict so keys should be unique...
        for key, value in copy.copy(self.params).items():
            if value is None:
                if remove_none:
                    del self.params[key]
                continue

            if isinstance(value, (str, int)):
                url += f'{key}={self.encode(str(value), safe="+", plus=True)}&'
            else:
                # At this point we should assume it's a list or tuple...
                # If it's not that's ultimately on us...
                joined: str = "+".join([self.encode(str(v), safe="+") for v in value])
                url += f"{key}={joined}&"

        return url.rstrip("&")

    @classmethod
    def encode(cls, value: str, /, safe: str = "", plus: bool = False) -> str:
        method = urllib.parse.quote_plus if plus else urllib.parse.quote
        unquote = urllib.parse.unquote_plus if plus else urllib.parse.unquote

        return method(value, safe=safe) if unquote(value) == value else value

    @property
    def url(self) -> str:
        return self._url

    @property
    def base_url(self) -> str:
        return self._base_url

    def update_params(self, params: ParamMapping, *, remove_none: bool = True) -> str:
        self.params.update(params)
        self._url = self.build_url(remove_none=remove_none)

        return self.url

    def update_headers(self, headers: dict[str, str]) -> None:
        self.headers.update(headers)


class HTTPAsyncIterator(Generic[T]):
    __slots__ = ("_http", "_route", "_cursor", "_first", "_max_results", "_converter", "_buffer")

    def __init__(
        self,
        http: HTTPClient,
        route: Route,
        max_results: int | None = None,
        converter: PaginatedConverter[T] = None,
    ) -> None:
        self._http = http
        self._route = route

        self._cursor: str | None | bool = None
        self._first: int = int(route.params.get("first", 20))  # 20 is twitch default
        self._max_results: int | None = max_results

        if self._max_results is not None and self._max_results < self._first:
            self._first = self._max_results

        self._converter = converter or self._base_converter
        self._buffer: deque[T] = deque()

    async def _base_converter(self, data: Any) -> T:
        return data

    async def _call_next(self) -> None:
        if self._cursor is False:
            raise StopAsyncIteration

        if self._max_results is not None and self._max_results <= 0:
            raise StopAsyncIteration

        self._route.update_params({"after": self._cursor})
        data: RawResponse = await self._http.request_json(self._route)
        self._cursor = data.get("pagination", {}).get("cursor", False)

        try:
            inner: list[RawResponse] = data["data"]
        except KeyError as e:
            # TODO: Proper exception...
            raise ValueError('Expected "data" key not found.') from e

        for value in inner:
            if self._max_results is None:
                self._buffer.append(await self._do_conversion(value))
                continue

            self._max_results -= 1  # If this is causing issues, it's just pylance bugged/desynced...
            if self._max_results < 0:
                return

            self._buffer.append(await self._do_conversion(value))

    async def _do_conversion(self, data: RawResponse) -> T:
        return await self._converter(data)

    async def _flatten(self) -> list[T]:
        if not self._buffer:
            await self._call_next()

        return list(self._buffer)

    def __await__(self) -> Generator[Any, None, list[T]]:
        return self._flatten().__await__()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> T:
        if not self._buffer:
            await self._call_next()

        try:
            data = self._buffer.popleft()
        except IndexError as e:
            raise StopAsyncIteration from e

        return data


class HTTPClient:
    __slots__ = ("_session", "_client_id", "user_agent")

    def __init__(self, session: aiohttp.ClientSession | None = None, *, client_id: str) -> None:
        self._session: aiohttp.ClientSession | None = session  # should be set on the first request
        self._client_id: str = client_id

        # User Agent...
        pyver = f"{sys.version_info[0]}.{sys.version_info[1]}"
        ua = "TwitchioClient (https://github.com/PythonistaGuild/TwitchIO {0}) Python/{1} aiohttp/{2}"
        self.user_agent: str = ua.format(__version__, pyver, aiohttp.__version__)

    @property
    def headers(self) -> dict[str, str]:
        return {"User-Agent": self.user_agent, "Client-ID": self._client_id}

    async def _init_session(self) -> None:
        if self._session and not self._session.closed:
            return

        logger.debug("Initialising a new session on %s.", self.__class__.__qualname__)

        session = self._session or aiohttp.ClientSession()
        session.headers.update(self.headers)

        self._session = session

    def clear(self) -> None:
        if self._session and self._session.closed:
            logger.debug(
                "Clearing %s session. A new session will be created on the next request.", self.__class__.__qualname__
            )
            self._session = None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                logger.debug("Ignoring exception caught while closing %s session: %s.", self.__class__.__qualname__, e)

            self.clear()
            logger.debug("%s session closed successfully.", self.__class__.__qualname__)

    async def request(self, route: Route) -> RawResponse | str:
        await self._init_session()
        assert self._session is not None

        logger.debug("Attempting a request to %r with %s.", route, self.__class__.__qualname__)

        async with self._session.request(
            route.method,
            route.url,
            headers=route.headers,
            json=route.json or None,
        ) as resp:
            data: RawResponse | str = await json_or_text(resp)

            if resp.status >= 400:
                logger.error("Request %r failed with status %s: %s", route, resp.status, data)
                raise HTTPException(
                    f"Request {route} failed with status {resp.status}: {data}",
                    route=route,
                    status=resp.status,
                    extra=data,
                )

        # TODO: This method is not complete. This is purely for testing purposes.
        return data

    async def request_json(self, route: Route) -> Any:
        data = await self.request(route)

        if isinstance(data, str):
            # TODO: Add a HTTPException here.
            raise TypeError("Expected JSON data, but received text data.")

        return data

    def request_paginated(
        self,
        route: Route,
        max_results: int | None = None,
        *,
        converter: PaginatedConverter[T] | None = None,
    ) -> HTTPAsyncIterator[T]:
        iterator: HTTPAsyncIterator[T] = HTTPAsyncIterator(self, route, max_results, converter=converter)
        return iterator
