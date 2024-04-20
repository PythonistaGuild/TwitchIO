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
        CustomRewardsResponseDefaultImage,
        CustomRewardsResponseImage,
    )

__all__ = ("CustomReward", "RewardStreamSetting", "RewardCooldown")


class RewardCooldown:
    def __init__(self, is_enabled: bool, cooldown_seconds: int) -> None:
        self.is_enabled: bool = is_enabled
        self.cooldown_seconds: int = cooldown_seconds


class RewardStreamSetting:
    def __init__(self, is_enabled: bool, max_value: int) -> None:
        self.is_enabled: bool = is_enabled
        self.max_value: int = max_value


class CustomReward:
    """
    Represents a custom reward from a broadcaster's channel.

    Attributes
    -----------
    id: str
        The ID of the Custom Reward
    title: str
        ...
    prompt: str
        ...
    cost: int
        ...
    default_image: ...
        ...
    background_color: Color
        ...
    enabled: bool
        ...
    input_required: bool
        ...
    paused: bool
        ...
    in_stock: bool
        ...
    image: dict[str, Asset] | None
        ...
    skip_queue: bool
        ...
    current_stream: int | None
        ...
    cooldown_until: datetime.datetime
        ...
    cooldown: RewardCooldown
        ...
    max_per_stream: RewardStreamSetting
        ...
    max_per_user_stream: RewardStreamSetting
        ...
    """

    __slots__ = (
        "_http",
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
        "current_stream",
        "cooldown_until",
    )

    def __init__(self, data: CustomRewardsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self._image: CustomRewardsResponseImage | None = data["image"]
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.prompt: str = data["prompt"]
        self.cost: int = int(data["cost"])
        self.default_image: CustomRewardsResponseDefaultImage = data["default_image"]
        self.background_color: Colour = Colour.from_hex(data["background_color"])
        self.enabled: bool = data["is_enabled"]
        self.input_required: bool = data["is_user_input_required"]
        self.paused: bool = data["is_paused"]
        self.in_stock: bool = data["is_in_stock"]
        self.skip_queue: bool = data["should_redemptions_skip_request_queue"]
        self.current_stream: int | None = data.get("redemptions_redeemed_current_stream")
        self.cooldown_until: datetime.datetime | None = (
            parse_timestamp(data["cooldown_expires_at"]) if data["cooldown_expires_at"] else None
        )
        self.cooldown: RewardCooldown = RewardCooldown(
            data["global_cooldown_setting"]["is_enabled"],
            data["global_cooldown_setting"]["global_cooldown_seconds"]
        )
        self.max_per_stream: RewardStreamSetting = RewardStreamSetting(
            data["max_per_stream_setting"]["is_enabled"],
            data["max_per_stream_setting"]["max_per_stream"]
        )
        self.max_per_user_stream: RewardStreamSetting = RewardStreamSetting(
            data["max_per_user_per_stream_setting"]["is_enabled"],
            data["max_per_user_per_stream_setting"]["max_per_user_per_stream"],
        )

    @property
    def image(self) -> dict[str, Asset] | None:
        if self._image is not None:
            return {k: Asset(str(v), http=self._http) for k, v in self._image.items()}
        else:
            return None
