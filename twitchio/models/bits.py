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
        BitsLeaderboardResponse,
        BitsLeaderboardResponseData,
        CheermotesResponseData,
        CheermotesResponseTiers,
        ExtensionTransactionsResponseCost,
        ExtensionTransactionsResponseData,
        ExtensionTransactionsResponseProductData,
    )


__all__ = (
    "BitsLeaderboard",
    "BitLeaderboardUser",
    "CheerEmote",
    "CheerEmoteTier",
    "ExtensionTransaction",
    "ExtensionProductData",
    "ExtensionCost",
)


class BitsLeaderboard:
    """
    Represents a Bits leaderboard.

    Attributes
    ------------
    started_at: datetime.datetime | None
        The time the leaderboard started.
    ended_at: datetime.datetime | None
        The time the leaderboard ended.
    leaders: list[BitLeaderboardUser]
        The current leaders of the Leaderboard.
    """

    __slots__ = ("leaders", "started_at", "ended_at")

    def __init__(self, data: BitsLeaderboardResponse, *, http: HTTPClient) -> None:
        self.started_at = (
            parse_timestamp(data["date_range"]["started_at"]) if data["date_range"]["started_at"] else None
        )
        self.ended_at = parse_timestamp(data["date_range"]["ended_at"]) if data["date_range"]["ended_at"] else None
        self.leaders = [BitLeaderboardUser(d, http=http) for d in data["data"]]

    def __repr__(self) -> str:
        return f"<BitsLeaderboard started_at={self.started_at} ended_at={self.ended_at}>"


class BitLeaderboardUser:
    __slots__ = ("user", "rank", "score")

    def __init__(self, data: BitsLeaderboardResponseData, *, http: HTTPClient) -> None:
        self.user = PartialUser(data["user_id"], data["user_login"], http=http)
        self.rank: int = int(data["rank"])
        self.score: int = int(data["score"])

    def __repr__(self) -> str:
        return f"<BitLeaderboardUser user={self.user} rank={self.rank} score={self.score}>"


class CheerEmoteTier:
    """
    Represents a Cheer Emote tier.

    Attributes
    -----------
    min_bits: int
        The minimum bits for the tier
    id: str
        The ID of the tier
    colour: str
        The colour of the tier
    images: dict[str, dict[str, dict[str, str]]]
        contains two dicts, ``light`` and ``dark``. Each item will have an ``animated`` and ``static`` item,
        which will contain yet another dict, with sizes ``1``, ``1.5``, ``2``, ``3``, and ``4``.
        Ex. ``cheeremotetier.images["light"]["animated"]["1"]``
    can_cheer: bool
        Indicates whether emote information is accessible to users.
    show_in_bits_card: bool
        Indicates whether twitch hides the emote from the bits card.
    """

    __slots__ = "min_bits", "id", "color", "images", "can_cheer", "show_in_bits_card"

    def __init__(self, data: CheermotesResponseTiers) -> None:
        self.min_bits: int = data["min_bits"]
        self.id: str = data["id"]
        self.color: str = data["color"]
        self.images = data["images"]
        self.can_cheer: bool = data["can_cheer"]
        self.show_in_bits_card: bool = data["show_in_bits_card"]

    def __repr__(self) -> str:
        return f"<CheerEmoteTier id={self.id} min_bits={self.min_bits}>"


class CheerEmote:
    """
    Represents a Cheer Emote

    Attributes
    -----------
    prefix: str
        The string used to Cheer that precedes the Bits amount.
    tiers: CheerEmoteTier
        The tiers this Cheer Emote has
    type: str
        Shows whether the emote is ``global_first_party``, ``global_third_party``, ``channel_custom``, ``display_only``, or ``sponsored``.
    order: int
        Order of the emotes as shown in the bits card, in ascending order.
    last_updated datetime.datetime
        The date this cheermote was last updated.
    charitable: bool
        Indicates whether this emote provides a charity contribution match during charity campaigns.
    """

    __slots__ = (
        "_http",
        "prefix",
        "tiers",
        "type",
        "order",
        "last_updated",
        "charitable",
    )

    def __init__(self, data: CheermotesResponseData) -> None:
        self.prefix: str = data["prefix"]
        self.tiers = [CheerEmoteTier(d) for d in data["tiers"]]
        self.type: str = data["type"]
        self.order: int = int(data["order"])
        self.last_updated = parse_timestamp(data["last_updated"])
        self.charitable: bool = data["is_charitable"]

    def __repr__(self) -> str:
        return f"<CheerEmote prefix={self.prefix} type={self.type} order={self.order}>"


class ExtensionTransaction:
    """
    Represents an Extension Transaction.

    Attributes
    -----------
    id: str
        An ID that identifies the transaction.
    timestamp: datetime.datetime
        The UTC date and time of the transaction.
    broadcaster: twitchio.PartialUser
        The broadcaster that owns the channel where the transaction occurred.
    user: twitchio.PartialUser
        The user that purchased the digital product.
    product_type: str
        The type of transaction. Currently only ``BITS_IN_EXTENSION``
    product_data: twitchio.ExtensionProductData
        Details about the digital product.
    """

    __slots__ = ("id", "timestamp", "broadcaster", "user", "product_type", "product_data")

    def __init__(self, data: ExtensionTransactionsResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.timestamp: datetime.datetime = parse_timestamp(data["timestamp"])
        self.broadcaster = PartialUser(data["broadcaster_id"], data["broadcaster_login"], http=http)
        self.user = PartialUser(data["user_id"], data["user_login"], http=http)
        self.product_type: str = data["product_type"]
        self.product_data: ExtensionProductData = ExtensionProductData(data["product_data"])

    def __repr__(self) -> str:
        return f"<ExtensionTransaction id={self.id} timestamp={self.timestamp} product_type={self.product_type}>"


class ExtensionProductData:
    """
    Represents Product Data of an Extension Transaction.

    Attributes
    -----------
    domain: str
        Set to twitch.ext. + <the extension's ID>.
    sku: str
        An ID that identifies the digital product.
    cost: twitchio.ExtensionCost
        Contains details about the digital product's cost.
    in_development: bool
        Whether the product is in development.
    display_name: str
        The name of the digital product.
    expiration: str
        This field is always empty since you may purchase only unexpired products.
    broadcast: bool
        Whether the data was broadcast to all instances of the extension.
    """

    __slots__ = ("domain", "cost", "sku", "in_development", "display_name", "expiration", "broadcast")

    def __init__(self, data: ExtensionTransactionsResponseProductData) -> None:
        self.domain: str = data["domain"]
        self.sku: str = data["sku"]
        self.cost: ExtensionCost = ExtensionCost(data["cost"])
        self.in_development: bool = data["inDevelopment"]
        self.display_name: str = data["displayName"]
        self.expiration: str = data["expiration"]
        self.broadcast: bool = data["broadcast"]

    def __repr__(self) -> str:
        return f"<ExtensionProductData domain={self.domain} display_name={self.display_name} sku={self.sku}>"

    def __str__(self) -> str:
        return self.display_name


class ExtensionCost:
    """
    Represents Cost of an Extension Transaction.

    Attributes
    -----------
    amount: int
        The amount exchanged for the digital product.
    type: str
        The type of currency exchanged. Currently only ``bits``
    """

    __slots__ = ("amount", "type")

    def __init__(self, data: ExtensionTransactionsResponseCost) -> None:
        self.amount: int = int(data["amount"])
        self.type: str = data["type"]

    def __repr__(self) -> str:
        return f"<ExtensionCost amount={self.amount} type={self.type}>"

    def __str__(self) -> str:
        return str(self.amount)
