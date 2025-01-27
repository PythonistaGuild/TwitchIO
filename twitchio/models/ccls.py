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


if TYPE_CHECKING:
    from twitchio.types_.responses import ContentClassificationLabelData


__all__ = ("ContentClassificationLabel",)


class ContentClassificationLabel:
    """Represents a Content Classification Label.

    Attributes
    -----------
    id: str
        Unique identifier for the CCL.
    description: str
        Localized description of the CCL.
    name: str
        Localized name of the CCL.
    """

    __slots__ = ("description", "id", "name")

    def __init__(self, data: ContentClassificationLabelData) -> None:
        self.id: str = data["id"]
        self.description: str = data["description"]
        self.name: str = data["name"]

    def __repr__(self) -> str:
        return f"<ContentClassificationLabel id={self.id}>"
