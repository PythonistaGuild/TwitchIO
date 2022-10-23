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
import copy
from typing import Dict, Optional

from .abc import Messageable
from .cache import Cache
from .chatter import PartialChatter

__all__ = ("Channel",)


class Channel(Messageable):

    __slots__ = ("_name", "_id", "_websocket", "_chatters")

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self._id: Optional[int] = attrs.get("id")
        self._chatters: Cache = Cache()

    def __repr__(self) -> str:
        return f"Channel: name={self._name}, shard_index={self._websocket.shard_index}"

    async def send(self, content: str) -> None:
        """|coro|
        Sends a whisper message to the channel's user.

        Parameters
        -----------
        content: :class:`str`
            The content to send to the user
        """
        await self._websocket.send(f"PRIVMSG #{self._name} :{content}")

    @property
    def name(self) -> str:
        """
        The channel name.

        Returns
        --------
        :class:`str`
        """
        return self._name

    @property
    def id(self) -> Optional[int]:
        """
        The channel ID.

        Returns
        --------
        Optional[:class:`int`]
        """
        return self._id and int(self._id)

    @property
    def owner(self) -> Optional[PartialChatter]:
        """
        The channel owner.

        Returns
        --------
        Optional[:class:`~twitchio.PartialChatter`]
        """
        return self._chatters.get(self._name, default=None)

    @property
    def chatters(self) -> dict[str, PartialChatter]:
        """
        A mapping of the channel's chatter cache.

        Returns
        --------
        Dict[:class:`str`, :class:`~twitchio.PartialChatter`]
        """
        return copy.copy(self._chatters.nodes)

    def get_chatter(self, name: str) -> Optional[PartialChatter]:
        """Method which returns a chatter from the channel's cache.

        Could be ``None`` if the chatter is not in cache.

        Parameters
        -----------
        name: :class:`str`
            The name of the chatter to find

        Returns
        --------
        Optional[:class:`~twitchio.PartialChatter`]
        """
        name = name.lstrip("#").lower()

        return self._chatters.get(name, default=None)
