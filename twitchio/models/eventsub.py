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

from typing import TYPE_CHECKING, Any, ClassVar

from twitchio.http import HTTPClient
from twitchio.types_.eventsub import (
    ChannelAdBreakBeginEvent,
    ChannelChatClearEvent,
    ChannelChatClearUserMessagesEvent,
    ChannelChatMessageDeleteEvent,
    ChannelChatSettingsUpdateEvent,
    ChannelFollowEvent,
    ChannelUpdateEvent,
    ChannelVIPAddEvent,
)
from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime


class BaseEvent:
    _registry: ClassVar[dict[str, type]] = {}
    type: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.type is not None:
            BaseEvent._registry[cls.type] = cls

    @classmethod
    def create_instance(cls, event_type: str, payload: dict[str, Any], http: HTTPClient | None = None) -> Any:
        event_cls = cls._registry.get(event_type)
        if event_cls is None:
            raise ValueError(f"No class registered for event type {event_type}")
        return event_cls(payload) if http is None else event_cls(payload, http=http)


class ChannelUpdate(BaseEvent):
    type = "channel.update"

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
    type = "channel.follow"

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
    type = "channel.ad_break.begin"

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
    type = "channel.chat.clear"

    __slots__ = ("broadcaster",)

    def __init__(self, payload: ChannelChatClearEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChannelChatClear broadcaster={self.broadcaster}>"


class ChannelChatClearUserMessages(BaseEvent):
    type = "channel.chat.clear_user_messages"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelChatClearUserMessagesEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["target_user_id"], payload["target_user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelChatClearUserMessages broadcaster={self.broadcaster} user={self.user}>"


class ChannelChatMessageDelete(BaseEvent):
    type = "channel.chat.message_delete"

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
    type = "channel.chat_settings.update"

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
        return f"<ChannelChatSettingsUpdate broadcaster={self.broadcaster} {self.slow_mode_wait_time} {self.follower_mode_duration}>"


class ChannelVIPAdd(BaseEvent):
    type = "channel.vip.add"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelVIPAddEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelVIPAdd broadcaster={self.broadcaster} user={self.user}>"
