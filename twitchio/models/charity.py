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

from twitchio.assets import Asset
from twitchio.user import PartialUser


if TYPE_CHECKING:
    from ..http import HTTPClient
    from ..types_.eventsub import ChatCharityAmountData
    from ..types_.responses import (
        CharityCampaignDonationsResponseAmount,
        CharityCampaignDonationsResponseData,
        CharityCampaignResponseCurrentAmount,
        CharityCampaignResponseData,
        CharityCampaignResponseTargetAmount,
    )


__all__ = ("CharityCampaign", "CharityDonation", "CharityValues")


class CharityCampaign:
    """Represents a charity campaign.

    Attributes
    -----------
    id: str
        An ID that identifies the charity campaign.
    broadcaster: PartialUser
        The broadcaster that's running the campaign.
    name: str
        The charity's name.
    description: str
        A description of the charity.
    logo: Asset
        A logo for the charity campaign that is of size 100px X 100px.
    website: str
        A URL to the charity's website.
    current_amount: CharityValues
        The current amount of donations that the campaign has received.
    target_amount: CharityValues | None
        The campaign's fundraising goal. This is None if the broadcaster has not defined a fundraising goal.
    """

    __slots__ = ("broadcaster", "current_amount", "description", "id", "logo", "name", "target_amount", "website")

    def __init__(self, data: CharityCampaignResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.broadcaster: PartialUser = PartialUser(
            data["broadcaster_id"], data["broadcaster_login"], data["broadcaster_name"], http=http
        )
        self.name: str = data["charity_name"]
        self.description: str = data["charity_description"]
        self.logo: Asset = Asset(data["charity_logo"], http=http, dimensions=(100, 100))
        self.website: str = data["charity_website"]
        self.current_amount: CharityValues = CharityValues(data["current_amount"])
        self.target_amount: CharityValues | None = CharityValues(data["target_amount"]) if data["target_amount"] else None


class CharityValues:
    """Represents the current/target funds of a charity campaign.

    Attributes
    -----------
    value: int
        The monetary amount. The amount is specified in the currency's minor unit.
        For example, the minor units for USD is cents, so if the amount is $5.50 USD, value is set to 550.
    decimal_places: int
        The number of decimal places used by the currency.
    currency: str
        The currency this charity is raising funds in. eg ``USD``, ``GBP``, ``EUR``.
    """

    __slots__ = ("currency", "decimal_places", "value")

    def __init__(
        self,
        data: CharityCampaignResponseCurrentAmount
        | CharityCampaignResponseTargetAmount
        | CharityCampaignDonationsResponseAmount
        | ChatCharityAmountData,
    ) -> None:
        self.value: int = int(data["value"])
        decimal_places: int = data.get("decimal_places") or data.get("decimal_place", 0)
        self.decimal_places: int = decimal_places
        self.currency: str = data["currency"]

    def __repr__(self) -> str:
        return f"<CharityValues value={self.value} decimal_places={self.decimal_places} currency={self.currency}>"

    @property
    def decimal_value(self) -> str:
        """Returns the value in decimal format with 2 decimal places."""
        return format(self.value / 10**self.decimal_places, ".2f")


class CharityDonation:
    """Represents a charity campaign donation.

    Attributes
    -----------
    id: str
        An ID that identifies the donation. The ID is unique across campaigns.
    user: PartialUser
        The user who donated money to the campaign.
    campaign_id: str
        The ID of the charity campaign that the donation applies to.
    amount: str
        The the amount of money that the user donated.
    """

    __slots__ = ("_http", "amount", "campaign_id", "id", "user")

    def __init__(self, data: CharityCampaignDonationsResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.campaign_id: str = data["campaign_id"]
        self.amount: CharityValues = CharityValues(data["amount"])
