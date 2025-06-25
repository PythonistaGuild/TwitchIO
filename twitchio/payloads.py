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

from .eventsub.enums import TransportMethod


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from .authentication import Scopes
    from .eventsub.enums import SubscriptionType
    from .types_.eventsub import Condition, _SubscriptionData
    from .types_.tokens import _TokenRefreshedPayload


__all__ = ("EventErrorPayload", "TokenRefreshedPayload", "WebsocketSubscriptionData")


class EventErrorPayload:
    """Payload received in the :class:`Client.event_error` event when an error
    occurs during an event listener.

    Attributes
    ----------
    error: Exception
        The error that occurred.
    listener: Callable[..., Coroutine[Any, Any, None]]
        The listener that raised the error.
    original: Any
        The original event payload that was passed to the listener that caused the error.
    """

    __slots__ = ("error", "listener", "original")

    def __init__(self, *, error: Exception, listener: Callable[..., Coroutine[Any, Any, None]], original: Any) -> None:
        self.error: Exception = error
        self.listener: Callable[..., Coroutine[Any, Any, None]] = listener
        self.original: Any = original


class WebsocketSubscriptionData:
    """
    Payload returned from :meth:`~twitchio.Client.websocket_subscriptions` and
    :meth:`~twitchio.Client.delete_websocket_subscription` containing relevant information about the websocket subscription.

    Attributes
    ----------
    raw_data: dict[str, Any]
        The data contained in this class as a :class:`dict`
    condition: dict[str, str]
        The condition used to subscribe to the subscription as a :class:`dict`.
    token_for: str | None
        The User ID used to subscribe to this subscription. This could be the Client Users ID. Could be ``None``.
    transport: :class:`~twitchio.eventsub.TransportMethod`
        The :class:`~twitchio.eventsub.TransportMethod` enum.
        This will always be :attr:`~twitchio.eventsub.TransportMethod.WEBSOCKET`.
    type: :class:`~twitchio.eventsub.SubscriptionType`
        The subscription type as an enum value.
    version: str
        The version of the subscription on twitch.
    """

    __slots__ = (
        "condition",
        "raw_data",
        "token_for",
        "transport",
        "type",
        "version",
    )

    def __init__(self, data: _SubscriptionData) -> None:
        self.raw_data = data
        self.condition: Condition = data["condition"]
        self.token_for: str | None = data["token_for"]
        self.transport: TransportMethod = TransportMethod.WEBSOCKET
        self.type: SubscriptionType = data["type"]
        self.version: str = data["version"]


class TokenRefreshedPayload:
    """Payload received in the :func:`~twitchio.event_token_refreshed` event when a token managed by TwitchIO is successfully
    refreshed on the :class:`~twitchio.Client`.

    Attributes
    ----------
    user_id: str
        The User ID associated with the refreshed token.
    refresh_token: str
        The new refresh token returned by Twitch.
    token: str
        The updated token after refreshing returned by Twitch.
    scopes: :class:`~twitchio.Scopes`
        The scopes associated with the token.
    expires_in: int
        The time the new token expires as an :class:`int` of seconds.
    """

    __slots__ = (
        "expires_in",
        "refresh_token",
        "scopes",
        "token",
        "user_id",
    )

    def __init__(self, data: _TokenRefreshedPayload) -> None:
        self.user_id: str = data["user_id"]
        self.refresh_token: str = data["refresh_token"]
        self.token: str = data["token"]
        self.scopes: Scopes = data["scopes"]
        self.expires_in: int = data["expires_in"]
