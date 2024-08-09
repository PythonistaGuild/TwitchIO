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

from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.eventsub import (
        ChannelAdBreakBeginEvent,
        ChannelChatClearEvent,
        ChannelChatClearUserMessagesEvent,
        ChannelChatMessageDeleteEvent,
        ChannelChatSettingsUpdateEvent,
        ChannelFollowEvent,
        ChannelSubscribeEvent,
        ChannelSubscriptionEndEvent,
        ChannelSubscriptionGiftEvent,
        ChannelUpdateEvent,
        ChannelVIPAddEvent,
        StreamOfflineEvent,
        StreamOnlineEvent,
        UserAuthorizationGrantEvent,
        UserAuthorizationRevokeEvent,
        UserUpdateEvent,
        UserWhisperEvent,
    )


class BaseEvent:
    _registry: ClassVar[dict[str, type]] = {}
    subscription_type: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.subscription_type is not None:
            BaseEvent._registry[cls.subscription_type] = cls

    @classmethod
    def create_instance(cls, event_type: str, payload: dict[str, Any], http: HTTPClient | None = None) -> Any:
        event_cls = cls._registry.get(event_type)
        if event_cls is None:
            raise ValueError(f"No class registered for event type {event_type}")
        return event_cls(payload) if http is None else event_cls(payload, http=http)


class ChannelUpdate(BaseEvent):
    subscription_type = "channel.update"

    __slots__ = ("broadcaster", "title", "category_id", "category_name", "content_classification_labels")

    def __init__(self, payload: ChannelUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http)
        self.title = payload["title"]
        self.language = payload["language"]
        self.category_id = payload["category_id"]
        self.category_name = payload["category_name"]
        self.content_classification_labels = payload["content_classification_labels"]

    def __repr__(self) -> str:
        return f"<ChannelUpdate title={self.title} language={self.language} category_id={self.category_id} category_name={self.category_name}>"


class ChannelFollow(BaseEvent):
    subscription_type = "channel.follow"

    __slots__ = ("broadcaster", "user", "followed_at")

    def __init__(self, payload: ChannelFollowEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.followed_at: datetime.datetime = parse_timestamp(payload["followed_at"])

    def __repr__(self) -> str:
        return f"<ChannelFollow broadcaster={self.broadcaster} user={self.user} followed_at={self.followed_at}>"


class ChannelAdBreakBegin(BaseEvent):
    subscription_type = "channel.ad_break.begin"

    __slots__ = ("broadcaster", "requester", "duration", "automatic", "started_at")

    def __init__(self, payload: ChannelAdBreakBeginEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.requester: PartialUser = PartialUser(
            payload["requester_user_id"], payload["requester_user_login"], http=http
        )
        self.duration: int = int(payload["duration_seconds"])
        self.automatic: bool = payload["is_automatic"] == "true"  # TODO confirm this is a string and not a bool
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<ChannelAdBreakBegin broadcaster={self.broadcaster} requester={self.requester} started_at={self.started_at}>"


class ChannelChatClear(BaseEvent):
    subscription_type = "channel.chat.clear"

    __slots__ = ("broadcaster",)

    def __init__(self, payload: ChannelChatClearEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChannelChatClear broadcaster={self.broadcaster}>"


class ChannelChatClearUserMessages(BaseEvent):
    subscription_type = "channel.chat.clear_user_messages"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelChatClearUserMessagesEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["target_user_id"], payload["target_user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelChatClearUserMessages broadcaster={self.broadcaster} user={self.user}>"


class ChannelChatMessageDelete(BaseEvent):
    subscription_type = "channel.chat.message_delete"

    __slots__ = ("broadcaster", "user", "message_id")

    def __init__(self, payload: ChannelChatMessageDeleteEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["target_user_id"], payload["target_user_login"], http=http)
        self.message_id: str = payload["message_id"]

    def __repr__(self) -> str:
        return (
            f"<ChannelChatMessageDelete broadcaster={self.broadcaster} user={self.user} message_id={self.message_id}>"
        )


class ChannelChatSettingsUpdate(BaseEvent):
    subscription_type = "channel.chat_settings.update"

    __slots__ = (
        "broadcaster",
        "emote_mode",
        "follower_mode",
        "follower_mode_duration",
        "slow_mode",
        "slow_mode_wait_time",
        "subscriber_mode",
        "unique_chat_mode",
    )

    def __init__(self, payload: ChannelChatSettingsUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.emote_mode: bool = bool(payload["emote_mode"])
        self.follower_mode: bool = bool(payload["follower_mode"])
        self.slow_mode: bool = bool(payload["slow_mode"])
        self.subscriber_mode: bool = bool(payload["subscriber_mode"])
        self.unique_chat_mode: bool = bool(payload["unique_chat_mode"])
        self.slow_mode_wait_time: int | None = payload.get("slow_mode_wait_time_seconds")
        self.follower_mode_duration: int | None = payload.get("follower_mode_duration_minutes")

    def __repr__(self) -> str:
        return f"<ChannelChatSettingsUpdate broadcaster={self.broadcaster} slow_mode={self.slow_mode} follower_mode={self.follower_mode} subscriber_mode={self.subscriber_mode} unique_chat_mode={self.unique_chat_mode}>"


class ChannelSubscribe(BaseEvent):
    subscription_type = "channel.subscribe"

    __slots__ = (
        "broadcaster",
        "user",
        "tier",
        "gift",
    )

    def __init__(self, payload: ChannelSubscribeEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.gift: bool = bool(payload["is_gift"])

    def __repr__(self) -> str:
        return f"<ChannelSubscribe broadcaster={self.broadcaster} user={self.user} tier={self.tier} gift={self.gift}>"


class ChannelSubscriptionEnd(BaseEvent):
    subscription_type = "channel.subscribe.end"

    __slots__ = (
        "broadcaster",
        "user",
        "tier",
        "gift",
    )

    def __init__(self, payload: ChannelSubscriptionEndEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.gift: bool = bool(payload["is_gift"])

    def __repr__(self) -> str:
        return f"<ChannelSubscriptionEnd broadcaster={self.broadcaster} user={self.user} tier={self.tier} gift={self.gift}>"


class ChannelSubscriptionGift(BaseEvent):
    subscription_type = "channel.subscribe.end"

    __slots__ = ("broadcaster", "user", "tier", "total", "cumulative_total", "anonymous")

    def __init__(self, payload: ChannelSubscriptionGiftEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.total: int = int(payload["total"])
        self.anonymous: bool = bool(payload["is_anonymous"])
        cumulative_total = payload.get("cumulative_total")
        self.cumulative_total: int | None = int(cumulative_total) if cumulative_total is not None else None

    def __repr__(self) -> str:
        return f"<ChannelSubscriptionGift broadcaster={self.broadcaster} user={self.user} tier={self.tier} total={self.total}>"


class ChannelVIPAdd(BaseEvent):
    subscription_type = "channel.vip.add"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelVIPAddEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelVIPAdd broadcaster={self.broadcaster} user={self.user}>"


class StreamOnline(BaseEvent):
    subscription_type = "stream.online"

    __slots__ = ("broadcaster", "id", "type", "started_at")

    def __init__(self, payload: StreamOnlineEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.type: Literal["live", "playlist", "watch_party", "premiere", "rerun"] = payload["type"]
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<StreamOnline id={self.id} broadcaster={self.broadcaster} started_at={self.started_at}>"


class StreamOffline(BaseEvent):
    subscription_type = "stream.offline"

    __slots__ = "broadcaster"

    def __init__(self, payload: StreamOfflineEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )

    def __repr__(self) -> str:
        return f"<StreamOffline broadcaster={self.broadcaster}>"


class UserAuthorizationGrant(BaseEvent):
    subscription_type = "user.authorization.grant"

    __slots__ = ("client_id", "user")

    def __init__(self, payload: UserAuthorizationGrantEvent, *, http: HTTPClient) -> None:
        self.client_id: str = payload["client_id"]
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<UserAuthorizationGrant client_id={self.client_id} user={self.user}>"


class UserAuthorizationRevoke(BaseEvent):
    subscription_type = "user.authorization.revoke"

    __slots__ = ("client_id", "user")

    def __init__(self, payload: UserAuthorizationRevokeEvent, *, http: HTTPClient) -> None:
        self.client_id: str = payload["client_id"]
        self.user: PartialUser | None = (
            PartialUser(payload["user_id"], payload["user_login"], http=http) if payload.get("user_id") else None
        )

    def __repr__(self) -> str:
        return f"<UserAuthorizationRevoke client_id={self.client_id} user={self.user}>"


class UserUpdate(BaseEvent):
    subscription_type = "user.update"

    __slots__ = ("user", "email", "verified", "description")

    def __init__(self, payload: UserUpdateEvent, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.verified: bool = bool(payload["email_verified"])
        self.description: str = payload["description"]
        self.email: str | None = payload.get("email", None)

    def __repr__(self) -> str:
        return f"<UserUpdate user={self.user} verified={self.verified} description={self.description}>"


class Whisper(BaseEvent):
    subscription_type = "user.whisper.message"

    __slots__ = ("sender", "recipient", "id", "message")

    def __init__(self, payload: UserWhisperEvent, *, http: HTTPClient) -> None:
        self.sender: PartialUser = PartialUser(payload["from_user_id"], payload["from_user_login"], http=http)
        self.recipient: PartialUser = PartialUser(payload["to_user_id"], payload["to_user_login"], http=http)
        self.id: str = payload["whisper_id"]
        self.message: str = payload["whisper"]["text"]

    def __repr__(self) -> str:
        return f"<Whisper sender={self.sender} recipient={self.recipient} id={self.id} message={self.message}>"
