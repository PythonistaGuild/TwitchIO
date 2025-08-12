"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

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

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeAlias

from twitchio.models.eventsub_ import ChannelPointsRedemptionAdd, ChannelPointsRedemptionUpdate, ChatMessage

from .core import CommandErrorPayload, ContextType, RewardCommand, RewardStatus
from .exceptions import *
from .types_ import BotT
from .view import StringView


__all__ = ("Context",)


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from twitchio.models import SentMessage
    from twitchio.user import Chatter, PartialUser

    from .bot import Bot
    from .components import Component
    from .core import Command
    from .translators import Translator

    PrefixT: TypeAlias = str | Iterable[str] | Callable[[Bot, ChatMessage], Coroutine[Any, Any, str | Iterable[str]]]


class Context(Generic[BotT]):
    """The Context class constructed when a message or reward redemption in the respective events is received and processed
    in a :class:`~.commands.Bot`.

    This object is available in all :class:`~.commands.Command`'s, :class:`~.commands.RewardCommand`'s,
    :class:`~twitchio.ext.commands.Group`'s and associated sub-commands and all command related events.
    It is also included in various areas relating to command invocation, including, :func:`~twitchio.ext.commands.guard`'s and
    before and after hooks.

    The :class:`~.commands.Context` class is a useful tool which provides information surrounding the command invocation,
    the broadcaster and chatter involved and provides many useful methods and properties for ease of us.

    Usually you wouldn't construct this class this yourself, however it could be subclassed and used with
    :meth:`~twitchio.ext.commands.Bot.get_context` to implement custom functionality.

    Parameters
    ----------
    payload: :class:`twitchio.ChatMessage` | :class:`~twitchio.ChannelPointsRedemptionAdd` | :class:`~twitchio.ChannelPointsRedemptionUpdate`
        The message or redemption object used to construct this Context.
    bot: :class:`~.commands.Bot`
        Your :class:`~.commands.Bot` class, this is required to perform multiple operations.
    """

    def __init__(
        self,
        payload: ChatMessage | ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate,
        *,
        bot: BotT,
    ) -> None:
        self._payload: ChatMessage | ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate = payload
        self._bot = bot
        self._component: Component | None = None
        self._prefix: str | None = None

        if isinstance(payload, ChatMessage):
            self._raw_content: str = payload.text
            self._invoked_with: str | None = None
            self._type: ContextType = ContextType.MESSAGE
        else:
            self._raw_content = payload.user_input
            self._invoked_with = payload.reward.id
            self._type: ContextType = ContextType.REWARD

        self._command: Command[Any, ...] | RewardCommand[Any, ...] | None = None
        self._invoked_subcommand: Command[Any, ...] | RewardCommand[Any, ...] | None = None
        self._subcommand_trigger: str | None = None
        self._command_failed: bool = False
        self._error_dispatched: bool = False

        self._failed: bool = False
        self._passed_guards = False

        self._view: StringView = StringView(self._raw_content)

        self._args: list[Any] = []
        self._kwargs: dict[str, Any] = {}

        self._prepare_called: bool = False

    @property
    def message(self) -> ChatMessage | None:
        """Property returning the :class:`~twitchio.ChatMessage` that this :class:`~.commands.Context` was
        created from. This could be ``None`` if :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`.
        """
        return self._payload if isinstance(self._payload, ChatMessage) else None

    @property
    def redemption(self) -> ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate | None:
        """Property returning the :class:`~twitchio.ChannelPointsRedemptionAdd` or :class:`~twitchio.ChannelPointsRedemptionUpdate`
        that this :class:`~.commands.Context` was created from. This could be ``None`` if :attr:`~.commands.Context.type`
        is :attr:`~.commands.ContextType.MESSAGE`.
        """
        return (
            self._payload if isinstance(self._payload, (ChannelPointsRedemptionAdd, ChannelPointsRedemptionUpdate)) else None
        )

    @property
    def payload(self) -> ChatMessage | ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate:
        """Property returning the :class:`~twitchio.ChatMessage` or either :class:`~twitchio.ChannelPointsRedemptionAdd`
        or :class:`~twitchio.ChannelPointsRedemptionUpdate` associated with this :class:`~.commands.Context`.

        Unlike :attr:`~.commands.Context.message` and :attr:`~.commands.Context.redemption` this will always return a value.
        """
        return self._payload

    @property
    def component(self) -> Component | None:
        """Property returning the :class:`~.commands.Component` that this context was used in, if the
        :class:`~.commands.Command` belongs to it. This is only set once a :class:`~.commands.Command`
        has been found and invoked.
        """
        return self._component

    @property
    def command(self) -> Command[Any, ...] | RewardCommand[Any, ...] | None:
        """Property returning the :class:`~.commands.Command` or :class:`~.commands.RewardCommand` associated with this context,
        if found.

        This is only set when a command begins invocation. Could be ``None`` if the command has not started invocation,
        or one was not found.
        """
        return self._command

    @property
    def invoked_subcommand(self) -> Command[Any, ...] | None:
        """Property returning the subcommand associated with this context if their is one.

        Returns ``None`` when a standard command without a parent :class:`~.commands.Group` is invoked.
        """
        return self._invoked_subcommand

    @property
    def subcommand_trigger(self) -> str | None:
        return self._subcommand_trigger

    @property
    def invoked_with(self) -> str | None:
        """Property returning the string the context used to attempt to find
        a valid :class:`~.commands.Command`.

        If :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD` this will return the ID of the reward.

        Could be ``None`` if a command has not been invoked from this context yet.
        """
        return self._invoked_with

    @property
    def chatter(self) -> Chatter | PartialUser:
        """Property returning a :class:`~twitchio.Chatter` if :attr:`~.commands.Context.type` is
        :attr:`~.commands.ContextType.MESSAGE`; E.g. when invoked from a :class:`~twitchio.ChatMessage`.

        When :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`, this will return a
        :class:`twitchio.PartialUser`, which is the user who redeemed the reward.
        """
        return self._payload.chatter if isinstance(self._payload, ChatMessage) else self._payload.user

    @property
    def author(self) -> Chatter | PartialUser:
        """Property returning a :class:`~twitchio.Chatter` if :attr:`~.commands.Context.type` is
        :attr:`~.commands.ContextType.MESSAGE`; E.g. when invoked from a :class:`~twitchio.ChatMessage`.

        When :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`, this will return a
        :class:`twitchio.PartialUser`, which is the user who redeemed the reward.
        """
        return self._payload.chatter if isinstance(self._payload, ChatMessage) else self._payload.user

    @property
    def broadcaster(self) -> PartialUser:
        """Property returning the :class:`twitchio.PartialUser` who is the broadcaster of the channel associated with this
        context.
        """
        return self._payload.broadcaster

    @property
    def source_broadcaster(self) -> PartialUser | None:
        """Property returning the :class:`twitchio.PartialUser` who is the broadcaster of the channel associated with
        the original :class:`~twitchio.ChatMessage`.

        This will usually always be ``None`` as the default behaviour is to ignore shared messages when invoking commands.

        This will always be ``None`` when :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`.
        """
        return self._payload.source_broadcaster if isinstance(self._payload, ChatMessage) else None

    @property
    def channel(self) -> PartialUser:
        """An alias to :attr:`.broadcaster`."""
        return self.broadcaster

    @property
    def bot(self) -> BotT:
        """Property returning the :class:`~.commands.Bot` object."""
        return self._bot

    @property
    def prefix(self) -> str | None:
        """Property returning the prefix associated with this context or ``None``.

        This will only return a prefix after the context has been prepared, which occurs during invocation of a command,
        and after a valid prefix found.

        This will always be ``None`` when :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`.
        """
        return self._prefix

    @property
    def content(self) -> str:
        """Property returning the raw content of the message associated with this context.

        If :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`, this will be the ``user_input`` of the
        reward, if provided by the user.
        """
        return self._raw_content

    @property
    def type(self) -> ContextType:
        """Property returning the :class:`.commands.ContextType` associated with this :class:`.commands.Context`.

        This will be :attr:`~.commands.ContextType.MESSAGE` when the context is invoked from a :class:`~twitchio.ChatMessage`.

        Otherwise when invoked from a Channel Points Redemption this will be :attr:`~.commands.ContextType.REWARD`.
        """
        return self._type

    @property
    def translator(self) -> Translator[Any] | None:
        """Property returning the :class:`.commands.Translator` assigned to the :class:`.commands.Command` if found or
        ``None``. This property will always return ``None`` if no valid command or prefix is associated with this Context."""
        if not self.command:
            return None

        return self.command.translator

    @property
    def error_dispatched(self) -> bool:
        return self._error_dispatched

    @error_dispatched.setter
    def error_dispatched(self, value: bool, /) -> None:
        self._error_dispatched = value

    @property
    def args(self) -> list[Any]:
        """A list of arguments processed and passed to the :class:`~.commands.Command` callback.

        This is only set after the command begins invocation.
        """
        return self._args

    @property
    def kwargs(self) -> dict[str, Any]:
        """A dict of keyword-arguments processed and passed to the :class:`~.commands.Command` callback.

        This is only set after the command begins invocation.
        """
        return self._kwargs

    @property
    def failed(self) -> bool:
        """Property indicating whether the context failed to invoke the associated command."""
        return self._failed

    def is_owner(self) -> bool:
        """Method which returns whether the chatter associated with this context is the owner of the bot.

        .. warning::

            You must have set the :attr:`~commands.Bot.owner_id` correctly first,
            otherwise this method will return ``False``.

        Returns
        -------
        bool
            Whether the chatter that this context is associated with is the owner of this bot.
        """
        return self.chatter.id == self.bot.owner_id

    def is_valid(self) -> bool:
        """Method which indicates whether this context is valid. E.g. has a valid command prefix.

        If :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD` this will return ``True`` if a valid
        command is found.
        """
        if isinstance(self._payload, (ChannelPointsRedemptionAdd, ChannelPointsRedemptionUpdate)):
            return self._command is not None

        return self._prefix is not None

    def _validate_prefix(self, potential: str | Iterable[str]) -> None:
        assert isinstance(self._payload, ChatMessage)
        text: str = self._payload.text

        if isinstance(potential, str):
            if text.startswith(potential):
                self._prefix = potential

            return

        for prefix in tuple(potential):
            if not isinstance(prefix, str):  # type: ignore
                msg = f'Command prefix in iterable or iterable returned from coroutine must be "str", not: {type(prefix)}'
                raise PrefixError(msg)

            if text.startswith(prefix):
                self._prefix = prefix
                return

    async def _get_prefix(self) -> None:
        assert isinstance(self._payload, ChatMessage)

        assigned: PrefixT = self._bot._get_prefix
        potential: str | Iterable[str]

        if callable(assigned):
            potential = await assigned(self._bot, self._payload)
        else:
            potential = assigned

        if not isinstance(potential, Iterable):  # type: ignore
            msg = f'Command prefix must be a "str", "Iterable[str]" or a coroutine returning either. Not: {type(potential)}'
            raise PrefixError(msg)

        self._validate_prefix(potential)

    def _get_command(self, reset: bool = False) -> None:
        if self._prepare_called:
            return

        commands = self._bot._commands

        if isinstance(self._payload, (ChannelPointsRedemptionAdd, ChannelPointsRedemptionUpdate)):
            status = self._payload.status
            unique = f"{self._payload.reward.id}_{status}"
            self._command = commands.get(self._payload.reward.id, commands.get(unique))
            return

        if not self.prefix:
            return

        self._view.skip_string(self.prefix)

        next_ = self._view.get_word()
        self._invoked_with = next_
        command = commands.get(next_)

        if reset:
            self._view.reset()

        if not command:
            return

        self._command = command
        return

    async def fetch_command(self) -> Command[Any, ...] | RewardCommand[Any, ...] | None:
        """|coro|

        Method which validates the prefix and finds and returns the command that would be invoked or ``None`` if no valid
        command can be found.

        If no valid ``prefix`` is found this method will always return ``None``.

        .. note::

            Unlike :meth:`.prepare` this method resets the state of the internal string-view used to find the ``prefix``,
            ``command`` and ``arguments`` and can be safely used at anytime.

        .. versionadded:: 3.1

        Returns
        -------
        :class:`twitchio.ext.commands.Command` | :class:`twitchio.ext.commands.RewardCommand` | None
            The :class:`twitchio.ext.commands.Command` or :class:`twitchio.ext.commands.RewardCommand` if found alongside
            a valid prefix, otherwise ``None``.
        """
        try:
            await self._prepare(reset=True)
        except PrefixError:
            return

        return self._command

    async def _prepare(self, reset: bool = False) -> None:
        if isinstance(self._payload, ChatMessage):
            await self._get_prefix()

        self._get_command(reset=reset)

        if reset is False:
            self._prepare_called = True

    async def prepare(self) -> None:
        """|coro|

        Method called before invocation, used to retrieve a valid prefix and valid command.

        This coroutine is called automatically in :meth:`.invoke` before anything else.

        Could be overriden to add extra setup before command invocation.

        .. note::

            If this method is overriden you should call `await super().prepare()` to ensure correct setup of the context.
        """
        await self._prepare()

    async def invoke(self) -> bool | None:
        """|coro|

        Invoke and process the command associated with this message or redemption context if it is valid.

        This method first prepares the context for invocation, and checks whether the context has a
        valid command with a valid prefix.

        .. warning::

            Usually you wouldn't use this method yourself, as it handled by TwitchIO interanally when
            :meth:`~.commands.Bot.process_commands` is called in various events.

        .. important::

            Due to the way this method works, the only error raised will be :exc:`~.commands.CommandNotFound`.
            All other errors that occur will be sent to the :func:`twitchio.event_command_error` event.

        Returns
        -------
        bool
            If this method explicitly returns ``False`` the context is not valid. E.g. has no valid command prefix.
            When ``True`` the command successfully completed invocation without error.
        ``None``
            Returned when the command is found and begins to process. This does not indicate the command was completed
            successfully. See also :func:`twitchio.event_command_completed` for an event fired when a
            command successfully completes the invocation process.

        Raises
        ------
        CommandNotFound
            The :class:`~.commands.Command` trying to be invoked could not be found.
        """
        await self.prepare()

        if not self.is_valid():
            return False

        if not self._command:
            raise CommandNotFound(f'The command "{self._invoked_with}" was not found.')

        if isinstance(self._payload, (ChannelPointsRedemptionAdd, ChannelPointsRedemptionUpdate)):
            assert isinstance(self._command, RewardCommand)

            status: RewardStatus = RewardStatus(self._payload.status)
            invoke_when: RewardStatus = self._command._invoke_when

            if invoke_when is RewardStatus.all:
                pass
            elif status is not invoke_when:
                return

        self.bot.dispatch("command_invoked", self)

        try:
            await self._command.invoke(self)
        except CommandError as e:
            self._failed = True
            await self._command._dispatch_error(self, e)

        if self._passed_guards:
            try:
                await self._bot.after_invoke(self)
                if self._component:
                    await self._component.component_after_invoke(self)

                if self._command._after_hook:
                    base_args: list[Any] = [self]
                    base_args.insert(0, self._component) if self._component else None

                    await self._command._after_hook(*base_args)
            except Exception as e:
                payload = CommandErrorPayload(context=self, exception=CommandHookError(str(e), e))
                self.bot.dispatch("command_error", payload=payload)
                return

        if not self._failed:
            self.bot.dispatch("command_completed", self)

        return True

    async def send(self, content: str, *, me: bool = False) -> SentMessage:
        """|coro|

        Send a chat message to the channel associated with this context.

        .. important::

            You must have the ``user:write:chat`` scope. If an app access token is used,
            then additionally requires the ``user:bot`` scope on the bot,
            and either ``channel:bot`` scope from the broadcaster or moderator status.

        Parameters
        ----------
        content: str
            The content of the message you would like to send. This cannot exceed ``500`` characters. Additionally the content
            parameter will be stripped of all leading and trailing whitespace.
        me: bool
            An optional bool indicating whether you would like to send this message with the ``/me`` chat command.

        Returns
        -------
        SentMessage
            The payload received by Twitch after sending this message.

        Raises
        ------
        HTTPException
            Twitch failed to process the message, could be ``400``, ``401``, ``403``, ``422`` or any ``5xx`` status code.
        MessageRejectedError
            Twitch rejected the message from various checks.
        """
        new = (f"/me {content}" if me else content).strip()
        return await self.channel.send_message(sender=self.bot.bot_id, message=new)

    async def send_translated(self, content: str, *, me: bool = False, langcode: str | None = None) -> SentMessage:
        """|coro|

        Send a translated chat message to the channel associated with this context.

        You must have added a :class:`.commands.Translator` to your :class:`.commands.Command` in order to effectively use
        this method. If no :class:`.commands.Translator` is found, this method acts identical to :meth:`.send`.

        If this method can not find a valid language code, E.g. both :meth:`.commands.Translator.get_langcode` and the parameter
        ``langcode`` return ``None``, this method acts identical to :meth:`.send`.

        See the following documentation for more details on translators:

        - :class:`.commands.Translator`
        - :func:`.commands.translator`

        .. important::

            You must have the ``user:write:chat`` scope. If an app access token is used,
            then additionally requires the ``user:bot`` scope on the bot,
            and either ``channel:bot`` scope from the broadcaster or moderator status.

        Parameters
        ----------
        content: str
            The content of the message you would like to translate and then send.
            This **and** the translated version of this content cannot exceed ``500`` characters.
            Additionally the content parameter will be stripped of all leading and trailing whitespace.
        me: bool
            An optional bool indicating whether you would like to send this message with the ``/me`` chat command.
        langcode: str | None
            An optional ``langcode`` to override the ``langcode`` returned from :meth:`.commands.Translator.get_langcode`.
            This should only be provided if you do custom language code lookups outside of your
            :class:`.commands.Translator`. Defaults to ``None``.


        Returns
        -------
        SentMessage
            The payload received by Twitch after sending this message.

        Raises
        ------
        HTTPException
            Twitch failed to process the message, could be ``400``, ``401``, ``403``, ``422`` or any ``5xx`` status code.
        MessageRejectedError
            Twitch rejected the message from various checks.
        TranslatorError
            An error occurred during translation.
        """
        translator: Translator[Any] | None = self.translator
        new = (f"/me {content}" if me else content).strip()

        if not self.command or not translator:
            return await self.channel.send_message(sender=self.bot.bot_id, message=new)

        invoked = self.invoked_with

        try:
            code = langcode or translator.get_langcode(self, invoked.lower()) if invoked else None
        except Exception as e:
            raise TranslatorError(f"An exception occurred fetching a language code for '{invoked}'.", original=e) from e

        if code is None:
            return await self.channel.send_message(sender=self.bot.bot_id, message=new)

        try:
            translated = await translator.translate(self, content, code)
        except Exception as e:
            raise TranslatorError(f"An exception occurred translating content for '{invoked}'.", original=e) from e

        new_translated = (f"/me {translated}" if me else translated).strip()
        return await self.channel.send_message(sender=self.bot.bot_id, message=new_translated)

    async def reply(self, content: str, *, me: bool = False) -> SentMessage:
        """|coro|

        Send a chat message as a reply to the user who this message is associated with and to the channel associated with
        this context.

        .. warning::

            You cannot use this method in Reward based context. E.g.
            if :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`.

        .. important::

            You must have the ``user:write:chat`` scope. If an app access token is used,
            then additionally requires the ``user:bot`` scope on the bot,
            and either ``channel:bot`` scope from the broadcaster or moderator status.

        Parameters
        ----------
        content: str
            The content of the message you would like to send. This cannot exceed ``500`` characters. Additionally the content
            parameter will be stripped of all leading and trailing whitespace.
        me: bool
            An optional bool indicating whether you would like to send this message with the ``/me`` chat command.

        Returns
        -------
        SentMessage
            The payload received by Twitch after sending this message.

        Raises
        ------
        HTTPException
            Twitch failed to process the message, could be ``400``, ``401``, ``403``, ``422`` or any ``5xx`` status code.
        MessageRejectedError
            Twitch rejected the message from various checks.
        TypeError
            Cannot reply in a Reward based Context.
        """
        if self._type is ContextType.REWARD:
            raise TypeError("Cannot reply to a message in a Reward based context.")

        new = (f"/me {content}" if me else content).strip()
        return await self.channel.send_message(sender=self.bot.bot_id, message=new, reply_to_message_id=self._payload.id)

    async def reply_translated(self, content: str, *, me: bool = False, langcode: str | None = None) -> SentMessage:
        """|coro|

        Send a translated chat message as a reply to the user who this message is associated with and to the channel associated with
        this context.

        You must have added a :class:`.commands.Translator` to your :class:`.commands.Command` in order to effectively use
        this method. If no :class:`.commands.Translator` is found, this method acts identical to :meth:`.reply`.

        If this method can not find a valid language code, E.g. both :meth:`.commands.Translator.get_langcode` and the parameter
        ``langcode`` return ``None``, this method acts identical to :meth:`.reply`.

        See the following documentation for more details on translators:

        - :class:`.commands.Translator`
        - :func:`.commands.translator`

        .. warning::

            You cannot use this method in Reward based context. E.g.
            if :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`.

        .. important::

            You must have the ``user:write:chat`` scope. If an app access token is used,
            then additionally requires the ``user:bot`` scope on the bot,
            and either ``channel:bot`` scope from the broadcaster or moderator status.

        Parameters
        ----------
        content: str
            The content of the message you would like to translate and then send.
            This **and** the translated version of this content cannot exceed ``500`` characters.
            Additionally the content parameter will be stripped of all leading and trailing whitespace.
        me: bool
            An optional bool indicating whether you would like to send this message with the ``/me`` chat command.
        langcode: str | None
            An optional ``langcode`` to override the ``langcode`` returned from :meth:`.commands.Translator.get_langcode`.
            This should only be provided if you do custom language code lookups outside of your
            :class:`.commands.Translator`. Defaults to ``None``.


        Returns
        -------
        SentMessage
            The payload received by Twitch after sending this message.

        Raises
        ------
        HTTPException
            Twitch failed to process the message, could be ``400``, ``401``, ``403``, ``422`` or any ``5xx`` status code.
        MessageRejectedError
            Twitch rejected the message from various checks.
        TranslatorError
            An error occurred during translation.
        """
        if self._type is ContextType.REWARD:
            raise TypeError("Cannot reply to a message in a Reward based context.")

        translator: Translator[Any] | None = self.translator
        new = (f"/me {content}" if me else content).strip()

        if not self.command or not translator:
            return await self.channel.send_message(sender=self.bot.bot_id, message=new, reply_to_message_id=self._payload.id)

        invoked = self.invoked_with

        try:
            code = langcode or translator.get_langcode(self, invoked.lower()) if invoked else None
        except Exception as e:
            raise TranslatorError(f"An exception occurred fetching a language code for '{invoked}'.", original=e) from e

        if code is None:
            return await self.channel.send_message(sender=self.bot.bot_id, message=new, reply_to_message_id=self._payload.id)

        try:
            translated = await translator.translate(self, content, code)
        except Exception as e:
            raise TranslatorError(f"An exception occurred translating content for '{invoked}'.", original=e) from e

        new_translated = (f"/me {translated}" if me else translated).strip()
        return await self.channel.send_message(
            sender=self.bot.bot_id,
            message=new_translated,
            reply_to_message_id=self._payload.id,
        )

    async def send_announcement(
        self, content: str, *, color: Literal["blue", "green", "orange", "purple", "primary"] | None = None
    ) -> None:
        """|coro|

        Send an announcement to the channel associated with this channel as the bot.

        .. important::

            The broadcaster of the associated channel must have granted your bot the ``moderator:manage:announcements`` scope.

        Parameters
        ----------
        content: str
            The content of the announcement to send. This cannot exceed `500` characters. Announcements longer than ``500``
            characters will be truncated instead by Twitch.
        color: Literal["blue", "green", "orange", "purple", "primary"] | None
            An optional colour to use for the announcement. If set to ``"primary``" or ``None``
            the channels accent colour will be used instead. Defaults to ``None``.

        Returns
        -------
        None

        Raises
        ------
        HTTPException
            Sending the announcement failed. Could be ``400``, ``401`` or any ``5xx`` status code.
        """
        await self.channel.send_announcement(moderator=self.bot.bot_id, message=content, color=color)

    async def delete_message(self) -> None:
        """|coro|

        Delete the message associated with this context.

        .. warning::

            You cannot use this method in Reward based context. E.g.
            if :attr:`~.commands.Context.type` is :attr:`~.commands.ContextType.REWARD`.

        .. important::

            The broadcaster of the associated channel must have granted your bot the ``moderator:manage:chat_messages`` scope.

        .. note::

            You cannot delete messages from the broadcaster *or* any moderator, and the message must not be more than
            ``6 hours`` old.

        Raises
        ------
        HTTPException
            Twitch failed to remove the message. Could be ``400``, ``401``, ``403``, ``404`` or any ``5xx`` status code.
        TypeError
            Cannot delete the message of a Reward based Context.
        """
        if self._type is ContextType.REWARD:
            raise TypeError("Cannot delete a message in a Reward based context.")

        await self.channel.delete_chat_messages(moderator=self.bot.bot_id, message_id=self._payload.id)

    async def clear_messages(self) -> None:
        """|coro|

        Clear all the chat messages from chat for the channel associated with this context.

        .. important::

            The broadcaster of the associated channel must have granted your bot the ``moderator:manage:chat_messages`` scope.

        Raises
        ------
        HTTPException
            Twitch failed to remove the message. Could be ``400``, ``401``, ``403``, ``404`` or any ``5xx`` status code.
        """
        await self.channel.delete_chat_messages(moderator=self.bot.bot_id, message_id=None)
