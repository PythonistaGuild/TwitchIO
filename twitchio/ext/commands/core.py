# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2018 TwitchIO

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
from typing import Union

from .errors import *


class Command:

    def __init__(self, name: str, func, **attrs):
        self._name = name
        self._callback = func
        self.aliases = attrs.get('aliases', None)
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()

        self.on_error = None
        self._before_invoke = None
        self._after_invoke = None

        self.instance = None

        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(annotation=eval(value.annotation, func.__globals__))

    @property
    def name(self):
        return self._name

    async def _convert_types(self, param, parsed):

        converter = param.annotation
        if converter is param.empty:
            if param.default in (param.empty, None):
                converter = str
            else:
                converter = type(param.default)

        try:
            argument = converter(parsed)
        except Exception:
            raise BadArgument(f'Invalid argument parsed at `{param.name}` in command `{self.name}`.'
                                    f' Expected type {converter} got {type(parsed)}.')

        return argument

    async def parse_args(self, instance, parsed):
        iterator = iter(self.params.items())
        index = 0
        args = []
        kwargs = {}

        try:
            next(iterator)
            if instance:
                next(iterator)
        except StopIteration:
            raise MissingRequiredArguments(f'self or ctx is a required argument which is missing.')

        for _, param in iterator:
            index += 1
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                try:
                    argument = parsed.pop(index)
                except (KeyError, IndexError):
                    if param.default is not param.empty:
                        args.append(param.default)
                    else:
                        raise MissingRequiredArguments(f'Missing required arguments in command: {self.name}()')
                else:
                    argument = await self._convert_types(param, argument)
                    args.append(argument)

            elif param.kind == param.KEYWORD_ONLY:
                rest = ' '.join(parsed.values())
                if rest.startswith(' '):
                    rest = rest.lstrip(' ')

                if not rest and param.default is not param.empty:
                    rest = param.default

                if not rest and param.default is not None:
                    raise MissingRequiredArguments(f'Missing required arguments in commands: {self.name}()')

                rest = await self._convert_types(param, rest)
                kwargs[param.name] = rest
                parsed.clear()
                break
            elif param.VAR_POSITIONAL:
                args.extend(parsed.values())
                break

        if parsed:
            pass  # TODO Raise Too Many Arguments.

        return args, kwargs

    def error(self, func):
        """Decorator which registers a coroutine as a local error handler.

        event_command_error will still be invoked alongside this local handler.
        The local handler must take ctx and error as parameters.

        Parameters
        ------------
        func : :ref:`coroutine <coroutine>`
            The coroutine function to register as a local error handler.

        Raises
        --------
        twitchio.TwitchIOBException
            The func is not a coroutine function.
        """
        if not inspect.iscoroutinefunction(func):
            raise CommandError('Command error handler must be a coroutine.')

        self.on_error = func
        return func

    def before_invoke(self, func):
        """Decorator which registers a coroutine as a before invocation hook.

        The hook will be called before a command is invoked.
        The hook must take ctx as a sole parameter.

        Parameters
        ------------
        func: :ref:`coroutine <coroutine>`
            The coroutine function to register as a before invocation hook.

        Raises
        --------
        twitchio.TwitchIOBException
            The func is not a coroutine function.
        """
        if not inspect.iscoroutinefunction(func):
            raise CommandError('Before invoke func must be a coroutine')

        self._before_invoke = func
        return func


def command(*, name: str=None, aliases: Union[list, tuple]=None, cls=None):
    if cls and not inspect.isclass(cls):
        raise TypeError(f'cls must be of type <class> not <{type(cls)}>')

    cls = cls or Command

    def decorator(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Command callback must be a coroutine.')

        fname = name or func.__name__
        command = cls(name=fname, func=func, aliases=aliases)

        return command
    return decorator


class AutoCog:
    pass


def cog(*, name: str=None, **attrs):
    def wrapper(klass):
        class Cog(AutoCog, klass):

            def __new__(cls, *args, **kwargs):
                result = super().__new__(cls)

                result.__module__ = klass.__module__
                result.__name__ = name or klass.__name__

                for k, v in attrs.items():
                    setattr(result, k, v)

                return result

            def _prepare(self, bot):
                for name_, member in inspect.getmembers(self):
                    if isinstance(member, Command):
                        member.instance = self
                        bot.add_command(member)

                    elif name_.startswith('event_'):
                        bot.add_listener(member, name_)

                bot.cogs[self.__name__] = self

        return Cog
    return wrapper
