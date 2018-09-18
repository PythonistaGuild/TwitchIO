import inspect
from typing import Union

from .errors import *


class TwitchCommand:

    def __init__(self, name: str, func, **attrs):
        self.name = name
        self.callback = func
        self.aliases = attrs.get('aliases', None)
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()

        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(annotation=eval(value.annotation, func.__globals__))

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


def twitch_command(*, name: str=None, aliases: Union[list, tuple]=None, cls=None):
    if cls and not inspect.isclass(cls):
        raise TypeError(f'cls must be of type <class> not <{type(cls)}>')

    cls = cls or TwitchCommand

    def decorator(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Command callback must be a coroutine.')

        fname = name or func.__name__

        return cls(name=fname, func=func, aliases=aliases)
    return decorator
