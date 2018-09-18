import inspect
from typing import Union

from .errors import TwitchIOCommandError


class TwitchCommand:

    def __init__(self, name: str, func, **attrs):
        self.name = name
        self.callback = func
        self.aliases = attrs.get('aliases', None)
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()


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
