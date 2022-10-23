from __future__ import annotations

import copy
import typing
from typing import Optional, cast

from twitchio import Channel, Message
from twitchio.abc import Messageable

from .errors import *

if typing.TYPE_CHECKING:
    from .bot import Bot
    from .commands import Command
    from .components import Component


class Context(Messageable):
    def __init__(self, message: Message, bot: "Bot", **attrs):
        attrs["name"] = cast(Channel, message.channel).name
        attrs["websocket"] = cast(Channel, message.channel)._websocket
        super().__init__(**attrs)

        self.message: Message = message
        self._message_copy = copy.copy(message)
        if "reply-parent-msg-id" in self._message_copy.tags:
            _, _, self._message_copy.content = self._message_copy.content.partition(" ")

        self.channel: Channel = cast(Channel, self.message.channel)

        self.bot: Bot = bot

        self.prefix: Optional[str] = self._get_prefix()
        self.command = self._get_command()

        self.args: tuple = ()
        self.kwargs: dict = {}

        self._component: Component | None = None
        if self.command and self.command._component:
            self._component = self.command._component

    def _get_command_string(self) -> str:
        return self._message_copy.content.removeprefix(cast(str, self.prefix)).split()[0]

    def _get_command(self) -> Optional[Command]:
        if not self.is_valid:
            return None

        cmdstr = self._get_command_string()

        try:
            cmd = self.bot.commands[cmdstr]
        except KeyError:
            return None

        return cmd

    def _get_prefix(self) -> Optional[str]:
        for prefix in self.bot.prefixes:
            if self._message_copy.content.startswith(prefix):
                return prefix

        return None

    @property
    def is_valid(self) -> bool:
        return self.prefix is not None

    @property
    def invoked_with(self) -> str:
        return self._get_command_string()

    async def send(self, content: str) -> None:
        await self.channel.send(content=content)

    @property
    def name(self) -> str:
        return self.channel.name

    @property
    def component(self) -> Optional[Component]:
        return self._component

    async def invoke(self, *, parse_args_first: bool = True) -> None:
        try:
            # There was no valid prefix found...
            if not self.is_valid:
                raise InvalidInvocationContext("This Context is invalid for command invocation.")

            # No Command was found for this Context object.
            if not self.command:
                raise CommandNotFoundError(f'The command "{self._get_command_string()}" could not be found.')

            # Do arg parsing before any invocations or checks...
            if parse_args_first:
                self.command.parse_args(self)

            # Invoke before_invoke... Global > Component > Command
            await self.bot.before_invoke(self)
            if self.component:
                await self.component.component_before_invoke(self)

            # Actual command invocation... Parses args here if parse_args_first is False.
            await self.command.invoke(context=self)

            # Invoke after_invoke... Global > Component > Command
            await self.bot.after_invoke(self)
            if self.component:
                await self.component.component_after_invoke(self)

        except TwitchIOCommandError as e:
            await self.bot.event_command_error(self, e)

        except Exception as e:
            exception = TwitchIOCommandError(str(e), original=e)
            await self.bot.event_command_error(self, exception)
