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

from __future__ import annotations
import inspect
import types
from functools import partial
from typing import Callable, Dict, List

from .core import Command, Context


__all__ = ("Cog",)


class CogEvent:
    def __init__(self, *, name: str, func: Callable, module: str):
        self.name = name
        self.func = func
        self.module = module


class CogMeta(type):
    def __new__(mcs, *args, **kwargs):
        name, bases, attrs = args
        attrs["__cogname__"] = kwargs.pop("name", name)

        self = super().__new__(mcs, name, bases, attrs, **kwargs)
        self._events = {}
        self._commands = {}

        for name, mem in inspect.getmembers(self):
            if isinstance(mem, (CogEvent, Command)) and name.startswith(("cog_", "bot_")):  # Invalid method prefixes
                raise RuntimeError(f'The event or command "{name}" starts with an invalid prefix (cog_ or bot_).')

            if isinstance(mem, CogEvent):
                try:
                    self._events[mem.name].append(mem.func)
                except KeyError:
                    self._events[mem.name] = [mem.func]

        return self


class Cog(metaclass=CogMeta):
    """Class used for creating a TwitchIO Cog.

    Cogs help organise code and provide powerful features for creating bots.
    Cogs can contain commands, events and special cog specific methods to help with checks,
    before and after command invocation hooks, and cog error handlers.

    To use a cog simply subclass Cog and add it. Once added, cogs can be un-added and re-added live.

    Examples
    ----------

    .. code:: py

        # In modules/test.py

        from twitchio.ext import commands


        class MyCog(commands.Cog):

            def __init__(self, bot: commands.Bot):
                self.bot = bot

            @commands.command()
            async def hello(self, ctx: commands.Context):
                await ctx.send(f"Hello, {ctx.author.name}!")

            @commands.Cog.event()
            async def event_message(self, message):
                # An event inside a cog!
                if message.echo:
                    return

                print(message.content)


        def prepare(bot: commands.Bot):
            # Load our cog with this module...
            bot.add_cog(MyCog(bot))
    """

    _commands: Dict[str, Command]
    _events: Dict[str, List[Callable]]

    def _load_methods(self, bot) -> None:
        for name, method in inspect.getmembers(self):
            if isinstance(method, Command):
                method._instance = self
                method.cog = self

                self._commands[method.name] = method
                bot.add_command(method)

        events = self._events.copy()
        self._events = {}

        for event, callbacks in events.items():
            for callback in callbacks:
                callback = partial(callback, self)
                bot.add_event(callback=callback, name=event)

    def _unload_methods(self, bot) -> None:
        for name in self._commands:
            bot.remove_command(name)

        for event, callbacks in self._events.items():
            for callback in callbacks:
                bot.remove_event(callback=callback)

        self._events = {}

        try:
            self.cog_unload()
        except Exception:
            pass

    @classmethod
    def event(cls, event: str = None) -> Callable[[types.FunctionType], CogEvent]:
        """Add an event listener to this Cog.

        Examples
        ----------

        .. code:: py

            class MyCog(commands.Cog):

                def __init__(...):
                    ...

                @commands.Cog.event()
                async def event_message(self, message: twitchio.Message):
                    print(message.content)

                @commands.Cog.event("event_ready")
                async def bot_is_ready(self):
                    print('Bot is ready!')
        """

        def decorator(func) -> CogEvent:
            event_name = event or func.__name__

            return CogEvent(name=event_name, func=func, module=cls.__module__)

        return decorator

    @property
    def name(self) -> str:
        """This cogs name."""
        return self.__cogname__  # type: ignore

    @property
    def commands(self) -> dict:
        """The commands associated with this cog as a mapping."""
        return self._commands  # type: ignore

    async def cog_error(self, exception: Exception) -> None:
        pass

    async def cog_command_error(self, ctx: Context, exception: Exception) -> None:
        """Method invoked when an error is raised in one of this cogs commands.

        Parameters
        -------------
        ctx: :class:`Context`
            The context around the invoked command.
        exception: Exception
            The exception raised.
        """
        pass

    async def cog_check(self, ctx: Context) -> bool:
        """A cog-wide check which is ran everytime a command from this Cog is invoked.

        Parameters
        ------------
        ctx: :class:`Context`
            The context used to try and invoke this command.

        Notes
        -------
        .. note::

            This method must return True/False or raise. If this check returns False or raises, it will fail
            and an exception will be propagated to error handlers.
        """
        return True

    def cog_unload(self) -> None:
        pass
