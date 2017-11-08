import inspect
import asyncio
from .errors import *


class Command:
    def __init__(self, name: str, func, **attrs):
        self.name = name
        self.aliases = attrs.get('aliases', None)
        self.func = func
        self._self = attrs.get('_self', False)
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()

    async def _convert_types(self, param, parsed):

        converter = param.annotation
        if converter is param.empty:
            if param.default is not param.empty:
                converter = str if param.default is None else type(param.default)
            else:
                converter = str

        try:
            argument = converter(parsed)
        except Exception:
            raise TwitchBadArgument('Invalid argument parsed at `{0}` in command `{1}`. Expected type {2} got {3}.'
                                    .format(param.name, self.name, converter, type(parsed)))

        return argument

    async def parse_args(self, parsed):

        iterator = iter(self.params.items())
        index = 0
        args = []
        kwargs = {}

        try:
            next(iterator)
        except StopIteration:
            raise TwitchIOCommandError("{0}() missing 1 required positional argument: 'self'".format(self.name))

        try:
            next(iterator)
        except StopIteration:
            raise TwitchIOCommandError("{0}() missing 1 required positional argument: 'ctx'".format(self.name))

        for name, param in iterator:
            index += 1
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                try:
                    argument = parsed.pop(index)
                except (KeyError, IndexError):
                    if param.default is not param.empty:
                        args.append(param.default)
                    else:
                        raise TwitchMissingRequiredArguments('Missing required arguments in command: {}()'
                                                             .format(self.name))
                else:
                    argument = await self._convert_types(param, argument)
                    args.append(argument)

            if param.kind == param.KEYWORD_ONLY:
                rest = ' '.join(parsed.values())
                if rest.startswith(' '):
                    rest = rest.lstrip(' ')
                kwargs[param.name] = rest
                parsed.clear()
                break

        if parsed:
            pass  # TODO Raise Too Many Arguments.

        return args, kwargs


def twitch_command(aliases: list=None):
    def decorator(func):
        cls = Command
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Command callback must be a coroutine.')

        fname = func.__name__
        return cls(name=fname, func=func, aliases=aliases)

    return decorator
