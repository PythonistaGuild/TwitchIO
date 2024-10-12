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
from typing import TYPE_CHECKING, Any

from .exceptions import *
from .view import StringView


__all__ = ("Context",)


if TYPE_CHECKING:
    from models.eventsub_ import ChatMessage
    from types_.options import Prefix_T
    from user import Chatter, PartialUser

    from .bot import Bot
    from .core import Command


class Context:
    def __init__(self, message: ChatMessage, bot: Bot) -> None:
        self._message: ChatMessage = message
        self._bot: Bot = bot
        self._prefix: str | None = None

        self._raw_content: str = self._message.text
        self._command: Command[Any, ...] | None = None
        self._invoked_subcommand: Command[Any, ...] | None = None
        self._invoked_with: str | None = None
        self._subcommand_trigger: str | None = None
        self._command_failed: bool = False
        self._error_dispatched: bool = False

        self._view: StringView = StringView(self._raw_content)

        self._args: list[Any] = []
        self._kwargs: dict[str, Any] = {}

    @property
    def message(self) -> ChatMessage:
        return self._message

    @property
    def command(self) -> Command[Any, ...] | None:
        return self._command

    @property
    def invoked_subcommand(self) -> Command[Any, ...] | None:
        return self._invoked_subcommand

    @property
    def subcommand_trigger(self) -> str | None:
        return self._subcommand_trigger

    @property
    def invoked_with(self) -> str | None:
        return self._invoked_with

    @property
    def chatter(self) -> Chatter:
        return self._message.chatter

    @property
    def broadcaster(self) -> PartialUser:
        return self._message.broadcaster

    @property
    def channel(self) -> PartialUser:
        return self.broadcaster

    @property
    def bot(self) -> Bot:
        return self._bot

    @property
    def prefix(self) -> str | None:
        return self._prefix

    @property
    def content(self) -> str:
        return self._raw_content

    @property
    def error_dispatched(self) -> bool:
        return self._error_dispatched

    @error_dispatched.setter
    def error_dispatched(self, value: bool, /) -> None:
        self._error_dispatched = value

    @property
    def args(self) -> list[Any]:
        return self._args

    @property
    def kwargs(self) -> dict[str, Any]:
        return self._kwargs

    def is_owner(self) -> bool:
        return self.chatter.id == self.bot.owner_id

    def is_valid(self) -> bool:
        return self._prefix is not None

    def _validate_prefix(self, potential: str | Iterable[str]) -> None:
        text: str = self._message.text

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
        assigned: Prefix_T = self._bot._get_prefix
        potential: str | Iterable[str]

        if callable(assigned):
            potential = await assigned(self._bot, self._message)
        else:
            potential = assigned

        if not isinstance(potential, Iterable):  # type: ignore
            msg = f'Command prefix must be a "str", "Iterable[str]" or a coroutine returning either. Not: {type(potential)}'
            raise PrefixError(msg)

        self._validate_prefix(potential)

    def _get_command(self) -> None:
        if not self.prefix:
            return

        commands = self._bot._commands
        self._view.skip_string(self.prefix)

        next_ = self._view.get_word()
        self._invoked_with = next_
        command = commands.get(next_)

        if not command:
            return

        self._command = command
        return

    async def _prepare(self) -> None:
        await self._get_prefix()
        self._get_command()

    async def prepare(self) -> None:
        await self._prepare()

    async def invoke(self) -> None:
        await self.prepare()

        if not self.is_valid():
            return

        if not self._command:
            raise CommandNotFound(f'The command "{self._invoked_with}" was not found.')

        try:
            await self._bot.before_invoke(self)
        except Exception as e:
            raise CommandHookError(str(e), e) from e

        # TODO: Payload...
        self.bot.dispatch("command_invoked")

        try:
            await self._command.invoke(self)
        except CommandError as e:
            await self._command._dispatch_error(self, e)
            return

        try:
            await self._bot.after_invoke(self)
        except Exception as e:
            raise CommandHookError(str(e), e) from e

        # TODO: Payload...
        self.bot.dispatch("command_completed")

    async def send(self, content: str) -> None:
        await self.channel.send_message(sender_id=self.bot.bot_id, message=content)
