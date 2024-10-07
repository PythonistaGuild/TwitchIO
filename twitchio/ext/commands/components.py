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
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Self, Unpack

from .core import Command, CommandErrorPayload


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from types_ import ComponentOptions

    from .context import Context


__all__ = ("Component",)


class _MetaComponent:
    __component_name__: str
    __component_extras__: dict[Any, Any]
    __component_specials__: ClassVar[list[str]] = []
    __all_commands__: dict[str, Command[Any, ...]]
    __all_listeners__: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]]
    __all_checks__: list[Callable[..., Coroutine[Any, Any, None]]]

    @classmethod
    def _component_special(cls, obj: Any) -> Any:
        setattr(obj, "__component_special__", True)
        cls.__component_specials__.append(obj.__name__)

        return obj

    def __init_subclass__(cls, **kwargs: Unpack[ComponentOptions]) -> None:
        name: str | None = kwargs.get("name")
        if name:
            cls.__component_name__ = name

        cls.__component_extras__ = kwargs.get("extras", {})

    def __new__(cls, *args: Any, **Kwargs: Any) -> Self:
        self: Self = super().__new__(cls)

        if not hasattr(self, "__component_name__"):
            self.__component_name__ = cls.__qualname__

        commands: dict[str, Command[Any, ...]] = {}
        listeners: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]] = {}
        checks: list[Callable[..., Coroutine[Any, Any, None]]] = []

        no_special: str = 'Commands, listeners and checks must not start with special name "component_" in components:'
        no_over: str = 'The special method "{}" can not be overriden in components.'

        for base in reversed(cls.__mro__):
            for name, member in base.__dict__.items():
                if name in self.__component_specials__ and not hasattr(member, "__component_special__"):
                    raise TypeError(no_over.format(name))

                if isinstance(member, Command):
                    if name.startswith("component_"):
                        raise TypeError(f'{no_special} "{member._callback.__qualname__}" is invalid.')  # type: ignore

                    if not member.extras:
                        member._extras = self.__component_extras__

                    if not member.parent:  # type: ignore
                        commands[name] = member

                elif hasattr(member, "__listener_name__"):
                    if name.startswith("component_"):
                        raise TypeError(f'{no_special} "{member.__qualname__}" is invalid.')

                    # Need to inject the component into the listener...
                    injected = partial(member, self)

                    try:
                        listeners[member.__listener_name__].append(injected)
                    except KeyError:
                        listeners[member.__listener_name__] = [injected]

                elif hasattr(member, "__component_check__"):
                    if not member.__component_check__:
                        continue

                    if name.startswith("component_"):
                        raise TypeError(f'{no_special} "{member.__qualname__}" is invalid.')

                    checks.append(member)

        cls.__all_commands__ = commands
        cls.__all_listeners__ = listeners
        cls.__all_checks__ = checks

        return self


class Component(_MetaComponent):
    async def component_command_error(self, payload: CommandErrorPayload) -> None: ...

    async def component_load(self) -> None: ...

    async def component_before_invoke(self, ctx: Context) -> None: ...

    async def component_after_invoke(self, ctx: Context) -> None: ...

    @_MetaComponent._component_special
    def extras(self) -> dict[Any, Any]:
        return self.__component_extras__

    @classmethod
    def listener(cls, name: str | None = None) -> Any:
        def wrapper(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., Coroutine[Any, Any, None]]:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'Component listener func "{func.__qualname__}" must be a coroutine function.')

            name_ = name or func.__name__
            qual = f"event_{name_.removeprefix('event_')}"

            setattr(func, "__listener_name__", qual)

            return func

        return wrapper

    @classmethod
    def check(cls) -> Any:
        def wrapper(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., Coroutine[Any, Any, None]]:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'Component check func "{func.__qualname__}" must be a coroutine function.')

            setattr(func, "__component_check__", True)

            return func

        return wrapper
