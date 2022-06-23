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
from typing import Optional, cast

from .parser import IRCPayload

__all__ = ("PartialChatter",)


class PartialChatter:

    __slots__ = ("_name", "_colour", "_display_name", "_mod", "_turbo", "_id", "tags", "badges")

    def __init__(
        self,
        payload: IRCPayload,
    ):
        self._name = payload.user

        tags = payload.tags
        badges = payload.badges

        if tags:
            self._colour = tags.get("color")
            self._display_name = tags.get("display-name")
            self._mod = tags.get("mod")
            self._turbo = tags.get("turbo")
            self._id = tags.get("user-id")

        self.tags = tags
        self.badges = badges

    def __repr__(self):
        return f"PartialUser: id={self._id}, name={self._name}"

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.id == other.id

    def __gt__(self, other):
        # TODO
        ...

    def __lt__(self, other):
        # TODO
        ...

    @property
    def id(self) -> int:
        """The users ID."""
        return int(cast(int, self._id))

    @property
    def name(self) -> Optional[str]:
        """The users name."""
        return self._name

    @property
    def colour(self) -> Optional[str]:
        """The users colour."""
        if self._colour:
            return hex(self._colour.removeprefix("#"))

    color = colour

    @property
    def display_name(self) -> Optional[str]:
        """The users display name."""
        return self._display_name

    @property
    def is_mod(self) -> bool:
        """Whether the user is mod of this channel."""
        return True  # TODO
