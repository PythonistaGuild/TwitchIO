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


class StreamOnlineEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    started_at: str


class StreamOnlinePayload(TypedDict):
    subscription: BaseSubscription[BroadcasterCondition]
    event: StreamOnlineEvent


class StreamOfflineEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class StreamOfflinePayload(TypedDict):
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


class UserAuthorizationGrantPayload(TypedDict):
    subscription: BaseSubscription[ClientCondition]
    event: UserAuthorizationGrantEvent


class UserAuthorizationRevokePayload(TypedDict):
    subscription: BaseSubscription[ClientCondition]
    event: UserAuthorizationRevokeEvent


class UserUpdateEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    email: NotRequired[str]
    email_verified: bool
    description: str


class UserUpdatePayload(TypedDict):
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


class UserWhisperPayload(TypedDict):
    subscription: BaseSubscription[UserCondition]
    event: UserWhisperEvent
