"""MIT License

Copyright (c) 2017-2022 TwitchIO

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
import asyncio
import sys
import traceback
from typing import Optional, Union, Coroutine, Dict, TYPE_CHECKING

from .channel import Channel
from .limiter import IRCRateLimiter
from .message import Message
from .parser import IRCPayload
from .shards import ShardInfo
from .chatter import PartialChatter
from .websocket import Websocket

if TYPE_CHECKING:
    from ext.eventsub import EventSubClient


class Client:
    """THe main Twitch HTTP and IRC Client.

    This client can be used as a standalone to both HTTP and IRC or used together.

    Parameters
    ----------
    token: Optional[str]
        The token to use for IRC authentication.
    heartbeat: Optional[float]
        An optional heartbeat to provide to keep connections over proxies and such alive.
        Defaults to 30.0.
    verified: Optional[bool]
        Whether or not your bot is verified or not. Defaults to False.
    join_timeout: Optional[float]
        An optional float to use to timeout channel joins. Defaults to 15.0.
    initial_channels: Optional[Union[list, tuple, callable, coroutine]]
        An optional list or tuple of channels to join on bot start. This may be a callable or coroutine,
        but must return a list or tuple.
    shard_limit: int
        The amount of channels per websocket. Defaults to 100 channels per socket.
    cache_size: Optional[int]
        The size of the internal channel cache. Defaults to unlimited.
    eventsub: Optional[:class:`EventSubClient`]
        The EventSubClient instance to use with the client to dispatch subscribed webhook events.
    """

    def __init__(self,
                 token: Optional[str] = None,
                 heartbeat: Optional[float] = 30.0,
                 verified: Optional[bool] = False,
                 join_timeout: Optional[float] = 15.0,
                 initial_channels: Optional[Union[list, tuple, callable, Coroutine]] = None,
                 shard_limit: int = 100,
                 cache_size: Optional[int] = None,
                 eventsub: Optional["EventSubClient"] = None,
                 ):
        self._token: str = token.removeprefix('oauth:') if token else token

        self._heartbeat = heartbeat
        self._verified = verified
        self._join_timeout = join_timeout

        self._cache_size = cache_size

        self._shards = {}
        self._shard_limit = shard_limit
        self._initial_channels = initial_channels or []

        self._limiter = IRCRateLimiter(status='verified' if verified else 'user', bucket='joins')

        self._eventsub = None
        if eventsub:
            self._eventsub = eventsub
            self._eventsub._client = self
            self._eventsub._client_ready.set()

        self.loop: asyncio.AbstractEventLoop = None  # type: ignore

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise exc_val

    async def _shard(self):
        if asyncio.iscoroutinefunction(self._initial_channels):
            channels = await self._initial_channels()

        elif callable(self._initial_channels):
            channels = self._initial_channels()

        elif isinstance(self._initial_channels, (list, tuple)):
            channels = self._initial_channels
        else:
            raise TypeError('initial_channels must be a list, tuple, callable or coroutine returning a list or tuple.')

        if not isinstance(channels, (list, tuple)):
            raise TypeError('initial_channels must return a list or tuple of str.')

        chunked = [channels[x:x+self._shard_limit] for x in range(0, len(channels), self._shard_limit)]

        for index, chunk in enumerate(chunked, 1):
            self._shards[index] = ShardInfo(number=index,
                                            channels=channels,
                                            websocket=Websocket(
                                                client=self,
                                                limiter=self._limiter,
                                                shard_index=index,
                                                heartbeat=self._heartbeat,
                                                join_timeout=self._join_timeout,
                                                initial_channels=chunk,
                                                cache_size=self._cache_size
                                            ))

    def run(self, token: Optional[str] = None) -> None:
        """A blocking call that starts and connects the bot to IRC.

        This methods abstracts away starting and cleaning up for you.

        Parameters
        ----------
        token: str
            An optional token to pass to connect to Twitch IRC. This can also be placed in your bots init.

        .. warning::

            You should not use this method unless you are connecting to IRC.

        .. note::

            Since this method is blocking it should be the last thing to be called.
            Anything under it will only execute after this method has completed.

        .. info::

            If you want to take more control over cleanup, see :meth:`close`.
        """
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self._shard())

        if token:
            token = token.removeprefix("oauth:")

        self._token = token if not self._token else self._token

        asyncio.run(self.setup())

        for shard in self._shards.values():
            shard._websocket._token = self._token
            self.loop.create_task(shard._websocket._connect())

        if self._eventsub:
            self.loop.create_task(self._eventsub._run())  # TODO: Cleanup...

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.loop.run_until_complete(self.close())

    async def start(self, token: Optional[str] = None) -> None:
        """|coro|

        Parameters
        ----------
        token: str
            An optional token to pass to connect to Twitch IRC. This can also be placed in :class:`Client` init.
        """
        await self._shard()

        if token:
            token = token.removeprefix("oauth:")

        self._token = token if not self._token else self._token

        await self.setup()

        shard_tasks = []
        for shard in self._shards.values():
            shard._websocket._token = self._token
            shard_tasks.append(asyncio.create_task(shard._websocket._connect()))

        await asyncio.wait(shard_tasks)

    async def close(self) -> None:
        for shard in self._shards.values():
            await shard._websocket.close()

    @property
    def shards(self) -> Dict[int, ShardInfo]:
        """A dict of shard number to :class:`ShardInfo`"""
        return self._shards

    @property
    def nick(self) -> Optional[str]:
        """The bots nickname.

        This may be None if a shard has not become ready, or you have entered invalid credentials.
        """
        return self._shards[1]._websocket.nick

    nickname = nick

    def get_channel(self, name: str, /) -> Optional[Channel]:
        """Method which returns a channel from cache if it exits.

        Could be None if the channel is not in cache.

        Parameters
        ----------
        name: str
            The name of the channel to search cache for.

        Returns
        -------
        channel: Optional[:class:`Channel`]
            The channel matching the provided name.
        """
        name = name.removeprefix('#').lower()

        for shard in self._shards.values():
            channel = shard._websocket._channel_cache.get(name, default=None)

            if channel:
                break

        return channel

    def get_message(self, id_: str, /) -> Optional[Message]:
        """Method which returns a message from cache if it exists.

        Could be None if the message is not in cache.

        Parameters
        ----------
        id_: str
            The message ID to search cache for.

        Returns
        -------
        message: Optional[:class:`Message`]
            The message matching the provided identifier.
        """
        for shard in self._shards.values():
            message = shard._websocket._message_cache.get(id_, default=None)

            if message:
                break

        return message

    async def event_shard_ready(self, number: int) -> None:
        """|coro|

        Event fired when a shard becomes ready.

        Parameters
        ----------
        number: int
            The shard number identifier.

        Returns
        -------
        None
        """
        pass

    async def event_ready(self) -> None:
        """|coro|

        Event fired when the bot has completed startup.
        This includes all shards being ready.

        Returns
        -------
        None
        """
        pass

    async def event_error(self, error: Exception) -> None:
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_raw_data(self, data: str) -> None:
        """|coro|

        Event fired with the raw data received, unparsed, by Twitch.

        Parameters
        ----------
        data: str
            The data received from Twitch.

        Returns
        -------
        None
        """
        pass

    async def event_raw_payload(self, payload: IRCPayload) -> None:
        """|coro|

        Event fired with the parsed IRC payload object.

        Parameters
        ----------
        payload: :class:`IRCPayload`
            The parsed IRC payload from Twitch.

        Returns
        -------
        None
        """
        pass

    async def event_message(self, message) -> None:
        """|coro|

        Event fired when receiving a message in a joined channel.

        Parameters
        ----------
        message
            The message received via Twitch.

        Returns
        -------
        None
        """
        pass

    async def event_join(self, channel: Channel, chatter: PartialChatter) -> None:
        """|coro|

        Event fired when a JOIN is received via Twitch.

        Parameters
        ----------
        channel: :class:`Channel`
            ...
        chatter: :class:`PartialChatter`
            ...
        """

    async def event_part(self, channel: Optional[Channel], chatter: PartialChatter) -> None:
        """|coro|

        Event fired when a PART is received via Twitch.

        Parameters
        ----------
        channel: Optional[:class:`Channel`]
            ... Could be None if the channel is not in your cache.
        chatter: :class:`PartialChatter`
            ...
        """

    async def setup(self) -> None:
        """|coro|

        Method called before the Client has logged in to Twitch, used for asynchronous setup.

        Useful for setting up state, like databases, before the client has logged in.

        .. versionadded:: 3.0
        """
        pass
