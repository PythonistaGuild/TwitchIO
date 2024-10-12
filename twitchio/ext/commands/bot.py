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

import logging
from typing import TYPE_CHECKING, Any, Unpack

from twitchio.client import Client

from .context import Context
from .converters import _BaseConverter
from .core import Command, CommandErrorPayload, Group, Mixin
from .exceptions import *


if TYPE_CHECKING:
    from models.eventsub_ import ChatMessage
    from types_.options import Prefix_T

    from twitchio.types_.options import ClientOptions

    from .components import Component


logger: logging.Logger = logging.getLogger(__name__)


class Bot(Mixin[None], Client):
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str,
        owner_id: str | None = None,
        prefix: Prefix_T,
        **options: Unpack[ClientOptions],
    ) -> None:
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            **options,
        )

        self._owner_id: str | None = owner_id
        self._get_prefix: Prefix_T = prefix
        self._components: dict[str, Component] = {}
        self._base_converter: _BaseConverter = _BaseConverter(self)

    @property
    def bot_id(self) -> str:
        assert self._bot_id
        return self._bot_id

    @property
    def owner_id(self) -> str | None:
        return self._owner_id

    def _cleanup_component(self, component: Component, /) -> None:
        for command in component.__all_commands__.values():
            self.remove_command(command.name)

        for listeners in component.__all_listeners__.values():
            for listener in listeners:
                self.remove_listener(listener)

    async def _add_component(self, component: Component, /) -> None:
        for command in component.__all_commands__.values():
            command._injected = component

            if isinstance(command, Group):
                for sub in command.walk_commands():
                    sub._injected = component

            self.add_command(command)

        for name, listeners in component.__all_listeners__.items():
            for listener in listeners:
                self.add_listener(listener, event=name)

        await component.component_load()

    async def add_component(self, component: Component, /) -> None:
        try:
            await self._add_component(component)
        except Exception as e:
            self._cleanup_component(component)
            raise ComponentLoadError from e

        self._components[component.__component_name__] = component

    async def _process_commands(self, message: ChatMessage) -> None:
        ctx: Context = Context(message, bot=self)
        await self.invoke(ctx)

    async def process_commands(self, message: ChatMessage) -> None:
        await self._process_commands(message)

    async def invoke(self, ctx: Context) -> None:
        try:
            await ctx.invoke()
        except CommandError as e:
            payload = CommandErrorPayload(context=ctx, exception=e)
            self.dispatch("command_error", payload=payload)

    async def event_channel_chat_message(self, payload: ChatMessage) -> None:
        if payload.chatter.id == self.bot_id:
            return

        await self.process_commands(payload)

    async def event_command_error(self, payload: CommandErrorPayload) -> None:
        command: Command[Any, ...] | None = payload.context.command
        if command and command.has_error and payload.context.error_dispatched:
            return

        msg = f'Ignoring exception in command "{payload.context.command}":\n'
        logger.error(msg, exc_info=payload.exception)

    async def before_invoke(self, ctx: Context) -> None: ...

    async def after_invoke(self, ctx: Context) -> None: ...

    async def guard(self, ctx: Context) -> None: ...
