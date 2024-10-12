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
    __all_guards__: list[Callable[..., Coroutine[Any, Any, None]]]

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
        guards: list[Callable[..., Coroutine[Any, Any, None]]] = []

        no_special: str = 'Commands, listeners and guards must not start with special name "component_" in components:'
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

                elif hasattr(member, "__component_guard__"):
                    if not member.__component_guard__:
                        continue

                    if name.startswith("component_"):
                        raise TypeError(f'{no_special} "{member.__qualname__}" is invalid.')

                    guards.append(member)

        cls.__all_commands__ = commands
        cls.__all_listeners__ = listeners
        cls.__all_guards__ = guards

        return self


class Component(_MetaComponent):
    async def component_command_error(self, payload: CommandErrorPayload) -> None:
        """Event called when an error occurs in a command in this Component.

        Similar to :meth:`~.commands.Bot.event_command_error` except only catches errors from commands within this Component.

        This method is intended to be overwritten, by default it does nothing.
        """

    async def component_load(self) -> None:
        """Hook called when the component is about to be loaded into the bot.

        You should use this hook to do any async setup required when loading a component.
        See: :meth:`.component_teardown` for a hook called when a Component is unloaded from the bot.

        This method is intended to be overwritten, by default it does nothing.

        .. important::

            If this method raises or fails, the Component will **NOT** be loaded. Instead it will be cleaned up and removed
            and the error will propagate.
        """

    async def component_teardown(self) -> None:
        """Hook called when the component is about to be unloaded from the bot.

        You should use this hook to do any async teardown/cleanup required on the component.
        See: :meth:`.component_load` for a hook called when a Component is loaded into the bot.

        This method is intended to be overwritten, by default it does nothing.
        """

    async def component_before_invoke(self, ctx: Context) -> None:
        """Hook called before a :class:`~.commands.Command` in this Component is invoked.

        Similar to :meth:`~.commands.Bot.before_invoke` but only applies to commands in this Component.
        """

    async def component_after_invoke(self, ctx: Context) -> None:
        """Hook called after a :class:`~.commands.Command` has successfully invoked in this Component.

        Similar to :meth:`~.commands.Bot.after_invoke` but only applies to commands in this Component.
        """

    @_MetaComponent._component_special
    def extras(self) -> dict[Any, Any]:
        return self.__component_extras__

    @classmethod
    def listener(cls, name: str | None = None) -> Any:
        # TODO: Docs...
        """|deco|

        A decorator which adds a an event listener to this component.
        """

        def wrapper(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., Coroutine[Any, Any, None]]:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'Component listener func "{func.__qualname__}" must be a coroutine function.')

            name_ = name or func.__name__
            qual = f"event_{name_.removeprefix('event_')}"

            setattr(func, "__listener_name__", qual)

            return func

        return wrapper

    @classmethod
    def guard(cls) -> Any:
        # TODO: Docs...
        """|deco|

        A decorator which adds a guard to every :class:`~.commands.Command` in this Component.
        """

        def wrapper(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., Coroutine[Any, Any, None]]:
            if not asyncio.iscoroutinefunction(func):
                raise TypeError(f'Component guard func "{func.__qualname__}" must be a coroutine function.')

            setattr(func, "__component_guard__", True)

            return func

        return wrapper
