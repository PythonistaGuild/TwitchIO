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
        AutomodSettingsResponseData,
        BannedUsersResponseData,
        BanUserResponseData,
        CheckAutomodStatusResponseData,
    )

__all__ = ("AutomodSettings", "AutoModStatus", "AutomodCheckMessage", "Ban", "BannedUser", "Timeout")


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
    Represents the AutoModSettings of a broadcaster's chat room.

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

    def to_dict(self, use_ids: bool = False) -> dict[str, str | int | None]:
        """
        Returns the AutomodSettings as a dictionary. This is the equivalent of the raw payload returned by Twitch.

        Parameters
        ----------
        use_ids : bool
            Whether to include the broadcaster and moderator IDs in the dictionary.

        Returns
        -------
        dict[str, str | int | None]
            Dictionary data type of AutomodSettings
        """
        result: dict[str, str | int | None] = {}
        user_related = {"broadcaster", "moderator"}

        if use_ids:
            for user_attr in user_related:
                user = getattr(self, user_attr, None)
                result[f"{user_attr}_id"] = getattr(user, "id", None) if user else None

        for attribute in self.__slots__:
            if attribute in user_related and not use_ids:
                continue
            attr_value = getattr(self, attribute, None)
            if attr_value is not None and hasattr(attr_value, "to_dict"):
                result[attribute] = attr_value.to_dict()
            elif attribute not in user_related:
                result[attribute] = attr_value

        return result


class BannedUser:
    """
    Represents a BannedUser.

    Attributes
    ----------
    user: PartialUser
        The user banned or timed out.
    moderator: PartialUser
        The moderator who banned or put the user in timeout.
    expires_at: datetime.datetime | None
        Datetime of when the timeout will end. This is None if permanently banned.
    created_at: datetime.datetime
        Datetime of when the user was banned.
    reason: str
        The reason the user was banned or put in a timeout if the moderator provided one.
    """

    __slots__ = ("user", "expires_at", "created_at", "moderator", "reason")

    def __init__(self, data: BannedUsersResponseData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.moderator: PartialUser = PartialUser(data["moderator_id"], data["moderator_login"], http=http)
        self.expires_at: datetime.datetime | None = parse_timestamp(data["expires_at"]) if data["expires_at"] else None
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.reason: str = data["reason"]

    def __repr__(self) -> str:
        return f"<BannedUser user={self.user} created_at={self.created_at} expires_at={self.expires_at}>"


class Ban:
    """
    Represents a Ban.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose chat room the user was banned from chatting in.
    user: PartialUser
        The user banned or timed out.
    moderator: PartialUser
        The moderator who banned or put the user in timeout.
    created_at: datetime.datetime
        Datetime of when the user was banned.
    """

    __slots__ = ("broadcaster", "user", "end_time", "created_at", "moderator")

    def __init__(self, data: BanUserResponseData, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], None, http=http)
        self.user: PartialUser = PartialUser(data["user_id"], None, http=http)
        self.moderator: PartialUser = PartialUser(data["moderator_id"], None, http=http)
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self) -> str:
        return f"<BanEvent user={self.user} created_at={self.created_at} end_time={self.end_time}>"


class Timeout:
    """
    Represents a Timeout.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose chat room the user was timed out from chatting in.
    user: PartialUser
        The user timed out.
    moderator: PartialUser
        The moderator who put the user in timeout.
    end_time: datetime.datetime
        Datetime of when the timeout will end.
    created_at: datetime.datetime
        Datetime of when the user was timed out.
    """

    __slots__ = ("broadcaster", "user", "end_time", "created_at", "moderator")

    def __init__(self, data: BanUserResponseData, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], None, http=http)
        self.user: PartialUser = PartialUser(data["user_id"], None, http=http)
        self.moderator: PartialUser = PartialUser(data["moderator_id"], None, http=http)
        self.end_time: datetime.datetime | None = parse_timestamp(data["end_time"]) if data["end_time"] else None
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self) -> str:
        return f"<BanEvent user={self.user} created_at={self.created_at} end_time={self.end_time}>"
