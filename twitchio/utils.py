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

import json
import logging
import os
import pathlib
import sys
from typing import Any


__all__ = ("JSON_LOADS", "MISSING", "ColorFormatter", "ColourFormatter", "setup_logging")


try:
    import orjson  # type: ignore

    JSON_LOADS: Any = orjson.loads  # type: ignore
except ImportError:
    JSON_LOADS: Any = json.loads  # type: ignore


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
                logging.CRITICAL: "\x1b[48;2;161;38;46m",
            }

        elif self._supports_colour:
            self._colours = {
                logging.DEBUG: "\x1b[40;1m",
                logging.INFO: "\x1b[34;1m",
                logging.WARNING: "\x1b[33;1m",
                logging.ERROR: "\x1b[31m",
                logging.CRITICAL: "\x1b[41m",
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
