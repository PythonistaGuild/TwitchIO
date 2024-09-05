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
from typing import TYPE_CHECKING, Unpack

from twitchio.client import Client

from .context import Context
from .core import CommandErrorPayload, Mixin
from .exceptions import *


if TYPE_CHECKING:
    from models.eventsub_ import ChatMessage
    from types_.options import Prefix_T

    from twitchio.types_.options import ClientOptions


logger: logging.Logger = logging.getLogger(__name__)


class Bot(Mixin[None], Client):
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str,
        prefix: Prefix_T,
        **options: Unpack[ClientOptions],
    ) -> None:
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            **options,
        )

        self._get_prefix: Prefix_T = prefix

    @property
    def bot_id(self) -> str:
        assert self._bot_id
        return self._bot_id

    async def _process_commands(self, message: ChatMessage) -> None:
        ctx: Context = Context(message, bot=self)

        try:
            await self.invoke(ctx)
        except CommandError as e:
            payload = CommandErrorPayload(context=ctx, exception=e)
            self.dispatch("command_error", payload=payload)

    async def process_commands(self, message: ChatMessage) -> None:
        await self._process_commands(message)

    async def invoke(self, ctx: Context) -> None:
        await ctx.invoke()

    async def event_channel_chat_message(self, payload: ChatMessage) -> None:
        if payload.chatter.id == self.bot_id:
            return

        await self.process_commands(payload)

    async def event_command_error(self, payload: CommandErrorPayload) -> None:
        msg = f'Ignoring exception in command "{payload.context.command}":\n'
        logger.error(msg, exc_info=payload.exception)

    async def before_invoke_hook(self, ctx: Context) -> None: ...

    async def after_invoke_hook(self, ctx: Context) -> None: ...
