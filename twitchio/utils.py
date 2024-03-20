from __future__ import annotations

import colorsys
import json
import logging
import os
import pathlib
import struct
import sys
from datetime import datetime
from typing import TYPE_CHECKING, Any

from backports.datetime_fromisoformat import MonkeyPatch  # type: ignore


if TYPE_CHECKING:
    from typing_extensions import Self

    from .types_.colours import Colours

MonkeyPatch.patch_fromisoformat()  # type: ignore

try:
    import orjson  # type: ignore

    _from_json = orjson.loads  # type: ignore
except ImportError:
    _from_json = json.loads

__all__ = ("_from_json", "setup_logging", "ColourFormatter", "ColorFormatter", "parse_timestamp")


def is_docker() -> bool:
    path: pathlib.Path = pathlib.Path("/proc/self/cgroup")

    exists: bool = path.exists()
    is_file: bool = path.is_file()
    return exists or (is_file and any("docker" in line for line in path.open()))


def stream_supports_colour(stream: Any) -> bool:
    is_a_tty = hasattr(stream, "isatty") and stream.isatty()

    # Pycharm and Vscode support colour in their inbuilt editors
    if "PYCHARM_HOSTED" in os.environ or os.environ.get("TERM_PROGRAM") == "vscode":
        return is_a_tty

    if sys.platform != "win32":
        # Docker does not consistently have a tty attached to it
        return is_a_tty or is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ("ANSICON" in os.environ or "WT_SESSION" in os.environ)


def stream_supports_rgb(stream: Any) -> bool:
    if not stream_supports_colour(stream):
        return False

    if "COLORTERM" in os.environ:
        return os.environ["COLORTERM"] in ("truecolor", "24bit")

    return False


def parse_timestamp(timestamp: str) -> datetime:
    """
    Parses a timestamp in ISO8601 format to a datetime object.

    Parameters
    ----------
    timestamp : str
        The ISO8601 timestamp to be parsed.

    Returns
    -------
    datetime.datetime
        The parsed datetime object.
    """
    return datetime.fromisoformat(timestamp)


class ColourFormatter(logging.Formatter):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._handler: logging.StreamHandler[Any] = kwargs.get("handler", logging.StreamHandler())

        self._supports_colour: bool = stream_supports_colour(self._handler.stream)
        self._supports_rgb: bool = stream_supports_rgb(self._handler.stream)

        self._colours: dict[int, str] = {}
        self._RESET: str = "\033[0m"

        if self._supports_rgb:
            self._colours = {
                logging.DEBUG: "\x1b[40;1m",
                logging.INFO: "\x1b[38;2;100;55;215;1m",
                logging.WARNING: "\x1b[38;2;204;189;51;1m",
                logging.ERROR: "\x1b[38;2;161;38;46m",
                logging.CRITICAL: "\x1b[48;2;161;38;46",
            }

        elif self._supports_colour:
            self._colours = {
                logging.DEBUG: "\x1b[40;1m",
                logging.INFO: "\x1b[34;1m",
                logging.WARNING: "\x1b[33;1m",
                logging.ERROR: "\x1b[31m",
                logging.CRITICAL: "\x1b[41",
            }

        self._FORMATS: dict[int, logging.Formatter] = {
            level: logging.Formatter(
                f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m {colour}%(name)s\x1b[0m %(message)s"
            )
            for level, colour in self._colours.items()
        }

    def format(self, record: logging.LogRecord) -> str:
        formatter: logging.Formatter | None = self._FORMATS.get(record.levelno, None)
        if formatter is None:
            formatter = self._FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output


ColorFormatter = ColourFormatter


def setup_logging(
    *,
    handler: logging.Handler | None = None,
    formatter: logging.Formatter | None = None,
    level: int | None = None,
    root: bool = True,
) -> None:
    if level is None:
        level = logging.INFO

    if handler is None:
        handler = logging.StreamHandler()

    if formatter is None:
        if isinstance(handler, logging.StreamHandler) and stream_supports_colour(handler.stream):  # type: ignore
            formatter = ColourFormatter()
        else:
            dt_fmt = "%Y-%m-%d %H:%M:%S"
            formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")

    if root:
        logger = logging.getLogger()
    else:
        library, _, _ = __name__.partition(".")
        logger = logging.getLogger(library)

    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)  # type: ignore


# Colour stuff...


class Colour:
    __slots__ = (
        "_code",
        "_hex",
        "_hex_clean",
        "_html",
        "_rgb",
        "_hls",
        "_rgb_coords",
    )

    def __init__(self, data: Colours) -> None:
        self._code: int = data["code"]
        self._hex: str = data["hex"]
        self._hex_clean: str = data["hex_clean"]
        self._html: str = data["html"]
        self._rgb: tuple[int, int, int] = data["rgb"]
        self._hls: tuple[float, float, float] = data["hls"]
        self._rgb_coords: tuple[float, ...] = data["rgb_coords"]

    @property
    def code(self) -> int:
        return self._code

    @property
    def hex(self) -> str:
        return self._hex

    @property
    def hex_clean(self) -> str:
        return self._hex_clean

    @property
    def html(self) -> str:
        return self._html

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self._rgb

    @property
    def hls(self) -> tuple[float, float, float]:
        return self._hls

    @property
    def rgb_coords(self) -> tuple[float, ...]:
        return self._rgb_coords

    def __repr__(self) -> str:
        return f"<Colour code={self._code} hex={self._hex} html={self._html}>"

    def __str__(self) -> str:
        return self._hex

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Colour):
            return NotImplemented

        return self._code == __value._code

    @classmethod
    def from_hex(cls, hex_: str, /) -> Self:
        value: str = hex_.lstrip("#")

        rgb: tuple[int, int, int] = struct.unpack("BBB", bytes.fromhex(value))
        int_: int = int(value, 16)
        html: str = f"#{value}"
        hexa: str = hex(int_)
        rgb_coords: tuple[float, ...] = tuple(c / 255 for c in rgb)

        hue, light, sat = colorsys.rgb_to_hls(*rgb_coords)
        hls: tuple[float, ...] = (round(hue * 360), round(light * 100), round(sat * 100))

        payload: Colours = {
            "code": int_,
            "hex": hexa,
            "hex_clean": value,
            "html": html,
            "rgb": rgb,
            "hls": hls,
            "rgb_coords": rgb_coords,
        }

        return cls(payload)


Color = Colour
