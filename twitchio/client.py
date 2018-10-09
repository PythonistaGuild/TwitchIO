import asyncio
from typing import Union
from twitchio.http import HTTPSession


class TwitchClient:

    def __init__(self, *, loop=None, client_id=None, **kwargs):
        loop = loop or asyncio.get_event_loop()
        self.http = HTTPSession(loop=loop, client_id=client_id)

    async def get_users(self, *users: Union[str, int]):
        """|coro|

        Method which retrieves user information on the specified names/ids.

        Parameters
        ------------
        \*users: str [Required]
            The user name(s)/id(s) to retrieve data for.

        Returns
        ---------
        dict:
            Dict containing user(s) data.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream.

        Notes
        -------
        .. note::
            This method accepts both user ids or names, or a combination of both. Multiple names/ids may be passed.
        """
        return await self.http._get_users(*users)

    async def get_stream_by_name(self, channel: str):
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Parameters
        ------------
        channel: str [Required]
            The channel name to retrieve data for.

        Returns
        ---------
        dict:
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream.
        """
        return await self.http._get_stream_by_name(channel)

    async def get_stream_by_id(self, channel: int):
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Parameters
        ------------
        channel: int [Required]
            The channel id to retrieve data for.

        Returns
        ---------
        dict:
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream.
        """
        return await self.http._get_stream_by_id(channel)

    async def get_streams(self, *channels: Union[int, str]):
        """|coro|

        Method which retrieves multiple stream information on the given channels, provided they are active (Live).

        Parameters
        ------------
        \*channels: Union[int, str]
            The channels in id or name form, to retrieve information for.

        Returns
        ---------
        list:
            List containing active streamer data. Could be None if none of the streams are live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching streams.
        """
        return await self.http._get_streams(*channels)

    async def get_games(self, *games: Union[str, int]):
        """|coro|

        Method which retrieves games information on the given game ID(s)/Name(s).

        Parameters
        ------------
        \*games: Union[str, int] [Required]
            The games in either id or name form to retrieve information for.

        Returns
        ---------
        list:
            List containing game information. could be None if no games matched.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching games.
        """
        return await self.http._get_games(*games)

    async def get_chatters(self, channel: str):
        """|coro|

        Method which retrieves the currently active chatters on the given stream.

        Parameters
        ------------
        channel: str [Required]
            The channel name to retrieve data for.

        Returns
        ---------
        dict:
            Dict containing active chatter data.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream chatters.
        """
        return await self.http._get_chatters(channel)
