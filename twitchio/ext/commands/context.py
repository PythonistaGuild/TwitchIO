import typing
from typing import Optional

from twitchio import Channel, Message
from twitchio.abc import Messageable
from .errors import *

if typing.TYPE_CHECKING:
    from .bot import Bot
    from .commands import Command


class Context(Messageable):

    def __init__(self, message: Message, bot: 'Bot', **attrs):
        attrs['name'] = message.channel.name
        attrs['websocket'] = message.channel._websocket
        super().__init__(**attrs)

        self.message: Message = message
        self.channel: Channel = self.message.channel

        self.bot: 'Bot' = bot

        self.prefix = self._get_prefix()
        self.command = self._get_command()

        self.args: tuple = ()
        self.kwargs: dict = {}

    def _get_command_string(self) -> str:
        return self.message.content.removeprefix(self.prefix).split()[0]

    def _get_command(self) -> Optional['Command']:
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
            if self.message.content.startswith(prefix):
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

    async def invoke(self) -> None:
        if not self.is_valid:
            raise InvalidInvocationContext('This Context is invalid for command invocation.')

        if not self.command:
            raise CommandNotFoundError(f'The command "{self._get_command_string()}" could not be found.')

        await self.command.invoke(context=self)

