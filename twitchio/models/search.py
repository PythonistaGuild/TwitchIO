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

from __future__ import annotations

from typing import TYPE_CHECKING

from twitchio.assets import Asset
from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp

from .games import Game


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import GamesResponse, SearchChannelsResponseData


__all__ = ("SearchChannel",)


class SearchChannel:
    """Represents a channel via a search.

    Attributes
    -----------
    broadcaster: PartialUser
        The broadcaster / channel.
    title: str
        The stream's title. Is an empty string if the broadcaster didn't set it.
    game_id: str
        The ID of the game that the broadcaster is playing or last played.
    game_name: str
        The name of the game that the broadcaster is playing or last played.
    live: bool
        A Boolean value that determines whether the broadcaster is streaming live. Is True if the broadcaster is streaming live; otherwise, False.
    tags: list[str]
        The tags applied to the channel.
    thumbnail: Asset
        An Asset for the thumbnail of the broadcaster's profile image.
    language: str
        The ISO 639-1 two-letter language code of the language used by the broadcaster. For example, en for English. If the broadcaster uses a language not in the list of `supported stream languages <https://help.twitch.tv/s/article/languages-on-twitch#streamlang>`_, the value is other.
    started_at: datetime.datetime | None
        Datetime of when the broadcaster started streaming. Is None if the broadcaster is not streaming live.

    """

    __slots__ = (
        "_http",
        "broadcaster",
        "game_id",
        "language",
        "live",
        "name",
        "started_at",
        "tags",
        "thumbnail",
        "title",
    )

    def __init__(self, data: SearchChannelsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.broadcaster: PartialUser = PartialUser(data["id"], data["broadcaster_login"], data["display_name"], http=http)
        self.game_id: str = data["game_id"]
        self.title: str = data["title"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.language: str = data["broadcaster_language"]
        self.live: bool = data["is_live"]
        self.started_at: datetime.datetime | None = parse_timestamp(data["started_at"]) if self.live else None
        self.tags: list[str] = data["tags"]

    def __repr__(self) -> str:
        return f"<SearchChannel broadcaster={self.broadcaster} title={self.title} live={self.live} game_id={self.game_id}>"

    async def fetch_game(self) -> Game | None:
        """|coro|

        Fetches the :class:`~twitchio.Game` associated with this channel.

        The :class:`~twitchio.Game` returned is current from the time the :class:`~twitchio.SearchChannel`
        instance was created.

        Returns
        -------
        twitchio.Game
            The game associated with this :class:`~twitchio.SearchChannel` instance.
        """
        payload: GamesResponse = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http) if payload["data"] else None
