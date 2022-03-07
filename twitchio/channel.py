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
import copy
from typing import Dict, Optional

from .abc import Messageable
from .cache import Cache
from .user import PartialUser


class Channel(Messageable):

    __slots__ = (
        '_name',
        '_id',
        '_websocket',
        '_users'
                 )

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self._id = attrs.get('id')
        self._users = Cache()

    def __repr__(self) -> str:
        return f'Channel: name={self._name}, shard_index={self._websocket.shard_index}'

    async def send(self, content: str) -> None:
        await self._websocket.send(f"PRIVMSG #{self._name} :{content}")

    @property
    def name(self) -> str:
        """The channel name."""
        return self._name

    @property
    def id(self) -> int:
        """The channel ID."""
        return int(self._id)

    @property
    def owner(self) -> Optional[PartialUser]:
        """The channel owner."""
        return self._users.get(self._name, default=None)

    @property
    def users(self) -> Dict[str, PartialUser]:
        """A mapping of the channel's user cache."""
        return copy.copy(self._users.items())

    def get_user(self, name: str) -> Optional[PartialUser]:
        """Method which returns a user from the channel's cache.

        Could be None if the user is not in cache.
        """
        name = name.removeprefix('#').lower()

        return self._users.get(name, default=None)
