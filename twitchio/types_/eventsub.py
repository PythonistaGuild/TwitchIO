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


class ClientCondition(TypedDict):
    client_id: str


class BroadcasterCondition(TypedDict):
    broadcaster_user_id: str


class BroadcasterUserCondition(TypedDict):
    broadcaster_user_id: str
    user_id: str


class BroadcasterModeratorCondition(TypedDict):
    broadcaster_user_id: str
    moderator_user_id: str


class UserCondition(TypedDict):
    user_id: str


class BaseBroadcasterEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class BroadcasterModeratorEvent(BaseBroadcasterEvent):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str


class BroadcasterUserEvent(BaseBroadcasterEvent):
    user_id: str
    user_login: str
    user_name: str


class WebhookTransport:
    method: Literal["webhook"]
    callback: str


class WebsocketTransport:
    method: Literal["websocket"]
    session_id: str


class BaseSubscription(TypedDict, Generic[T]):
    id: str
    type: str
    version: str
    status: str
    cost: NotRequired[int]
    condition: T
    created_at: str


class WebhookSubscription(BaseSubscription[T], TypedDict):
    transport: WebhookTransport


class WebhookSocketSubscription(BaseSubscription[T], TypedDict):
    transport: WebhookTransport | WebsocketTransport


class ChannelUpdateEvent(BaseBroadcasterEvent):
    title: str
    language: str
    category_id: int
    category_name: int
    content_classification_labels: list[str]


class ChannelUpdateResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterCondition]
    event: ChannelUpdateEvent


class ChannelFollowEvent(BroadcasterUserEvent):
    followed_at: str


class ChannelFollowResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterModeratorCondition]
    event: ChannelFollowEvent


class ChannelAdBreakBeginEvent(BaseBroadcasterEvent):
    requester_user_id: str
    requester_user_login: str
    requester_user_name: str
    duration_seconds: str
    duration_seconds: str
    duration_seconds: str
    started_at: str
    is_automatic: str


class ChannelAdBreakBeginResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterCondition]
    event: ChannelAdBreakBeginEvent


class ChannelChatClearEvent(BaseBroadcasterEvent): ...


class ChannelChatClearResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterUserCondition]
    event: ChannelChatClearEvent


class ChannelChatClearMessagesEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_user_name: str


class ChannelChatClearMessagesResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterUserCondition]
    event: ChannelChatClearMessagesEvent


class ChannelChatMessagesDeleteEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_user_name: str
    message_id: str


class ChannelChatMessagesDeleteResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterUserCondition]
    event: ChannelChatMessagesDeleteEvent


class ChannelChatSettingsUpdateEvent(BaseBroadcasterEvent):
    emote_mode: bool
    follower_mode: bool
    follower_mode: bool
    follower_mode_duration_minutes: bool
    slow_mode: bool
    slow_mode_wait_time_seconds: int
    subscriber_mode: bool
    unique_chat_mode: bool


class ChannelChatSettingsUpdateResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterUserCondition]
    event: ChannelChatSettingsUpdateEvent


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


class GoalBeginProgressResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterCondition]
    event: GoalBeginProgressEvent


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


class GoalEndResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterCondition]
    event: GoalEndEvent


class StreamOnlineEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    started_at: str


class StreamOnlineResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterCondition]
    event: StreamOnlineEvent


class StreamOfflineEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class StreamOfflineResponse(TypedDict):
    subscription: WebhookSocketSubscription[BroadcasterCondition]
    event: StreamOfflineEvent


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


class UserAuthorizationGrantResponse(TypedDict):
    subscription: WebhookSubscription[ClientCondition]
    event: UserAuthorizationGrantEvent


class UserAuthorizationRevokeResponse(TypedDict):
    subscription: WebhookSubscription[ClientCondition]
    event: UserAuthorizationRevokeEvent


class UserUpdateEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    email: NotRequired[str]
    email_verified: bool
    description: str


class UserUpdateResponse(TypedDict):
    subscription: WebhookSocketSubscription[UserCondition]
    event: UserUpdateEvent


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


class UserWhisperResponse(TypedDict):
    subscription: WebhookSocketSubscription[UserCondition]
    event: UserWhisperEvent
