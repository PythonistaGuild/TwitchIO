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

from .channel import Channel
from .parser import IRCPayload
from .chatter import PartialChatter


class Message:
    """TwitchIO Message object representing a messages received via Twitch.

    Attributes
    ----------
    content: str
        The message content.
    channel: :class:`Channel`
        The channel the message was sent from.
    author: :class:`PartialChatter`
        The chatter that sent the message.
    echo: bool
        Bool indicating whether the message is a message sent from the bot or not. True indicates the message
        was sent from the bot.
    raw: str
        The raw message string received via Twitch.
    """

    __slots__ = (
        '_tags',
        '_id',
        'content',
        'channel',
        'author',
        '_badges',
        'echo',
        'raw',
        'timestamp'
    )

    def __init__(self,
                 payload: IRCPayload,
                 *,
                 channel: Channel,
                 chatter: PartialChatter,
                 echo: bool = False
                 ):
        self._tags = payload.tags
        self._badges: dict = payload.badges

        self._id: str = self._tags.get('id')
        self.content: str = payload.message
        self.channel: Channel = channel
        self.author: PartialChatter = chatter

        self.echo: bool = echo
        self.raw: str = payload.raw

        self.timestamp = ...

    def __repr__(self):
        return f'Message: ' \
               f'id={self.id}, ' \
               f'author=<{self.author}>, ' \
               f'channel=<{self.channel}>, ' \
               f'echo={self.echo}, ' \
               f'timestamp={self.timestamp}'

    def __str__(self):
        return self.content

    def __eq__(self, other):
        return self.id == other.id

    @property
    def id(self) -> str:
        """The message ID."""
        return self._id

    @property
    def tags(self) -> dict:
        """The tags associated with the message."""
        return self._tags

    @property
    def badges(self) -> dict:
        """The badges associated with the message."""
        return self._badges
