from __future__ import annotations

import asyncio
import inspect
import shlex
from typing import Collection, Dict, List, Optional, AnyStr, Tuple, TypeVar, Union
from types import FunctionType

from .context import Context


__all__ = ('Command', 'command')

Callback = TypeVar("Callback", bound=FunctionType)


class Command:

    def __init__(self,
                 callback: Callback,
                 *,
                 name: Optional[str] = None,
                 aliases: Optional[List[str]] = None,
                 positional_delimiter: Optional[str] = '=',
                 **kwargs):
        self._callback = callback
        self._name = name
        self._aliases = aliases or []
        self._pos_delim = positional_delimiter

        sig = inspect.signature(callback)
        self.params = sig.parameters.copy()  # type: ignore

        self._instance = None
        self._component = kwargs.pop('__component__', None)

    async def __call__(self, *args, **kwargs):
        await self._callback(*args, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def aliases(self) -> list:
        return self._aliases

    def _parse_args(self, to_parse: str, /) -> tuple[
        dict[str, dict[str, int | str | list[str] | None] | dict[str, int | str] | dict[str, int | list[str]]], dict[
            str, str]]:

        splat = shlex.split(to_parse)
        splat_copy = splat.copy()

        positionals = {}
        keywords = {}

        index = 0
        for name, param in self.params.items():
            if index < 2:
                index += 1
                continue

            if param.kind == param.POSITIONAL_ONLY:
                value = \
                    [splat_copy.pop(i) for i, v in enumerate(splat_copy) if v.startswith(f'{name}{self._pos_delim}')] \
                    or None

                if value and len(value) > 1:
                    raise ValueError(f'The argument "{name}" can not have more than one value.')

                if value:
                    value = value[0].removeprefix(f'{name}{self._pos_delim}')

                positionals[name] = {'index': index, 'value': value}

            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                positionals[name] = {'index': index, 'value': splat_copy.pop(0)}

            elif param.kind == param.KEYWORD_ONLY:
                keywords[name] = ' '.join(v for v in splat_copy)

            else:
                positionals[name] = {'index': index, 'value': [v for v in splat_copy]}

            index += 1

        return positionals, keywords

    def _reposition_args(self, args) -> tuple:
        return tuple(v['value'] for k, v in sorted(args.items(), key=lambda item: item[1]['index']))

    async def invoke(self, context: Context) -> None:
        to_parse = context.message.content.removeprefix(context.prefix)
        to_parse = to_parse.removeprefix(context.invoked_with)
        to_parse = to_parse.strip()

        if to_parse:
            args, kwargs = self._parse_args(to_parse)
            args = self._reposition_args(args)
        else:
            args = ()
            kwargs = {}

        await self._callback(self._instance, context, *args, **kwargs)


def command(
        *,
        name: Optional[str] = None,
        aliases: Optional[Collection[str]] = None,
        cls: Optional[Command] = Command,
        positional_delimiter: Optional[str] = '='
        ):
    # noinspection PyTypeChecker
    if cls and not issubclass(cls, Command):
        raise TypeError(f'cls parameter must derive from {Command!r}.')

    def wrapped(func: Callback):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError('Command callbacks must be coroutines.')

        return cls(name=name or func.__name__,
                   callback=func, aliases=aliases,
                   positional_delimiter=positional_delimiter)
    return wrapped
