from __future__ import annotations

import asyncio
import inspect
import shlex
from types import FunctionType
from typing import Any, Callable, Collection, Coroutine, Dict, List, Optional, Type, TypeVar, Union, cast
from typing_extensions import reveal_type

from .context import Context

__all__ = ("Command", "command")

Callback = Callable[..., Coroutine[Any, Any, None]]


class Command:
    def __init__(
        self,
        callback: Callback,
        *,
        name: Optional[str] = None,
        aliases: Optional[Collection[str]] = None,
        positional_delimiter: Optional[str] = "=",
        **kwargs,
    ):
        self._callback = callback
        self._name = name or callback.__name__
        self._aliases = aliases or []
        self._pos_delim = positional_delimiter

        sig = inspect.signature(callback)
        self.params = sig.parameters.copy()

        self._instance = None
        self._component = kwargs.pop("__component__", None)

    async def __call__(self, *args, **kwargs):
        await self._callback(*args, **kwargs)

    @property
    def name(self) -> str:
        return self._name

    @property
    def aliases(self) -> list:
        return list(self._aliases)

    def _parse_args(
        self, to_parse: str, /
    ) -> tuple[
        Dict[str, Dict[str, Union[int, str, List[str], None, Dict[str, Union[int, str]], Dict[str, int | list[str]]]]],
        Dict[str, str],
    ]:

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
                value = [
                    splat_copy.pop(i) for i, v in enumerate(splat_copy) if v.startswith(f"{name}{self._pos_delim}")
                ] or None

                if value and len(value) > 1:
                    raise ValueError(f'The argument "{name}" can not have more than one value.')

                if value:
                    value = value[0].removeprefix(f"{name}{self._pos_delim}")

                positionals[name] = {"index": index, "value": value}

            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                positionals[name] = {"index": index, "value": splat_copy.pop(0)}

            elif param.kind == param.KEYWORD_ONLY:
                keywords[name] = " ".join(v for v in splat_copy)

            else:
                positionals[name] = {"index": index, "value": [v for v in splat_copy]}

            index += 1

        return positionals, keywords

    def _reposition_args(self, args) -> tuple:
        return tuple(v["value"] for k, v in sorted(args.items(), key=lambda item: item[1]["index"]))

    async def invoke(self, context: Context) -> None:
        content = context._message_copy.content

        to_parse = content.removeprefix(context.prefix or "")
        to_parse = to_parse.removeprefix(context.invoked_with)
        to_parse = to_parse.strip()

        if to_parse:
            args, kwargs = self._parse_args(to_parse)
            args = self._reposition_args(args)
        else:
            args = ()
            kwargs = {}

        context.args = args
        context.kwargs = kwargs

        await self._callback(self._instance, context, *args, **kwargs)


CommandT = TypeVar("CommandT", bound=Command)


def command(
    *,
    name: Optional[str] = None,
    aliases: Optional[Collection[str]] = None,
    cls: Type[CommandT] = Command,
    positional_delimiter: Optional[str] = "=",
):
    if cls and not issubclass(cls, Command):
        raise TypeError(f"cls parameter must derive from {Command!r}.")

    def wrapped(func: Callback) -> CommandT:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Command callbacks must be coroutines.")

        return cast(
            CommandT,
            cls(
                name=name or func.__name__,
                callback=func,
                aliases=aliases or [],
                positional_delimiter=positional_delimiter,
            ),
        )

    return wrapped
