"""
The MIT License (MIT)

Copyright (c) 2017-2019 TwitchIO

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
import sys
import traceback
from typing import Union
from twitchio.channel import Channel
from twitchio.client import Client
from twitchio.websocket import WSConnection


class Bot(Client):

    def __init__(self, irc_token: str, *, nick: str, prefix: Union[str, list, tuple],
                 initial_channels: Union[list, tuple]=None, **kwargs):
        super().__init__(client_id=kwargs.get('client_id'))

        self.loop = kwargs.get('loop', asyncio.get_event_loop())
        self._connection = WSConnection(bot=self, token=irc_token, nick=nick.lower(), loop=self.loop,
                                        initial_channels=initial_channels)

        self._preix = prefix
        self._nick = nick.lower()

        self._commands = {}
        self._events = {}
        self._cogs = {}

    def add_command(self):
        pass

    def add_event(self):
        pass

    @property
    def nick(self):
        return self._nick

    @property
    def commands(self):
        return self._commands

    @property
    def events(self):
        return self._events

    @property
    def cogs(self):
        return self._cogs

    def get_channel(self, name: str):
        """Retrieve a channel from the cache.

        Parameters
        -----------
        name: str
            The channel name to retrieve from cache. Returns None if no channel was found.

        Returns
        --------
            :class:`.Channel`
        """
        name = name.lower()

        try:
            self._connection._cache[name]  # this is a bit silly, but for now it'll do...
        except KeyError:
            return None

        # Basically the cache doesn't store channels naturally, instead it stores a channel key
        # With the associated users as a set.
        # We create a Channel here and return it only if the cache has that channel key.

        channel = Channel(name=name, websocket=self._connection, bot=self)
        return channel

    async def event_command_error(self, ctx, error):
        """|coro|

        Event called when an error occurs during command invocation.

        Parameters
        ------------
        ctx: :class:`.Context`
            The command context.
        error: :class:`.Exception`
            The exception raised while trying to invoke the command.
        """
        print('Ignoring exception in command: {0}:'.format(error), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_mode(self, channel, user, status):
        """|coro|

        Event called when a MODE is received from Twitch.

        Parameters
        ------------
        channel: :class:`.Channel`
            Channel object relevant to the MODE event.
        user: :class:`.User`
            User object containing relevant information to the MODE.
        status: str
            The JTV status received by Twitch. Could be either o+ or o-.
            Indicates a moderation promotion/demotion to the :class:`.User`
        """
        pass

    async def event_userstate(self, user):
        """|coro|

        Event called when a USERSTATE is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the USERSTATE.
        """
        pass

    async def event_raw_usernotice(self, channel, tags: dict):
        """|coro|

        Event called when a USERNOTICE is received from Twitch.
        Since USERNOTICE's can be fairly complex and vary, the following sub-events are available:

            :meth:`event_usernotice_subscription` :
            Called when a USERNOTICE Subscription or Re-subscription event is received.


        .. seealso::

            For more information on how to handle USERNOTICE's visit:
            https://dev.twitch.tv/docs/irc/tags/#usernotice-twitch-tags


        Parameters
        ------------
        channel: :class:`.Channel`
            Channel object relevant to the USERNOTICE event.
        tags : dict
            A dictionary with the relevant information associated with the USERNOTICE.
            This could vary depending on the event.
        """
        pass

    async def event_usernotice_subscription(self, metadata):
        """|coro|

        Event called when a USERNOTICE subscription or re-subscription event is received from Twitch.

        Parameters
        ------------
        metadata: :class:`twitchio.dataclasses.NoticeSubscription`
            The object containing various metadata about the subscription event.
            For ease of use, this contains a :class:`.User` and :class:`.Channel`.
        """
        pass

    async def event_part(self, user):
        """|coro|

        Event called when a PART is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the PART.
        """
        pass

    async def event_join(self, channel, user):
        """|coro|

        Event called when a JOIN is received from Twitch.

        Parameters
        ------------
        channel: :class:`.Channel`
            The channel associated with the JOIN.
        user: :class:`.User`
            User object containing relevant information to the JOIN.
        """
        pass

    async def event_message(self, message):
        """|coro|

        Event called when a PRIVMSG is received from Twitch.

        Parameters
        ------------
        message: :class:`.Message`
            Message object containing relevant information.
        """
        pass   # TODO

    async def event_error(self, error: Exception, data=None):
        """|coro|

        Event called when an error occurs while processing data.

        Parameters
        ------------
        error: Exception
            The exception raised.
        data: str
            The raw data received from Twitch. Depending on how this is called, this could be None.

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_error(error, data):
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        """
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_ready(self):
        """|coro|

        Event called when the Bot has logged in and is ready.

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_ready():
                print(f'Logged into Twitch | {bot.nick}')
        """
        pass

    async def event_raw_data(self, data):
        """|coro|

        Event called with the raw data received by Twitch.

        Parameters
        ------------
        data: str
            The raw data received from Twitch.

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_raw_data(data):
                print(data)
        """
        pass

    def run(self):
        try:
            self.loop.create_task(self._connection._connect())
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._connection._close()
