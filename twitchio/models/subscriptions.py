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

from twitchio.types_.responses import (
    CheckUserSubscriptionResponseData,
)
from twitchio.user import PartialUser


if TYPE_CHECKING:
    from twitchio.http import HTTPAsyncIterator, HTTPClient
    from twitchio.types_.responses import (
        BroadcasterSubscriptionsResponse,
        BroadcasterSubscriptionsResponseData,
        CheckUserSubscriptionResponseData,
    )


__all__ = ("UserSubscription", "BroadcasterSubscription", "BroadcasterSubscriptions")


class UserSubscription:
    """
    Represents a subscription of a user.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster being subscribed to.
    gift: bool
        A Boolean value that determines whether the subscription is a gift subscription. Is True if the subscription was gifted.
    tier: int
        The type of subscription. Possible values are:

        - 1000: Tier 1
        - 2000: Tier 2
        - 3000: Tier 3
    gifter: PartialUser | None
        The user who gifted the subscription. This is None if `gift` is False.
    """

    __slots__ = (
        "broadcaster",
        "gifter",
        "gift",
        "tier",
    )

    def __init__(
        self, data: BroadcasterSubscriptionsResponseData | CheckUserSubscriptionResponseData, *, http: HTTPClient
    ) -> None:
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], data["broadcaster_login"], http=http)
        self.gift: bool = bool(data["is_gift"])
        self.tier: int = int(data["tier"])
        _gifter_id, _gifter_login = data.get("gifter_id"), data.get("gifter_login")
        self.gifter: PartialUser | None = (
            PartialUser(_gifter_id, _gifter_login, http=http) if self.gift and _gifter_id is not None else None
        )

    def __repr__(self) -> str:
        return f"<UserSubscription broadcaster={self.broadcaster} tier={self.tier} gift={self.gift}>"

    @property
    def rounded_tier(self) -> int:
        """
        Returns the tier as a single digit. e.g. Tier 1000 = 1.
        """
        return round(self.tier / 1000)


class BroadcasterSubscription(UserSubscription):
    """
    Represents a subscription of a user.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster being subscribed to.
    gift: bool
        A Boolean value that determines whether the subscription is a gift subscription. Is True if the subscription was gifted.
    tier: int
        The type of subscription. Possible values are:

        - 1000: Tier 1
        - 2000: Tier 2
        - 3000: Tier 3
    gifter: PartialUser | None
        The user who gifted the subscription. This is None if `gift` is False.
    plan_name: str
        The name of the subscription.
    user: PartialUser
        The subscribing user.
    """

    __slots__ = ("plan_name", "user")

    def __init__(self, data: BroadcasterSubscriptionsResponseData, *, http: HTTPClient) -> None:
        super().__init__(data, http=http)
        self.plan_name: str = data["plan_name"]
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<BroadcasterSubscription broadcaster={self.broadcaster} tier={self.tier} gift={self.gift} plan_name={self.plan_name}>"


class BroadcasterSubscriptions:
    """
    Represents all the users that subscribe to a broadcaster.

    Attributes
    ----------
    subscriptions: HTTPAsyncIterator[BroadcasterSubscription]
        HTTPAsyncIterator of [`BroadcasterSubscription`][] objects.
    total: int
        The total number of users that subscribe to this broadcaster.
    points: int
        The current number of subscriber points earned by this broadcaster.
        Points are based on the subscription tier of each user that subscribes to this broadcaster.

        For example, a Tier 1 subscription is worth 1 point, Tier 2 is worth 2 points, and Tier 3 is worth 6 points.
        The number of points determines the number of emote slots that are unlocked for the broadcaster (see [Subscriber Emote Slots](https://help.twitch.tv/s/article/subscriber-emote-guide#emoteslots)).
    """

    __slots__ = (
        "subscriptions",
        "total",
        "points",
    )

    def __init__(
        self, data: BroadcasterSubscriptionsResponse, iterator: HTTPAsyncIterator[BroadcasterSubscription]
    ) -> None:
        self.subscriptions: HTTPAsyncIterator[BroadcasterSubscription] = iterator
        self.total: int = data["total"]
        self.points: int = data["points"]

    def __repr__(self) -> str:
        return f"<BroadcasterSubscriptions total={self.total} points={self.points}>"
