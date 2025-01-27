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


if TYPE_CHECKING:
    from twitchio.http import HTTPClient
    from twitchio.types_.responses import GamesResponseData


__all__ = ("Game",)


class Game:
    """Represents a Game on Twitch.

    You can retrieve a game by its ID, name or IGDB ID using the :meth:`~twitchio.Client.fetch_games`
    method or the various ``.fetch_game()`` methods of other models.

    To fetch a list of games, see: :meth:`~twitchio.Client.fetch_games`

    Supported Operations
    --------------------

    +-------------+----------------------------------+----------------------------------------------------+
    | Operation   | Usage(s)                        | Description                                         |
    +=============+==================================+====================================================+
    | __str__     | str(game), f"{game}"             | Returns the games name.                            |
    +-------------+----------------------------------+----------------------------------------------------+
    | __repr__    | repr(game), f"{game!r}"          | Returns the games official representation.         |
    +-------------+----------------------------------+----------------------------------------------------+
    | __eq__      | game == game2, game != game2     | Checks if two games are equal.                     |
    +-------------+----------------------------------+----------------------------------------------------+


    Attributes
    ----------
    id: str
        The ID of the game provided by Twitch.
    name: str
        The name of the game.
    box_art: Asset
        The box art of the game as an :class:`~twitchio.Assets`.
    igdb_id: str | None
        The IGDB ID of the game. If this is not available to Twitch it will be ``None``.
    """

    __slots__ = ("box_art", "id", "igdb_id", "name")

    def __init__(self, data: GamesResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.igdb_id: str | None = data.get("igdb_id", None)
        self.box_art: Asset = Asset(data["box_art_url"], http=http, dimensions=(1080, 1440))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Game id={self.id} name={self.name}>"

    def __eq__(self, __value: object) -> bool:
        return __value.id == self.id if isinstance(__value, Game) else NotImplemented
