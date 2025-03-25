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

from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp

from .games import Game


if TYPE_CHECKING:
    from twitchio.http import HTTPAsyncIterator, HTTPClient
    from twitchio.types_.responses import (
        ChannelEditorsResponseData,
        ChannelFollowersResponse,
        ChannelFollowersResponseData,
        ChannelInformationResponseData,
        FollowedChannelsResponse,
        FollowedChannelsResponseData,
        GamesResponse,
    )

__all__ = (
    "ChannelEditor",
    "ChannelFollowerEvent",
    "ChannelFollowers",
    "ChannelInfo",
    "FollowedChannels",
    "FollowedChannelsEvent",
)


class ChannelEditor:
    """Represents an editor of a channel.

    Attributes
    -----------
    user: PartialUser
        PartialUser who has editor permissions.
    created_at: datetime.datetime
        The datetime of when the user became one of the broadcaster's editors.
    """

    __slots__ = ("created_at", "user")

    def __init__(self, data: ChannelEditorsResponseData, *, http: HTTPClient) -> None:
        self.user = PartialUser(data["user_id"], data["user_name"].lower(), data["user_name"], http=http)
        self.created_at = parse_timestamp(data["created_at"])

    def __repr__(self) -> str:
        return f"<ChannelEditor user={self.user} created_at={self.created_at}>"


class FollowedChannelsEvent:
    """Represents a followed channel event.

    Attributes
    -----------
    broadcaster: PartialUser
        PartialUser that identifies the channel that this user is following.
        If no results are found it returns an empty list.
    followed_at: datetime.datetime
        The datetime of when the user followed the channel.
    """

    __slots__ = ("broadcaster", "followed_at")

    def __init__(self, data: FollowedChannelsResponseData, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=http
        )
        self.followed_at = parse_timestamp(data["followed_at"])

    def __repr__(self) -> str:
        return f"<ChannelFollowedEvent broadcaster={self.broadcaster} followed_at={self.followed_at}>"


class FollowedChannels:
    """Represents channels followed.

    Attributes
    -----------
    followed: HTTPAsyncIterator[FollowedChannelsEvent]
        HTTPAsyncIterator of PartialUsers that identifies channel's this user follows.
        If no results are found it returns an empty list.
    total: int
        The total number of users that follow this broadcaster.
    """

    __slots__ = ("followed", "total")

    def __init__(self, data: FollowedChannelsResponse, iterator: HTTPAsyncIterator[FollowedChannelsEvent]) -> None:
        self.followed: HTTPAsyncIterator[FollowedChannelsEvent] = iterator
        self.total: int = int(data["total"])

    def __repr__(self) -> str:
        return f"<ChannelsFollowed total={self.total}>"


class ChannelFollowerEvent:
    """Represents a ChannelFollowerEvent

    Attributes
    -----------
    user: PartialUser
        PartialUser that identifies a user that follows this channel.
    followed_at: datetime.datetime
        The datetime of when the user followed the channel.
    """

    __slots__ = ("followed_at", "user")

    def __init__(self, data: ChannelFollowersResponseData, *, http: HTTPClient) -> None:
        self.user = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.followed_at = parse_timestamp(data["followed_at"])

    def __repr__(self) -> str:
        return f"<ChannelFollowerEvent user={self.user} followed_at={self.followed_at}>"


class ChannelFollowers:
    """Represents channel followers

    Attributes
    -----------
    followers: HTTPAsyncIterator[ChannelFollowerEvent]
        PartialUser that identifies a user that follows this channel.
    total: int
        The total number of users that follow this broadcaster.
    """

    __slots__ = ("followers", "total")

    def __init__(self, data: ChannelFollowersResponse, iterator: HTTPAsyncIterator[ChannelFollowerEvent]) -> None:
        self.followers: HTTPAsyncIterator[ChannelFollowerEvent] = iterator
        self.total: int = int(data["total"])

    def __repr__(self) -> str:
        return f"<ChannelFollowers total={self.total}>"


class ChannelInfo:
    """Represents a channel's current information

    Attributes
    -----------
    user: PartialUser
        The user whose channel information was requested.
    game_id: int
        Current game ID being played on the channel.
    game_name: str
        Name of the game being played on the channel.
    title: str
        Title of the stream.
    language: str
        Language of the channel.
    delay: int
        Stream delay in seconds.
        This defaults to 0 if the broadcaster_id does not match the user access token.
    tags: list[str]
        The tags applied to the channel.
    classification_labels: list[str]
        The CCLs applied to the channel.
    is_branded_content: bool
        Boolean flag indicating if the channel has branded content.
    """

    __slots__ = (
        "_http",
        "classification_labels",
        "delay",
        "game_id",
        "game_name",
        "is_branded_content",
        "language",
        "tags",
        "title",
        "user",
    )

    def __init__(self, data: ChannelInformationResponseData, *, http: HTTPClient) -> None:
        self.user = PartialUser(data["broadcaster_id"], data["broadcaster_name"], data["broadcaster_name"], http=http)
        self.game_id: str = data["game_id"]
        self.game_name: str = data["game_name"]
        self.title: str = data["title"]
        self.language: str = data["broadcaster_language"]
        self.delay: int = int(data["delay"])
        self.tags: list[str] = data["tags"]
        self.classification_labels: list[str] = data["content_classification_labels"]
        self.is_branded_content: bool = data["is_branded_content"]

        self._http: HTTPClient = http

    def __repr__(self) -> str:
        return f"<ChannelInfo user={self.user} game_id={self.game_id} game_name={self.game_name} title={self.title} language={self.language} delay={self.delay}>"

    async def fetch_game(self) -> Game | None:
        """|coro|

        Fetches the :class:~twitchio.Game` associated with this ChannelInfo.

        Returns
        -------
        Game | None
            The game associated with this ChannelInfo.
        """
        payload: GamesResponse = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http) if payload["data"] else None
