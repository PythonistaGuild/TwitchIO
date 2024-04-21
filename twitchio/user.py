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

from .models_test.channel_points import CustomReward


if TYPE_CHECKING:
    from .http import HTTPClient

__all__ = ("PartialUser",)


class PartialUser:
    """
    A class that contains minimal data about a user from the API.

    Attributes
    -----------
    id: :class:`str`
        The user's ID.
    name: Optional[:class:`str`]
        The user's name. In most cases, this is provided. There are however, rare cases where it is not.
    """

    __slots__ = "id", "name", "_http", "_cached_rewards"

    def __init__(self, id: int | str, name: str | None = None, *, http: HTTPClient) -> None:
        self._http = http
        self.id = str(id)
        self.name = name

    def __repr__(self) -> str:
        return f"<PartialUser id={self.id}, name={self.name}>"

    async def fetch_custom_reward(self, token_for: str) -> CustomReward:
        data = await self._http.get_custom_reward(broadcaster_id=self.id, token_for=token_for)
        return CustomReward(data["data"][0], http=self._http)
