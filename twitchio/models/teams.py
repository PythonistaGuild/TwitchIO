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
    from twitchio.types_.responses import ChannelTeamsResponseData, TeamsResponseData


__all__ = ("ChannelTeam", "Team")


class Team:
    """Represents information for a specific Twitch Team

    Attributes
    -----------
    users: list[PartialUser]
        List of users in the specified Team.
    background_image: Asset | None
        URL for the Team background image.
    banner: Asset | None
        URL for the Team banner.
    created_at: datetime.datetime
        Date and time the Team was created.
    updated_at: datetime.datetime
        Date and time the Team was last updated.
    info: str
        Team description.
    thumbnail: Asset | None
        Image URL for the Team logo.
    name: str
        Team name.
    display_name: str
        Team display name.
    id: str
        Team ID.
    """

    __slots__ = (
        "background_image",
        "banner",
        "created_at",
        "display_name",
        "id",
        "info",
        "name",
        "thumbnail",
        "updated_at",
        "users",
    )

    def __init__(self, data: TeamsResponseData, *, http: HTTPClient) -> None:
        self.users: list[PartialUser] = [
            PartialUser(x["user_id"], x["user_login"], x["user_name"], http=http) for x in data["users"]
        ]
        self.background_image: Asset | None = (
            Asset(data["background_image_url"], http=http) if data["background_image_url"] else None
        )
        self.banner: Asset | None = Asset(data["banner"], http=http) if data["banner"] else None
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"])
        self.info: str = data["info"]
        self.thumbnail: Asset | None = Asset(data["thumbnail_url"], http=http) if data["thumbnail_url"] else None
        self.name: str = data["team_name"]
        self.display_name: str = data["team_display_name"]
        self.id: str = data["id"]

    def __repr__(self) -> str:
        return f"<Team users={self.users} name={self.name} display_name={self.display_name} id={self.id} created_at={self.created_at}>"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, __value: object) -> bool:
        return __value.id == self.id if isinstance(__value, Team) else NotImplemented


class ChannelTeam:
    """Represents the Twitch Teams of which the specified channel/broadcaster is a member

    Attributes
    -----------
    broadcaster: PartialUser
        The broadcaster.
    background_image: Asset | None
        Asset for the team background image.
    banner: Asset | None
        Asset for the team banner.
    created_at: datetime.datetime
        Date and time the Team was created.
    updated_at: datetime.datetime`
        Date and time the Team was last updated.
    info: str
        Team description.
    thumbnail_url: Asset | None
        Asset for the team logo.
    name: str
        Team name.
    display_name: str
        Team display name.
    id: str
        Team ID.
    """

    __slots__ = (
        "background_image",
        "banner",
        "broadcaster",
        "created_at",
        "display_name",
        "id",
        "info",
        "name",
        "thumbnail",
        "updated_at",
    )

    def __init__(self, data: ChannelTeamsResponseData, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=http
        )
        self.background_image: Asset | None = (
            Asset(data["background_image_url"], http=http) if data["background_image_url"] else None
        )
        self.banner: Asset | None = Asset(data["banner"], http=http) if data["banner"] else None
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"])
        self.info: str = data["info"]
        self.thumbnail: Asset | None = Asset(data["thumbnail_url"], http=http) if data["thumbnail_url"] else None
        self.name: str = data["team_name"]
        self.display_name: str = data["team_display_name"]
        self.id: str = data["id"]

    def __repr__(self) -> str:
        return f"<ChannelTeam user={self.broadcaster} name={self.name} display_name={self.display_name} id={self.id} created_at={self.created_at}>"
