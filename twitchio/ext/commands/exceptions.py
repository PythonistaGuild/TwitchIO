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

from twitchio.exceptions import TwitchioException


__all__ = (
    "CommandError",
    "CommandInvokeError",
    "CommandHookError",
    "CommandNotFound",
    "PrefixError",
    "InputError",
    "ArgumentError",
)


class CommandError(TwitchioException): ...


class CommandInvokeError(CommandError):
    def __init__(self, msg: str | None = None, original: Exception | None = None) -> None:
        self.original: Exception | None = original
        super().__init__(msg)


class CommandHookError(CommandInvokeError): ...


class CommandNotFound(CommandError): ...


class PrefixError(CommandError): ...


class InputError(CommandError): ...


class ArgumentError(InputError): ...


class UnexpectedQuoteError(ArgumentError):
    def __init__(self, quote: str) -> None:
        self.quote: str = quote
        super().__init__(f"Unexpected quote mark, {quote!r}, in non-quoted string")


class InvalidEndOfQuotedStringError(ArgumentError):
    def __init__(self, char: str) -> None:
        self.char: str = char
        super().__init__(f"Expected space after closing quotation but received {char!r}")


class ExpectedClosingQuoteError(ArgumentError):
    def __init__(self, close_quote: str) -> None:
        self.close_quote: str = close_quote
        super().__init__(f"Expected closing {close_quote}.")
