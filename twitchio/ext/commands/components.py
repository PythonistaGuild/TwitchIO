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
from collections.abc import Coroutine
from functools import partial
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeAlias, Unpack

from .core import Command, CommandErrorPayload


if TYPE_CHECKING:
    from collections.abc import Callable

    from .context import Context
    from .types_ import BotT, ComponentOptions


__all__ = ("Component",)


CoroC: TypeAlias = Coroutine[Any, Any, bool]


class _MetaComponent:
    __component_name__: str
    __component_extras__: dict[Any, Any]
    __component_specials__: ClassVar[list[str]] = []
    __all_commands__: dict[str, Command[Any, ...]]
    __all_listeners__: dict[str, list[Callable[..., Coroutine[Any, Any, None]]]]
    __all_guards__: list[Callable[..., bool] | Callable[..., CoroC]]

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
        guards: list[Callable[..., bool] | Callable[..., CoroC]] = []

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
    """TwitchIO Component class.

    Components are a powerful class used to help organize and manage commands, events, guards and errors.

    This class inherits from a special metaclass which implements logic to help manage other parts of the TwitchIO
    commands extension together.

    The Component must be added to your bot via :meth:`.commands.Bot.add_component`. After this class has been added, all
    commands and event listeners contained within the component will also be added to your bot.

    You can remove this Component and all the commands and event listeners associated with it via
    :meth:`.commands.Bot.remove_component`.

    There are two built-in methods of components that aid in doing any setup or teardown, when they are added and removed
    respectfully.

    - :meth:`~.component_load`

    - :meth:`~.component_teardown`


    Below are some special methods of Components which are designed to be overriden when needed:

    - :meth:`~.component_load`

    - :meth:`~.component_teardown`

    - :meth:`~.component_command_error`

    - :meth:`~.component_before_invoke`

    - :meth:`~.component_after_invoke`


    Components also implement some special decorators which can only be used inside of Components. The decorators are
    class method decorators and won't need an instance of a Component to use.

    - :meth:`~.listener`

    - :meth:`~.guard`


    Commands can beed added to Components with their respected decorators, and don't need to be added to the bot, as they
    will be added when you add the component.

    - ``@commands.command()``

    - ``@commands.group()``


    .. note::

        This version of TwitchIO has not yet implemented the ``modules`` implementation of ``commands.ext``.
        This part of ``commands.ext`` will allow you to easily load and unload separate python files that could contain
        components.

    .. important::

        Due to the implementation of Components, you shouldn't make a call to ``super().__init__()`` if you implement an
        ``__init__`` on this component.

    Examples
    --------

    .. code:: python3

        class Bot(commands.Bot):
            # Do your required __init__ etc first...

            # You can use setup_hook to add components...
            async def setup_hook(self) -> None:
                await self.add_component(MyComponent())


        class MyComponent(commands.Component):

            # Some simple commands...
            @commands.command()
            async def hi(self, ctx: commands.Command) -> None:
                await ctx.send(f"Hello {ctx.chatter.mention}!")

            @commands.command()
            async def apple(self, ctx: commands.Command, *, count: int) -> None:
                await ctx.send(f"You have {count} apples?!")

            # An example of using an event listener in a component...
            @commands.Component.listener()
            async def event_message(self, message: twitchio.ChatMessage) -> None:
                print(f"Received Message in component: {message.content}")

            # An example of a before invoke hook that is executed directly before any command in this component...
            async def component_before_invoke(self, ctx: commands.Command) -> None:
                print(f"Processing command in component '{self.name}'.")
    """

    @property
    def name(self) -> str:
        """Property returning the name of this component, this is either the qualified name of the class or
        the custom provided name if set.
        """
        return self.__component_name__

    async def component_command_error(self, payload: CommandErrorPayload) -> bool | None:
        """Event called when an error occurs in a command in this Component.

        Similar to :meth:`~.commands.Bot.event_command_error` except only catches errors from commands within this Component.

        This method is intended to be overwritten, by default it does nothing.

        .. note::

            Explicitly returning ``False`` in this function will stop it being dispatched to any other error handler.
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

    async def component_before_invoke(self, ctx: Context[BotT]) -> None:
        """Hook called before a :class:`~.commands.Command` in this Component is invoked.

        Similar to :meth:`~.commands.Bot.before_invoke` but only applies to commands in this Component.
        """

    async def component_after_invoke(self, ctx: Context[BotT]) -> None:
        """Hook called after a :class:`~.commands.Command` has successfully invoked in this Component.

        Similar to :meth:`~.commands.Bot.after_invoke` but only applies to commands in this Component.
        """

    @_MetaComponent._component_special
    def extras(self) -> MappingProxyType[Any, Any]:
        """Property returning a :class:`types.MappingProxyType` of the extras applied to every command in this Component.

        See: :attr:`~.commands.Command.extras` for more information on :class:`~.commands.Command` extras.
        """
        return MappingProxyType(self.__component_extras__)

    @_MetaComponent._component_special
    def guards(self) -> list[Callable[..., bool] | Callable[..., CoroC]]:
        """Property returning the guards applied to every command in this Component.

        See: :func:`.commands.guard` for more information on guards and how to use them.

        See: :meth:`.guard` for a way to apply guards to every command in this Component.
        """
        return self.__all_guards__

    @classmethod
    def listener(cls, name: str | None = None) -> Any:
        """|deco|

        A decorator which adds an event listener similar to :meth:`~.commands.Bot.listener` but contained within this
        component.

        Event listeners in components can listen to any dispatched event, and don't interfere with their base implementation.
        See: :meth:`~.commands.Bot.listener` for more information on event listeners.

        By default, listeners use the name of the function wrapped for the event name. This can be changed by passing the
        name parameter.

        .. note::

            You can have multiple of the same event listener per component, see below for an example.

        Examples
        --------

            .. code:: python3

                # By default if no name parameter is passed, the name of the event listened to is the same as the function...

                class MyComponent(commands.Component):

                    @commands.Component.listener()
                    async def event_message(self, payload: twitchio.ChatMessage) -> None:
                        ...

            .. code:: python3

                # You can listen to two or more of the same event in a single component...
                # The name parameter should have the "event_" prefix removed...

                class MyComponent(commands.Component):

                    @commands.Component.listener("message")
                    async def event_message_one(self, payload: twitchio.ChatMessage) -> None:
                        ...

                    @commands.Component.listener("message")
                    async def event_message_two(self, payload: twitchio.ChatMessage) -> None:
                        ...

        Parameters
        ----------
        name: str
            The name of the event to listen to, E.g. ``"event_message"`` or simply ``"message"``.
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
        """|deco|

        A decorator which wraps a standard function *or* coroutine function which should
        return either ``True`` or ``False``, and applies a guard to every :class:`~.commands.Command` in this component.

        The wrapped function should take in one parameter :class:`~.commands.Context` the context surrounding
        command invocation, and return a bool indicating whether a command should be allowed to run.

        If the wrapped function returns ``False``, the chatter will not be able to invoke the command and an error will be
        raised. If the wrapped function returns ``True`` the chatter will be able to invoke the command,
        assuming all the other guards also pass their predicate checks.

        See: :func:`~.commands.guard` for more information on guards, what they do and how to use them.

        See: :meth:`~.commands.Bot.global_guard` for a global guard, applied to every command the bot has added.

        Example
        -------

        .. code:: python3

            class NotModeratorError(commands.GuardFailure):
                ...

            class MyComponent(commands.Component):

                # The guard below will be applied to every command contained in your component...
                # This guard raises our custom exception for easily identifying the error in our handler...

                @commands.Component.guard()
                def is_moderator(self, ctx: commands.Context) -> bool:
                    if not ctx.chatter.moderator:
                        raise NotModeratorError

                    return True

                @commands.command()
                async def test(self, ctx: commands.Context) -> None:
                    await ctx.reply(f"You are a moderator of {ctx.channel}")

                async def component_command_error(self, payload: commands.CommandErrorPayload) -> bool | None:
                    error = payload.exception
                    ctx = payload.context

                    if isinstance(error, NotModeratorError):
                        await ctx.reply("Only moderators can use this command!")

                        # This explicit False return stops the error from being dispatched anywhere else...
                        return False

        Raises
        ------
        GuardFailure
            The guard predicate returned ``False`` and prevented the chatter from using the command.
        """

        def wrapper(func: Callable[..., bool] | Callable[..., CoroC]) -> Callable[..., bool] | Callable[..., CoroC]:
            setattr(func, "__component_guard__", True)
            return func

        return wrapper
