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
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import TeamsResponseData


__all__ = ("Team",)


class Team:
    """
    Represents information for a specific Twitch Team

    Attributes
    -----------
    users: list[twitchio.PartialUser]
        List of users in the specified Team.
    background_image_url: str
        URL for the Team background image.
    banner: str
        URL for the Team banner.
    created_at: datetime.datetime
        Date and time the Team was created.
    updated_at: datetime.datetime
        Date and time the Team was last updated.
    info: str
        Team description.
    thumbnail_url: str
        Image URL for the Team logo.
    name: str
        Team name.
    display_name: str
        Team display name.
    id: str
        Team ID.
    """

    __slots__ = (
        "users",
        "background_image",
        "banner",
        "created_at",
        "updated_at",
        "info",
        "thumbnail",
        "name",
        "display_name",
        "id",
    )

    def __init__(self, data: TeamsResponseData, *, http: HTTPClient) -> None:
        self.users: list[PartialUser] = [PartialUser(x["user_id"], x["user_login"], http=http) for x in data["users"]]
        self.background_image: Asset | None = (
            Asset(data["background_image_url"], http=http) if data["background_image_url"] else None
        )
        self.banner: str = data["banner"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"])
        self.info: str = data["info"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.name: str = data["team_name"]
        self.display_name: str = data["team_display_name"]
        self.id: str = data["id"]

    def __repr__(self) -> str:
        return f"<Team users={self.users} team_name={self.name} team_display_name={self.display_name} id={self.id} created_at={self.created_at}>"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Team):
            return NotImplemented

        return __value.id == self.id
