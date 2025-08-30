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

import base64
import copy
import html
import importlib.resources
import json
import struct
import zlib
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self, overload

from .enums import Animation, AnimationSpeed, EventPosition, Font
from .exceptions import BlueprintError


if TYPE_CHECKING:
    import os

    from aiohttp.web import WebSocketResponse

    from .types_ import OverlayEventT, OverlayPartT


__all__ = ("Overlay", "OverlayEvent", "PlayerOverlay")


class OverlayEvent:
    __VERSION__: ClassVar[int] = 1

    def __init__(self) -> None:
        self._raw: OverlayEventT = {
            "parts": [],
            "audio": "",
            "duration": 800000,
            "duration_is_audio": False,
            "force_override": False,
            "stack_event": True,
        }

    def escape(self, value: str, /) -> str:
        return html.escape(value)

    def add_html(self) -> Self: ...

    def add_text(
        self,
        content: str,
        *,
        animation: Animation | None = None,
        animation_speed: AnimationSpeed | None = None,
        font: Font | None = None,  # TODO: Default Font...
        size: int = 24,
    ) -> Self:
        # TODO: Font...

        if not isinstance(size, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Parameter 'size' expected 'int' got {type(size)!r}.")

        escaped = self.escape(content)
        middle = f" animate__{animation.value}" if animation else ""
        speed = f" animate__{animation_speed.value}" if animation_speed else ""

        part: OverlayPartT = {"content": escaped, "animation": middle, "speed": speed, "size": size}
        self._raw["parts"].append(part)

        return self

    def add_image(self) -> Self: ...

    def set_audio(self) -> Self: ...

    def set_position(self) -> Self: ...

    def set_duration(self, value: int, *, as_audio: bool = False) -> Self: ...

    @overload
    def _compress(self, convert: Literal[True] = True) -> str: ...

    @overload
    def _compress(self, convert: Literal[False]) -> bytearray: ...

    def _compress(self, convert: bool = True) -> str | bytearray:
        dump = json.dumps(self.as_dict()).encode(encoding="UTF-8")
        bites = bytearray()

        # Version Header: 2 Bytes
        bites[:2] = struct.pack(">H", self.__VERSION__)
        # Compressed Data
        bites[2:] = zlib.compress(dump, level=9)

        if convert:
            return base64.b64encode(bites).decode()

        return bites

    @classmethod
    def from_blueprint(cls, template_string: str, /) -> Self:
        decoded = base64.b64decode(template_string)
        version = struct.unpack(">H", decoded[:2])

        if not version:
            raise BlueprintError("Blueprint is missing the version header.")

        if version[0] != cls.__VERSION__:
            raise BlueprintError(f"Blueprint version mismtach: got '{version}' excpected '{cls.__VERSION__}'.")

        value = decoded[2:]
        decompressed = zlib.decompress(value)

        inst = cls()
        inst._raw = json.loads(decompressed)

        return inst

    def to_blueprint(self) -> str:
        return self._compress()

    def as_dict(self) -> OverlayEventT:
        return copy.deepcopy(self._raw)


class Overlay:
    __sockets__: dict[str, WebSocketResponse]
    __title__: str = ""
    __template__: str = ""
    __javascript__: str = ""
    __stylesheet__: str = ""

    def __new__(cls, *args: Any, **Kwargs: Any) -> Self:
        inst = super().__new__(cls)

        pack = importlib.resources.files(__package__ or "twitchio.ext.overlays")
        static = pack / "static"

        # Load default static files...
        for file in static.iterdir():
            name = file.name

            if name == "scripts.js":
                inst.__javascript__ = inst.__javascript__ or file.read_text(encoding="UTF-8")
            elif name == "styles.css":
                inst.__stylesheet__ = inst.__stylesheet__ or file.read_text(encoding="UTF-8")
            elif name == "template":
                inst.__template__ = inst.__template__ or file.read_text(encoding="UTF-8")

        # Set default title...
        if not inst.__title__:
            inst.__title__ = cls.__qualname__

        inst.__sockets__ = {}
        return inst

    def __init__(self, *, secret: str) -> None:
        self._secret = secret
        self._position = EventPosition.center

    @property
    def secret(self) -> str:
        return self._secret

    async def setup(self) -> str | None: ...

    async def close(self) -> str | None:
        for id_, sock in self.__sockets__.items():
            try:
                await sock.close()
            except Exception:
                # TODO: Logging...
                pass

            self.__sockets__.pop(id_, None)

    async def trigger(self, event: OverlayEvent, *, skip_queue: bool = False) -> None:
        # TODO: Check connected?
        if not isinstance(event, OverlayEvent):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Expected OverlayEvent or derivative for {self!r} trigger, got {event!r}.")

        # TODO: Skip Queue...
        await self._push(event)

    async def _push(self, event: OverlayEvent) -> None:
        for id, sock in self.__sockets__.copy().items():
            if sock.closed:
                self.__sockets__.pop(id, None)

            data = {"eventData": event.as_dict(), "position": self._position.value}
            try:
                await sock.send_json(data)
            except Exception:
                # TODO: Logging...
                pass

    def connected(self) -> bool: ...

    @property
    def template(self) -> str:
        return self.__template__

    @property
    def javascript(self) -> str:
        return self.__javascript__

    @property
    def stylesheet(self) -> str:
        return self.__stylesheet__

    @property
    def title(self) -> str:
        return self.__title__

    def set_template(self, path: os.PathLike[str] | str, *, content: str | None = None) -> None:
        if content:
            self.__template__ = content
            return

        with open(path) as fp:
            self.__template__ = fp.read()

    def set_stylesheet(self, path: os.PathLike[str] | str, *, content: str | None = None) -> None:
        if content:
            self.__stylesheet__ = content
            return

        with open(path) as fp:
            self.__stylesheet__ = fp.read()

    def set_javascript(self, path: os.PathLike[str] | str, *, content: str | None = None) -> None:
        if content:
            self.__javascript__ = content
            return

        with open(path) as fp:
            self.__javascript__ = fp.read()

    def set_position(self, position: EventPosition, /) -> Self:
        self._position = position
        return self

    def generate_html(self) -> str:
        template = self.template
        js = self.javascript
        css = self.stylesheet
        title = self.title

        return template.format(stylesheet=css, javascript=js, title=title)


class PlayerOverlay(Overlay): ...
