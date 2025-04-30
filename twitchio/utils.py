"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild
Copyright (c) 2015-present Rapptz (https://github.com/Rapptz/discord.py/blob/master/discord/utils.py)

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

import asyncio
import colorsys
import datetime
import functools
import json
import logging
import os
import pathlib
import struct
import sys
import typing
from collections.abc import Callable, Iterable
from functools import wraps
from typing import TYPE_CHECKING, Any, ForwardRef, Generic, Literal, Self, TypeVar, Union, cast
from urllib.parse import quote


if TYPE_CHECKING:
    from collections.abc import Generator

    from .types_.colours import Colours
    from .types_.options import WaitPredicateT


try:
    import orjson  # type: ignore

    _from_json: Any = orjson.loads  # type: ignore
except ImportError:
    _from_json: Any = json.loads


PY_312 = sys.version_info >= (3, 12)


__all__ = (
    "MISSING",
    "ColorFormatter",
    "ColourFormatter",
    "_from_json",
    "_is_submodule",
    "clamp",
    "date_to_datetime_with_z",
    "handle_user_ids",
    "parse_timestamp",
    "setup_logging",
    "url_encode_datetime",
)

T_co = TypeVar("T_co", covariant=True)


class classproperty(Generic[T_co]):
    def __init__(self, fget: Callable[[Any], T_co]) -> None:
        self.fget = fget

    def __get__(self, instance: Any | None, owner: type[Any]) -> T_co:
        return self.fget(owner)

    def __set__(self, instance: Any | None, value: Any) -> None:
        raise AttributeError("cannot set attribute")


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


def parse_timestamp(timestamp: str) -> datetime.datetime:
    """
    Parses a timestamp in ISO8601 format to a datetime object.

    Parameters
    ----------
    timestamp: str
        The ISO8601 timestamp to be parsed.

    Returns
    -------
    datetime.datetime
        The parsed datetime object.
    """
    return datetime.datetime.fromisoformat(timestamp)


def clamp(value: int, minimum: int, maximum: int) -> int:
    if minimum > maximum:
        raise ValueError("minimum value cannot be higher than maximum value.")

    return max(min(value, maximum), minimum)


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
    """A helper function to setup logging for your application.

    Parameters
    ----------
    handler: :class:`logging.Handler` | None
        An optional :class:`logging.Handler` to use. Defaults to ``None``, which creates a :class:`logging.StreamHandler`
        by default.
    formatter: :class:`logging.Formatter` | None
        An optional :class:`logging.Formatter` to use. Defaults to ``None``, which uses a custom TrueColour
        formatter by default, falling back to standard colour support and finally no colour support if no colour
        is supported.
    level: int | None
        An optional int indicating the level of logging output. Defaults to ``20``, which is ``INFO``.
    root: bool
        An optional bool indicating whether logging should be setup on the root logger. When ``False``, logging will only be
        setup for twitchio. Defaults to ``True``.

    Examples
    --------

    .. code-block:: python3

        import logging

        import twitchio


        LOGGER: logging.Logger = logging.getLogger(__name__)
        twitchio.utils.setup_logging(level=logging.INFO)
        ...

        arg: str = "World!"
        LOGGER.info("Hello %s", arg)
    """
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

    .. tip::
        There is an alias for this class called `Color`.

    Supported Operations
    --------------------

    +-------------+----------------------------------------+----------------------------------------------------------+
    | Operation   | Usage(s)                               | Description                                              |
    +=============+========================================+==========================================================+
    | __str__     | str(colour), f"{colour}"               | Returns the colour as a hex string.                      |
    +-------------+----------------------------------------+----------------------------------------------------------+
    | __repr__    | repr(colour), f"{colour!r}"            | Returns the colours official representation.             |
    +-------------+----------------------------------------+----------------------------------------------------------+
    | __eq__      | colour1 == colour2                     | Checks if two colours are equal.                         |
    +-------------+----------------------------------------+----------------------------------------------------------+
    | __format__  | f"{colour:html}", f"{colour:rgb}",     | Returns a colour str in the specified format.            |
    |             | f"{colour:hls}"                        |                                                          |
    +-------------+----------------------------------------+----------------------------------------------------------+
    | __int__     | int(colour)                            | Returns the code as an integer.                          |
    +-------------+----------------------------------------+----------------------------------------------------------+

    """

    __slots__ = (
        "_code",
        "_hex",
        "_hex_clean",
        "_hls",
        "_hls_coords",
        "_html",
        "_rgb",
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

        This is not the same as :attr:`~twitchio.Colour.hls_coords`.

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
    def defaults(cls) -> tuple[Self, ...]:
        """Classmethod which returns a :class:`tuple` of :class:`~twitchio.Colour` representing every default chat colour
        on Twitch.

        Returns
        -------
        tuple[:class:`~twitchio.Colour`]
            A tuple of :class:`~twitchio.Colour` representing every default colour.
        """
        all_ = (
            cls.blue(),
            cls.blue_violet(),
            cls.cadet_blue(),
            cls.chocolate(),
            cls.coral(),
            cls.dodger_blue(),
            cls.firebrick(),
            cls.green(),
            cls.golden_rod(),
            cls.hot_pink(),
            cls.orange_red(),
            cls.sea_green(),
            cls.spring_green(),
            cls.yellow_green(),
        )

        return all_

    @classmethod
    def from_hex(cls, hex_: str, /) -> Self:
        """Class method to create a :class:`~twitchio.Colour` object from a hex string.

        A valid hex string can be in either one of the following formats:

        - `"#FFDD00"`
        - `"FFDD00"`
        - `"0xFFDD00"`

        For ints see: [`.from_int`][twitchio.Colour.from_int].

        Example
        -------
        .. code:: python3

            colour = twitchio.Colour.from_hex("#FFDD00")
            print(colour)


        Parameters
        ----------
        hex_: str
            Positional only. The hex string to convert to a :class:`~twitchio.Colour` object.

        Returns
        -------
        twitchio.Colour
            The :class:`~twitchio.Colour` object created from the hex string.
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
        """Class method to create a :class:`~twitchio.Colour` object from a base-10 or base-16 integer.

        A valid integer can be in either one of the following formats:

        - `16768256`
        - `0xFFDD00`

        For hex strings see: :meth:`Colour.from_hex`.

        Example
        -------
        .. code:: python3

            colour = twitchio.Colour.from_int(0xffdd00)
            print(colour)

        Parameters
        ----------
        code: int
            Positional only. The integer to convert to a :class:`~twitchio.Colour` object.

        Returns
        -------
        twitchio.Colour
            The :class:`~twitchio.Colour` object created from the integer.
        """
        hex_: str = f"{code:X}"

        return cls.from_hex(hex_)

    @classmethod
    def red(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `red` colour from the Twitch API.

        This corresponds to hex: `#FF0000`

        Example
        -------
        .. code:: python3

            red_colour = twitchio.Colour.red()

        """
        return cls.from_hex("FF0000")

    @classmethod
    def blue(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `blue` colour from the Twitch API.

        This corresponds to hex: `#0000FF`

        Example
        -------
        .. code:: python3

            blue_colour = twitchio.Colour.blue()

        """
        return cls.from_hex("0000FF")

    @classmethod
    def green(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `green` colour from the Twitch API.

        This corresponds to hex: `#008000`

        Example
        -------
        .. code:: python3

            green_colour = twitchio.Colour.green()

        """
        return cls.from_hex("008000")

    @classmethod
    def firebrick(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `firebrick` colour from the Twitch API.

        This corresponds to hex: `#B22222`

        Example
        -------
        .. code:: python3

            firebrick_colour = twitchio.Colour.firebrick()

        """
        return cls.from_hex("B22222")

    @classmethod
    def coral(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `coral` colour from the Twitch API.

        This corresponds to hex: `#FF7F50`

        Example
        -------
        .. code:: python3

            coral_colour = twitchio.Colour.coral()

        """
        return cls.from_hex("FF7F50")

    @classmethod
    def yellow_green(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `yellow_green` colour from the Twitch API.

        This corresponds to hex: `#9ACD32`

        Example
        -------
        .. code:: python3

            yellow_green_colour = twitchio.Colour.yellow_green()

        """
        return cls.from_hex("9ACD32")

    @classmethod
    def orange_red(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `orange_red` colour from the Twitch API.

        This corresponds to hex: `#FF4500`

        Example
        -------
        .. code:: python3

            orange_red_colour = twitchio.Colour.orange_red()

        """
        return cls.from_hex("FF4500")

    @classmethod
    def sea_green(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `sea_green` colour from the Twitch API.

        This corresponds to hex: `#2E8B57`

        Example
        -------
        .. code:: python3

            sea_green_colour = twitchio.Colour.sea_green()

        """
        return cls.from_hex("2E8B57")

    @classmethod
    def golden_rod(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `golden_rod` colour from the Twitch API.

        This corresponds to hex: `#DAA520`

        Example
        -------
        .. code:: python3

            golden_rod_colour = twitchio.Colour.golden_rod()

        """
        return cls.from_hex("DAA520")

    @classmethod
    def chocolate(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `chocolate` colour from the Twitch API.

        This corresponds to hex: `#D2691E`

        Example
        -------
        .. code:: python3

            chocolate_colour = twitchio.Colour.chocolate()

        """
        return cls.from_hex("D2691E")

    @classmethod
    def cadet_blue(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `cadet_blue` colour from the Twitch API.

        This corresponds to hex: `#5F9EA0`

        Example
        -------
        .. code:: python3

            cadet_blue_colour = twitchio.Colour.cadet_blue()

        """
        return cls.from_hex("5F9EA0")

    @classmethod
    def dodger_blue(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `dodger_blue` colour from the Twitch API.

        This corresponds to hex: `#1E90FF`

        Example
        -------
        .. code:: python3

            dodger_blue_colour = twitchio.Colour.dodger_blue()

        """
        return cls.from_hex("1E90FF")

    @classmethod
    def hot_pink(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `hot_pink` colour from the Twitch API.

        This corresponds to hex: `#FF69B4`

        Example
        -------
        .. code:: python3

            hot_pink_colour = twitchio.Colour.hot_pink()

        """
        return cls.from_hex("FF69B4")

    @classmethod
    def blue_violet(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `blue_violet` colour from the Twitch API.

        This corresponds to hex: `#8A2BE2`

        Example
        -------
        .. code:: python3

            blue_violet_colour = twitchio.Colour.blue_violet()

        """
        return cls.from_hex("8A2BE2")

    @classmethod
    def spring_green(cls) -> Self:
        """Class method to create a :class:`~twitchio.Colour` with the default `spring_green` colour from the Twitch API.

        This corresponds to hex: `#00FF7F`

        Example
        -------
        .. code:: python3

            sping_green_colour = twitchio.Colour.spring_green()

        """
        return cls.from_hex("00FF7F")

    @classmethod
    def announcement_blue(cls) -> str:
        """A helper class method returning the string "blue", which can be used when sending an announcement.

        Example
        -------

        .. code:: python3

            await ctx.send_announcement("Hello", colour=Colour.announcement_blue())
        """
        return "blue"

    @classmethod
    def announcement_green(cls) -> str:
        """A helper class method returning the string "green", which can be used when sending an announcement.

        Example
        -------

        .. code:: python3

            await ctx.send_announcement("Hello", colour=Colour.announcement_green())
        """
        return "green"

    @classmethod
    def announcement_orange(cls) -> str:
        """A helper class method returning the string "orange", which can be used when sending an announcement.

        Example
        -------

        .. code:: python3

            await ctx.send_announcement("Hello", colour=Colour.announcement_orange())
        """
        return "orange"

    @classmethod
    def announcement_purple(cls) -> str:
        """A helper class method returning the string "purple", which can be used when sending an announcement.

        Example
        -------

        .. code:: python3

            await ctx.send_announcement("Hello", colour=Colour.announcement_purple())
        """
        return "purple"

    @classmethod
    def announcement_primary(cls) -> str:
        """A helper class method returning the string "primary", which can be used when sending an announcement.

        .. note::

            "primary" is the default value used by Twitch and isn't required to be sent.
            The channel's accent color is used to highlight the announcement instead.

        Example
        -------

        .. code:: python3

            await ctx.send_announcement("Hello", colour=Colour.announcement_primary())
        """
        return "primary"


Color = Colour


def chunk_list(sequence: list[Any], n: int) -> Generator[Any, Any, Any]:
    for i in range(0, len(sequence), n):
        yield sequence[i : i + n]


def url_encode_datetime(dt: datetime.datetime) -> str:
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
    formatted_dt = dt.replace(tzinfo=datetime.UTC).isoformat() if dt.tzinfo is None else dt.isoformat()

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


class EventWaiter:
    _set: set[Self]

    def __init__(self, *, event: str, predicate: WaitPredicateT | None = None, timeout: float | None = None) -> None:
        self._event: str = event
        self._timeout: float | None = timeout
        self._predicate: WaitPredicateT = predicate or self.predicate
        self.__future: asyncio.Future[Any] = asyncio.Future()

    async def __call__(self, *args: Any) -> Any:
        if self.__future.done():
            self._set.discard(self)
            return

        try:
            result = await self._predicate(*args)
        except Exception as e:
            self._set.discard(self)
            self.__future.set_exception(e)
            return

        if not result:
            return

        self._set.discard(self)

        if not args:
            self.__future.set_result(None)
        else:
            self.__future.set_result(*args)

    async def wait(self) -> Any:
        try:
            async with asyncio.timeout(self._timeout):
                return await self.__future
        except TimeoutError:
            self._set.discard(self)
            raise

    async def predicate(self, *args: Any) -> bool:
        return True


F = TypeVar("F", bound=Callable[..., Any])


def handle_user_ids(is_self: bool = False) -> Callable[..., Any]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from .user import PartialUser

            new_args = [
                arg.id if isinstance(arg, PartialUser) else arg for i, arg in enumerate(args) if not (is_self and i == 0)
            ]

            if is_self and args:
                new_args.insert(0, args[0])

            new_kwargs = {k: (v.id if isinstance(v, PartialUser) else v) for k, v in kwargs.items()}

            return func(*new_args, **new_kwargs)

        return cast("F", wrapper)

    return decorator


def _is_submodule(parent: str, child: str) -> bool:
    return parent == child or child.startswith(f"{parent}.")


def date_to_datetime_with_z(date: datetime.date) -> str:
    return f"{datetime.datetime.combine(date, datetime.time(0, 0)).isoformat()}Z"


def flatten_literal_params(parameters: Iterable[Any]) -> tuple[Any, ...]:
    params: list[Any] = []
    literal_cls = type(Literal[0])

    for p in parameters:
        if isinstance(p, literal_cls):
            params.extend(p.__args__)  # type: ignore
        else:
            params.append(p)

    return tuple(params)


def normalise_optional_params(parameters: Iterable[Any]) -> tuple[Any, ...]:
    none_cls = type(None)
    return tuple(p for p in parameters if p is not none_cls) + (none_cls,)  # noqa: RUF005


def evaluate_annotation(
    tp: Any,
    globals: dict[str, Any],
    locals: dict[str, Any],
    cache: dict[str, Any],
    *,
    implicit_str: bool = True,
) -> Any:
    if isinstance(tp, ForwardRef):
        tp = tp.__forward_arg__
        # ForwardRefs always evaluate their internals
        implicit_str = True

    if implicit_str and isinstance(tp, str):
        if tp in cache:
            return cache[tp]
        evaluated = evaluate_annotation(eval(tp, globals, locals), globals, locals, cache)
        cache[tp] = evaluated
        return evaluated

    if PY_312 and getattr(tp.__repr__, "__objclass__", None) is typing.TypeAliasType:  # type: ignore
        temp_locals = dict(**locals, **{t.__name__: t for t in tp.__type_params__})  # type: ignore
        annotation = evaluate_annotation(tp.__value__, globals, temp_locals, cache.copy())  # type: ignore
        if hasattr(tp, "__args__"):
            annotation = annotation[tp.__args__]
        return annotation

    if hasattr(tp, "__supertype__"):
        return evaluate_annotation(tp.__supertype__, globals, locals, cache)

    if hasattr(tp, "__metadata__"):
        # Annotated[X, Y] can access Y via __metadata__
        metadata = tp.__metadata__[0]
        return evaluate_annotation(metadata, globals, locals, cache)

    if hasattr(tp, "__args__"):
        implicit_str = True
        is_literal = False
        args = tp.__args__
        if not hasattr(tp, "__origin__"):
            return tp
        if tp.__origin__ is Union:
            try:
                if args.index(type(None)) != len(args) - 1:
                    args = normalise_optional_params(tp.__args__)
            except ValueError:
                pass
        if tp.__origin__ is Literal:
            args = flatten_literal_params(tp.__args__)
            implicit_str = False
            is_literal = True

        evaluated_args = tuple(evaluate_annotation(arg, globals, locals, cache, implicit_str=implicit_str) for arg in args)

        if is_literal and not all(isinstance(x, (str, int, bool, type(None))) for x in evaluated_args):
            raise TypeError("Literal arguments must be of type str, int, bool, or NoneType.")

        try:
            return tp.copy_with(evaluated_args)
        except AttributeError:
            return tp.__origin__[evaluated_args]  # type: ignore

    return tp


def resolve_annotation(
    annotation: Any,
    globalns: dict[str, Any],
    localns: dict[str, Any] | None,
    cache: dict[str, Any] | None,
) -> Any:
    if annotation is None:
        return type(None)
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)

    locals = globalns if localns is None else localns
    if cache is None:
        cache = {}
    return evaluate_annotation(annotation, globalns, locals, cache)


def is_inside_class(func: Callable[..., Any]) -> bool:
    # For methods defined in a class, the qualname has a dotted path
    # denoting which class it belongs to. So, e.g. for A.foo the qualname
    # would be A.foo while a global foo() would just be foo.
    #
    # Unfortunately, for nested functions this breaks. So inside an outer
    # function named outer, those two would end up having a qualname with
    # outer.<locals>.A.foo and outer.<locals>.foo

    if func.__qualname__ == func.__name__:
        return False
    (remaining, _, _) = func.__qualname__.rpartition(".")
    return not remaining.endswith("<locals>")


def unwrap_function(function: Callable[..., Any], /) -> Callable[..., Any]:
    partial = functools.partial

    while True:
        if hasattr(function, "__wrapped__"):
            function = function.__wrapped__  # type: ignore
        elif isinstance(function, partial):
            function = function.func
        else:
            return function
