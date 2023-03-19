from __future__ import annotations
import datetime
import hmac
import hashlib
import logging
from enum import Enum
from typing import Dict, TYPE_CHECKING, Optional, Type, Union, Tuple, List
from typing_extensions import Literal

from aiohttp import web

from twitchio import PartialUser, parse_timestamp as _parse_datetime

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
    user: :class:`twitchio.PartialUser`
        The user that was banned
    broadcaster: :class:`twitchio.PartialUser`
        The broadcaster who's channel the ban occurred in
    moderator: :class:`twitchio.PartialUser`
        The moderator responsible for the ban
    reason: :class:`str`
        The reason for the ban
    ends_at: Optional[:class:`datetime.datetime`]
        When the ban ends at. Could be ``None``
    permanant: :class:`bool`
        A typo of ``permanent`` Kept for backwards compatibility
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
    user: :class:`twitchio.PartialUser`
        The user who subscribed
    broadcaster: :class:`twitchio.PartialUser`
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


class ChannelSubscriptionEndData(EventData):
    """
    A Subscription End event

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The user who subscribed
    broadcaster: :class:`twitchio.PartialUser`
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


class ChannelSubscriptionGiftData(EventData):
    """
    A Subscription Gift event
    Explicitly, the act of giving another user a Subscription.
    Receiving a gift-subscription uses ChannelSubscribeData above, with is_gift is ``True``

    Attributes
    -----------
    is_anonymous: :class:`bool`
        Whether the gift sub was anonymous
    user: Optional[:class:`twitchio.PartialUser`]
        The user that gifted subs. Will be ``None`` if ``is_anonymous`` is ``True``
    broadcaster: :class:`twitchio.PartialUser`
        The channel that was subscribed to
    tier: :class:`int`
        The tier of the subscription
    total: :class:`int`
        The total number of subs gifted by a user at once
    cumulative_total: Optional[:class:`int`]
        The total number of subs gifted by a user overall. Will be ``None`` if ``is_anonymous`` is ``True``
    """

    __slots__ = "is_anonymous", "user", "broadcaster", "tier", "total", "cumulative_total"

    def __init__(self, client: EventSubClient, data: dict):
        self.is_anonymous: bool = data["is_anonymous"]
        self.user: Optional[PartialUser] = None if self.is_anonymous else _transform_user(client, data, "user")
        self.broadcaster: Optional[PartialUser] = _transform_user(client, data, "broadcaster_user")
        self.tier = int(data["tier"])
        self.total = int(data["total"])
        self.cumulative_total: Optional[int] = None if self.is_anonymous else int(data["cumulative_total"])


class ChannelSubscriptionMessageData(EventData):
    """
    A Subscription Message event.
    A combination of resubscriptions + the messages users type as part of the resub.

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The user who subscribed
    broadcaster: :class:`twitchio.PartialUser`
        The channel that was subscribed to
    tier: :class:`int`
        The tier of the subscription
    message: :class:`str`
        The user's resubscription message
    emote_data: :class:`list`
        emote data within the user's resubscription message. Not the emotes themselves
    cumulative_months: :class:`int`
        The total number of months a user has subscribed to the channel
    streak: Optional[:class:`int`]
        The total number of months subscribed in a row. ``None`` if the user declines to share it.
    duration: :class:`int`
        The length of the subscription. Typically 1, but some users may buy subscriptions for several months.
    """

    __slots__ = "user", "broadcaster", "tier", "message", "emote_data", "cumulative_months", "streak", "duration"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.tier = int(data["tier"])
        self.message: str = data["message"]["text"]
        self.emote_data: List[Dict] = data["message"].get("emotes", [])
        self.cumulative_months: int = data["cumulative_months"]
        self.streak: Optional[int] = data["streak_months"]
        self.duration: int = data["duration_months"]


class ChannelCheerData(EventData):
    """
    A Cheer event

    Attributes
    ----------
    is_anonymous: :class:`bool`
        Whether the cheer was anonymous
    user: Optional[:class:`twitchio.PartialUser`]
        The user that cheered. Will be ``None`` if ``is_anonymous`` is ``True``
    broadcaster: :class:`twitchio.PartialUser`
        The channel the cheer happened on
    message: :class:`str`
        The message sent along with the bits
    bits: :class:`int`
        The amount of bits sent
    """

    __slots__ = "user", "broadcaster", "is_anonymous", "message", "bits"

    def __init__(self, client: EventSubClient, data: dict):
        self.is_anonymous: bool = data["is_anonymous"]
        self.user: Optional[PartialUser] = _transform_user(client, data, "user") if not self.is_anonymous else None
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.message: str = data["message"]
        self.bits = int(data["bits"])


class ChannelUpdateData(EventData):
    """
    A Channel Update event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
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
    user: :class:`twitchio.PartialUser`
        The user that was unbanned
    broadcaster: :class:`twitchio.PartialUser`
        The channel the unban occurred in
    moderator: :class`twitchio.PartialUser`
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
    user: :class:`twitchio.PartialUser`
        The user that followed
    broadcaster: :class:`twitchio.PartialUser`
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
    raider: :class:`twitchio.PartialUser`
        The person initiating the raid
    reciever: :class:`twitchio.PartialUser`
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
    user: :class:`twitchio.PartialUser`
        The user being added or removed from the moderator status
    broadcaster: :class:`twitchio.PartialUser`
        The channel that is having a moderator added/removed
    """

    __slots__ = "broadcaster", "user"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.broadcaster = _transform_user(client, data, "broadcaster_user")


class CustomReward:
    """
    A Custom Reward

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel that has this reward
    id: :class:`str`
        The ID of the reward
    title: :class:`str`
        The title of the reward
    cost: :class:`int`
        The cost of the reward in Channel Points
    prompt: :class:`str`
        The prompt of the reward
    enabled: Optional[:class:`bool`]
        Whether or not the reward is enabled. Will be `None` for Redemption events.
    paused: Optional[:class:`bool`]
        Whether or not the reward is paused. Will be `None` for Redemption events.
    in_stock: Optional[:class:`bool`]
        Whether or not the reward is in stock. Will be `None` for Redemption events.
    cooldown_until: Optional[:class:`datetime.datetime`]
        How long until the reward is off cooldown and can be redeemed again. Will be `None` for Redemption events.
    input_required: Optional[:class:`bool`]
        Whether or not the reward requires an input. Will be `None` for Redemption events.
    redemptions_skip_queue: Optional[:class:`bool`]
        Whether or not redemptions for this reward skips the queue. Will be `None` for Redemption events.
    redemptions_current_stream: Optional[:class:`int`]
        How many redemptions of this reward have been redeemed for this stream. Will be `None` for Redemption events.
    max_per_stream: Tuple[:class:`bool`, :class:`int`]
        Whether or not a per-stream redemption limit is in place, and if so, the maximum number of redemptions allowed
        per stream. Will be `None` for Redemption events.
    max_per_user_per_stream: Tuple[:class:`bool`, :class:`int`]
        Whether or not a per-user-per-stream redemption limit is in place, and if so, the maximum number of redemptions
        allowed per user per stream. Will be `None` for Redemption events.
    cooldown: Tuple[:class:`bool`, :class:`int`]
        Whether or not a global cooldown is in place, and if so, the number of seconds until the reward can be redeemed
        again. Will be `None` for Redemption events.
    background_color: Optional[:class:`str`]
        Hexadecimal color code for the background of the reward.
    image: Optional[:class:`str`]
        Image URL for the reward.
    """

    __slots__ = (
        "broadcaster",
        "id",
        "title",
        "cost",
        "prompt",
        "enabled",
        "paused",
        "in_stock",
        "cooldown_until",
        "input_required",
        "redemptions_skip_queue",
        "redemptions_current_stream",
        "max_per_stream",
        "max_per_user_stream",
        "cooldown",
        "background_color",
        "image",
    )

    def __init__(self, data, broadcaster):
        self.broadcaster: PartialUser = broadcaster

        self.id: str = data["id"]

        self.title: str = data["title"]
        self.cost: int = data["cost"]
        self.prompt: str = data["prompt"]

        self.enabled: Optional[bool] = data.get("is_enabled", None)
        self.paused: Optional[bool] = data.get("is_paused", None)
        self.in_stock: Optional[bool] = data.get("is_in_stock", None)

        self.cooldown_until: Optional[datetime.datetime] = (
            _parse_datetime(data["cooldown_expires_at"]) if data.get("cooldown_expires_at", None) else None
        )

        self.input_required: Optional[bool] = data.get("is_user_input_required", None)
        self.redemptions_skip_queue: Optional[bool] = data.get("should_redemptions_skip_request_queue", None)
        self.redemptions_current_stream: Optional[bool] = data.get("redemptions_redeemed_current_stream", None)

        self.max_per_stream: Tuple[Optional[bool], Optional[int]] = (
            data.get("max_per_stream", {}).get("is_enabled"),
            data.get("max_per_stream", {}).get("value"),
        )
        self.max_per_user_stream: Tuple[Optional[bool], Optional[int]] = (
            data.get("max_per_user_per_stream", {}).get("is_enabled"),
            data.get("max_per_user_per_stream", {}).get("value"),
        )
        self.cooldown: Tuple[Optional[bool], Optional[int]] = (
            data.get("global_cooldown", {}).get("is_enabled"),
            data.get("global_cooldown", {}).get("seconds"),
        )

        self.background_color: Optional[str] = data.get("background_color", None)
        self.image: Optional[str] = data.get("image", data.get("default_image", {})).get("url_1x", None)


class CustomRewardAddUpdateRemoveData(EventData):
    """
    A Custom Reward Add/Update/Remove event

    Attributes
    -----------
    id: :class:`str`
        The ID of the custom reward
    broadcaster: :class:`twitchio.PartialUser`
        The channel the custom reward was modified in
    reward: :class:`CustomReward`
        The reward object
    """

    __slots__ = "reward", "broadcaster", "id"

    def __init__(self, client: EventSubClient, data: dict):
        self.id: str = data["id"]
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.reward = CustomReward(data, self.broadcaster)


class CustomRewardRedemptionAddUpdateData(EventData):
    """
    A Custom Reward Redemption event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel the redemption occurred in
    user: :class:`twitchio.PartialUser`
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
        self.reward = CustomReward(data["reward"], self.broadcaster)


class HypeTrainContributor:
    """
    A Contributor to a Hype Train

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The user
    type: :class:`str`
        One of "bits, "subscription" or "other". The way they contributed to the hype train
    total: :class:`int`
        How many points they've contributed to the Hype Train
    """

    __slots__ = "user", "type", "total"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.type: Literal["bits", "subscription", "other"] = data["type"]  # one of bits, subscription
        self.total: int = data["total"]


class HypeTrainBeginProgressData(EventData):
    """
    A Hype Train Begin/Progress event

    Attributes
    -----------

    broadcaster: :class:`twitchio.PartialUser`
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
    level: :class:`int`
        The current level of the Hype Train
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
        "level",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.total_points: int = data["total"]
        self.progress: int = data["progress"]
        self.goal: int = data["goal"]
        self.started = _parse_datetime(data["started_at"])
        self.expires = _parse_datetime(data["expires_at"])
        self.top_contributions = [HypeTrainContributor(client, d) for d in data["top_contributions"]]
        self.last_contribution = HypeTrainContributor(client, data["last_contribution"])
        self.level: int = data["level"]


class HypeTrainEndData(EventData):
    """
    A Hype Train End event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
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


class PollChoice:
    """
    A Poll Choice

    Attributes
    -----------
    choice_id: :class:`str`
        The ID of the choice
    title: :class:`str`
        The title of the choice
    bits_votes: :class:`int`
        How many votes were cast using Bits

        .. warning::

            Twitch have removed support for voting with bits.
            This will return as 0

    channel_points_votes: :class:`int`
        How many votes were cast using Channel Points
    votes: :class:`int`
        The total number of votes, including votes cast using Bits and Channel Points
    """

    __slots__ = "choice_id", "title", "bits_votes", "channel_points_votes", "votes"

    def __init__(self, data):
        self.choice_id: str = data["id"]
        self.title: str = data["title"]
        self.bits_votes: int = data.get("bits_votes", 0)
        self.channel_points_votes: int = data.get("channel_points_votes", 0)
        self.votes: int = data.get("votes", 0)


class BitsVoting:
    """
    Information on voting on a poll with Bits

    Attributes
    -----------
    is_enabled: :class:`bool`
        Whether users can use Bits to vote on the poll
    amount_per_vote: :class:`int`
        How many Bits are required to cast an extra vote

        .. warning::

            Twitch have removed support for voting with bits.
            This will return as False and 0 respectively

    """

    __slots__ = "is_enabled", "amount_per_vote"

    def __init__(self, data):
        self.is_enabled: bool = data["is_enabled"]
        self.amount_per_vote: int = data["amount_per_vote"]


class ChannelPointsVoting:
    """
    Information on voting on a poll with Channel Points

    Attributes
    -----------
    is_enabled: :class:`bool`
        Whether users can use Channel Points to vote on the poll
    amount_per_vote: :class:`int`
        How many Channel Points are required to cast an extra vote
    """

    __slots__ = "is_enabled", "amount_per_vote"

    def __init__(self, data):
        self.is_enabled: bool = data["is_enabled"]
        self.amount_per_vote: int = data["amount_per_vote"]


class PollStatus(Enum):
    """
    The status of a poll.

    ACTIVE: Poll is currently in progress.
    COMPLETED: Poll has reached its `ended_at` time.
    TERMINATED: Poll has been manually terminated before its `ended_at` time.
    ARCHIVED: Poll is no longer visible on the channel.
    MODERATED: Poll is no longer visible to any user on Twitch.
    INVALID: Something went wrong determining the state.
    """

    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    ARCHIVED = "archived"
    MODERATED = "moderated"
    INVALID = "invalid"


class PollBeginProgressData(EventData):
    """
    A Poll Begin/Progress event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel the poll occured in
    poll_id: :class:`str`
        The ID of the poll
    title: :class:`str`
        The title of the poll
    choices: List[:class:`PollChoice`]
        The choices in the poll
    bits_voting: :class:`BitsVoting`
        Information on voting on the poll with Bits

        .. warning::

            Twitch have removed support for voting with bits.

    channel_points_voting: :class:`ChannelPointsVoting`
        Information on voting on the poll with Channel Points
    started_at: :class:`datetime.datetime`
        When the poll started
    ends_at: :class:`datetime.datetime`
        When the poll is set to end
    ...
    """

    __slots__ = (
        "broadcaster",
        "poll_id",
        "title",
        "choices",
        "bits_voting",
        "channel_points_voting",
        "started_at",
        "ends_at",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.poll_id: str = data["id"]
        self.title: str = data["title"]
        self.choices = [PollChoice(c) for c in data["choices"]]
        self.bits_voting = BitsVoting(data["bits_voting"])
        self.channel_points_voting = ChannelPointsVoting(data["channel_points_voting"])
        self.started_at = _parse_datetime(data["started_at"])
        self.ends_at = _parse_datetime(data["ends_at"])


class PollEndData(EventData):
    """
    A Poll End event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel the poll occured in
    poll_id: :class:`str`
        The ID of the poll
    title: :class:`str`
        The title of the poll
    choices: List[:class:`PollChoice`]
        The choices in the poll
    bits_voting: :class:`BitsVoting`
        Information on voting on the poll with Bits

        .. warning::

            Twitch have removed support for voting with bits.

    channel_points_voting: :class:`ChannelPointsVoting`
        Information on voting on the poll with Channel Points
    status: :class:`PollStatus`
        How the poll ended
    started_at: :class:`datetime.datetime`
        When the poll started
    ended_at: :class:`datetime.datetime`
        When the poll is set to end
    """

    __slots__ = (
        "broadcaster",
        "poll_id",
        "title",
        "choices",
        "bits_voting",
        "channel_points_voting",
        "status",
        "started_at",
        "ended_at",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.poll_id: str = data["id"]
        self.title: str = data["title"]
        self.choices = [PollChoice(c) for c in data["choices"]]
        self.bits_voting = BitsVoting(data["bits_voting"])
        self.channel_points_voting = ChannelPointsVoting(data["channel_points_voting"])
        self.status = PollStatus(data["status"].lower())
        self.started_at = _parse_datetime(data["started_at"])
        self.ended_at = _parse_datetime(data["ended_at"])


class Predictor:
    """
    A Predictor

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The user who predicted an outcome
    channel_points_used: :class:`int`
        How many Channel Points the user used to predict this outcome
    channel_points_won: :class:`int`
        How many Channel Points was distributed to the user.
        Will be `None` if the Prediction is unresolved, cancelled (refunded), or the user predicted the losing outcome.
    """

    __slots__ = "user", "channel_points_used", "channel_points_won"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.channel_points_used: int = data["channel_points_used"]
        self.channel_points_won: int = data["channel_points_won"]


class PredictionOutcome:
    """
    A Prediction Outcome

    Attributes
    -----------
    outcome_id: :class:`str`
        The ID of the outcome
    title: :class:`str`
        The title of the outcome
    channel_points: :class:`int`
        The amount of Channel Points that have been bet for this outcome
    color: :class:`str`
        The color of the outcome. Can be `blue` or `pink`
    users: :class:`int`
        The number of users who predicted the outcome
    top_predictors: List[:class:`Predictor`]
        The top predictors of the outcome
    """

    __slots__ = "outcome_id", "title", "channel_points", "color", "users", "top_predictors"

    def __init__(self, client: EventSubClient, data: dict):
        self.outcome_id: str = data["id"]
        self.title: str = data["title"]
        self.channel_points: int = data.get("channel_points", 0)
        self.color: str = data["color"]
        self.users: int = data.get("users", 0)
        self.top_predictors = [Predictor(client, x) for x in data.get("top_predictors", [])]

    @property
    def colour(self) -> str:
        """The colour of the prediction. Alias to color."""
        return self.color


class PredictionStatus(Enum):
    """
    The status of a Prediction.

    ACTIVE: Prediction is active and viewers can make predictions.
    LOCKED: Prediction has been locked and viewers can no longer make predictions.
    RESOLVED: A winning outcome has been chosen and the Channel Points have been distributed to the users who guessed the correct outcome.
    CANCELED: Prediction has been canceled and the Channel Points have been refunded to participants.
    """

    ACTIVE = "active"
    LOCKED = "locked"
    RESOLVED = "resolved"
    CANCELED = "canceled"


class PredictionBeginProgressData(EventData):
    """
    A Prediction Begin/Progress event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel the prediction occured in
    prediction_id: :class:`str`
        The ID of the prediction
    title: :class:`str`
        The title of the prediction
    outcomes: List[:class:`PredictionOutcome`]
        The outcomes for the prediction
    started_at: :class:`datetime.datetime`
        When the prediction started
    locks_at: :class:`datetime.datetime`
        When the prediction is set to be locked
    """

    __slots__ = "broadcaster", "prediction_id", "title", "outcomes", "started_at", "locks_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.prediction_id: str = data["id"]
        self.title: str = data["title"]
        self.outcomes = [PredictionOutcome(client, x) for x in data["outcomes"]]
        self.started_at = _parse_datetime(data["started_at"])
        self.locks_at = _parse_datetime(data["locks_at"])


class PredictionLockData(EventData):
    """
    A Prediction Begin/Progress event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel the prediction occured in
    prediction_id: :class:`str`
        The ID of the prediction
    title: :class:`str`
        The title of the prediction
    outcomes: List[:class:`PredictionOutcome`]
        The outcomes for the prediction
    started_at: :class:`datetime.datetime`
        When the prediction started
    locked_at: :class:`datetime.datetime`
        When the prediction was locked
    """

    __slots__ = "broadcaster", "prediction_id", "title", "outcomes", "started_at", "locked_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.prediction_id: str = data["id"]
        self.title: str = data["title"]
        self.outcomes = [PredictionOutcome(client, x) for x in data["outcomes"]]
        self.started_at = _parse_datetime(data["started_at"])
        self.locked_at = _parse_datetime(data["locked_at"])


class PredictionEndData(EventData):
    """
    A Prediction Begin/Progress event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
        The channel the prediction occured in
    prediction_id: :class:`str`
        The ID of the prediction
    title: :class:`str`
        The title of the prediction
    winning_outcome_id: :class:`str`
        The ID of the outcome that won
    outcomes: List[:class:`PredictionOutcome`]
        The outcomes for the prediction
    status: :class:`PredictionStatus`
        How the prediction ended
    started_at: :class:`datetime.datetime`
        When the prediction started
    ended_at: :class:`datetime.datetime`
        When the prediction ended
    """

    __slots__ = (
        "broadcaster",
        "prediction_id",
        "title",
        "winning_outcome_id",
        "outcomes",
        "status",
        "started_at",
        "ended_at",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")
        self.prediction_id: str = data["id"]
        self.title: str = data["title"]
        self.winning_outcome_id: str = data["winning_outcome_id"]
        self.outcomes = [PredictionOutcome(client, x) for x in data["outcomes"]]
        self.status = PredictionStatus(data["status"].lower())
        self.started_at = _parse_datetime(data["started_at"])
        self.ended_at = _parse_datetime(data["ended_at"])


class StreamOnlineData(EventData):
    """
    A Stream Start event

    Attributes
    -----------
    broadcaster: :class:`twitchio.PartialUser`
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
    broadcaster: :class:`twitchio.PartialUser`
        The channel that stopped streaming
    """

    __slots__ = ("broadcaster",)

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster = _transform_user(client, data, "broadcaster_user")


class UserAuthorizationGrantedData(EventData):
    """
    An Authorization Granted event

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The user that has granted authorization for your app
    client_id: :class:`str`
        The client id of the app that had its authorization granted
    """

    __slots__ = "client_id", "user"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "user")
        self.client_id: str = data["client_id"]


class UserAuthorizationRevokedData(EventData):
    """
    An Authorization Revokation event

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
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
    user: :class:`twitchio.PartialUser`
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


class ChannelGoalBeginProgressData(EventData):
    """
    A goal begin event

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The broadcaster that started the goal
    id : :class:`str`
        The ID of the goal event
    type: :class:`str`
        The goal type
    description: :class:`str`
        The goal description
    current_amount: :class:`int`
        The goal current amount
    target_amount: :class:`int`
        The goal target amount
    started_at: :class:`datetime.datetime`
        The datetime the goal was started
    """

    __slots__ = "user", "id", "type", "description", "current_amount", "target_amount", "started_at"

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "broadcaster_user")
        self.id: str = data["id"]
        self.type: str = data["type"]
        self.description: str = data["description"]
        self.current_amount: int = data["current_amount"]
        self.target_amount: int = data["target_amount"]
        self.started_at: datetime.datetime = _parse_datetime(data["started_at"])


class ChannelGoalEndData(EventData):
    """
    A goal end event

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The broadcaster that ended the goal
    id : :class:`str`
        The ID of the goal event
    type: :class:`str`
        The goal type
    description: :class:`str`
        The goal description
    is_achieved: :class:`bool`
        Whether the goal is achieved
    current_amount: :class:`int`
        The goal current amount
    target_amount: :class:`int`
        The goal target amount
    started_at: :class:`datetime.datetime`
        The datetime the goal was started
    ended_at: :class:`datetime.datetime`
        The datetime the goal was ended
    """

    __slots__ = (
        "user",
        "id",
        "type",
        "description",
        "current_amount",
        "target_amount",
        "started_at",
        "is_achieved",
        "ended_at",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.user = _transform_user(client, data, "broadcaster_user")
        self.id: str = data["id"]
        self.type: str = data["type"]
        self.description: str = data["description"]
        self.is_achieved: bool = data["is_achieved"]
        self.current_amount: int = data["current_amount"]
        self.target_amount: int = data["target_amount"]
        self.started_at: datetime.datetime = _parse_datetime(data["started_at"])
        self.ended_at: datetime.datetime = _parse_datetime(data["ended_at"])


class ChannelShieldModeBeginData(EventData):
    """
    Represents a Shield Mode activation status.

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster whose Shield Mode status was updated.
    moderator: :class:`~twitchio.PartialUser`
        The moderator that updated the Shield Mode staus.
    started_at: :class:`datetime.datetime`
        The UTC datetime of when Shield Mode was last activated.
    """

    __slots__ = ("broadcaster", "moderator", "started_at")

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster: PartialUser = _transform_user(client, data, "broadcaster_user")
        self.moderator: PartialUser = _transform_user(client, data, "moderator_user")
        self.started_at: datetime.datetime = _parse_datetime(data["started_at"])


class ChannelShieldModeEndData(EventData):
    """
    Represents a Shield Mode activation status.

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster whose Shield Mode status was updated.
    moderator: :class:`~twitchio.PartialUser`
        The moderator that updated the Shield Mode staus.
    ended_at: :class:`datetime.datetime`
        The UTC datetime of when Shield Mode was last deactivated.
    """

    __slots__ = ("broadcaster", "moderator", "ended_at")

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster: PartialUser = _transform_user(client, data, "broadcaster_user")
        self.moderator: PartialUser = _transform_user(client, data, "moderator_user")
        self.ended_at: datetime.datetime = _parse_datetime(data["ended_at"])


class ChannelShoutoutCreateData(EventData):
    """
    Represents a Shoutout event being sent.

    Requires the ``moderator:read:shoutouts`` or ``moderator:manage:shoutouts`` scope.

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster from who sent the shoutout event.
    moderator: :class:`~twitchio.PartialUser`
        The moderator who sent the shoutout event.
    to_broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster who the shoutout was sent to.
    started_at: :class:`datetime.datetime`
        The datetime the shoutout was sent.
    viewer_count: :class:`int`
        The viewer count at the time of the shoutout
    cooldown_ends_at: :class:`datetime.datetime`
        The datetime the broadcaster can send another shoutout.
    target_cooldown_ends_at: :class:`datetime.datetime`
        The datetime the broadcaster can send another shoutout to the same broadcaster.
    """

    __slots__ = (
        "broadcaster",
        "moderator",
        "to_broadcaster",
        "started_at",
        "viewer_count",
        "cooldown_ends_at",
        "target_cooldown_ends_at",
    )

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster: PartialUser = _transform_user(client, data, "broadcaster_user")
        self.moderator: PartialUser = _transform_user(client, data, "moderator_user")
        self.to_broadcaster: PartialUser = _transform_user(client, data, "to_broadcaster_user")
        self.started_at: datetime.datetime = _parse_datetime(data["started_at"])
        self.viewer_count: int = data["viewer_count"]
        self.cooldown_ends_at: datetime.datetime = _parse_datetime(data["cooldown_ends_at"])
        self.target_cooldown_ends_at: datetime.datetime = _parse_datetime(data["target_cooldown_ends_at"])


class ChannelShoutoutReceiveData(EventData):
    """
    Represents a Shoutout event being received.

    Requires the ``moderator:read:shoutouts`` or ``moderator:manage:shoutouts`` scope.

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster receiving shoutout event.
    from_broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster who sent the shoutout.
    started_at: :class:`datetime.datetime`
        The datetime the shoutout was sent.
    viewer_count: :class:`int`
        The viewer count at the time of the shoutout
    """

    __slots__ = ("broadcaster", "from_broadcaster", "started_at", "viewer_count")

    def __init__(self, client: EventSubClient, data: dict):
        self.broadcaster: PartialUser = _transform_user(client, data, "broadcaster_user")
        self.from_broadcaster: PartialUser = _transform_user(client, data, "to_broadcaster_user")
        self.started_at: datetime.datetime = _parse_datetime(data["started_at"])
        self.viewer_count: int = data["viewer_count"]


_DataType = Union[
    ChannelBanData,
    ChannelUnbanData,
    ChannelSubscribeData,
    ChannelSubscriptionEndData,
    ChannelSubscriptionGiftData,
    ChannelSubscriptionMessageData,
    ChannelCheerData,
    ChannelUpdateData,
    ChannelFollowData,
    ChannelRaidData,
    ChannelModeratorAddRemoveData,
    ChannelGoalBeginProgressData,
    ChannelGoalEndData,
    CustomRewardAddUpdateRemoveData,
    CustomRewardRedemptionAddUpdateData,
    HypeTrainBeginProgressData,
    HypeTrainEndData,
    PollBeginProgressData,
    PollEndData,
    PredictionBeginProgressData,
    PredictionLockData,
    PredictionEndData,
    StreamOnlineData,
    StreamOfflineData,
    UserAuthorizationGrantedData,
    UserAuthorizationRevokedData,
    UserUpdateData,
    ChannelShieldModeBeginData,
    ChannelShieldModeEndData,
    ChannelShoutoutCreateData,
    ChannelShoutoutReceiveData,
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
    followV2 = "channel.follow", 2, ChannelFollowData
    subscription = "channel.subscribe", 1, ChannelSubscribeData
    subscription_end = "channel.subscription.end", 1, ChannelSubscriptionEndData
    subscription_gift = "channel.subscription.gift", 1, ChannelSubscriptionGiftData
    subscription_message = "channel.subscription.message", 1, ChannelSubscriptionMessageData
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

    channel_goal_begin = "channel.goal.begin", 1, ChannelGoalBeginProgressData
    channel_goal_progress = "channel.goal.progress", 1, ChannelGoalBeginProgressData
    channel_goal_end = "channel.goal.end", 1, ChannelGoalEndData

    channel_shield_mode_begin = "channel.shield_mode.begin", 1, ChannelShieldModeBeginData
    channel_shield_mode_end = "channel.shield_mode.end", 1, ChannelShieldModeEndData

    channel_shoutout_create = "channel.shoutout.create", 1, ChannelShoutoutCreateData
    channel_shoutout_receive = "channel.shoutout.receive", 1, ChannelShoutoutReceiveData

    hypetrain_begin = "channel.hype_train.begin", 1, HypeTrainBeginProgressData
    hypetrain_progress = "channel.hype_train.progress", 1, HypeTrainBeginProgressData
    hypetrain_end = "channel.hype_train.end", 1, HypeTrainEndData

    poll_begin = "channel.poll.begin", 1, PollBeginProgressData
    poll_progress = "channel.poll.progress", 1, PollBeginProgressData
    poll_end = "channel.poll.end", 1, PollEndData

    prediction_begin = "channel.prediction.begin", 1, PredictionBeginProgressData
    prediction_progress = "channel.prediction.progress", 1, PredictionBeginProgressData
    prediction_lock = "channel.prediction.lock", 1, PredictionLockData
    prediction_end = "channel.prediction.end", 1, PredictionEndData

    stream_start = "stream.online", 1, StreamOnlineData
    stream_end = "stream.offline", 1, StreamOfflineData

    user_authorization_grant = "user.authorization.grant", 1, UserAuthorizationGrantedData
    user_authorization_revoke = "user.authorization.revoke", 1, UserAuthorizationRevokedData

    user_update = "user.update", 1, UserUpdateData


SubscriptionTypes = _SubscriptionTypes()
