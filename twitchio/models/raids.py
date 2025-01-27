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

    from twitchio.types_.responses import StartARaidResponseData

__all__ = ("Raid",)


class Raid:
    """Represents a raid for a broadcaster / channel

    Attributes
    -----------
    created_at: datetime.datetime
        Datetime of when the raid started.
    mature: bool
        Indicates whether the stream being raided is marked as mature.
    """

    __slots__ = ("created_at", "mature")

    def __init__(self, data: StartARaidResponseData) -> None:
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.mature: bool = data["is_mature"]

    def __repr__(self) -> str:
        return f"<Raid created_at={self.created_at} mature={self.mature}>"
