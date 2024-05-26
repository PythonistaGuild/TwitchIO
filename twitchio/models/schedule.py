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


__all__ = ("Schedule", "ScheduleSegment", "ScheduleCategory", "ScheduleVacation")


class Schedule:
    """
    Represents a channel's stream schedule

    Attributes
    -----------
    segments: list[ScheduleSegment]
        The list of broadcasts in the broadcaster's streaming schedule.
    broadcaster: PartialUser
        The broadcaster that owns the broadcast schedule.
    vacation: ScheduleVacation | None
        The dates when the broadcaster is on vacation and not streaming. Is set to None if vacation mode is not enabled.
    """

    __slots__ = ("segments", "broadcaster", "vacation")

    def __init__(self, data: ChannelStreamScheduleResponseData, *, http: HTTPClient) -> None:
        self.segments: list[ScheduleSegment] = [ScheduleSegment(d) for d in data["segments"]]
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], data["broadcaster_login"], http=http)
        self.vacation: ScheduleVacation | None = ScheduleVacation(data["vacation"]) if data["vacation"] else None

    def __repr__(self) -> str:
        return f"<Schedule segments={self.segments} broadcaster={self.broadcaster} vacation={self.vacation}>"


class ScheduleSegment:
    """
    Represents a segment of a channel's stream schedule

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

    __slots__ = ("id", "start_time", "end_time", "title", "canceled_until", "recurring", "category")

    def __init__(self, data: ChannelStreamScheduleResponseSegments) -> None:
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
        return (
            f"<ScheduleSegment id={self.id} start_time={self.start_time} end_time={self.end_time} title={self.title}>"
        )


class ScheduleCategory:
    """
    Game or category details of a stream's schedule

    Attributes
    -----------
    id: :class:`str`
        The game or category ID.
    name: :class:`str`
        The game or category name.
    """

    __slots__ = ("id", "name")

    def __init__(self, data: ChannelStreamScheduleResponseCategory) -> None:
        self.id = data["id"]
        self.name = data["name"]

    def __repr__(self) -> str:
        return f"<ScheduleCategory id={self.id} name={self.name}>"


class ScheduleVacation:
    """
    A schedule's vacation details

    Attributes
    -----------
    start_time: datetime.datetime
        Start date of stream schedule vaction.
    end_time: datetime.datetime
        End date of stream schedule vaction.
    """

    __slots__ = ("start_time", "end_time")

    def __init__(self, data: ChannelStreamScheduleResponseVacation) -> None:
        self.start_time = parse_timestamp(data["start_time"])
        self.end_time = parse_timestamp(data["end_time"])

    def __repr__(self) -> str:
        return f"<ScheduleVacation start_time={self.start_time} end_time={self.end_time}>"
