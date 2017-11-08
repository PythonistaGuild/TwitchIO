import inspect

from .connection import *


class Client(BaseConnection):

    def __init__(self, nick: str, token: str, initial_channels: (list, tuple, callable), **attrs):
        modes = attrs.pop('modes', ("commands", "tags", "membership"))
        self.intergrated = attrs.get('integrated', False)
        self._gather_channels = initial_channels
        attrs['nick'] = nick
        attrs['token'] = token
        attrs['modes'] = modes
        super().__init__(**attrs)

    def run(self, pre_run=None):
        """A blocking call that initializes the event loop.

        This should be the last function to be called."""

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
            task = self.loop.create_task(self.keep_alive(channels))
        except RuntimeError:
            pass  # TODO Handling here.

        def end_loop(fut):
            self.loop.stop()

        task.add_done_callback(end_loop)

        if self.intergrated:
            self.task = task
            return

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            #todo stuff
            print('Terminating TwitchIO Client...')

    async def get_chatters(self, channel: str):
        """|coro|

        Method which attempts to retrieve the current viewers for the provided channel.

        Parameters
        ------------
        channel: str
            The channel name to retrieve viewer data from.

        Returns
        ---------
        json
            A json containing the channels viewer data.
        """
        return await self._http._get_chatters(channel)

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
