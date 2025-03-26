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

from twitchio.models.games import Game
from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import (
        DropsEntitlementsResponseData,
        GamesResponse,
        UpdateDropsEntitlementsResponseData,
    )


__all__ = ("Entitlement", "EntitlementStatus")


class Entitlement:
    """Represents a drops entitlement.

    Attributes
    -----------
    id: str
        An ID that identifies the entitlement.
    benefit_id: str
        An ID that identifies the benefit (reward).
    timestamp: datetime.datetime
        Datetime of when the entitlement was granted.
    user: PartialUser
        PartialUser of who was granted the entitlement.
    game_id: str
        An ID that identifies the game the user was playing when the reward was entitled.
    fulfillment_status: typing.Literal["CLAIMED", "FULFILLED"]
        The entitlement's fulfillment status. Can be either `CLAIMED` or `FULFILLED`.
    last_updated: datetime.datetime
        Datetime of when the entitlement was last updated.
    """

    __slots__ = (
        "_http",
        "benefit_id",
        "fulfillment_status",
        "game_id",
        "id",
        "last_updated",
        "timestamp",
        "user",
    )

    def __init__(self, data: DropsEntitlementsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.benefit_id: str = data["benefit_id"]
        self.timestamp: datetime.datetime = parse_timestamp(data["timestamp"])
        self.user: PartialUser = PartialUser(data["user_id"], None, http=http)
        self.game_id: str = data["game_id"]
        self.fulfillment_status: Literal["CLAIMED", "FULFILLED"] = data["fulfillment_status"]
        self.last_updated: datetime.datetime = parse_timestamp(data["last_updated"])

    def __repr__(self) -> str:
        return f"<Entitlement id={self.id} id={self.id} benefit_id={self.benefit_id}>"

    def __str__(self) -> str:
        return self.id

    async def fetch_game(self) -> Game | None:
        """|coro|

        Fetches the :class:`~twitchio.Game` associated with this drop entitlement.

        Returns
        -------
        Game | None
            The game associated with this drop entitlement.
        """
        payload: GamesResponse = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http) if payload["data"] else None


class EntitlementStatus:
    """The status of entitlements after an update.

    Attributes
    -----------
    status: typing.Literal["INVALID_ID", "NOT_FOUND", "SUCCESS", "UNAUTHORIZED", "UPDATE_FAILED"]
        Indicates whether the status of the entitlements in the ids field were successfully updated.

        +----------------+----------------------------------------------------------------------------------------------------+
        | Status         | Description                                                                                        |
        +================+====================================================================================================+
        | INVALID_ID     | The entitlement IDs in the ids field are not valid.                                                |
        +----------------+----------------------------------------------------------------------------------------------------+
        | NOT_FOUND      | The entitlement IDs in the ids field were not found.                                               |
        +----------------+----------------------------------------------------------------------------------------------------+
        | SUCCESS        | The status of the entitlements in the ids field were successfully updated.                         |
        +----------------+----------------------------------------------------------------------------------------------------+
        | UNAUTHORIZED   | The user or organization identified by the user access token is not authorized to update the       |
        |                | entitlements.                                                                                      |
        +----------------+----------------------------------------------------------------------------------------------------+
        | UPDATE_FAILED  | The update failed. These are considered transient errors and the request should be retried later.  |
        +----------------+----------------------------------------------------------------------------------------------------+

    ids: list[str]
        The list of entitlement ids that the status in the status field applies to.
    """

    def __init__(self, data: UpdateDropsEntitlementsResponseData) -> None:
        self.status: Literal["INVALID_ID", "NOT_FOUND", "SUCCESS", "UNAUTHORIZED", "UPDATE_FAILED"] = data["status"]
        self.ids: list[str] = data["ids"]

    def __repr__(self) -> str:
        return f"<EntitlementStatus status={self.status} ids={self.ids}>"
