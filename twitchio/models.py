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

from .user import BitLeaderboardUser, PartialUser

if TYPE_CHECKING:
    from .http import TwitchHTTP

__all__ = (
    "BitsLeaderboard",
    "Clip",
    "CheerEmote",
    "CheerEmoteTier"
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