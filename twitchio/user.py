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
import time
from typing import TYPE_CHECKING, List, Optional

from .enums import BroadcasterTypeEnum, UserTypeEnum
from .errors import HTTPException, Unauthorized
from .rewards import CustomReward


if TYPE_CHECKING:
    from .http import TwitchHTTP
    from .channel import Channel
    from .models import BitsLeaderboard, Clip

__all__ = (
    "PartialUser",
    "BitLeaderboardUser",
    "User",
)

class PartialUser:
    __slots__ = "id", "name", "_http", "_cached_rewards"
    def __init__(self, http: "TwitchHTTP", id: str, name: str):
        self.id = int(id)
        self.name = name
        self._http = http

        self._cached_rewards = None

    @property
    def channel(self) -> Optional["Channel"]:
        """
        Returns the :class:`twitchio.Channel` associated with this user. Could be None if you are not part of the channel's chat

        Returns
        --------
        Optional[:class:`twitchio.Channel`]
        """
        from .channel import Channel
        if self.name in self._http.client._connection._cache:
            return Channel(self.name, self._http.client._connection)

    async def fetch(self, token: str=None, force=False) -> "User":
        """|coro|
        Fetches the full user from the api or cache

        Parameters
        -----------
        token : :class:`str`
            Optional OAuth token to be used instead of the bot-wide OAuth token
        force : :class:`bool`
            Whether to force a fetch from the api or try to get from the cache first. Defaults to False

        Returns
        --------
        :class:`twitchio.User` The full user associated with this PartialUser
        """
        data = await self._http.client.fetch_users(ids=[self.id], force=force, token=token)
        return data[0]

    async def get_custom_rewards(self, token: str, *, only_manageable=False, ids: List[int]=None, force=False) -> List["CustomReward"]:
        """|coro|
        Fetches the channels custom rewards (aka channel points) from the api.
        Parameters
        ----------
        token : :class:`str`
            The users oauth token.
        only_manageable : :class:`bool`
            Whether to fetch all rewards or only ones you can manage. Defaults to false.
        ids : List[:class:`int`]
            An optional list of reward ids
        force : :class:`bool`
            Whether to force a fetch or try to get from cache. Defaults to False

        Returns
        -------

        """
        if not force and self._cached_rewards:
            if self._cached_rewards[0]+300 > time.monotonic():
                return self._cached_rewards[1]

        try:
            data = await self._http.get_rewards(token, self.id, only_manageable, ids)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise
        else:
            values = [CustomReward(self._http, x, self) for x in data]
            self._cached_rewards = time.monotonic(), values
            return values


    async def fetch_bits_leaderboard(self, token: str, period: str="all", user_id: int=None, started_at: datetime.datetime=None) -> "BitsLeaderboard":
        """|coro|
        Fetches the bits leaderboard for the channel. This requires an OAuth token with the bits:read scope.

        Parameters
        -----------
        token: :class:`str`
            the OAuth token with the bits:read scope
        period: Optional[:class:`str`]
            one of `day`, `week`, `month`, `year`, or `all`, defaults to `all`
        started_at: Optional[:class:`datetime.datetime`]
            the timestamp to start the period at. This is ignored if the period is `all`
        user_id: Optional[:class:`int`]
            the id of the user to fetch for
        """
        from .models import BitsLeaderboard
        data = await self._http.get_bits_board(token, period, user_id, started_at)
        return BitsLeaderboard(self._http, data)

    async def start_commercial(self, token: str, length: int) -> dict:
        """|coro|
        Starts a commercial on the channel. Requires an OAuth token with the `channel:edit:commercial` scope.

        Parameters
        -----------
        token: :class:`str`
            the OAuth token
        length: :class:`int`
            the length of the commercial. Should be one of `30`, `60`, `90`, `120`, `150`, `180`

        Returns
        --------
        :class:`dict` a dictionary with `length`, `message`, and `retry_after`
        """
        data = await self._http.post_commericial(token, str(self.id), length)
        return data[0]

    async def create_clip(self, token: str, has_delay=False) -> dict:
        """|coro|
        Creates a clip on the channel. Note that clips are not created instantly, so you will have to query
        :ref:`~.get_clips` to confirm the clip was created. Requires an OAuth token with the `clips:edit` scope

        Parameters
        -----------
        token: :class:`str`
            the OAuth token
        has_delay: :class:`bool`
            Whether the clip should have a delay to match that of a viewer. Defaults to False

        Returns
        --------
        :class:`dict` a dictionary with `id` and `edit_url`
        """
        data = await self._http.post_create_clip(token, self.id, has_delay)
        return data[0]

    async def fetch_clips(self) -> List["Clip"]:
        """|coro|
        Fetches clips from the api. This will only return clips from the specified user.
        Use :ref:`twitchio.Client` to fetch clips by id

        Returns
        --------
        List[:class:`twitchio.Clip`]
        """
        from .models import Clip

        data = await self._http.get_clips(self.id)

        return [Clip(self._http, x) for x in data]

    async def fetch_hypetrain_events(self, id: str=None, token: str=None):
        """|coro|
        Fetches hypetrain event from the api. Needs a token with the channel:read:hype_train scope.

        Parameters
        -----------
        id: Optional[:class:`str`]
            The hypetrain id, if known, to fetch for
        token: Optional[:class:`str`]
            The oauth token to use. Will default to the one passed to the bot/client.

        Returns
        --------
            List[:class:`twitchio.HypeTrainEvent`]
            A list of hypetrain events
        """
        from .models import HypeTrainEvent
        data = await self._http.get_hype_train(self.id, id=id, token=token)
        return [HypeTrainEvent(self._http, d) for d in data]

class BitLeaderboardUser(PartialUser):
    __slots__ = "rank", "score"
    def __init__(self, http: "TwitchHTTP", data: dict):
        super(BitLeaderboardUser, self).__init__(http, id=data['user_id'], name=data['user_name'])
        self.rank: int = data['rank']
        self.score: int = data['score']

class User(PartialUser):
    __slots__ = ("_http", "id", "name", "display_name", "type", "broadcaster_type", "description", "profile_image", "offline_image", "view_count", "email", "_cached_rewards")
    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.id = int(data['id'])
        self.name = data['login']
        self.display_name = data['display_name']
        self.type = UserTypeEnum(data['type'])
        self.broadcaster_type = BroadcasterTypeEnum(data['broadcaster_type'])
        self.description = data['description']
        self.profile_image = data['profile_image_url']
        self.offline_image = data['offline_image_url']
        self.view_count = data['view_count'],
        self.email = data.get("email", None)