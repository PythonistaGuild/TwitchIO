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
from ..user import PartialUser


if TYPE_CHECKING:
    import datetime

    from ..http import HTTPClient
    from ..types_.responses import CustomRewardResponse
    from ..utils import Colour, parse_timestamp

__all__ = ("CustomReward",)


class CustomReward:
    """
    Represents a custom reward from a broadcaster's channel.

    Attributes
    -----------
    snooze_count: int
        The number of snoozes available for the broadcaster.
    snooze_refresh_at: datetime.datetime
        The UTC datetime when the broadcaster will gain an additional snooze.
    duration: int
        The length in seconds of the scheduled upcoming ad break.
    next_ad_at: datetime.datetime | None
        The UTC datetime of the broadcaster's next scheduled ad format. None if channel has no ad scheduled.
    last_ad_at: datetime.datetime | None
        The UTC datetime of the broadcaster's last ad-break. None if channel has not run an ad or is not live.
    preroll_free_time: int
        The amount of pre-roll free time remaining for the channel in seconds. Returns 0 if they are currently not pre-roll free.
    """

    __slots__ = (
        "broadcaster",
        "id",
        "title",
        "prompt",
        "cost",
        "image",
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

    def __init__(self, data: CustomRewardResponse, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], data["broadcaster_login"])
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.prompt: str = data["prompt"]
        self.cost: int = int(data["cost"])
        self.image: Asset | None = Asset(data["image"], http=http) if data["image"] else None #TODO This is an object of multiple image urls
        self.default_image = data["default_image"]
        self.background_color = data["background_color"]
        self.enabled: bool = data["is_enabled"]
        self.input_required: bool = data["is_user_input_required"]
        self.max_per_stream_setting: bool = data["is_user_input_required"]
        self.paused: bool = data["is_paused"]
        self.in_stock: bool = data["is_in_stock"]
        self.skip_queue: bool = data["should_redemptions_skip_request_queue"]
        self.current_stream: int = data.get("redemptions_redeemed_current_stream", 0)
        self.cooldown_until: datetime.datetime | None = parse_timestamp(data["cooldown_expires_at"]) if data["cooldown_expires_at"] else None
        
