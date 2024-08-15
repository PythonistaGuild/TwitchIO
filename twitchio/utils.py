from __future__ import annotations

import colorsys
import json
import logging
import os
import pathlib
import struct
import sys
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Self
from urllib.parse import quote


if TYPE_CHECKING:
    from collections.abc import Generator

    from .types_.colours import Colours


try:
    import orjson  # type: ignore

    _from_json = orjson.loads  # type: ignore
except ImportError:
    _from_json = json.loads


__all__ = (
    "_from_json",
    "setup_logging",
    "ColourFormatter",
    "ColorFormatter",
    "parse_timestamp",
    "url_encode_datetime",
    "MISSING",
)


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
    """Helper class for working with colours in TwitchIO.

    ??? tip
        There is an alias for this class called `Color`.

    Supported Operations
    --------------------

    | Operation   | Usage(s)                                 | Description                                        |
    |-----------  |------------------------------------------|----------------------------------------------------|
    | `__str__`   | `str(colour)`, `f"{colour}"`             | Returns the colour as a hex string.                |
    | `__repr__`  | `repr(colour)`, `f"{colour!r}"`          | Returns the colours official representation.       |
    | `__eq__`    | `colour1 == colour2`                     | Checks if two colours are equal.                   |
    | `__format__`| `f"{colour:html}"`, `f"{colour:rgb}"`    | Returns a colour str in the specified format.      |
    |             | `f"{colour:hls}"`                        |                                                    |
    | `__int__`   | `int(colour)`                            | Returns the colour code as an integer.             |
    """

    __slots__ = (
        "_code",
        "_hex",
        "_hex_clean",
        "_html",
        "_rgb",
        "_hls",
        "_rgb_coords",
        "_hls_coords",
    )

    def __init__(self, data: Colours) -> None:
        self._code: int = data["code"]
        self._hex: str = data["hex"]
        self._hex_clean: str = data["hex_clean"]
        self._html: str = data["html"]
        self._rgb: tuple[int, int, int] = data["rgb"]
        self._hls: tuple[float, float, float] = data["hls"]
        self._rgb_coords: tuple[float, ...] = data["rgb_coords"]
        self._hls_coords: tuple[float, ...] = data["hls_coords"]

    @property
    def code(self) -> int:
        """Property returning the colour as an integer.

        E.g. `16768256`
        """
        return self._code

    @property
    def hex(self) -> str:
        """Property returning the colour as a hex string.

        E.g. `"0xFFDD00"`
        """
        return self._hex

    @property
    def hex_clean(self) -> str:
        """Property returning the colour as a hex string without any prefix.

        E.g. `"FFDD00"`
        """
        return self._hex_clean

    @property
    def html(self) -> str:
        """Property returning the colour as a hex string with a `#` prefix.

        E.g. `"#FFDD00"`
        """
        return self._html

    @property
    def rgb(self) -> tuple[int, int, int]:
        """Property returning the colour as an RGB tuple of `int`.

        E.g. `(255, 221, 0)`
        """
        return self._rgb

    @property
    def hls(self) -> tuple[float, float, float]:
        """Property returning the colour as an HLS tuple of `float`.

        This is not the same as [`.hls_coords`][twitchio.Colour.hls_coords].

        E.g. `(52, 50, 100)`
        """
        return self._hls

    @property
    def rgb_coords(self) -> tuple[float, ...]:
        """Property returning the colour as an RGB tuple of `float` coordinates.

        E.g. `(1.0, 0.8666666666666667, 0.0)`
        """
        return self._rgb_coords

    @property
    def hls_coords(self) -> tuple[float, ...]:
        """Property returning the colour as an HLS tuple of `float` coordinates.

        E.g. `(0.14444444444444446, 0.5, 1.0)`
        """
        return self._hls_coords

    def __repr__(self) -> str:
        return f"<Colour code={self._code} hex={self._hex} html={self._html}>"

    def __str__(self) -> str:
        return self._hex

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Colour):
            return NotImplemented

        return self._code == __value._code

    def __hash__(self) -> int:
        return hash(self._code)

    def __format__(self, format_spec: str) -> str:
        if format_spec == "html":
            return self._html

        elif format_spec == "rgb":
            return f"rgb{self._rgb}"

        elif format_spec == "hls":
            return f"hls{self._hls}"

        else:
            return str(self)

    def __int__(self) -> int:
        return self._code

    @classmethod
    def from_hex(cls, hex_: str, /) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] object from a hex string.

        A valid hex string can be in either one of the following formats:

        - `"#FFDD00"`
        - `"FFDD00"`
        - `"0xFFDD00"`

        For ints see: [`.from_int`][twitchio.Colour.from_int].

        Example
        -------
        ```py
            colour = twitchio.Colour.from_hex("#FFDD00")
            print(colour)
        ```

        Parameters
        ----------
        hex_: str
            Positional only. The hex string to convert to a [`Colour`][twitchio.Colour] object.

        Returns
        -------
        twitchio.Colour
            The [`Colour`][twitchio.Colour] object created from the hex string.
        """
        value: str = hex_.lstrip("#")
        value = value.removeprefix("0x")

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
            "hls_coords": (hue, light, sat),
        }

        return cls(payload)

    @classmethod
    def from_int(cls, code: int, /) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] object from a base-10 or base-16 integer.

        A valid integer can be in either one of the following formats:

        - `16768256`
        - `0xFFDD00`

        For hex strings see: [`.from_hex`][twitchio.Colour.from_hex].

        Example
        -------
        ```py
            colour = twitchio.Colour.from_int(0xffdd00)
            print(colour)
        ```

        Parameters
        ----------
        code: int
            Positional only. The integer to convert to a [`Colour`][twitchio.Colour] object.

        Returns
        -------
        twitchio.Colour
            The [`Colour`][twitchio.Colour] object created from the integer.
        """
        hex_: str = f"{code:X}"

        return cls.from_hex(hex_)

    @classmethod
    def red(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `red` colour from the Twitch API.

        This corresponds to hex: `#FF0000`

        Example
        -------
        ```py
            red_colour = twitch.Colour.red()
        ```
        """
        return cls.from_hex("FF0000")

    @classmethod
    def blue(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `blue` colour from the Twitch API.

        This corresponds to hex: `#0000FF`

        Example
        -------
        ```py
            blue_colour = twitch.Colour.blue()
        ```
        """
        return cls.from_hex("0000FF")

    @classmethod
    def green(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `green` colour from the Twitch API.

        This corresponds to hex: `#008000`

        Example
        -------
        ```py
            green_colour = twitch.Colour.green()
        ```
        """
        return cls.from_hex("008000")

    @classmethod
    def firebrick(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `firebrick` colour from the Twitch API.

        This corresponds to hex: `#B22222`

        Example
        -------
        ```py
            firebrick_colour = twitch.Colour.firebrick()
        ```
        """
        return cls.from_hex("B22222")

    @classmethod
    def coral(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `coral` colour from the Twitch API.

        This corresponds to hex: `#FF7F50`

        Example
        -------
        ```py
            coral_colour = twitch.Colour.coral()
        ```
        """
        return cls.from_hex("FF7F50")

    @classmethod
    def yellow_green(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `yellow_green` colour from the Twitch API.

        This corresponds to hex: `#9ACD32`

        Example
        -------
        ```py
            yellow_green_colour = twitch.Colour.yellow_green()
        ```
        """
        return cls.from_hex("9ACD32")

    @classmethod
    def orange_red(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `orange_red` colour from the Twitch API.

        This corresponds to hex: `#FF4500`

        Example
        -------
        ```py
            orange_red_colour = twitch.Colour.orange_red()
        ```
        """
        return cls.from_hex("FF4500")

    @classmethod
    def sea_green(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `sea_green` colour from the Twitch API.

        This corresponds to hex: `#2E8B57`

        Example
        -------
        ```py
            sea_green_colour = twitch.Colour.sea_green()
        ```
        """
        return cls.from_hex("2E8B57")

    @classmethod
    def golden_rod(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `golden_rod` colour from the Twitch API.

        This corresponds to hex: `#DAA520`

        Example
        -------
        ```py
            golden_rod_colour = twitch.Colour.golden_rod()
        ```
        """
        return cls.from_hex("DAA520")

    @classmethod
    def chocolate(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `chocolate` colour from the Twitch API.

        This corresponds to hex: `#D2691E`

        Example
        -------
        ```py
            chocolate_colour = twitch.Colour.chocolate()
        ```
        """
        return cls.from_hex("D2691E")

    @classmethod
    def cadet_blue(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `cadet_blue` colour from the Twitch API.

        This corresponds to hex: `#5F9EA0`

        Example
        -------
        ```py
            cadet_blue_colour = twitch.Colour.cadet_blue()
        ```
        """
        return cls.from_hex("5F9EA0")

    @classmethod
    def dodger_blue(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `dodger_blue` colour from the Twitch API.

        This corresponds to hex: `#1E90FF`

        Example
        -------
        ```py
            dodger_blue_colour = twitch.Colour.dodger_blue()
        ```
        """
        return cls.from_hex("1E90FF")

    @classmethod
    def hot_pink(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `hot_pink` colour from the Twitch API.

        This corresponds to hex: `#FF69B4`

        Example
        -------
        ```py
            hot_pink_colour = twitch.Colour.hot_pink()
        ```
        """
        return cls.from_hex("FF69B4")

    @classmethod
    def blue_violet(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `blue_violet` colour from the Twitch API.

        This corresponds to hex: `#8A2BE2`

        Example
        -------
        ```py
            blue_violet_colour = twitch.Colour.blue_violet()
        ```
        """
        return cls.from_hex("8A2BE2")

    @classmethod
    def spring_green(cls) -> Self:
        """Class method to create a [`Colour`][twitchio.Colour] with the default `spring_green` colour from the Twitch API.

        This corresponds to hex: `#00FF7F`

        Example
        -------
        ```py
            sping_green_colour = twitch.Colour.spring_green()
        ```
        """
        return cls.from_hex("00FF7F")


Color = Colour


def chunk_list(sequence: list[Any], n: int) -> Generator[Any, Any, Any]:
    for i in range(0, len(sequence), n):
        yield sequence[i : i + n]


def url_encode_datetime(dt: datetime) -> str:
    """
    Formats a datetime object to an RFC 3339 compliant string and URL-encodes it.
    If the datetime object does not have a timezone, it is converted to UTC first.

    Parameters
    ----------
    dt : datetime.datetime
        Datetime object.

    Returns
    -------
    str
        The URL encoded parsed datetime object.
    """
    formatted_dt = dt.replace(tzinfo=UTC).isoformat() if dt.tzinfo is None else dt.isoformat()

    return quote(formatted_dt)


class _MissingSentinel:
    __slots__ = ()

    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()
