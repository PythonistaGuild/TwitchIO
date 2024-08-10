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

from twitchio.models.chat import EmoteSet
from twitchio.user import PartialUser
from twitchio.utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.eventsub import (
        ChannelAdBreakBeginEvent,
        ChannelChatClearEvent,
        ChannelChatClearUserMessagesEvent,
        ChannelChatMessageDeleteEvent,
        ChannelChatMessageEvent,
        ChannelChatSettingsUpdateEvent,
        ChannelFollowEvent,
        ChannelSubscribeEvent,
        ChannelSubscriptionEndEvent,
        ChannelSubscriptionGiftEvent,
        ChannelUpdateEvent,
        ChannelVIPAddEvent,
        ChatMessageBadge as ChatMessageBadgeData,
        ChatMessageCheer as ChatMessageCheerData,
        ChatMessageCheermote as ChatMessageCheermoteData,
        ChatMessageEmote as ChatMessageEmoteData,
        ChatMessageFragments as ChatMessageFragmentsData,
        ChatMessageReply as ChatMessageReplyData,
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
        self.automatic: bool = bool(payload["is_automatic"])
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


class ChatMessageReply:
    __slots__ = (
        "parent_message_id",
        "parent_message_body",
        "parent_user_id",
        "parent_user_name",
        "parent_user_login",
        "thread_message_id",
        "thread_user_id",
        "thread_user_name",
        "thread_user_login",
    )

    def __init__(self, data: ChatMessageReplyData) -> None:
        self.parent_message_id: str = data["parent_message_id"]
        self.parent_message_body: str = data["parent_message_body"]
        self.parent_user_id: str = data["parent_user_id"]
        self.parent_user_name: str = data["parent_user_name"]
        self.parent_user_login: str = data["parent_user_login"]
        self.thread_message_id: str = data["thread_message_id"]
        self.thread_user_id: str = data["thread_user_id"]
        self.thread_user_name: str = data["thread_user_name"]
        self.thread_user_login: str = data["thread_user_login"]

    def __repr__(self) -> str:
        return f"<ChatMessageReply parent_message_id={self.parent_message_id} parent_user_id={self.parent_user_id}>"


class ChatMessageCheer:
    __slots__ = ("bits",)

    def __init__(self, data: ChatMessageCheerData) -> None:
        self.bits: int = int(data["bits"])

    def __repr__(self) -> str:
        return f"<ChatMessageCheer bits={self.bits}>"


class ChatMessageBadge:
    __slots__ = ("set_id", "id", "info")

    def __init__(self, data: ChatMessageBadgeData) -> None:
        self.set_id: str = data["set_id"]
        self.id: str = data["id"]
        self.info: str = data["info"]

    def __repr__(self) -> str:
        return f"<ChatMessageBadge set_id={self.set_id} id={self.id} info={self.info}>"


class ChatMessageEmote:
    __slots__ = ("set_id", "id", "owner_id", "format")

    def __init__(self, data: ChatMessageEmoteData, *, http: HTTPClient) -> None:
        self.set_id: str = data["emote_set_id"]
        self.id: str = data["id"]
        self.owner_id: str = data["owner_id"]
        self.format: list[Literal["static", "animated"]] = data["format"]

    def __repr__(self) -> str:
        return f"<ChatMessageEmote set_id={self.set_id} id={self.id} owner_id={self.owner_id} format={self.format}>"

    async def fetch_emote_set(self, *, http: HTTPClient, token_for: str | None = None) -> EmoteSet:
        data = await http.get_emote_sets(emote_set_ids=[self.set_id], token_for=token_for)
        return EmoteSet(data["data"][0], template=data["template"], http=http)


class ChatMessageCheermote:
    __slots__ = ("prefix", "bits", "tier")

    def __init__(self, data: ChatMessageCheermoteData) -> None:
        self.prefix: str = data["prefix"]
        self.bits: int = int(data["bits"])
        self.tier: int = int(data["tier"])

    def __repr__(self) -> str:
        return f"<ChatMessageCheermote prefix={self.prefix} bits={self.bits} tier={self.tier}>"


class ChatMessageFragment:
    __slots__ = ("text", "type", "cheermote", "emote", "mention")

    def __init__(self, data: ChatMessageFragmentsData, *, http: HTTPClient) -> None:
        self.text = data["text"]
        self.type: Literal["text", "cheermote", "emote", "mention"] = data["type"]
        user = data.get("mention")
        self.mention: PartialUser | None = (
            PartialUser(user["user_id"], user["user_login"], http=http) if user is not None else None
        )
        self.cheermote: ChatMessageCheermote | None = (
            ChatMessageCheermote(data["cheermote"]) if data["cheermote"] is not None else None
        )
        self.emote: ChatMessageEmote | None = ChatMessageEmote(data["emote"], http=http) if data["emote"] else None

    def __repr__(self) -> str:
        return f"<ChatMessageFragment type={self.type} text={self.text}>"


class ChannelChatMessage(BaseEvent):
    subscription_type = "channel.chat.message"

    __slots__ = (
        "broadcaster",
        "chatter",
        "id",
        "text",
        "fragments",
        "color",
        "badges",
        "message_type",
        "cheer",
        "reply",
        "channel_points_id",
        "channel_points_animation_id",
    )

    def __init__(self, payload: ChannelChatMessageEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.chatter: PartialUser = PartialUser(payload["chatter_user_id"], payload["chatter_user_login"], http=http)
        self.id: str = payload["message_id"]
        self.text: str = payload["message"]["text"]
        self.color: Colour | None = Colour.from_hex(payload["color"]) if payload["color"] else None
        self.channel_points_id: str | None = payload["channel_points_custom_reward_id"]
        self.channel_points_animation_id: str | None = payload["channel_points_animation_id"]
        self.reply: ChatMessageReply | None = (
            ChatMessageReply(payload["reply"]) if payload["reply"] is not None else None
        )
        self.message_type: Literal[
            "text",
            "channel_points_highlighted",
            "channel_points_sub_only",
            "user_intro",
            "power_ups_message_effect",
            "power_ups_gigantified_emote",
        ] = payload["message_type"]

        self.cheer: ChatMessageCheer | None = (
            ChatMessageCheer(payload["cheer"]) if payload["cheer"] is not None else None
        )
        self.badges: list[ChatMessageBadge] = [ChatMessageBadge(badge) for badge in payload["badges"]]

        self.fragments: list[ChatMessageFragment] = [
            ChatMessageFragment(fragment, http=http) for fragment in payload["message"]["fragments"]
        ]

    @property
    def colour(self) -> Colour | None:
        return self.color

    def __repr__(self) -> str:
        return (
            f"<ChannelChatMessage broadcaster={self.broadcaster} chatter={self.chatter} id={self.id} text={self.text}>"
        )


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
