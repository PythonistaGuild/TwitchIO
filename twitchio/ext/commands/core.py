"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild
Copyright (c) 2015 - present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import asyncio
import copy
import inspect
from collections.abc import Callable, Coroutine, Generator
from types import MappingProxyType, UnionType
from typing import TYPE_CHECKING, Any, Concatenate, Generic, Literal, ParamSpec, TypeAlias, TypeVar, Union, Unpack, overload

import twitchio
from twitchio.utils import MISSING, unwrap_function

from .cooldowns import BaseCooldown, Bucket, BucketType, Cooldown, KeyT
from .exceptions import *
from .types_ import CommandOptions, Component_T


__all__ = (
    "Command",
    "CommandErrorPayload",
    "Group",
    "Mixin",
    "command",
    "cooldown",
    "group",
    "guard",
    "is_broadcaster",
    "is_elevated",
    "is_moderator",
    "is_owner",
    "is_staff",
    "is_vip",
)


if TYPE_CHECKING:
    from twitchio.user import Chatter

    from .context import Context

    P = ParamSpec("P")
else:
    P = TypeVar("P")


Coro: TypeAlias = Coroutine[Any, Any, None]
CoroC: TypeAlias = Coroutine[Any, Any, bool]

DT = TypeVar("DT")
VT = TypeVar("VT")


def get_signature_parameters(
    function: Callable[..., Any],
    globalns: dict[str, Any],
    /,
    *,
    skip_parameters: int | None = None,
) -> dict[str, inspect.Parameter]:
    signature = inspect.Signature.from_callable(function)
    params: dict[str, inspect.Parameter] = {}

    cache: dict[str, Any] = {}
    eval_annotation = twitchio.utils.evaluate_annotation
    required_params = twitchio.utils.is_inside_class(function) + 1 if skip_parameters is None else skip_parameters

    if len(signature.parameters) < required_params:
        raise TypeError(f"Command signature requires at least {required_params - 1} parameter(s)")

    iterator = iter(signature.parameters.items())
    for _ in range(0, required_params):
        next(iterator)

    for name, parameter in iterator:
        annotation = parameter.annotation

        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue

        annotation = eval_annotation(annotation, globalns, globalns, cache)
        params[name] = parameter.replace(annotation=annotation)

    return params


class CommandErrorPayload:
    """Payload received in the :func:`~twitchio.event_command_error` event.

    Attributes
    ----------
    context: :class:`~.commands.Context`
        The context surrounding command invocation.
    exception: :exc:`.commands.CommandError`
        The exception raised during command invocation.
    """

    __slots__ = ("context", "exception")

    def __init__(self, *, context: Context, exception: CommandError) -> None:
        self.context: Context = context
        self.exception: CommandError = exception


class Command(Generic[Component_T, P]):
    """The TwitchIO ``commands.Command`` class.

    These are usually not created manually, instead see:

    - :func:`.commands.command`

    - :meth:`.commands.Bot.add_command`
    """

    def __init__(
        self,
        callback: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
        *,
        name: str,
        **kwargs: Unpack[CommandOptions],
    ) -> None:
        self._name: str = name
        self.callback = callback
        self._aliases: list[str] = kwargs.get("aliases", [])
        self._guards: list[Callable[..., bool] | Callable[..., CoroC]] = getattr(self._callback, "__command_guards__", [])
        self._buckets: list[Bucket[Context]] = getattr(self._callback, "__command_cooldowns__", [])
        self._guards_after_parsing = kwargs.get("guards_after_parsing", False)
        self._cooldowns_first = kwargs.get("cooldowns_before_guards", False)

        self._injected: Component_T | None = None
        self._error: Callable[[Component_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro] | None = None
        self._extras: dict[Any, Any] = kwargs.get("extras", {})
        self._parent: Group[Component_T, P] | None = kwargs.get("parent")
        self._bypass_global_guards: bool = kwargs.get("bypass_global_guards", False)

    def __repr__(self) -> str:
        return f"Command(name={self._name}, parent={self.parent})"

    def __str__(self) -> str:
        return self._name

    async def __call__(self, context: Context) -> None:
        callback = self._callback(self._injected, context) if self._injected else self._callback(context)  # type: ignore
        await callback

    @property
    def component(self) -> Component_T | None:
        """Property returning the :class:`~.commands.Component` associated with this command or
        ``None`` if there is not one.
        """
        return self._injected

    @property
    def parent(self) -> Group[Component_T, P] | None:
        """Property returning the :class:`~.commands.Group` this sub-command belongs to or ``None`` if it is not apart
        of a group.
        """
        return self._parent

    @property
    def name(self) -> str:
        """Property returning the name of this command."""
        return self._name

    @property
    def aliases(self) -> list[str]:
        """Property returning a copy of the list of aliases associated with this command, if it has any set.

        Could be an empty ``list`` if no aliases have been set.
        """
        return copy.copy(self._aliases)

    @property
    def extras(self) -> MappingProxyType[Any, Any]:
        """Property returning the extras stored on this command as :class:`MappingProxyType`.

        Extras is a dict that can contain any information, and is stored on the command object for future retrieval.
        """
        return MappingProxyType(self._extras)

    @property
    def has_error(self) -> bool:
        """Property returning a ``bool``, indicating whether this command has any local error handlers."""
        return self._error is not None

    @property
    def guards(self) -> list[Callable[..., bool] | Callable[..., CoroC]]:
        """Property returning a list of command specific :func:`.guard`'s added."""
        return self._guards

    @property
    def callback(self) -> Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro]:
        """Property returning the coroutine callback used in invocation.
        E.g. the function you wrap with :func:`.command`.
        """
        return self._callback

    @callback.setter
    def callback(
        self, func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro]
    ) -> None:
        self._callback = func
        unwrap = unwrap_function(func)
        self.module: str = unwrap.__module__

        try:
            globalns = unwrap.__globals__
        except AttributeError:
            globalns = {}

        self._params: dict[str, inspect.Parameter] = get_signature_parameters(func, globalns)

    def _convert_literal_type(
        self, context: Context, param: inspect.Parameter, args: tuple[Any, ...], *, raw: str | None
    ) -> Any:
        name: str = param.name
        result: Any = MISSING

        for arg in reversed(args):
            type_: type = type(arg)
            base = context.bot._base_converter._DEFAULTS.get(type_)

            if base:
                try:
                    result = base(raw)
                except Exception:
                    continue

                break

        if result not in args:
            pretty: str = " | ".join(str(a) for a in args)
            raise BadArgument(f'Failed to convert Literal, expected any [{pretty}], got "{raw}".', name=name, value=raw)

        return result

    async def _do_conversion(self, context: Context, param: inspect.Parameter, *, annotation: Any, raw: str | None) -> Any:
        name: str = param.name

        if isinstance(annotation, UnionType) or getattr(annotation, "__origin__", None) is Union:
            converters = list(annotation.__args__)

            try:
                converters.remove(type(None))
            except ValueError:
                pass

            result: Any = MISSING

            for c in reversed(converters):
                try:
                    result = await self._do_conversion(context, param=param, annotation=c, raw=raw)
                except Exception:
                    continue

            if result is MISSING:
                raise BadArgument(
                    f'Failed to convert argument "{name}" with any converter from Union: {converters}.',
                    name=name,
                    value=raw,
                )

            return result

        if getattr(annotation, "__origin__", None) is Literal:
            result = self._convert_literal_type(context, param, annotation.__args__, raw=raw)
            if result is MISSING:
                raise BadArgument(
                    f"Failed to convert Literal, no converter found for types in {annotation.__args__}",
                    name=name,
                    value=raw,
                )

            return result

        base = context.bot._base_converter._DEFAULTS.get(annotation, None if annotation != param.empty else str)
        if base:
            try:
                result = base(raw)
            except Exception as e:
                raise BadArgument(f'Failed to convert "{name}" to {base}', name=name, value=raw) from e

            return result

        converter = context.bot._base_converter._MAPPING.get(annotation, annotation)

        try:
            result = converter(context, raw)
        except Exception as e:
            raise BadArgument(f'Failed to convert "{name}" to {type(converter)}', name=name, value=raw) from e

        if not asyncio.iscoroutine(result):
            return result

        try:
            result = await result
        except Exception as e:
            raise BadArgument(f'Failed to convert "{name}" to {type(converter)}', name=name, value=raw) from e

        return result

    async def _parse_arguments(self, context: Context) -> ...:
        context._view.skip_ws()
        params: list[inspect.Parameter] = list(self._params.values())

        args: list[Any] = []
        kwargs = {}

        for param in params:
            if param.kind == param.KEYWORD_ONLY:
                raw = context._view.read_rest()

                if raw:
                    result = await self._do_conversion(context, param=param, raw=raw, annotation=param.annotation)
                    kwargs[param.name] = result
                    break

                if param.default == param.empty:
                    raise MissingRequiredArgument(param=param)

                kwargs[param.name] = param.default

            elif param.kind == param.VAR_POSITIONAL:
                packed: list[Any] = []

                while True:
                    context._view.skip_ws()
                    raw = context._view.get_quoted_word()
                    if not raw:
                        break

                    result = await self._do_conversion(context, param=param, raw=raw, annotation=param.annotation)
                    packed.append(result)

                args.extend(packed)
                break

            elif param.kind == param.POSITIONAL_OR_KEYWORD:
                raw = context._view.get_quoted_word()
                context._view.skip_ws()

                if raw:
                    result = await self._do_conversion(context, param=param, raw=raw, annotation=param.annotation)
                    args.append(result)
                    continue

                if param.default == param.empty:
                    raise MissingRequiredArgument(param=param)

                args.append(param.default)

        return args, kwargs

    async def _guard_runner(self, guards: list[Callable[..., bool] | Callable[..., CoroC]], *args: Any) -> None:
        exc_msg = f'The guard predicates for command "{self.name}" failed.'

        for guard in guards:
            try:
                result = guard(*args)
                if asyncio.iscoroutine(result):
                    result = await result
            except GuardFailure:
                raise
            except Exception as e:
                raise GuardFailure(exc_msg, guard=guard) from e

            if result is not True:
                raise GuardFailure(exc_msg, guard=guard)

    async def _run_guards(self, context: Context, *, with_cooldowns: bool = True) -> None:
        if with_cooldowns and self._cooldowns_first:
            await self._run_cooldowns(context)

        # Run global guard first...
        if not self._bypass_global_guards:
            await self._guard_runner([context.bot.global_guard], context)

        # Run component guards next, if this command is in a component...
        if self._injected is not None and self._injected.__all_guards__:
            await self._guard_runner(self._injected.__all_guards__, self._injected, context)

        # Run command specific guards...
        if self._guards:
            await self._guard_runner(self._guards, context)

        if with_cooldowns and not self._cooldowns_first:
            await self._run_cooldowns(context)

    async def _run_cooldowns(self, context: Context) -> None:
        type_ = "group" if isinstance(self, Group) else "command"

        for bucket in self._buckets:
            cooldown = await bucket.get_cooldown(context)
            if cooldown is None:
                continue

            retry = cooldown.update()
            if retry is None:
                continue

            raise CommandOnCooldown(
                f'The {type_} "{self}" is on cooldown. Try again in {retry} seconds.',
                remaining=retry,
                cooldown=cooldown,
            )

    async def _invoke(self, context: Context) -> None:
        context._component = self._injected

        if not self._guards_after_parsing:
            await self._run_guards(context)
            context._passed_guards = True

        try:
            args, kwargs = await self._parse_arguments(context)
        except (ConversionError, MissingRequiredArgument):
            raise
        except Exception as e:
            raise ConversionError("An unknown error occurred converting arguments.") from e

        context._args = args
        context._kwargs = kwargs

        args: list[Any] = [context, *args]
        args.insert(0, self._injected) if self._injected else None

        if self._guards_after_parsing:
            await self._run_guards(context)
            context._passed_guards = True

        if self._guards_after_parsing:
            await self._run_cooldowns(context)

        try:
            await context.bot.before_invoke(context)
            if self._injected is not None:
                await self._injected.component_before_invoke(context)
        except Exception as e:
            raise CommandHookError(str(e), e) from e

        callback = self._callback(*args, **kwargs)  # type: ignore

        try:
            await callback
        except Exception as e:
            raise CommandInvokeError(msg=str(e), original=e) from e

    async def invoke(self, context: Context) -> None:
        try:
            await self._invoke(context)
        except CommandError as e:
            await self._dispatch_error(context, e)
        except Exception as e:
            error = CommandInvokeError(str(e), original=e)
            await self._dispatch_error(context, error)

    async def _dispatch_error(self, context: Context, exception: CommandError) -> None:
        payload = CommandErrorPayload(context=context, exception=exception)

        if self._error is not None:
            if self._injected:
                await self._error(self._injected, payload)  # type: ignore
            else:
                await self._error(payload)  # type: ignore

        result = True
        if self._injected is not None:
            result = await self._injected.component_command_error(payload=payload)

        # If the component error handler returns explicit False, we won't further dispatch the error...
        if result is False:
            return

        context.error_dispatched = True
        context.bot.dispatch("command_error", payload=payload)

    def error(
        self,
        func: Callable[[Component_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro],
    ) -> Callable[[Component_T, CommandErrorPayload], Coro] | Callable[[CommandErrorPayload], Coro]:
        """|deco|

        A decorator which adds a local error handler to this command.

        Similar to :meth:`~commands.Bot.event_command_error` except local to this command.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Command specific "error" callback for "{self._name}" must be a coroutine function.')

        self._error = func
        return func

    def before_invoke(self) -> None: ...

    def after_invoke(self) -> None: ...


class Mixin(Generic[Component_T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        case_: bool = kwargs.pop("case_insensitive", False)
        self._case_insensitive: bool = case_
        self._commands: dict[str, Command[Component_T, ...]] = {} if not case_ else _CaseInsensitiveDict()

        super().__init__(*args, **kwargs)

    @property
    def case_insensitive(self) -> bool:
        """Property returning a bool indicating whether this Mixin is using case insensitive commands."""
        return self._case_insensitive

    def add_command(self, command: Command[Component_T, ...], /) -> None:
        """Add a :class:`~.commands.Command` object to the mixin.

        For group commands you would usually use the :meth:`~.Group.command` decorator instead.

        See: :func:`~.commands.command`.
        """
        if not isinstance(command, Command):  # type: ignore
            raise TypeError(f'Expected "{Command}" got "{type(command)}".')

        if command.name in self._commands:
            raise CommandExistsError(f'A command with the name "{command.name}" is already registered.')

        name: str = command.name
        self._commands[name] = command

        for alias in command.aliases:
            if alias in self._commands:
                self.remove_command(name)
                raise CommandExistsError(f'A command with the alias "{alias}" already exists.')

            self._commands[alias] = command

    def remove_command(self, name: str, /) -> Command[Any, ...] | None:
        """Remove a :class:`~.commands.Command` object from the mixin by it's name.

        Parameters
        ----------
        name: str
            The name of the :class:`~.commands.Command` to remove that was previously added.

        Returns
        -------
        None
            No commands with provided name were found.
        Command
            The :class:`~.commands.Command` which was removed.
        """
        command = self._commands.pop(name, None)
        if not command:
            return

        if name in command.aliases:
            return command

        for alias in command.aliases:
            cmd = self._commands.pop(alias, None)

            if cmd is not None and cmd != command:
                self._commands[alias] = cmd

        return command


def command(
    name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None, **kwargs: Any
) -> Any:
    """|deco|

    A decorator which turns a coroutine into a :class:`~.commands.Command` which can be used in
    :class:`~.commands.Component`'s or added to a :class:`~.commands.Bot`.

    Commands are powerful tools which enable bots to process messages and convert the content into mangeable arguments and
    :class:`~.commands.Context` which is parsed to the wrapped callback coroutine.

    Commands also benefit to such things as :func:`~.guard`'s and the ``before`` and ``after`` hooks on both,
    :class:`~.commands.Component` and :class:`~.commands.Bot`.

    Command callbacks should take in at minimum one parameter, which is :class:`~.commands.Context` and is always
    passed.

    Parameters
    ----------
    name: str | None
        An optional custom name to use for this command. If this is ``None`` or not passed, the coroutine function name
        will be used instead.
    aliases: list[str] | None
        An optional list of aliases to use for this command.
    extras: dict
        A dict of any data which is stored on this command object. Can be used anywhere you have access to the command object,
        E.g. in a ``before`` or ``after`` hook.
    guards_after_parsing: bool
        An optional bool, indicating whether to run guards after argument parsing has completed.
        Defaults to ``False``, which means guards will be checked **before** command arguments are parsed and available.
    cooldowns_before_guards: bool
        An optional bool, indicating whether to run cooldown guards after all other guards succeed.
        Defaults to ``False``, which means cooldowns will be checked **after** all guards have successfully completed.
    bypass_global_guards: bool
        An optional bool, indicating whether the command should bypass the :meth:`.Bot.global_guard`.
        Defaults to ``False``.

    Examples
    --------

    .. code:: python3

        # When added to a Bot or used in a component you can invoke this command with your prefix, E.g:
        # !hi or !howdy

        @commands.command(name="hi", aliases=["hello", "howdy"])
        async def hi_command(ctx: commands.Context) -> None:
            ...

    Raises
    ------
    ValueError
        The callback being wrapped is already a command.
    TypeError
        The callback must be a coroutine function.
    """

    def wrapper(
        func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
    ) -> Command[Any, ...]:
        if isinstance(func, Command):
            raise ValueError(f'Callback "{func._callback}" is already a Command.')  # type: ignore

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Command callback for "{func.__qualname__}" must be a coroutine function.')

        func_name = func.__name__
        name_ = name.strip().replace(" ", "") or func_name if name else func_name

        return Command(name=name_, callback=func, aliases=aliases or [], extras=extras or {}, **kwargs)

    return wrapper


def group(
    name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None, **kwargs: Any
) -> Any:
    """|deco|

    A decorator which turns a coroutine into a :class:`~.commands.Group` which can be used in
    :class:`~.commands.Component`'s or added to a :class:`~.commands.Bot`.

    Group commands act as parents to other commands (sub-commands).

    See: :func:`.~commands.command` for more information on commands.

    Group commands are a powerful way of grouping similar sub-commands into a more user friendly interface.

    Group callbacks should take in at minimum one parameter, which is :class:`~.commands.Context` and is always
    passed.

    Parameters
    ----------
    name: str | None
        An optional custom name to use for this group. If this is ``None`` or not passed, the coroutine function name
        will be used instead.
    aliases: list[str] | None
        An optional list of aliases to use for this group.
    extras: dict
        A dict of any data which is stored on this command object. Can be used anywhere you have access to the command object,
        E.g. in a ``before`` or ``after`` hook.
    invoke_fallback: bool
        An optional bool which tells the parent to be invoked as a fallback when no sub-command can be found.
        Defaults to ``False``.
    apply_cooldowns: bool
        An optional bool indicating whether the cooldowns on this group are checked before invoking any sub commands.
        Defaults to ``True``.
    apply_guards: bool
        An optional bool indicating whether the guards on this group should be ran before invoking any sub commands.
        Defaults to ``True``.

    Examples
    --------

    .. code:: python3

        # When added to a Bot or used in a component you can invoke this group and sub-commands with your prefix, E.g:
        # !socials
        # !socials discord OR !socials twitch
        # When invoke_fallback is True, the parent command will be invoked if a sub-command cannot be found...

        @commands.group(name="socials", invoke_fallback=True)
        async def socials_group(ctx: commands.Context) -> None:
            await ctx.send("https://discord.gg/RAKc3HF, https://twitch.tv/chillymosh, ...")

        @socials_group.command(name="discord", aliases=["disco"])
        async def socials_discord(ctx: commands.Context) -> None:
            await ctx.send("https://discord.gg/RAKc3HF")

        @socials_group.command(name="twitch")
        async def socials_twitch(ctx: commands.Context) -> None:
            await ctx.send("https://twitch.tv/chillymosh")

    Raises
    ------
    ValueError
        The callback being wrapped is already a command or group.
    TypeError
        The callback must be a coroutine function.
    """

    def wrapper(
        func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
    ) -> Group[Any, ...]:
        if isinstance(func, Command):
            raise ValueError(f'Callback "{func._callback.__name__}" is already a Command.')  # type: ignore

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'Group callback for "{func.__qualname__}" must be a coroutine function.')

        func_name = func.__name__
        name_ = name.strip().replace(" ", "") or func_name if name else func_name

        return Group(name=name_, callback=func, aliases=aliases or [], extras=extras or {}, **kwargs)

    return wrapper


class Group(Mixin[Component_T], Command[Component_T, P]):
    """The TwitchIO ``commands.Command`` class.

    These are usually not created manually, instead see:

    - :func:`.commands.group`

    - :meth:`.commands.Bot.add_command`
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._invoke_fallback: bool = kwargs.get("invoke_fallback", False)
        self._apply_cooldowns: bool = kwargs.get("apply_cooldowns", True)
        self._apply_guards: bool = kwargs.get("apply_guards", True)

    def walk_commands(self) -> Generator[Command[Component_T, P] | Group[Component_T, P]]:
        """A generator which recursively walks through the sub-commands and sub-groups of this group."""
        for command in self._commands.values():
            yield command

            if isinstance(command, Group):
                yield from command.walk_commands()

    async def _invoke(self, context: Context) -> None:
        view = context._view
        view.skip_ws()
        trigger = view.get_word()

        next_ = self._commands.get(trigger, None)
        context._command = next_ or self
        context._invoked_subcommand = next_
        context._invoked_with = f"{context._invoked_with} {trigger}"
        context._subcommand_trigger = trigger or None

        if not trigger or (not next_ and self._invoke_fallback):
            view.undo()
            await super()._invoke(context=context)

        elif next_:
            if self._apply_cooldowns:
                await super()._run_cooldowns(context)

            if self._apply_guards:
                await super()._run_guards(context, with_cooldowns=False)

            await next_.invoke(context=context)

        else:
            raise CommandNotFound(f'The sub-command "{trigger}" for group "{self._name}" was not found.')

    async def invoke(self, context: Context) -> None:
        try:
            await self._invoke(context)
        except CommandError as e:
            await self._dispatch_error(context, e)

    def command(
        self,
        name: str | None = None,
        aliases: list[str] | None = None,
        extras: dict[Any, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """|deco|

        A decorator which adds a :class:`~.commands.Command` as a sub-command to this group.

        See: :class:`~.commands.command` for more information on commands

        Examples
        --------

        .. code:: python3

            # When added to a Bot or used in a component you can invoke this group and sub-commands with your prefix, E.g:
            # !socials
            # !socials discord OR !socials twitch
            # When invoke_fallback is True, the parent command will be invoked if a sub-command cannot be found...

            @commands.group(name="socials", invoke_fallback=True)
            async def socials_group(ctx: commands.Context) -> None:
                await ctx.send("https://discord.gg/RAKc3HF, https://twitch.tv/chillymosh, ...")

            @socials_group.command(name="discord", aliases=["disco"])
            async def socials_discord(ctx: commands.Context) -> None:
                await ctx.send("https://discord.gg/RAKc3HF")

            @socials_group.command(name="twitch")
            async def socials_twitch(ctx: commands.Context) -> None:
                await ctx.send("https://twitch.tv/chillymosh")

        Parameters
        ----------
        name: str | None
            An optional custom name to use for this sub-command. If this is ``None`` or not passed, the coroutine function name
            will be used instead.
        aliases: list[str] | None
            An optional list of aliases to use for this command.
        extras: dict
            A dict of any data which is stored on this command object. Can be used anywhere you have access to the command object,
            E.g. in a ``before`` or ``after`` hook.
        guards_after_parsing: bool
            An optional bool, indicating whether to run guards after argument parsing has completed.
            Defaults to ``False``, which means guards will be checked **before** command arguments are parsed and available.
        cooldowns_before_guards: bool
            An optional bool, indicating whether to run cooldown guards after all other guards succeed.
            Defaults to ``False``, which means cooldowns will be checked **after** all guards have successfully completed.
        bypass_global_guards: bool
            An optional bool, indicating whether the command should bypass the :func:`~.commands.Bot.global_guard`.
            Defaults to ``False``.
        """

        def wrapper(
            func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
        ) -> Command[Any, ...]:
            new = command(name=name, aliases=aliases, extras=extras, parent=self, **kwargs)(func)

            self.add_command(new)
            return new

        return wrapper

    def group(
        self, name: str | None = None, aliases: list[str] | None = None, extras: dict[Any, Any] | None = None, **kwargs: Any
    ) -> Any:
        """|deco|

        A decorator which adds a :class:`~.commands.Group` as a sub-group to this group.

        Examples
        --------

        .. code:: python3

            # When added to a Bot or used in a component you can invoke this group and sub-commands with your prefix, E.g:
            # !socials
            # !socials discord OR !socials twitch
            # !socials discord one OR !socials discord two
            # When invoke_fallback is True, the parent command will be invoked if a sub-command cannot be found...

            @commands.group(name="socials", invoke_fallback=True)
            async def socials_group(ctx: commands.Context) -> None:
                await ctx.send("https://discord.gg/RAKc3HF, https://twitch.tv/chillymosh, ...")

            @socials_group.command(name="twitch")
            async def socials_twitch(ctx: commands.Context) -> None:
                await ctx.send("https://twitch.tv/chillymosh")

            # Add a group to our parent group which further separates the commands...
            @socials_group.group(name="discord", aliases=["disco"], invoke_fallback=True)
            async def socials_discord(ctx: commands.Context) -> None:
                await ctx.send("https://discord.gg/RAKc3HF, https://discord.gg/...")

            @socials_discord.command(name="one", aliases=["1"])
            async def socials_discord_one(ctx: commands.Context) -> None:
                await ctx.send("https://discord.gg/RAKc3HF")

            @socials_discord.command(name="two", aliases=["2"])
            async def socials_discord_two(ctx: commands.Context) -> None:
                await ctx.send("https://discord.gg/...")

        Parameters
        ----------
        name: str | None
            An optional custom name to use for this group. If this is ``None`` or not passed, the coroutine function name
            will be used instead.
        aliases: list[str] | None
            An optional list of aliases to use for this group.
        extras: dict
            A dict of any data which is stored on this command object. Can be used anywhere you have access to the command object,
            E.g. in a ``before`` or ``after`` hook.
        invoke_fallback: bool
            An optional bool which tells the parent to be invoked as a fallback when no sub-command can be found.
            Defaults to ``False``.
        apply_cooldowns: bool
            An optional bool indicating whether the cooldowns on this group are checked before invoking any sub commands.
            Defaults to ``True``.
        apply_guards: bool
            An optional bool indicating whether the guards on this group should be ran before invoking any sub commands.
            Defaults to ``True``.
        """

        def wrapper(
            func: Callable[Concatenate[Component_T, Context, P], Coro] | Callable[Concatenate[Context, P], Coro],
        ) -> Command[Any, ...]:
            new = group(name=name, aliases=aliases, extras=extras, parent=self, **kwargs)(func)

            self.add_command(new)
            return new

        return wrapper


def guard(predicate: Callable[..., bool] | Callable[..., CoroC]) -> Any:
    """A function which takes in a predicate as a either a standard function *or* coroutine function which should
    return either ``True`` or ``False``, and adds it to your :class:`~.commands.Command` as a guard.

    The predicate function should take in one parameter, :class:`.commands.Context`, the context used in command invocation.

    If the predicate function returns ``False``, the chatter will not be able to invoke the command and an error will be
    raised. If the predicate function returns ``True`` the chatter will be able to invoke the command,
    assuming all the other guards also pass their predicate checks.

    Guards can also raise custom exceptions, however your exception should inherit from :exc:`~.commands.GuardFailure` which
    will allow your exception to propagate successfully to error handlers.

    Any number of guards can be used on a :class:`~.commands.Command` and all must pass for the command to be successfully
    invoked.

    All guards are executed in the specific order displayed below:

    - **Global Guard:** :meth:`.commands.Bot.global_guard`

    - **Component Guards:** :meth:`.commands.Component.guard`

    - **Command Specific Guards:** The command specific guards, E.g. by using this or other guard decorators on a command.

    .. note::

        Guards are checked and ran **after** all command arguments have been parsed and converted, but **before** any
        ``before_invoke`` hooks are ran.

    It is easy to create simple decorator guards for your commands, see the examples below.

    Some built-in helper guards have been premade, and are listed below:

    - :func:`~.commands.is_staff`

    - :func:`~.commands.is_broadcaster`

    - :func:`~.commands.is_moderator`

    - :func:`~.commands.is_vip`

    - :func:`~.commands.is_elevated`

    Example
    -------

    .. code:: python3

        def is_cool():
            def predicate(ctx: commands.Context) -> bool:
                return ctx.chatter.name.startswith("cool")

            return commands.guard(predicate)

        @is_cool()
        @commands.command()
        async def cool(self, ctx: commands.Context) -> None:
            await ctx.reply("You are cool...!")

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def wrapper(func: Any) -> Any:
        if isinstance(func, Command):
            func._guards.append(predicate)

        else:
            try:
                func.__command_guards__.append(predicate)
            except AttributeError:
                func.__command_guards__ = [predicate]

        return func  # type: ignore

    return wrapper


def is_owner() -> Any:
    """|deco|

    A decorator which adds a :func:`~.commands.guard` to a :class:`~.commands.Command`.

    This guards adds a predicate which prevents any chatter from using a command
    who does is not the owner of this bot. You can set the owner of the bot via :attr:`~.commands.Bot.owner_id`.

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def predicate(context: Context) -> bool:
        return context.chatter.id == context.bot.owner_id

    return guard(predicate)


def is_staff() -> Any:
    """|deco|

    A decorator which adds a :func:`~.commands.guard` to a :class:`~.commands.Command`.

    This guards adds a predicate which prevents any chatter from using a command
    who does not possess the ``Twitch Staff`` badge.

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def predicate(context: Context) -> bool:
        return context.chatter.staff

    return guard(predicate)


def is_broadcaster() -> Any:
    """|deco|

    A decorator which adds a :func:`~.commands.guard` to a :class:`~.commands.Command`.

    This guards adds a predicate which prevents any chatter from using a command
    who does not possess the ``Broadcaster`` badge.

    See also, :func:`~.commands.is_elevated` for a guard to allow the ``broadcaster``, any ``moderator`` or ``VIP`` chatter
    to use the command.

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def predicate(context: Context) -> bool:
        return context.chatter.id == context.broadcaster.id

    return guard(predicate)


def is_moderator() -> Any:
    """|deco|

    A decorator which adds a :func:`~.commands.guard` to a :class:`~.commands.Command`.

    This guards adds a predicate which prevents any chatter from using a command
    who does not possess the ``Moderator`` badge.

    See also, :func:`~.commands.is_elevated` for a guard to allow the ``broadcaster``, any ``moderator`` or ``VIP`` chatter
    to use the command.

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def predicate(context: Context) -> bool:
        return context.chatter.moderator

    return guard(predicate)


def is_vip() -> Any:
    """|deco|

    A decorator which adds a :func:`~.commands.guard` to a :class:`~.commands.Command`.

    This guards adds a predicate which prevents any chatter from using a command who does not possess the ``VIP`` badge.

    .. note::

        Due to a Twitch limitation, moderators and broadcasters can not be VIPs, another guard has been made to help aid
        in allowing these members to also be seen as VIP, see: :func:`~.commands.is_elevated`.

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def predicate(context: Context) -> bool:
        return context.chatter.vip

    return guard(predicate)


def is_elevated() -> Any:
    """|deco|

    A decorator which adds a :func:`~.commands.guard` to a :class:`~.commands.Command`.

    This guards adds a predicate which prevents any chatter from using a command who does not posses one or more of the
    folowing badges: ``broadcaster``, ``moderator`` or ``VIP``.

    .. important::

        The chatter only needs **1** of the badges to pass the guard.

    Example
    -------

        .. code:: python3

            # This command can be run by anyone with broadcaster, moderator OR VIP status...

            @commands.is_elevated()
            @commands.command()
            async def test(self, ctx: commands.Context) -> None:
                await ctx.reply("You are allowed to use this command!")

    Raises
    ------
    GuardFailure
        The guard predicate returned ``False`` and prevented the chatter from using the command.
    """

    def predicate(context: Context) -> bool:
        chatter: Chatter = context.chatter
        return chatter.moderator or chatter.vip

    return guard(predicate)


def cooldown(*, base: type[BaseCooldown] = Cooldown, key: KeyT = BucketType.chatter, **kwargs: Any) -> Any:
    """|deco|

    A decorator which adds a :class:`~.commands.Cooldown` to a :class:`~.Command`.

    The parameters of this decorator may change depending on the class passed to the ``base`` parameter.
    The parameters needed for the default built-in classes are listed instead.

    When a command is on cooldown or ratelimited, the :exc:`~.commands.CommandOnCooldown` exception is raised and propagated to all
    error handlers.

    Parameters
    ----------
    base: :class:`~.commands.BaseCooldown`
        Optional base class to use to construct the cooldown. By default this is the :class:`~.commands.Cooldown` class, which
        implements a ``Token Bucket Algorithm``. Another option is the :class:`~.commands.GCRACooldown` class which implements
        the Generic Cell Rate Algorithm, which can be thought of as similar to a continuous state leaky-bucket algorithm, but
        instead of updating internal state, calculates a Theoretical Arrival Time (TAT), making it more performant,
        and dissallowing short bursts of requests. However before choosing a class, consider reading more information on the
        differences between the ``Token Bucket`` and ``GCRA``.

        A custom class which inherits from :class:`~.commands.BaseCooldown` could also be used. All ``keyword-arguments``
        passed to this decorator, minus ``base`` and ``key`` will also be passed to the constructor of the cooldown base class.

        Useful if you would like to implement your own ratelimiting algorithm.
    key: Callable[[Any], Hashable] | Callable[[Any], Coroutine[Any, Any, Hashable]] | :class:`~.commands.BucketType`
        A regular or coroutine function, or :class:`~.commands.BucketType` which must return a :class:`typing.Hashable`
        used to determine the keys for the cooldown.

        The :class:`~.commands.BucketType` implements some default strategies. If your function returns ``None`` the cooldown
        will be bypassed. See below for some examples. By default the key is :attr:`~.commands.BucketType.chatter`.
    rate: int
        An ``int`` indicating how many times a command should be allowed ``per`` x amount of time. Note the relevance and
        effects of both ``rate`` and ``per`` change slightly between algorithms.
    per: float | datetime.timedelta
        A ``float`` or :class:`datetime.timedelta` indicating the length of the time (as seconds) a cooldown window is open.

        E.g. if ``rate`` is ``2`` and ``per`` is ``60.0``, using the default :class:`~.commands.Cooldown` class, you will only
        be able to send ``two`` commands ``per 60 seconds``, with the window starting when you send the first command.

    Examples
    --------

    Using the default :class:`~.commands.Cooldown` to allow the command to be ran twice by an individual chatter, every 10 seconds.

    .. code:: python3

        @commands.command()
        @commands.cooldown(rate=2, per=10, key=commands.BucketType.chatter)
        async def hello(ctx: commands.Context) -> None:
            ...

    Using a custom key to bypass cooldowns for certain users.

    .. code:: python3

        def bypass_cool(ctx: commands.Context) -> typing.Hashable | None:
            # Returning None will bypass the cooldown

            if ctx.chatter.name.startswith("cool"):
                return None

            # For everyone else, return and call the default chatter strategy
            # This strategy returns a tuple of (channel/broadcaster.id, chatter.id) to use as the unique key
            return commands.BucketType.chatter(ctx)

        @commands.command()
        @commands.cooldown(rate=2, per=10, key=bypass_cool)
        async def hello(ctx: commands.Context) -> None:
            ...

    Using a custom function to implement dynamic keys.

    .. code:: python3

        async def custom_key(ctx: commands.Context) -> typing.Hashable | None:
            # As an example, get some user info from a database with the chatter...
            # This is just to showcase a use for an async version of a custom key...
            ...

            # Example column in database...
            if row["should_bypass_cooldown"]:
                return None

            # Note: Returing chatter.id is equivalent to commands.BucketType.user NOT commands.BucketType.chatter
            # which uses the channel ID and User ID together as the key...
            return ctx.chatter.id

        @commands.command()
        @commands.cooldown(rate=1, per=300, key=custom_key)
        async def hello(ctx: commands.Context) -> None:
            ...
    """
    bucket_: Bucket[Context] = Bucket.from_cooldown(base=base, key=key, **kwargs)

    def wrapper(func: Any) -> Any:
        nonlocal bucket_

        if isinstance(func, Command):
            func._buckets.append(bucket_)
        else:
            try:
                func.__command_cooldowns__.append(bucket_)
            except AttributeError:
                func.__command_cooldowns__ = [bucket_]

        return func  # type: ignore

    return wrapper


class _CaseInsensitiveDict(dict[str, VT]):
    def __contains__(self, key: object) -> bool:
        return super().__contains__(key.casefold()) if isinstance(key, str) else False

    def __delitem__(self, key: str) -> None:
        return super().__delitem__(key.casefold())

    def __getitem__(self, key: str) -> VT:
        return super().__getitem__(key.casefold())

    @overload
    def get(self, key: str, /) -> VT | None: ...

    @overload
    def get(self, key: str, default: VT, /) -> VT: ...

    @overload
    def get(self, key: str, default: DT, /) -> VT | DT: ...

    def get(self, key: str, default: DT = None, /) -> VT | DT:
        return super().get(key.casefold(), default)

    @overload
    def pop(self, key: str, /) -> VT: ...

    @overload
    def pop(self, key: str, default: VT, /) -> VT: ...

    @overload
    def pop(self, key: str, default: DT, /) -> VT | DT: ...

    def pop(self, key: str, default: DT = MISSING, /) -> VT | DT:
        if default is MISSING:
            return super().pop(key.casefold())

        return super().pop(key.casefold(), default)

    def __setitem__(self, key: str, value: VT) -> None:
        super().__setitem__(key.casefold(), value)
