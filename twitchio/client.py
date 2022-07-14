"""MIT License

Copyright (c) 2017-present TwitchIO

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
from __future__ import annotations

import asyncio
import inspect
import sys
import traceback
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Optional, Tuple, Union

from twitchio.http import HTTPAwaitableAsyncIterator, HTTPHandler

from .channel import Channel
from .chatter import PartialChatter
from .limiter import IRCRateLimiter
from .message import Message
from .models import PartialUser, User
from .parser import IRCPayload
from .shards import ShardInfo
from .tokens import BaseTokenHandler
from .websocket import Websocket

if TYPE_CHECKING:
    from ext.eventsub import EventSubClient

_initial_channels_T = Optional[Union[List[str], Tuple[str], Callable[[], List[str]], Coroutine[Any, Any, None]]]

__all__ = ("Client",)


class Client:
    """THe main Twitch HTTP and IRC Client.

    This client can be used as a standalone to both HTTP and IRC or used together.

    Parameters
    ----------
    token_handler: :class:`~twitchio.BaseTokenHandler`
        Your token handler instance. See ... # TODO doc link to explaining token handlers
    heartbeat: Optional[:class:`float`]
        An optional heartbeat to provide to keep connections over proxies and such alive.
        Defaults to 30.0.
    verified: Optional[:class:`bool`]
        Whether or not your bot is verified or not. Defaults to False.
    join_timeout: Optional[:class:`float`]
        An optional float to use to timeout channel joins. Defaults to 15.0.
    initial_channels: Optional[Union[List[:class:`str`], Tuple[:class:`str`], :class:`callable`, :class:`coroutine`]]
        An optional list or tuple of channels to join on bot start. This may be a callable or coroutine,
        but must return a :clas:`list` or :class:`tuple`.
    shard_limit: :class:`int`
        The amount of channels per websocket. Defaults to 100 channels per socket.
    cache_size: Optional[:class:`int`]
        The size of the internal channel cache. Defaults to unlimited.
    eventsub: Optional[:class:`~twitchio.ext.EventSubClient`]
        The EventSubClient instance to use with the client to dispatch subscribed webhook events.
    """

    def __init__(
        self,
        token_handler: BaseTokenHandler,
        heartbeat: Optional[float] = 30.0,
        verified: Optional[bool] = False,
        join_timeout: Optional[float] = 15.0,
        initial_channels: _initial_channels_T = None,
        shard_limit: int = 100,
        cache_size: Optional[int] = None,
        eventsub: Optional[EventSubClient] = None,
        **kwargs,
    ):
        self._token_handler: BaseTokenHandler = token_handler._post_init(self)
        self._heartbeat = heartbeat
        self._verified = verified
        self._join_timeout = join_timeout

        self._cache_size = cache_size

        self._shards = {}
        self._shard_limit = shard_limit
        self._initial_channels: _initial_channels_T = initial_channels or []

        self._limiter = IRCRateLimiter(status="verified" if verified else "user", bucket="joins")
        self._http = HTTPHandler(None, self._token_handler, client=self, **kwargs)

        self._eventsub: Optional[EventSubClient] = None
        if eventsub:
            self._eventsub = eventsub
            self._eventsub._client = self
            self._eventsub._client_ready.set()

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._kwargs: Dict[str, Any] = kwargs

        self._is_closed = False
        self._has_acquired = False

    async def __aenter__(self):
        await self.setup()
        self._has_acquired = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._has_acquired = False
        if not self._is_closed:
            await self.close()

    async def _shard(self):
        if inspect.iscoroutinefunction(self._initial_channels):
            channels = await self._initial_channels()  # type: ignore

        elif callable(self._initial_channels):
            channels = self._initial_channels()

        elif isinstance(self._initial_channels, (list, tuple)):
            channels = self._initial_channels
        else:
            raise TypeError("initial_channels must be a list, tuple, callable or coroutine returning a list or tuple.")

        if not isinstance(channels, (list, tuple)):
            raise TypeError("initial_channels must return a list or tuple of str.")

        chunked = [channels[x : x + self._shard_limit] for x in range(0, len(channels), self._shard_limit)]

        for index, chunk in enumerate(chunked, 1):
            self._shards[index] = ShardInfo(
                number=index,
                channels=channels,
                websocket=Websocket(
                    token_handler=self._token_handler,
                    client=self,
                    limiter=self._limiter,
                    shard_index=index,
                    heartbeat=self._heartbeat,
                    join_timeout=self._join_timeout,
                    initial_channels=chunk,  # type: ignore
                    cache_size=self._cache_size,
                    **self._kwargs,
                ),
            )

    def run(self) -> None:
        """A blocking call that starts and connects the bot to IRC.

        This methods abstracts away starting and cleaning up for you.

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

        for shard in self._shards.values():
            self.loop.create_task(shard._websocket._connect())

        if self._eventsub:
            self.loop.create_task(self._eventsub._run())  # TODO: Cleanup...

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.loop.run_until_complete(self.close())

    async def start(self) -> None:
        """|coro|
        This method connects to twitch's IRC servers, and prepares to handle incoming messages.
        This method will not return until all the IRC shards have been closed
        """
        if not self._has_acquired:
            raise RuntimeError(
                "You must first enter an async context by calling `async with client:`"
            )  # TODO need better error

        await self._shard()

        shard_tasks = [asyncio.create_task(shard._websocket._connect()) for shard in self._shards.values()]

        await asyncio.wait(shard_tasks)

    async def close(self) -> None:
        for shard in self._shards.values():
            await shard._websocket.close()

        await self._http.cleanup()

        self._is_closed = True

    @property
    def shards(self) -> Dict[int, ShardInfo]:
        """A dict of shard number to :class:`~twitchio.ShardInfo`"""
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
        name: :class:`str`
            The name of the channel to search cache for.

        Returns
        -------
        channel: Optional[:class:`~twitchio.Channel`]
            The channel matching the provided name.
        """
        name = name.strip("#").lower()

        channel = None

        for shard in self._shards.values():
            channel = shard._websocket._channel_cache.get(name, default=None)

            if channel:
                break

        return channel

    def get_message(self, id_: str, /) -> Optional[Message]:
        """Method which returns a message from cache if it exists.

        Could be ``None`` if the message is not in cache.

        Parameters
        ----------
        id_: :class:`str`
            The message ID to search cache for.

        Returns
        -------
        message: Optional[:class:`~twitchio.Message`]
            The message matching the provided identifier.
        """
        message = None

        for shard in self._shards.values():
            message = shard._websocket._message_cache.get(id_, default=None)

            if message:
                break

        return message

    async def fetch_users(
        self, names: Optional[List[str]] = None, ids: Optional[List[int]] = None, target: Optional[PartialUser] = None
    ) -> List[User]:
        """|coro|

        Fetches users from twitch. You can provide any combination of up to 100 names and ids, but you must pass at least 1.

        Parameters
        -----------
        names: Optional[List[:class:`str`]]
            A list of usernames
        ids: Optional[List[Union[:class:`str`, :class:`int`]]
            A list of IDs
        target: Optional[:class:`~twitchio.PartialUser`]
            The target of this HTTP call. Passing a user will tell the library to put this call under the authorized token for that user, if one exists in your token handler

        Returns
        --------
        List[:class:`~twitchio.User`]
        """
        if not names and not ids:
            raise ValueError("No names or ids passed to fetch_users")

        data: HTTPAwaitableAsyncIterator[User] = self._http.get_users(ids=ids, logins=names, target=target)
        data.set_adapter(lambda http, data: User(http, data))

        return await data

    async def fetch_user(
        self, name: Optional[str] = None, id: Optional[int] = None, target: Optional[PartialUser] = None
    ) -> User:
        """|coro|

        Fetches a user from twitch. This is the same as :meth:`~Client.fetch_users`, but only returns one :class:`~twitchio.User`, instead of a list.
        You may only provide either name or id, not both.

        Parameters
        -----------
        name: Optional[:class:`str`]
            A username
        id: Optional[:class:`int`]
            A user ID
        target: Optional[:class:`~twitchio.PartialUser`]
            The target of this HTTP call. Passing a user will tell the library to put this call under the authorized token for that user, if one exists in your token handler

        Returns
        --------
        :class:`~twitchio.User`
        """
        if not name and not id:
            raise ValueError("Expected a name or id")

        if name and id:
            raise ValueError("Expected a name or id, got nothing")

        data: HTTPAwaitableAsyncIterator[User] = self._http.get_users(
            ids=[id] if id else None, logins=[name] if name else None, target=target
        )
        data.set_adapter(lambda http, data: User(http, data))
        resp = await data

        return resp[0]

    async def event_shard_ready(self, number: int) -> None:
        """|coro|

        Event fired when a shard becomes ready.

        Parameters
        ----------
        number: :class:`int`
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
        data: :class:`str`
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
        payload: :class:`~twitchio.IRCPayload`
            The parsed IRC payload from Twitch.

        Returns
        -------
        None
        """
        pass

    async def event_message(self, message: Message) -> None:
        """|coro|

        Event fired when receiving a message in a joined channel.

        Parameters
        ----------
        message: :class:`~twitchio.Message`
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
        channel: :class:`~twitchio.Channel`
            ...
        chatter: :class:`~twitchio.PartialChatter`
            ...
        """

    async def event_part(self, channel: Optional[Channel], chatter: PartialChatter) -> None:
        """|coro|

        Event fired when a PART is received via Twitch.

        Parameters
        ----------
        channel: Optional[:class:`~twitchio.Channel`]
            ... Could be None if the channel is not in your cache.
        chatter: :class:`~twitchio.PartialChatter`
            ...
        """

    async def setup(self) -> None:
        """|coro|

        Method called before the Client has logged in to Twitch, used for asynchronous setup.

        Useful for setting up state, like databases, before the client has logged in.

        .. versionadded:: 3.0
        """
        pass
