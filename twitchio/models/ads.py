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

import datetime
from typing import TYPE_CHECKING

from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    from twitchio.types_.responses import AdScheduleResponseData, SnoozeNextAdResponseData, StartCommercialResponseData


__all__ = ("AdSchedule", "CommercialStart", "SnoozeAd")


class CommercialStart:
    """Represents a Commercial starting.

    Attributes
    ----------
    length: int
        The length of the commercial you requested. If you request a commercial that's longer than 180 seconds, the API uses 180 seconds.
    message: str
        A message that indicates whether Twitch was able to serve an ad.
    retry_after: int
        The number of seconds you must wait before running another commercial.
    """

    __slots__ = ("length", "message", "retry_after")

    def __init__(self, data: StartCommercialResponseData) -> None:
        self.length: int = int(data["length"])
        self.message: str = data["message"]
        self.retry_after: int = int(data["retry_after"])

    def __repr__(self) -> str:
        return f"<CommercialStart length={self.length} message={self.message}>"


class AdSchedule:
    """
    Represents ad schedule information.

    Attributes
    -----------
    snooze_count: int
        The number of snoozes available for the broadcaster.
    snooze_refresh_at: datetime.datetime | None
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

    __slots__ = ("duration", "last_ad_at", "next_ad_at", "preroll_free_time", "snooze_count", "snooze_refresh_at")

    def __init__(self, data: AdScheduleResponseData) -> None:
        self.snooze_count: int = int(data["snooze_count"])
        self.snooze_refresh_at: datetime.datetime | None = (
            _parse_timestamp(data["snooze_refresh_at"]) if data["snooze_refresh_at"] else None
        )
        self.duration: int = int(data["duration"])
        self.next_ad_at: datetime.datetime | None = _parse_timestamp(data["next_ad_at"]) if data["next_ad_at"] else None
        self.last_ad_at: datetime.datetime | None = _parse_timestamp(data["last_ad_at"]) if data["last_ad_at"] else None
        self.preroll_free_time: int = int(data["preroll_free_time"])

    def __repr__(self) -> str:
        return f"<AddSchedule snooze_count={self.snooze_count} duration={self.duration} next_ad_at={self.next_ad_at}>"


class SnoozeAd:
    """
    Represents ad schedule information.

    Attributes
    -----------
    snooze_count: int
        The number of snoozes available for the broadcaster.
    snooze_refresh_at: datetime.datetime | None
        The UTC datetime when the broadcaster will gain an additional snooze.
    next_ad_at: datetime.datetime | None
        The UTC datetime of the broadcaster's next scheduled ad. None if channel has no ad scheduled.
    """

    __slots__ = ("next_ad_at", "snooze_count", "snooze_refresh_at")

    def __init__(self, data: SnoozeNextAdResponseData) -> None:
        self.snooze_count: int = int(data["snooze_count"])
        self.snooze_refresh_at: datetime.datetime | None = (
            _parse_timestamp(data["snooze_refresh_at"]) if data["snooze_refresh_at"] else None
        )
        self.next_ad_at: datetime.datetime | None = _parse_timestamp(data["next_ad_at"]) if data["next_ad_at"] else None

    def __repr__(self) -> str:
        return f"<SnoozeAd snooze_count={self.snooze_count} snooze_refresh_at={self.snooze_refresh_at} next_ad_at={self.next_ad_at}>"


def _parse_timestamp(timestamp: str | int) -> datetime.datetime:
    """Helper function for Ads due to incorrect Twitch documention and a known issue with the return format.
    This may be incorporated into the main `parse_timestamp` utility function in the future.
    """
    if isinstance(timestamp, str):
        return parse_timestamp(timestamp)
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)
