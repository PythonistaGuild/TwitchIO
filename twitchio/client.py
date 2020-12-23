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

import asyncio
import inspect
import warnings
import traceback
import sys
from typing import Union, Callable, List, Optional

from .websocket import WSConnection
from .http import TwitchHTTP
from .channel import Channel
from .message import Message
from .user import User
from .cache import user_cache


class Client:

    def __init__(self,
                 irc_token: str,
                 *,
                 nick: str,
                 api_token: str = None,
                 client_id: str = None,
                 client_secret: str = None,
                 initial_channels: Union[list, tuple, Callable] = None,
                 loop: asyncio.AbstractEventLoop = None,
                 **kwargs
                 ):

        self._nick = nick.lower()
        self.loop = loop or asyncio.get_event_loop()
        self._connection = WSConnection(client=self, token=irc_token, nick=nick.lower(), loop=self.loop,
                                        initial_channels=initial_channels)
        self._http = TwitchHTTP(self, nick, api_token=api_token, client_id=client_id, client_secret=client_secret)

        self._events = {}


    def run(self):
        try:
            self.loop.create_task(self._connection._connect())
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.loop.create_task(self.close())

    async def close(self):
        # TODO session close
        await self._connection._close()

    def run_event(self, name, *args, **kwargs):
        name = f"event_{name}"

        async def wrapped(func):
            try:
                await func(*args, **kwargs)
            except Exception as e:
                if name == "event_error":
                    # don't enter a dispatch loop!
                    raise

                self.run_event("error", e)

        inner_cb = getattr(self, name, None)
        if inner_cb is not None:
            if inspect.iscoroutinefunction(inner_cb):
                self.loop.create_task(wrapped(inner_cb))
            else:
                warnings.warn(f"event '{name}' callback is not a coroutine", category=RuntimeWarning)

        if name in self._events:
            for event in self._events[name]:
                self.loop.create_task(wrapped(event))

    def add_event(self, callback: Callable, name: str = None) -> None:
        if not inspect.iscoroutine(callback) and not inspect.iscoroutinefunction(callback):
            raise ValueError("callback must be a coroutine")

        event_name = name or callback.__name__
        callback._event = event_name  # used to remove the event

        if event_name in self._events:
            self._events[event_name].append(callback)

        else:
            self._events[event_name] = [callback]

    def remove_event(self, callback: Callable) -> bool:
        if not hasattr(callback, "_event"):
            raise ValueError("callback is not a registered event")

        if callback in self._events[callback._event]:
            self._events[callback._event].remove(callback)
            return True

        return False

    def event(self, name: str = None) -> Callable:

        def decorator(func: Callable) -> Callable:
            self.add_event(func, name)
            return func

        return decorator

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

        channel = Channel(name=name, websocket=self._connection)
        return channel

    @property
    def events(self):
        return self._events

    @property
    def nick(self):
        return self._nick

    @user_cache()
    async def fetch_users(self, names: List[str]=None, ids: List[int]=None, force=False) -> List[User]:
        """|coro|
        Fetches users from the helix API

        Parameters
        -----------
        names: Optional[List[:class:`str`]]
            usernames of people to fetch
        ids: Optional[List[:class:`str`]]
            ids of people to fetch
        force: :class:`bool`
            whether to force a fetch from the api, or check the cache first. Defaults to False

        Returns
        --------
        List[:class:`twitchio.User`]
        """
        assert names or ids
        data = await self._http.get_users(ids, names)
        return [User(self._http, x) for x in data]

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

    async def event_message(self, message: Message):
        """|coro|

        Event called when a PRIVMSG is received from Twitch.

        Parameters
        ------------
        message: :class:`.Message`
            Message object containing relevant information.
        """
        pass

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