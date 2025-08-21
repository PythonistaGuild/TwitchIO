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

from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import (
        HypeTrainEventsResponseContributions,
        HypeTrainEventsResponseData,
        HypeTrainStatusResponseData,
        HypeTrainStatusTopContributions,
    )

    CombinedContributionType = Literal["BITS", "SUBS", "OTHER", "bits", "subscriptions", "other"]

__all__ = ("HypeTrainAllTimeHigh", "HypeTrainContribution", "HypeTrainEvent", "HypeTrainStatus")


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
    type: typing.Literal["BITS", "SUBS", "OTHER", "bits", "subscription", "other"]
        Identifies the contribution method.

        **HypeTrainEvent:**

        - **BITS**: cheering with Bits.
        - **SUBS**: subscription activity like subscribing or gifting subscriptions.
        - **OTHER**: covers other contribution methods not listed.

        **HypeTrainStatus:**

        - **bits**: cheering with Bits.
        - **subscription**: subscription activity like subscribing or gifting subscriptions.
        - **other**: covers other contribution methods not listed.

    user: PartialUser
        The user making the contribution.
    """

    __slots__ = ("total", "type", "user")

    def __init__(
        self, data: HypeTrainEventsResponseContributions | HypeTrainStatusTopContributions, *, http: HTTPClient
    ) -> None:
        self.total: int = int(data["total"])
        self.type: CombinedContributionType = data["type"]

        if "user" in data:
            self.user = PartialUser(data["user"], http=http)
        else:
            self.user = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<HypeTrainContribution total={self.total} type={self.type} user={self.user}>"


class HypeTrainAllTimeHigh(NamedTuple):
    """The all time high data for a Hype Train.

    Attributes
    -----------
    level: int
        The level of the record Hype Train.
    total: int
        The total amount contributed to the record Hype Train.
    achieved_at: datetime.datetime
        The datetime when the record was achieved.
    """

    level: int
    total: int
    achieved_at: datetime.datetime


class HypeTrainStatus:
    """Represents the current status of a Hype Train.

    Attributes
    -----------
    id: str
        The ID of the Hype Train.
    broadcaster: PartialUser
        The user whose channel the Hype Train is occurring on.
    level: int
        The current level of the Hype Train.
    total: int
        The total amount contributed to the Hype Train.
    progress: int
        The number of points contributed to the Hype Train at the current level.
    goal: int
        The value needed to reach the next level.
    top_contributions: list[HypeTrainContribution]
        The contributors with the most points contributed.
    started_at: datetime.datetime
        The time the Hype Train started.
    expires_at: datetime.datetime
        The time the Hype Train expires.
    type: typing.Literal["treasure", "golden_kappa", "regular"]
        The type of Hype Train. Can be one of `treasure`, `golden_kappa`, or `regular`.
    all_time_high: HypeTrainAllTimeHigh | None
        Information about the channel's hype train records.
    shared_train: bool
        Whether this Hype Train is a shared train.
    shared_train_participants: list[PartialUser]
        A list containing the broadcasters participating in the shared hype train.
    shared_all_time_high: HypeTrainAllTimeHigh | None
        Information about the channel's shared hype train records.
    """

    __slots__ = (
        "all_time_high",
        "broadcaster",
        "expires_at",
        "goal",
        "id",
        "level",
        "progress",
        "shared_all_time_high",
        "shared_train",
        "shared_train_participants",
        "started_at",
        "top_contributions",
        "total",
        "type",
    )

    def __init__(self, data: HypeTrainStatusResponseData, *, http: HTTPClient) -> None:
        current = data.get("current")
        if current is None:
            raise ValueError("HypeTrainStatus requires 'current'")
        all_time_high = data.get("all_time_high")
        shared_all_time_high = data.get("shared_all_time_high")

        self.id: str = current["id"]
        self.broadcaster = PartialUser(
            current["broadcaster_user_id"], current["broadcaster_user_id"], current["broadcaster_user_name"], http=http
        )
        self.level: int = current["level"]
        self.total: int = current["total"]
        self.progress: int = current["progress"]
        self.goal: int = current["goal"]
        self.started_at: datetime.datetime = parse_timestamp(current["started_at"])
        self.expires_at: datetime.datetime = parse_timestamp(current["expires_at"])
        self.type: Literal["treasure", "golden_kappa", "regular"] = current["type"]
        self.top_contributions: list[HypeTrainContribution] = [
            HypeTrainContribution(c, http=http) for c in current["top_contributions"]
        ]
        self.all_time_high: HypeTrainAllTimeHigh | None = (
            HypeTrainAllTimeHigh(
                level=all_time_high["level"],
                total=all_time_high["total"],
                achieved_at=parse_timestamp(all_time_high["achieved_at"]),
            )
            if all_time_high is not None
            else None
        )
        self.shared_train: bool = current["is_shared_train"]
        self.shared_train_participants: list[PartialUser] = (
            [
                PartialUser(u["broadcaster_user_id"], u["broadcaster_user_login"], u["broadcaster_user_name"], http=http)
                for u in current["shared_train_participants"]
            ]
            if self.shared_train
            else []
        )
        self.shared_all_time_high: HypeTrainAllTimeHigh | None = (
            HypeTrainAllTimeHigh(
                level=shared_all_time_high["level"],
                total=shared_all_time_high["total"],
                achieved_at=parse_timestamp(shared_all_time_high["achieved_at"]),
            )
            if shared_all_time_high is not None
            else None
        )
