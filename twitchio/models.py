"""
The MIT License (MIT)

Copyright (c) 2017-2020 TwitchIO

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
from typing import Optional, Union, TYPE_CHECKING

from . import enums
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
    "ModEvent"
)

class BitsLeaderboard:
    """
    Represents a Bits leaderboard from the twitch API.
    """
    __slots__ = "_http", "leaders", "started_at", "ended_at"
    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.started_at = datetime.datetime.fromisoformat(data['date_range']['started_at'])
        self.ended_at = datetime.datetime.fromisoformat(data['date_range']['ended_at'])
        self.leaders = [BitLeaderboardUser(http, x) for x in data['data']]

class CheerEmoteTier:
    __slots__ = "min_bits", "id", "colour", "images", "can_cheer", "show_in_bits_card"
    def __init__(self, data: dict):
        self.min_bits: int = data['min_bits']
        self.id: str = data['id']
        self.colour: str = data['colour']
        self.images = data['images']
        self.can_cheer: bool = data['can_cheer']
        self.show_in_bits_card: bool = data['show_in_bits_card']

class CheerEmote:
    __slots__ = "_http", "prefix", "tiers", "type", "order", "last_updated", "charitable"
    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.prefix = data['prefix']
        self.tiers = [CheerEmoteTier(x) for x in data['tiers']]
        self.type = data['type']
        self.order = data['order']
        self.last_updated = datetime.datetime.strptime(data['last_updated'], "%Y-%m-%dT%H:%M:%SZ")
        self.charitable = data['is_charitable']

class Clip:
    __slots__ = "id", "url", "embed_url", "broadcaster", "creator", "video_id", "game_id", "language",\
                "title", "views", "created_at", "thumbnail_url"
    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id = data['id']
        self.url = data['url']
        self.embed_url = data['embed_url']
        self.broadcaster = PartialUser(http, data['broadcaster_id'], data['broadcaster_name'])
        self.creator = PartialUser(http, data['creator_id'], data['creator_name'])
        self.video_id = data['video_id']
        self.game_id = data['game_id']
        self.language = data['language']
        self.title = data['title']
        self.views = data['view_count']
        self.created_at = datetime.datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        self.thumbnail_url = data['thumbnail_url']

class HypeTrainContribution:
    __slots__ = "total", "type", "user"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.total: int = data['total']
        self.type: str = data['type']
        self.user = PartialUser(http, id=data['user'], name=None) # we'll see how this goes

class HypeTrainEvent:
    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "expiry", "event_id", "goal", "level",\
                "started_at", "top_contributions", "contributions_total", "cooldown_end_time", "last_contribution"

    def __init__(self, http: "TwitchHTTP", data: dict):
        self.id: str = data['id']
        self.event_id: str = data['event_data']['id']
        self.type: str = data['event_type']
        self.version: str = data['version']
        self.broadcaster = PartialUser(http, id=data['event_data']['broadcaster_id'], name=None)
        self.timestamp = datetime.datetime.strptime(data['event_timestamp'], "%Y-%m-%dT%H:%M:%SZ")
        self.cooldown_end_time = datetime.datetime.strptime(data['event_data']['cooldown_end_time'], "%Y-%m-%dT%H:%M:%SZ")
        self.expiry = datetime.datetime.strptime(data['expires_at'], "%Y-%m-%dT%H:%M:%SZ")
        self.started_at = datetime.datetime.strptime(data['event_data']['started_at'], "%Y-%m-%dT%H:%M:%SZ")
        self.last_contribution = HypeTrainContribution(http, data['event_data']['last_contribution'])
        self.level: int = data['event_data']['level']
        self.top_contributions = [HypeTrainContribution(http, x) for x in data['event_data']['top_contributions']]
        self.contributions_total: int = data['event_data']['total']

class BanEvent:
    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user", "expires_at"

    def __init__(self, http: "TwitchHTTP", data: dict, broadcaster: Optional[Union[PartialUser, User]]):
        self.id: str = data['id']
        self.type: str = data['event_type']
        self.timestamp = datetime.datetime.strptime(data['event_timestamp'], "%Y-%m-%dT%H:%M:%SZ")
        self.version: float = float(data['version'])
        self.broadcaster = broadcaster or PartialUser(http, data['event_data']['broadcaster_id'],
                                                      data['event_data']['broadcaster_name'])
        self.user = PartialUser(http, data['event_data']['user_id'], data['event_data']['user_name'])
        self.expires_at = datetime.datetime.strptime(data['event_data']['expires_at'], "%Y-%m-%dT%H:%M:%SZ") if \
            data['event_data']['expires_at'] else None

class FollowEvent:
    __slots__ = "from_user", "to_user", "followed_at"

    def __init__(self, http: "TwitchHTTP", data: dict, from_: Union[User, PartialUser]=None, to: Union[User, PartialUser]=None):
        self.from_user = from_ or PartialUser(http, data['from_id'], data['from_name'])
        self.to_user = to or PartialUser(http, data['to_id'], data['to_id'])
        self.followed_at = datetime.datetime.strptime(data['followed_at'], "%Y-%m-%dT%H:%M:%SZ")

class SubscriptionEvent:
    __slots__ = "broadcaster", "gift", "tier", "plan_name", "user"

    def __init__(self, http: "TwitchHTTP", data: dict, broadcaster: Union[User, PartialUser]=None, user: Union[User, PartialUser]=None):
        self.broadcaster = broadcaster or PartialUser(http, data['broadcaster_id'], data['broadcaster_name'])
        self.user = user or PartialUser(http, data['user_id'], data['user_name'])
        self.tier = int(data['tier']) / 1000
        self.plan_name: str = data['plan_name']
        self.gift: bool = data['is_gift']

class Marker:
    __slots__ = "id", "created_at", "description", "position", "url"

    def __init__(self, data: dict):
        self.id: int = data['id']
        self.created_at = datetime.datetime.strptime(data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        self.description: str = data['description']
        self.position: int = data['position_seconds']
        self.url: Optional[str] = data.get("URL", None)

class VideoMarkers:
    __slots__ = "id", "markers"

    def __init__(self, data: dict):
        self.id: str = data['video_id']
        self.markers = [Marker(d) for d in data]

class Game:
    __slots__ = "id", "name", "box_art_url"

    def __init__(self, data: dict):
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self.box_art_url: str = data['box_art_url']

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
        self.id: int = data['id']
        self.type = enums.ModEventEnum(value=data['event_type'])
        self.timestamp = datetime.datetime.strptime(data['event_timestamp'], "%Y-%m-%dT%H:%M:%SZ")
        self.version: str = data['version']
        self.broadcaster = broadcaster
        self.user = PartialUser(http, data['event_data']['user_id'], data['event_data']['user_name'])
