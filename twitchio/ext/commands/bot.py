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

import asyncio
import importlib.util
import logging
import sys
import types
from typing import TYPE_CHECKING, Any, TypeAlias, Unpack

from twitchio.client import AutoClient, Client
from twitchio.user import PartialUser

from ...utils import _is_submodule
from .context import Context
from .core import Command, CommandErrorPayload, Group, Mixin
from .exceptions import *


if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Iterable, Mapping

    from twitchio.authentication.payloads import ClientCredentialsPayload, ValidateTokenPayload
    from twitchio.eventsub.subscriptions import SubscriptionPayload
    from twitchio.models.eventsub_ import ChannelPointsRedemptionAdd, ChannelPointsRedemptionUpdate, ChatMessage
    from twitchio.types_.eventsub import SubscriptionResponse
    from twitchio.user import User

    from .components import Component
    from .types_ import AutoBotOptions, BotOptions, BotT

    PrefixT: TypeAlias = str | Iterable[str] | Callable[["Bot", "ChatMessage"], Coroutine[Any, Any, str | Iterable[str]]]


logger: logging.Logger = logging.getLogger(__name__)


class Bot(Mixin[None], Client):
    """The TwitchIO ``commands.Bot`` class.

    The Bot is an extension of and inherits from :class:`twitchio.Client` and comes with additonal powerful features for
    creating and managing bots on Twitch.

    Unlike :class:`twitchio.Client`, the :class:`~.Bot` class allows you to easily make use of built-in the commands ext.

    The easiest way of creating and using a bot is via subclassing, some examples are provided below.

    .. note::

        Any examples contained in this class which use ``twitchio.Client`` can be changed to ``commands.Bot``.


    Parameters
    ----------
    client_id: str
        The client ID of the application you registered on the Twitch Developer Portal.
    client_secret: str
        The client secret of the application you registered on the Twitch Developer Portal.
        This must be associated with the same ``client_id``.
    bot_id: str
        The User ID associated with the Bot Account.
        Unlike on :class:`~twitchio.Client` this is a required argument on :class:`~.Bot`.
    owner_id: str | None
        An optional ``str`` which is the User ID associated with the owner of this bot. This should be set to your own user
        accounts ID, but is not required. Defaults to ``None``.
    prefix: str | Iterabale[str] | Coroutine[Any, Any, str | Iterable[str]]
        The prefix(es) to listen to, to determine whether a message should be treated as a possible command.

        This can be a ``str``, an iterable of ``str`` or a coroutine which returns either.

        This is a required argument, common prefixes include: ``"!"`` or ``"?"``.

    Example
    -------

        .. code:: python3

            import asyncio
            import logging

            import twitchio
            from twitchio import eventsub
            from twitchio.ext import commands

            LOGGER: logging.Logger = logging.getLogger("Bot")

            class Bot(commands.Bot):

                def __init__(self) -> None:
                    super().__init__(client_id="...", client_secret="...", bot_id="...", owner_id="...", prefix="!")

                # Do some async setup, as an example we will load a component and subscribe to some events...
                # Passing the bot to the component is completely optional...
                async def setup_hook(self) -> None:

                    # Listen for messages on our channel...
                    # You need appropriate scopes, see the docs on authenticating for more info...
                    payload = eventsub.ChatMessageSubscription(broadcaster_user_id=self.owner_id, user_id=self.bot_id)
                    await self.subscribe_websocket(payload=payload)

                    await self.add_component(SimpleCommands(self))
                    LOGGER.info("Finished setup hook!")

            class SimpleCommands(commands.Component):

                def __init__(self, bot: Bot) -> None:
                    self.bot = bot

                @commands.command()
                async def hi(self, ctx: commands.Context) -> None:
                    '''Command which sends you a hello.'''
                    await ctx.reply(f"Hello {ctx.chatter}!")

                @commands.command()
                async def say(self, ctx: commands.Context, *, message: str) -> None:
                    '''Command which repeats what you say: !say I am an apple...'''
                    await ctx.send(message)

            def main() -> None:
                # Setup logging, this is optional, however a nice to have...
                twitchio.utils.setup_logging(level=logging.INFO)

                async def runner() -> None:
                    async with Bot() as bot:
                        await bot.start()

                try:
                    asyncio.run(runner())
                except KeyboardInterrupt:
                    LOGGER.warning("Shutting down due to Keyboard Interrupt...")

            main()
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str,
        owner_id: str | None = None,
        prefix: PrefixT,
        **options: Unpack[BotOptions],
    ) -> None:
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            **options,
        )

        self._owner_id: str | None = owner_id
        self._get_prefix: PrefixT = prefix
        self._components: dict[str, Component] = {}
        self.__modules: dict[str, types.ModuleType] = {}
        self._owner: User | None = None

    @property
    def bot_id(self) -> str:
        """Property returning the ID of the bot.

        You must ensure you set this via the keyword argument ``bot_id="..."`` in the constructor of this class.

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

    @property
    def owner(self) -> User | None:
        """Property which returns the :class:`~twitchio.User` associated with with the User who owns this bot.

        Could be ``None`` if no ``owner_id`` was passed to the Bot constructor or the request failed.
        Passing a ``owner_id`` is highly recommended.

        .. important::

            If ``owner_id`` has not been passed to the constructor of this :class:`.Bot` this will return ``None``.
        """
        return self._owner

    async def login(self, *, token: str | None = None, load_tokens: bool = True, save_tokens: bool = True) -> None:
        if self._login_called:
            return

        self._login_called = True
        self._save_tokens = save_tokens

        if not self._http.client_id:
            raise RuntimeError('Expected a valid "client_id", instead received: %s', self._http.client_id)

        if not token and not self._http.client_secret:
            raise RuntimeError(f'Expected a valid "client_secret", instead received: {self._http.client_secret}')

        if not token:
            payload: ClientCredentialsPayload = await self._http.client_credentials_token()
            validated: ValidateTokenPayload = await self._http.validate_token(payload.access_token)
            token = payload.access_token

            logger.info("Generated App Token for Client-ID: %s", validated.client_id)

        self._http._app_token = token

        if load_tokens:
            async with self._http._token_lock:
                await self.load_tokens()

        if self._bot_id:
            logger.debug("Fetching Clients self user for %r", self.__class__.__name__)
            partial = PartialUser(id=self._bot_id, http=self._http)
            self._user = await partial.user() if self._fetch_self else partial

        if self._owner_id:
            logger.debug("Fetching owner User for %r", self.__class__.__name__)
            partial = PartialUser(id=self._owner_id, http=self._http)

            try:
                user = await partial.user()
            except Exception:
                logger.warning("Failed to retrieve the Owner User during startup. Owner will be None.")
            else:
                self._owner = user

        await self._setup()

    async def close(self, **options: Any) -> None:
        for module in tuple(self.__modules):
            try:
                await self.unload_module(module)
            except Exception as e:
                logger.debug('Failed to unload module "%s" gracefully during close: %s.', module, e)

        for component in tuple(self._components):
            try:
                await self.remove_component(component)
            except Exception as e:
                logger.debug('Failed to remove component "%s" gracefully during close: %s.', component, e)

        await super().close(**options)

    def _cleanup_component(self, component: Component, /) -> None:
        for command in component.__all_commands__.values():
            self.remove_command(command.name)

        for listeners in component.__all_listeners__.values():
            for listener in listeners:
                self.remove_listener(listener)

    async def _add_component(self, component: Component, /) -> None:
        if component.__component_name__ in self._components:
            raise ComponentLoadError(f'A component named "{component.__component_name__}" has already been loaded.')

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

            if isinstance(e, ComponentLoadError):
                raise e

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

    def get_component(self, name: str, /) -> Component | None:
        """
        Retrieve a Component from the bots loaded Component.
        This will return `None` if the Component was not found.

        Parameters
        ----------
        name: str
            The name of the Component.

        Returns
        -------
        Component | None
        """
        return self._components.get(name)

    def get_context(
        self,
        payload: ChatMessage | ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate,
        *,
        cls: Any = None,
    ) -> Any:
        """Method to create and retrieve a :class:`~.commands.Context` object from either a
        :class:`twitchio.ChatMessage`, :class:`twitchio.ChannelPointsRedemptionAdd` or :class:`twitchio.ChannelPointsRedemptionUpdate`.

        This method can be overriden to accept a custom class which inherits from :class:`~.commands.Context` for use within
        the command invocation process, instead of the default.

        Parameters
        ----------
        payload: :class:`~twitchio.ChatMessage` | :class:`twitchio.ChannelPointsRedemptionAdd` | :class:`twitchio.ChannelPointsRedemptionUpdate`
            The message or redemption to construct a :class:`~.commands.Context` or derivative from.
        cls: Any
            A custom class to use as the context. This should inherit from :class:`~.commands.Context`.

        Examples
        --------

        .. code:: python3

            class CustomContext(commands.Context):
                ...

            class Bot(commands.Bot):

                def get_context(self, payload, *, cls: Any = None) -> CustomContext:
                    cls = cls or CustomContext
                    return cls(payload, bot=self)

            @commands.command()
            async def test(ctx: CustomContext) -> None:
                ...
        """
        cls = cls or Context
        return cls(payload, bot=self)

    async def _process_commands(
        self, payload: ChatMessage | ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate
    ) -> None:
        ctx = self.get_context(payload)
        await self.invoke(ctx)

    async def process_commands(
        self, payload: ChatMessage | ChannelPointsRedemptionAdd | ChannelPointsRedemptionUpdate
    ) -> None:
        await self._process_commands(payload)

    async def invoke(self, ctx: Context[BotT]) -> None:
        try:
            await ctx.invoke()
        except CommandError as e:
            payload = CommandErrorPayload(context=ctx, exception=e)
            self.dispatch("command_error", payload=payload)

    async def event_custom_redemption_add(self, payload: ChannelPointsRedemptionAdd) -> None:
        await self.process_commands(payload)

    async def event_custom_redemption_update(self, payload: ChannelPointsRedemptionUpdate) -> None:
        await self.process_commands(payload)

    async def event_message(self, payload: ChatMessage) -> None:
        if payload.chatter.id == self.bot_id:
            return

        if payload.source_broadcaster is not None:
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

    async def before_invoke(self, ctx: Context[BotT]) -> None:
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

    async def after_invoke(self, ctx: Context[BotT]) -> None:
        """A post invoke hook for all commands that have been added to the bot.

        Commands from :class:`~.commands.Component`'s are included, however if you wish to control them separately,
        see: :meth:`~.commands.Component.component_after_invoke`.

        The post-invoke hook will be called after a valid command has completed invocation. If this coroutine errors,
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

    async def global_guard(self, ctx: Context[BotT], /) -> bool:
        """|coro|

        A global guard applied to all commmands added to the bot.

        This coroutine function should take in one parameter :class:`~.commands.Context` the context surrounding
        command invocation, and return a bool indicating whether a command should be allowed to run.

        If this function returns ``False``, the chatter will not be able to invoke the command and an error will be
        raised. If this function returns ``True`` the chatter will be able to invoke the command,
        assuming all the other guards also pass their predicate checks.

        See: :func:`~.commands.guard` for more information on guards, what they do and how to use them.

        .. note::

            This is the first guard to run, and is applied to every command.

        .. important::

            Unlike command specific guards or :meth:`.commands.Component.guard`, this function must
            be always be a coroutine.


        This coroutine is intended to be overriden when needed and by default always returns ``True``.

        Parameters
        ----------
        ctx: commands.Context
            The context associated with command invocation.

        Raises
        ------
        GuardFailure
            The guard predicate returned ``False`` and prevented the chatter from using the command.
        """
        return True

    async def subscribe_webhook(
        self,
        payload: SubscriptionPayload,
        *,
        callback_url: str | None = None,
        eventsub_secret: str | None = None,
    ) -> SubscriptionResponse | None:
        return await super().subscribe_webhook(
            payload=payload,
            callback_url=callback_url,
            eventsub_secret=eventsub_secret,
        )

    async def subscribe_websocket(
        self,
        payload: SubscriptionPayload,
        *,
        as_bot: bool | None = None,
        token_for: str | PartialUser | None = None,
        socket_id: str | None = None,
    ) -> SubscriptionResponse | None:
        defaults = payload.default_auth
        if as_bot is None:
            as_bot = defaults.get("as_bot", True)
        return await super().subscribe_websocket(payload=payload, as_bot=as_bot, token_for=token_for, socket_id=socket_id)

    def _get_module_name(self, name: str, package: str | None) -> str:
        try:
            return importlib.util.resolve_name(name, package)
        except ImportError as e:
            raise ModuleNotFoundError(f'The module "{name}" was not found.') from e

    async def _remove_module_remnants(self, name: str) -> None:
        for component_name, component in self._components.copy().items():
            if component.__module__ == name or component.__module__.startswith(f"{name}."):
                await self.remove_component(component_name)

    async def _module_finalizers(self, name: str, module: types.ModuleType) -> None:
        try:
            func = getattr(module, "teardown")
        except AttributeError:
            pass
        else:
            try:
                await func(self)
            except Exception:
                pass
        finally:
            self.__modules.pop(name, None)
            sys.modules.pop(name, None)

            name = module.__name__
            for m in list(sys.modules.keys()):
                if _is_submodule(name, m):
                    del sys.modules[m]

    async def load_module(self, name: str, *, package: str | None = None) -> None:
        """|coro|

        Loads a module.

        A module is a python module that contains commands, cogs, or listeners.

        A module must have a global coroutine, ``setup`` defined as the entry point on what to do when the module is loaded.
        The coroutine takes a single argument, the ``bot``.

        .. versionchanged:: 3.0
            This method is now a :term:`coroutine`.

        Parameters
        ----------
        name: str
            The module to load. It must be dot separated like regular Python imports accessing a sub-module.
            e.g. ``foo.bar`` if you want to import ``foo/bar.py``.
        package: str | None
            The package name to resolve relative imports with.
            This is required when loading an extension using a relative path.
            e.g. ``.foo.bar``. Defaults to ``None``.

        Raises
        ------
        ModuleAlreadyLoadedError
            The module is already loaded.
        ModuleNotFoundError
            The module could not be imported.
            Also raised if module could not be resolved using the `package` parameter.
        ModuleLoadFailure
            There was an error loading the module.
        NoEntryPointError
            The module does not have a setup coroutine.
        TypeError
            The module's setup function is not a coroutine.
        """

        name = self._get_module_name(name, package)

        if name in self.__modules:
            raise ModuleAlreadyLoadedError(f"The module {name} has already been loaded.")

        spec = importlib.util.find_spec(name)
        if spec is None:
            raise ModuleNotFoundError(name)

        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module

        try:
            spec.loader.exec_module(module)  # type: ignore
        except Exception as e:
            del sys.modules[name]
            raise ModuleLoadFailure(name, e) from e

        try:
            entry = getattr(module, "setup")
        except AttributeError as exc:
            del sys.modules[name]
            raise NoEntryPointError(f'The module "{module}" has no setup coroutine.') from exc

        if not asyncio.iscoroutinefunction(entry):
            del sys.modules[name]
            raise TypeError(f'The module "{module}"\'s setup function is not a coroutine.')

        try:
            await entry(self)
        except Exception as e:
            del sys.modules[name]
            await self._remove_module_remnants(module.__name__)
            raise ModuleLoadFailure(name, e) from e

        self.__modules[name] = module

    async def unload_module(self, name: str, *, package: str | None = None) -> None:
        """|coro|

        Unloads a module.

        When the module is unloaded, all commands, listeners and components are removed from the bot, and the module is un-imported.

        You can add an optional global coroutine of ``teardown`` to the module to do miscellaneous clean-up if necessary.
        This also takes a single paramter of the ``bot``, similar to ``setup``.

        .. versionchanged:: 3.0
            This method is now a :term:`coroutine`.

        Parameters
        ----------
        name: str
            The module to unload. It must be dot separated like regular Python imports accessing a sub-module.
            e.g. ``foo.bar`` if you want to import ``foo/bar.py``.
        package: str | None
            The package name to resolve relative imports with.
            This is required when unloading an extension using a relative path.
            e.g. ``.foo.bar``. Defaults to ``None``.

        Raises
        ------
        ModuleNotLoaded
            The module was not loaded.
        """

        name = self._get_module_name(name, package)
        module = self.__modules.get(name)

        if module is None:
            raise ModuleNotLoadedError(name)

        await self._remove_module_remnants(module.__name__)
        await self._module_finalizers(name, module)

    async def reload_module(self, name: str, *, package: str | None = None) -> None:
        """|coro|

        Atomically reloads a module.

        This attempts to unload and then load the module again, in an atomic way.
        If an operation fails mid reload then the bot will revert back to the prior working state.

        .. versionchanged:: 3.0
            This method is now a :term:`coroutine`.

        Parameters
        ----------
        name: str
            The module to unload. It must be dot separated like regular Python imports accessing a sub-module.
            e.g. ``foo.bar`` if you want to import ``foo/bar.py``.
        package: str | None
            The package name to resolve relative imports with.
            This is required when unloading an extension using a relative path.
            e.g. ``.foo.bar``. Defaults to ``None``.

        Raises
        ------
        ModuleNotLoaded
            The module was not loaded.
        ModuleNotFoundError
            The module could not be imported.
            Also raised if module could not be resolved using the `package` parameter.
        ModuleLoadFailure
            There was an error loading the module.
        NoEntryPointError
            The module does not have a setup coroutine.
        TypeError
            The module's setup function is not a coroutine.
        """

        name = self._get_module_name(name, package)
        module = self.__modules.get(name)

        if module is None:
            raise ModuleNotLoadedError(name)

        modules = {name: module for name, module in sys.modules.items() if _is_submodule(module.__name__, name)}

        try:
            await self._remove_module_remnants(module.__name__)
            await self._module_finalizers(name, module)
            await self.load_module(name)
        except Exception as e:
            await module.setup(self)
            self.__modules[name] = module
            sys.modules.update(modules)
            raise e

    @property
    def modules(self) -> Mapping[str, types.ModuleType]:
        """Mapping[:class:`str`, :class:`py:types.ModuleType`]: A read-only mapping of extension name to extension."""
        return types.MappingProxyType(self.__modules)


class AutoBot(Bot, AutoClient):
    """The TwitchIO :class:`~twitchio.ext.commands.AutoBot` class used to easily manage Twitch Conduits and Shards.

    This class behaves identically to :class:`~twitchio.ext.commands.Bot` with the addition of inheriting from
    :class:`~twitchio.AutoClient`. See: :class:`~twitchio.AutoClient` for more details on how this class differs from
    the :class:`~twitchio.ext.commands.Bot` which inherits from :class:`~twitchio.Client`.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str,
        owner_id: str | None = None,
        prefix: PrefixT,
        **options: Unpack[AutoBotOptions],
    ) -> None:
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            owner_id=owner_id,
            prefix=prefix,
            **options,
        )
