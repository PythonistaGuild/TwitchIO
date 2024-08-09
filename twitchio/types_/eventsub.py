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

from typing import Generic, Literal, NotRequired, TypedDict, TypeVar

from .conduits import Condition


T = TypeVar("T")

EventSubHeaders = TypedDict(
    "EventSubHeaders",
    {
        "Twitch-Eventsub-Message-Id": str,
        "Twitch-Eventsub-Message-Retry": str,
        "Twitch-Eventsub-Message-Type": Literal["notification", "webhook_callback_verification", "revocation"],
        "Twitch-Eventsub-Message-Signature": str,
        "Twitch-Eventsub-Message-Timestamp": str,
        "Twitch-Eventsub-Subscription-Type": str,
        "Twitch-Eventsub-Subscription-Version": str,
    },
    total=False,
)


class SubscriptionCreateTransport(TypedDict):
    method: Literal["websocket"] | Literal["webhook"] | Literal["conduit"]
    callback: NotRequired[str]
    secret: NotRequired[str]
    session_id: NotRequired[str]


class SubscriptionCreateRequest(TypedDict):
    type: str
    version: str
    condition: Condition
    transport: SubscriptionCreateTransport
    session_id: NotRequired[str]
    conduit_id: NotRequired[str]


class BaseBroadcasterEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class BaseUserEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str


class BaseModeratorEvent(TypedDict):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str


class BroadcasterModeratorEvent(BaseBroadcasterEvent, BaseModeratorEvent): ...


class BroadcasterUserEvent(BaseBroadcasterEvent, BaseUserEvent): ...


class BroadcasterModUserEvent(BaseBroadcasterEvent):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str
    user_id: str
    user_login: str
    user_name: str


class WebhookTransport(TypedDict):
    method: Literal["webhook"]
    callback: str


class WebsocketTransport(TypedDict):
    method: Literal["websocket"]
    session_id: str


class ConduitTransport(TypedDict):
    method: Literal["conduit"]
    conduit_id: str


class WebsocketMetadata(TypedDict):
    message_id: str
    message_type: str
    message_timestamp: str
    subscription_type: str
    subscription_version: str


class BaseSubscription(TypedDict, Generic[T]):
    id: str
    type: str
    version: str
    status: Literal["enabled"] | Literal["webhook_callback_verification_pending"]
    cost: NotRequired[int]
    condition: T
    created_at: str


class AnySubscription(BaseSubscription[T]):
    transport: WebhookTransport | WebsocketTransport | ConduitTransport


class SubscriptionResponse(TypedDict):
    data: list[AnySubscription[Condition]]
    total: int
    total_cost: int
    max_total_cost: int


class ChannelUpdateEvent(BaseBroadcasterEvent):
    title: str
    language: str
    category_id: str
    category_name: str
    content_classification_labels: list[str]


class ChannelFollowEvent(BroadcasterUserEvent):
    followed_at: str


class ChannelAdBreakBeginEvent(BaseBroadcasterEvent):
    requester_user_id: str
    requester_user_login: str
    requester_user_name: str
    duration_seconds: str
    duration_seconds: str
    duration_seconds: str
    started_at: str
    is_automatic: str


class ChannelChatClearEvent(BaseBroadcasterEvent): ...


class ChannelChatClearUserMessagesEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_user_name: str


class ChannelChatMessageDeleteEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_user_name: str
    message_id: str


class ChannelChatSettingsUpdateEvent(BaseBroadcasterEvent):
    emote_mode: bool
    follower_mode: bool
    follower_mode: bool
    follower_mode_duration_minutes: int | None
    slow_mode: bool
    slow_mode_wait_time_seconds: int | None
    subscriber_mode: bool
    unique_chat_mode: bool


class ChannelSubscribeEvent(BroadcasterUserEvent):
    tier: str
    is_gift: bool


class ChannelSubscriptionEndEvent(BroadcasterUserEvent):
    tier: str
    is_gift: bool


class ChannelSubscriptionGiftEvent(BroadcasterUserEvent):
    total: int
    tier: str
    cumulative_total: int | None
    is_anonymous: bool


class SubscribeEmotes(TypedDict):
    begin: int
    end: int
    id: str


class SubscribeMessage(TypedDict):
    text: str
    emotes: list[SubscribeEmotes]


class ChannelSubscribeMessageEvent(BroadcasterUserEvent):
    total: int
    tier: str
    cumulative_months: int
    streak_months: int | None
    duration_monhs: int
    message: SubscribeMessage


class ChannelCheerEvent(BroadcasterUserEvent):
    is_anonymous: bool
    message: str
    bits: int


class ChannelRaidEvent(TypedDict):
    from_broadcaster_user_id: str
    from_broadcaster_user_login: str
    from_broadcaster_user_name: str
    to_broadcaster_user_id: str
    to_broadcaster_user_login: str
    to_broadcaster_user_name: str
    viewers: int


class ChannelBanEvent(BroadcasterModUserEvent):
    reason: str
    banned_at: str
    ends_at: str
    is_permanent: bool


class ChannelUnbanEvent(BroadcasterModUserEvent): ...


class ChannelUnbanRequestEvent(BroadcasterUserEvent):
    id: str
    text: str
    created_at: str


class ChannelUnbanRequestSolveEvent(BroadcasterModUserEvent):
    id: str
    resolution_text: str
    status: str


class ChannelVIPAddEvent(BroadcasterUserEvent): ...


class GoalBeginProgressEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    description: str
    current_amount: int
    target_amount: int
    started_at: str


class GoalEndEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    description: str
    is_achieved: bool
    current_amount: int
    target_amount: int
    started_at: str
    ended_at: str


class StreamOnlineEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: Literal["live", "playlist", "watch_party", "premiere", "rerun"]
    started_at: str


class StreamOfflineEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class UserAuthorizationGrantEvent(TypedDict):
    client_id: str
    user_id: str
    user_login: str
    user_name: str


class UserAuthorizationRevokeEvent(TypedDict):
    client_id: str
    user_id: str
    user_login: str | None
    user_name: str | None


class UserUpdateEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    email: NotRequired[str]
    email_verified: bool
    description: str


class WhisperContent(TypedDict):
    text: str


class UserWhisperEvent(TypedDict):
    from_user_id: str
    from_user_login: str
    from_user_name: str
    to_user_id: str
    to_user_login: str
    to_user_name: str
    whisper_id: str
    whisper: WhisperContent
