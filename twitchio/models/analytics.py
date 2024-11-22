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

    from twitchio.types_.responses import ExtensionAnalyticsResponseData, GameAnalyticsResponseData

__all__ = ("ExtensionAnalytics", "GameAnalytics")


class AnalyticsBase:
    """Base class for analytics.

    Attributes
    ----------
    id: str
        An ID that identifies the report's subject.
    url: str
        The URL to download the report.
    type: str
        The type of report.
    started_at: datetime.datetime
        The start date of the reporting window.
    ended_at: datetime.datetime
        The end date of the reporting window.
    """

    __slots__ = ("ended_at", "id", "started_at", "type", "url")

    def __init__(self, data: ExtensionAnalyticsResponseData | GameAnalyticsResponseData, *, id_field: str) -> None:
        self.id: str = data[id_field]
        self.url: str = data["URL"]
        self.type: str = data["type"]
        self.started_at: datetime.datetime = parse_timestamp(data["date_range"]["started_at"])
        self.ended_at: datetime.datetime = parse_timestamp(data["date_range"]["ended_at"])

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} type={self.type} started_at={self.started_at} ended_at={self.ended_at}>"


class ExtensionAnalytics(AnalyticsBase):
    """Represents Extension Analytics.

    Attributes
    ----------
    id: str
        An ID that identifies the extension that the report was generated for.
    url: str
        The URL to download the report.
    type: str
        The type of report.
    started_at: datetime.datetime
        The start date of the reporting window.
    ended_at: datetime.datetime
        The end date of the reporting window.
    """

    def __init__(self, data: ExtensionAnalyticsResponseData) -> None:
        super().__init__(data, id_field="extension_id")


class GameAnalytics(AnalyticsBase):
    """Represents Game Analytics.

    Attributes
    ----------
    id: str
        An ID that identifies the game that the report was generated for.
    url: str
        The URL to download the report.
    type: str
        The type of report.
    started_at: datetime.datetime
        The start date of the reporting window.
    ended_at: datetime.datetime
        The end date of the reporting window.
    """

    def __init__(self, data: GameAnalyticsResponseData) -> None:
        super().__init__(data, id_field="game_id")
