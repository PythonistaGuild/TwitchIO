"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

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

import datetime
import time
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .channel import Channel
    from .chatter import Chatter, PartialChatter


class Message:
    """
    Attributes
    -----------
    content: :class:`str`
        The content of this message.
    echo: :class:`bool`
        Boolean representing if this is a self-message or not.
    first: :class:`bool`
        Boolean representing whether it's a first message or not.

    """

    __slots__ = (
        "_raw_data",
        "content",
        "_author",
        "echo",
        "first",
        "_timestamp",
        "_channel",
        "_tags",
        "_id",
    )

    def __init__(self, **kwargs):
        self._raw_data = kwargs.get("raw_data")
        self.content = kwargs.get("content")
        self._author = kwargs.get("author")
        self._channel = kwargs.get("channel")
        self._tags = kwargs.get("tags")
        self.echo = kwargs.get("echo", False)

        self.first = False
        if self._tags is not None:
            first = self._tags.get("first-msg")
            if first == "1":
                self.first = True

        try:
            self._id = self._tags["id"]
            self._timestamp = self._tags["tmi-sent-ts"]
        except KeyError:
            self._id = None
            self._timestamp = datetime.datetime.now().timestamp() * 1000

    @property
    def id(self) -> str:
        """The Message ID."""
        return self._id

    @property
    def author(self) -> Union["Chatter", "PartialChatter"]:
        """The User object associated with the Message."""
        return self._author

    @property
    def channel(self) -> "Channel":
        """The Channel object associated with the Message."""
        return self._channel

    @property
    def raw_data(self) -> str:
        """The raw data received from Twitch for this Message."""
        return self._raw_data

    @property
    def tags(self) -> dict:
        """The tags associated with the Message.

        Could be None.
        """
        return self._tags

    @property
    def timestamp(self) -> datetime.datetime:
        """The Twitch timestamp for this Message.

        Returns
        ---------
        timestamp:
            UTC datetime object of the Twitch timestamp.
        """
        return datetime.datetime.utcfromtimestamp(int(self._timestamp) / 1000)
