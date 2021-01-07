# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

__all__ = ('Message', 'Channel', 'User', 'Context', 'NoticeSubscription', 'ClearChat')


import datetime
import time
from typing import *

from .abcs import Messageable
from .errors import EchoMessageWarning, HTTPException, Unauthorized


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

    async def get_custom_rewards(self, token: str, broadcaster_id: int, *, only_manageable=False, ids: List[int]=None) -> List["CustomReward"]:
        """
        Fetches the channels custom rewards (aka channel points) from the api.
        Parameters
        ----------
        token : :class:`str`
            The users oauth token.
        broadcaster_id : :class:`int`
            The id of the broadcaster.
        only_manageable : :class:`bool`
            Whether to fetch all rewards or only ones you can manage. Defaults to false.
        ids : List[:class:`int`]
            An optional list of reward ids

        Returns
        -------

        """
        try:
            data = await self._http.get_rewards(token, broadcaster_id, only_manageable, ids)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise
        else:
            return [CustomReward(self._http, x, self) for x in data['data']]


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
                self._badges[k] = v

        self._mod = int(self._tags.get('mod', 0)) if self._tags else attrs.get('mod', 0)

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
    def prediction(self) -> Optional[str]:
        """
        the chatters current prediction.

        Returns
        --------
        Optional[:class:`str`] Either blue, pink, or None
        """
        if "blue-1" in self._badges:
            return "blue"
        elif "pink-2" in self._badges:
            return "pink"

        return None

    @property
    def is_mod(self) -> bool:
        """A boolean indicating whether the User is a moderator of the current channel."""
        if self._mod == 1:
            return True
        if self.channel.name == self.name.lower():
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

class CustomReward:
    """
    Represents a Custom Reward object, as given by the api. Use :ref:`User.get_custom_rewards` to fetch these
    """
    __slots__ = "_http", "_channel", "id", "image", "background_color", "enabled", "cost", "title", "prompt", \
                "input_required", "max_per_stream", "max_per_user_stream", "cooldown", "paused", "in_stock", \
                "redemptions_skip_queue", "redemptions_current_stream", "cooldown_until", "_broadcaster_id"

    def __init__(self, http, obj: dict, channel: Channel):
        self._http = http
        self._channel = channel
        self._broadcaster_id = obj['broadcaster_id']
        
        self.id = obj['id']
        self.image = obj['image']['url_1x'] if obj['image'] else obj['default_image']['url_1x']
        self.background_color = obj['background_color']
        self.enabled = obj['is_enabled']
        self.cost = obj['cost']
        self.title = obj['title']
        self.prompt = obj['prompt']
        self.input_required = obj['is_user_input_required']
        self.max_per_stream = obj['max_per_stream_setting']['is_enabled'], obj['max_per_stream_setting']['max_per_stream']
        self.max_per_user_stream = obj['max_per_user_per_stream_setting']['is_enabled'], \
                                    obj['max_per_user_per_stream_setting']['max_per_user_per_stream']
        self.cooldown = obj['global_cooldown_setting']['is_enabled'], obj['global_cooldown_setting']['global_cooldown_seconds']
        self.paused = obj['paused']
        self.in_stock = obj['is_in_stock']
        self.redemptions_skip_queue = obj['should_redemptions_skip_request_queue']
        self.redemptions_current_stream = obj['redemptions_redeemed_current_stream']
        self.cooldown_until = obj['cooldown_expires_at']


    async def edit(
            self,
            token: str,
            title: str = None,
            prompt: str = None,
            cost: int = None,
            background_color: str = None,
            enabled: bool = None,
            input_required: bool = None,
            max_per_stream_enabled: bool = None,
            max_per_stream: int = None,
            max_per_user_per_stream_enabled: bool = None,
            max_per_user_per_stream: int = None,
            global_cooldown_enabled: bool = None,
            global_cooldown: int = None,
            paused: bool = None,
            redemptions_skip_queue: bool = None
    ):
        """
        Edits the reward. Note that apps can only modify rewards they have made.
        
        Parameters
        -----------
        token: the bearer token for the channel of the reward
        title: the new title of the reward
        prompt: the new prompt for the reward
        cost: the new cost for the reward
        background_color: the new background color for the reward
        enabled: whether the reward is enabled or not
        input_required: whether user input is required or not
        max_per_stream_enabled: whether the stream limit should be enabled
        max_per_stream: how many times this can be redeemed per stream
        max_per_user_per_stream_enabled: whether the user stream limit should be enabled
        max_per_user_per_stream: how many times a user can redeem this reward per stream
        global_cooldown_enabled: whether the global cooldown should be enabled
        global_cooldown: how many seconds the global cooldown should be
        paused: whether redemptions on this reward should be paused or not
        redemptions_skip_queue: whether redemptions skip the request queue or not

        Returns
        --------
        :class:`CustomReward` itself.
        """

        try:
            data = await self._http.update_reward(
                token,
                self._broadcaster_id,
                self._id,
                title,
                prompt,
                cost,
                background_color,
                enabled,
                input_required,
                max_per_stream_enabled,
                max_per_stream,
                max_per_user_per_stream_enabled,
                max_per_user_per_stream,
                global_cooldown_enabled,
                global_cooldown,
                paused,
                redemptions_skip_queue
            )
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise
        else:
            for reward in data['data']:
                if reward['id'] == self._id:
                    self.__init__(self._http, reward, self._channel)
                    break

        return self

    async def delete(self, token: str):
        """
        Deletes the custom reward

        Parameters
        ----------
        token: :class:`str` the oauth token of the target channel

        Returns
        --------
        None
        """
        try:
            await self._http.delete_reward(token, self._broadcaster_id, self._id)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise

    async def get_redemptions(self, token: str, status: str, sort: str = None):
        """
        Gets redemptions for this reward

        Parameters
        -----------
        token: :class:`str` the oauth token of the target channel
        status: :class:`str` one of UNFULFILLED, FULFILLED or CANCELED
        sort: :class:`str` the order redemptions are returned in. One of OLDEST, NEWEST. Default: OLDEST.
        """
        try:
            data = await self._http.get_reward_redemptions(token, self._broadcaster_id, self._id, status=status, sort=sort)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise
        else:
            return [CustomRewardRedemption(x, self._http, self) for x in data['data']]


class CustomRewardRedemption:
    __slots__ = "_http", "_broadcaster_id", "id", "user_id", "user_name", "input", "status", "redeemed_at", "reward"
    def __init__(self, obj, http, parent):
        self._http = http
        self._broadcaster_id = obj['broadcaster_id']
        self.id = obj['id']
        self.user_id = int(obj['user_id'])
        self.user_name = obj['user_name']
        self.input = obj['user_input']
        self.status = obj['status']
        self.redeemed_at = datetime.datetime.fromisoformat(obj['redeemed_at'])
        self.reward = parent or obj['reward']

    async def fulfill(self, token: str):
        """
        marks the redemption as fulfilled

        Parameters
        ----------
        token: :class:`str` the token of the target channel

        Returns
        --------
        itself.
        """
        reward_id = self.reward.id if isinstance(self.reward, CustomReward) else self.reward['id']
        try:
            data = await self._http.update_reward_redemption_status(token, self._broadcaster_id, self.id, reward_id, "FULFILLED")
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise
        else:
            self.__init__(data['data'], self._http, self.reward if isinstance(self.reward, CustomReward) else None)
            return self

    async def refund(self, token: str):
        """
        marks the redemption as cancelled

        Parameters
        ----------
        token: :class:`str` the token of the target channel

        Returns
        --------
        itself.
        """
        reward_id = self.reward.id if isinstance(self.reward, CustomReward) else self.reward['id']
        try:
            data = await self._http.update_reward_redemption_status(token, self._broadcaster_id, self.id, reward_id,
                                                                    "CANCELLED")
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException("The custom reward was created by a different application, or channel points are "
                                    "not available for the broadcaster (403)", error.args[1], 403) from error
            raise
        else:
            self.__init__(data['data'], self._http, self.reward if isinstance(self.reward, CustomReward) else None)
            return self

class ClearChat: # Add class for event_ban
    """
    The Dataclass sent to `event_ban` events.
    Attributes
    ------------
    channel : :class:`.Channel`
        The channel associated with the subscription event.
    user : :class:`.User`
        The user associated with the subscription event.
    tags : dict
        The raw tags dict associated with the subscription event.
    ban_duration : Optional[int]
        Duration of the timeout, in seconds.Could be None if the ban is permanent.
    """

    def __init__(self, *, channel: Channel, user: User, tags: dict):
        self.channel = channel
        self.user = user

        self.tags = tags

        self.ban_duration = tags.get('ban-duration', None)
        if self.ban_duration:
            self.ban_duration = int(self.ban_duration)
