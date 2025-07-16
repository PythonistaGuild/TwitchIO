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
    from twitchio.types_.responses import (
        ClipsResponseData,
        CreateClipResponseData,
        GamesResponse,
    )

    from .videos import Video


__all__ = ("Clip", "CreatedClip")


class Clip:
    """Represents a Twitch Clip

    Attributes
    -----------
    id: str
        The ID of the clip.
    url: str
        The URL of the clip.
    embed_url: str
        The URL to embed the clip with.
    broadcaster: twitchio.PartialUser
        The user whose channel the clip was created on.
    creator: twitchio.PartialUser
        The user who created the clip.
    video_id: str
        The ID of the video the clip is sourced from. This could be an empty :class:`str` if the video associated with the Clip
        is not available. This could be due to either the broadcaster or Twitch removing the video or because the video has
        not yet been made available (this can take a few minutes after Clip creation to occur).
    game_id: str
        The ID of the game that was being played when the clip was created.
    language: str
        The language, in an `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ format, of the stream when the clip was created.
    title: str
        The title of the clip.
    views: int
        The amount of views this clip has.
    created_at: datetime.datetime
        When the clip was created.
    thumbnail: twitchio.Asset
        The :class:`~twitchio.Asset` that can be used to read or save the thumbnail associated with this Clip.
    is_featured: bool
        Indicates if the clip is featured or not.
    """

    __slots__ = (
        "_http",
        "broadcaster",
        "created_at",
        "creator",
        "embed_url",
        "game_id",
        "id",
        "is_featured",
        "language",
        "thumbnail",
        "title",
        "url",
        "video_id",
        "views",
    )

    def __init__(self, data: ClipsResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.url: str = data["url"]
        self.embed_url: str = data["embed_url"]
        self.broadcaster: PartialUser = PartialUser(
            data["broadcaster_id"], data["broadcaster_name"].lower(), data["broadcaster_name"], http=http
        )
        self.creator: PartialUser = PartialUser(
            data["creator_id"], data["creator_name"].lower(), data["creator_name"], http=http
        )
        self.video_id: str = data["video_id"]
        self.game_id: str = data["game_id"]
        self.language: str = data["language"]
        self.title: str = data["title"]
        self.views: int = data["view_count"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.is_featured: bool = data["is_featured"]
        self._http: HTTPClient = http

    def __repr__(self) -> str:
        return f"<Clip id={self.id} broadcaster={self.broadcaster} creator={self.creator}>"

    def __str__(self) -> str:
        return self.id

    async def fetch_game(self) -> Game | None:
        """|coro|

        Fetches the :class:`~twitchio.Game` associated with this Clip.

        Returns
        -------
        Game | None
            The game associated with this Clip.
        """
        payload: GamesResponse = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http) if payload["data"] else None

    async def fetch_video(self) -> Video | None:
        """|coro|

        Fetches the :class:`~twitchio.Video` associated with this clip, if it can be found.

        .. note::

            If :attr:`.video_id` is an empty :class:`str` this method will return ``None``. This could be due to either the
            broadcaster or Twitch removing the video or because the video has not yet been made available
            (this can take a few minutes after Clip creation to occur).

        Returns
        -------
        Video
            The video associated with this Clip.
        None
            The video was not found or is not yet available.
        """
        if not self.video_id:
            return None

        data: list[Video] = await self._http.get_videos(ids=[self.video_id], period="all", sort="time", type="all", first=1)
        return data[0] if data else None


class CreatedClip:
    __slots__ = ("edit_url", "id")

    def __init__(self, data: CreateClipResponseData) -> None:
        self.id = data["id"]
        self.edit_url = data["edit_url"]
