"""
The MIT License (MIT)

Copyright (c) 2017-2020 TwitchIO

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
from .core import *
from .errors import *

__all__ = ("Cog",)

class Cog:

    __valid_slots__ = ('cog_unload', 'cog_check', 'cog_error', 'cog_command_error')

    def __init_subclass__(cls, *args, **kwargs):
        cls.__cogname__  = kwargs.get("name", cls.__name__)

        for name, mem in inspect.getmembers(cls):
            if name.startswith(('cog', 'bot')) and name not in cls.__valid_slots__:  # Invalid method prefixes
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

    def _unload_methods(self, bot):
        for name in self._commands:
            bot.remove_command(name)

        try:
            self.cog_unload()
        except:
            pass

    def _run_events(self, bot, event, *args, **kwargs):
        async def wrapped(func):
            try:
                await func(self, *args, **kwargs)
            except Exception as e:
                bot.loop.create_task(self.cog_error(e))
                bot.run_event("event_error", e)

        if event in self._events:
            for fun in self._events[event]:
                bot.loop.create_task(wrapped(fun))


    @classmethod
    def event(cls, event: str = None):
        if not hasattr(cls, "_events"):
            cls._events = {}

        def decorator(func):
            event_name = event or func.__name__
            if event_name in cls.__valid_slots__:
                raise ValueError(f"{event_name} cannot be a decorated event")

            if event_name in cls._events:
                cls._events[event_name].append(func)
            else:
                cls._events[event_name] = [func]

            return func

        return decorator

    @property
    def name(self):
        return self.__cogname__

    @property
    def commands(self):
        return self._commands

    async def cog_error(self, exception: Exception):
        pass

    async def cog_command_error(self, ctx, exception: Exception):
        pass

    async def cog_check(self, ctx: Context) -> bool:
        return True

    async def cog_unload(self):
        pass
