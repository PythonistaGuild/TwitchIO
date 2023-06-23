# -*- coding: utf-8 -*-

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
from typing import Optional, TYPE_CHECKING

from .errors import HTTPException, Unauthorized
from .utils import parse_timestamp

if TYPE_CHECKING:
    from .http import TwitchHTTP
    from .user import PartialUser
__all__ = "CustomReward", "CustomRewardRedemption"


class CustomReward:
    """
    Represents a Custom Reward object, as given by the api. Use :func:`~twitchio.PartialUser.get_custom_rewards` to fetch these

    Attributes
    -----------
    id: :class:`str`
        The id of the custom reward
    title: :class:`str`
        The title of the custom reward
    image: :class:`str`
        The url of the image of the custom reward
    background_color: :class:`str`
        The background color of the custom reward
    enabled: :class:`bool`
        Whether the custom reward is enabled
    cost: :class:`int`
        The cost of the custom reward
    prompt: :class:`str`
        The prompt of the custom reward
    input_required: :class:`bool`
        Whether the custom reward requires input
    max_per_stream: Tuple[:class:`bool`, :class:`int`]
        Whether the custom reward is limited to a certain amount per stream, and how many
    max_per_user_stream: Tuple[:class:`bool`, :class:`int`]
        Whether the custom reward is limited to a certain amount per user per stream, and how many
    cooldown: Tuple[:class:`bool`, :class:`int`]
        Whether the custom reward has a cooldown, and how long it is
    paused: :class:`bool`
        Whether the custom reward is paused
    in_stock: :class:`bool`
        Whether the custom reward is in stock
    redemptions_skip_queue: :class:`bool`
        Whether the custom reward's redemptions skip the request queue
    redemptions_current_stream: :class:`bool`
        Whether the custom reward's redemptions are only valid for the current stream
    cooldown_until: :class:`datetime.datetime`
        The datetime the custom reward's cooldown will expire
    """

    __slots__ = (
        "_http",
        "_channel",
        "id",
        "image",
        "background_color",
        "enabled",
        "cost",
        "title",
        "prompt",
        "input_required",
        "max_per_stream",
        "max_per_user_stream",
        "cooldown",
        "paused",
        "in_stock",
        "redemptions_skip_queue",
        "redemptions_current_stream",
        "cooldown_until",
        "_broadcaster_id",
    )

    def __init__(self, http: "TwitchHTTP", obj: dict, channel: "PartialUser"):
        self._http = http
        self._channel = channel

        try:
            self._broadcaster_id = obj["broadcaster_id"]
        except KeyError:
            self._broadcaster_id = obj["channel_id"]
        self.id = obj["id"]
        self.image = obj["image"]["url_1x"] if obj["image"] else obj["default_image"]["url_1x"]
        self.background_color = obj["background_color"]
        self.enabled = obj["is_enabled"]
        self.cost = obj["cost"]
        self.title = obj["title"]
        self.prompt = obj["prompt"]
        self.input_required = obj["is_user_input_required"]

        try:
            self.max_per_stream = (
                obj["max_per_stream_setting"]["is_enabled"],
                obj["max_per_stream_setting"]["max_per_stream"],
            )
            self.max_per_user_stream = (
                obj["max_per_user_per_stream_setting"]["is_enabled"],
                obj["max_per_user_per_stream_setting"]["max_per_user_per_stream"],
            )
            self.cooldown = (
                obj["global_cooldown_setting"]["is_enabled"],
                obj["global_cooldown_setting"]["global_cooldown_seconds"],
            )
        except KeyError:
            self.max_per_stream = (obj["max_per_stream"]["is_enabled"], obj["max_per_stream"]["max_per_stream"])
            self.max_per_user_stream = (
                obj["max_per_user_per_stream"]["is_enabled"],
                obj["max_per_user_per_stream"]["max_per_user_per_stream"],
            )
            self.cooldown = (
                obj["global_cooldown"]["is_enabled"],
                obj["global_cooldown"]["global_cooldown_seconds"],
            )
        self.paused = obj["is_paused"]
        self.in_stock = obj["is_in_stock"]
        self.redemptions_skip_queue = obj["should_redemptions_skip_request_queue"]
        self.redemptions_current_stream = obj["redemptions_redeemed_current_stream"]
        self.cooldown_until = obj["cooldown_expires_at"]

    async def edit(
        self,
        token: str,
        title: Optional[str] = None,
        prompt: Optional[str] = None,
        cost: Optional[int] = None,
        background_color: Optional[str] = None,
        enabled: Optional[bool] = None,
        input_required: Optional[bool] = None,
        max_per_stream_enabled: Optional[bool] = None,
        max_per_stream: Optional[int] = None,
        max_per_user_per_stream_enabled: Optional[bool] = None,
        max_per_user_per_stream: Optional[int] = None,
        global_cooldown_enabled: Optional[bool] = None,
        global_cooldown: Optional[int] = None,
        paused: Optional[bool] = None,
        redemptions_skip_queue: Optional[bool] = None,
    ):
        """
        Edits the reward. Note that apps can only modify rewards they have made.

        Parameters
        -----------
        token: :class:`str`
            The bearer token for the channel of the reward
        title: Optional[:class:`str`]
            The new title of the reward
        prompt: Optional[:class:`str`]
            The new prompt for the reward
        cost: Optional[:class:`int`]
            The new cost for the reward
        background_color: Optional[:class:`str`]
            The new background color for the reward
        enabled: Optional[:class:`bool`]
            Whether the reward is enabled or not
        input_required: Optional[:class:`bool`]
            Whether user input is required or not
        max_per_stream_enabled: Optional[:class:`bool`]
            Whether the stream limit should be enabled
        max_per_stream: Optional[:class:`int`]
            How many times this can be redeemed per stream
        max_per_user_per_stream_enabled: Optional[:class:`bool`]
            Whether the user stream limit should be enabled
        max_per_user_per_stream: Optional[:class:`int`]
            How many times a user can redeem this reward per stream
        global_cooldown_enabled: Optional[:class:`bool`]
            Whether the global cooldown should be enabled
        global_cooldown: Optional[:class:`int`]
            How many seconds the global cooldown should be
        paused: Optional[:class:`bool`]
            Whether redemptions on this reward should be paused or not
        redemptions_skip_queue: Optional[:class:`bool`]
            Whether redemptions skip the request queue or not

        Returns
        --------
        :class:`CustomReward` itself.
        """

        try:
            data = await self._http.update_reward(
                token,
                self._broadcaster_id,
                self.id,
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
                redemptions_skip_queue,
            )
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise
        else:
            for reward in data:
                if reward["id"] == self.id:
                    self.__init__(self._http, reward, self._channel)
                    break
        return self

    async def delete(self, token: str):
        """
        Deletes the custom reward

        Parameters
        ----------
        token:
            :class:`str` the oauth token of the target channel

        Returns
        --------
        None
        """
        try:
            await self._http.delete_custom_reward(token, self._broadcaster_id, self.id)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise

    async def get_redemptions(self, token: str, status: str, sort: str = "OLDEST", first: int = 20):
        """
        Gets redemptions for this reward

        Parameters
        -----------
        token:
            :class:`str` the oauth token of the target channel
        status:
            :class:`str` one of UNFULFILLED, FULFILLED or CANCELED
        sort:
            Optional[:class:`str`] the order redemptions are returned in. One of OLDEST, NEWEST. Default: OLDEST.
        first:
            :class:`int` Number of results to be returned when getting the paginated Custom Reward Redemption objects for a reward.
            Limit: 50. Default: 20.
        """
        try:
            data = await self._http.get_reward_redemptions(
                token, self._broadcaster_id, self.id, status=status, sort=sort, first=first
            )
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise
        else:
            return [CustomRewardRedemption(x, self._http, self) for x in data]

    def __repr__(self):
        return f"<CustomReward id={self.id} title={self.title} cost={self.cost}>"


class CustomRewardRedemption:
    __slots__ = "_http", "_broadcaster_id", "id", "user_id", "user_name", "input", "status", "redeemed_at", "reward"

    def __init__(self, obj: dict, http: "TwitchHTTP", parent: Optional[CustomReward]):
        self._http = http
        self._broadcaster_id = obj["broadcaster_id"]
        self.id = obj["id"]
        self.user_id = int(obj["user_id"])
        self.user_name = obj["user_name"]
        self.input = obj["user_input"]
        self.status = obj["status"]
        self.redeemed_at = parse_timestamp(obj["redeemed_at"])
        self.reward = parent or obj["reward"]

    def __repr__(self):
        return f"<CustomRewardRedemption id={self.id} user_id={self.user_id} user_name={self.user_name} input={self.input} status={self.status} redeemed_at={self.redeemed_at}>"

    async def fulfill(self, token: str):
        """
        marks the redemption as fulfilled

        Parameters
        ----------
        token:
            :class:`str` the token of the target channel

        Returns
        --------
        itself.
        """
        reward_id = self.reward.id if isinstance(self.reward, CustomReward) else self.reward["id"]
        try:
            data = await self._http.update_reward_redemption_status(
                token, self._broadcaster_id, self.id, reward_id, True
            )
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise
        else:
            self.__init__(data[0], self._http, self.reward if isinstance(self.reward, CustomReward) else None)
            return self

    async def refund(self, token: str):
        """
        marks the redemption as cancelled

        Parameters
        ----------
        token:
            :class:`str` the token of the target channel

        Returns
        --------
        itself.
        """
        reward_id = self.reward.id if isinstance(self.reward, CustomReward) else self.reward["id"]
        try:
            data = await self._http.update_reward_redemption_status(
                token, self._broadcaster_id, self.id, reward_id, False
            )
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise
        else:
            self.__init__(data[0], self._http, self.reward if isinstance(self.reward, CustomReward) else None)
            return self
