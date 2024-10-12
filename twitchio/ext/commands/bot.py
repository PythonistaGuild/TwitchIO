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
        """Property returning the ID of the bot.

        This **MUST** be set via the keyword argument ``bot_id="..."`` in the constructor of this class.

        Returns
        -------
        str
            The ``bot_id`` that was set.
        """
        assert self._bot_id
        return self._bot_id

    @property
    def owner_id(self) -> str | None:
        """Property returning the ID of the user who owns this bot.

        This can be set via the keyword argument ``owner_id="..."`` in the constructor of this class.

        Returns
        -------
        str | None
            The owner ID that has been set. ``None`` if this has not been set.
        """
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
        """|coro|

        Method to add a :class:`.commands.Component` to the bot.

        All :class:`~.commands.Command` and :meth:`~.commands.Component.listener`'s in the component will be loaded alongside
        the component.

        If this method fails, including if :meth:`~.commands.Component.component_load` fails, everything will be rolled back
        and cleaned up and a :exc:`.commands.ComponentLoadError` will be raised from the original exception.

        Parameters
        ----------
        component: :class:`~.commands.Component`
            The component to add to the bot.

        Raises
        ------
        ComponentLoadError
            The component failed to load.
        """
        try:
            await self._add_component(component)
        except Exception as e:
            self._cleanup_component(component)
            raise ComponentLoadError from e

        self._components[component.__component_name__] = component

    async def remove_component(self, name: str, /) -> Component | None:
        """|coro|

        Method to remove a :class:`.commands.Component` from the bot.

        All :class:`~.commands.Command` and :meth:`~.commands.Component.listener`'s in the component will be unloaded
        alongside the component.

        If this method fails when :meth:`~.commands.Component.component_teardown` fails, the component will still be unloaded
        completely from the bot, with the exception being logged.

        Parameters
        ----------
        name: str
            The name of the component to unload.

        Returns
        -------
        Component | None
            The component that was removed. ``None`` if the component was not found.
        """
        component: Component | None = self._components.pop(name, None)
        if not component:
            return component

        self._cleanup_component(component)

        try:
            await component.component_teardown()
        except Exception as e:
            msg = f"Ignoring exception in {component.__class__.__qualname__}.component_teardown: {e}\n"
            logger.error(msg, exc_info=e)

        return component

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
        """An event called when an error occurs during command invocation.

        By default this event logs the exception raised.

        You can override this method, however you should take care to log unhandled exceptions.

        Parameters
        ----------
        payload: :class:`.commands.CommandErrorPayload`
            The payload associated with this event.
        """
        command: Command[Any, ...] | None = payload.context.command
        if command and command.has_error and payload.context.error_dispatched:
            return

        msg = f'Ignoring exception in command "{payload.context.command}":\n'
        logger.error(msg, exc_info=payload.exception)

    async def before_invoke(self, ctx: Context) -> None:
        """A pre invoke hook for all commands that have been added to the bot.

        Commands from :class:`~.commands.Component`'s are included, however if you wish to control them separately,
        see: :meth:`~.commands.Component.component_before_invoke`.

        The pre-invoke hook will be called directly before a valid command is scheduled to run. If this coroutine errors,
        a :exc:`~.commands.CommandHookError` will be raised from the original error.

        Useful for setting up any state like database connections or http clients for command invocation.

        The order of calls with the pre-invoke hooks is:

        - :meth:`.commands.Bot.before_invoke`

        - :meth:`.commands.Component.component_before_invoke`

        - Any ``before_invoke`` hook added specifically to the :class:`~.commands.Command`.


        .. note::

            This hook only runs after successfully parsing arguments and passing all guards associated with the
            command, component (if applicable) and bot.

        Parameters
        ----------
        ctx: :class:`.commands.Context`
            The context associated with command invocation, before being passed to the command.
        """

    async def after_invoke(self, ctx: Context) -> None:
        """A post invoke hook for all commands that have been added to the bot.

        Commands from :class:`~.commands.Component`'s are included, however if you wish to control them separately,
        see: :meth:`~.commands.Component.component_after_invoke`.

        The post-invoke hook will be called after a valid command has been invoked. If this coroutine errors,
        a :exc:`~.commands.CommandHookError` will be raised from the original error.

        Useful for cleaning up any state like database connections or http clients.

        The order of calls with the post-invoke hooks is:

        - :meth:`.commands.Bot.after_invoke`

        - :meth:`.commands.Component.component_after_invoke`

        - Any ``after_invoke`` hook added specifically to the :class:`~.commands.Command`.


        .. note::

            This hook is always called even when the :class:`~.commands.Command` fails to invoke but similar to
            :meth:`.before_invoke` only if parsing arguments and guards are successfully completed.

        Parameters
        ----------
        ctx: :class:`.commands.Context`
            The context associated with command invocation, after being passed through the command.
        """

    async def guard(self, ctx: Context) -> None: ...
