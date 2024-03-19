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

import io
import logging
from typing import TYPE_CHECKING, Any

import yarl


if TYPE_CHECKING:
    import os

    from .http import HTTPClient


logger: logging.Logger = logging.getLogger(__name__)


class Asset:
    """Represents an asset from Twitch.

    Assets can be used to save or read from images or other media from Twitch.
    You can also retrieve the URL of the asset via the provided properties and methods.

    !!! version
        **3.0.0** - Added the asset class which will replace all
        previous properties of models with attached media URLs.

    Supported Operations
    --------------------

    | Operation   | Usage(s)                                 | Description                                        |
    |-----------  |------------------------------------------|----------------------------------------------------|
    | `__str__`   | `str(asset)`, `f"{asset}"`               | Returns the asset's URL.                           |
    | `__repr__`  | `repr(asset)`, `f"{asset!r}"`            | Returns the asset's official representation.       |
    """

    __slots__ = ("_http", "_ext", "_dimensions", "_original_url", "_url", "_name")

    def __init__(
        self,
        url: str,
        *,
        http: HTTPClient,
        name: str | None = None,
        dimensions: tuple[int, int] | None = None,
    ) -> None:
        self._http: HTTPClient = http
        self._ext: str = yarl.URL(url).suffix
        self._dimensions: tuple[int, int] | None = dimensions
        self._original_url: str = url
        self._url: str = url.format(width=dimensions[0], height=dimensions[1]) if dimensions else url
        self._name: str = name or yarl.URL(self._url).name

    @property
    def url(self) -> str:
        """The URL of the asset.

        If the asset supports custom dimensions, the URL will contain the dimensions set.

        See: [`.set_dimensions`][twitchio.Asset.set_dimensions] for information on setting custom dimensions.
        """
        return self._url

    @property
    def base_url(self) -> str:
        """The base URL of the asset without any dimensions set.

        This is the URL provided by Twitch before any dimensions are set.
        """
        return self._original_url

    @property
    def name(self) -> str:
        """A property that returns the default name of the asset."""
        return self._name

    @property
    def ext(self) -> str:
        """A property that returns the file extension of the asset."""
        return self._ext

    @property
    def dimensions(self) -> tuple[int, int] | None:
        """A property that returns the dimensions of the asset if it supports custom dimensions or `None`.

        See: [`.set_dimensions`][twitchio.Asset.set_dimensions] for more information.
        """
        return self._dimensions

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f"Asset(name={self.name}, url={self.url})"

    def set_dimensions(self, width: int, height: int) -> None:
        """Set the dimensions of the asset for saving or reading.

        By default all assets that support custom dimensions already have pre-defined values set.
        If custom dimensions are **not** supported, a warning will be logged and the default dimensions will be used.

        !!! warning
            If you need to custom dimensions for an asset that supports it you should use this method **before**
            calling [`.save`][twitchio.Asset.save] or [`.read`][twitchio.Asset.read].

        Examples
        --------
        ```py
            # Fetch a game and set the box art dimensions to 720x960; which is a 3:4 aspect ratio.

            game: twitchio.Game = await client.fetch_game("League of Legends")
            game.box_art.set_dimensions(720, 960)

            # Call read or save...
            await game.box_art.save()
        ```

        Parameters
        ----------
        width: int
            The width of the asset.
        height: int
            The height of the asset.
        """
        if not self._dimensions:
            logger.warning("Setting dimensions on asset %r is not supported.", self)
            return

        self._dimensions = (width, height)
        self._url = self._original_url.format(width=width, height=height)

    def url_for(self, width: int, height: int) -> str:
        """Return a new URL for the asset with the specified dimensions.

        !!! info
            This method does not return new dimensions on assets that do not support it.

        !!! warning
            This method does not set dimensions for saving or reading.
            If you need custom dimensions for an asset that supports it see: [`.set_dimensions`][twitchio.Asset.set_dimensions].

        Parameters
        ----------
        width: int
            The width of the asset.
        height: int
            The height of the asset.

        Returns
        -------
        str
            The new URL for the asset with the specified dimensions or
            the original URL if the asset does not support custom dimensions.
        """
        if not self._dimensions:
            logger.warning("Setting dimensions on asset %r is not supported.", self)
            return self._url

        return self._original_url.format(width=width, height=height)

    async def save(self, fp: str | os.PathLike[Any] | io.BufferedIOBase | None = None, seek_start: bool = True) -> int:
        """Save this asset to a file or file-like object.

        Examples
        --------
        === "Save with defaults"
            ```py
                # Fetch a game and save the box art to the current working directory with the asset's default name.

                game: twitchio.Game = await client.fetch_game("League of Legends")
                await game.box_art.save()
            ```


        === "Save with a custom name"
            ```py
                # Fetch a game and save the box art to the current working directory with a custom name.

                game: twitchio.Game = await client.fetch_game("League of Legends")
                await game.box_art.save("custom_name.png")
            ```

        === "Save with a file-like object"

            ```py
                # Fetch a game and save the box art to a file-like object.

                game: twitchio.Game = await client.fetch_game("League of Legends")
                with open("custom_name.png", "wb") as fp:
                    await game.box_art.save(fp)
            ```

        Parameters
        ----------
        fp: Union[str, os.PathLike, io.BufferedIOBase, None]
            The file path or file-like object to save the asset to.
            If `None`, the asset will be saved to the current working directory with the asset's default name.
            Defaults to `None`.
        seek_start: bool
            Whether to seek to the start of the file after successfully writing data. Defaults to `True`.

        Returns
        -------
        int
            The number of bytes written to the file or file-like object.
        """
        data: io.BytesIO = await self.read()
        written: int = 0

        if isinstance(fp, io.BufferedIOBase):
            written = fp.write(data.read())

            if seek_start:
                fp.seek(0)

            return written

        with open(fp or self.name, "wb") as new:
            written = new.write(data.read())

        return written

    async def read(self, *, seek_start: bool = True, chunk_size: int = 1024) -> io.BytesIO:
        """Read from the asset and return a [io.BytesIO](https://docs.python.org/3/library/io.html#io.BytesIO) buffer.

        You can use this method to save the asset to memory and use it later.

        Examples
        --------
        ```py
            # Fetch a game and read the box art to memory.

            game: twitchio.Game = await client.fetch_game("League of Legends")
            data: io.BytesIO = await game.box_art.read()

            # Later...
            some_bytes = data.read()
        ```

        Parameters
        ----------
        seek_start: bool
            Whether to seek to the start of the buffer after successfully writing data. Defaults to `True`.
        chunk_size: int
            The size of the chunk to use when reading from the asset. Defaults to `1024`.

        Returns
        -------
        io.BytesIO
            A bytes buffer containing the asset's data.
        """
        fp: io.BytesIO = io.BytesIO()

        async for chunk in self._http._request_asset(self.url, chunk_size=chunk_size):
            fp.write(chunk)

        if seek_start:
            fp.seek(0)

        return fp
