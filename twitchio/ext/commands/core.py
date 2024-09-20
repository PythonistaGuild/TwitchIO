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
from typing import TYPE_CHECKING, Any, Concatenate, Generic, ParamSpec, TypeAlias, TypeVar, Unpack

from .exceptions import *
from .types_ import CommandOptions, Component_T


__all__ = (
    "CommandErrorPayload",
    "Command",
    "Mixin",
    "Group",
    "command",
    "group",
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


class Command(Generic[Component_T, P]):
    def __init__(
        self,
        callback: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
        *,
        name: str,
        **kwargs: Unpack[CommandOptions],
    ) -> None:
        self._name: str = name
        self._callback = callback
        self._aliases: list[str] = kwargs.get("aliases", [])

        self._injected: Component_T | None = None
        self._error: Callable[[Component_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro] | None = None
        self._extras: dict[Any, Any] = kwargs.get("extras", {})
        self._parent: Group[Component_T, P] | None = kwargs.get("parent", None)

    def __repr__(self) -> str:
        return f"Command(name={self._name}, parent={self.parent})"

    def __str__(self) -> str:
        return self._name

    async def __call__(self, context: Context) -> None:
        callback = self._callback(self._injected, context) if self._injected else self._callback(context)  # type: ignore
        await callback

    @property
    def component(self) -> Component_T | None:
        return self._injected

    @property
    def parent(self) -> Group[Component_T, P] | None:
        return self._parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def aliases(self) -> list[str]:
        return self._aliases

    @property
    def extras(self) -> dict[Any, Any]:
        return self._extras

    @property
    def has_error(self) -> bool:
        return self._error is not None

    async def _invoke(self, context: Context) -> None:
        # TODO: Argument parsing...
        # TODO: Checks... Including cooldowns...
        callback = self._callback(self._injected, context) if self._injected else self._callback(context)  # type: ignore

        try:
            await callback
        except Exception as e:
            raise CommandInvokeError(msg=str(e), original=e) from e

    async def invoke(self, context: Context) -> None:
        try:
            await self._invoke(context)
        except CommandError as e:
            await self._dispatch_error(context, e)

    async def _dispatch_error(self, context: Context, exception: CommandError) -> None:
        payload = CommandErrorPayload(context=context, exception=exception)

        if self._error is not None:
            if self._injected:
                await self._error(self._injected, payload)  # type: ignore
            else:
                await self._error(payload)  # type: ignore

        if self._injected is not None:
            await self._injected.component_command_error(payload=payload)

        context.error_dispatched = True
        context.bot.dispatch("command_error", payload=payload)

    def error(
        self,
        func: Callable[[Component_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro],
    ) -> Callable[[Component_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro]:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Command specific "error" callback for "{self._name}" must be a coroutine function.')

        self._error = func
        return func


class Mixin(Generic[Component_T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._commands: dict[str, Command[Component_T, ...]] = {}
        super().__init__(*args, **kwargs)

    def add_command(self, command: Command[Component_T, ...], /) -> None:
        if not isinstance(command, Command):  # type: ignore
            raise TypeError(f'Expected "{Command}" got "{type(command)}".')

        if command.name in self._commands:
            raise CommandExistsError(f'A command with the name "{command.name}" is already registered.')

        name: str = command.name
        self._commands[name] = command

        for alias in command.aliases:
            if alias in self._commands:
                self.remove_command(name)
                raise CommandExistsError(f'A command with the alias "{alias}" already exists.')

            self._commands[name] = command

    def remove_command(self, name: str, /) -> Command[Any, ...] | None:
        command = self._commands.pop(name, None)
        if not command:
            return

        if name in command.aliases:
            return command

        for alias in command.aliases:
            cmd = self._commands.pop(alias, None)

            if cmd is not None and cmd != command:
                self._commands[alias] = cmd

        return command


def command(
    name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None, **kwargs: Any
) -> Any:
    def wrapper(
        func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
    ) -> Command[Any, ...]:
        if isinstance(func, Command):
            raise ValueError(f'Callback "{func._callback}" is already a Command.')  # type: ignore

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Command callback for "{func.__qualname__}" must be a coroutine function.')

        func_name = func.__name__
        name_ = func_name if not name else name.strip().replace(" ", "") or func_name

        return Command(name=name_, callback=func, aliases=aliases or [], extras=extras or {}, **kwargs)

    return wrapper


def group(
    name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None, **kwargs: Any
) -> Any:
    def wrapper(
        func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
    ) -> Group[Any, ...]:
        if isinstance(func, Command):
            raise ValueError(f'Callback "{func._callback.__name__}" is already a Command.')  # type: ignore

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Group callback for "{func.__qualname__}" must be a coroutine function.')

        func_name = func.__name__
        name_ = func_name if not name else name.strip().replace(" ", "") or func_name

        return Group(name=name_, callback=func, aliases=aliases or [], extras=extras or {}, **kwargs)

    return wrapper


class Group(Mixin[Component_T], Command[Component_T, P]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._invoke_fallback: bool = kwargs.get("invoke_fallback", False)

    def walk_commands(self) -> ...:
        for command in self._commands.values():
            yield command

            if isinstance(command, Group):
                yield from command.walk_commands()

    async def _invoke(self, context: Context) -> None:
        view = context._view
        view.skip_ws()
        trigger = view.get_word()

        next_ = self._commands.get(trigger, None)
        context._command = next_ or self
        context._invoked_subcommand = next_
        context._invoked_with = f"{context._invoked_with} {trigger}"
        context._subcommand_trigger = trigger or None

        if not trigger:
            await super()._invoke(context=context)

        elif trigger and next_:
            await next_.invoke(context=context)

        elif self._invoke_fallback:
            await super()._invoke(context=context)

        else:
            raise CommandNotFound(f'The sub-command "{trigger}" for group "{self._name}" was not found.')

    async def invoke(self, context: Context) -> None:
        try:
            await self._invoke(context)
        except CommandError as e:
            await self._dispatch_error(context, e)

    def command(
        self, name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None
    ) -> Any:
        def wrapper(
            func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
        ) -> Command[Any, ...]:
            new = command(name=name, aliases=aliases, extras=extras, parent=self)(func)

            self.add_command(new)
            return new

        return wrapper

    def group(
        self, name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None, **kwargs: Any
    ) -> Any:
        def wrapper(
            func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
        ) -> Command[Any, ...]:
            new = group(name=name, aliases=aliases, extras=extras, parent=self)(func)

            self.add_command(new)
            return new

        return wrapper
