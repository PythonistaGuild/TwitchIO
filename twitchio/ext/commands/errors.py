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


class TwitchCommandError(Exception):
    """Base TwitchIO Command Error. All command errors derive from this error."""

    pass


class InvalidCogMethod(TwitchCommandError):
    pass


class InvalidCog(TwitchCommandError):
    pass


class MissingRequiredArgument(TwitchCommandError):
    pass


class BadArgument(TwitchCommandError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ArgumentParsingFailed(BadArgument):
    def __init__(self, message: str, original: Exception):
        self.original = original
        super().__init__(message)


class CommandNotFound(TwitchCommandError):
    pass


class CommandOnCooldown(TwitchCommandError):
    def __init__(self, command, retry_after):
        self.command = command
        self.retry_after = retry_after
        super().__init__(f"Command <{command.name}> is on cooldown. Try again in ({retry_after:.2f})s")


class CheckFailure(TwitchCommandError):
    pass
