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


__all__ = (
    "HTTPException",
    "InvalidTokenException",
    "MessageRejectedError",
    "MissingConduit",
    "TwitchioException",
    "WebsocketConnectionException",
)


if TYPE_CHECKING:
    from .http import Route
    from .models import SentMessage
    from .user import PartialUser


class TwitchioException(Exception):
    """Base exception for TwitchIO.

    All custom TwitchIO exceptions inherit from this class.
    """


class HTTPException(TwitchioException):
    """Exception raised when an HTTP request fails.

    This exception can be raised anywhere the :class:`twitchio.Client` or :class:`twitchio.ext.commands.Bot`
    is used to make a HTTP request to the Twitch API.

    Attributes
    ----------
    route: :class:`twitchio.Route` | None
        An optional :class:`twitchio.Route` supplied to this exception, which contains various information about the
        request.
    status: int
        The HTTP response code received from Twitch. E.g. ``404`` or ``409``.
    extra: dict[Literal["message"], str]
        A dict with a single key named "message", which may contain additional information from Twitch
        about why the request failed.
    """

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
    """Exception raised when an token can not be validated or refreshed.

    This exception inherits from :exc:`~twitchio.HTTPException` and contains additional information.

    .. warning::

        This exception may contain sensitive information.

    Attributes
    ----------
    token: str | None
        The token which failed to be validated or refreshed. Could be ``None``.
    refresh: str | None
        The refresh token used to attempt refreshing the token. Could be ``None``.
    route: :class:`twitchio.Route` | None
        An optional :class:`twitchio.Route` supplied to this exception, which contains various information about the
        request.
    status: int
        The HTTP response code received from Twitch. E.g. ``404`` or ``409``.
    extra: dict[Literal["message"], str]
        A dict with a single key named "message", which may contain additional information from Twitch
        about why the request failed.
    """

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


class WebsocketConnectionException(TwitchioException):
    """..."""


class EventsubVerifyException(TwitchioException): ...


class MessageRejectedError(TwitchioException):
    """Exception raised when Twitch rejects a sent message. This is not the same as a :exc:`HTTPException` which is raised
    when the request fails for a reason.

    Attributes
    ----------
    channel: :class:`~twitchio.PartialUser`
        The the channel the message was attempted to be sent to.
    code: str | None
        The drop code Twitch responded with.
    message: str | None
        The message Twitch responded with, with the reason why the message was rejected.
    content: str
        The content of the original message sent.
    """

    def __init__(self, msg: str, *, message: SentMessage, channel: PartialUser, content: str) -> None:
        self.channel: PartialUser = channel
        self.code: str | None = message.dropped_code
        self.message: str | None = message.dropped_message
        self.content: str = content
        super().__init__(msg)


class MissingConduit(TwitchioException):
    """Exception raised when :class:`~twitchio.AutoClient` or :class:`~twitchio.ext.commands.AutoBot` attempts to perform
    an action that requires an associated :class:`twitchio.Conduit` which is missing or not assigned yet.
    """
