# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

import asyncio
from collections import namedtuple
from typing import Union

from twitchio.errors import HTTPException
from twitchio.http import HTTPSession


User = namedtuple('User', ('id', 'login', 'display_name', 'type', 'broadcaster_type', 'description',
                           'profile_image', 'offline_image', 'view_count', 'created_at'))
Chatters = namedtuple('Chatters', ('count', 'all', 'broadcaster', 'vips', 'moderators', 'staff',
                                   'admins', 'global_mods', 'viewers'))


class Client:

    def __init__(self, *, loop=None, client_id=None, client_secret=None, api_token=None, scopes: list=None, **kwargs):
        loop = loop or asyncio.get_event_loop()
        self.http = HTTPSession(loop=loop, client_id=client_id, client_secret=client_secret, api_token=api_token, scopes=scopes)

    async def get_users(self, *users: Union[str, int]) -> list:
        """|coro|

        Method which retrieves user information on the specified names/ids.

        Parameters
        ------------
        \*users: str
            The user name(s)/id(s) to retrieve data for.

        Returns
        ---------
        list: User
            List containing user data in a namedtuple.

        Raises
        --------
        HTTPException
            Bad request while fetching stream.

        Notes
        -------
        .. note::
            This method accepts both user ids or names, or a combination of both. Multiple names/ids may be passed.
        """

        data = await self.http.get_users(*users)

        return [User(*user.values()) for user in data]

    async def get_stream(self, channel: Union[int, str]):
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Parameters
        ------------
        channel: Union[int, str]
            The channel id or name to retrieve data for.

        Returns
        ---------
        dict
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        HTTPException
            Bad request while fetching stream.
        """

        data = await self.http.get_streams(channels=[channel])

        try:
            return data[0]
        except IndexError:
            pass

    async def get_streams(self, *, game_id=None, language=None, channels=None, limit=None):
        """|coro|

        Method which retrieves multiple stream information on the given channels, provided they are active (Live).

        Parameters
        ------------
        game_id: Optional[int]
            The game to filter streams for.
        language: Optional[str]
            The language to filter streams for.
        channels: Optional[Union[int, str]]
            The channels in id or name form, to retrieve information for.
        limit: Optional[int]
            Maximum number of results to return.

        Returns
        ---------
        list
            List containing active streamer data. Could be None if none of the streams are live.

        Raises
        --------
        HTTPException
            Bad request while fetching streams.
        """

        return await self.http.get_streams(game_id=game_id, language=language, channels=channels, limit=limit)

    async def get_games(self, *games: Union[str, int]):
        """|coro|

        Method which retrieves games information on the given game ID(s)/Name(s).

        Parameters
        ------------
        \*games: Union[str, int]
            The games in either id or name form to retrieve information for.

        Returns
        ---------
        list
            List containing game information. Could be None if no games matched.

        Raises
        --------
        HTTPException
            Bad request while fetching games.
        """

        return await self.http.get_games(*games)

    async def get_top_games(self, limit=None):
        """|coro|

        Retrieves the top games currently being played on Twitch.

        Parameters
        ------------
        limit: Optional[int]
            Maximum amount of results to fetch.

        Returns
        ---------
        list
            List containing game information. Could be None if no games matched.

        Raises
        --------
        HTTPException
            Bad request while fetching games.
        """

        return await self.http.get_top_games(limit=limit)

    async def modify_webhook_subscription(self, *, callback, mode, topic, lease_seconds=0, secret=None):
        """|coro|

        Creates a webhook subscription.

        Parameters
        ----------
        callback: str
            The URL which will be called to verify the subscripton and on callback.
        mode: :class:`.WebhookMode`
            Mode which describes whether the subscription should be created or not.
        topic: :class:`.Topic`
            Details about the subscription.
        lease_seconds: Optional[int]
            How many seconds the subscription should last. Defaults to 0, maximum is 846000.
        secret: Optional[str]
            A secret string which Twitch will use to add the `X-Hub-Signature` header to webhook requests.
            You can use this to verify the POST request came from Twitch using `sha256(secret, body)`.

        Raises
        --------
        HTTPException
            Bad request while modifying the subscription.
        """

        await self.http.modify_webhook_subscription(
            callback=callback,
            mode=mode.name,
            topic=topic.as_uri(),
            lease_seconds=lease_seconds,
            secret=secret,
        )

    async def get_follow(self, from_id: Union[int, str], to_id: Union[int, str]):
        """|coro|

        Retrieves the follow relationship between two users, provided it exists.

        Parameters
        ------------
        from_id: Union[int, str]
            The user who is following.
        to_id: Union[int, str]
            The user being followed.

        Returns
        ---------
        dict
            Dict containing follow relationship data. Could be None if there is no follow relationship.

        Raises
        --------
        HTTPException
            Bad request while fetching follow relationship.
        """

        data = await self.http.get_follow(str(from_id), str(to_id))

        try:
            return data[0]
        except IndexError:
            pass

    async def get_followers(self, user_id: Union[int, str], *, count: bool=False):
        """|coro|

        Retrieves the list of users who are following a user.

        Parameters
        ------------
        user_id: Union[int, str]
            The user to retrieve the list of followers for.
        count: bool
            Whether to return only the total count of followers or not. Defaults to False.

        Returns
        ---------
        list
            List containing users following this user.
        int
            An int of the total count of followers. Only available when ``count``=True

        Raises
        --------
        HTTPException
            Bad request while fetching users.
        """

        return await self.http.get_followers(str(user_id), count=count)

    async def get_following(self, user_id: Union[int, str], count: bool=False):
        """|coro|

        Retrieves the list of users who this user is following.

        Parameters
        ------------
        user_id: Union[int, str]
            The user to retrieve the list of followed users for.
        count: bool
            Whether to return only the total count of followed users or not. Defaults to False.

        Returns
        ---------
        list
            List containing users that the user is following.
        int
            An int of the total count of followed users. Only available when ``count``=True

        Raises
        --------
        HTTPException
            Bad request while fetching users.
        """

        return await self.http.get_following(str(user_id), count=count)

    async def get_chatters(self, channel: str):
        """|coro|

        Method which retrieves the currently active chatters on the given stream.

        Parameters
        ------------
        channel: str
            The channel name to retrieve data for.

        Returns
        ---------
        Chatters
            Namedtuple containing active chatter data.

        Raises
        --------
        HTTPException
            Bad request while fetching stream chatters.
        """

        url = f'http://tmi.twitch.tv/group/user/{channel.lower()}/chatters'

        async with self.http._session.get(url) as resp:
            if 200 <= resp.status < 300:
                data = await resp.json()
            else:
                raise HTTPException(f'Fetching chatters failed: {resp.status}', resp.reason)

            all_ = []
            for x in data['chatters'].values():
                all_ += x

            return Chatters(data['chatter_count'], all_, *data['chatters'].values())

    async def create_clip(self, token: str, broadcaster_id: Union[str, int]):
        """|coro|

        Method which creates and returns an edit clip url for the given broadcaster_id.

        Parameters
        ------------
        token: str
            The token to use for Authorization.
        broadcaster_id: Union[str, int]
            The id of the stream you wish to create a clip for.

        Raises
        --------
        HTTPException
            Bad request while creating a clip.
        """

        return await self.http.create_clip(token, broadcaster_id)
