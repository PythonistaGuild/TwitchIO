from __future__ import annotations
import asyncio
import typing

from twitchio import Client
from .commands import Command, Collection

if typing.TYPE_CHECKING:
    from ..components import ComponentMeta


class Bot(Client):

    def __init__(self, prefix: typing.Union[list, callable, typing.Coroutine], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._commands = {}

    def add_component(self, component: ComponentMeta):
        component._bot = self

    def add_command(self, command):

        if not asyncio.iscoroutinefunction(command._callback):
            raise TypeError('Commands must be coroutines.')

        if not isinstance(command, (Command, Collection)):
            raise TypeError(f'Commands must be an instance of Command or Collection not <{command!r}>')

        if command._name in self._commands:
            raise RuntimeError(f'The command <{command._name}> already exists.')

        for alias in command._aliases:
            if alias in self._commands:
                raise RuntimeError(f'A command with the name/alias <{command._name}> already exists.')

        if isinstance(command, Collection):
            # TODO Stuck here trying to figure out whether a collection has a command
            # With the same name or alias...
            pass

        self._commands[command._name] = command







