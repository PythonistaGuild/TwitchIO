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
from typing import Union, Optional
from twitchio.abcs import Messageable
from .cooldowns import *
from .errors import *


__all__ = ('Command', 'command', 'Context', 'cooldown')


class Event:
    pass


class Command:

    def __init__(self, name: str, func, **attrs):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Command callback must be a coroutine.')

        self._callback = func
        self._checks = []
        self._cooldowns = []
        self._name = name

        self._instance = None
        self.cog = None

        try:
            self._checks.extend(func.__checks__)
        except AttributeError:
            pass

        try:
            self._cooldowns.extend(func.__cooldowns__)
        except AttributeError:
            pass

        self.aliases = attrs.get('aliases', None)
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()

        self.event_error = None
        self._before_invoke = None
        self._after_invoke = None
        self.no_global_checks = attrs.get('no_global_checks', False)

        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(annotation=eval(value.annotation, func.__globals__))

    @property
    def name(self):
        return self._name

    def _convert_types(self, param, parsed):

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

    def parse_args(self, instance, parsed):
        iterator = iter(self.params.items())
        index = 0
        args = []
        kwargs = {}

        try:
            next(iterator)
            if instance:
                next(iterator)
        except StopIteration:
            raise TwitchCommandError(f'self or ctx is a required argument which is missing.')

        for _, param in iterator:
            index += 1
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                try:
                    argument = parsed.pop(index)
                except (KeyError, IndexError):
                    if param.default is param.empty:
                        raise MissingRequiredArgument(param)
                    args.append(param.default)
                else:
                    argument = self._convert_types(param, argument)
                    args.append(argument)

            elif param.kind == param.KEYWORD_ONLY:
                rest = ' '.join(parsed.values())
                if rest.startswith(' '):
                    rest = rest.lstrip(' ')

                if rest:
                    rest = self._convert_types(param, rest)
                elif param.default is param.empty:
                    raise MissingRequiredArgument(param)
                else:
                    rest = param.default

                kwargs[param.name] = rest
                parsed.clear()
                break
            elif param.VAR_POSITIONAL:
                args.extend(parsed.values())
                break

        if parsed:
            pass  # TODO Raise Too Many Arguments.

        return args, kwargs


class Context(Messageable):

    __messageable_channel__ = True

    def __init__(self, message, bot, **attrs):
        self.message = message
        self.channel = message.channel
        self.author = message.author

        self.prefix = attrs.get('prefix')

        self.command = attrs.get('command')
        if self.command:
            self.cog = self.command.cog

        self.args = attrs.get('args')
        self.kwargs = attrs.get('kwargs')

        self.view = attrs.get('view')
        self.is_valid = attrs.get('valid')

        self.bot = bot
        self._ws = self.channel._ws

    def _fetch_channel(self):
        return self.channel         # Abstract method

    def _fetch_websocket(self):
        return self._ws             # Abstract method

    def _bot_is_mod(self):
        cache = self._ws._cache[self.channel._name]
        for user in cache:
            if user.name == self._ws.nick:
                try:
                    mod = user.is_mod
                except AttributeError:
                    return False

                return mod

    @property
    def chatters(self) -> Optional[set]:
        """The channels current chatters."""
        try:
            users = self._ws._cache[self.channel._name]
        except KeyError:
            return None

        return users

    @property
    def users(self) -> Optional[set]:   # Alias to chatters
        """Alias to chatters."""
        return self.chatters

    def get_user(self, name: str):
        """Retrieve a user from the channels user cache.

        Parameters
        -----------
        name: str
            The user's name to try and retrieve.

        Returns
        --------
        Union[:class:`twitchio.user.User`, :class:`twitchio.user.PartialUser`]
            Could be a :class:`twitchio.user.PartialUser` depending on how the user joined the channel.
            Returns None if no user was found.
        """
        name = name.lower()

        cache = self._ws._cache[self.channel._name]
        for user in cache:
            if user.name == name:
                return user

        return None


def command(*, name: str = None, aliases: Union[list, tuple] = None, cls=None, no_global_checks=False):
    if cls and not inspect.isclass(cls):
        raise TypeError(f'cls must be of type <class> not <{type(cls)}>')

    cls = cls or Command

    def decorator(func):
        fname = name or func.__name__
        cmd = cls(name=fname, func=func, aliases=aliases, no_global_checks=no_global_checks)

        return cmd
    return decorator


def cooldown(rate, per, bucket=Bucket.default):
    def decorator(func):
        if isinstance(func, Command):
            func._cooldowns.append(Cooldown(rate, per, bucket))
        else:
            func.__cooldowns__ = [Cooldown(rate, per, bucket)]
        return func
    return decorator

