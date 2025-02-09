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

from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import (
        ChannelStreamScheduleResponseCategory,
        ChannelStreamScheduleResponseData,
        ChannelStreamScheduleResponseSegments,
        ChannelStreamScheduleResponseVacation,
    )


__all__ = ("Schedule", "ScheduleCategory", "ScheduleSegment", "ScheduleVacation")


class Schedule:
    """Represents a channel's stream schedule

    Attributes
    -----------
    segments: list[ScheduleSegment]
        The list of broadcasts in the broadcaster's streaming schedule.
    broadcaster: PartialUser
        The broadcaster that owns the broadcast schedule.
    vacation: ScheduleVacation | None
        The dates when the broadcaster is on vacation and not streaming. Is set to None if vacation mode is not enabled.
    """

    __slots__ = ("broadcaster", "segments", "vacation")

    def __init__(self, data: ChannelStreamScheduleResponseData, *, http: HTTPClient) -> None:
        self.segments: list[ScheduleSegment] = [
            ScheduleSegment(d, http=http, broadcaster_id=data["broadcaster_id"]) for d in data["segments"]
        ]
        self.broadcaster: PartialUser = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=http
        )
        self.vacation: ScheduleVacation | None = ScheduleVacation(data["vacation"]) if data["vacation"] else None

    def __repr__(self) -> str:
        return f"<Schedule segments={self.segments} broadcaster={self.broadcaster} vacation={self.vacation}>"


class ScheduleSegment:
    """Represents a segment of a channel's stream schedule

    Attributes
    -----------
    id: str
        The ID for the scheduled broadcast.
    start_time: datetime.datetime
        Scheduled start time for the scheduled broadcast
    end_time: datetime.datetime
        Scheduled end time for the scheduled broadcast
    title: str
        Title for the scheduled broadcast.
    canceled_until: datetime.datetime | None
        Indicates whether the broadcaster canceled this segment of a recurring broadcast.
        If the broadcaster canceled this segment, this field is set to the same value that's in the end_time field; otherwise, it's None.
    category: ScheduleCategory | None
        The game or category details for the scheduled broadcast.
    is_recurring: bool
        Indicates if the scheduled broadcast is recurring weekly.
    """

    __slots__ = (
        "_broadcaster_id",
        "_http",
        "canceled_until",
        "category",
        "end_time",
        "id",
        "recurring",
        "start_time",
        "title",
    )

    def __init__(self, data: ChannelStreamScheduleResponseSegments, *, http: HTTPClient, broadcaster_id: str) -> None:
        self._http: HTTPClient = http
        self._broadcaster_id = broadcaster_id
        self.id: str = data["id"]
        self.start_time: datetime.datetime = parse_timestamp(data["start_time"])
        self.end_time: datetime.datetime = parse_timestamp(data["end_time"])
        self.title: str = data["title"]
        self.canceled_until: datetime.datetime | None = (
            parse_timestamp(data["canceled_until"]) if data["canceled_until"] else None
        )
        self.category: ScheduleCategory | None = ScheduleCategory(data["category"]) if data["category"] else None
        self.recurring: bool = bool(data["is_recurring"])

    def __repr__(self) -> str:
        return f"<ScheduleSegment id={self.id} start_time={self.start_time} end_time={self.end_time} title={self.title}>"

    async def update_segment(
        self,
        *,
        start_time: datetime.datetime | None = None,
        duration: int | None = None,
        category_id: str | None = None,
        title: str | None = None,
        canceled: bool | None = None,
        timezone: str | None = None,
    ) -> Schedule:
        """|coro|

        Updates a scheduled broadcast segment.

        .. note::
            Requires a user access token that includes the ``channel:manage:schedule`` scope.

        Parameters
        ----------
        token_for: str | PartialUser
            User access token that includes the ``channel:manage:schedule`` scope.
        start_time: datetime.datetime | None
            The datetime that the broadcast segment starts. This can be timezone aware.
        duration: int | None
            he length of time, in minutes, that the broadcast is scheduled to run. The duration must be in the range 30 through 1380 (23 hours)
        category_id: str | None
            The ID of the category that best represents the broadcast's content. To get the category ID, use the [Search Categories][twitchio.client.search_categories].
        title: str | None
            The broadcast's title. The title may contain a maximum of 140 characters.
        canceled: bool | None
            A Boolean value that indicates whether the broadcast is canceled. Set to True to cancel the segment.
        timezone: str | None
            The time zone where the broadcast takes place. Specify the time zone using `IANA time zone database <https://www.iana.org/time-zones>`_ format (for example, America/New_York).

        Returns
        -------
        Schedule
            Schedule object.

        Raises
        ------
        ValueError
            Duration must be between 30 and 1380.
        ValueError
            Title must not be greater than 140 characters.
        """
        if duration is not None and (duration < 30 or duration > 1380):
            raise ValueError("Duration must be between 30 and 1380.")
        if title is not None and len(title) > 140:
            raise ValueError("Title must not be greater than 140 characters.")

        data = await self._http.patch_channel_stream_schedule_segment(
            broadcaster_id=self._broadcaster_id,
            id=self.id,
            start_time=start_time,
            duration=duration,
            category_id=category_id,
            title=title,
            canceled=canceled,
            timezone=timezone,
            token_for=self._broadcaster_id,
        )

        return Schedule(data["data"], http=self._http)

    async def delete(self) -> None:
        """|coro|

        Removes a broadcast segment from the broadcaster's streaming schedule.

        For recurring segments, removing a segment removes all segments in the recurring schedule.

        .. note::
            Requires a user access token that includes the ``channel:manage:schedule`` scope.

        Parameters
        ----------
        token_for: str | PartialUser
            User access token that includes the ``channel:manage:schedule`` scope.
        """
        return await self._http.delete_channel_stream_schedule_segment(
            broadcaster_id=self._broadcaster_id, id=self.id, token_for=self._broadcaster_id
        )


class ScheduleCategory:
    """Game or category details of a stream's schedule

    Attributes
    -----------
    id: str
        The game or category ID.
    name: str
        The game or category name.
    """

    __slots__ = ("id", "name")

    def __init__(self, data: ChannelStreamScheduleResponseCategory) -> None:
        self.id = data["id"]
        self.name = data["name"]

    def __repr__(self) -> str:
        return f"<ScheduleCategory id={self.id} name={self.name}>"


class ScheduleVacation:
    """A schedule's vacation details

    Attributes
    -----------
    start_time: datetime.datetime
        Start date of stream schedule vaction.
    end_time: datetime.datetime
        End date of stream schedule vaction.
    """

    __slots__ = ("end_time", "start_time")

    def __init__(self, data: ChannelStreamScheduleResponseVacation) -> None:
        self.start_time = parse_timestamp(data["start_time"])
        self.end_time = parse_timestamp(data["end_time"])

    def __repr__(self) -> str:
        return f"<ScheduleVacation start_time={self.start_time} end_time={self.end_time}>"
