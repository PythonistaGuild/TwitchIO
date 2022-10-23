"""MIT License

Copyright (c) 2017-present TwitchIO

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
from typing import Any, TYPE_CHECKING, Callable

from twitchio import PartialChatter
from .errors import BadArgumentError

if TYPE_CHECKING:
    from .context import Context


__all__ = ('_converter_mapping', )


async def BoolConverter(context: Context, argument) -> bool:
    if isinstance(argument, str):
        argument = argument.lower()

    if argument in ("yes", "y", "1", "true", "on", True, 1):
        return True

    elif argument in ("no", "n", "0", "false", "off", False, 0):
        return False

    raise BadArgumentError(f'Expected a boolean value, got "{argument}" instead.')


async def ChatterConverter(context: Context, argument) -> PartialChatter:
    channel = context.channel

    chatter = channel.get_chatter(argument)
    if not chatter:
        raise BadArgumentError(f'The chatter with name "{argument}" does not exist in channel "{context.channel}"')

    return chatter


_converter_mapping: dict[type, type | Callable[[Context, str], Any]] = {
    bool: BoolConverter,
    PartialChatter: ChatterConverter
}
