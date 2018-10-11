import asyncio
from typing import Union
from twitchio.http import HelixHTTPSession


class TwitchClient:

    def __init__(self, *, loop=None, client_id=None, **kwargs):
        loop = loop or asyncio.get_event_loop()
        self.http = HelixHTTPSession(loop=loop, client_id=client_id)

    async def get_users(self, *users: Union[str, int]):
        """|coro|

        Method which retrieves user information on the specified names/ids.

        Parameters
        ------------
        \*users: str
            The user name(s)/id(s) to retrieve data for.

        Returns
        ---------
        dict
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

        return await self.http.get_users(*users)

    async def get_stream_by_name(self, channel: str):
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Parameters
        ------------
        channel: str
            The channel name to retrieve data for.

        Returns
        ---------
        dict
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream.
        """

        data = await self.http.get_streams(channels=[channel])
        return data[0]

    async def get_stream_by_id(self, channel: int):
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Parameters
        ------------
        channel: int
            The channel id to retrieve data for.

        Returns
        ---------
        dict
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream.
        """

        data = await self.http.get_streams(channels=[channel])
        return data[0]

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
        TwitchHTTPException
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
        TwitchHTTPException
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
        TwitchHTTPException
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
        TwitchHTTPException
            Bad request while modifying the subscription.
        """

        await self.http.modify_webhook_subscription(
            callback=callback,
            mode=mode.name,
            topic=topic.as_uri(),
            lease_seconds=lease_seconds,
            secret=secret,
        )
