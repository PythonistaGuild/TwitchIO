"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

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

from __future__ import annotations
import inspect

import itertools
import copy
import types
from typing import Any, Union, Optional, Callable, Awaitable, Tuple, TYPE_CHECKING, List, Type, Set, TypeVar
from typing_extensions import Literal

from twitchio.abcs import Messageable
from .cooldowns import *
from .errors import *
from . import builtin_converter

if TYPE_CHECKING:
    import sys

    from twitchio import Message, Chatter, PartialChatter, Channel, User, PartialUser
    from . import Cog, Bot
    from .stringparser import StringParser

    if sys.version_info >= (3, 10):
        UnionT = Union[types.UnionType, Union]
    else:
        UnionT = Union


__all__ = ("Command", "command", "Group", "Context", "cooldown")


class EmptyArgumentSentinel:
    def __repr__(self) -> str:
        return "<EMPTY>"

    def __eq__(self, __value: object) -> bool:
        return False


EMPTY = EmptyArgumentSentinel()


def _boolconverter(_, param: str):
    param = param.lower()
    if param in {"yes", "y", "1", "true", "on"}:
        return True
    elif param in {"no", "n", "0", "false", "off"}:
        return False
    raise BadArgument(f"Expected a boolean value, got {param}")


class Command:
    """A class for implementing bot commands.

    Parameters
    ------------
    name: :class:`str`
        The name of the command.
    func: :class:`Callable`
        The coroutine that executes when the command is invoked.

    Attributes
    ------------
    name: :class:`str`
        The name of the command.
    cog: :class:`~twitchio.ext.commands.Cog`
        The cog this command belongs to.
    aliases: Optional[Union[:class:`list`, :class:`tuple`]]
        Aliases that can be used to also invoke the command.
    """

    def __init__(self, name: str, func: Callable, **attrs) -> None:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Command callback must be a coroutine.")
        self._callback = func
        self._checks = []
        self._cooldowns = []
        self._name = name

        self._instance = None
        self.cog = None
        self.parent: Optional[Group] = attrs.get("parent")

        try:
            self._checks.extend(func.__checks__)  # type: ignore
        except AttributeError:
            pass
        try:
            self._cooldowns.extend(func.__cooldowns__)  # type: ignore
        except AttributeError:
            pass
        self.aliases = attrs.get("aliases", None)
        sig = inspect.signature(func)
        self.params = sig.parameters.copy()  # type: ignore

        self.event_error = None
        self._before_invoke = None
        self._after_invoke = None
        self.no_global_checks = attrs.get("no_global_checks", False)

        for key, value in self.params.items():
            if isinstance(value.annotation, str):
                self.params[key] = value.replace(annotation=eval(value.annotation, func.__globals__))  # type: ignore

    @property
    def name(self) -> str:
        return self._name

    @property
    def full_name(self) -> str:
        if not self.parent:
            return self._name
        return f"{self.parent.full_name} {self._name}"

    def _is_optional_argument(self, converter: Any):
        return (getattr(converter, "__origin__", None) is Union or isinstance(converter, types.UnionType)) and type(
            None
        ) in converter.__args__

    def resolve_union_callback(self, name: str, converter: UnionT) -> Callable[[Context, str], Any]:
        # print(type(converter), converter.__args__)

        args = converter.__args__  # type: ignore # pyright doesnt like this

        async def _resolve(context: Context, arg: str) -> Any:
            t = EMPTY

            for original in args:
                underlying = self._resolve_converter(name, original, context)

                try:
                    t: Any = underlying(context, arg)
                    if inspect.iscoroutine(t):
                        t = await t

                    break
                except Exception as l:
                    t = EMPTY  # thisll get changed when t is a coroutine, but is still invalid, so roll it back
                    continue

            if t is EMPTY:
                raise UnionArgumentParsingFailed(name, args)

            return t

        return _resolve

    def resolve_optional_callback(self, name: str, converter: Any, context: Context) -> Callable[[Context, str], Any]:
        underlying = self._resolve_converter(name, converter.__args__[0], context)

        async def _resolve(context: Context, arg: str) -> Any:
            try:
                t: Any = underlying(context, arg)
                if inspect.iscoroutine(t):
                    t = await t

            except Exception:
                return EMPTY  # instruct the parser to roll back and ignore this argument

            return t

        return _resolve

    def _resolve_converter(
        self, name: str, converter: Union[Callable, Awaitable, type], ctx: Context
    ) -> Callable[..., Any]:
        if (
            isinstance(converter, type)
            and converter.__module__.startswith("twitchio")
            and converter in builtin_converter._mapping
        ):
            return self._convert_builtin_type(name, converter, builtin_converter._mapping[converter])

        elif converter is bool:
            converter = self._convert_builtin_type(name, bool, _boolconverter)

        elif converter in (str, int):
            original: type[str | int] = converter  # type: ignore
            converter = self._convert_builtin_type(name, original, lambda _, arg: original(arg))

        elif self._is_optional_argument(converter):
            return self.resolve_optional_callback(name, converter, ctx)

        elif isinstance(converter, types.UnionType) or getattr(converter, "__origin__", None) is Union:
            return self.resolve_union_callback(name, converter)  # type: ignore

        elif hasattr(converter, "__metadata__"):  # Annotated
            annotated = converter.__metadata__  # type: ignore
            return self._resolve_converter(name, annotated[0], ctx)

        return converter  # type: ignore

    def _convert_builtin_type(
        self,
        arg_name: str,
        original: type,
        converter: Union[Callable[[Context, str], Any], Callable[[Context, str], Awaitable[Any]]],
    ) -> Callable[[Context, str], Awaitable[Any]]:
        async def resolve(ctx, arg: str) -> Any:
            try:
                t = converter(ctx, arg)

                if inspect.iscoroutine(t):
                    t = await t

                return t
            except Exception as e:
                raise ArgumentParsingFailed(
                    f"Failed to convert `{arg}` to expected type {original.__name__} for argument `{arg_name}`",
                    original=e,
                    argname=arg_name,
                    expected=original,
                ) from e

        return resolve

    async def _convert_types(self, context: Context, param: inspect.Parameter, parsed: str) -> Any:
        converter = param.annotation

        if converter is param.empty:
            if param.default in (param.empty, None):
                converter = str
            else:
                converter = type(param.default)

        true_converter = self._resolve_converter(param.name, converter, context)

        try:
            argument = true_converter(context, parsed)
            if inspect.iscoroutine(argument):
                argument = await argument
        except BadArgument as e:
            if e.name is None:
                e.name = param.name

            raise
        except Exception as e:
            raise ArgumentParsingFailed(
                f"Failed to parse `{parsed}` for argument {param.name}", original=e, argname=param.name, expected=None
            ) from e
        return argument

    async def parse_args(self, context: Context, instance: Optional[Cog], parsed: dict, index=0) -> Tuple[list, dict]:
        if isinstance(self, Group):
            parsed = parsed.copy()
        iterator = iter(self.params.items())
        args = []
        kwargs = {}

        try:
            next(iterator)
            if instance:
                next(iterator)
        except StopIteration:
            raise TwitchCommandError("self or ctx is a required argument which is missing.")
        for _, param in iterator:
            index += 1
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                try:
                    argument = parsed.pop(index)
                except (KeyError, IndexError):
                    if self._is_optional_argument(param.annotation):  # parameter is optional and at the end.
                        args.append(param.default if param.default is not param.empty else None)
                        continue

                    if param.default is param.empty:
                        raise MissingRequiredArgument(argname=param.name)

                    args.append(param.default)
                else:
                    _parsed_arg = await self._convert_types(context, param, argument)

                    if _parsed_arg is EMPTY:
                        parsed[index] = argument
                        index -= 1
                        args.append(param.default if param.default is not param.empty else None)

                        continue
                    else:
                        args.append(_parsed_arg)

            elif param.kind == param.KEYWORD_ONLY:
                rest = " ".join(parsed.values())
                if rest.startswith(" "):
                    rest = rest.lstrip(" ")
                if rest:
                    rest = await self._convert_types(context, param, rest)
                elif param.default is param.empty:
                    raise MissingRequiredArgument(argname=param.name)
                else:
                    rest = param.default
                kwargs[param.name] = rest
                parsed.clear()
                break
            elif param.kind == param.VAR_POSITIONAL:
                args.extend([await self._convert_types(context, param, argument) for argument in parsed.values()])
                parsed.clear()
                break
        if parsed:
            pass  # TODO Raise Too Many Arguments.
        return args, kwargs

    async def invoke(self, context: Context, *, index=0) -> None:
        # TODO Docs
        if not context.view:
            return

        async def try_run(func, *, to_command=False):
            try:
                await func
            except Exception as _e:
                if not to_command:
                    context.bot.run_event("error", _e)
                else:
                    context.bot.run_event("command_error", context, _e)

        try:
            args, kwargs = await self.parse_args(context, self._instance, context.view.words, index=index)
        except (MissingRequiredArgument, BadArgument) as e:
            if self.event_error:
                args_ = [self._instance, context] if self._instance else [context]
                await try_run(self.event_error(*args_, e))

            context.bot.run_event("command_error", context, e)
            return

        context.args, context.kwargs = args, kwargs
        check_result = await self.handle_checks(context)

        if check_result is not True:
            context.bot.run_event("command_error", context, check_result)
            return
        limited = self._run_cooldowns(context)

        if limited:
            context.bot.run_event("command_error", context, limited[0])
            return
        instance = self._instance
        args = [instance, context] if instance else [context]
        await try_run(context.bot.global_before_invoke(context))

        if self._before_invoke:
            await try_run(self._before_invoke(*args), to_command=True)
        try:
            await self._callback(*args, *context.args, **context.kwargs)
        except Exception as e:
            if self.event_error:
                await try_run(self.event_error(*args, e))
            context.bot.run_event("command_error", context, e)
        else:
            context.bot.run_event("command_complete", context)
        # Invoke our after command hooks
        if self._after_invoke:
            await try_run(self._after_invoke(*args), to_command=True)
        await try_run(context.bot.global_after_invoke(context))

    def _run_cooldowns(self, context: Context) -> Optional[List[CommandOnCooldown]]:
        try:
            buckets = self._cooldowns[0].get_buckets(context)
        except IndexError:
            return None
        expired = []

        try:
            for bucket in buckets:
                bucket.update_bucket(context)
        except CommandOnCooldown as e:
            expired.append(e)
        return expired

    async def handle_checks(self, context: Context) -> Union[Literal[True], Exception]:
        # TODO Docs

        if not self.no_global_checks:
            checks = [predicate for predicate in itertools.chain(context.bot._checks, self._checks)]
        else:
            checks = self._checks
        try:
            for predicate in checks:
                result = predicate(context)

                if inspect.isawaitable(result):
                    result = await result  # type: ignore
                if not result:
                    raise CheckFailure(f"The check {predicate} for command {self.name} failed.")
            if self.cog and not await self.cog.cog_check(context):
                raise CheckFailure(f"The cog check for command <{self.name}> failed.")
            return True
        except Exception as e:
            return e

    async def __call__(self, context: Context, *, index=0) -> None:
        await self.invoke(context, index=index)


class Group(Command):
    def __init__(self, *args, invoke_with_subcommand=False, **kwargs) -> None:
        super(Group, self).__init__(*args, **kwargs)
        self._sub_commands = {}
        self._invoke_with_subcommand = invoke_with_subcommand

    async def __call__(self, context: Context, *, index=0) -> None:
        if not context.view:
            return
        if not context.view.words:
            return await self.invoke(context, index=index)
        arg: Tuple[int, str] = list(context.view.words.items())[0]  # type: ignore
        if arg[1] in self._sub_commands:
            _ctx = copy.copy(context)
            _ctx.view = _ctx.view.copy()
            _ctx.view.words.pop(arg[0])
            await self._sub_commands[arg[1]](_ctx, index=arg[0])

            if self._invoke_with_subcommand:
                await self.invoke(context, index=index)
        else:
            await self.invoke(context, index=index)

    def command(
        self, *, name: str = None, aliases: Union[list, tuple] = None, cls=Command, no_global_checks=False
    ) -> Callable[[Callable], Command]:
        if cls and not inspect.isclass(cls):
            raise TypeError(f"cls must be of type <class> not <{type(cls)}>")

        def decorator(func: Callable):
            fname = name or func.__name__
            cmd = cls(name=fname, func=func, aliases=aliases, no_global_checks=no_global_checks, parent=self)
            self._sub_commands[cmd.name] = cmd
            if cmd.aliases:
                for a in cmd.aliases:
                    self._sub_commands[a] = cmd
            return cmd

        return decorator

    def group(
        self,
        *,
        name: str = None,
        aliases: Union[list, tuple] = None,
        cls: Type[Group] = None,
        no_global_checks=False,
        invoke_with_subcommand=False,
    ) -> Callable[[Callable], Group]:
        cls = cls or Group
        if cls and not inspect.isclass(cls):
            raise TypeError(f"cls must be of type <class> not <{type(cls)}>")

        def decorator(func: Callable):
            fname = name or func.__name__
            cmd = cls(
                name=fname,
                func=func,
                aliases=aliases,
                no_global_checks=no_global_checks,
                parent=self,
                invoke_with_subcommand=invoke_with_subcommand,
            )
            self._sub_commands[cmd.name] = cmd
            if cmd.aliases:
                for a in cmd.aliases:
                    self._sub_commands[a] = cmd
            return cmd

        return decorator


class Context(Messageable):
    """
    A class that represents the context in which a command is being invoked under.

    This class contains the meta data to help you understand more about the invocation context.
    This class is not created manually and is instead passed around to commands as the first parameter.

    Attributes
    -----------
    message: :class:`~twitchio.Message`
        The message that triggered the command being executed.
    channel: :class:`~twitchio.Channel`
        The channel the command was invoked in.
    author: Union[:class:`~twitchio.PartialChatter`, :class:`~twitchio.Chatter`]
        The Chatter object of the user in chat that invoked the command.
    prefix: Optional[:class:`str`]
        The prefix that was used to invoke the command.
    command: Optional[:class:`~twitchio.ext.commands.Command`]
        The command that was invoked
    cog: Optional[:class:`~twitchio.ext.commands.Cog`]
        The cog that contains the command that was invoked.
    args: Optional[List[:class:`Any`]]
        List of arguments that were passed to the command.
    kwargs: Optional[Dict[:class:`str`, :class:`Any`]]
        List of kwargs that were passed to the command.
    view: Optional[:class:`~twitchio.ext.commmands.StringParser`]
        StringParser object that breaks down the command string received.
    bot: :class:`~twitchio.ext.commands.Bot`
        The bot that contains the command that was invoked.
    """

    __messageable_channel__ = True

    def __init__(self, message: Message, bot: Bot, **attrs) -> None:
        self.message: Message = message
        self.channel: Channel = message.channel
        self.author: Union[Chatter, PartialChatter] = message.author

        self.prefix: Optional[str] = attrs.get("prefix")

        self.command: Optional[Command] = attrs.get("command")
        if self.command:
            self.cog: Optional[Cog] = self.command.cog
        self.args: Optional[list] = attrs.get("args")
        self.kwargs: Optional[dict] = attrs.get("kwargs")

        self.view: Optional[StringParser] = attrs.get("view")
        self.is_valid: bool = attrs.get("valid")

        self.bot: Bot = bot
        self._ws = self.author._ws

    def _fetch_channel(self) -> Messageable:
        return self.channel or self.author  # Abstract method

    def _fetch_websocket(self):
        return self._ws  # Abstract method

    def _fetch_message(self):
        return self.message  # Abstract method

    def _bot_is_mod(self) -> bool:
        if not self.channel:
            return False
        cache = self._ws._cache[self.channel._name]
        for user in cache:
            if user.name == self._ws.nick:
                try:
                    mod = user.is_mod
                except AttributeError:
                    return False
                return mod

    @property
    def chatters(self) -> Optional[Set[Chatter]]:
        """The channels current chatters."""
        try:
            users = self._ws._cache[self.channel._name]
        except (KeyError, AttributeError):
            return None
        return users

    @property
    def users(self) -> Optional[Set[Chatter]]:  # Alias to chatters
        """Alias to chatters."""
        return self.chatters

    def get_user(self, name: str) -> Optional[Union[PartialUser, User]]:
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

        if not self.channel:
            return None
        cache = self._ws._cache[self.channel._name]
        for user in cache:
            if user.name == name:
                return user
        return None

    async def reply(self, content: str):
        """|coro|


        Send a message in reply to the user who sent a message in the destination
        associated with the dataclass.

        Destination will be the context of which the message/command was sent.

        Parameters
        ------------
        content: str
            The content you wish to send as a message. The content must be a string.

        Raises
        --------
        InvalidContent
            Invalid content.
        """
        entity = self._fetch_channel()
        ws = self._fetch_websocket()
        message = self._fetch_message()

        self.check_content(content)
        self.check_bucket(channel=entity.name)

        try:
            name = entity.channel.name
        except AttributeError:
            name = entity.name
        if entity.__messageable_channel__:
            await ws.reply(message.id, f"PRIVMSG #{name} :{content}\r\n")
        else:
            await ws.send(f"PRIVMSG #jtv :/w {name} {content}\r\n")


C = TypeVar("C", bound="Command")
G = TypeVar("G", bound="Group")


def command(
    *, name: str = None, aliases: Union[list, tuple] = None, cls: type[C] = Command, no_global_checks=False
) -> Callable[[Callable], C]:
    if cls and not inspect.isclass(cls):
        raise TypeError(f"cls must be of type <class> not <{type(cls)}>")

    def decorator(func: Callable) -> C:
        fname = name or func.__name__
        return cls(
            name=fname,
            func=func,
            aliases=aliases,
            no_global_checks=no_global_checks,
        )

    return decorator


def group(
    *,
    name: str = None,
    aliases: Union[list, tuple] = None,
    cls: G = Group,
    no_global_checks=False,
    invoke_with_subcommand=False,
) -> Callable[[Callable], G]:
    if cls and not inspect.isclass(cls):
        raise TypeError(f"cls must be of type <class> not <{type(cls)}>")

    def decorator(func: Callable) -> G:
        fname = name or func.__name__
        return cls(
            name=fname,
            func=func,
            aliases=aliases,
            no_global_checks=no_global_checks,
            invoke_with_subcommand=invoke_with_subcommand,
        )

    return decorator


FN = TypeVar("FN")


def cooldown(rate, per, bucket=Bucket.default):
    def decorator(func: FN) -> FN:
        if isinstance(func, Command):
            func._cooldowns.append(Cooldown(rate, per, bucket))
        else:
            func.__cooldowns__ = [Cooldown(rate, per, bucket)]
        return func

    return decorator
