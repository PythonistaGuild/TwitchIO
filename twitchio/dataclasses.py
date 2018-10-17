# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2018 TwitchIO

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

from .abcs import Messageable


class Message:

    __slots__ = ('_author', '_channel', '_raw_data', 'content', 'clean_content', '_tags', '_timestamp')

    def __init__(self, **attrs):
        self._author = attrs.pop('author', None)
        self._channel = attrs.pop('channel', None)
        self._raw_data = attrs.pop('raw_data', None)
        self.content = attrs.pop('content', None)
        self.clean_content = attrs.pop('clean_content', None)
        self._tags = attrs.pop('tags', None)

        if self._tags:
            try:
                self._timestamp = self.tags['sent-ts']
            except KeyError:
                self._timestamp = self.tags['tmi-sent-ts']

    @property
    def author(self):
        """The User object associated with the Message."""
        return self._author

    @property
    def channel(self):
        """The Channel object associated with the Message."""
        return self._channel

    @property
    def raw_data(self):
        """The raw data received from Twitch for this Message."""
        return self._raw_data

    @property
    def tags(self):
        """The tags associated with the Message.

        Could be None.
        """
        return self._tags

    @property
    def timestamp(self):
        """The Twitch timestamp for this Message.

        Returns
        ---------
        timestamp:
            UTC datetime object of the Twitch timestamp.
        """
        timestamp = datetime.datetime.utcfromtimestamp(self._timestamp/1000)
        return timestamp


class Channel(Messageable):

    __slots__ = ('_channel', '_ws', '_http', )

    def __init__(self, name, ws, http):
        self._channel = name
        self._http = http
        self._ws = ws

    def __str__(self):
        return self._channel

    @property
    def name(self):
        """The channel name."""
        return self._channel

    def _get_channel(self):
        return self.name, None

    def _get_method(self):
        return self.__class__.__name__

    @property
    def _get_socket(self):
        return self._ws

    async def get_stream(self):
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Returns
        ---------
        dict:
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching streams.
        """

        data = await self._http.get_streams(channels=[self.name])
        return data[0]

    async def get_chatters(self):
        """|coro|

        Method which retrieves the currently active chatters on the given stream.

        Returns
        ---------
        namedtuple:
            A namedtuple containing chatter data.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream chatters.
        """

        return await self._http.get_chatters(self.name)


class User:

    __slots__ = ('_name', '_channel', '_tags', 'display_name', '_id', 'type',
                 '_colour', 'subscriber', 'turbo', '_badges', '_ws', '_mod')

    def __init__(self, ws, **attrs):
        self._name = attrs.pop('author', None)
        self._channel = attrs.pop('channel', self._name)
        self._tags = attrs.pop('tags', None)
        self._ws = ws

        if not self._tags:
            self._tags = {'None': 'None'}

        self.display_name = self._tags.get('display-name', self._name)
        self._id = int(self._tags.get('user-id', 0))
        self.type = self._tags.get('user-type', 'Empty')
        self._colour = self._tags.get('color', None)
        self.subscriber = self._tags.get('subscriber', None)
        self.turbo = self._tags.get('turbo', None)
        self._badges = self._tags.get('badges', ',').split(',')
        self._mod = self._tags.get('mod', 0) if self._tags else attrs.get('mod', 0)

    def __repr__(self):
        return '<User name={0.name} channel={0._channel}>'.format(self)

    @property
    def name(self):
        """The user's name."""
        return self._name

    @property
    def id(self):
        """The user's ID.

         Could be None if no Tags were received."""
        return self._id

    @property
    def channel(self):
        """The channel object associated with the User.

        .. note::

            The channel will be valid for the data which triggered the Event. It is possible the
            user could be in multiple channels. E.g: The User BobRoss sends a message from the Channel ArtIsCool.
            The Channel object received will be ArtIsCool.
        """
        return self._channel

    @property
    def colour(self):
        """The user's colour.

        Could be None if no Tags were received.
        """
        return self._colour

    @property
    def color(self):
        """An American-English alias to colour."""
        return self.colour

    @property
    def is_turbo(self):
        """A boolean indicating whether the User is Turbo.

        Could be None if no Tags were received.
        """
        return self.turbo

    @property
    def is_subscriber(self):
        """A boolean indicating whether the User is a subscriber of the current channel.

        Could be None if no Tags were received.
        """
        return self.subscriber

    @property
    def badges(self):
        """The badges associated with the User.

        Could be None if no Tags were received.
        """
        return self._badges

    @property
    def tags(self):
        """The Tags received for the User.

        Could be a Dict containing None if no tags were received.
        """
        return self._tags

    @property
    def is_mod(self):
        """A boolean indicating whether the User is a moderator of the current channel.

        Could be None if no Tags were received.
        """
        if self._mod == 1:
            return True
        if self.channel.name == self.display_name.lower():
            return True
        else:
            return False


class Context(Messageable):
    """
    :ivar author: The author of the command.
    :ivar prefix: The prefix associated with the command.
    :ivar message: The message associated with the command.
    :ivar channel: The channel associated with the command.
    :ivar command: The command which was invoked.

    .. note::
        Context is only available through the commands extension.
    """

    def __init__(self, message: Message, channel: Channel, user: User, **attrs):
        self.message = message
        self.channel = channel
        self.content = message.content
        self.author = user
        self.prefix = attrs.get('prefix', None)

        self._ws = self.channel._ws

        self.command = attrs.get('Command', None)
        self.args = attrs.get('args', None)
        self.kwargs = attrs.get('kwargs', None)

    def _get_channel(self):
        return self.channel.name, None

    def _get_method(self):
        return self.__class__.__name__

    @property
    def _get_socket(self):
        return self._ws

    async def get_stream(self):
        """|coro|

        Method which retrieves stream information on the channel stored in Context, provided it is active (Live).

        Returns
        ---------
        dict
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching streams.
        """
        return await self.channel.get_stream()

    async def get_chatters(self):
        """|coro|

        Method which retrieves the currently active chatters on the given stream.

        Returns
        ---------
        dict
            Dict containing active chatter data.

        Raises
        --------
        TwitchHTTPException
            Bad request while fetching stream chatters.
        """
        return await self.channel.get_chatters()
