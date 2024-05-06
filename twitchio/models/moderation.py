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


if TYPE_CHECKING:
    from twitchio.http import HTTPClient
    from twitchio.types_.responses import AutomodSettingsResponseData, CheckAutomodStatusResponseData

__all__ = ("AutomodSettings", "AutoModStatus", "AutomodCheckMessage")


class AutoModStatus:
    """
    Represents a raid for a broadcaster / channel

    Attributes
    -----------
    msg_id: str
        A caller-defined ID passed in the request.
    permitted: bool
        A Boolean value that indicates whether Twitch would approve the message for chat or hold it for moderator review or block it from chat.
        Is True if Twitch would approve the message; otherwise, False if Twitch would hold the message for moderator review or block it from chat.
    """

    __slots__ = ("msg_id", "permitted")

    def __init__(self, data: CheckAutomodStatusResponseData) -> None:
        self.msg_id: str = data["msg_id"]
        self.permitted: bool = data["is_permitted"]

    def __repr__(self) -> str:
        return f"<AutoModStatus msg_id={self.msg_id} permitted={self.permitted}>"


class AutomodCheckMessage:
    """
    Represents the message to check with automod

    Attributes
    -----------
    id: str
        Developer-generated identifier for mapping messages to results.
    text: str
        Message text.
    """

    __slots__ = ("id", "text")

    def __init__(self, id: str, text: str) -> None:
        self.id = id
        self.text = text

    def _to_dict(self) -> dict[str, str]:
        return {"msg_id": self.id, "msg_text": self.text}

    def __repr__(self) -> str:
        return f"<AutomodCheckMessage id={self.id} text={self.text}>"


class AutomodSettings:
    """
    Represents the AutoMod Settings of a broadcaster's chat room.

    Attributes
    -----------
    broadcaster: PartialUser
        The PartialUser instance representing the broadcaster.
    moderator: PartialUser
        The PartialUser instance representing the moderator.
    overall_level: int | None
        The overall moderation level, which could be None if the broadcaster has set one or more of the individual settings.
    disability: int
        The Automod level for discrimination against disability.
    aggression: int
        The Automod level for hostility involving aggression.
    sexuality_sex_or_gender : int
        The AutoMod level for discrimination based on sexuality, sex, or gender.
    misogyny: int
        The Automod level for discrimination against women.
    bullying: int
        The Automod level for hostility involving name calling or insults.
    swearing: int
        The Automod level for profanity.
    race_ethnicity_or_religion: int
        The Automod level for racial discrimination.
    sex_based_terms: int
        The Automod level for sexual content.

    """

    __slots__ = (
        "broadcaster",
        "moderator",
        "overall_level",
        "disability",
        "aggression",
        "sexuality_sex_or_gender",
        "misogyny",
        "bullying",
        "swearing",
        "race_ethnicity_or_religion",
        "sex_based_terms",
    )

    def __init__(self, data: AutomodSettingsResponseData, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], None, http=http)
        self.moderator: PartialUser = PartialUser(data["moderator_id"], None, http=http)
        self.overall_level: int | None = int(data["overall_level"]) if data["overall_level"] else None
        self.disability: int = data["disability"]
        self.aggression: int = data["aggression"]
        self.sexuality_sex_or_gender: int = data["sexuality_sex_or_gender"]
        self.misogyny: int = data["misogyny"]
        self.bullying: int = data["bullying"]
        self.swearing: int = data["swearing"]
        self.race_ethnicity_or_religion: int = data["race_ethnicity_or_religion"]
        self.sex_based_terms: int = data["sex_based_terms"]

    def __repr__(self) -> str:
        return f"<AutomodSettings broadcaster={self.broadcaster} moderator={self.moderator} overall_level={self.overall_level}>"
