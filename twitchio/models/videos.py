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


if TYPE_CHECKING:
    from twitchio.http import HTTPClient
    from twitchio.types_.responses import VideosResponseData


__all__ = ("Video",)


class Video:
    """Represents video information

    Attributes
    -----------
    id: int
        The ID of the video.
    user: PartialUser
        User who owns the video.
    title: str
        Title of the video
    description: str
        Description of the video.
    created_at: datetime.datetime
        Date when the video was created.
    published_at: datetime.datetime
        Date when the video was published.
    url: str
        URL of the video.
    thumbnail_url: str
        Template URL for the thumbnail of the video.
    viewable: str
        Indicates whether the video is public or private.
    view_count: int
        Number of times the video has been viewed.
    language: str
        Language of the video.
    type: str
        The type of video.
    duration: str
        Length of the video.
    """

    __slots__ = (
        "_http",
        "created_at",
        "description",
        "duration",
        "id",
        "language",
        "published_at",
        "thumbnail",
        "title",
        "type",
        "url",
        "user",
        "view_count",
        "viewable",
    )

    def __init__(self, data: VideosResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.user = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.title: str = data["title"]
        self.description: str = data["description"]
        self.created_at = parse_timestamp(data["created_at"])
        self.published_at = parse_timestamp(data["published_at"])
        self.url: str = data["url"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.viewable: str = data["viewable"]
        self.view_count: int = data["view_count"]
        self.language: str = data["language"]
        self.type: str = data["type"]
        self.duration: str = data["duration"]

    def __repr__(self) -> str:
        return f"<Video id={self.id} title={self.title} url={self.url}>"

    async def delete(self, token_for: str) -> None:
        """Deletes the video. For bulk deletion see :meth:`~twitchio.Client.delete_videos`

        Parameters
        -----------
        token_for: str
            A user oauth token with the ``channel:manage:videos`` scope.
        """
        await self._http.delete_videos(ids=[self.id], token_for=token_for)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Video):
            return NotImplemented

        return self.id == other.id
