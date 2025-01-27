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

from collections.abc import Callable, Coroutine
from typing import Any


__all__ = ("EventErrorPayload",)


class EventErrorPayload:
    """Payload received in the :class:`Client.event_error` event when an error
    occurs during an event listener.

    Attributes
    ----------
    error: Exception
        The error that occurred.
    listener: Callable[..., Coroutine[Any, Any, None]]
        The listener that raised the error.
    original: Any
        The original event payload that was passed to the listener that caused the error.
    """

    __slots__ = ("error", "listener", "original")

    def __init__(self, *, error: Exception, listener: Callable[..., Coroutine[Any, Any, None]], original: Any) -> None:
        self.error: Exception = error
        self.listener: Callable[..., Coroutine[Any, Any, None]] = listener
        self.original: Any = original
