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


class Cog:

    __valid_slots__ = ('cog_unload', 'cog_check', 'cog_error', )

    def __init_subclass__(cls, *args, **kwargs):

        try:
            cls.__name__ = cls.name
        except AttributeError:
            cls.name = cls.__name__

        for name, mem in inspect.getmembers(cls):
            if name.startswith(('cog', 'bot')) and name not in cls.__valid_slots__:  # Invalid method prefixes
                raise InvalidCogMethod(f'The method "{name}" starts with an invalid prefix (cog or bot).')

        cls._events = {}
        cls._commands = {}

    def _load_methods(self, bot):
        for name, method in inspect.getmembers(self):
            if isinstance(method, Command):
                method._instance = self
                method.cog = self

                self._commands[name] = method
                bot.add_command(method)

    @property
    def commands(self):
        return self._commands
