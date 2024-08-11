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

import abc
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Unpack


if TYPE_CHECKING:
    from ..types_.conduits import Condition


__all__ = (
    "SubscriptionPayload",
    "AutomodMessageHoldSubscription",
    "AutomodMessageUpdateSubscription",
    "AutomodSettingsUpdateSubscription",
    "AutomodTermsUpdateSubscription",
    "ChannelUpdateSubscription",
    "ChannelFollowSubscription",
    "ChannelAdBreakBeginSubscription",
    "ChannelChatClearSubscription",
    "ChannelChatClearUserMessagesSubscription",
    "ChannelChatMessageSubscription",
    "ChannelChatNotificationSubscription",
    "ChannelChatMessageDeleteSubscription",
    "ChannelChatSettingsUpdateSubscription",
    "ChannelSubscribeSubscription",
    "ChannelSubscriptionEndSubscription",
    "ChannelSubscriptionGiftSubscription",
    "ChannelSubscribeMessageSubscription",
    "ChannelCheerSubscription",
    "ChannelRaidSubscription",
    "ChannelBanSubscription",
    "ChannelUnbanSubscription",
    "ChannelUnbanRequestSubscription",
    "ChannelUnbanRequestResolveSubscription",
    "ChannelVIPAddSubscription",
    "ShoutoutCreateSubscription",
    "ShoutoutReceiveSubscription",
    "StreamOnlineSubscription",
    "StreamOfflineSubscription",
    "UserAuthorizationGrantSubscription",
    "UserAuthorizationRevokeSubscription",
    "UserUpdateSubscription",
    "WhisperReceivedSubscription",
)


class SubscriptionPayload(abc.ABC):
    type: ClassVar[Any]
    version: ClassVar[Any]

    __slots__ = (
        "broadcaster_user_id",
        "moderator_user_id",
        "user_id",
        "campaign_id",
        "category_id",
        "organization_id",
        "client_id",
        "conduit_id",
        "reward_id",
        "from_broadcaster_user_id",
        "to_broadcaster_user_id",
        "broadcaster_id",
    )

    def __init__(self, **condition: Unpack[Condition]) -> None:
        raise NotImplementedError

    @property
    def condition(self) -> Condition:
        raise NotImplementedError


class AutomodMessageHoldSubscription(SubscriptionPayload):
    type: ClassVar[Literal["automod.message.hold"]] = "automod.message.hold"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodMessageUpdateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["automod.message.update"]] = "automod.message.update"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodSettingsUpdateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["automod.settings.update"]] = "automod.settings.update"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodTermsUpdateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["automod.terms.update"]] = "automod.terms.update"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelUpdateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.update"]] = "channel.update"
    version: ClassVar[Literal["2"]] = "2"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelFollowSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.follow"]] = "channel.follow"
    version: ClassVar[Literal["2"]] = "2"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelAdBreakBeginSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.ad_break.begin"]] = "channel.ad_break.begin"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelChatClearSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat.clear"]] = "channel.chat.clear"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChannelChatClearUserMessagesSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat.clear_user_messages"]] = "channel.chat.clear_user_messages"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChannelChatMessageSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat.message"]] = "channel.chat.message"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChannelChatNotificationSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat.notification"]] = "channel.chat.notification"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChannelChatMessageDeleteSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat.message_delete"]] = "channel.chat.message_delete"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChannelChatSettingsUpdateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.chat_settings.update"]] = "channel.chat_settings.update"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChannelSubscribeSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.subscribe"]] = "channel.subscribe"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelSubscriptionEndSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.subscribe.end"]] = "channel.subscribe.end"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelSubscriptionGiftSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.subscribe.gift"]] = "channel.subscribe.gift"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelSubscribeMessageSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.subscribe.message"]] = "channel.subscribe.message"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelCheerSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.cheer"]] = "channel.cheer"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelRaidSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.raid"]] = "channel.raid"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.to_broadcaster_user_id: str = condition.get("to_broadcaster_user_id", "")

        if not self.to_broadcaster_user_id:
            raise ValueError('The parameter "to_broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"to_broadcaster_user_id": self.to_broadcaster_user_id}


class ChannelBanSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.ban"]] = "channel.ban"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelUnbanSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.unban"]] = "channel.unban"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelUnbanRequestSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.unban_request.create"]] = "channel.unban_request.create"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelUnbanRequestResolveSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.unban_request.resolve"]] = "channel.unban_request.resolve"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelVIPAddSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.vip.add"]] = "channel.vip.add"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ShoutoutCreateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.shoutout.create"]] = "channel.shoutout.create"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ShoutoutReceiveSubscription(SubscriptionPayload):
    type: ClassVar[Literal["channel.shoutout.receive"]] = "channel.shoutout.receive"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class StreamOnlineSubscription(SubscriptionPayload):
    type: ClassVar[Literal["stream.online"]] = "stream.online"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class StreamOfflineSubscription(SubscriptionPayload):
    type: ClassVar[Literal["stream.offline"]] = "stream.offline"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class UserAuthorizationGrantSubscription(SubscriptionPayload):
    type: ClassVar[Literal["user.authorization.grant"]] = "user.authorization.grant"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.client_id: str = condition.get("client_id", "")

        if not self.client_id:
            raise ValueError('The parameter "client_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"client_id": self.client_id}


class UserAuthorizationRevokeSubscription(SubscriptionPayload):
    type: ClassVar[Literal["user.authorization.revoke"]] = "user.authorization.revoke"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.client_id: str = condition.get("client_id", "")

        if not self.client_id:
            raise ValueError('The parameter "client_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"client_id": self.client_id}


class UserUpdateSubscription(SubscriptionPayload):
    type: ClassVar[Literal["user.update"]] = "user.update"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.user_id: str = condition.get("user_id", "")

        if not self.user_id:
            raise ValueError('The parameter "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"user_id": self.user_id}


class WhisperReceivedSubscription(SubscriptionPayload):
    type: ClassVar[Literal["user.whisper.message"]] = "user.whisper.message"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.user_id: str = condition.get("user_id", "")

        if not self.user_id:
            raise ValueError('The parameter "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"user_id": self.user_id}
