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
    from twitchio.types_.responses import PollsResponseChoices, PollsResponseData

__all__ = ("Poll", "PollChoice")


class Poll:
    """Represents a Poll

    +-------------+--------------------------------------------------------------------+
    | Status      | Description                                                        |
    +=============+====================================================================+
    | ACTIVE      | The poll is running.                                               |
    +-------------+--------------------------------------------------------------------+
    | COMPLETED   | The poll ended on schedule.                                        |
    +-------------+--------------------------------------------------------------------+
    | TERMINATED  | The poll was terminated before its scheduled end.                  |
    +-------------+--------------------------------------------------------------------+
    | ARCHIVED    | The poll has been archived and is no longer visible on the channel.|
    +-------------+--------------------------------------------------------------------+
    | MODERATED   | The poll was deleted.                                              |
    +-------------+--------------------------------------------------------------------+
    | INVALID     | Something went wrong while determining the state.                  |
    +-------------+--------------------------------------------------------------------+

    Attributes
    ----------
    id: str
        An ID that identifies the poll.
    broadcaster: PartialUser
        The broadcaster that created the poll.
    title: str
        The question that viewers are voting on.
    choices: list[PollChoice]
        A list of choices that viewers can choose from. The list will contain a minimum of two choices and up to a maximum of five choices.
    channel_points_voting_enabled: bool
        A Boolean value that indicates whether viewers may cast additional votes using Channel Points.
    channel_points_per_vote: int
        The number of points the viewer must spend to cast one additional vote.
    status: Literal["ACTIVE", "COMPLETED", "TERMINATED", "ARCHIVED", "MODERATED", "INVALID"]
        The poll's status. Valid values are `ACTIVE`, `COMPLETED`, `TERMINATED`, `ARCHIVED`, `MODERATED` and `INVALID`.
    duration: int
        The length of time (in seconds) that the poll will run for.
    started_at: datetime.datetime
        The datetime of when the poll began.
    ended_at: datetime.datetime | None
        The datetime of when the poll ended. This is None if status is ``ACTIVE``.
    """

    __slots__ = (
        "_http",
        "id",
        "broadcaster",
        "title",
        "choices",
        "channel_points_voting_enabled",
        "channel_points_per_vote",
        "status",
        "duration",
        "started_at",
        "ended_at",
    )

    def __init__(self, data: PollsResponseData, *, http: HTTPClient) -> None:
        self._http = http
        self.id: str = data["id"]
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], data["broadcaster_login"], http=http)
        self.title: str = data["title"]
        self.choices: list[PollChoice] = [PollChoice(c) for c in data["choices"]]
        self.channel_points_voting_enabled: bool = bool(data["channel_points_voting_enabled"])
        self.channel_points_per_vote: int = int(data["channel_points_per_vote"])
        self.status: Literal["ACTIVE", "COMPLETED", "TERMINATED", "ARCHIVED", "MODERATED", "INVALID"] = data["status"]
        self.duration: int = int(data["duration"])
        self.started_at: datetime.datetime = parse_timestamp(data["started_at"])
        _ended_at = data.get("ended_at")
        self.ended_at: datetime.datetime | None = parse_timestamp(_ended_at) if _ended_at else None

    def __repr__(self) -> str:
        return f"<Poll id={self.id} title={self.title} status={self.status} started_at={self.started_at}>"

    async def end_poll(self, *, status: Literal["ARCHIVED", "TERMINATED"], token_for: str) -> Poll:
        """End an active poll.

        Parameters
        ----------
        status  Literal["ARCHIVED", "TERMINATED"]
            The status to set the poll to. Possible case-sensitive values are: "ARCHIVED" and "TERMINATED".
        token_for: str
            User access token that includes the `channel:manage:polls` scope.

        Returns
        -------
        Poll
            A Poll object.
        """
        data = await self._http.patch_poll(
            broadcaster_id=self.broadcaster.id, id=self.id, status=status, token_for=token_for
        )
        return Poll(data["data"][0], http=self._http)


class PollChoice:
    """Represents a poll choice.

    Attributes
    ----------
    id: str
        An ID that identifies the choice.
    title: str
        The choice's title.
    votes: int
        The total number of votes cast for this choice.
    channel_points_votes: int
        The number of votes cast using Channel Points.
    """

    __slots__ = ("id", "title", "votes", "channel_points_votes")

    def __init__(self, data: PollsResponseChoices) -> None:
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.votes: int = int(data["votes"])
        self.channel_points_votes: int = int(data["channel_points_votes"])

    def __repr__(self) -> str:
        return f"<PollChoice id={self.id} title={self.title} votes={self.votes} channel_points_votes={self.channel_points_votes}>"
