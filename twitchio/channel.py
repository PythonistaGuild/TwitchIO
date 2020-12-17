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

from typing import Optional
from .abcs import Messageable


class Channel(Messageable):

    __slots__ = ('_name', '_ws')

    __messageable_channel__ = True

    def __init__(self, **kwargs):
        self._name = kwargs.get('name')
        self._ws = kwargs.get('websocket')

    def __eq__(self, other):
        return other.name == self._name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f'<Channel name: {self.name}>'

    def _fetch_channel(self):
        return self   # Abstract method

    def _fetch_websocket(self):
        return self._ws     # Abstract method

    def _bot_is_mod(self):
        cache = self._ws._cache[self.name]
        for user in cache:
            if user.name == self._ws.nick:
                try:
                    mod = user.is_mod
                except AttributeError:
                    return False

                return mod

    @property
    def name(self) -> str:
        """The channel name."""
        return self._name

    @property
    def chatters(self) -> Optional[set]:
        """The channels current chatters."""
        try:
            users = self._ws._cache[self._name]
        except KeyError:
            return None

        return users

    @property
    def users(self) -> Optional[set]:   # Alias to chatters
        """Alias to chatters."""
        return self.chatters

    def get_user(self, name: str):
        """Retrieve a user from the channels user cache.

        Parameters
        -----------
        name: str
            The user's name to try and retrieve.

        Returns
        --------
        Union[:class:`twitchio.user.User`, :class:`twitchio.user.PartialUser`]
            Could be a :class:`twitchio.user.PartialUser` depending on how the user joined the channel.
            Returns None if no user was found.
        """
        name = name.lower()

        cache = self._ws._cache[self._name]
        for user in cache:
            if user.name == name:
                return user

        return None
