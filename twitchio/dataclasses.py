# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2019 TwitchIO

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

__all__ = ('Message', 'Channel', 'User', 'Context', 'NoticeSubscription')


import datetime
import time
from typing import *

from .abcs import Messageable
from .errors import EchoMessageWarning


class Message:

    __slots__ = ('_author', '_channel', '_raw_data', 'content', 'clean_content', '_tags', '_timestamp', 'echo')

    def __init__(self, **attrs):
        self._author = attrs.pop('author', None)
        self._channel = attrs.pop('channel', None)
        self._raw_data = attrs.pop('raw_data', None)
        self.content = attrs.pop('content', None)
        self.clean_content = attrs.pop('clean_content', None)
        self._tags = attrs.pop('tags', None)
        self.echo = False

        try:
            self._timestamp = self._tags['tmi-sent-ts']
        except (TypeError, KeyError):
            self._timestamp = time.time()

    @property
    def author(self) -> 'User':  # stub
        """The User object associated with the Message."""
        return self._author

    @property
    def channel(self) -> 'Channel':  # stub
        """The Channel object associated with the Message."""
        return self._channel

    @property
    def raw_data(self) -> str:
        """The raw data received from Twitch for this Message."""
        return self._raw_data

    @property
    def tags(self) -> Optional[dict]:
        """The tags associated with the Message.

        Could be None.
        """
        return self._tags

    @property
    def timestamp(self) -> datetime.datetime.timestamp:
        """The Twitch timestamp for this Message.

        Returns
        ---------
        timestamp:
            UTC datetime object of the Twitch timestamp.
        """
        timestamp = datetime.datetime.utcfromtimestamp(int(self._timestamp) / 1000)
        return timestamp


class Channel(Messageable):

    __slots__ = ('_channel', '_ws', '_http', '_echo', '_users')

    def __init__(self, name, ws, http):
        self._channel = name
        self._http = http
        self._ws = ws
        self._echo = False
        self._users = {}

    def __str__(self):
        return self._channel

    @property
    def name(self) -> str:
        """The channel name."""
        return self._channel

    @property
    def chatters(self) -> list:
        """The channel's chatters."""
        return list(self._users.values())

    def _get_channel(self) -> Tuple[str, None]:
        return self.name, None

    def _get_method(self) -> str:
        return self.__class__.__name__

    @property
    def _get_socket(self):  # stub
        if self._echo is True:
            raise EchoMessageWarning('Unable to respond to Echo-Messages.')

        return self._ws

    async def get_stream(self) -> dict:
        """|coro|

        Method which retrieves stream information on the channel, provided it is active (Live).

        Returns
        ---------
        dict:
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        HTTPException
            Bad request while fetching streams.
        """

        data = await self._http.get_streams(channels=[self.name])

        try:
            return data[0]
        except IndexError:
            pass


class User:

    __slots__ = ('_name', '_channel', '_tags', 'display_name', '_id', 'type',
                 '_colour', 'subscriber', 'turbo', '_badges', '_ws', '_mod')

    def __init__(self, ws, **attrs):
        self._name = attrs.pop('author', None)
        self._channel = attrs.pop('channel', self._name)
        self._tags = attrs.pop('tags', None)
        self._ws = ws

        if not self._tags:
            self._tags = {}

        self.display_name = self._tags.get('display-name', self._name)
        self._id = int(self._tags.get('user-id', 0))
        self.type = self._tags.get('user-type', 'Empty')
        self._colour = self._tags.get('color', None)
        self.subscriber = self._tags.get('subscriber', None)
        self.turbo = self._tags.get('turbo', None)

        self._badges = {}
        badges = self._tags.get('badges', None)
        if badges:
            for chunk in badges.split(','):
                k, _, v = chunk.partition('/')
                self._badges[k] = int(v)

        self._mod = self._tags.get('mod', 0) if self._tags else attrs.get('mod', 0)

    def __repr__(self):
        return '<User name={0.name} channel={0._channel}>'.format(self)

    def __eq__(self, other):
        return other == self.name

    def __hash__(self):
        return hash(self.name)

    @property
    def name(self) -> str:
        """The user's name."""
        return self._name

    @property
    def id(self) -> int:
        """The user's ID.

         Could be 0 if no Tags were received."""
        return self._id

    @property
    def channel(self) -> Channel:
        """The channel object associated with the User.

        .. note::

            The channel will be valid for the data which triggered the Event. It is possible the
            user could be in multiple channels. E.g: The User BobRoss sends a message from the Channel ArtIsCool.
            The Channel object received will be ArtIsCool.
        """
        return self._channel

    @property
    def colour(self) -> Optional[str]:
        """The user's colour.

        Could be None if no Tags were received.
        """
        return self._colour

    @property
    def color(self) -> Optional[str]:
        """An American-English alias to colour."""
        return self.colour

    @property
    def is_turbo(self) -> bool:
        """A boolean indicating whether the User is Turbo.

        Could be None if no Tags were received.
        """
        return self.turbo

    @property
    def is_subscriber(self) -> bool:
        """A boolean indicating whether the User is a subscriber of the current channel.

        Could be None if no Tags were received.
        """
        return self.subscriber

    @property
    def badges(self) -> dict:
        """The badges associated with the User.

        Could be an empty Dict if no Tags were received.
        """
        return self._badges

    @property
    def tags(self) -> dict:
        """The Tags received for the User.

        Could be an empty Dict if no tags were received.
        """
        return self._tags

    @property
    def is_mod(self) -> bool:
        """A boolean indicating whether the User is a moderator of the current channel."""
        if self._mod == 1:
            return True
        if self.channel.name == self.display_name.lower():
            return True
        else:
            return False


class Context(Messageable):
    """
    The context of which a command is invoked under.

    Attributes
    ------------
    author : :class:`.User`
        The author of the command.
    prefix : str
        The prefix associated with the command.
    message : :class:`.Message`
        The message associated with the command.
    channel : :class:`.Channel`
        The channel associated with the command.
    command : :class:`twitchio.ext.core.Command`
        The command which was invoked.


    .. note::
        Context is only available through the commands extension.
    """

    def __init__(self, message: Message, channel: Channel, user: User, **attrs):
        self.message = message
        self.channel = channel
        self.content = message.content
        self.author = user
        self.prefix = attrs.get('prefix', None)

        self._echo = self.channel._echo
        self._ws = self.channel._ws

        self.command = attrs.get('Command', None)
        self.args = attrs.get('args', None)
        self.kwargs = attrs.get('kwargs', None)

    def _get_channel(self) -> Tuple[str, None]:
        return self.channel.name, None

    def _get_method(self) -> str:
        return self.__class__.__name__

    @property
    def _get_socket(self):  # stub
        if self._echo is True:
            raise EchoMessageWarning('Unable to respond to Echo-Messages.')

        return self._ws

    async def get_stream(self) -> dict:
        """|coro|

        Method which retrieves stream information on the channel stored in Context, provided it is active (Live
        Returns
        ---------
        dict
            Dict containing active streamer data. Could be None if the stream is not live.

        Raises
        --------
        HTTPException
            Bad request while fetching streams.
        """
        return await self.channel.get_stream()


class NoticeSubscription:
    """
    The Dataclass sent to `event_usernotice_subscription` events.

    Attributes
    ------------
    channel : :class:`.Channel`
        The channel associated with the subscription event.
    user : :class:`.User`
        The user associated with the subscription event.
    tags : dict
        The raw tags dict associated with the subscription event.
    cumulative_months : Optional[int]
        The total number of months the user has subscribed. Could be None if not provided.
    share_streak : bool
        Boolean indicating whether users want their streaks to be shared.
    streak_months : Optional[int]
        The number of consecutive months the user has subscribed. Could be None if not provided.
        This is 0 if ``share_streak`` is False.
    sub_plan : str
        The type of subscription plan being used.
        Valid values: Prime, 1000, 2000, 3000.

        1000, 2000, and 3000 refer to the first, second, and third levels of paid subscriptions,
        respectively (currently $4.99, $9.99, and $24.99).
    sub_plan_name : str
        The display name of the subscription plan.
        This may be a default name or one created by the channel owner.
    """

    def __init__(self, *, channel: Channel, user: User, tags: dict):
        self.channel = channel
        self.user = user

        self.tags = tags

        self.cumulative_months = tags.get('msg-param-cumulative-months', None)
        if self.cumulative_months:
            self.cumulative_months = int(self.cumulative_months)

        self.share_streak = bool(tags['msg-param-should-share-streak'])

        self.streak_months = tags.get('msg-param-streak-months', None)
        if self.streak_months:
            self.streak_months = int(self.streak_months)

        self.sub_plan = tags['msg-param-sub-plan']
        self.sub_plan_name = tags['msg-param-sub-plan-name']
