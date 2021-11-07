from __future__ import annotations
import datetime
import hmac
import hashlib
import logging
from typing import Dict, TYPE_CHECKING, Optional, Type, Union
from typing_extensions import Literal

from aiohttp import web

from twitchio import CustomReward, PartialUser, parse_timestamp as _parse_datetime

if TYPE_CHECKING:
    from .server import EventSubClient

try:
    import ujson as json

    def _loads(s: str) -> dict:
        return json.loads(s)


except ModuleNotFoundError:
    import json

    def _loads(s: str) -> dict:
        return json.loads(s)


logger = logging.getLogger("twitchio.ext.eventsub")


class EmptyObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Subscription:
    __slots__ = "id", "status", "type", "version", "cost", "condition", "transport", "created_at"

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.status: str = data["status"]
        self.type: str = data["type"]
        self.version = int(data["version"])
        self.cost: int = data["cost"]
        self.condition: Dict[str, str] = data["condition"]
        self.created_at = _parse_datetime(data["created_at"])
        self.transport = EmptyObject()
        self.transport.method: str = data["transport"]["method"]  # noqa
        self.transport.callback: str = data["transport"]["callback"]  # noqa


class Headers:
    """
    The headers of the inbound EventSub message

    Attributes
    -----------
    message_id: :class:`str`
        The unique ID of the message
    message_retry: :class:`int`
        Unknown
    signature: :class:`str`
        The signature associated with the message
    subscription_type: :class:`str`
        The type of the subscription on the inbound message
    subscription_version: :class:`str`
        The version of the subscription.
    timestamp: :class:`datetime.datetime`
        The timestamp the message was sent at
    """

    def __init__(self, request: web.Request):
        self.message_id: str = request.headers["Twitch-Eventsub-Message-Id"]
        self.message_retry: int = int(request.headers["Twitch-Eventsub-Message-Retry"])
        self.message_type: str = request.headers["Twitch-Eventsub-Message-Type"]
        self.signature: str = request.headers["Twitch-Eventsub-Message-Signature"]
        self.subscription_type: str = request.headers["Twitch-Eventsub-Subscription-Type"]
        self.subscription_version: str = request.headers["Twitch-Eventsub-Subscription-Version"]
        self.timestamp = _parse_datetime(request.headers["Twitch-Eventsub-Message-Timestamp"])
        self._raw_timestamp = request.headers["Twitch-Eventsub-Message-Timestamp"]


class BaseEvent:
    """
    The base of all the event classes

    Attributes
    -----------
    subscription: :class:`Subscription`
        The subscription attached to the message
    headers: :class`Headers`
        The headers received with the message
    """

    __slots__ = "_client", "_raw_data", "subscription", "headers"

    def __init__(self, client: EventSubClient, data: str, request: web.Request):
        self._client = client
        self._raw_data = data
        _data: dict = _loads(data)
        self.subscription = Subscription(_data["subscription"])
        self.headers = Headers(request)
        self.setup(_data)

    def setup(self, data: dict):
        pass

    def verify(self):
        hmac_message = (self.headers.message_id + self.headers._raw_timestamp + self._raw_data).encode("utf-8")
        secret = self._client.secret.encode("utf-8")
        digest = hmac.new(secret, msg=hmac_message, digestmod=hashlib.sha256).hexdigest()

        if not hmac.compare_digest(digest, self.headers.signature[7:]):
            logger.warning(f"Recieved a message with an invalid signature, discarding.")
            return web.Response(status=400)

        return web.Response(status=200)


class RevokationEvent(BaseEvent):
    pass


class ChallengeEvent(BaseEvent):
    """
    A challenge event.

    Attributes
    -----------
    challenge: :class`str`
        The challenge received from twitch
    """

    __slots__ = ("challenge",)

    def setup(self, data: dict):
        self.challenge: str = data["challenge"]

    def verify(self):
        hmac_message = (self.headers.message_id + self.headers._raw_timestamp + self._raw_data).encode("utf-8")
        secret = self._client.secret.encode("utf-8")
        digest = hmac.new(secret, msg=hmac_message, digestmod=hashlib.sha256).hexdigest()

        if not hmac.compare_digest(digest, self.headers.signature[7:]):
            logger.warning(f"Recieved a message with an invalid signature, discarding.")
            return web.Response(status=400)

        return web.Response(status=200, text=self.challenge)


class NotificationEvent(BaseEvent):
    """
    A notification event

    Attributes
    -----------
    data: :class:`models._DataType`
        The data associated with this event
    """

    __slots__ = ("data",)

    def setup(self, _data: dict):
        data: dict = _data["event"]
        typ = self.subscription.type
        if typ not in SubscriptionTypes._type_map:
            raise ValueError(f"Unexpected subscription type '{typ}'")

        self.data: _DataType = SubscriptionTypes._type_map[typ](self._client, data)


def _transform_user(client: EventSubClient, data: dict, field: str) -> PartialUser:
    return client.client.create_user(int(data[field + "_id"]), data[field + "_name"])


class EventData:
    __slots__ = ()


class ChannelBanData(EventData):
    """
    A Ban event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user that was banned
    broadcaster: :class:`PartialUser`
        The broadcaster who's channel the ban occurred in
    moderator: :class:`PartialUser`
        The moderator responsible for the ban
    reason: :class:`str`
        The reason for the ban
    ends_at: Optional[:class:`datetime.datetime`]
        When the ban ends at. Could be ``None``
    permanant: :class:`bool`
        A typo of ``permanent``. Kept for backwards compatibility
    permanent: :class:`bool`
        Whether the ban is permanent
    """

    __slots__ = "user", "broadcaster", "moderator", "reason", "ends_at", "permenant", "permanent"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.moderator = _transform_user(client, data, "moderator_user")
        self.reason: str = data["reason"]
        self.ends_at: Optional[datetime.datetime] = data["ends_at"] and _parse_datetime(data["ends_at"])
        self.permenant: bool = data["is_permanent"]
        self.permanent = self.permenant  # fix the spelling while keeping backwards compat


class ChannelSubscribeData(EventData):
    """
    A Subscription event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user who subscribed
    broadcaster: :class:`PartialUser`
        The channel that was subscribed to
    tier: :class:`int`
        The tier of the subscription
    is_gift: :class:`bool`
        Whether the subscription was a gift or not
    """

    __slots__ = "user", "broadcaster", "tier", "is_gift"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.tier = int(data["tier"])
        self.is_gift: bool = data["is_gift"]


class ChannelCheerData(EventData):
    """
    A Cheer event

    Attributes
    ----------
    is_anonymous: :class:`bool`
        Whether the cheer was anonymous
    user: Optional[:class:`PartialUser`]
        The user that cheered. Will be ``None`` if ``is_anonymous`` is ``True``
    broadcaster: :class:`PartialUser`
        The channel the cheer happened on
    message: :class:`str`
        The message sent along with the bits
    bits: :class:`int`
        The amount of bits sent
    """

    __slots__ = "user", "broadcaster", "is_anonymous", "message", "bits"

    def __init__(self, client: EventSubClient, data: dict):
        self.is_anonymous: bool = data["is_anonymous"]
        self.user: Optional[PartialUser] = self.is_anonymous and _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.message: str = data["message"]
        self.bits = int(data["bits"])


class ChannelUpdateData(EventData):
    """
    A Channel Update event

    Attributes
    -----------
    broadcaster: :class:`PartialUser`
        The channel that was updated
    title: :class:`str`
        The title of the stream
    language: :class:`str`
        The language of the channel
    category_id: :class:`str`
        The category the stream is in
    category_name: :class:`str`
        The category the stream is in
    is_mature: :class:`bool`
        Whether the channel is marked as mature by the broadcaster
    """

    __slots__ = "broadcaster", "title", "language", "category_id", "category_name", "is_mature"

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.title: str = data["title"]
        self.language: str = data["language"]
        self.category_id: str = data["category_id"]
        self.category_name: str = data["category_name"]
        self.is_mature: bool = data["is_mature"] == "true"


class ChannelUnbanData(EventData):
    """
    A Channel Unban event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user that was unbanned
    broadcaster: :class:`PartialUser`
        The channel the unban occurred in
    moderator: :class`PartialUser`
        The moderator that preformed the unban
    """

    __slots__ = "user", "broadcaster", "moderator"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.moderator = _transform_user(client, data, "moderator_user")


class ChannelFollowData(EventData):
    """
    A Follow event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user that followed
    broadcaster: :class:`PartialUser`
        The channel that was followed
    followed_at: :class:`datetime.datetime`
        When the follow occurred
    """

    __slots__ = "user", "broadcaster", "followed_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.followed_at = _parse_datetime(data["followed_at"])


class ChannelRaidData(EventData):
    """
    A Raid event

    Attributes
    -----------
    raider: :class:`PartialUser`
        The person initiating the raid
    reciever: :class:`PartialUser`
        The person recieving the raid
    viewer_count: :class:`int`
        The amount of people raiding
    """

    __slots__ = "raider", "reciever", "viewer_count"

    def __init__(self, client: EventSubClient, data: dict):
        self.raider = _transform_user(client, data, "from_broadcaster_user")
        self.reciever = _transform_user(client, data, "to_broadcaster_user")
        self.viewer_count: int = data["viewers"]


class ChannelModeratorAddRemoveData(EventData):
    """
    A Moderator Add/Remove event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user being added or removed from the moderator status
    broadcaster: :class:`PartialUser`
        The channel that is having a moderator added/removed
    """

    __slots__ = "broadcaster", "user"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")


class CustomRewardAddUpdateRemoveData(EventData):
    """
    A Custom Reward Add/Update/Remove event

    Attributes
    -----------
    id: :class:`str`
        The ID of the custom reward
    broadcaster: :class:`PartialUser`
        The channel the custom reward was modified in
    reward: :class:`CustomReward`
        The reward object
    """

    __slots__ = "reward", "broadcaster", "id"

    def __init__(self, client: EventSubClient, data: dict):
        self.id: str = data["id"]
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.reward = CustomReward(client.client._http, data, self.broadcaster)


class CustomRewardRedemptionAddUpdateData(EventData):
    """
    A Custom Reward Redemption event

    Attributes
    -----------
    broadcaster: :class:PartialUser`
        The channel the redemption occurred in
    user: :class:`PartialUser`
        The user that redeemed the reward
    id: :class:`str`
        The ID of the redemption
    input: :class:`str`
        The user input, if present. This will be an empty string if it is not present
    status: :class:`str`
        One of "unknown", "unfulfilled", "fulfilled", or "cancelled"
    redeemed_at: :class:`datetime.datetime`
        When the reward was redeemed at
    reward: :class:`CustomReward`
        The reward object
    """

    __slots__ = "broadcaster", "id", "user", "input", "status", "reward", "redeemed_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.user = _transform_user(client, data, "user")
        self.id: str = data["id"]
        self.input: str = data["user_input"]
        self.status: Literal["unknown", "unfulfilled", "fulfilled", "cancelled"] = data["status"]
        self.redeemed_at = _parse_datetime(data["redeemed_at"])
        self.reward = CustomReward(client.client._http, data["reward"], self.broadcaster)


class HypeTrainContributor:
    """
    A Contributor to a Hype Train

    Attributes
    -----------
    user: :class:`PartialUser`
        The user
    type: :class:`str`
        One of "bits" or "subscription". The way they contributed to the hype train
    total: :class:`int`
        How many points they've contributed to the Hype Train
    """

    __slots__ = "user", "type", "total"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.type: Literal["bits", "subscription"] = data["type"]  # one of bits, subscription
        self.total: int = data["total"]


class HypeTrainBeginProgressData(EventData):
    """
    A Hype Train Begin/Progress event
    Attributes
    -----------
    broadcaster: :class:`PartialUser`
        The channel the Hype Train occurred in
    total_points: :class:`int`
        The total amounts of points in the Hype Train
    progress: :class:`int`
        The progress of the Hype Train towards the next level
    goal: :class:`int`
        The goal to reach the next level
    started: :class:`datetime.datetime`
        When the Hype Train started
    expires: :class:`datetime.datetime`
        When the Hype Train ends
    top_contributions: List[:class:`HypeTrainContributor`]
        The top contributions of the Hype Train
    last_contribution: :class:`HypeTrainContributor`
        The last contributor to the Hype Train
    """

    __slots__ = (
        "broadcaster",
        "total_points",
        "progress",
        "goal",
        "top_contributions",
        "last_contribution",
        "started",
        "expires",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.total_points: int = data["total"]
        self.progress: int = data["progress"]
        self.goal: int = data["goal"]
        self.started = _parse_datetime(data["started_at"])
        self.expires = _parse_datetime(data["expire_at"])
        self.top_contributions = [HypeTrainContributor(client, d) for d in data["top_contributions"]]
        self.last_contribution = HypeTrainContributor(client, data["last_contribution"])


class HypeTrainEndData(EventData):
    """
    A Hype Train End event

    Attributes
    -----------
    broadcaster: :class:`PartialUser`
        The channel the Hype Train occurred in
    total_points: :class:`int`
        The total amounts of points in the Hype Train
    level: :class:`int`
        The level the hype train reached
    started: :class:`datetime.datetime`
        When the Hype Train started
    top_contributions: List[:class:`HypeTrainContributor`]
        The top contributions of the Hype Train
    cooldown_ends_at: :class:`datetime.datetime`
        When another Hype Train can begin
    """

    __slots__ = "broadcaster", "level", "total_points", "top_contributions", "started", "ended", "cooldown_ends_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.total_points: int = data["total"]
        self.level: int = data["level"]
        self.started = _parse_datetime(data["started_at"])
        self.ended = _parse_datetime(data["ended_at"])
        self.cooldown_ends_at = _parse_datetime(data["cooldown_ends_at"])
        self.top_contributions = [HypeTrainContributor(client, d) for d in data["top_contributions"]]


class StreamOnlineData(EventData):
    """
    A Stream Start event

    Attributes
    -----------
    broadcaster: :class:`PartialUser`
        The channel that went live
    id: :class:`str`
        Some sort of ID for the stream
    type: :class:`str`
        One of "live", "playlist", "watch_party", "premier", or "rerun". The type of live event.
    started_at: :class:`datetime.datetime`
    """

    __slots__ = "broadcaster", "id", "type", "started_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.id: str = data["id"]
        self.type: Literal["live", "playlist", "watch_party", "premier", "rerun"] = data["type"]
        self.started_at = _parse_datetime(data["started_at"])


class StreamOfflineData(EventData):
    """
    A Stream End event

    Attributes
    -----------
    broadcaster: :class:`PartialUser`
        The channel that stopped streaming
    """

    __slots__ = ("broadcaster",)

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")


class UserAuthorizationRevokedData(EventData):
    """
    An Authorization Revokation event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user that has revoked authorization for your app
    client_id: :class:`str`
        The client id of the app that had its authorization revoked
    """

    __slots__ = "client_id", "user"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.client_id: str = data["client_id"]


class UserUpdateData(EventData):
    """
    A User Update event

    Attributes
    -----------
    user: :class:`PartialUser`
        The user that was updated
    email: Optional[:class:`str`]
        The users email, if you have permission to read this information
    description: :class:`str`
        The channels description (displayed as ``bio``)
    """

    __slots__ = "user", "email", "description"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.email: Optional[str] = data["email"]
        self.description: str = data["description"]


_DataType = Union[
    ChannelBanData,
    ChannelUnbanData,
    ChannelSubscribeData,
    ChannelCheerData,
    ChannelUpdateData,
    ChannelFollowData,
    ChannelRaidData,
    ChannelModeratorAddRemoveData,
    CustomRewardAddUpdateRemoveData,
    CustomRewardRedemptionAddUpdateData,
    HypeTrainBeginProgressData,
    HypeTrainEndData,
    StreamOnlineData,
    StreamOfflineData,
    UserAuthorizationRevokedData,
    UserUpdateData,
]


class _SubTypesMeta(type):
    def __new__(mcs, clsname, bases, attributes):
        attributes["_type_map"] = {args[0]: args[2] for name, args in attributes.items() if not name.startswith("_")}
        attributes["_name_map"] = {args[0]: name for name, args in attributes.items() if not name.startswith("_")}
        return super().__new__(mcs, clsname, bases, attributes)


class _SubscriptionTypes(metaclass=_SubTypesMeta):
    _type_map: Dict[str, Type[_DataType]]
    _name_map: Dict[str, str]

    follow = "channel.follow", 1, ChannelFollowData
    subscription = "channel.subscribe", 1, ChannelSubscribeData
    cheer = "channel.cheer", 1, ChannelCheerData
    raid = "channel.raid", 1, ChannelRaidData
    ban = "channel.ban", 1, ChannelBanData
    unban = "channel.unban", 1, ChannelUnbanData

    channel_update = "channel.update", 1, ChannelUpdateData
    channel_moderator_add = "channel.moderator.add", 1, ChannelModeratorAddRemoveData
    channel_moderator_remove = "channel.moderator.remove", 1, ChannelModeratorAddRemoveData
    channel_reward_add = "channel.channel_points_custom_reward.add", 1, CustomRewardAddUpdateRemoveData
    channel_reward_update = "channel.channel_points_custom_reward.update", 1, CustomRewardAddUpdateRemoveData
    channel_reward_remove = "channel.channel_points_custom_reward.remove", 1, CustomRewardAddUpdateRemoveData
    channel_reward_redeem = (
        "channel.channel_points_custom_reward_redemption.add",
        1,
        CustomRewardRedemptionAddUpdateData,
    )
    channel_reward_redeem_updated = (
        "channel.channel_points_custom_reward_redemption.update",
        1,
        CustomRewardRedemptionAddUpdateData,
    )

    hypetrain_begin = "channel.hype_train.begin", 1, HypeTrainBeginProgressData
    hypetrain_progress = "channel.hype_train.progress", 1, HypeTrainBeginProgressData
    hypetrain_end = "channel.hype_train.end", 1, HypeTrainEndData

    stream_start = "stream.online", 1, StreamOnlineData
    stream_end = "stream.offline", 1, StreamOfflineData

    user_authorization_revoke = "user.authorization.revoke", 1, UserAuthorizationRevokedData

    user_update = "user.update", 1, UserUpdateData


SubscriptionTypes = _SubscriptionTypes()
