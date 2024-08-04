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


class BroadcasterModeratorCondition(TypedDict):
    broadcaster_user_id: str
    moderator_user_id: str


class UserCondition(TypedDict):
    user_id: str


class BaseBroadcasterEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class BaseBroadcasterModeratorEvent(BaseBroadcasterEvent):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str


class BaseBroadcasterUserEvent(BaseBroadcasterEvent):
    user_id: str
    user_login: str
    user_name: str


class Transport(TypedDict):
    method: str
    callback: str  # TODO check for websocket payloads


class BaseSubscription(TypedDict, Generic[T]):
    id: str
    type: str
    version: str
    status: str
    cost: NotRequired[int]
    condition: T
    transport: Transport
    created_at: str


class ChannelUpdateEvent(BaseBroadcasterEvent):
    title: str
    language: str
    category_id: int
    category_name: int
    content_classification_labels: list[str]


class ChannelUpdateResponse(TypedDict):
    subscription: BaseSubscription[BroadcasterCondition]
    event: ChannelUpdateEvent


class ChannelFollowEvent(BaseBroadcasterUserEvent):
    followed_at: str


class ChannelFollowResponse(TypedDict):
    subscription: BaseSubscription[BroadcasterModeratorCondition]
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
    subscription: BaseSubscription[BroadcasterCondition]
    event: ChannelAdBreakBeginEvent


class ChannelChatClearEvent(BaseBroadcasterEvent): ...


class ChannelChatClearnResponse(TypedDict):
    subscription: BaseSubscription[BroadcasterCondition]
    event: ChannelChatClearEvent


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
    subscription: BaseSubscription[BroadcasterCondition]
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
    subscription: BaseSubscription[BroadcasterCondition]
    event: GoalEndEvent


class StreamOnlineEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    started_at: str


class StreamOnlineResponse(TypedDict):
    subscription: BaseSubscription[BroadcasterCondition]
    event: StreamOnlineEvent


class StreamOfflineEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class StreamOfflineResponse(TypedDict):
    subscription: BaseSubscription[BroadcasterCondition]
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
    subscription: BaseSubscription[ClientCondition]
    event: UserAuthorizationGrantEvent


class UserAuthorizationRevokeResponse(TypedDict):
    subscription: BaseSubscription[ClientCondition]
    event: UserAuthorizationRevokeEvent


class UserUpdateEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    email: NotRequired[str]
    email_verified: bool
    description: str


class UserUpdateResponse(TypedDict):
    subscription: BaseSubscription[UserCondition]
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
    subscription: BaseSubscription[UserCondition]
    event: UserWhisperEvent
