import inspect

from .base import *
from .dataclasses import Context


class Client(BaseConnection):

    def __init__(self, **attrs):
        modes = attrs.pop('modes', ("commands", "tags", "membership"))
        self.intergrated = attrs.get('integrated', False)
        self._gather_channels = attrs.get('initial_channels')
        attrs['modes'] = modes
        super().__init__(**attrs)

    def run(self, pre_run=None):
        # todo Major Buggo in pre_run....
        """A blocking call that initializes the IRC Bot event loop.

        This should be the last function to be called.

        .. warning:: You do not need to use this function unless you are accessing the IRC Endpoints."""

        if not self.loop:
            self.loop = asyncio.get_event_loop()

        if callable(pre_run):
            ret = pre_run()
            if inspect.isawaitable(ret):
                self.loop.run_until_complete(ret)

        if callable(self._gather_channels):
            channels = self._gather_channels()
            if inspect.isawaitable(channels):
                channels = self.loop.run_until_complete(channels)
        else:
            channels = self._gather_channels

        # todo Task or Stand-Alone / Actual callback handling.

        try:
            self.loop.create_task(self.keep_alive(channels))
        except RuntimeError:
            pass  # TODO Handling here.

        if self.intergrated:
            return

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            #todo stuff
            print('Terminating TwitchIO Client...')

    async def get_chatters(self, channel):
        """|coro|

        Method which attempts to retrieve the current viewers for the provided channel.

        Parameters
        ------------
        channel: Context, Channel or str
            The channel name to retrieve viewer data from. Could be either Context, channel or string.

        Returns
        ---------
        json
            A json containing the streams viewer data.
        """
        if isinstance(channel, Context):
            channel = channel.channel

        return await self._http._get_chatters(channel)

    async def get_streams(self, channels: (list, tuple)):
        """|coro|

        Method which retrieves information on active streams with the channels provided.

        Parameters
        ------------
        channels: list or tuple of str or int
            A list of channel/stream names and/or ids.

        Returns
        ---------
        dict
            Dict containing active streamer data.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching streams.
        """
        if not isinstance(channels, (list, tuple)):
            raise ClientError('Channels must be either a list or tuple. Type {} was provided.'.format(type(channels)))

        return await self._http._get_streams(channels)

    async def is_live(self, channel):
        """|coro|

        Method which checks whether a stream is currently live.

        Parameters
        ------------
        channel: Context, Channel or str
            The channel to check. Could be either Context, channel or string.

        Returns
        ---------
        bool
            Boolean indicating whether the channel is currently live.
        """
        if isinstance(channel, Context):
            channel = channel.channel
        resp = await self._http._get_stream(channel)

        try:
            resp = resp['data'][0]['type'] == 'live'
        except IndexError:
            return False
        return resp

    @property
    def rate_status(self):
        """The current rate limit status.

        If the bot has Moderator status on all current connected channels,
        this will return Full else Restricted.

        Returns
        ---------
        status: str
            Full/Restricted
        """
        if self._rate_status == 1:
            return "Full"
        else:
            return "Restricted"
