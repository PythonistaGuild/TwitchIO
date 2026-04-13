"""MIT License

Copyright (c) 2025 - Present Evie. P., Chillymosh and TwitchIO

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

from typing import ClassVar, Literal, Unpack

from ..http import Route
from .conditions import *


# TODO: Check condition keys are valid?
# TODO: Doc generic classes


class _BaseSubscription[T]:
    method: ClassVar[Literal["POST"]] = "POST"
    path: ClassVar[Literal["eventsub/subscriptions"]] = "eventsub/subscriptions"
    type: str
    version: str
    scopes: ClassVar[...]

    def __init__(self, *, condition: T, type: str, version: str) -> None:
        self._condition: T = condition
        self.type = type
        self.version = version

        self._data = {"type": self.type, "version": self.version, "condition": self._condition}

    def route(self) -> Route:
        return Route(self.path, method=self.method, data=self._data)

    @property
    def condition(self) -> T:
        return self._condition


class Subscription[T](_BaseSubscription[T]):
    """Base subscription class used to make an EventSub subscription to Twitch.

    Parameters
    ----------
    condition: ...
        ...
    type: ...
        ...
    version: ...
        ...

    Attributes
    ----------
    method: ClassVar[Literal["POST"]]
        The HTTP method used to make the subscription request. This will always be ``"POST"``.
    path: ClassVar[Literal["eventsub/subscriptions"]]
        The HTTP path ised to make the subscription request. This will aluways be ``"eventsub/subscriptions"``.
    type: str
        The eventsub subscription type passed to Twitch. E.g. ``"channel.chat.message"``.
        See: https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/ for more info.
    version: str
        The eventsub subscription version passed to Twitch. E.g. ``"1"``.
        See: https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/ for more info.
    scopes: ...
        ...
    """

    # TODO: "type" and "version" Literal type...

    def __init__(self, *, condition: T, type: str, version: str) -> None:
        super().__init__(condition=condition, type=type, version=version)


class ChatMessageSubscription(Subscription[ChannelChatMessageCT]):
    _type: ClassVar[str] = "channel.chat.message"
    _version: ClassVar[str] = "1"
    scopes: ClassVar[...]

    def __init__(self, **condition: Unpack[ChannelChatMessageCT]) -> None:
        super().__init__(condition=condition, type=self._type, version=self._version)
