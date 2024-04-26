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

from typing import TYPE_CHECKING

from ..assets import Asset
from ..utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from ..http import HTTPClient
    from ..types_.responses import (
        CustomRewardsResponseData,
        CustomRewardsResponseImage,
    )

__all__ = ("CustomReward", "RewardStreamSetting", "RewardCooldown")


class RewardCooldown:
    """
    Represents a custom reward's global cooldown settings

    Attributes
    -----------
    is_enabled: bool
        Whether a coooldown between redemptions is enabled or not. Default is False.
    cooldown_seconds: int
        The cooldown period in seconds. This only applies if ``is_enabled`` is True.
        Min value is 1; however, the minimum value is 60 for it to be shown in the Twitch UX.
    """

    def __init__(self, is_enabled: bool, cooldown_seconds: int) -> None:
        self.is_enabled: bool = is_enabled
        self.cooldown_seconds: int = cooldown_seconds

    def __repr__(self) -> str:
        return f"<RewardCooldown is_enabled={self.is_enabled} cooldown_seconds={self.cooldown_seconds}>"


class RewardStreamSetting:
    """
    Represents a custom reward's stream settings.

    Attributes
    -----------
    is_enabled: bool
        Whether the stream setting is enabled or not. Default is False.
    max_value: int
        The max number of redemptions allowed. Minimum value is 1.
    """

    def __init__(self, is_enabled: bool, max_value: int) -> None:
        self.is_enabled: bool = is_enabled
        self.max_value: int = max_value

    def __repr__(self) -> str:
        return f"<RewardStreamSetting is_enabled={self.is_enabled} max_value={self.max_value}>"


class CustomReward:
    """
    Represents a custom reward from a broadcaster's channel.

    Attributes
    -----------
    id: str
        The ID that uniquely identifies this custom reward.
    title: str
        The title of the reward.
    prompt: str
        The prompt shown to the viewer when they redeem the reward if user input is required.
    cost: int
        The cost of the reward in Channel Points.
    default_image: dict[str, Asset]
        A dictionary of default images for the reward. The keys are as follows: url_1x, url_2x and url_4x.
    background_color: Colour
        The background colour to use for the reward.
    enabled: bool
        A Boolean value that determines whether the reward is enabled. Is true if enabled; otherwise, false. Disabled rewards aren't shown to the user.
    input_required: bool
        A Boolean value that determines whether the user must enter information when redeeming the reward. Is true if the reward requires user input.
    paused: bool
        A Boolean value that determines whether the reward is currently paused. Is true if the reward is paused. Viewers can't redeem paused rewards.
    in_stock: bool
        A Boolean value that determines whether the reward is currently in stock. Is true if the reward is in stock. Viewers can't redeem out of stock rewards.
    image: dict[str, Asset] | None
        A dictionary of custom images for the reward. This will return None if the broadcaster did not upload any images.
        The keys, if available, are as follows: url_1x, url_2x and url_4x.
    skip_queue: bool
        A Boolean value that determines whether redemptions should be set to FULFILLED status immediately when a reward is redeemed. If false, status is set to UNFULFILLED and follows the normal request queue process. The default is false.
    current_stream_redeems: int | None
        The number of redemptions redeemed during the current live stream. The number counts against the ``max_per_stream.max_value`` limit. This is None if the broadcaster's stream isn't live or ``max_per_stream_setting`` isn't enabled.
    cooldown_until: datetime.datetime | None
        The datetime of when the cooldown period expires. Is null if the reward isn't in a cooldown state
    cooldown: RewardCooldown
        The cooldown settings of a reward. This represents whether reward has a cooldown enabled and the cooldown period in seconds.
    max_per_stream: RewardStreamSetting
        The settings of a reward over a live stream. This represents whether a reward has a max number of redemptions per stream and if the setting is enabled or not.
    max_per_user_stream: RewardStreamSetting
        The settings of a reward over a live stream per user. This represents whether a reward has a max number of redemptions per user per stream and if the setting is enabled or not.
    """

    __slots__ = (
        "_http",
        "_broadcaster_id",
        "id",
        "title",
        "prompt",
        "cost",
        "_image",
        "default_image",
        "background_color",
        "enabled",
        "input_required",
        "max_per_stream",
        "max_per_user_stream",
        "cooldown",
        "paused",
        "in_stock",
        "skip_queue",
        "current_stream_redeems",
        "cooldown_until",
    )

    def __init__(self, data: CustomRewardsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self._broadcaster_id: str = data["broadcaster_id"]
        self._image: CustomRewardsResponseImage | None = data["image"]
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.prompt: str = data["prompt"]
        self.cost: int = int(data["cost"])
        self.default_image: dict[str, Asset] = {
            k: Asset(str(v), http=self._http) for k, v in data["default_image"].items()
        }
        self.background_color: Colour = Colour.from_hex(data["background_color"])
        self.enabled: bool = data["is_enabled"]
        self.input_required: bool = data["is_user_input_required"]
        self.paused: bool = data["is_paused"]
        self.in_stock: bool = data["is_in_stock"]
        self.skip_queue: bool = data["should_redemptions_skip_request_queue"]
        self.current_stream_redeems: int | None = data.get("redemptions_redeemed_current_stream")
        self.cooldown_until: datetime.datetime | None = (
            parse_timestamp(data["cooldown_expires_at"]) if data["cooldown_expires_at"] else None
        )
        self.cooldown: RewardCooldown = RewardCooldown(
            data["global_cooldown_setting"]["is_enabled"], data["global_cooldown_setting"]["global_cooldown_seconds"]
        )
        self.max_per_stream: RewardStreamSetting = RewardStreamSetting(
            data["max_per_stream_setting"]["is_enabled"], data["max_per_stream_setting"]["max_per_stream"]
        )
        self.max_per_user_stream: RewardStreamSetting = RewardStreamSetting(
            data["max_per_user_per_stream_setting"]["is_enabled"],
            data["max_per_user_per_stream_setting"]["max_per_user_per_stream"],
        )

    def __repr__(self) -> str:
        return f"<CustomReward id={self.id} title={self.title} cost={self.cost}>"

    def __str__(self) -> str:
        return self.title

    @property
    def image(self) -> dict[str, Asset] | None:
        if self._image is not None:
            return {k: Asset(str(v), http=self._http) for k, v in self._image.items()}
        else:
            return None

    async def delete(self, *, token_for: str) -> None:
        """
        Delete the custom reward.

        !!! info
            The app used to create the reward is the only app that may delete it.
            If the reward's redemption status is UNFULFILLED at the time the reward is deleted, its redemption status is marked as FULFILLED.

        !!! note
            Requires a user access token that includes the channel:manage:redemptions scope.

        Attributes
        -----------
        token_for: str
            The user's token that has permission delete the reward.
        """
        await self._http.delete_custom_reward(
            broadcaster_id=self._broadcaster_id, reward_id=self.id, token_for=token_for
        )

    async def edit(
        self,
        *,
        token_for: str,
        title: str | None = None,
        cost: int | None = None,
        prompt: str | None = None,
        enabled: bool | None = None,
        background_color: str | Colour | None = None,
        user_input_required: bool | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        redemptions_skip_queue: bool | None = None,
    ) -> CustomReward: ...
