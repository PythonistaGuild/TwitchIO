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
import html
import json
import secrets
import struct
import zlib
from typing import TYPE_CHECKING, ClassVar, Literal, Self, overload

from .enums import *


if TYPE_CHECKING:
    import os

    from .types_ import NodeDataT, OverlayDataT


__all__ = ("Node", "Overlay")


class Node:
    def __init__(self, data: NodeDataT) -> None:
        self._raw = data
        self._type: Literal["text", "image", "audio", "html"] = data.get("type", "text")

        element = data.get("element")
        self._element = HTMLElement(element) if element else None

        self._html_id = data.get("html_id")
        self._html_class = data.get("html_class")
        self._location = data.get("location")

    @property
    def type(self) -> Literal["text", "image", "audio", "html"]:
        return self._type

    @property
    def element(self) -> HTMLElement | None:
        return self._element

    @property
    def html_id(self) -> str | None:
        return self._html_id

    @property
    def html_class(self) -> str | None:
        return self._html_class

    @property
    def location(self) -> str | None:
        return self._location


class Overlay:
    VERSION: ClassVar[int] = 0

    def __init__(self, data: OverlayDataT | None = None, *, duration: int = 5000) -> None:
        self._nodes: list[Node] = []
        self._audio: Node | None = None

        data = data or {}
        nodes = data.get("nodes", [])

        for n in nodes:
            node = Node(n)
            self._nodes.append(node)

        self._duration = data.get("delay") or duration

    def add_text(
        self,
        text: str,
        *,
        element: HTMLElement = HTMLElement.span,
        html_class: str | None = None,
        html_id: str | None = None,
    ) -> Self:
        data: NodeDataT = {}

        data["type"] = "text"
        data["html_class"] = html_class
        data["html_id"] = html_id
        data["element"] = element.value

        clean = html.escape(text)
        id_ = f'id="{html_id}" ' if html_id else ""
        class_ = f'class="{html_class}"' if html_class else ""

        html_ = f"<{element.value} {id_}{class_}>{clean}</{element.value}>"
        data["raw"] = html_

        node = Node(data)
        self._nodes.append(node)

        return self

    def add_image(self) -> ...: ...

    def add_html(self) -> ...: ...

    def set_audio(self, file: str | os.PathLike[str]) -> Self:
        data: NodeDataT = {}
        identifier: str = secrets.token_urlsafe(4)

        uri = f"media/{file}" if not str(file).startswith(("http://", "https://")) else file
        data["type"] = "audio"
        data["location"] = str(file)
        data["html_id"] = identifier
        data["raw"] = f"<audio id='{identifier}'><source src='{uri}'></audio>"

        node = Node(data)
        self._audio = node

        return self

    def set_stylesheet(self) -> ...: ...

    def set_duration(self, value: int, /) -> Self:
        self._duration = value
        return self

    def build(self) -> OverlayDataT:
        data: OverlayDataT = {"nodes": [], "delay": self._duration}
        nodes = data["nodes"]

        for node in self._nodes:
            nodes.append(node._raw)

        if self._audio:
            nodes.append(self._audio._raw)

        return data

    def __str__(self) -> str:
        return self._compress()

    def __bytes__(self) -> bytearray:
        return self._compress(convert=False)

    def __format__(self, specifier: str) -> str:
        spec = specifier.lower()

        if spec == "b64":
            return self._compress()

        if spec == "bytes":
            return str(self._compress(convert=False))

        if spec == "raw":
            return str(self.build())

        if spec == "json":
            return json.dumps(self.build())

        return str(self)

    @overload
    def _compress(self, convert: Literal[True] = True) -> str: ...

    @overload
    def _compress(self, convert: Literal[False]) -> bytearray: ...

    def _compress(self, convert: bool = True) -> str | bytearray:
        dump = json.dumps(self.build()).encode(encoding="UTF-8")
        bites = bytearray()

        # Version Header: 2 Bytes
        bites[:2] = struct.pack(">H", 0)
        # Compressed Data
        bites[2:] = zlib.compress(dump, level=9)

        if convert:
            return base64.b64encode(bites).decode()

        return bites

    @classmethod
    def from_string(cls, template_string: str, /) -> Self:
        decoded = base64.b64decode(template_string)
        version = struct.unpack(">H", decoded[:2])

        if not version:
            raise RuntimeError

        if version[0] != cls.VERSION:
            raise RuntimeError

        value = decoded[2:]
        decompressed = zlib.decompress(value)

        return cls(json.loads(decompressed))

    @classmethod
    def from_bytes(cls, template_bytes: bytes | bytearray, /) -> Self:
        bites: bytearray = bytearray(template_bytes) if isinstance(template_bytes, bytes) else template_bytes

        version = struct.unpack(">H", bites[:2])
        if not version:
            raise RuntimeError

        if version[0] != cls.VERSION:
            raise RuntimeError

        decompressed = zlib.decompress(bites[2:])
        return cls(json.loads(decompressed))
