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

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Concatenate, Generic, ParamSpec, TypeAlias, TypeVar

from .exceptions import CommandError, CommandInvokeError
from .types_ import Cog_T


__all__ = (
    "CommandErrorPayload",
    "Command",
    "Mixin",
    "Group",
    "command",
)


if TYPE_CHECKING:
    from .context import Context

    P = ParamSpec("P")
else:
    P = TypeVar("P")


Coro: TypeAlias = Coroutine[Any, Any, None]


class CommandErrorPayload:
    __slots__ = ("context", "exception")

    def __init__(self, *, context: Context, exception: CommandError) -> None:
        self.context: Context = context
        self.exception: CommandError = exception


class Command(Generic[Cog_T, P]):
    def __init__(
        self,
        *,
        name: str,
        callback: Callable[Concatenate[Cog_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
    ) -> None:
        self._name: str = name
        self._callback = callback

        self._cog: Cog_T | None = None
        self._error: Callable[[Cog_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro] | None = None

    def __str__(self) -> str:
        return self._name

    @property
    def cog(self) -> Cog_T | None:
        return self._cog

    async def _invoke(self, context: Context) -> None:
        # TODO: Argument parsing...
        # TODO: Checks... Including cooldowns...
        callback = self._callback(self._cog, context) if self._cog else self._callback(context)  # type: ignore

        try:
            await callback
        except Exception as e:
            raise CommandInvokeError(msg=str(e), original=e) from e

    async def _dispatch_error(self, context: Context, exception: CommandError) -> None:
        payload = CommandErrorPayload(context=context, exception=exception)

        if self._error is not None:
            if self._cog:
                await self._error(self._cog, payload)  # type: ignore
            else:
                await self._error(payload)  # type: ignore

        if self._cog is not None:
            await self._cog.cog_command_error(payload=payload)

        context.bot.dispatch("command_error", payload=payload)

    def error(
        self,
        func: Callable[[Cog_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro],
    ) -> Callable[[Cog_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Command specific "error" callback for "{self._name}" must be a coroutine function.')

        self._error = func
        return func


class Mixin(Generic[Cog_T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._commands: dict[str, Command[Cog_T, ...]] = {}
        super().__init__(*args, **kwargs)


class Group(Mixin[Cog_T], Command[Cog_T, P]):
    def walk_commands(self) -> ...: ...


def command(name: str | None = None) -> Any:
    def wrapper(
        func: Callable[Concatenate[Cog_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro] | Command[Any, ...],
    ) -> Command[Any, ...]:
        if isinstance(func, Command):
            raise ValueError(f'Callback "{func._callback.__name__}" is already a Command.')

        name_ = name or func.__name__
        return Command(name=name_, callback=func)

    return wrapper
