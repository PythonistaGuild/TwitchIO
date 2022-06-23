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
from __future__ import annotations
import datetime
from typing import Literal, Optional, TYPE_CHECKING, Tuple, Union
from typing_extensions import Self

from twitchio.http import HTTPAwaitableAsyncIterator

from .exceptions import HTTPException, HTTPResponseException, Unauthorized
from .utils import parse_timestamp

if TYPE_CHECKING:
    from .http import HTTPHandler
    from .models import PartialUser


__all__ = "CustomReward", "CustomRewardRedemption"

class PartialCustomReward:
    """
    Represents a partial Custom Reward object. These are used to fill in for full CustomReward objects in places where the API doesn't provide
    full Reward objects, such as the ``reward`` slot of Custom Reward Redemptions.

    To perform any HTTP requests (such as :func:`CustomReward.edit`, :func:`CustomReward.delete` or :func:`CustomReward.get_redemptions`),
    use :func:`~twitchio.PartialUser.get_custom_rewards` to fetch a :class:`CustomReward` object

    Attributes
    -----------
    id: :class:`str`
        The ID of the reward
    title: :class:`str`
        The title of the reward
    prompt: :class:`str`
        The prompt of the reward
    cost: :class:`int`
        How much the reward costed to redeem
    """
    
    __slots__ = ("id", "title", "prompt", "cost")

    def __init__(self, obj: dict) -> None:
        self.id: str = obj["id"]
        self.title: str = obj["title"]
        self.prompt: str = obj["prompt"]
        self.cost: int = obj["cost"]


class CustomReward:
    """
    Represents a Custom Reward object, as given by the api. Use :func:`~twitchio.PartialUser.get_custom_rewards` to fetch these

    Attributes
    -----------
    id: class:`str`
        The ID of the Custom Reward
    image: :class:`str`
        The image of the Custom Reward. If none has been uploaded, this defaults to the default image provided
    background_color: :class:`str`
        The background colour of the reward. This is a hex with a # prefix
    enabled: :class:`bool
        Whether or not this reward is enabled
    cost: :class:`int`
        How much this reward costs to use
    title: :class:`str`
        The title of this reward
    prompt: :class:`str`
        The prompt the user sees when redeeming this reward
    input_required: :class:`str`
        Whether this reward accepts input or not
    max_per_stream: Tuple[:class:`bool`, :class:`int`]
        A tuple that indicates whether there is a maximum enabled (index 0) and what the maximum is, if enabled (index 1)
    max_per_user_stream: Tuple[:class:`bool`, :class:`int`]
        A tuple that indicates whether there is a per user maximum enabled (index 0) and what the maximum is, if enabled (index 1)
    paused: :class`bool`
        When True, users cannot redeem this reward
    in_stock: :class:`bool`
        Is the reward currently in stock? If False, users cannot redeem this reward
    redemptions_skip_queue: :class:`bool
        Should redemptions be set to FULFILLED status immediately when redeemed and skip the request queue instead of the normal UNFULFILLED status
    redemptions_current_stream: Optional[:class:`int`]
        How many times this reward has been redeemed in the current stream. Will be ``None`` if the stream is not live or max_per_stream is disabled
    cooldown_until: Optional[:class:`datetime.datetime`]
        If not ``None``, a timestamp that indicates when the cooldown for this reward ends
    """

    __slots__ = (
        "_http",
        "_user",
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

    def __init__(self, http: HTTPHandler, obj: dict, user: PartialUser) -> None:
        self._http: HTTPHandler = http
        self._user: PartialUser = user

        try:
            self._broadcaster_id = obj["broadcaster_id"]
        except KeyError:
            self._broadcaster_id = obj["channel_id"]

        self.id: str = obj["id"]
        self.image: str = obj["image"]["url_1x"] if obj["image"] else obj["default_image"]["url_1x"]
        self.background_color: str = obj["background_color"]
        self.enabled: bool = obj["is_enabled"]
        self.cost: int = obj["cost"]
        self.title: str = obj["title"]
        self.prompt: str = obj["prompt"]
        self.input_required: bool = obj["is_user_input_required"]

        self.max_per_stream: Tuple[bool, int] = (
            obj["max_per_stream_setting"]["is_enabled"],
            obj["max_per_stream_setting"]["max_per_stream"],
        )
        self.max_per_user_stream: Tuple[bool, int] = (
            obj["max_per_user_per_stream_setting"]["is_enabled"],
            obj["max_per_user_per_stream_setting"]["max_per_user_per_stream"],
        )
        self.cooldown: Tuple[bool, int] = (
            obj["global_cooldown_setting"]["is_enabled"],
            obj["global_cooldown_setting"]["global_cooldown_seconds"],
        )
        self.paused: bool = obj["is_paused"]
        self.in_stock: bool = obj["is_in_stock"]
        self.redemptions_skip_queue: bool = obj["should_redemptions_skip_request_queue"]
        self.redemptions_current_stream: Optional[int] = obj["redemptions_redeemed_current_stream"]
        self.cooldown_until: Optional[datetime.datetime] = obj["cooldown_expires_at"] and parse_timestamp(obj["cooldown_expires_at"])

    async def edit(
        self,
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
    ) -> Self:
        """
        Edits the reward. Note that apps can only modify rewards they have made.

        Parameters
        -----------
        title: Optional[:class:`str`]
            the new title of the reward
        prompt: Optional[:class:`str`]
            the new prompt for the reward
        cost: Optional[:class:`int`]
            the new cost for the reward
        background_color: Optional[:class:`str`]
            the new background color for the reward
        enabled: Optional[:class:`bool`]
            whether the reward is enabled or not
        input_required: Optional[:class:`bool`]
            whether user input is required or not
        max_per_stream_enabled: Optional[:class:`bool`]
            whether the stream limit should be enabled
        max_per_stream: Optional[:class:`int`]
            how many times this can be redeemed per stream
        max_per_user_per_stream_enabled: Optional[:class:`bool`]
            whether the user stream limit should be enabled
        max_per_user_per_stream: Optional[:class:`int`]
            how many times a user can redeem this reward per stream
        global_cooldown_enabled: Optional[:class:`bool`]
            whether the global cooldown should be enabled
        global_cooldown: Optional[:class:`int`]
            how many seconds the global cooldown should be
        paused: Optional[:class:`bool`]
            whether redemptions on this reward should be paused or not
        redemptions_skip_queue: Optional[:class:`bool`]
            whether redemptions skip the request queue or not

        Returns
        --------
        :class:`CustomReward` itself.
        """

        try:
            data = await self._http.update_reward(
                self._user,
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
        except HTTPResponseException as error:
            status = error.status
            if status == 403:
                raise HTTPResponseException(
                    error._response,
                    await error._response.json(),
                    message="The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)"
                ) from error
            raise
        else:
            for reward in data["data"]:
                if reward["id"] == self.id:
                    self.__init__(self._http, reward, self._user)
                    break

        return self

    async def delete(self) -> None:
        """
        Deletes the custom reward

        Returns
        --------
        None
        """
        try:
            await self._http.delete_custom_reward(self._user, self._broadcaster_id, self.id)
        except Unauthorized as error:
            raise Unauthorized(error._response, await error._response.json(), message=f"The token for {self._user} is invalid") from error
        except HTTPResponseException as error:
            raise HTTPResponseException(
                    error._response,
                    await error._response.json(),
                    message="The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)"
                ) from error

    async def get_redemptions(self, status: Literal["UNFULFILLED", "FULFILLED", "CANCELLED"], sort: Literal["OLDEST", "NEWEST"] = "OLDEST") -> HTTPAwaitableAsyncIterator[CustomRewardRedemption]:
        """
        Gets redemptions for this reward

        Parameters
        -----------
        status:
            :class:`str` one of UNFULFILLED, FULFILLED or CANCELED
        sort:
            Optional[:class:`str`] the order redemptions are returned in. One of OLDEST, NEWEST. Default: OLDEST.
        """
        try:
            pager = self._http.get_reward_redemptions(
                self._user, self._broadcaster_id, self.id, status=status, sort=sort
            )
        except Unauthorized as error:
            raise Unauthorized(error._response, await error._response.json(), message=f"The token for {self._user} is invalid") from error
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
            pager.set_adapter(lambda http, data: CustomRewardRedemption(http, data, self))
            return pager


class CustomRewardRedemption:
    """
    A redemption of a :class:`CustomReward`

    Attributes
    -----------
    id: :class:`str`
        The ID of the redemption
    user: :class:`~twitchio.PartialUser`
        The user who redeemed the reward
    input: :class:`str`
        The input from the user, if the reward requires it. Otherwise this is an empty string
    status: Literal["UNFULFILLED", "FULFILLED", "CANCELLED"]
        The status of the redemption
    redeemed_at: :class:`datetime.datetime`
        When the reward was redeemed
    reward: Union[:class:`PartialCustomReward`, :class:`CustomReward`]
        The reward this was redeemed with. This will always be a :class:`CustomReward` when fetched with :func:`CustomReward.get_redemptions`
    """

    __slots__ = "_http", "_broadcaster", "id", "user", "input", "status", "redeemed_at", "reward"

    def __init__(self, http: HTTPHandler, obj: dict, parent: Optional[CustomReward]):
        self._http: HTTPHandler = http
        self._broadcaster = PartialUser(http, obj["broadcaster_id"], obj["broadcaster_name"])
        self.id: str = obj["id"]
        self.user: PartialUser = PartialUser(http, obj["user_id"], obj["user_name"])
        self.input: str = obj["user_input"]
        self.status: Literal["UNFULFILLED", "FULFILLED", "CANCELLED"] = obj["status"]
        self.redeemed_at: datetime.datetime = parse_timestamp(obj["redeemed_at"])
        self.reward: Union[PartialCustomReward, CustomReward] = parent or PartialCustomReward(obj["reward"])

    def __repr__(self):
        return f"<CustomRewardRedemption id={self.id} user={self.user} input={self.input} status={self.status} redeemed_at={self.redeemed_at}>"

    async def fulfill(self) -> Self:
        """
        marks the redemption as fulfilled

        Returns
        --------
        itself.
        """
        reward_id = self.reward.id if isinstance(self.reward, CustomReward) else self.reward.id
        try:
            data = await self._http.update_reward_redemption_status(
                self._broadcaster, self._broadcaster.id, self.id, reward_id, True
            )
        except Unauthorized:
            raise
        except HTTPResponseException as error:
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
            self.__init__(self._http, data["data"], self.reward if isinstance(self.reward, CustomReward) else None)
            return self

    async def refund(self) -> Self:
        """
        marks the redemption as cancelled

        Returns
        --------
        itself.
        """
        reward_id = self.reward.id if isinstance(self.reward, CustomReward) else self.reward.id
        try:
            data = await self._http.update_reward_redemption_status(
                self._broadcaster, self._broadcaster.id, self.id, reward_id, False
            )
        except Unauthorized:
            raise
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
            self.__init__(self._http, data["data"], self.reward if isinstance(self.reward, CustomReward) else None)
            return self
