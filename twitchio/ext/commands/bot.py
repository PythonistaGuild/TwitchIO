from __future__ import annotations

import asyncio
from typing import Coroutine, Dict, List, Optional, Union

from .commands import Command
from .components import Component
from .context import Context
from twitchio import Client, Message


class Bot(Client):

    def __init__(self, prefix: Union[list, callable, Coroutine], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__commands: Dict[str, Command] = {}
        self.__components: Dict[str, Component] = {}

        self._unassigned_prefixes = prefix
        self._prefixes: List[str] = []

        self._in_context: bool = False

    async def __aenter__(self) -> Bot:
        self._in_context = True

        await self._prepare_prefixes()
        await super().__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._in_context = False

        await super().__aexit__(exc_type, exc_val, exc_tb)

    def run(self, token: Optional[str] = None) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._prepare_prefixes())

        super().run(token=token)

    async def start(self, token: Optional[str] = None) -> None:
        if not self._in_context:
            raise RuntimeError('"bot.start" can only be used within the bot async context manager.')

        await super().start(token=token)

    @property
    def prefixes(self) -> List[str]:
        return self._prefixes

    @property
    def commands(self) -> Dict[str, Command]:
        return self.__commands

    @property
    def components(self) -> Dict[str, Component]:
        return self.__components

    async def _prepare_prefixes(self) -> None:
        if asyncio.iscoroutine(self._unassigned_prefixes):
            prefixes = await self._unassigned_prefixes(self)

        elif callable(self._unassigned_prefixes):
            prefixes = self._unassigned_prefixes(self)

        else:
            prefixes = self._unassigned_prefixes

        if isinstance(prefixes, str):
            self._prefixes = [prefixes]

        elif isinstance(prefixes, list):
            if not all(isinstance(prefix, str) for prefix in prefixes):
                raise TypeError('prefix parameter must be a str, list of str or callable/coroutine returning either.')
            self._prefixes = prefixes

        else:
            raise TypeError('prefix parameter must be a str, list of str or callable/coroutine returning either.')

    def get_context(self, message: Message, *, cls: Optional[Context] = Context) -> Context:
        # noinspection PyTypeChecker
        if cls and not issubclass(cls, Context):
            raise TypeError(f'cls parameter must derive from {Context!r}.')

        return cls(message, self)

    async def process_commands(self, message: Message):
        context = self.get_context(message=message)

        if context.is_valid:
            await context.invoke()

    def add_command(self, command: Command) -> None:
        if not isinstance(command, Command):
            raise TypeError(f'The command argument must be a subclass of commands.Command.')

        if command.name in self.commands or any(x in self.commands for x in command.aliases):
            raise ValueError(f'Command "{command.name}" is already registered command or alias.')

        if not asyncio.iscoroutinefunction(command._callback):
            raise TypeError('Command callbacks must be coroutines.')

        command._instance = command._component or self

        self.__commands[command.name] = command

    async def add_component(self, component: Component) -> None:
        pass

    async def remove_component(self, component: Component) -> None:
        pass

    async def load_extension(self):
        pass

    async def unload_extension(self):
        pass

    async def reload_extension(self):
        pass







