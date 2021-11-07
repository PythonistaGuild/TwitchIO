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
    "Team",
    "ChannelTeams",
)


class BitsLeaderboard:
    """
    Represents a Bits leaderboard from the twitch API.

    Attributes
    ------------
    started_at: datetime.datetime
        The time the leaderboard started.
    ended_at: datetime.datetime
        The time the leaderboard ended.
    leaders: List[:class:`BitLeaderboardUser`]
        The current leaders of the Leaderboard.
    """

    __slots__ = "_http", "leaders", "started_at", "ended_at"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.started_at = datetime.datetime.fromisoformat(data["date_range"]["started_at"])
        self.ended_at = datetime.datetime.fromisoformat(data["date_range"]["ended_at"])
        self.leaders = [BitLeaderboardUser(http, x) for x in data["data"]]

    def __repr__(self):
        return f"<BitsLeaderboard started_at={self.started_at} ended_at={self.ended_at}>"


class CheerEmoteTier:

    __slots__ = "min_bits", "id", "colour", "images", "can_cheer", "show_in_bits_card"

    def __init__(self, data: dict):
        self.min_bits: int = data["min_bits"]
        self.id: str = data["id"]
        self.colour: str = data["colour"]
        self.images = data["images"]
        self.can_cheer: bool = data["can_cheer"]
        self.show_in_bits_card: bool = data["show_in_bits_card"]

    def __repr__(self):
        return f"<CheerEmoteTier id={self.id} min_bits={self.min_bits}>"


class CheerEmote:

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


class Clip:

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
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id = data["id"]
        self.url = data["url"]
        self.embed_url = data["embed_url"]
        self.broadcaster = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.creator = PartialUser(http, data["creator_id"], data["creator_name"])
        self.video_id = data["video_id"]
        self.game_id = data["game_id"]
        self.language = data["language"]
        self.title = data["title"]
        self.views = data["view_count"]
        self.created_at = parse_timestamp(data["created_at"])
        self.thumbnail_url = data["thumbnail_url"]

    def __repr__(self):
        return f"<Clip id={self.id} broadcaster={self.broadcaster} creator={self.creator}>"


class HypeTrainContribution:

    __slots__ = "total", "type", "user"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.total: int = data["total"]
        self.type: str = data["type"]
        self.user = PartialUser(http, id=data["user"], name=None)  # we'll see how this goes

    def __repr__(self):
        return f"<HypeTrainContribution total={self.total} type={self.type} user={self.user}>"


class HypeTrainEvent:

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

    def __repr__(self):
        return f"<HypeTrainEvent id={self.id} type={self.type} level={self.level} broadcaster={self.broadcaster}>"


class BanEvent:

    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user", "expires_at"

    def __init__(self, http: "TwitchHTTP", data: dict, broadcaster: Optional[Union[PartialUser, User]]):
        self.id: str = data["id"]
        self.type: str = data["event_type"]
        self.timestamp = parse_timestamp(data["event_timestamp"])
        self.version: float = float(data["version"])
        self.broadcaster = broadcaster or PartialUser(
            http, data["event_data"]["broadcaster_id"], data["event_data"]["broadcaster_name"]
        )
        self.user = PartialUser(http, data["event_data"]["user_id"], data["event_data"]["user_name"])
        self.expires_at = (
            parse_timestamp(data["event_data"]["expires_at"]) if data["event_data"]["expires_at"] else None
        )

    def __repr__(self):
        return f"<BanEvent id={self.id} type={self.type} broadcaster={self.broadcaster} user={self.user}>"


class FollowEvent:

    __slots__ = "from_user", "to_user", "followed_at"

    def __init__(
        self,
        http: "TwitchHTTP",
        data: dict,
        from_: Union[User, PartialUser] = None,
        to: Union[User, PartialUser] = None,
    ):
        self.from_user = from_ or PartialUser(http, data["from_id"], data["from_name"])
        self.to_user = to or PartialUser(http, data["to_id"], data["to_name"])
        self.followed_at = parse_timestamp(data["followed_at"])

    def __repr__(self):
        return f"<FollowEvent from_user={self.from_user} to_user={self.to_user} followed_at={self.followed_at}>"


class SubscriptionEvent:

    __slots__ = "broadcaster", "gift", "tier", "plan_name", "user"

    def __init__(
        self,
        http: "TwitchHTTP",
        data: dict,
        broadcaster: Union[User, PartialUser] = None,
        user: Union[User, PartialUser] = None,
    ):
        self.broadcaster = broadcaster or PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.user = user or PartialUser(http, data["user_id"], data["user_name"])
        self.tier = int(data["tier"]) / 1000
        self.plan_name: str = data["plan_name"]
        self.gift: bool = data["is_gift"]

    def __repr__(self):
        return (
            f"<SubscriptionEvent broadcaster={self.broadcaster} user={self.user} tier={self.tier} "
            f"plan_name={self.plan_name} gift={self.gift}>"
        )


class Marker:

    __slots__ = "id", "created_at", "description", "position", "url"

    def __init__(self, data: dict):
        self.id: int = data["id"]
        self.created_at = parse_timestamp(data["created_at"])
        self.description: str = data["description"]
        self.position: int = data["position_seconds"]
        self.url: Optional[str] = data.get("URL")

    def __repr__(self):
        return f"<Marker id={self.id} created_at={self.created_at} position={self.position} url={self.url}>"


class VideoMarkers:

    __slots__ = "id", "markers"

    def __init__(self, data: dict):
        self.id: str = data["video_id"]
        self.markers = [Marker(d) for d in data]

    def __repr__(self):
        return f"<VideoMarkers id={self.id}>"


class Game:

    __slots__ = "id", "name", "box_art_url"

    def __init__(self, data: dict):
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self.box_art_url: str = data["box_art_url"]

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

    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user"

    def __init__(self, http: "TwitchHTTP", data: dict, broadcaster: Union[PartialUser, User]):
        self.id: int = data["id"]
        self.type = enums.ModEventEnum(value=data["event_type"])
        self.timestamp = parse_timestamp(data["event_timestamp"])
        self.version: str = data["version"]
        self.broadcaster = broadcaster
        self.user = PartialUser(http, data["event_data"]["user_id"], data["event_data"]["user_name"])

    def __repr__(self):
        return f"<ModEvent id={self.id} type={self.type} broadcaster={self.broadcaster} user={self.user}>"


class AutomodCheckMessage:

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

    __slots__ = "id", "permitted"

    def __init__(self, data: dict):
        self.id: str = data["msg_id"]
        self.permitted: bool = data["is_permitted"]

    def __repr__(self):
        return f"<AutomodCheckResponse id={self.id} permitted={self.permitted}>"


class Extension:

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
        self.id: id = int(data["id"])
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

        Deletes the video. For bulk deletion see :ref:`twitchio.Client.delete_videos`

        Parameters
        -----------
        token: :class:`str`
            The users oauth token with the channel:manage:videos
        """
        await self._http.delete_videos(token, ids=[str(self.id)])


class Tag:

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
        self.tag_ids: List[str] = data["tag_ids"]
        self.is_mature: bool = data["is_mature"]

    def __repr__(self):
        return f"<Stream id={self.id} user={self.user} title={self.title} started_at={self.started_at}>"


class ChannelInfo:

    __slots__ = ("user", "game_id", "game_name", "title", "language", "delay")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.user = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.game_id: int = data["game_id"]
        self.game_name: str = data["game_name"]
        self.title: str = data["title"]
        self.language: str = data["broadcaster_language"]
        self.delay: int = data["delay"]

    def __repr__(self):
        return f"<ChannelInfo user={self.user} game_id={self.game_id} game_name={self.game_name} title={self.title} language={self.language} delay={self.delay}>"


class Prediction:

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

    __slots__ = ("outcome_id", "title", "channel_points", "color")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.channel_points_used: int = data["channel_points_used"]
        self.channel_points_won: int = data["channel_points_won"]
        self.user = PartialUser(http, data["user"]["id"], data["user"]["name"])


class PredictionOutcome:

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

    @property
    def colour(self) -> str:
        """The colour of the prediction. Alias to color."""
        return self.color

    def __repr__(self):
        return f"<PredictionOutcome outcome_id={self.outcome_id} title={self.title} channel_points={self.channel_points} color={self.color}>"


class Schedule:

    __slots__ = ("segments", "user", "vacation")

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.segments = [ScheduleSegment(d) for d in data["data"]["segments"]]
        self.user = PartialUser(http, data["data"]["broadcaster_id"], data["data"]["broadcaster_login"])
        self.vacation = ScheduleVacation(data["data"]["vacation"]) if data["data"]["vacation"] else None

    def __repr__(self):
        return f"<Schedule segments={self.segments} user={self.user} vacation={self.vacation}>"


class ScheduleSegment:

    __slots__ = ("id", "start_time", "end_time", "title", "canceled_until", "category", "is_recurring")

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.start_time = parse_timestamp(data["start_time"])
        self.end_time = parse_timestamp(data["end_time"])
        self.title: str = data["title"]
        self.canceled_until = parse_timestamp(data["canceled_until"]) if data["canceled_until"] else None
        self.category = ScheduleCategory(data["category"]) if data["category"] else None
        self.is_recurring: bool = data["is_recurring"]

    def __repr__(self):
        return f"<Segment id={self.id} start_time={self.start_time} end_time={self.end_time} title={self.title} canceled_until={self.canceled_until} category={self.category} is_recurring={self.is_recurring}>"


class ScheduleCategory:

    __slots__ = ("id", "name")

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]

    def __repr__(self):
        return f"<ScheduleCategory id={self.id} name={self.name}>"


class ScheduleVacation:

    __slots__ = ("start_time", "end_time")

    def __init__(self, data: dict):
        self.start_time = parse_timestamp(data["start_time"])
        self.end_time = parse_timestamp(data["end_time"])

    def __repr__(self):
        return f"<ScheduleVacation start_time={self.start_time} end_time={self.end_time}>"


class Team:

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
        self.background_image_url = data["background_image_url"]
        self.banner = data["banner"]
        self.created_at = parse_timestamp(data["created_at"].split(" ")[0])
        self.updated_at = parse_timestamp(data["updated_at"].split(" ")[0])
        self.info = data["info"]
        self.thumbnail_url = data["thumbnail_url"]
        self.team_name = data["team_name"]
        self.team_display_name = data["team_display_name"]
        self.id = data["id"]

    def __repr__(self):
        return f"<Team users={self.users} team_name={self.team_name} team_display_name={self.team_display_name} id={self.id} created_at={self.created_at}>"


class ChannelTeams:

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
        self.background_image_url = data["background_image_url"]
        self.banner = data["banner"]
        self.created_at = parse_timestamp(data["created_at"].split(" ")[0])
        self.updated_at = parse_timestamp(data["updated_at"].split(" ")[0])
        self.info = data["info"]
        self.thumbnail_url = data["thumbnail_url"]
        self.team_name = data["team_name"]
        self.team_display_name = data["team_display_name"]
        self.id = data["id"]

    def __repr__(self):
        return f"<ChannelTeams user={self.broadcaster} team_name={self.team_name} team_display_name={self.team_display_name} id={self.id} created_at={self.created_at}>"
