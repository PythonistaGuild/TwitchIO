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

from typing import TYPE_CHECKING, Literal

from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import HypeTrainEventsResponseContributions, HypeTrainEventsResponseData

__all__ = ("HypeTrainContribution", "HypeTrainEvent")


class HypeTrainEvent:
    """Represents a Hype Train Event.

    Attributes
    -----------
    id: str
        The ID of the event.
    hype_train_id: str
        The ID of the Hype Train.
    type: str
        The type of the event, in the form, hypetrain.{event_name} (i.e. `hypetrain.progression`).
    version: str
        The version of the endpoint.
    broadcaster: PartialUser
        The user whose channel the Hype Train is occurring on.
    timestamp: datetime.datetime
        The time the event happened at.
    cooldown_end_time: datetime.datetime
        The time that another Hype Train can happen at.
    expiry: datetime.datetime
        The time that this Hype Train expires at.
    started_at: datetime.datetime
        The time that this Hype Train started at.
    last_contribution: HypeTrainContribution
        The last contribution to this Hype Train.
    level: int
        The level reached on this Hype Train (1-5).
    top_contributions: list[HypeTrainContribution]
        The top contributors to the Hype Train.
    total_contributed: int
        The current total amount raised.
    goal: int
        The goal for the next Hype Train level
    """

    __slots__ = (
        "broadcaster",
        "cooldown_end_time",
        "expiry",
        "goal",
        "hype_train_id",
        "id",
        "last_contribution",
        "level",
        "started_at",
        "timestamp",
        "top_contributions",
        "total_contributed",
        "type",
        "version",
    )

    def __init__(self, data: HypeTrainEventsResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.type: str = data["event_type"]
        self.timestamp: datetime.datetime = parse_timestamp(data["event_timestamp"])
        self.version: str = data["version"]
        self.broadcaster = PartialUser(data["event_data"]["broadcaster_id"], None, http=http)
        self.cooldown_end_time: datetime.datetime = parse_timestamp(data["event_data"]["cooldown_end_time"])
        self.expiry: datetime.datetime = parse_timestamp(data["event_data"]["expires_at"])
        self.goal: int = int(data["event_data"]["goal"])
        self.hype_train_id: str = data["event_data"]["id"]
        self.last_contribution = HypeTrainContribution(data["event_data"]["last_contribution"], http=http)
        self.level: int = int(data["event_data"]["level"])
        self.started_at: datetime.datetime = parse_timestamp(data["event_data"]["started_at"])
        self.top_contributions = [HypeTrainContribution(d, http=http) for d in data["event_data"]["top_contributions"]]
        self.total_contributed: int = data["event_data"]["total"]

    def __repr__(self) -> str:
        return f"<HypeTrainEvent id={self.id} type={self.type} level={self.level} broadcaster={self.broadcaster}>"


class HypeTrainContribution:
    """A Contribution to a Hype Train

    Attributes
    -----------
    total: int
        The total amount contributed. If type is ``BITS``, total represents the amount of Bits used.
        If type is ``SUBS``, total is 500, 1000, or 2500 to represent tier 1, 2, or 3 subscriptions, respectively.
    type: typing.Literal["BITS", "SUBS", "OTHER"]
        Identifies the contribution method, either BITS, SUBS or OTHER.
    user: PartialUser
        The user making the contribution.
    """

    __slots__ = "total", "type", "user"

    def __init__(self, data: HypeTrainEventsResponseContributions, *, http: HTTPClient) -> None:
        self.total: int = int(data["total"])
        self.type: Literal["BITS", "SUBS", "OTHER"] = data["type"]
        self.user = PartialUser(data["user"], None, http=http)

    def __repr__(self) -> str:
        return f"<HypeTrainContribution total={self.total} type={self.type} user={self.user}>"
