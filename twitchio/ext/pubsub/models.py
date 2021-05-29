"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

import datetime
from typing import List, Optional

from twitchio import PartialUser, Client, Channel, CustomReward


__all__ = (
    "PoolError",
    "PoolFull",
    "PubSubMessage",
    "PubSubBitsMessage",
    "PubSubBitsBadgeMessage",
    "PubSubChatMessage",
    "PubSubBadgeEntitlement",
    "PubSubChannelPointsMessage",
    "PubSubModerationActionModeratorAdd",
    "PubSubModerationActionBanRequest",
    "PubSubModerationActionChannelTerms",
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

    __slots__ = "content", "id", "type"

    def __init__(self, content: str, id: str, type: str):
        self.content = content
        self.id = int(id)
        self.type = type


class PubSubBadgeEntitlement:

    __slots__ = "new", "old"

    def __init__(self, new: int, old: int):
        self.new = new
        self.old = old


class PubSubMessage:

    __slots__ = "topic", "_data"

    def __init__(self, client: Client, topic: Optional[str], data: dict):
        self.topic = topic
        self._data = data


class PubSubBitsMessage(PubSubMessage):

    __slots__ = "badge_entitlement", "bits_used", "channel_id", "context", "anonymous", "message", "user", "version"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)

        self.message = PubSubChatMessage(data["chat_message"], data["message_id"], data["message_type"])
        self.badge_entitlement = (
            PubSubBadgeEntitlement(data["badge_entitlement"]["new_version"], data["badge_entitlement"]["old_version"])
            if data["badge_entitlement"]
            else None
        )
        self.bits_used: int = data["bits_used"]
        self.channel_id: int = int(data["channel_id"])
        self.user = (
            PartialUser(client._http, data["user_id"], data["user_name"]) if data["user_id"] is not None else None
        )
        self.version: str = data["version"]


class PubSubBitsBadgeMessage(PubSubMessage):

    __slots__ = "user", "channel", "badge_tier", "message", "timestamp"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.user = PartialUser(client._http, data["user_id"], data["user_name"])
        self.channel: Channel = client.get_channel(data["channel_name"]) or Channel(
            name=data["channel_name"], websocket=client._connection
        )
        self.badge_tier: int = data["badge_tier"]
        self.message = data["chat_message"]
        self.timestamp = datetime.datetime.strptime(data["time"], "%Y-%m-%dT%H:%M:%SZ")


class PubSubChannelPointsMessage(PubSubMessage):

    __slots__ = "timestamp", "channel_id", "user", "id", "reward", "input", "status"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)

        redemption = data["message"]["data"]["redemption"]

        self.timestamp = datetime.datetime.strptime(
            redemption["redeemed_at"][0:25] + redemption["redeemed_at"][28:], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.channel_id: int = int(redemption["channel_id"])
        self.id: str = redemption["id"]
        self.user = PartialUser(client._http, redemption["user"]["id"], redemption["user"]["display_name"])
        self.reward = CustomReward(client._http, redemption["reward"], PartialUser(client._http, self.channel_id, None))
        self.input = redemption.get("user_input")
        self.status: str = redemption["status"]


class PubSubModerationActionBanRequest(PubSubMessage):

    __slots__ = "action", "args", "created_by", "message_id", "target", "from_automod"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.action: str = data["message"]["data"]["moderation_action"]
        self.args: List[str] = data["message"]["data"]["args"]
        self.created_by = PartialUser(
            client._http, data["message"]["data"]["created_by_user_id"], data["message"]["data"]["created_by"]
        )
        self.message_id: str = data["message"]["data"]["msg_id"]
        self.target = (
            PartialUser(
                client._http, data["message"]["data"]["target_user_id"], data["message"]["data"]["target_user_login"]
            )
            if data["message"]["data"]["target_user_id"]
            else None
        )
        self.from_automod: bool = data["message"]["data"]["from_automod"]


class PubSubModerationActionChannelTerms(PubSubMessage):

    __slots__ = "type", "channel_id", "id", "text", "requester", "expires_at", "updated_at", "from_automod"

    def __init__(self, client: Client, topic: str, data: dict):
        super().__init__(client, topic, data)
        self.type: str = data["message"]["type"]
        self.channel_id = int(data["message"]["data"]["channel_id"])
        self.id: str = data["message"]["data"]["id"]
        self.text: str = data["message"]["data"]["text"]
        self.requester = PartialUser(
            client._http, data["message"]["data"]["requester_id"], data["message"]["data"]["requester_login"]
        )

        self.expires_at = self.updated_at = None
        if data["message"]["data"]["expires_at"]:
            self.expires_at = datetime.datetime.strptime(data["message"]["data"]["expires_at"], "%Y-%m-%dT%H:%M:%SZ")

        if data["message"]["data"]["updated_at"]:
            self.updated_at = datetime.datetime.strptime(data["message"]["data"]["updated_at"], "%Y-%m-%dT%H:%M:%SZ")

        self.from_automod: bool = data["message"]["data"]["from_automod"]


class PubSubModerationActionModeratorAdd(PubSubMessage):

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


def _find_mod_action(client: Client, topic: str, data: dict):
    typ = data["message"]["type"]
    if typ in ("approve_unban_request", "deny_unban_request"):
        return PubSubModerationActionBanRequest(client, topic, data)

    elif typ == "channel_terms_action":
        return PubSubModerationActionChannelTerms(client, topic, data)

    elif typ == "moderator_added":
        return PubSubModerationActionModeratorAdd(client, topic, data)

    else:
        raise ValueError(f"unknown pubsub moderation action '{typ}'")


_mapping = {
    "channel-bits-events-v2": ("pubsub_bits", PubSubBitsMessage),
    "channel-bits-badge-unlocks": ("pubsub_bits_badge", PubSubBitsBadgeMessage),
    "channel-subscribe-events-v1": ("pubsub_subscription", None),
    "chat_moderator_actions": ("pubsub_moderation", _find_mod_action),
    "channel-points-channel-v1": ("pubsub_channel_points", PubSubChannelPointsMessage),
    "whispers": ("pubsub_whisper", None),
}


def create_message(client, msg: dict):
    topic = msg["data"]["topic"].split(".")[0]
    r = _mapping[topic]
    return r[0], r[1](client, topic, msg["data"])
