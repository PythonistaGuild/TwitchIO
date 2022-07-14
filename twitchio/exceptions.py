"""MIT License

Copyright (c) 2017-present TwitchIO

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

from typing import Optional

__all__ = (
    "TwitchIOException",
    "JoinFailed",
    "AuthenticationError",
    "InvalidToken",
    "RefreshFailure",
    "EventNotFound",
    "HTTPException",
    "HTTPResponseException",
    "Unauthorized",
)

from typing import TYPE_CHECKING

import aiohttp

if TYPE_CHECKING:
    from .types.payloads import ErrorType


class TwitchIOException(Exception):
    pass


class JoinFailed(TwitchIOException):
    pass


class AuthenticationError(TwitchIOException):
    pass


class InvalidToken(AuthenticationError):
    pass


class RefreshFailure(AuthenticationError):
    pass


class EventNotFound(Exception):
    pass


class HTTPException(TwitchIOException):
    pass


class HTTPResponseException(HTTPException):
    def __init__(self, response: aiohttp.ClientResponse, data: ErrorType, *, message: Optional[str] = None) -> None:
        self.status = response.status
        self._response = response
        self.message = message or data["message"]
        super().__init__(self.message)


class Unauthorized(HTTPResponseException):
    pass
