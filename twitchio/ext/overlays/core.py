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
import logging
import struct
import zlib
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self, overload

from twitchio.utils import MISSING, Colour, clamp

from .enums import Alignment, Animation, AnimationSpeed, EventPosition, Font
from .exceptions import AudioLoadedError, BlueprintError


if TYPE_CHECKING:
    import os

    from aiohttp.web import WebSocketResponse

    from .types_ import ImageDimensions, OverlayEventT, OverlayPartT


__all__ = ("Overlay", "OverlayEvent", "PlayerOverlay")


LOGGER: logging.Logger = logging.getLogger(__name__)


class OverlayEvent:
    __VERSION__: ClassVar[int] = 1

    def __init__(self) -> None:
        self._raw: OverlayEventT = {
            "parts": [],
            "audio": "",
            "volume": 0.5,
            "duration": 5000,
            "duration_is_audio": False,
            "force_override": False,
            "stack_event": False,
            "animation": None,
            "speed": None,
        }

    def __repr__(self) -> str:
        return (
            f"OverlayEvent(parts={len(self._raw['parts'])}, duration={self._raw['duration']}, volume={self._raw['volume']})"
        )

    def __format__(self, format_spec: str) -> str:
        if format_spec in ("bp", "template"):
            return self.to_blueprint()

        return repr(self)

    def escape(self, value: str, /) -> str:
        """Method which escapes the provided the content via the ``html`` standard library.

        Parameters
        ----------
        value: str
            The content to escape.

        Returns
        -------
        str
            The escaped content.
        """
        return html.escape(value)

    def reset(self) -> Self:
        """Method to reset this event back to it's default state.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        self._raw = {
            "parts": [],
            "audio": "",
            "volume": 0.5,
            "duration": 5000,
            "duration_is_audio": False,
            "force_override": False,
            "stack_event": False,
            "animation": None,
            "speed": None,
        }
        return self

    def set_properties(
        self,
        *,
        animation: Animation = MISSING,
        animation_speed: AnimationSpeed = MISSING,
        override: bool = MISSING,
        stack: bool = MISSING,
        duration: int = MISSING,
        volume: int = MISSING,
    ) -> Self:
        """Method which allows setting various properties on the overlay event.

        Any argument not provided will be ignored.

        Parameters
        ----------
        animation: ...
            ...
        animation_speed: ...
            ...
        override: ...
            ...
        stack: ...
            ...
        duration: ...
            ...
        volume: ...
            ...

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        if animation is not MISSING:
            self._raw["animation"] = f"animate__{animation.value}"

        if animation_speed is not MISSING:
            self._raw["speed"] = f"animate__{animation_speed.value}"

        if override is not MISSING:
            self._raw["force_override"] = override

        if stack is not MISSING:
            self._raw["stack_event"] = stack

        if duration is not MISSING:
            self._raw["duration"] = duration

        if volume is not MISSING:
            vol = clamp(volume, 0, 100) / 100
            self._raw["volume"] = vol

        return self

    def add_html(
        self,
        html: str,
        animation: Animation | None = None,
        animation_speed: AnimationSpeed | None = None,
        alignment: Alignment | None = None,
    ) -> Self:
        """Method to add a custom HTML segment to this event.

        .. important::

            This method is unsafe and care should be taken to ensure that the input is trusted. The input provided to this
            method will **NOT** be escaped and could be used to inject scripts into the Javascript of the overlay.

        .. warning::

            We do not recommend using this method if any of the input comes from a third-party or external source; including
            chatters or other API's.

        Parameters
        ----------
        html: str
            The ``HTML`` to use as a segment for this event. Ensure the content provided to this parameter is trusted.
        animation: :class:`~twitchio.ext.overlays.Animation` | ``None``
            An optional animation to apply to the provided HTML content. Defaults to ``None``.
        animation_speed: :class:`~twitchio.ext.overlays.AnimationSpeed` | ``None``
            An optional speed of animation to provide. Defaults to ``None`` which is the default speed.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        middle = f" animate__{animation.value}" if animation else ""
        speed = f" animate__{animation_speed.value}" if animation_speed else ""
        part: OverlayPartT = {
            "content": html,
            "animation": middle,
            "speed": speed,
            "alignment": f" {alignment.value}" if alignment else None,
        }

        self._raw["parts"].append(part)
        return self

    def add_text(
        self,
        content: str,
        *,
        animation: Animation | None = None,
        animation_speed: AnimationSpeed | None = None,
        font: Font | None = None,  # TODO: Default Font...
        size: int = 24,
        colour: Colour | None = None,
        alignment: Alignment | None = None,
    ) -> Self:
        """Method to add custom text content as a segement to this event.

        .. note::

            The text content provided to this method is escaped via :meth:`.escape`.

        Parameters
        ----------
        content: str
            The text content to use as a segment for this event. This content will be escaped.
        animation: :class:`~twitchio.ext.overlays.Animation` | ``None``
            An optional animation to apply to the provided text content. Defaults to ``None``.
        animation_speed: :class:`~twitchio.ext.overlays.AnimationSpeed` | ``None``
            An optional speed of animation to provide. Defaults to ``None`` which is the default speed.
        font: :class:`~twitchio.ext.overlays.Font` | ``None``
            ...
        size: int
            An optional :class:`int` which is the size of the font in `px`. Defaults to ``24``.
        colour: :class:`twitchio.Colour`
            An optional :class:`twitchio.Colour` or :class:`twitchio.Color` to use for the text. Defaults to ``None``, which
            will be ``black`` / ``#000000``.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """

        if not isinstance(size, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Parameter 'size' expected 'int' got {type(size)!r}.")

        escaped = self.escape(content)
        middle = f" animate__{animation.value}" if animation else ""
        speed = f" animate__{animation_speed.value}" if animation_speed else ""
        col = colour or Colour.from_hex("#000000")

        part: OverlayPartT = {
            "content": escaped,
            "animation": middle,
            "speed": speed,
            "size": size,
            "colour": col.html,
            "alignment": f" {alignment.value}" if alignment else None,
        }
        self._raw["parts"].append(part)

        return self

    def add_image(
        self,
        identifier: str,
        /,
        animation: Animation | None = None,
        animation_speed: AnimationSpeed | None = None,
        dimensions: ImageDimensions | None = None,
        alignment: Alignment | None = None,
    ) -> Self:
        middle = f" animate__{animation.value}" if animation else ""
        speed = f" animate__{animation_speed.value}" if animation_speed else ""
        part: OverlayPartT = {
            "content": identifier,
            "is_image": True,
            "animation": middle,
            "speed": speed,
            "dimensions": dimensions,
            "alignment": f" {alignment.value}" if alignment else None,
        }
        self._raw["parts"].append(part)

        return self

    def set_audio(self, identifier: str, /, *, volume: int = 50) -> Self:
        """Method which sets the audio for this overlay event.

        Parameters
        ----------
        identifier: str
            The audio identifier, which should be a unique identifier which was used in
            :meth:`~twitchio.ext.overlays.Overlay.mount_audio`.
        volume: int
            An optional :class:`int` which sets the volume of the audio. The volume will be clamped between ``0`` and ``100``.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        vol = clamp(volume, 0, 100) / 100

        self._raw["audio"] = identifier
        self._raw["volume"] = vol

        return self

    def set_duration(self, value: int | None = 5000, *, as_audio: bool = False) -> Self:
        """Method which sets the overall duration of this overlay event.

        Parameters
        ----------
        value: int | None
            The duration of the event in ``ms (milliseconds)`` as an :class:`int`. Could be ``None`` which would mean the
            event will not be removed from the overlay until another condition is met, such as a new event overriding it.
            Defaults to ``5000`` (5 seconds).
        as_audio: bool
            An optional bool which when set will ensure the event lasts for as long as any audio provided does. If a duration
            is provided when this parameter is set to ``True``, the duration will be additive. Defaults to ``False``.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        duration = max(0, value or 0) or None
        self._raw["duration"] = duration
        self._raw["duration_is_audio"] = as_audio

        return self

    def set_stacking(self, value: bool, /) -> Self:
        """Method which sets whether or not this overlay event should stack below the previous event.

        Parameters
        ----------
        value: bool
            If set to ``True``, the overlay event will stack below other events. Defaults to ``False``.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        self._raw["stack_event"] = value
        return self

    def set_override(self, value: bool, /) -> Self:
        """Method which sets whether ot not this overlay event should override any previous events.

        Setting this to ``True`` will ensure any previous events are removed.

        Parameters
        ----------
        value: bool
            If set to ``True``, all previous events will be removed when this event is triggered.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
        self._raw["force_override"] = value
        return self

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
        """Classmethod which loads and returns a previous designed event from a Blueprint string.

        You can generate a blueprint for an event via :meth:`.to_blueprint`.

        Parameters
        ----------
        template_string: str
            The previous saved blueprint string to load an event from.

        Returns
        -------
        OverlayEvent
            This method returns ``self`` which allows for fluid-style chaining.
        """
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
        """Method which generates and returns a blueprint string, which can be saved and used later to load an event.

        You can load an event from a blueprint via :meth:`.from_blueprint`.

        Returns
        -------
        str
            The event in the form of a compressed string, which can easily be saved and loaded later.
        """
        return self._compress()

    def as_dict(self) -> OverlayEventT:
        """Method which does a deep-copy on the raw data and returns it as a dictionary.

        Returns
        -------
        dict
            The raw data for this event.
        """
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
        self._audio_paths: dict[str, os.PathLike[str] | str] = {}
        self._image_paths: dict[str, os.PathLike[str] | str] = {}

    @property
    def secret(self) -> str:
        """Property returning the overlay secret.

        The secret is used to generate a URL on the adapter to access the overlay.
        """
        return self._secret

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

    @property
    def position(self) -> EventPosition:
        return self._position

    @property
    def audio(self) -> MappingProxyType[str, os.PathLike[str] | str]:
        return MappingProxyType(self._audio_paths)

    @property
    def images(self) -> MappingProxyType[str, os.PathLike[str] | str]:
        return MappingProxyType(self._image_paths)

    async def setup(self) -> None:
        """|coro|

        Method which allows custom asynchronous setup to occur on the overlay.

        This method is called once when the overlay is added to an adapter.

        Should be overriden if async setup is required.
        """
        ...

    async def teardown(self) -> None:
        """|coro|

        Method which allows custom asynchronous cleanup to occur on the overlay.

        This method is called once when the overlay is removed from an adapter.

        Should be overriden if async cleanup is required.
        """
        ...

    async def close(self) -> None:
        """|coro|

        Method which performs cleanup on the overlay and gracefully closes any active connections.

        This method could be overriden, however consider using :meth:`.teardown` instead.

        The default implementation of this method should be called if overriden, e.g. ``await super().close()``.
        """
        for id_, sock in self.__sockets__.items():
            try:
                await sock.close()
            except Exception as e:
                LOGGER.debug("Exception occurred duting cleanup on websocket '%s' on '%r': %s", id_, self, e)

            self.__sockets__.pop(id_, None)

    async def trigger(self, event: OverlayEvent, /) -> None:
        # TODO: Check connected?
        if not isinstance(event, OverlayEvent):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError(f"Expected OverlayEvent or derivative for {self!r} trigger, got {event!r}.")

        await self._push(event)

    async def _push(self, event: OverlayEvent) -> None:
        for id_, sock in self.__sockets__.copy().items():
            if sock.closed:
                self.__sockets__.pop(id_, None)

            data = {"eventData": event.as_dict(), "position": self._position.value}

            try:
                await sock.send_json(data)
            except Exception as e:
                LOGGER.warning("Exception occurred while sending data to overlay websocket '%s' on '%r': %s", id_, self, e)

    def connected(self) -> bool: ...

    def set_template(self, path: os.PathLike[str] | str, *, content: str | None = None) -> Self:
        """Method which sets the default HTML template used by the overlay.

        Returns
        -------
        Overlay
            This method returns ``self`` which allows for fluid-style chaining.
        """
        # TODO: Explain Templates...
        # TODO: Explain default template
        if content:
            self.__template__ = content
            return self

        with open(path) as fp:
            self.__template__ = fp.read()

        return self

    def set_stylesheet(self, path: os.PathLike[str] | str, *, content: str | None = None) -> Self:
        if content:
            self.__stylesheet__ = content
            return self

        with open(path) as fp:
            self.__stylesheet__ = fp.read()

        return self

    def set_javascript(self, path: os.PathLike[str] | str, *, content: str | None = None) -> Self:
        if content:
            self.__javascript__ = content
            return self

        with open(path) as fp:
            self.__javascript__ = fp.read()

        return self

    def set_position(self, position: EventPosition, /) -> Self:
        self._position = position
        return self

    def mount_audio(self, identifier: str, *, path: os.PathLike[str] | str) -> Self:
        if identifier in self._audio_paths:
            raise AudioLoadedError(f"Audio with the identifier '{identifier}' has already been added to {self!r}.")

        self._audio_paths[identifier] = path
        return self

    def unmount_audio(self, identifier: str, /) -> Self:
        if identifier not in self._audio_paths:
            raise AudioLoadedError(f"Audio with the identifier '{identifier}' has not been previously loaded to {self!r}.")

        del self._audio_paths[identifier]
        return self

    def get_audio(self, identifier: str, /) -> os.PathLike[str] | str | None:
        return self._audio_paths.get(identifier)

    # ...
    # TODO: Univieral Audio/Image Error?

    def mount_image(self, identifier: str, *, path: os.PathLike[str] | str) -> Self:
        if identifier in self._image_paths:
            raise AudioLoadedError(f"Image with the identifier '{identifier}' has already been added to {self!r}.")

        self._image_paths[identifier] = path
        return self

    def unmount_image(self, identifier: str, /) -> Self:
        if identifier not in self._image_paths:
            raise AudioLoadedError(f"Image with the identifier '{identifier}' has not been previously loaded to {self!r}.")

        del self._image_paths[identifier]
        return self

    def get_image(self, identifier: str, /) -> os.PathLike[str] | str | None:
        return self._image_paths.get(identifier)

    def generate_html(self) -> str:
        template = self.template
        js = self.javascript
        css = self.stylesheet
        title = self.title

        return template.format(stylesheet=css, javascript=js, title=title)


class PlayerOverlay(Overlay): ...
