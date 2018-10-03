import inspect
from typing import Union

from twitchio.dataclasses import Context
from .errors import *


class TwitchCommand:

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
            if param.default is not param.empty:
                converter = str if param.default is None else type(param.default)
            else:
                converter = str

        try:
            argument = converter(parsed)
        except Exception:
            raise TwitchBadArgument(f'Invalid argument parsed at `{param.name}` in command `{self.name}`.'
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
            raise TwitchMissingRequiredArguments(f'self or ctx is a required argument which is missing.')

        for name, param in iterator:
            index += 1
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                try:
                    argument = parsed.pop(index)
                except (KeyError, IndexError):
                    if param.default is not param.empty:
                        args.append(param.default)
                    else:
                        raise TwitchMissingRequiredArguments(f'Missing required arguments in command: {self.name}()')
                else:
                    argument = await self._convert_types(param, argument)
                    args.append(argument)

            if param.kind == param.KEYWORD_ONLY:
                rest = ' '.join(parsed.values())
                if rest.startswith(' '):
                    rest = rest.lstrip(' ')

                if not rest and param.default is not param.empty:
                    rest = param.default

                if not rest and param.default is not None:
                    raise TwitchMissingRequiredArguments(f'Missing required arguments in commands: {self.name}()')

                rest = await self._convert_types(param, rest)
                kwargs[param.name] = rest
                parsed.clear()
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
            raise TwitchIOBException('Command error handler must be a coroutine.')

        self.on_error = func
        return func

    def before_invoke(self, func):
        """Decorator which registers a coroutine as a before invocation hook.

        The hook will be called before the command is invoked.
        The hook must take ctx as a sole parameter.

        Parameters
        ------------
        func: :ref:`coroutine <coroutine>`
            The coroutine function to register as a before command hook.

        Raises
        --------
        twitchio.TwitchIOBException
            The func is not a coroutine function.
        """
        if not inspect.iscoroutinefunction(func):
            raise TwitchIOBException('Before invoke func must be a coroutine')

        self._before_invoke = func
        return func


def twitch_command(*, name: str=None, aliases: Union[list, tuple]=None, cls=None):
    if cls and not inspect.isclass(cls):
        raise TypeError(f'cls must be of type <class> not <{type(cls)}>')

    cls = cls or TwitchCommand

    def decorator(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Command callback must be a coroutine.')

        fname = name or func.__name__
        command = cls(name=fname, func=func, aliases=aliases)
        command.instance = command

        return command
    return decorator
