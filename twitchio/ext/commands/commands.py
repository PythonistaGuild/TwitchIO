from __future__ import annotations

import asyncio
from typing import Collection, List, Optional, TypeVar
from types import FunctionType


__all__ = ('Command', 'command')

Callback = TypeVar("Callback", bound=FunctionType)


class Command:

    def __init__(self,
                 callback: Callback,
                 *,
                 name: Optional[str] = None,
                 aliases: Optional[List[str]] = None):
        self._callback = callback
        self._name = name
        self._aliases = aliases or []

    async def __call__(self, *args, **kwargs):
        await self._callback(*args, **kwargs)


def command(*, name: Optional[str] = None, aliases: Optional[Collection[str]] = None, cls: Optional[Command] = Command):
    # noinspection PyTypeChecker
    if cls and not issubclass(cls, Command):
        raise TypeError(f'cls parameter must derive from {Command!r}.')

    def wrapped(func: Callback):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Command callbacks must be coroutines.')

        return cls(name=name or func.__name__, callback=func, aliases=aliases)
    return wrapped
