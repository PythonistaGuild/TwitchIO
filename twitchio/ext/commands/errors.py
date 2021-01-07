# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

__all__ = ('CommandError', 'CommandNotFound', 'MissingRequiredArgument', 'BadArgument', 'CheckFailure',)


from twitchio.errors import TwitchIOBException


class CommandError(TwitchIOBException):
    """Base Exception for errors raised by commands."""
    pass


class CommandNotFound(CommandError):
    """Exception raised when a command is not found."""
    pass


class CheckFailure(CommandError):
    """Exception raised when a check fails."""


class MissingRequiredArgument(CommandError):
    """Exception raised when a required argument is not passed to a command.

    Attributes
    ----------
    param: :class:`inspect.Parameter`
        The argument that is missing.
    """
    def __init__(self, param):
        self.param = param
        super().__init__(f'{param.name} is a required argument that is missing.')


class BadArgument(CommandError):
    """Exception raised when a bad argument is passed to a command."""
