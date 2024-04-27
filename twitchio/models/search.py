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
from twitchio.utils import parse_timestamp

from .games import Game


if TYPE_CHECKING:
    from twitchio.http import HTTPClient
    from twitchio.types_.responses import GamesResponse, SearchChannelsResponseData


__all__ = ("SearchChannel",)


class SearchChannel:
    __slots__ = (
        "_http",
        "id",
        "game_id",
        "name",
        "display_name",
        "language",
        "title",
        "thumbnail",
        "live",
        "started_at",
        "tag_ids",
    )

    def __init__(self, data: SearchChannelsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.display_name: str = data["display_name"]
        self.name: str = data["broadcaster_login"]
        self.id: str = data["id"]
        self.game_id: str = data["game_id"]
        self.title: str = data["title"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.language: str = data["broadcaster_language"]
        self.live: bool = data["is_live"]
        self.started_at = parse_timestamp(data["started_at"]) if self.live else None
        self.tag_ids: list[str] = data["tag_ids"]

    def __repr__(self) -> str:
        return f"<SearchUser name={self.name} title={self.title} live={self.live}>"

    async def fetch_game(self) -> Game:
        """
        Fetches the [`Game`][twitchio.Game] associated with this channel.

        !!! note
            The [`Game`][twitchio.Game] returned is current from the time the [`SearchChannel`][twitchio.SearchChannel]
            instance was created.

        Returns
        -------
        twitchio.Game
            The game associated with this [`SearchChannel`][twitchio.SearchChannel] instance.
        """
        payload: GamesResponse = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http)
