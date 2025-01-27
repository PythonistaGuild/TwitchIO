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
    from twitchio.types_.responses import CreatorGoalsResponseData

__all__ = ("Goal",)


class Goal:
    """Represents a broadcaster's goal.

    The goal's ``type`` determines how the ``current_target`` is increased or decreased.

    - If type is ``follower``, this field is set to the broadcaster's current number of followers. This number increases with new followers and decreases when users unfollow the broadcaster.

    - If type is ``subscription``, this field is increased and decreased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased or decreased by 2, not 1.

    - If type is ``subscription_count``, this field is increased by 1 for each new subscription and decreased by 1 for each user that unsubscribes.

    - If type is ``new_subscription``, this field is increased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased by 2, not 1.

    - If type is ``new_subscription_count``, this field is increased by 1 for each new subscription.

    +------------------------+-----------------------------------------------------------------------------------------------------------------------+
    | Type                   | Description                                                                                                           |
    +========================+=======================================================================================================================+
    | follower               | The goal is to increase followers.                                                                                    |
    +------------------------+-----------------------------------------------------------------------------------------------------------------------+
    | subscription           | The goal is to increase subscriptions. This type shows the net increase or decrease in tier points associated with    |
    |                        | the subscriptions.                                                                                                    |
    +------------------------+-----------------------------------------------------------------------------------------------------------------------+
    | subscription_count     | The goal is to increase subscriptions. This type shows the net increase or decrease in the number of subscriptions.   |
    +------------------------+-----------------------------------------------------------------------------------------------------------------------+
    | new_subscription       | The goal is to increase subscriptions. This type shows only the net increase in tier points associated with the       |
    |                        | subscriptions (it does not account for users that unsubscribed since the goal started).                               |
    +------------------------+-----------------------------------------------------------------------------------------------------------------------+
    | new_subscription_count | The goal is to increase subscriptions. This type shows only the net increase in the number of subscriptions (it does  |
    |                        | not account for users that unsubscribed since the goal started).                                                      |
    +------------------------+-----------------------------------------------------------------------------------------------------------------------+

    Attributes
    -----------
    id: str
        An ID that identifies this goal.
    broadcaster: PartialUser
        The broadcaster that created the goal.
    type: typing.Literal["follower", "subscription", "subscription_count", "new_subscription", "new_subscription_count"]
        The type of goal. Possible values are: `follower`, `subscription`, `subscription_count`, `new_subscription`, `new_subscription_count`
        Please refer to the documentation for more details.
    description: str
        A description of the goal. Is an empty string if not specified.
    current_amount: int
        The goal's current value.
    target_amount: int
        The goal's target value. For example, if the broadcaster has 200 followers before creating the goal, and their goal is to double that number, this field is set to 400.
    created_at: datetime.datetime
        The datetime that the broadcaster created the goal.

    """

    __slots__ = ("broadcaster", "created_at", "current_amount", "description", "id", "target_amount", "type")

    def __init__(self, data: CreatorGoalsResponseData, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.broadcaster: PartialUser = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=http
        )
        self.type: Literal[
            "follower", "subscription", "subscription_count", "new_subscription", "new_subscription_count"
        ] = data["type"]
        self.description: str = data["description"]
        self.current_amount: int = data["current_amount"]
        self.target_amount: int = data["target_amount"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self) -> str:
        return f"<Goal id={self.id} type={self.type} description={self.description}>"
