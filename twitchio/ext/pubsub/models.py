"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


from typing import List, Optional

from twitchio import PartialUser, Client, Channel, CustomReward, parse_timestamp


__all__ = (
    "PoolError",
    "PoolFull",
    "PubSubMessage",
    "PubSubBitsMessage",
    "PubSubBitsBadgeMessage",
    "PubSubChatMessage",
    "PubSubBadgeEntitlement",
    "PubSubChannelPointsMessage",
    "PubSubModerationAction",
    "PubSubModerationActionModeratorAdd",
    "PubSubModerationActionBanRequest",
    "PubSubModerationActionChannelTerms",
    "PubSubChannelSubscribe",
)


class PubSubError(Exception):
    pass


class ConnectionFailure(PubSubError):
    pass


class PoolError(PubSubError):
    pass


class PoolFull(PoolError):
    pass


class PubSubChatMessage:
    """
    A message received from twitch.

    Attributes
    -----------
    content: :class:`str`
        The content received
    id: :class:`str`
        The id of the payload
    type: :class:`str`
        The payload type
    """

    __slots__ = "content", "id", "type"

    def __init__(self, content: str, id: str, type: str):
        self.content = content
        self.id = id
        self.type = type


class PubSubBadgeEntitlement:
    """
    A badge entitlement

    Attributes
    -----------
    new: :class:`int`
        The new badge
    old: :class:`int`
        The old badge
    """

    __slots__ = "new", "old"

    def __init__(self, new: int, old: int):
        self.new = new
        self.old = old


class PubSubMessage:
    """
    A message from the pubsub websocket

    Attributes
    -----------
    topic: :class:`str`
        The topic subscribed to
    """

    __slots__ = "topic", "_data"

    def __init__(self, client: Client, topic: Optional[str], data: dict):
        self.topic = topic
        self._data = data


class PubSubBitsMessage(PubSubMessage):
    """
    A Bits message

    Attributes
    -----------
    message: :class:`PubSubChatMessage`
        The message sent along with the bits.
    badge_entitlement: Optional[:class:`PubSubBadgeEntitlement`]
        The badges received, if any.
    bits_used: :class:`int`
        The amount of bits used.
    channel_id: :class:`int`
        The channel the bits were given to.
    user: Optional[:class:`twitchio.PartialUser`]
        The user giving the bits. Can be None if anonymous.
    version: :class:`str`
        The event version.
    """

    __slots__ = "badge_entitlement", "bits_used", "channel_id", "context", "anonymous", "message", "user", "version"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)

        data = data["message"]
        self.message = PubSubChatMessage(data["data"]["chat_message"], data["message_id"], data["message_type"])
        self.badge_entitlement = (
            PubSubBadgeEntitlement(
                data["data"]["badge_entitlement"]["new_version"], data["data"]["badge_entitlement"]["old_version"]
            )
            if data["data"]["badge_entitlement"]
            else None
        )
        self.bits_used: int = data["data"]["bits_used"]
        self.channel_id: int = int(data["data"]["channel_id"])
        self.user = (
            PartialUser(client._http, data["data"]["user_id"], data["data"]["user_name"])
            if data["data"]["user_id"]
            else None
        )
        self.version: str = data["version"]


class PubSubBitsBadgeMessage(PubSubMessage):
    """
    A Badge message

    Attributes
    -----------
    user: :class:`twitchio.PartialUser`
        The user receiving the badge.
    channel: :class:`twitchio.Channel`
        The channel the user received the badge on.
    badge_tier: :class:`int`
        The tier of the badge
    message: :class:`str`
        The message sent in chat.
    timestamp: :class:`datetime.datetime`
        The time the event happened
    """

    __slots__ = "user", "channel", "badge_tier", "message", "timestamp"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        data = data["message"]
        self.user = PartialUser(client._http, data["user_id"], data["user_name"])
        self.channel: Channel = client.get_channel(data["channel_name"]) or Channel(
            name=data["channel_name"], websocket=client._connection
        )
        self.badge_tier: int = data["badge_tier"]
        self.message: str = data["chat_message"]
        self.timestamp = parse_timestamp(data["time"])


class PubSubChannelPointsMessage(PubSubMessage):
    """
    A Channel points redemption

    Attributes
    -----------
    timestamp: :class:`datetime.datetime`
        The timestamp the event happened.
    channel_id: :class:`int`
        The channel the reward was redeemed on.
    id: :class:`str`
        The id of the reward redemption.
    user: :class:`twitchio.PartialUser`
        The user redeeming the reward.
    reward: :class:`twitchio.CustomReward`
        The reward being redeemed.
    input: Optional[:class:`str`]
        The input the user gave, if any.
    status: :class:`str`
        The status of the reward.
    """

    __slots__ = "timestamp", "channel_id", "user", "id", "reward", "input", "status"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)

        redemption = data["message"]["data"]["redemption"]

        self.timestamp = parse_timestamp(redemption["redeemed_at"])
        self.channel_id: int = int(redemption["channel_id"])
        self.id: str = redemption["id"]
        self.user = PartialUser(client._http, redemption["user"]["id"], redemption["user"]["display_name"])
        self.reward = CustomReward(client._http, redemption["reward"], PartialUser(client._http, self.channel_id, None))
        self.input: Optional[str] = redemption.get("user_input")
        self.status: str = redemption["status"]


class PubSubModerationAction(PubSubMessage):
    """
    A basic moderation action.

    Attributes
    -----------
    action: :class:`str`
        The action taken.
    args: List[:class:`str`]
        The arguments given to the command.
    created_by: :class:`twitchio.PartialUser`
        The user that created the action.
    message_id: Optional[:class:`str`]
        The id of the message that created this action.
    target: :class:`twitchio.PartialUser`
        The target of this action.
    from_automod: :class:`bool`
        Whether this action was done automatically or not.
    """

    __slots__ = "action", "args", "created_by", "message_id", "target", "from_automod"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.action: str = data["message"]["data"]["moderation_action"]
        self.args: List[str] = data["message"]["data"]["args"]
        self.created_by = PartialUser(
            client._http, data["message"]["data"]["created_by_user_id"], data["message"]["data"]["created_by"]
        )
        self.message_id: Optional[str] = data["message"]["data"].get("msg_id")
        self.target = (
            PartialUser(
                client._http, data["message"]["data"]["target_user_id"], data["message"]["data"]["target_user_login"]
            )
            if data["message"]["data"]["target_user_id"]
            else None
        )
        self.from_automod: bool = data["message"]["data"].get("from_automod", False)


class PubSubModerationActionBanRequest(PubSubMessage):
    """
    A Ban/Unban event

    Attributes
    -----------
    action: :class:`str`
        The action taken.
    args: List[:class:`str`]
        The arguments given to the command.
    created_by: :class:`twitchio.PartialUser`
        The user that created the action.
    target: :class:`twitchio.PartialUser`
        The target of this action.
    """

    __slots__ = "action", "args", "created_by", "message_id", "target"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.action: str = data["message"]["data"]["moderation_action"]
        self.args: List[str] = data["message"]["data"]["moderator_message"]
        self.created_by = PartialUser(
            client._http, data["message"]["data"]["created_by_id"], data["message"]["data"]["created_by_login"]
        )
        self.target = (
            PartialUser(
                client._http, data["message"]["data"]["target_user_id"], data["message"]["data"]["target_user_login"]
            )
            if data["message"]["data"]["target_user_id"]
            else None
        )


class PubSubModerationActionChannelTerms(PubSubMessage):
    """
    A channel Terms update.

    Attributes
    -----------
    type: :class:`str`
        The type of action taken.
    channel_id: :class:`int`
        The channel id the action occurred on.
    id: :class:`str`
        The id of the Term.
    text: :class:`str`
        The text of the modified Term.
    requester: :class:`twitchio.PartialUser`
        The requester of this Term.
    """

    __slots__ = "type", "channel_id", "id", "text", "requester", "expires_at", "updated_at"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.type: str = data["message"]["data"]["type"]
        self.channel_id = int(data["message"]["data"]["channel_id"])
        self.id: str = data["message"]["data"]["id"]
        self.text: str = data["message"]["data"]["text"]
        self.requester = PartialUser(
            client._http, data["message"]["data"]["requester_id"], data["message"]["data"]["requester_login"]
        )

        self.expires_at = (
            parse_timestamp(data["message"]["data"]["expires_at"]) if data["message"]["data"]["expires_at"] else None
        )
        self.updated_at = (
            parse_timestamp(data["message"]["data"]["updated_at"]) if data["message"]["data"]["updated_at"] else None
        )


class PubSubChannelSubscribe(PubSubMessage):
    """
    Channel subscription

    Attributes
    -----------
    channel: :class:`twitchio.Channel`
        Channel that has been subscribed or subgifted.
    context: :class:`str`
        Event type associated with the subscription product.
    user: Optional[:class:`twitchio.PartialUser`]
        The person who subscribed or sent a gift subscription. Can be None if anonymous.
    message: :class:`str`
        Message sent with the sub/resub.
    emotes: Optional[List[:class:`dict`]]
        Emotes sent with the sub/resub.
    is_gift: :class:`bool`
        If this sub message was caused by a gift subscription.
    recipient: Optional[:class:`twitchio.PartialUser`]
        The person the who received the gift subscription.
    sub_plan: :class:`str`
        Subscription Plan ID.
    sub_plan_name: :class:`str`
        Channel Specific Subscription Plan Name.
    time: :class:`datetime.datetime`
        Time when the subscription or gift was completed. RFC 3339 format.
    cumulative_months: :class:`int`
        Cumulative number of tenure months of the subscription.
    streak_months: Optional[:class:`int`]
        Denotes the user's most recent (and contiguous) subscription tenure streak in the channel.
    multi_month_duration: Optional[:class:`int`]
        Number of months gifted as part of a single, multi-month gift OR number of months purchased as part of a multi-month subscription.
    """

    __slots__ = (
        "channel",
        "context",
        "user",
        "message",
        "emotes",
        "is_gift",
        "recipient",
        "sub_plan",
        "sub_plan_name",
        "time",
        "cumulative_months",
        "streak_months",
        "multi_month_duration",
    )

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)

        subscription = data["message"]

        self.channel: Channel = client.get_channel(subscription["channel_name"]) or Channel(
            name=subscription["channel_name"], websocket=client._connection
        )
        self.context: str = subscription["context"]
        try:
            self.user = PartialUser(client._http, int(subscription["user_id"]), subscription["user_name"])
        except KeyError:
            self.user = None

        self.message: str = subscription["sub_message"]["message"]
        try:
            self.emotes = subscription["sub_message"]["emotes"]
        except KeyError:
            self.emotes = None

        self.is_gift: bool = subscription["is_gift"]
        try:
            self.recipient = PartialUser(
                client._http, int(subscription["recipient_id"]), subscription["recipient_user_name"]
            )
        except KeyError:
            self.recipient = None

        self.sub_plan: str = subscription["sub_plan"]
        self.sub_plan_name: str = subscription["sub_plan_name"]
        self.time = parse_timestamp(subscription["time"])
        try:
            self.cumulative_months = int(subscription["cumulative_months"])
        except KeyError:
            self.cumulative_months = None
        try:
            self.streak_months = int(subscription["streak_months"])
        except KeyError:
            self.streak_months = None
        try:
            self.multi_month_duration = int(subscription["multi_month_duration"])
        except KeyError:
            self.multi_month_duration = None


class PubSubModerationActionModeratorAdd(PubSubMessage):
    """
    A moderator add event.

    Attributes
    -----------
    channel_id: :class:`int`
        The channel id the moderator was added to.
    moderation_action: :class:`str`
        Redundant.
    target: :class:`twitchio.PartialUser`
        The person who was added as a mod.
    created_by: :class:`twitchio.PartialUser`
        The person who added the mod.
    """

    __slots__ = "channel_id", "target", "moderation_action", "created_by"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.channel_id = int(data["message"]["data"]["channel_id"])
        self.moderation_action: str = data["message"]["data"]["moderation_action"]
        self.target = PartialUser(
            client._http, data["message"]["data"]["target_user_id"], data["message"]["data"]["target_user_login"]
        )
        self.created_by = PartialUser(
            client._http, data["message"]["data"]["created_by_user_id"], data["message"]["data"]["created_by"]
        )


_mod_actions = {
    "approve_unban_request": PubSubModerationActionBanRequest,
    "deny_unban_request": PubSubModerationActionBanRequest,
    "channel_terms_action": PubSubModerationActionChannelTerms,
    "moderator_added": PubSubModerationActionModeratorAdd,
    "moderation_action": PubSubModerationAction,
}


def _find_mod_action(client: Client, topic: str, data: dict):
    typ = data["message"]["type"]
    if typ in _mod_actions:
        return _mod_actions[typ](client, topic, data)

    else:
        raise ValueError(f"unknown pubsub moderation action '{typ}'")


_mapping = {
    "channel-bits-events-v2": ("pubsub_bits", PubSubBitsMessage),
    "channel-bits-badge-unlocks": ("pubsub_bits_badge", PubSubBitsBadgeMessage),
    "channel-subscribe-events-v1": ("pubsub_subscription", PubSubChannelSubscribe),
    "chat_moderator_actions": ("pubsub_moderation", _find_mod_action),
    "channel-points-channel-v1": ("pubsub_channel_points", PubSubChannelPointsMessage),
    "whispers": ("pubsub_whisper", None),
}


def create_message(client, msg: dict):
    topic = msg["data"]["topic"].split(".")[0]
    r = _mapping[topic]
    return r[0], r[1](client, topic, msg["data"])
