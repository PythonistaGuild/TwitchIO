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

from twitchio.assets import Asset
from twitchio.user import PartialUser
from twitchio.utils import Colour, parse_timestamp


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
    "BitLeaderboardUser",
    "BitsLeaderboard",
    "Cheermote",
    "CheermoteTier",
    "ExtensionCost",
    "ExtensionProductData",
    "ExtensionTransaction",
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
    total: int
        The number of ranked users. This is the value in the count query parameter or the total number of entries on the leaderboard, whichever is less.
    """

    __slots__ = ("ended_at", "leaders", "started_at", "total")

    def __init__(self, data: BitsLeaderboardResponse, *, http: HTTPClient) -> None:
        self.started_at = parse_timestamp(data["date_range"]["started_at"]) if data["date_range"]["started_at"] else None
        self.ended_at = parse_timestamp(data["date_range"]["ended_at"]) if data["date_range"]["ended_at"] else None
        self.leaders = [BitLeaderboardUser(d, http=http) for d in data["data"]]
        self.total: int = int(data["total"])

    def __repr__(self) -> str:
        return f"<BitsLeaderboard started_at={self.started_at} ended_at={self.ended_at} total={self.total}>"


class BitLeaderboardUser:
    """A user's details within the Bit Leaderboard.

    Attributes
    ------------
    user: PartialUser
        The user.
    rank: int
        The user's position on the leaderboard.
    score: int
        The number of Bits the user has cheered.
    """

    __slots__ = ("rank", "score", "user")

    def __init__(self, data: BitsLeaderboardResponseData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.rank: int = int(data["rank"])
        self.score: int = int(data["score"])

    def __repr__(self) -> str:
        return f"<BitLeaderboardUser user={self.user} rank={self.rank} score={self.score}>"


class CheermoteTier:
    """Represents a Cheermote tier.

    Attributes
    -----------
    min_bits: int
        The minimum bits for the tier
    id: str
        The ID of the tier
    colour: Colour
        The :class:`~twitchio.utils.Colour` of the tier. There is an alias named ``color``.
    images: dict[str, dict[str, dict[str, str]]]
        contains two dicts, ``light`` and ``dark``. Each item will have an ``animated`` and ``static`` item,
        which will contain yet another dict, with sizes ``1``, ``1.5``, ``2``, ``3``, and ``4``.
        Ex. ``cheermotetier.images["light"]["animated"]["1"]``
    can_cheer: bool
        Indicates whether emote information is accessible to users.
    show_in_bits_card: bool
        Indicates whether twitch hides the emote from the bits card.
    """

    __slots__ = ("_http", "can_cheer", "color", "colour", "id", "images", "min_bits", "show_in_bits_card")

    def __init__(self, data: CheermotesResponseTiers, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.min_bits: int = data["min_bits"]
        self.id: str = data["id"]
        self.colour: Colour = Colour.from_hex(data["color"])
        self.color = self.colour
        self.images = data["images"]
        self.can_cheer: bool = data["can_cheer"]
        self.show_in_bits_card: bool = data["show_in_bits_card"]

    def __repr__(self) -> str:
        return f"<CheermoteTier id={self.id} min_bits={self.min_bits}>"

    def get_image(
        self,
        *,
        theme: Literal["light", "dark"] = "light",
        scale: Literal["1", "1.5", "2", "3", "4"] = "2",
        format: Literal["default", "static", "animated"] = "default",
    ) -> Asset | None:
        """Creates an :class:`~twitchio.Asset` for the cheermote, which can be used to download/save the cheermote image.

        Parameters
        ----------
        theme: typing.Literal["light", "dark"]
            The background theme of the cheermote. Defaults to "light".
        scale: str
            The scale (size) of the cheermote. Usually this will be one of: "1", "1.5", "2", "3", "4"
            Defaults to "2".
        format: typing.Literal["default", "static", "animated"]
            The format of the image for the cheermote. E.g a static image (PNG) or animated (GIF).

            Use "default" to get the default format for the emote, which will be animated if available, otherwise static.
            Defaults to "default".

        Examples
        --------
        .. code:: python3

            cheermotes: list[twitchio.Cheermote] = await client.fetch_cheermotes()
            cheermote: twitchio.Cheermote = cheermotes[0]

            # Get and save the emote asset as an image
            asset: twitchio.Asset = await cheeremote.tiers[0].get_image()
            await asset.save()

        Returns
        -------
        Asset | None
            The :class:`~twitchio.Asset` for the cheermote.
            You can use the asset to :meth:`~twitchio.Asset.read` or :meth:`~twitchio.Asset.save` the cheermote image or
            return the generated URL with :attr:`~twitchio.Asset.url`.
        """
        theme_images = self.images.get(theme, self.images.get("light", {}))
        format_images = theme_images.get("animated" if format in ("animated", "default") else "static", {})
        image_url = format_images.get(scale)

        if image_url is None:
            for format_type in ("animated", "static"):
                if theme_images.get(format_type):
                    image_url = next(iter(theme_images[format_type].values()), None)
                    if image_url:
                        break

        return None if image_url is None else Asset(image_url, http=self._http)


class Cheermote:
    """Represents a Cheermote

    +---------------------+------------------------------------------------------------------------------------------------------------------------+
    | Type                | Description                                                                                                            |
    +=====================+========================================================================================================================+
    | global_first_party  | A Twitch-defined Cheermote that is shown in the Bits card.                                                             |
    +---------------------+------------------------------------------------------------------------------------------------------------------------+
    | global_third_party  | A Twitch-defined Cheermote that is not shown in the Bits card.                                                         |
    +---------------------+------------------------------------------------------------------------------------------------------------------------+
    | channel_custom      | A broadcaster-defined Cheermote.                                                                                       |
    +---------------------+------------------------------------------------------------------------------------------------------------------------+
    | display_only        | Do not use; for internal use only.                                                                                     |
    +---------------------+------------------------------------------------------------------------------------------------------------------------+
    | sponsored           | A sponsor-defined Cheermote. When used, the sponsor adds additional Bits to the amount that the user cheered. For      |
    |                     | example, if the user cheered Terminator100, the broadcaster might receive 110 Bits, which includes the sponsor's 10    |
    |                     | Bits contribution.                                                                                                     |
    +---------------------+------------------------------------------------------------------------------------------------------------------------+

    Attributes
    -----------
    prefix: str
        The string used to Cheer that precedes the Bits amount.
    tiers: CheermoteTier
        The tiers this Cheermote has
    type: str
        Shows whether the emote is ``global_first_party``, ``global_third_party``, ``channel_custom``, ``display_only``, or ``sponsored``.
    order: int
        Order of the cheermotes as shown in the bits card, in ascending order.
    last_updated datetime.datetime
        The date this cheermote was last updated.
    charitable: bool
        Indicates whether this emote provides a charity contribution match during charity campaigns.
    """

    __slots__ = (
        "_http",
        "charitable",
        "last_updated",
        "order",
        "prefix",
        "tiers",
        "type",
    )

    def __init__(self, data: CheermotesResponseData, *, http: HTTPClient) -> None:
        self.prefix: str = data["prefix"]
        self.tiers = [CheermoteTier(d, http=http) for d in data["tiers"]]
        self.type: str = data["type"]
        self.order: int = int(data["order"])
        self.last_updated = parse_timestamp(data["last_updated"])
        self.charitable: bool = data["is_charitable"]

    def __repr__(self) -> str:
        return f"<Cheermote prefix={self.prefix} type={self.type} order={self.order}>"


class ExtensionTransaction:
    """Represents an Extension Transaction.

    Attributes
    -----------
    id: str
        An ID that identifies the transaction.
    timestamp: datetime.datetime
        The UTC date and time of the transaction.
    broadcaster: PartialUser
        The broadcaster that owns the channel where the transaction occurred.
    user: PartialUser
        The user that purchased the digital product.
    product_type: str
        The type of transaction. Currently only ``BITS_IN_EXTENSION``
    product_data: ExtensionProductData
        Details about the digital product.
    """

    __slots__ = ("broadcaster", "id", "product_data", "product_type", "timestamp", "user")

    def __init__(self, data: ExtensionTransactionsResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.timestamp: datetime.datetime = parse_timestamp(data["timestamp"])
        self.broadcaster = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=http
        )
        self.user = PartialUser(data["user_id"], data["user_login"], http=http)
        self.product_type: str = data["product_type"]
        self.product_data: ExtensionProductData = ExtensionProductData(data["product_data"])

    def __repr__(self) -> str:
        return f"<ExtensionTransaction id={self.id} timestamp={self.timestamp} product_type={self.product_type}>"


class ExtensionProductData:
    """Represents Product Data of an Extension Transaction.

    Attributes
    -----------
    domain: str
        Set to twitch.ext. + <the extension's ID>.
    sku: str
        An ID that identifies the digital product.
    cost: ExtensionCost
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

    __slots__ = ("broadcast", "cost", "display_name", "domain", "expiration", "in_development", "sku")

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
    """Represents Cost of an Extension Transaction.

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
