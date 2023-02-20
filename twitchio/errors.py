"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from typing import Any, Optional


__all__ = (
    "TwitchIOException",
    "AuthenticationError",
    "InvalidContent",
    "IRCCooldownError",
    "EchoMessageWarning",
    "NoClientID",
    "NoToken",
    "HTTPException",
    "Unauthorized",
)


class TwitchIOException(Exception):
    pass


class AuthenticationError(TwitchIOException):
    pass


class InvalidContent(TwitchIOException):
    pass


class IRCCooldownError(TwitchIOException):
    pass


class EchoMessageWarning(TwitchIOException):
    pass


class NoClientID(TwitchIOException):
    pass


class NoToken(TwitchIOException):
    pass


class HTTPException(TwitchIOException):
    def __init__(
        self, message: str, *, reason: Optional[str] = None, status: Optional[int] = None, extra: Optional[Any] = None
    ):
        self.message = message
        self.reason = reason
        self.status = status
        self.extra = extra


class Unauthorized(HTTPException):
    pass
