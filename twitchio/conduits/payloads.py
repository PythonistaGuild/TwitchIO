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

from typing import TYPE_CHECKING, Any, ClassVar, Literal


if TYPE_CHECKING:
    from typing_extensions import Unpack

    from ..types_.conduits import Condition


__all__ = ("SubscriptionPayload", "ChannelChatMessageSubscription")


class SubscriptionPayload:
    type: ClassVar[Any]
    version: ClassVar[Any]

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str | None = condition.get("broadcaster_user_id", None)
        self.moderator_user_id: str | None = condition.get("moderator_user_id", None)
        self.user_id: str | None = condition.get("user_id", None)
        self.campaign_id: str | None = condition.get("campaign_id", None)
        self.category_id: str | None = condition.get("category_id", None)
        self.organization_id: str | None = condition.get("organization_id", None)
        self.client_id: str | None = condition.get("client_id", None)
        self.conduit_id: str | None = condition.get("conduit_id", None)
        self.reward_id: str | None = condition.get("reward_id", None)
        self.from_broadcaster_user_id: str | None = condition.get("from_broadcaster_user_id", None)
        self.to_broadcaster_user_id: str | None = condition.get("to_broadcaster_user_id", None)
        self.broadcaster_id: str | None = condition.get("broadcaster_id")


class ChannelChatMessageSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat.message"]] = "channel.chat.message"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        super().__init__(**condition)

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')
