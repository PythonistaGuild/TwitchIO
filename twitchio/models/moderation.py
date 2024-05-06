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

from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.types_.responses import CheckAutomodStatusResponseData

__all__ = ("AutoModStatus", "AutomodCheckMessage")


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
