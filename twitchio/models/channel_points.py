"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

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

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple

from twitchio.assets import Asset
from twitchio.user import PartialUser
from twitchio.utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPAsyncIterator, HTTPClient
    from twitchio.types_.responses import (
        CustomRewardRedemptionResponseData,
        CustomRewardsResponseData,
        CustomRewardsResponseImage,
    )


__all__ = ("CustomReward", "CustomRewardRedemption", "RewardCooldown", "RewardLimitSettings")


class RewardCooldown(NamedTuple):
    """NamedTuple that represents a custom reward's cooldown settings.

    Attributes
    -----------
    enabled: bool
        Whether a coooldown between redemptions is enabled or not. Default is False.
    seconds: int
        The cooldown period in seconds. This only applies if ``is_enabled`` is True.
        Min value is 1; however, the minimum value is 60 for it to be shown in the Twitch UX.
    """

    enabled: bool
    seconds: int


class RewardLimitSettings(NamedTuple):
    """NamedTuple that represents a custom reward's stream limit settings.

    Attributes
    -----------
    enabled: bool
        Whether the stream setting is enabled or not.
    value: int
        The max number of redemptions allowed. Minimum value is 1.
    """

    enabled: bool
    value: int


class CustomReward:
    """Represents a custom reward from a broadcaster's channel.

    Attributes
    -----------
    broadcaster: PartialUser
        The broadcaster that owns the CustomReward.
    id: str
        The ID that uniquely identifies this custom reward.
    title: str
        The title of the reward.
    prompt: str
        The prompt shown to the viewer when they redeem the reward if user input is required.
    cost: int
        The cost of the reward in Channel Points.
    default_image: dict[str, str]
        A dictionary of default images for the reward. The keys are as follows: url_1x, url_2x and url_4x.
    colour: Colour
        The background colour to use for the reward. There is an alias named ``color``.
    enabled: bool
        A Boolean value that determines whether the reward is enabled. Is True if enabled; otherwise, False. Disabled rewards aren't shown to the user.
    input_required: bool
        A Boolean value that determines whether the user must enter information when redeeming the reward. Is True if the reward requires user input.
    paused: bool
        A Boolean value that determines whether the reward is currently paused. Is True if the reward is paused. Viewers can't redeem paused rewards.
    in_stock: bool
        A Boolean value that determines whether the reward is currently in stock. Is True if the reward is in stock. Viewers can't redeem out of stock rewards.
    image: dict[str, str] | None
        A dictionary of custom images for the reward. This will return None if the broadcaster did not upload any images.
        The keys, if available, are as follows: url_1x, url_2x and url_4x.
    skip_queue: bool
        A Boolean value that determines whether redemptions should be set to FULFILLED status immediately when a reward is redeemed. If False, status is set to UNFULFILLED and follows the normal request queue process. The default is False.
    current_stream_redeems: int | None
        The number of redemptions redeemed during the current live stream. The number counts against the ``max_per_stream.max_value`` limit. This is None if the broadcaster's stream isn't live or ``max_per_stream_setting`` isn't enabled.
    cooldown_until: datetime.datetime | None
        The datetime of when the cooldown period expires. Is null if the reward isn't in a cooldown state
    cooldown: RewardCooldown
        The cooldown settings of a reward. This represents whether reward has a cooldown enabled and the cooldown period in seconds.
    max_per_stream: RewardLimitSettings
        The settings of a reward over a live stream. This represents whether a reward has a max number of redemptions per stream and if the setting is enabled or not.
    max_per_user_stream: RewardLimitSettings
        The settings of a reward over a live stream per user. This represents whether a reward has a max number of redemptions per user per stream and if the setting is enabled or not.
    """

    __slots__ = (
        "_http",
        "_image",
        "broadcaster",
        "colour",
        "cooldown",
        "cooldown_until",
        "cost",
        "current_stream_redeems",
        "default_image",
        "enabled",
        "id",
        "in_stock",
        "input_required",
        "max_per_stream",
        "max_per_user_stream",
        "paused",
        "prompt",
        "skip_queue",
        "title",
    )

    def __init__(self, data: CustomRewardsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.broadcaster: PartialUser = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=self._http
        )
        self._image: CustomRewardsResponseImage | None = data.get("image")
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.prompt: str = data["prompt"]
        self.cost: int = int(data["cost"])
        self.default_image: dict[str, str] = {k: str(v) for k, v in data["default_image"].items()}
        self.colour: Colour = Colour.from_hex(data["background_color"])
        self.enabled: bool = data["is_enabled"]
        self.input_required: bool = data["is_user_input_required"]
        self.paused: bool = data["is_paused"]
        self.in_stock: bool = data["is_in_stock"]
        self.skip_queue: bool = data["should_redemptions_skip_request_queue"]
        self.current_stream_redeems: int | None = (
            int(data["redemptions_redeemed_current_stream"])
            if data["redemptions_redeemed_current_stream"] is not None
            else None
        )
        self.cooldown_until: datetime.datetime | None = (
            parse_timestamp(data["cooldown_expires_at"]) if data["cooldown_expires_at"] else None
        )
        self.cooldown: RewardCooldown = RewardCooldown(
            bool(data["global_cooldown_setting"]["is_enabled"]),
            int(data["global_cooldown_setting"]["global_cooldown_seconds"]),
        )
        self.max_per_stream: RewardLimitSettings = RewardLimitSettings(
            bool(data["max_per_stream_setting"]["is_enabled"]), int(data["max_per_stream_setting"]["max_per_stream"])
        )
        self.max_per_user_stream: RewardLimitSettings = RewardLimitSettings(
            bool(data["max_per_user_per_stream_setting"]["is_enabled"]),
            int(data["max_per_user_per_stream_setting"]["max_per_user_per_stream"]),
        )

    def __repr__(self) -> str:
        return f"<CustomReward id={self.id} title={self.title} cost={self.cost}>"

    def __str__(self) -> str:
        return self.title

    @property
    def color(self) -> Colour | None:
        return self.colour

    @property
    def image(self) -> dict[str, str] | None:
        if self._image is not None:
            return {k: str(v) for k, v in self._image.items()}
        else:
            return None

    def get_image(self, size: Literal["1x", "2x", "4x"] = "2x", use_default: bool = False) -> Asset:
        """Get an image Asset for the reward at a specified size.

        Falls back to default images if no custom images have been uploaded.

        Parameters
        ----------
        size: str
            The size key of the image. Options are "1x", "2x", "4x". Defaults to "2x".
        use_default: bool
            Use default images instead of user uploaded images.

        Returns
        -------
        Asset
            The Asset for the image. Falls back to default images if no custom images have been uploaded.
        """
        if use_default or self.image is None or f"url_{size}" not in self.image:
            url = self.default_image[f"url_{size}"]
        else:
            url = self.image[f"url_{size}"]

        return Asset(url, http=self._http)

    async def delete(self) -> None:
        """|coro|

        Delete the custom reward.

        The app / client ID used to create the reward is the only app that may delete it.
        If the reward's redemption status is UNFULFILLED at the time the reward is deleted, its redemption status is marked as FULFILLED.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.
        """
        await self._http.delete_custom_reward(
            broadcaster_id=self.broadcaster.id, reward_id=self.id, token_for=self.broadcaster.id
        )

    async def update(
        self,
        *,
        title: str | None = None,
        cost: int | None = None,
        prompt: str | None = None,
        enabled: bool | None = None,
        colour: str | Colour | None = None,
        input_required: bool | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        paused: bool | None = None,
        skip_queue: bool | None = None,
    ) -> CustomReward:
        """|coro|

        Update the custom reward.

        .. important::
            The app / client ID used to create the reward is the only app that may update the reward.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.

        Parameters
        -----------
        title: str | None
            The reward's title.
            The title may contain a maximum of 45 characters and it must be unique amongst all of the broadcaster's custom rewards.
        cost: int | None
            The cost of the reward, in channel points. The minimum is 1 point.
        prompt: str | None
            The prompt shown to the viewer when they redeem the reward.
            ``input_required`` needs to be set to ``True`` for this to work,
        enabled: bool | None
             Boolean value that indicates whether the reward is enabled. Set to ``True`` to enable the reward. Viewers see only enabled rewards.
        colour: str | Colour | None
            The background colour to use for the reward. Specify the color using Hex format (for example, #00E5CB).
            You can also pass a twitchio.Colour object.
        input_required: bool | None
            A Boolean value that determines whether users must enter information to redeem the reward.
        max_per_stream: int | None
            The maximum number of redemptions allowed per live stream.
            Setting this to 0 disables the maximum number of redemptions per stream.
        max_per_user: int | None
            The maximum number of redemptions allowed per user per live stream.
            Setting this to 0 disables the maximum number of redemptions per user per stream.
        global_cooldown: int | None
            The cooldown period, in seconds. The minimum value is 1; however, for it to be shown in the Twitch UX, the minimum value is 60.
            Setting this to 0 disables the global cooldown period.
        paused: bool | None
            A Boolean value that determines whether to pause the reward. Set to ``True`` to pause the reward. Viewers can't redeem paused rewards.
        skip_queue: bool | None
            A Boolean value that determines whether redemptions should be set to FULFILLED status immediately when a reward is redeemed.
            If False, status is set to UNFULFILLED and follows the normal request queue process.

        Returns
        --------
        CustomReward

        Raises
        ------
        ValueError
            title must be a maximum of 45 characters.
        ValueError
            prompt must be a maximum of 200 characters.
        ValueError
            Minimum value must be at least 1.
        """

        if title is not None and len(title) > 45:
            raise ValueError("title must be a maximum of 45 characters.")
        if cost is not None and cost < 1:
            raise ValueError("cost must be at least 1.")
        if prompt is not None and len(prompt) > 200:
            raise ValueError("prompt must be a maximum of 200 characters.")

        data = await self._http.patch_custom_reward(
            broadcaster_id=self.broadcaster.id,
            token_for=self.broadcaster.id,
            reward_id=self.id,
            title=title,
            cost=cost,
            prompt=prompt,
            enabled=enabled,
            background_color=colour,
            user_input_required=input_required,
            max_per_stream=max_per_stream,
            max_per_user=max_per_user,
            global_cooldown=global_cooldown,
            paused=paused,
            skip_queue=skip_queue,
        )

        return CustomReward(data=data["data"][0], http=self._http)

    def fetch_redemptions(
        self,
        *,
        status: Literal["CANCELED", "FULFILLED", "UNFULFILLED"],
        ids: list[str] | None = None,
        sort: Literal["OLDEST", "NEWEST"] = "OLDEST",
        first: int = 20,
    ) -> HTTPAsyncIterator[CustomRewardRedemption]:
        """|aiter|

        Fetch redemptions from the CustomReward.

        Canceled and fulfilled redemptions are returned for only a few days after they're canceled or fulfilled.

        .. note::
            Requires a user access token that includes the ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

        Parameters
        -----------
        status: typing.Literal["CANCELED", "FULFILLED", "UNFULFILLED"]
            The state of the redemption. This can be one of the following: "CANCELED", "FULFILLED", "UNFULFILLED"
        ids: list[str] | None
            A list of IDs to filter the redemptions by. You may specify up to 50.
        sort: typing.Literal["OLDEST", "NEWEST"]
            The order to sort the redemptions by. The default is OLDEST.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 50.

        Returns
        --------
        HTTPAsyncIterator[CustomRewardRedemption]

        Raises
        ------
        ValueError
            You may only specify up to 50 redemption ids.
        """

        first = max(1, min(50, first))

        if ids is not None and len(ids) > 50:
            raise ValueError("You may only specify up to 50 redemption ids.")

        return self._http.get_custom_reward_redemptions(
            broadcaster_id=self.broadcaster.id,
            token_for=self.broadcaster.id,
            reward_id=self.id,
            ids=ids,
            status=status,
            sort=sort,
            first=first,
            parent_reward=self,
        )


class CustomRewardRedemption:
    """
    Represents a custom reward redemption.

    Attributes
    -----------
    id: str
        The ID that uniquely identifies this redemption.
    status: typing.Literal["CANCELED", "FULFILLED", "UNFULFILLED"]
        The state of the redemption. This can be one of the following: "CANCELED", "FULFILLED", "UNFULFILLED"
    redeemed_at: datetime.datetime
        The prompt shown to the viewer when they redeem the reward if user input is required.
    reward: CustomReward
        This is the reward that the redemption is from.
    user: PartialUser
        The user that made the redemption.
    """

    __slots__ = ("_http", "id", "redeemed_at", "reward", "status", "user")

    def __init__(
        self,
        data: CustomRewardRedemptionResponseData,
        parent_reward: CustomReward,
        http: HTTPClient,
    ) -> None:
        self.id = data["id"]
        self.status: Literal["CANCELED", "FULFILLED", "UNFULFILLED"] = data["status"]
        self.redeemed_at: datetime.datetime = parse_timestamp(data["redeemed_at"])
        self.reward: CustomReward = parent_reward
        self._http: HTTPClient = http
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["broadcaster_name"], http=self._http)

    def __repr__(self) -> str:
        return f"<CustomRewardRedemption id={self.id} status={self.status} redeemed_at={self.redeemed_at}>"

    async def fulfill(self) -> CustomRewardRedemption:
        """|coro|

        Updates a redemption's status to FULFILLED.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.


        Returns
        --------
        CustomRewardRedemption
        """
        data = await self._http.patch_custom_reward_redemption(
            broadcaster_id=self.reward.broadcaster.id,
            id=self.reward.broadcaster.id,
            token_for=self,
            reward_id=self.reward.id,
            status="FULFILLED",
        )
        return CustomRewardRedemption(data["data"][0], parent_reward=self.reward, http=self._http)

    async def refund(self) -> CustomRewardRedemption:
        """|coro|

        Updates a redemption's status to CANCELED.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.

        Returns
        --------
        CustomRewardRedemption
        """
        data = await self._http.patch_custom_reward_redemption(
            broadcaster_id=self.reward.broadcaster.id,
            id=self.id,
            token_for=self.reward.broadcaster.id,
            reward_id=self.reward.id,
            status="CANCELED",
        )
        return CustomRewardRedemption(data["data"][0], parent_reward=self.reward, http=self._http)
