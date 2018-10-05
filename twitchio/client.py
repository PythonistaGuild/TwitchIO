from typing import Sequence
from twitchio.http import HTTPSession


class TwitchClient:

    def __init__(self, loop, *, client_id=None):
        self.http = HTTPSession(loop=loop, client_id=client_id)

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

    async def get_streams_by_id(self, channels: Sequence[int]):
        """|coro|

        Method which retrieves multiple stream information on the given channels, provided they are active (Live).

        Parameters
        ------------
        channels: List[int]
            The channels in id form, to retrieve information for.

        Returns
        ---------
        list:
            List containing active streamer data. Could be None if none of the streams are live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching streams.
        """
        return await self.http._get_streams_by_id(channels)

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
