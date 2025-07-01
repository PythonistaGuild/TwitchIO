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

from typing import Any, Literal, Never, NotRequired, TypeAlias, TypedDict

from .eventsub import ShardStatus


__all__ = (
    "Condition",
    "ConduitData",
    "KeepAliveMessage",
    "KeepAliveMetaData",
    "MessageTypes",
    "MetaData",
    "NotificationMessage",
    "NotificationMetaData",
    "NotificationPayload",
    "NotificationSubscription",
    "NotificationTransport",
    "ReconnectMessage",
    "ReconnectMetaData",
    "ReconnectPayload",
    "ReconnectSession",
    "RevocationMessage",
    "RevocationMetaData",
    "RevocationPayload",
    "RevocationSubscription",
    "RevocationTransport",
    "WebsocketMessages",
    "WelcomeMessage",
    "WelcomeMetaData",
    "WelcomePayload",
    "WelcomeSession",
)


class ShardTransport(TypedDict):
    method: Literal["websocket", "webhook"]
    callback: NotRequired[str]
    session_id: NotRequired[str]
    connected_at: NotRequired[str]
    disconnected_at: NotRequired[str]


class ShardData(TypedDict):
    id: str
    status: ShardStatus
    transport: ShardTransport


class ShardUpdateTransport(TypedDict):
    method: Literal["webhook", "websocket"]
    callback: NotRequired[str]
    secret: NotRequired[str]
    session_id: NotRequired[str]


class ShardUpdateRequest(TypedDict):
    id: str
    transport: ShardUpdateTransport


class ConduitData(TypedDict):
    id: str
    shard_count: int


class WelcomeMetaData(TypedDict):
    message_id: str
    message_type: Literal["session_welcome"]
    message_timestamp: str


class KeepAliveMetaData(TypedDict):
    message_id: str
    message_type: Literal["session_keepalive"]
    message_timestamp: str


class NotificationMetaData(TypedDict):
    message_id: str
    message_type: Literal["notification"]
    message_timestamp: str
    subscription_type: str
    subscription_version: Literal["1", "2"]


class ReconnectMetaData(TypedDict):
    message_id: str
    message_type: Literal["session_reconnect"]
    message_timestamp: str


class RevocationMetaData(TypedDict):
    message_id: str
    message_type: Literal["revocation"]
    message_timestamp: str
    subscription_type: str
    subscription_version: str


class WelcomeSession(TypedDict):
    id: str
    status: Literal["connected"]
    keepalive_timeout_seconds: int
    reconnect_url: None
    connected_at: str


class WelcomePayload(TypedDict):
    session: WelcomeSession


class WelcomeMessage(TypedDict):
    metadata: WelcomeMetaData
    payload: WelcomePayload


class KeepAliveMessage(TypedDict):
    metadata: KeepAliveMetaData
    payload: dict[Never, Never]


class Condition(TypedDict, total=False):
    broadcaster_user_id: str
    moderator_user_id: str
    user_id: str
    campaign_id: str
    category_id: str
    organization_id: str
    client_id: str
    conduit_id: str
    reward_id: str
    from_broadcaster_user_id: str
    to_broadcaster_user_id: str
    broadcaster_id: str


class NotificationTransport(TypedDict):
    method: Literal["websocket", "webhook"]
    session_id: str


class NotificationSubscription(TypedDict):
    id: str
    status: str
    type: str
    version: Literal["1", "2"]
    cost: int
    condition: Condition
    transport: NotificationTransport
    created_at: str


class NotificationPayload(TypedDict):
    subscription: NotificationSubscription
    event: dict[str, Any]


class NotificationMessage(TypedDict):
    metadata: NotificationMetaData
    payload: NotificationPayload


class ReconnectSession(TypedDict):
    id: str
    status: Literal["reconnecting"]
    keepalive_timeout_seconds: None
    reconnect_url: str
    connected_at: str


class ReconnectPayload(TypedDict):
    session: ReconnectSession


class ReconnectMessage(TypedDict):
    metadata: ReconnectMetaData
    payload: ReconnectPayload


class RevocationTransport(TypedDict):
    method: Literal["websocket"] | Literal["webhook"]
    session_id: NotRequired[str]
    callback: NotRequired[str]


class RevocationSubscription(TypedDict):
    id: str
    status: Literal[
        "authorization_revoked", "user_removed", "version_removed", "notification_failures_exceeded", "chat_user_banned"
    ]
    type: str
    version: str
    cost: int
    condition: Condition
    transport: RevocationTransport
    created_at: str


class RevocationPayload(TypedDict):
    subscription: RevocationSubscription


class RevocationMessage(TypedDict):
    metadata: RevocationMetaData
    payload: RevocationPayload


WebsocketMessages: TypeAlias = WelcomeMessage | ReconnectMessage | RevocationMessage | NotificationMessage | KeepAliveMessage
MetaData: TypeAlias = WelcomeMetaData | ReconnectMetaData | RevocationMetaData | NotificationMetaData | KeepAliveMetaData
MessageTypes: TypeAlias = Literal["session_welcome", "session_reconnect", "session_keepalive", "notification", "revocation"]
