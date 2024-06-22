"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Command


class TwitchCommandError(Exception):
    """Base TwitchIO Command Error. All command errors derive from this error."""

    pass


class InvalidCogMethod(TwitchCommandError):
    pass


class InvalidCog(TwitchCommandError):
    pass


class MissingRequiredArgument(TwitchCommandError):
    def __init__(self, *args, argname: Optional[str] = None) -> None:
        self.name: str = argname or "unknown"

        if args:
            super().__init__(*args)
        else:
            super().__init__(f"Missing required argument `{self.name}`")


class BadArgument(TwitchCommandError):
    def __init__(self, message: str, argname: Optional[str] = None):
        self.name: str = argname  # type: ignore # this'll get fixed in the parser handler
        self.message = message
        super().__init__(message)


class ArgumentParsingFailed(BadArgument):
    def __init__(
        self, message: str, original: Exception, argname: Optional[str] = None, expected: Optional[type] = None
    ):
        self.original: Exception = original
        self.name: str = argname  # type: ignore # in theory this'll never be None but if someone is creating this themselves itll be none.
        self.expected_type: Optional[type] = expected

        Exception.__init__(self, message)  # bypass badArgument


class UnionArgumentParsingFailed(ArgumentParsingFailed):
    def __init__(self, argname: str, expected: tuple[type, ...]):
        self.name: str = argname
        self.expected_type: tuple[type, ...] = expected

        self.message = f"Failed to convert argument `{self.name}` to any of the valid options"
        Exception.__init__(self, self.message)


class CommandNotFound(TwitchCommandError):
    def __init__(self, message: str, name: str) -> None:
        self.name: str = name
        super().__init__(message)


class CommandOnCooldown(TwitchCommandError):
    def __init__(self, command: Command, retry_after: float):
        self.command: Command = command
        self.retry_after: float = retry_after
        super().__init__(f"Command <{command.name}> is on cooldown. Try again in ({retry_after:.2f})s")


class CheckFailure(TwitchCommandError):
    pass
