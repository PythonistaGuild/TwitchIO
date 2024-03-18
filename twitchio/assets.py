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
import io
import logging
from collections.abc import AsyncIterator

import aiohttp

from .exceptions import HTTPException


logger: logging.Logger = logging.getLogger(__name__)


class Asset:

    async def _request_bytes(self, url: str, *, chunk_size: int) -> AsyncIterator[bytes]:

        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status != 200:
                msg = f'Failed to get asset at "{url}" with status {resp.status}.'
                raise HTTPException(msg, status=resp.status, extra=await resp.text())

            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    def __init__(self, url: str, *, name: str, dimensions: tuple[int, int] | None = None) -> None:
        self._name: str | None = name
        self._dimensions: tuple[int, int] | None = dimensions
        self._original_url: str = url
        self._url: str = url.format(width=dimensions[0], height=dimensions[1]) if dimensions else url

    @property
    def url(self) -> str:
        return self._url

    @property
    def base_url(self) -> str:
        return self._original_url

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def default_dimensions(self) -> tuple[int, int] | None:
        return self._dimensions

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f'Asset(name={self.name}, url={self.url})'

    async def save(self, path: str) -> None:
        ...

    async def read(self, *, seek: bool = True, chunk_size: int = 1024) -> io.BytesIO:
        fp: io.BytesIO = io.BytesIO()

        async for chunk in self._request_bytes(self.url, chunk_size=chunk_size):
            fp.write(chunk)

        if seek:
            fp.seek(0)

        return fp
