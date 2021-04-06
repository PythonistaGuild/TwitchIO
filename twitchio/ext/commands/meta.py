"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

import inspect
from functools import partial

from .core import *
from .errors import *


__all__ = ("Cog",)


class Cog:
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

    __valid_slots__ = ("cog_unload", "cog_check", "cog_error", "cog_command_error")

    def __init_subclass__(cls, *args, **kwargs):
        cls.__cogname__ = kwargs.get("name", cls.__name__)

        for name, mem in inspect.getmembers(cls):
            if name.startswith(("cog", "bot")) and name not in cls.__valid_slots__:  # Invalid method prefixes
                raise InvalidCogMethod(f'The method "{name}" starts with an invalid prefix (cog or bot).')

        cls._events = getattr(cls, "_events", {})
        cls._commands = {}

    def _load_methods(self, bot):
        for name, method in inspect.getmembers(self):
            if isinstance(method, Command):
                method._instance = self
                method.cog = self

                self._commands[name] = method
                bot.add_command(method)

        events = self._events.copy()
        self._events = {}

        for event, callbacks in events.items():
            for callback in callbacks:

                callback = partial(callback, self)

                if event in self._events:
                    self._events[event].append(callback)
                else:
                    self._events[event] = [callback]

                bot.add_event(callback=callback, name=event)

    def _unload_methods(self, bot):
        for name in self._commands:
            bot.remove_command(name)

        for event, callbacks in self._events.items():
            for callback in callbacks:
                bot.remove_event(callback=callback)

        self._events = {}

        try:
            self.cog_unload()
        except Exception as e:
            pass

    @classmethod
    def event(cls, event: str = None):
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
        if not hasattr(cls, "_events"):
            cls._events = {}

        def decorator(func):
            event_name = event or func.__name__
            if event_name in cls.__valid_slots__:
                raise ValueError(f"{event_name} cannot be a decorated event.")

            if event_name in cls._events:
                cls._events[event_name].append(func)
            else:
                cls._events[event_name] = [func]

            return func

        return decorator

    @property
    def name(self) -> str:
        """This cogs name."""
        return self.__cogname__

    @property
    def commands(self) -> dict:
        """The commands associated with this cog as a mapping."""
        return self._commands

    async def cog_error(self, exception: Exception):
        pass

    async def cog_command_error(self, ctx: Context, exception: Exception):
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

    def cog_unload(self):
        pass
