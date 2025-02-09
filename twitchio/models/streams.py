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
        CreateStreamMarkerResponseData,
        GamesResponse,
        StreamMarkersResponseData,
        StreamMarkersResponseMarkers,
        StreamsResponseData,
    )


__all__ = ("Stream", "StreamMarker", "VideoMarkers")


class Stream:
    """Represents a Stream

    Attributes
    -----------
    id: str
        The current stream ID.
    user: twitchio.PartialUser
        The user who is streaming.
    game_id: str | None
        Current game ID being played on the channel. Could be `None` if no category / game has been set.
    game_name: str | None
        Name of the game being played on the channel. Could be `None` if no category / game has been set.
    type: str
        Whether the stream is "live" or not.
    title: str
        Title of the stream.
    viewer_count: int
        Current viewer count of the stream
    started_at: datetime.datetime
        UTC timestamp of when the stream started.
    language: str
        Language of the channel.
    thumbnail: Asset
        The :class:`~twitchio.Asset` which can be used to read or save the thumbnail associated with this stream.
    is_mature: bool
        Indicates whether the stream is intended for mature audience.
    tags: list[str]
        The tags applied to the channel.
    """

    __slots__ = (
        "_http",
        "game_id",
        "game_name",
        "id",
        "is_mature",
        "language",
        "started_at",
        "tags",
        "thumbnail",
        "title",
        "type",
        "user",
        "viewer_count",
    )

    def __init__(self, data: StreamsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http

        self.id: str = data["id"]
        self.user = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.game_id: str | None = data["game_id"] or None
        self.game_name: str | None = data["game_name"] or None
        self.type: str = data["type"]
        self.title: str = data["title"]
        self.viewer_count: int = data["viewer_count"]
        self.started_at = parse_timestamp(data["started_at"])
        self.language: str = data["language"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], dimensions=(640, 360), http=http)
        self.is_mature: bool = data["is_mature"]
        self.tags: list[str] = data["tags"]

    def __repr__(self) -> str:
        return f"<Stream id={self.id} user={self.user} title={self.title} started_at={self.started_at}>"

    async def fetch_game(self) -> Game | None:
        """|coro|

        Fetches the :class:`~twitchio.Game` associated with this stream.

        The :class:`~twitchio.Game` returned is current from the time the :class:`~twitchio.Stream`
        instance was created.

        Could be `None` if no category / game was set at the time the :class:`~twitchio.Stream`
        instance was created.

        Returns
        -------
        twitchio.Game | None
            The game associated with this :class:`~twitchio.Stream` instance, or `None`.
        """
        if self.game_id is None:
            return None

        payload: GamesResponse = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http) if payload["data"] else None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Stream):
            return NotImplemented

        return self.id == other.id and self.started_at == other.started_at


class StreamMarker:
    """Represents a stream marker.

    Attributes
    ----------
    id: str
        An ID that identifies the single market you added.
    created_at: datetime.datetime
        Datetime of when the user created the stream marker.
    position: int
        The relative offset (in seconds) of the marker from the beginning of the stream.
    url: str | None
        A URL that opens the video in Twitch Highlighter. This is None on creation but populated when fetched.
    """

    __slots__ = ("created_at", "description", "id", "position", "url")

    def __init__(self, data: CreateStreamMarkerResponseData | StreamMarkersResponseMarkers) -> None:
        self.id: str = data["id"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.description: str = data["description"]
        self.position: int = int(data["position_seconds"])
        self.url: str | None = data.get("url")

    def __repr__(self) -> str:
        return f"<StreamMarker id={self.id} created_at={self.created_at} position={self.position}>"


class VideoMarkers:
    """Represents stream markers for the latest stream.

    Attributes
    ----------
    user: PartialUser
        The user that created the stream marker.
    video_id: str
        An ID that identifies this video.
    markers: list[StreamMarker]
        The list of markers in this video. The list in ascending order by when the marker was created.
    """

    __slots__ = ("markers", "user", "video_id")

    def __init__(self, data: StreamMarkersResponseData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.video_id: str = data["videos"][0]["video_id"]
        self.markers: list[StreamMarker] = [StreamMarker(d) for d in data["videos"][0]["markers"]]

    def __repr__(self) -> str:
        return f"<VideoMarkers user={self.user} video_id={self.video_id}>"
