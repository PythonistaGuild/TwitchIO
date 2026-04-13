"""MIT License

Copyright (c) 2025 - Present Evie. P., Chillymosh and TwitchIO

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

import copy
import urllib.parse
from typing import TYPE_CHECKING, ClassVar

from ..exceptions import *
from ..utils import MISSING


if TYPE_CHECKING:
    from ..types_.http import HTTPMethodT, ParamMappingT


class Route:
    API_URL: ClassVar[str] = "https://api.twitch.tv/helix/"
    ID_URL: ClassVar[str] = "https://id.twitch.tv/"

    method: HTTPMethodT
    path: str

    def __init__(
        self,
        path: str,
        /,
        method: HTTPMethodT = MISSING,
        cli: bool = False,
        url: str | None = None,
        use_id: bool = False,
        params: ParamMappingT | None = None,
        data: ... = None,  # TODO: ...
    ) -> None:
        self._path = path
        self._method = method if method is not MISSING else "GET"
        self._cli = cli

        if cli and not url:
            raise MissingCLIParamError("Excpected the 'url' parameter when 'cli' is set.")

        self._is_id = use_id
        self._base_url = url or (self.API_URL if not use_id else self.ID_URL)
        self._params = params

        self._data = data  # TODO: ...
        self._url: str | None = self.format_url()

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"Route(method={self._method}, url={self._url}, cli={self._cli})"

    @property
    def cli(self) -> bool:
        return self._cli

    debug = cli

    @property
    def is_id(self) -> bool:
        return self._is_id

    @property
    def url(self) -> str | None:
        self._url

    @classmethod
    def encode(cls, value: str, /, safe: str = "", plus: bool = False) -> str:
        method = urllib.parse.quote_plus if plus else urllib.parse.quote
        unquote = urllib.parse.unquote_plus if plus else urllib.parse.unquote

        return method(value, safe=safe) if unquote(value) == value else value

    def format_url(self, *, remove_none: bool = False, duplicates: bool = True) -> str:
        self._path = self._path.lstrip("/").rstrip("/").strip()
        url = f"{self._base_url}{self._path}"

        if not self._params:
            return url

        url += "?"

        # We expect a dict so keys should be unique...
        for key, value in copy.copy(self._params).items():
            if value is None:
                if remove_none:
                    del self._params[key]
                continue

            if isinstance(value, (str, int)):
                url += f"{key}={self.encode(str(value), safe='+', plus=True)}&"
            elif duplicates:
                for v in value:
                    url += f"{key}={self.encode(str(v), safe='+', plus=True)}&"
            else:
                joined: str = "+".join([self.encode(str(v), safe="+") for v in value])
                url += f"{key}={joined}&"

        return url.rstrip("&")
