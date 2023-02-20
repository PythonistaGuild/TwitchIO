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

from __future__ import annotations
import datetime
from typing import Optional, Union, TYPE_CHECKING, List, Dict

from . import enums
from .utils import parse_timestamp
from .user import BitLeaderboardUser, PartialUser, User

if TYPE_CHECKING:
    from .http import TwitchHTTP
__all__ = (
    "BitsLeaderboard",
    "Clip",
    "CheerEmote",
    "CheerEmoteTier",
    "GlobalEmote",
    "ChannelEmote",
    "HypeTrainContribution",
    "HypeTrainEvent",
    "BanEvent",
    "FollowEvent",
    "SubscriptionEvent",
    "Marker",
    "VideoMarkers",
    "Game",
    "ModEvent",
    "AutomodCheckMessage",
    "AutomodCheckResponse",
    "Extension",
    "MaybeActiveExtension",
    "ActiveExtension",
    "ExtensionBuilder",
    "Video",
    "Tag",
    "WebhookSubscription",
    "Prediction",
    "Predictor",
    "PredictionOutcome",
    "Schedule",
    "ScheduleSegment",
    "ScheduleCategory",
    "ScheduleVacation",
    "Stream",
    "Team",
    "ChannelTeams",
    "ChannelInfo",
    "Poll",
    "PollChoice",
    "Goal",
    "ChatSettings",
    "Raid",
    "ChatterColor",
    "Timeout",
    "Ban",
    "ShieldStatus",
)


class BitsLeaderboard:
    """
    Represents a Bits leaderboard from the twitch API.

    Attributes
    ------------
    started_at: Optional[:class:`datetime.datetime`]
        The time the leaderboard started.
    ended_at: Optional[:class:`datetime.datetime`]
        The time the leaderboard ended.
    leaders: List[:class:`BitLeaderboardUser`]
        The current leaders of the Leaderboard.
    """

    __slots__ = "_http", "leaders", "started_at", "ended_at"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.started_at = (
            parse_timestamp(data["date_range"]["started_at"]) if data["date_range"]["started_at"] else None
        )
        self.ended_at = parse_timestamp(data["date_range"]["ended_at"]) if data["date_range"]["ended_at"] else None
        self.leaders = [BitLeaderboardUser(http, x) for x in data["data"]]

    def __repr__(self):
        return f"<BitsLeaderboard started_at={self.started_at} ended_at={self.ended_at}>"


class CheerEmoteTier:
    """
    Represents a Cheer Emote tier.

    Attributes
    -----------
    min_bits: :class:`int`
        The minimum bits for the tier
    id: :class:`str`
        The ID of the tier
    colour: :class:`str`
        The colour of the tier
    images: :class:`dict`
        contains two dicts, ``light`` and ``dark``. Each item will have an ``animated`` and ``static`` item,
        which will contain yet another dict, with sizes ``1``, ``1.5``, ``2``, ``3``, and ``4``.
        Ex. ``cheeremotetier.images["light"]["animated"]["1"]``
    can_cheer: :class:`bool`
        Indicates whether emote information is accessible to users.
    show_in_bits_card: :class`bool`
        Indicates whether twitch hides the emote from the bits card.
    """

    __slots__ = "min_bits", "id", "color", "images", "can_cheer", "show_in_bits_card"

    def __init__(self, data: dict):
        self.min_bits: int = data["min_bits"]
        self.id: str = data["id"]
        self.color: str = data["color"]
        self.images = data["images"]  # TODO types
        self.can_cheer: bool = data["can_cheer"]
        self.show_in_bits_card: bool = data["show_in_bits_card"]

    def __repr__(self):
        return f"<CheerEmoteTier id={self.id} min_bits={self.min_bits}>"


class CheerEmote:
    """
    Represents a Cheer Emote

    Attributes
    -----------
    prefix: :class:`str`
        The string used to Cheer that precedes the Bits amount.
    tiers: :class:`~CheerEmoteTier`
        The tiers this Cheer Emote has
    type: :class:`str`
        Shows whether the emote is ``global_first_party``, ``global_third_party``, ``channel_custom``, ``display_only``, or ``sponsored``.
    order: :class:`str`
        Order of the emotes as shown in the bits card, in ascending order.
    last_updated :class:`datetime.datetime`
        The date this cheermote was last updated.
    charitable: :class:`bool`
        Indicates whether this emote provides a charity contribution match during charity campaigns.
    """

    __slots__ = "_http", "prefix", "tiers", "type", "order", "last_updated", "charitable"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.prefix: str = data["prefix"]
        self.tiers = [CheerEmoteTier(x) for x in data["tiers"]]
        self.type: str = data["type"]
        self.order: str = data["order"]
        self.last_updated = parse_timestamp(data["last_updated"])
        self.charitable: bool = data["is_charitable"]

    def __repr__(self):
        return f"<CheerEmote prefix={self.prefix} type={self.type} order={self.order}>"


class GlobalEmote:
    """
    Represents a Global Emote

    Attributes
    -----------
    id: :class:`str`
        The ID of the emote.
    name: :class:`str`
        The name of the emote.
    images: :class:`dict`
        Contains the image URLs for the emote. These image URLs will always provide a static (i.e., non-animated) emote image with a light background.
    format: List[:class:`str`]
        The formats that the emote is available in.
    scale: List[:class:`str`]
        The sizes that the emote is available in.
    theme_mode: List[:class:`str`]
        The background themes that the emote is available in.
    """

    __slots__ = ("id", "name", "images", "format", "scale", "theme_mode", "template")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.images: dict = data["images"]
        self.format: List[str] = data["format"]
        self.scale: List[str] = data["scale"]
        self.theme_mode: List[str] = data["theme_mode"]

    def __repr__(self):
        return f"<GlobalEmote id={self.id} name={self.name}"


class ChannelEmote(GlobalEmote):
    """
    Represents a Channel Emote

    Attributes
    -----------
    id: :class:`str`
        The ID of the emote.
    name: :class:`str`
        The name of the emote.
    images: :class:`dict`
        Contains the image URLs for the emote. These image URLs will always provide a static (i.e., non-animated) emote image with a light background.
    tier: :class:`str`
        The subscriber tier at which the emote is unlocked.
    type: :class:`str`
        The type of emote.
    set_id: :class:`str`
        An ID that identifies the emote set that the emote belongs to.
    format: List[:class:`str`]
        The formats that the emote is available in.
    scale: List[:class:`str`]
        The sizes that the emote is available in.
    theme_mode: List[:class:`str`]
        The background themes that the emote is available in.
    """

    __slots__ = ("tier", "type", "set_id")

    def __init__(self, http: "TwitchHTTP", data: dict):
        super().__init__(http, data)
        self.tier: str = data["tier"]
        self.type: str = data["emote_type"]
        self.set_id: str = data["emote_set_id"]

    def __repr__(self):
        return f"<ChannelEmote id={self.id} name={self.name} type={self.type}>"


class Clip:
    """
    Represents a Twitch Clip

    Attributes
    -----------
    id: :class:`str`
        The ID of the clip.
    url: :class:`str`
        The URL of the clip.
    embed_url: :class:`str`
        The URL to embed the clip with.
    broadcaster: :class:`~twitchio.PartialUser`
        The user whose channel the clip was created on.
    creator: :class:`~twitchio.PartialUser`
        The user who created the clip.
    video_id: :class:`str`
        The ID of the video the clip is sourced from.
    game_id: :class:`str`
        The ID of the game that was being played when the clip was created.
    language: :class:`str`
        The language, in an `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ format, of the stream when the clip was created.
    title: :class:`str`
        The title of the clip.
    views: :class:`int`
        The amount of views this clip has.
    created_at: :class:`datetime.datetime`
        When the clip was created.
    thumbnail_url: :class:`str`
        The url of the clip thumbnail.
    duration: :class:`float`
        Duration of the Clip in seconds (up to 0.1 precision).
    vod_offset: Optional[:class:`int`]
        The zero-based offset, in seconds, to where the clip starts in the video (VOD) or stream.
        This can be None if the parent no longer exists
    """

    __slots__ = (
        "id",
        "url",
        "embed_url",
        "broadcaster",
        "creator",
        "video_id",
        "game_id",
        "language",
        "title",
        "views",
        "created_at",
        "thumbnail_url",
        "duration",
        "vod_offset",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: str = data["id"]
        self.url: str = data["url"]
        self.embed_url: str = data["embed_url"]
        self.broadcaster = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.creator = PartialUser(http, data["creator_id"], data["creator_name"])
        self.video_id: str = data["video_id"]
        self.game_id: str = data["game_id"]
        self.language: str = data["language"]
        self.title: str = data["title"]
        self.views: int = data["view_count"]
        self.created_at = parse_timestamp(data["created_at"])
        self.thumbnail_url: str = data["thumbnail_url"]
        self.duration: float = data["duration"]
        self.vod_offset: Optional[int] = data["vod_offset"]

    def __repr__(self):
        return f"<Clip id={self.id} broadcaster={self.broadcaster} creator={self.creator}>"


class HypeTrainContribution:
    """
    A Contribution to a Hype Train

    Attributes
    -----------
    total: :class:`int`
        Total aggregated amount of all contributions by the top contributor. If type is ``BITS``, total represents aggregate amount of bits used.
        If type is ``SUBS``, aggregate total where 500, 1000, or 2500 represent tier 1, 2, or 3 subscriptions respectively.
        For example, if top contributor has gifted a tier 1, 2, and 3 subscription, total would be 4000.
    type: :class:`str`
        Identifies the contribution method, either BITS, SUBS or OTHER.
    user: :class:`~twitchio.PartialUser`
        The user making the contribution.
    """

    __slots__ = "total", "type", "user"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.total: int = data["total"]
        self.type: str = data["type"]
        self.user = PartialUser(http, id=data["user"], name=None)  # we'll see how this goes

    def __repr__(self):
        return f"<HypeTrainContribution total={self.total} type={self.type} user={self.user}>"


class HypeTrainEvent:
    """
    Represents a Hype Train Event (progression)

    Attributes
    -----------
    id: :class:`str`
        The ID of the event.
    event_id: :class:`str`
        The ID of the Hype Train.
    type: :class:`str`
        The type of the event. Currently only ``hypetrain.progression``.
    version: :class:`str`
        The version of the endpoint.
    broadcaster: :class:`~twitchio.PartialUser`
        The user whose channel the Hype Train is occurring on.
    timestamp: :class:`datetime.datetime`
        The time the event happened at.
    cooldown_end_time: :class:`datetime.datetime`
        The time that another Hype Train can happen at.
    expiry: :class:`datetime.datetime`
        The time that this Hype Train expires at.
    started_at: :class:`datetime.datetime`
        The time that this Hype Train started at.
    last_contribution: :class:`HypeTrainContribution`
        The last contribution to this Hype Train.
    level: :class:`int`
        The level reached on this Hype Train (1-5).
    top_contributions: List[:class:`HypeTrainContribution`]
        The top contributors to the Hype Train.
    contributions_total: :class:`int`
        The total score towards completing the goal.
    goal: :class:`int`
        The goal for the next Hype Train level
    """

    __slots__ = (
        "id",
        "type",
        "timestamp",
        "version",
        "broadcaster",
        "expiry",
        "event_id",
        "goal",
        "level",
        "started_at",
        "top_contributions",
        "contributions_total",
        "cooldown_end_time",
        "last_contribution",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: str = data["id"]
        self.event_id: str = data["event_data"]["id"]
        self.type: str = data["event_type"]
        self.version: str = data["version"]
        self.broadcaster = PartialUser(http, id=data["event_data"]["broadcaster_id"], name=None)
        self.timestamp = parse_timestamp(data["event_timestamp"])
        self.cooldown_end_time = parse_timestamp(data["event_data"]["cooldown_end_time"])
        self.expiry = parse_timestamp(data["expires_at"])
        self.started_at = parse_timestamp(data["event_data"]["started_at"])
        self.last_contribution = HypeTrainContribution(http, data["event_data"]["last_contribution"])
        self.level: int = data["event_data"]["level"]
        self.top_contributions = [HypeTrainContribution(http, x) for x in data["event_data"]["top_contributions"]]
        self.contributions_total: int = data["event_data"]["total"]
        self.goal: int = data["event_data"]["goal"]

    def __repr__(self):
        return f"<HypeTrainEvent id={self.id} type={self.type} level={self.level} broadcaster={self.broadcaster}>"


class BanEvent:
    """
    This has been deprecated.

    Represents a user being banned from a channel.

    Attributes
    -----------
    id: :class:`str`
        The event ID.
    type: :class:`str`
        Type of ban event. Either ``moderation.user.ban`` or ``moderation.user.unban``.
    timestamp: :class:`datetime.datetime`
        The time the action occurred at.
    version: :class:`float`
        The version of the endpoint.
    broadcaster: :class:`~twitchio.PartialUser`
        The user whose channel the ban/unban occurred on.
    user: :class:`~twichio.PartialUser`
        The user who was banned/unbanned.
    moderator: :class:`~twitchio.PartialUser`
        The user who performed the action.
    expires_at: Optional[:class:`datetime.datetime`]
        When the ban expires.
    reason: :class:`str`
        The reason the moderator banned/unbanned the user.
    """

    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user", "expires_at", "moderator", "reason"

    def __init__(self, http: "TwitchHTTP", data: dict, broadcaster: Optional[Union[PartialUser, User]]):
        self.id: str = data["id"]
        self.type: str = data["event_type"]
        self.timestamp = parse_timestamp(data["event_timestamp"])
        self.version: float = float(data["version"])
        self.reason: str = data["event_data"]["reason"]
        self.broadcaster = broadcaster or PartialUser(
            http, data["event_data"]["broadcaster_id"], data["event_data"]["broadcaster_name"]
        )
        self.user = PartialUser(http, data["event_data"]["user_id"], data["event_data"]["user_name"])
        self.moderator = PartialUser(http, data["event_data"]["moderator_id"], data["event_data"]["moderator_name"])
        self.expires_at = (
            parse_timestamp(data["event_data"]["expires_at"]) if data["event_data"]["expires_at"] else None
        )

    def __repr__(self):
        return f"<BanEvent id={self.id} type={self.type} broadcaster={self.broadcaster} user={self.user}>"


class FollowEvent:
    """
    Represents a Follow Event.

    Attributes
    -----------
    from_user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user that followed another user.
    to_user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user that was followed.
    followed_at: :class:`datetime.datetime`
        When the follow happened.
    """

    __slots__ = "from_user", "to_user", "followed_at"

    def __init__(
        self,
        http: "TwitchHTTP",
        data: dict,
        from_: Union[User, PartialUser] = None,
        to: Union[User, PartialUser] = None,
    ):
        self.from_user: Union[User, PartialUser] = from_ or PartialUser(http, data["from_id"], data["from_name"])
        self.to_user: Union[User, PartialUser] = to or PartialUser(http, data["to_id"], data["to_name"])
        self.followed_at = parse_timestamp(data["followed_at"])

    def __repr__(self):
        return f"<FollowEvent from_user={self.from_user} to_user={self.to_user} followed_at={self.followed_at}>"


class SubscriptionEvent:
    """
    Represents a Subscription Event

    Attributes
    -----------
    broadcaster: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user that was subscribed to.
    user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user who subscribed.
    tier: :class:`int`
        The tier at which the user subscribed. Could be ``1``, ``2``, or ``3``.
    plan_name: :class:`str`
        Name of the description. (twitch docs aren't helpful, if you know what this is specifically please PR :) ).
    gift: :class:`bool`
        Whether the subscription is a gift.
    """

    __slots__ = "broadcaster", "gift", "tier", "plan_name", "user"

    def __init__(
        self,
        http: "TwitchHTTP",
        data: dict,
        broadcaster: Union[User, PartialUser] = None,
        user: Union[User, PartialUser] = None,
    ):
        self.broadcaster: Union[User, PartialUser] = broadcaster or PartialUser(
            http, data["broadcaster_id"], data["broadcaster_name"]
        )
        self.user: Union[User, PartialUser] = user or PartialUser(http, data["user_id"], data["user_name"])
        self.tier: int = round(int(data["tier"]) / 1000)
        self.plan_name: str = data["plan_name"]
        self.gift: bool = data["is_gift"]

    def __repr__(self):
        return (
            f"<SubscriptionEvent broadcaster={self.broadcaster} user={self.user} tier={self.tier} "
            f"plan_name={self.plan_name} gift={self.gift}>"
        )


class Marker:
    """
    Represents a stream Marker

    Attributes
    -----------
    id: :class:`str`
        The ID of the marker.
    created_at: :class:`datetime.datetime`
        When the marker was created.
    description: :class:`str`
        The description of the marker.
    position: :class:`int`
        The position of the marker, in seconds.
    url: Optional[:class:`str`]
        The url that leads to the marker.
    """

    __slots__ = "id", "created_at", "description", "position", "url"

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.created_at = parse_timestamp(data["created_at"])
        self.description: str = data["description"]
        self.position: int = data["position_seconds"]
        self.url: Optional[str] = data.get("URL")

    def __repr__(self):
        return f"<Marker id={self.id} created_at={self.created_at} position={self.position} url={self.url}>"


class VideoMarkers:
    """
    Represents markers contained in a video

    Attributes
    -----------
    id: :class:`str`
        The video id.
    markers: List[:class:`Marker`]
        The markers contained in the video.
    """

    __slots__ = "id", "markers"

    def __init__(self, data: dict):
        self.id: str = data["video_id"]
        self.markers = [Marker(d) for d in data["markers"]]

    def __repr__(self):
        return f"<VideoMarkers id={self.id}>"


class Game:
    """
    Represents a Game on twitch

    Attributes
    -----------
    id: :class:`int`
        Game ID.
    name: :class:`str`
        Game name.
    box_art_url: :class:`str`
        Template URL for the game's box art.
    igdb_id: Optional[:class:`int`]
        The IGDB ID of the game. If this is not available to Twitch it will return None
    """

    __slots__ = "id", "name", "box_art_url", "igdb_id"

    def __init__(self, data: dict):
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self.box_art_url: str = data["box_art_url"]
        self.igdb_id: Optional[int] = int(data["igdb_id"]) if data["igdb_id"] else None

    def __repr__(self):
        return f"<Game id={self.id} name={self.name}>"

    def art_url(self, width: int, height: int) -> str:
        """
        Adds width and height into the box art url

        Parameters
        -----------
        width: :class:`int`
            The width of the image
        height: :class:`int`
            The height of the image

        Returns
        --------
            :class:`str`
        """
        return self.box_art_url.format(width=width, height=height)


class ModEvent:
    """
    Represents a mod add/remove action

    Attributes
    -----------
    id: :class:`str`
        The ID of the event.
    type: :class:`~twitchio.ModEventEnum`
        The type of the event.
    timestamp: :class:`datetime.datetime`
        The timestamp of the event.
    version: :class:`str`
        The version of the endpoint.
    broadcaster: Union[:class:`~twitchio.PartialUser`, :class:`~twitchio.User`]
        The user whose channel the event happened on.
    user: :class:`~twitchio.PartialUser`
        The user being removed or added as a moderator.
    """

    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user"

    def __init__(self, http: "TwitchHTTP", data: dict, broadcaster: Union[PartialUser, User]):
        self.id: str = data["id"]
        self.type = enums.ModEventEnum(value=data["event_type"])
        self.timestamp = parse_timestamp(data["event_timestamp"])
        self.version: str = data["version"]
        self.broadcaster = broadcaster
        self.user = PartialUser(http, data["event_data"]["user_id"], data["event_data"]["user_name"])

    def __repr__(self):
        return f"<ModEvent id={self.id} type={self.type} broadcaster={self.broadcaster} user={self.user}>"


class AutomodCheckMessage:
    """
    Represents the message to check with automod

    Attributes
    -----------
    id: :class:`str`
        Developer-generated identifier for mapping messages to results.
    text: :class:`str`
        Message text.
    user_id: :class:`int`
        User ID of the sender.
    """

    __slots__ = "id", "text", "user_id"

    def __init__(self, id: str, text: str, user: Union[PartialUser, int]):
        self.id = id
        self.text = text
        self.user_id = user.id if isinstance(user, PartialUser) else user

    def _to_dict(self):
        return {"msg_id": self.id, "msg_text": self.text, "user_id": str(self.user_id)}

    def __repr__(self):
        return f"<AutomodCheckMessage id={self.id} user_id={self.user_id}>"


class AutomodCheckResponse:
    """
    Represents the response to a message check with automod

    Attributes
    -----------
    id: :class:`str`
        The message ID passed in the body of the check
    permitted: :class:`bool`
        Indicates if this message meets AutoMod requirements.
    """

    __slots__ = "id", "permitted"

    def __init__(self, data: dict):
        self.id: str = data["msg_id"]
        self.permitted: bool = data["is_permitted"]

    def __repr__(self):
        return f"<AutomodCheckResponse id={self.id} permitted={self.permitted}>"


class Extension:
    """
    Represents an extension for a specified user

    Attributes
    -----------
    id: :class:`str`
        ID of the extension.
    version: :class:`str`
        Version of the extension.
    active: :class:`bool`
        Activation state of the extension, for each extension type (component, overlay, mobile, panel).
    """

    __slots__ = "id", "active", "version", "_x", "_y"

    def __init__(self, data):
        self.id: str = data["id"]
        self.version: str = data["version"]
        self.active: bool = data["active"]
        self._x = None
        self._y = None

    def __repr__(self):
        return f"<Extension id={self.id} version={self.version} active={self.active}>"

    @classmethod
    def new(cls, active: bool, version: str, id: str, x: int = None, y: int = None) -> "Extension":
        self = cls.__new__(cls)
        self.active = active
        self.version = version
        self.id = id
        self._x = x
        self._y = y
        return self

    def _to_dict(self):
        v = {"active": self.active, "id": self.id, "version": self.version}
        if self._x is not None:
            v["x"] = self._x
        if self._y is not None:
            v["y"] = self._y
        return v


class MaybeActiveExtension(Extension):
    """
    Represents an extension for a specified user that could be may be activated

    Attributes
    -----------
    id: :class:`str`
        ID of the extension.
    version: :class:`str`
        Version of the extension.
    name: :class:`str`
        Name of the extension.
    can_activate: :class:`bool`
        Indicates whether the extension is configured such that it can be activated.
    types: List[:class:`str`]
        Types for which the extension can be activated.
    """

    __slots__ = "id", "version", "name", "can_activate", "types"

    def __init__(self, data):
        self.id: str = data["id"]
        self.version: str = data["version"]
        self.name: str = data["name"]
        self.can_activate: bool = data["can_activate"]
        self.types: List[str] = data["type"]

    def __repr__(self):
        return f"<MaybeActiveExtension id={self.id} version={self.version} name={self.name}>"


class ActiveExtension(Extension):
    """
    Represents an active extension for a specified user

    Attributes
    -----------
    id: :class:`str`
        ID of the extension.
    version: :class:`str`
        Version of the extension.
    active: :class:`bool`
        Activation state of the extension.
    name: :class:`str`
        Name of the extension.
    x: :class:`int`
        (Video-component Extensions only) X-coordinate of the placement of the extension. Could be None.
    y: :class:`int`
        (Video-component Extensions only) Y-coordinate of the placement of the extension. Could be None.
    """

    __slots__ = "id", "active", "name", "version", "x", "y"

    def __init__(self, data):
        self.active: bool = data["active"]
        self.id: Optional[str] = data.get("id", None)
        self.version: Optional[str] = data.get("version", None)
        self.name: Optional[str] = data.get("name", None)
        self.x: Optional[int] = data.get("x", None)  # x and y only show for component extensions.
        self.y: Optional[int] = data.get("y", None)

    def __repr__(self):
        return f"<ActiveExtension id={self.id} version={self.version} name={self.name}>"


class ExtensionBuilder:
    """
    Represents an extension to be updated for a specific user

    Attributes
    -----------
    panels: List[:class:`~twitchio.Extension`]
        List of panels to update for an extension.
    overlays: List[:class:`~twitchio.Extension`]
        List of overlays to update for an extension.
    components: List[:class:`~twitchio.Extension`]
        List of components to update for an extension.
    """

    __slots__ = "panels", "overlays", "components"

    def __init__(
        self, panels: List[Extension] = None, overlays: List[Extension] = None, components: List[Extension] = None
    ):
        self.panels = panels or []
        self.overlays = overlays or []
        self.components = components or []

    def _to_dict(self):
        return {
            "panel": {str(x): y._to_dict() for x, y in enumerate(self.panels)},
            "overlay": {str(x): y._to_dict() for x, y in enumerate(self.overlays)},
            "component": {str(x): y._to_dict() for x, y in enumerate(self.components)},
        }


class Video:
    """
    Represents video information

    Attributes
    -----------
    id: :class:`int`
        The ID of the video.
    user: :class:`~twitchio.PartialUser`
        User who owns the video.
    title: :class:`str`
        Title of the video
    description: :class:`str`
        Description of the video.
    created_at: :class:`datetime.datetime`
        Date when the video was created.
    published_at: :class:`datetime.datetime`
       Date when the video was published.
    url: :class:`str`
        URL of the video.
    thumbnail_url: :class:`str`
        Template URL for the thumbnail of the video.
    viewable: :class:`str`
        Indicates whether the video is public or private.
    view_count: :class:`int`
        Number of times the video has been viewed.
    language: :class:`str`
        Language of the video.
    type: :class:`str`
        The type of video.
    duration: :class:`str`
        Length of the video.
    """

    __slots__ = (
        "_http",
        "id",
        "user",
        "title",
        "description",
        "created_at",
        "published_at",
        "url",
        "thumbnail_url",
        "viewable",
        "view_count",
        "language",
        "type",
        "duration",
    )

    def __init__(self, http: "TwitchHTTP", data: dict, user: Union[PartialUser, User] = None):
        self._http = http
        self.id: int = int(data["id"])
        self.user = user or PartialUser(http, data["user_id"], data["user_name"])
        self.title: str = data["title"]
        self.description: str = data["description"]
        self.created_at = parse_timestamp(data["created_at"])
        self.published_at = parse_timestamp(data["published_at"])
        self.url: str = data["url"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.viewable: str = data["viewable"]
        self.view_count: int = data["view_count"]
        self.language: str = data["language"]
        self.type: str = data["type"]
        self.duration: str = data["duration"]

    def __repr__(self):
        return f"<Video id={self.id} title={self.title} url={self.url}>"

    async def delete(self, token: str):
        """|coro|

        Deletes the video. For bulk deletion see :func:`Client.delete_videos`

        Parameters
        -----------
        token: :class:`str`
            The users oauth token with the channel:manage:videos
        """
        await self._http.delete_videos(token, ids=[str(self.id)])


class Tag:
    """
    Represents a stream tag

    Attributes
    -----------
    id: :class:`str`
        An ID that identifies the tag.
    auto: :class:`bool`
        Indicates whether the tag is an automatic tag.
    localization_names: Dict[:class:`str`, :class:`str`]
        A dictionary that contains the localized names of the tag.
    localization_descriptions: :class:`str`
        A dictionary that contains the localized descriptions of the tag.
    """

    __slots__ = "id", "auto", "localization_names", "localization_descriptions"

    def __init__(self, data: dict):
        self.id: str = data["tag_id"]
        self.auto: bool = data["is_auto"]
        self.localization_names: Dict[str, str] = data["localization_names"]
        self.localization_descriptions: Dict[str, str] = data["localization_descriptions"]

    def __repr__(self):
        return f"<Tag id={self.id}>"


class WebhookSubscription:
    __slots__ = "callback", "expires_at", "topic"

    def __init__(self, data: dict):
        self.callback: str = data["callback"]
        self.expires_at = parse_timestamp(data["expired_at"])
        self.topic: str = data["topic"]

    def __repr__(self):
        return f"<WebhookSubscription callback={self.callback} topic={self.topic} expires_at={self.expires_at}>"


class Stream:
    """
    Represents a Stream

    Attributes
    -----------
    id: :class:`int`
        The current stream ID.
    user: :class:`~twitchio.PartialUser`
        The user who is streaming.
    game_id: :class:`int`
        Current game ID being played on the channel.
    game_name: :class:`str`
        Name of the game being played on the channel.
    type: :class:`str`
        Whether the stream is "live" or not.
    title: :class:`str`
        Title of the stream.
    viewer_count: :class:`int`
        Current viewer count of the stream
    started_at: :class:`datetime.datetime`
        UTC timestamp of when the stream started.
    language: :class:`str`
        Language of the channel.
    thumbnail_url: :class:`str`
        Thumbnail URL of the stream.
    tag_ids: List[:class:`str`]
        Tag IDs that apply to the stream.

        .. warning::

            This field will be deprecated by twitch in 2023.

    is_mature: :class:`bool`
        Indicates whether the stream is intended for mature audience.
    tags: List[:class:`str`]
        The tags applied to the channel.
    """

    __slots__ = (
        "id",
        "user",
        "game_id",
        "game_name",
        "type",
        "title",
        "viewer_count",
        "started_at",
        "language",
        "thumbnail_url",
        "tag_ids",
        "is_mature",
        "tags",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: int = data["id"]
        self.user = PartialUser(http, data["user_id"], data["user_name"])
        self.game_id: int = data["game_id"]
        self.game_name: str = data["game_name"]
        self.type: str = data["type"]
        self.title: str = data["title"]
        self.viewer_count: int = data["viewer_count"]
        self.started_at = parse_timestamp(data["started_at"])
        self.language: str = data["language"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.tag_ids: List[str] = data["tag_ids"] or []
        self.is_mature: bool = data["is_mature"]
        self.tags: List[str] = data["tags"]

    def __repr__(self):
        return f"<Stream id={self.id} user={self.user} title={self.title} started_at={self.started_at}>"


class ChannelInfo:
    """
    Represents a channel's current information

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        The user whose channel information was requested.
    game_id: :class:`int`
        Current game ID being played on the channel.
    game_name: :class:`str`
        Name of the game being played on the channel.
    title: :class:`str`
        Title of the stream.
    language: :class:`str`
        Language of the channel.
    delay: :class:`int`
        Stream delay in seconds.
        This defaults to 0 if the broadcaster_id does not match the user access token.
    tags: List[:class:`str`]
        The tags applied to the channel.
    """

    __slots__ = ("user", "game_id", "game_name", "title", "language", "delay", "tags")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.user = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.game_id: int = data["game_id"]
        self.game_name: str = data["game_name"]
        self.title: str = data["title"]
        self.language: str = data["broadcaster_language"]
        self.delay: int = data["delay"]
        self.tags: List[str] = data["tags"]

    def __repr__(self):
        return f"<ChannelInfo user={self.user} game_id={self.game_id} game_name={self.game_name} title={self.title} language={self.language} delay={self.delay}>"


class Prediction:
    """
    Represents channel point predictions

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        The user who is streaming.
    prediction_id: :class:`str`
        ID of the Prediction.
    title: :class:`str`
        Title for the Prediction.
    winning_outcome_id: :class:`str`
        ID of the winning outcome
    outcomes: List[:class:`~twitchio.PredictionOutcome`]
        List of possible outcomes for the Prediction.
    prediction_window: :class:`int`
        Total duration for the Prediction (in seconds).
    prediction_status: :class:`str`
        Status of the Prediction.
    created_at: :class:`datetime.datetime`
        Time for when the Prediction was created.
    ended_at: :class:`datetime.datetime`
        Time for when the Prediction ended.
    locked_at: :class:`datetime.datetime`
        Time for when the Prediction was locked.
    """

    __slots__ = (
        "user",
        "prediction_id",
        "title",
        "winning_outcome_id",
        "outcomes",
        "prediction_window",
        "prediction_status",
        "created_at",
        "ended_at",
        "locked_at",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.user = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.prediction_id: str = data["id"]
        self.title: str = data["title"]
        self.winning_outcome_id: str = data["winning_outcome_id"]
        self.outcomes: List[PredictionOutcome] = [PredictionOutcome(http, x) for x in data["outcomes"]]
        self.prediction_window: int = data["prediction_window"]
        self.prediction_status: str = data["status"]
        self.created_at = self._parse_time(data, "created_at")
        self.ended_at = self._parse_time(data, "ended_at")
        self.locked_at = self._parse_time(data, "locked_at")

    def _parse_time(self, data, field) -> Optional["Datetime"]:
        if field not in data or data[field] is None:
            return None
        time = data[field].split(".")[0]
        return datetime.datetime.fromisoformat(time)

    def __repr__(self):
        return f"<Prediction user={self.user} prediction_id={self.prediction_id} winning_outcome_id={self.winning_outcome_id} title={self.title}>"


class Predictor:
    """
    Represents a predictor

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        The user who is streaming.
    channel_points_used: :class:`int`
        Number of Channel Points used by the user.
    channel_points_won: :class:`int`
        Number of Channel Points won by the user.
    """

    __slots__ = ("channel_points_used", "channel_points_won", "user")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.channel_points_used: int = data["channel_points_used"]
        self.channel_points_won: int = data["channel_points_won"]
        self.user = PartialUser(http, data["user_id"], data["user_login"])

    def __repr__(self):
        return f"<Predictor user={self.user} channel_points_used={self.channel_points_used} channel_points_won={self.channel_points_won}>"


class PredictionOutcome:
    """
    Represents a prediction outcome

    Attributes
    -----------
    outcome_id: :class:`str`
        ID for the outcome.
    title: :class:`str`
        Text displayed for outcome.
    channel_points: :class:`int`
        Number of Channel Points used for the outcome.
    color: :class:`str`
        Color for the outcome.
    users: :class:`int`
        Number of unique uesrs that chose the outcome.
    top_predictors: List[:class:`~twitchio.Predictor`]
        List of the top predictors. Could be None.
    """

    __slots__ = ("outcome_id", "title", "channel_points", "color", "users", "top_predictors")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.outcome_id: str = data["id"]
        self.title: str = data["title"]
        self.channel_points: int = data["channel_points"]
        self.color: str = data["color"]
        self.users: int = data["users"]
        if data["top_predictors"]:
            self.top_predictors: List[Predictor] = [Predictor(http, x) for x in data["top_predictors"]]
        else:
            self.top_predictors: List[Predictor] = None

    def __repr__(self):
        return f"<PredictionOutcome outcome_id={self.outcome_id} title={self.title} channel_points={self.channel_points} color={self.color} users={self.users}>"

    @property
    def colour(self) -> str:
        """The colour of the prediction. Alias to color."""
        return self.color

    def __repr__(self):
        return f"<PredictionOutcome outcome_id={self.outcome_id} title={self.title} channel_points={self.channel_points} color={self.color}>"


class Schedule:
    """
    Represents a channel's stream schedule

    Attributes
    -----------
    segments: List[:class:`~twitchio.ScheduleSegment`]
        List of segments of a channel's stream schedule.
    user: :class:`~twitchio.PartialUser`
        The user of the channel associated to the schedule.
    vacation: :class:`~twitchio.ScheduleVacation`
        Vacation details of stream schedule.
    """

    __slots__ = ("segments", "user", "vacation")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.segments = [ScheduleSegment(d) for d in data["data"]["segments"]] if data["data"]["segments"] else []
        self.user = PartialUser(http, data["data"]["broadcaster_id"], data["data"]["broadcaster_login"])
        self.vacation = ScheduleVacation(data["data"]["vacation"]) if data["data"]["vacation"] else None

    def __repr__(self):
        return f"<Schedule segments={self.segments} user={self.user} vacation={self.vacation}>"


class ScheduleSegment:
    """
    Represents a list segments of a channel's stream schedule

    Attributes
    -----------
    id: :class:`str`
        The ID for the scheduled broadcast.
    start_time: :class:`datetime.datetime`
        Scheduled start time for the scheduled broadcast
    end_time: Optional[:class:`datetime.datetime`]
        Scheduled end time for the scheduled broadcast
    title: :class:`str`
        Title for the scheduled broadcast.
    canceled_until: :class:`datetime.datetime`
        Used with recurring scheduled broadcasts. Specifies the date of the next recurring broadcast.
    category: :class:`~twitchio.ScheduleCategory`
        The game or category details for the scheduled broadcast.
    is_recurring: :class:`bool`
        Indicates if the scheduled broadcast is recurring weekly.
    """

    __slots__ = ("id", "start_time", "end_time", "title", "canceled_until", "category", "is_recurring")

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.start_time = parse_timestamp(data["start_time"])
        self.end_time = parse_timestamp(data["end_time"]) if data["end_time"] else None
        self.title: str = data["title"]
        self.canceled_until = parse_timestamp(data["canceled_until"]) if data["canceled_until"] else None
        self.category = ScheduleCategory(data["category"]) if data["category"] else None
        self.is_recurring: bool = data["is_recurring"]

    def __repr__(self):
        return f"<ScheduleSegment id={self.id} start_time={self.start_time} end_time={self.end_time} title={self.title} canceled_until={self.canceled_until} category={self.category} is_recurring={self.is_recurring}>"


class ScheduleCategory:
    """
    Game or category details of a stream's schedule

    Attributes
    -----------
    id: :class:`str`
        The game or category ID.
    name: :class:`str`
        The game or category name.
    """

    __slots__ = ("id", "name")

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]

    def __repr__(self):
        return f"<ScheduleCategory id={self.id} name={self.name}>"


class ScheduleVacation:
    """
    A schedule's vacation details

    Attributes
    -----------
    start_time: :class:`datetime.datetime`
        Start date of stream schedule vaction.
    end_time: :class:`datetime.datetime`
        End date of stream schedule vaction.
    """

    __slots__ = ("start_time", "end_time")

    def __init__(self, data: dict):
        self.start_time = parse_timestamp(data["start_time"])
        self.end_time = parse_timestamp(data["end_time"])

    def __repr__(self):
        return f"<ScheduleVacation start_time={self.start_time} end_time={self.end_time}>"


class Team:
    """
    Represents information for a specific Twitch Team

    Attributes
    -----------
    users: List[:class:`~twitchio.PartialUser`]
        List of users in the specified Team.
    background_image_url: :class:`str`
        URL for the Team background image.
    banner: :class:`str`
        URL for the Team banner.
    created_at: :class:`datetime.datetime`
        Date and time the Team was created.
    updated_at: :class:`datetime.datetime`
        Date and time the Team was last updated.
    info: :class:`str`
        Team description.
    thumbnail_url: :class:`str`
        Image URL for the Team logo.
    team_name: :class:`str`
        Team name.
    team_display_name: :class:`str`
        Team display name.
    id: :class:`str`
        Team ID.
    """

    __slots__ = (
        "users",
        "background_image_url",
        "banner",
        "created_at",
        "updated_at",
        "info",
        "thumbnail_url",
        "team_name",
        "team_display_name",
        "id",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.users: List[PartialUser] = [PartialUser(http, x["user_id"], x["user_login"]) for x in data["users"]]
        self.background_image_url: str = data["background_image_url"]
        self.banner: str = data["banner"]
        self.created_at = parse_timestamp(data["created_at"].split(" ")[0])
        self.updated_at = parse_timestamp(data["updated_at"].split(" ")[0])
        self.info: str = data["info"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.team_name: str = data["team_name"]
        self.team_display_name: str = data["team_display_name"]
        self.id = data["id"]

    def __repr__(self):
        return f"<Team users={self.users} team_name={self.team_name} team_display_name={self.team_display_name} id={self.id} created_at={self.created_at}>"


class ChannelTeams:
    """
    Represents the Twitch Teams of which the specified channel/broadcaster is a member

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster.
    background_image_url: :class:`str`
        URL for the Team background image.
    banner: :class:`str`
        URL for the Team banner.
    created_at: :class:`datetime.datetime`
        Date and time the Team was created.
    updated_at: :class:`datetime.datetime`
        Date and time the Team was last updated.
    info: :class:`str`
        Team description.
    thumbnail_url: :class:`str`
        Image URL for the Team logo.
    team_name: :class:`str`
        Team name.
    team_display_name: :class:`str`
        Team display name.
    id: :class:`str`
        Team ID.
    """

    __slots__ = (
        "broadcaster",
        "background_image_url",
        "banner",
        "created_at",
        "updated_at",
        "info",
        "thumbnail_url",
        "team_name",
        "team_display_name",
        "id",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.broadcaster: PartialUser = PartialUser(http, data["broadcaster_id"], data["broadcaster_login"])
        self.background_image_url: str = data["background_image_url"]
        self.banner: str = data["banner"]
        self.created_at = parse_timestamp(data["created_at"].split(" ")[0])
        self.updated_at = parse_timestamp(data["updated_at"].split(" ")[0])
        self.info: str = data["info"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.team_name: str = data["team_name"]
        self.team_display_name: str = data["team_display_name"]
        self.id = data["id"]

    def __repr__(self):
        return f"<ChannelTeams user={self.broadcaster} team_name={self.team_name} team_display_name={self.team_display_name} id={self.id} created_at={self.created_at}>"


class Poll:
    """
    Represents a list of Polls for a broadcaster / channel

    .. note::

        Twitch have removed support for voting with bits.
        By default bits_votes, bits_voting_enabled and bits_per_vote will be received as either 0 or False.

    Attributes
    -----------
    id: :class:`str`
        ID of a poll.
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster.
    title: :class:`str`
        Question displayed for the poll.
    choices: List[:class:`~twitchio.PollChoice`]
        The poll choices.
    bits_voting_enabled: :class:`bool`
        Indicates if Bits can be used for voting.

        .. warning::

            Twitch have removed support for voting with bits.
            This will return as False

    bits_per_vote: :class:`int`
        Number of Bits required to vote once with Bits.

        .. warning::

            Twitch have removed support for voting with bits.
            This will return as 0

    channel_points_voting_enabled: :class:`bool`
        Indicates if Channel Points can be used for voting.
    channel_points_per_vote: :class:`int`
        Number of Channel Points required to vote once with Channel Points.
    status: :class:`str`
        Poll status. Valid values: ACTIVE, COMPLETED, TERMINATED, ARCHIVED, MODERATED, INVALID
    duration: :class:`int`
        Total duration for the poll (in seconds).
    started_at: :class:`datetime.datetime`
        Date and time the poll was started.
    ended_at: :class:`datetime.datetime`
        Date and time the poll was ended.
    """

    __slots__ = (
        "id",
        "broadcaster",
        "title",
        "choices",
        "channel_points_voting_enabled",
        "channel_points_per_vote",
        "status",
        "duration",
        "started_at",
        "ended_at",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: str = data["id"]
        self.broadcaster = PartialUser(http, data["broadcaster_id"], data["broadcaster_login"])
        self.title: str = data["title"]
        self.choices: List[PollChoice] = [PollChoice(d) for d in data["choices"]] if data["choices"] else []
        self.channel_points_voting_enabled: bool = data["channel_points_voting_enabled"]
        self.channel_points_per_vote: int = data["channel_points_per_vote"]
        self.status: str = data["status"]
        self.duration: int = data["duration"]
        self.started_at: datetime.datetime = parse_timestamp(data["started_at"])
        try:
            self.ended_at: Optional[datetime.datetime] = parse_timestamp(data["ended_at"])
        except KeyError:
            self.ended_at = None

    def __repr__(self):
        return f"<Polls id={self.id} broadcaster={self.broadcaster} title={self.title} status={self.status} duration={self.duration} started_at={self.started_at} ended_at={self.ended_at}>"


class PollChoice:
    """
    Represents a polls choices

    Attributes
    -----------
    id: :class:`str`
        ID for the choice.
    title: :class:`str`
        Text displayed for the choice.
    votes: :class:`int`
        Total number of votes received for the choice across all methods of voting.
    channel_points_votes: :class:`int`
        Number of votes received via Channel Points.
    bits_votes: :class:`int`
        Number of votes received via Bits.

        .. warning::

            Twitch have removed support for voting with bits.
            This will return as 0

    """

    __slots__ = ("id", "title", "votes", "channel_points_votes", "bits_votes")

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.votes: int = data["votes"]
        self.channel_points_votes: int = data["channel_points_votes"]
        self.bits_votes: int = data["bits_votes"]

    def __repr__(self):
        return f"<PollChoice id={self.id} title={self.title} votes={self.votes} channel_points_votes={self.channel_points_votes} bits_votes={self.bits_votes}>"


class Goal:
    """
    Represents a list of Goals for a broadcaster / channel

    Attributes
    -----------
    id: :class:`str`
        An ID that uniquely identifies this goal.
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster.
    type: :class:`str`
        The type of goal.
        Valid values: follower, subscription, subscription_count, new_subscription and new_subscription_count.
    description: :class:`str`
        A description of the goal, if specified.
    current_amount: :class:`int`
        The current value.
    target_amount: :class:`int`
        Number of Bits required to vote once with Bits.
    created_at: :class:`datetime.datetime`
        Date and time of when the broadcaster created the goal.
    """

    __slots__ = (
        "id",
        "broadcaster",
        "type",
        "description",
        "current_amount",
        "target_amount",
        "created_at",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: str = data["id"]
        self.broadcaster = PartialUser(http, data["broadcaster_id"], data["broadcaster_login"])
        self.type: str = data["type"]
        self.description: str = data["description"]
        self.current_amount: int = data["current_amount"]
        self.target_amount: int = data["target_amount"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self):
        return f"<Goal id={self.id} broadcaster={self.broadcaster} description={self.description} current_amount={self.current_amount} target_amount={self.target_amount} created_at={self.created_at}>"


class ChatSettings:
    """
    Represents current chat settings of a broadcaster / channel

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster. Only returns the ID.
    emote_mode: :class:`bool`
        Indicates whether emote only mode is enabled.
    follower_mode: :class:`bool`
        Indicates whether follower only chat is enabled.
    follower_mode_duration: Optional[:class:`int`]
        The length of time, in minutes, that the followers must have followed the broadcaster to participate in chat.
    slow_mode: :class:`bool`
        Indicates whether the chat is in slow mode.
    slow_mode_wait_time: Optional[:class:`int`]
        The amount of time, in seconds, that users need to wait between sending messages.
    subscriber_mode: :class:`bool`
        Indicates whether only users that subscribe to the broadcaster's channel can talk in chat.
    unique_chat_mode: :class:`bool`
        Indicates whether the broadcaster requires users to post only unique messages in the chat room.
    moderator: Optional[:class:`~twitchio.PartialUser`]
        The User of the moderator, if provided. Only returns the ID.
    non_moderator_chat_delay: Optional[:class:`bool`]
        Indicates whether the broadcaster adds a short delay before chat messages appear in the chat room.
    non_moderator_chat_delay_duration: Optional[:class:`int`]
        The amount of time, in seconds, that messages are delayed from appearing in chat.
    """

    __slots__ = (
        "broadcaster",
        "emote_mode",
        "follower_mode",
        "follower_mode_duration",
        "slow_mode",
        "slow_mode_wait_time",
        "subscriber_mode",
        "unique_chat_mode",
        "moderator",
        "non_moderator_chat_delay",
        "non_moderator_chat_delay_duration",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.broadcaster = PartialUser(http, data["broadcaster_id"], None)
        self.emote_mode: bool = data["emote_mode"]
        self.follower_mode: bool = data["follower_mode"]
        self.follower_mode_duration: Optional[int] = data.get("follower_mode_duration")
        self.slow_mode: bool = data["slow_mode"]
        self.slow_mode_wait_time: Optional[int] = data.get("slow_mode_wait_time")
        self.subscriber_mode: bool = data["subscriber_mode"]
        self.unique_chat_mode: bool = data["unique_chat_mode"]
        self.non_moderator_chat_delay: Optional[bool] = data.get("non_moderator_chat_delay")
        self.non_moderator_chat_delay_duration: Optional[int] = data.get("non_moderator_chat_delay_duration")
        try:
            self.moderator = PartialUser(http, data["moderator_id"], None)
        except KeyError:
            self.moderator = None

    def __repr__(self):
        return f"<ChatSettings broadcaster={self.broadcaster} emote_mode={self.emote_mode} follower_mode={self.follower_mode} slow_mode={self.slow_mode} subscriber_mode={self.subscriber_mode} unique_chat_mode={self.unique_chat_mode}>"


class ChatterColor:
    """
    Represents chatters current name color.

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        PartialUser of the chatter.
    color: :class:`str`
        The color of the chatter's name.
    """

    __slots__ = ("user", "color")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.user = PartialUser(http, data["user_id"], data["user_login"])
        self.color: str = data["color"]

    def __repr__(self):
        return f"<ChatterColor user={self.user} color={self.color}>"


class Raid:
    """
    Represents a raid for a broadcaster / channel

    Attributes
    -----------
    created_at: :class:`datetime.datetime`
        Date and time of when the raid started.
    is_mature: :class:`bool`
        Indicates whether the stream being raided is marked as mature.
    """

    __slots__ = ("created_at", "is_mature")

    def __init__(self, data: dict):
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.is_mature: bool = data["is_mature"]

    def __repr__(self):
        return f"<Raid created_at={self.created_at} is_mature={self.is_mature}>"


class Ban:
    """
    Represents a ban for a broadcaster / channel

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster whose chat room the user was banned from chatting in.
    moderator: :class:`~twitchio.PartialUser`
        The moderator that banned the user.
    user: :class:`~twitchio.PartialUser`
        The user that was banned.
    created_at: :class:`datetime.datetime`
        Date and time of when the ban was created.
    """

    __slots__ = ("broadcaster", "moderator", "user", "created_at")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.broadcaster = PartialUser(http, data["broadcaster_id"], None)
        self.moderator = PartialUser(http, data["moderator_id"], None)
        self.user = PartialUser(http, data["user_id"], None)
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self):
        return f"<Ban broadcaster={self.broadcaster} user={self.user} created_at={self.created_at}>"


class Timeout:
    """
    Represents a timeout for a broadcaster / channel

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster whose chat room the user was timed out from chatting in.
    moderator: :class:`~twitchio.PartialUser`
        The moderator that timed the user out.
    user: :class:`~twitchio.PartialUser`
        The user that was timed out.
    created_at: :class:`datetime.datetime`
        Date and time of when the timeout was created.
    end_time: :class:`datetime.datetime`
        Date and time of when the timeout will end.
    """

    __slots__ = ("broadcaster", "moderator", "user", "created_at", "end_time")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.broadcaster = PartialUser(http, data["broadcaster_id"], None)
        self.moderator = PartialUser(http, data["moderator_id"], None)
        self.user = PartialUser(http, data["user_id"], None)
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.end_time: datetime.datetime = parse_timestamp(data["end_time"])

    def __repr__(self):
        return f"<Timeout broadcaster={self.broadcaster} user={self.user} created_at={self.created_at} end_time={self.end_time}>"


class ShieldStatus:
    """
    Represents a Shield Mode activation status.

    Attributes
    -----------
    moderator: :class:`~twitchio.PartialUser`
        The moderator that last activated Shield Mode.
    display_name: :class:`str`
        The moderator's display name. Is an empty string if Shield Mode hasn't been previously activated.
    last_activated_at: :class:`datetime.datetime`
        The UTC datetime of when Shield Mode was last activated.
        Is an empty string if Shield Mode hasn't been previously activated.
    is_active: :class:`bool`
        A Boolean value that determines whether Shield Mode is active.
        Is true if the broadcaster activated Shield Mode; otherwise, false.
    """

    __slots__ = ("moderator", "display_name", "last_activated_at", "is_active")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.moderator: Optional[PartialUser] = (
            PartialUser(http, data["moderator_id"], data["moderator_login"]) if data["moderator_id"] else None
        )
        self.display_name: Optional[str] = data.get("moderator_name")
        self.is_active: bool = data["is_active"]
        self.last_activated_at: Optional[datetime.datetime] = (
            parse_timestamp(data["last_activated_at"]) if data["last_activated_at"] else None
        )

    def __repr__(self):
        return f"<ShieldStatus moderator={self.moderator} is_active={self.is_active} last_activated_at={self.last_activated_at}>"
