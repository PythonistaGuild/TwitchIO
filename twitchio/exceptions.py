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

from typing import TYPE_CHECKING, Any


__all__ = ("TwitchioException", "HTTPException", "WebsocketTimeoutException")


if TYPE_CHECKING:
    from .http import Route


class TwitchioException(Exception):
    """Base exception for TwitchIO."""

    # TODO: Document this class.


class HTTPException(TwitchioException):
    """Exception raised when an HTTP request fails."""

    # TODO: Document this class.
    # TODO: Add extra attributes to this class. E.g. response, status, etc.

    def __init__(
        self,
        msg: str = "",
        /,
        *,
        route: Route | None = None,
        status: int,
        extra: str | dict[str, Any],
    ) -> None:
        self.route = route
        self.status = status
        self.extra = {"message": extra} if isinstance(extra, str) else extra

        super().__init__(msg)


class InvalidTokenException(HTTPException):
    """Exception raised when an invalid token can not be validated or refreshed."""

    def __init__(
        self,
        msg: str = "",
        /,
        *,
        token: str | None = None,
        refresh: str | None = None,
        type_: str,
        original: HTTPException,
    ) -> None:
        self.token = token
        self.refresh = refresh
        self.invalid_type = type_

        super().__init__(msg, route=original.route, status=original.status, extra=original.extra)


class WebsocketTimeoutException(TwitchioException):
    """Exception raised when a conduit websocket has timed-out waiting for a "session_welcome" message."""