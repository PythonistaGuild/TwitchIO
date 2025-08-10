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
import logging
import math
from collections import defaultdict
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, Self, Unpack, overload

from .authentication import ManagedHTTPClient, Scopes, UserTokenPayload
from .eventsub.enums import SubscriptionType
from .eventsub.websockets import Websocket, WebsocketClosed
from .exceptions import HTTPException, MissingConduit
from .http import HTTPAsyncIterator
from .models.bits import Cheermote, ExtensionTransaction
from .models.ccls import ContentClassificationLabel
from .models.channels import ChannelInfo
from .models.chat import ChatBadge, ChatterColor, EmoteSet, GlobalEmote
from .models.eventsub_ import Conduit, WebsocketWelcome
from .models.games import Game
from .models.teams import Team
from .payloads import EventErrorPayload, WebsocketSubscriptionData
from .user import ActiveExtensions, Extension, PartialUser, User
from .utils import MISSING, EventWaiter, clamp, unwrap_function
from .web import AiohttpAdapter, has_starlette
from .web.utils import BaseAdapter


if TYPE_CHECKING:
    import datetime
    from collections.abc import Awaitable, Callable, Collection, Coroutine

    import aiohttp

    from .authentication import ClientCredentialsPayload, ValidateTokenPayload
    from .eventsub.subscriptions import SubscriptionPayload
    from .http import HTTPAsyncIterator
    from .models.clips import Clip
    from .models.entitlements import Entitlement, EntitlementStatus
    from .models.eventsub_ import ConduitShard, EventsubSubscription, EventsubSubscriptions
    from .models.search import SearchChannel
    from .models.streams import Stream, VideoMarkers
    from .models.videos import Video
    from .types_.conduits import ShardUpdateRequest
    from .types_.eventsub import ShardStatus, SubscriptionCreateTransport, SubscriptionResponse, _SubscriptionData
    from .types_.options import AutoClientOptions, ClientOptions, WaitPredicateT
    from .types_.tokens import TokenMappingData


logger: logging.Logger = logging.getLogger(__name__)


__all__ = ("AutoClient", "Client", "ConduitInfo", "MultiSubscribeError", "MultiSubscribePayload", "MultiSubscribeSuccess")


class Client:
    """The TwitchIO Client.

    The ``Client`` acts as an entry point to the Twitch API, EventSub and OAuth and serves as a base for chat-bots.

    :class:`~twitchio.ext.commands.Bot` inherits from this class and such should be treated as a ``Client`` with an in-built
    commands extension.

    You don't need to :meth:`~.start` or :meth:`~.run` the ``Client`` to use it soley as a HTTP Wrapper,
    but you must still :meth:`~.login` with this use case.

    Parameters
    -----------
    client_id: str
        The client ID of the application you registered on the Twitch Developer Portal.
    client_secret: str
        The client secret of the application you registered on the Twitch Developer Portal.
        This must be associated with the same `client_id`.
    bot_id: str | None
        An optional `str` which should be the User ID associated with the Bot Account.

        It is highly recommended setting this parameter as it will allow TwitchIO to use the bot's own tokens where
        appropriate and needed.
    redirect_uri: str | None
        An optional ``str`` to set as the redirect uri for anything relating to
        Twitch OAuth via :class:`twitchio.web.StarletteAdapter` or :class:`twitchio.web.AiohttpAdapter`.
        This is a convenience attribute, it is preferred you
        use a custom :class:`~twitchio.web.StarletteAdapter` or :class:`~twitchio.web.AiohttpAdapter` instead.
    scopes: twitchio.Scopes | None
        An optional :class:`~twitchio.Scopes` object to use as defaults when using anything related to Twitch OAuth.

        Useful when you want to set default scopes for users to authenticate with.
    session: aiohttp.ClientSession | None
        An optional :class:`aiohttp.ClientSession` to use for all HTTP requests including any requests made with
        :class:`~twitchio.Asset`'s.
    adapter:  twitchio.StarletteAdapter | twitchio.AiohttpAdapter | None
        An optional :class:`twitchio.web.StarletteAdapter` or :class:`twitchio.web.AiohttpAdapter` to use as the clients web server adapter.

        The adapter is a built-in webserver used for OAuth and when needed for EventSub over Webhooks.

        When this is not provided, it will default to a :class:`twitchio.web.AiohttpAdapter` with default settings.
    fetch_client_user: bool
        An optional bool indicating whether to fetch and cache the client/bot accounts own :class:`.User` object to use with
        :attr:`.user`.
        Defaults to ``True``. You must pass ``bot_id`` for this parameter to have any effect.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str | None = None,
        **options: Unpack[ClientOptions],
    ) -> None:
        redirect_uri: str | None = options.get("redirect_uri")
        scopes: Scopes | None = options.get("scopes")
        session: aiohttp.ClientSession = options.get("session", MISSING) or MISSING
        self._bot_id: str | None = bot_id

        self._http = ManagedHTTPClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
            client=self,
        )
        if not has_starlette:
            msg = "If you require the StarletteAdapter please install the required packages: 'pip install twitchio[starlette]'."
            logger.warning(msg)

        adapter: BaseAdapter | type[BaseAdapter] = options.get("adapter", AiohttpAdapter)
        if isinstance(adapter, BaseAdapter):
            adapter.client = self
            self._adapter = adapter
        else:
            self._adapter = adapter()
            self._adapter.client = self

        # Own Client User. Set in login...
        self._fetch_self: bool = options.get("fetch_client_user", True)
        self._user: User | PartialUser | None = None

        self._listeners: dict[str, set[Callable[..., Coroutine[Any, Any, None]]]] = defaultdict(set)
        self._wait_fors: dict[str, set[EventWaiter]] = defaultdict(set)

        self._login_called: bool = False
        self._has_closed: bool = False
        self._save_tokens: bool = True

        # Websockets for EventSub
        self._websockets: dict[str, dict[str, Websocket]] = defaultdict(dict)

        self._ready_event: asyncio.Event = asyncio.Event()
        self._ready_event.clear()

        self.__waiter: asyncio.Event = asyncio.Event()
        self._setup_called = False

    @property
    def adapter(self) -> BaseAdapter:
        """Property returning the :class:`~twitchio.AiohttpAdapter` or :class:`~twitchio.StarlettepAdapter` the bot is
        currently running."""
        return self._adapter

    async def set_adapter(self, adapter: BaseAdapter) -> None:
        """|coro|

        Method which sets and starts a new web adapter which inherits from either :class:`~twitchio.AiohttpAdapter` or
        :class:`~twitchio.StarlettepAdapter` or implements the :class:`~twitchio.BaseAdapter` specifications.

        Parameters
        ----------
        adapter: :class:`~twitchio.BaseAdapter`
            The new adapter to assign and start.

        Returns
        -------
        None
        """
        if self._adapter and self._adapter._running:
            await self._adapter.close(False)

        self._adapter = adapter
        self._adapter.client = self

        if self._setup_called and not self._adapter._running:
            await self._adapter.run()

    @property
    def tokens(self) -> MappingProxyType[str, TokenMappingData]:
        """Property which returns a read-only mapping of the tokens that are managed by the `Client`.

        **For various methods of managing the tokens on the client, see:**

        :meth:`~.add_token`

        :meth:`~.remove_token`

        :meth:`~.load_tokens`

        :meth:`~.save_tokens`


        .. warning::

            This method returns sensitive information such as user-tokens. You should take care not to expose these tokens.
        """
        return MappingProxyType(dict(self._http._tokens))

    @property
    def bot_id(self) -> str | None:
        """Property which returns the User-ID associated with this :class:`~twitchio.Client` if set, or `None`.

        This can be set using the `bot_id` parameter when initialising the :class:`~twitchio.Client`.

        .. note::

            It is highly recommended to set this parameter.
        """
        return self._bot_id

    @property
    def user(self) -> User | PartialUser | None:
        """Property which returns the :class:`.User` or :class:`.PartialUser` associated with with the Client/Bot.

        In most cases this will be a :class:`.User` object. Could be :class:`.PartialUser` when passing ``False`` to the
        ``fetch_client_user`` keyword parameter of Client.

        Could be ``None`` if no ``bot_id`` was passed to the Client constructor.

        .. important::

            If ``bot_id`` has not been passed to the constructor of :class:`.Client` this will return ``None``.
        """
        return self._user

    async def event_error(self, payload: EventErrorPayload) -> None:
        """
        Event called when an error occurs in an event or event listener.

        This event can be overriden to handle event errors differently.
        By default, this method logs the error and ignores it.

        .. warning::

            If an error occurs in this event, it will be ignored and logged. It will **NOT** re-trigger this event.

        Parameters
        ----------
        payload: EventErrorPayload
            A payload containing the Exception, the listener, and the original payload.
        """
        logger.error('Ignoring Exception in listener "%s":\n', payload.listener.__qualname__, exc_info=payload.error)

    async def _dispatch(self, listener: Callable[..., Coroutine[Any, Any, None]], *, original: Any | None = None) -> None:
        try:
            called_: Awaitable[None] = listener(original) if original else listener()
            await called_
        except Exception as e:
            try:
                payload: EventErrorPayload = EventErrorPayload(
                    error=e, listener=unwrap_function(listener), original=original
                )
                await self.event_error(payload)
            except Exception as inner:
                logger.error(
                    'Ignoring Exception in listener "%s.event_error":\n', self.__class__.__qualname__, exc_info=inner
                )

    def dispatch(self, event: str, payload: Any | None = None) -> None:
        name: str = "event_" + event.lower()

        listeners: set[Callable[..., Coroutine[Any, Any, None]]] = self._listeners[name]
        extra: Callable[..., Coroutine[Any, Any, None]] | None = getattr(self, name, None)
        if extra:
            listeners.add(extra)

        logger.debug('Dispatching event: "%s" to %d listeners.', name, len(listeners))
        _ = [asyncio.create_task(self._dispatch(listener, original=payload)) for listener in listeners]

        waits: set[asyncio.Task[None]] = set()
        for waiter in self._wait_fors[name]:
            coro = waiter(payload) if payload else waiter()
            task = asyncio.create_task(coro, name=f'TwitchIO:Client.wait_for: "{name}"')

            task.add_done_callback(waits.discard)
            waits.add(task)

    def safe_dispatch(self, name: str, *, payload: Any | None = None) -> None:
        """Method to dispatch a custom :ref:`event <Event Ref>`.

        When an event is dispatched all listeners listening to the event, coroutine functions defined on the
        :class:`~twitchio.Client` with the same name, and :meth:`~twitchio.Client.wait_for` waiting for the event will be
        triggered.

        Internally the :class:`~twitchio.Client` uses a method similar to this, however to avoid conflicts with built-in events
        it is not documented and you should use this method instead when needing a custom event dispatched.

        This method avoids conflicts with internal events by prefixing the name of the event with ``event_safe_``;
        specifically in this case ``safe_`` is added between the ``event_`` prefix and the name of the event.

        All events in TwitchIO, including custom ones, must take between ``0`` or ``1`` arguments only. If ``None`` is
        passed to the payload parameter (default), the event will be dispatched with no arguments attached. Otherwise you can
        provide one parameter ``payload`` which (ideally) is a class containing all the information and methods needed in
        your event. Keep in mind that events expect consistency; E.g. If your event takes a payload argument it should
        **always** take a payload argument and vice versa. If designing an ``ext`` for TwitchIO this also will be inline
        with how end-users will expect events to work.

        .. note::

            If you intend on using this in a custom ``ext`` for example; consider also adding a small prefix to the name to
            identify your extension from others.

        .. warning::

            Overriding this method is highly discouraged. Any changes made to the safe name of the event may have hard to
            track and unwanted side effects. TwitchIO uses events internally and any changes to these dispatched events
            internally by users may also lead to consequences such as being rate limted or banned by Twitch, banned by
            broadcasters or; memory, CPU, network and other performance issues.

        Parameters
        ----------
        name: str
            The name of the event you wish to dispatch. Remember the name of the event will be prefixed with ``event_safe_``.
        payload: Any | None
            The payload object dispatched to all your listeners. Defaults to ``None`` which would pass ``0`` arguments to all
            listeners.

        Example
        -------

        .. code:: python3

            class CoolPayload:

                def __init__(self, number: int) -> None:
                    self.number = number


            class CoolComponent(commands.Component):

                @commands.Component.listener()
                async def event_safe_cool(self, payload: CoolPayload) -> None:
                    print(f"Received 'cool' event with number: {payload.number}")


            # Somewhere...
            payload = CoolPayload(number=9)
            client.safe_dispatch("cool", payload)
        """
        name_ = f"safe_{name}"
        self.dispatch(name_, payload)

    async def setup_hook(self) -> None:
        """
        Method called after :meth:`~.login` has been called but before the client is ready.

        :meth:`~.start` calls :meth:`~.login` internally for you, so when using
        :meth:`~.start` this method will be called after the client has generated and validated an
        app token. The client won't complete start up until this method has completed.

        This method is intended to be overriden to provide an async environment for any setup required.

        By default, this method does not implement any logic.
        """
        ...

    async def login(self, *, token: str | None = None, load_tokens: bool = True, save_tokens: bool = True) -> None:
        """|coro|

        Method to login the client and generate or store an app token.

        This method is called automatically when using :meth:`~.start`.
        You should **NOT** call this method if you are using :meth:`~.start`.

        This method calls :meth:`~.setup_hook`.

        .. note::

            If no token is provided, the client will attempt to generate a new app token for you.
            This is usually preferred as generating a token is inexpensive and does not have rate-limits associated with it.

        Parameters
        ----------
        token: str | None
            An optional app token to use instead of generating one automatically.
        load_tokens: bool
            Optional bool which indicates whether the :class:`Client` should call :meth:`.load_tokens` during
            login automatically. Defaults to ``True``.
        save_tokens: bool
            Optional bool which inicates whether the :class:`Client` should call :meth:`.save_tokens` during the
            :meth:`.close` automatically. Defaults to ``True``.
        """
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
        else:
            self._http._has_loaded = True

        if self._bot_id:
            logger.debug("Fetching Clients self user for %r", self.__class__.__name__)
            partial = PartialUser(id=self._bot_id, http=self._http)
            self._user = await partial.user() if self._fetch_self else partial

        # Might need a skip_setup parameter?
        await self._setup()

    async def _setup(self) -> None:
        await self.setup_hook()
        self._setup_called = True

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start(
        self,
        token: str | None = None,
        *,
        with_adapter: bool = True,
        load_tokens: bool = True,
        save_tokens: bool = True,
    ) -> None:
        """|coro|

        Method to login and run the `Client` asynchronously on an already running event loop.

        You should not call :meth:`~.login` if you are using this method as it is called internally
        for you.

        .. note::

            This method blocks asynchronously until the client is closed.

        Parameters
        ----------
        token: str | None
            An optional app token to use instead of generating one automatically.
        with_adapter: bool
            Whether to start and run a web adapter. Defaults to `True`.
        load_tokens: bool
            Optional bool which indicates whether the :class:`Client` should call :meth:`.load_tokens` during
            :meth:`.login` automatically. Defaults to ``True``.
        save_tokens: bool
            Optional bool which inicates whether the :class:`Client` should call :meth:`.save_tokens` during the
            :meth:`.close` automatically. Defaults to ``True``.

        Examples
        --------

        .. code:: python3

            import asyncio
            import twitchio


            async def main() -> None:
                client = twitchio.Client(...)

                async with client:
                    await client.start()
        """
        self.__waiter.clear()
        await self.login(token=token, load_tokens=load_tokens, save_tokens=save_tokens)

        if with_adapter and not self._adapter._running:
            await self._adapter.run()

        # Dispatch ready event... May change places in the future.
        self.dispatch("ready")
        self._ready_event.set()

        try:
            await self.__waiter.wait()
        finally:
            self._ready_event.clear()
            await self.close()

    def run(
        self,
        token: str | None = None,
        *,
        with_adapter: bool = True,
        load_tokens: bool = True,
        save_tokens: bool = True,
    ) -> None:
        """Method to login the client and create a continuously running event loop.

        The behaviour of this method is similar to :meth:`~.start` but instead of being used in an already running
        async environment, this method will setup and create an async environment for you.

        You should not call :meth:`~.login` if you are using this method as it is called internally
        for you.

        .. important::

            You can not use this method in an already running async event loop. See: :meth:`~.start` for starting the
            client in already running async environments.

        .. note::

            This method will block until the client is closed.

        Parameters
        ----------
        token: str | None
            An optional app token to use instead of generating one automatically.
        with_adapter: bool
            Whether to start and run a web adapter. Defaults to `True`.
        load_tokens: bool
            Optional bool which indicates whether the :class:`Client` should call :meth:`.load_tokens` during
            :meth:`.login` automatically. Defaults to ``True``.
        save_tokens: bool
            Optional bool which inicates whether the :class:`Client` should call :meth:`.save_tokens` during the
            :meth:`.close` automatically. Defaults to ``True``.

        Examples
        --------

        .. code:: python3

            client = twitchio.Client(...)
            client.run()
        """

        async def run() -> None:
            async with self:
                await self.start(token=token, with_adapter=with_adapter, load_tokens=load_tokens, save_tokens=save_tokens)

        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            pass

    async def close(self, **options: Any) -> None:
        r"""|coro|

        Method which closes the :class:`~Client` gracefully.

        This method is called for you automatically when using :meth:`~.run` or when using the client with the
        async context-manager, E.g: `async with client:`

        You can override this method to implement your own clean-up logic, however you should call `await super().close()`
        when doing this.

        Parameters
        ----------
        \*
        save_tokens: bool | None
            An optional bool override which allows overriding the identical keyword-argument set in either
            :meth:`.run`, :meth:`.start` or :meth:`.login` to call the :meth:`.save_tokens` coroutine.
            Defaults to ``None`` which won't override.

        Examples
        --------

        .. code:: python3

            async def close(self) -> None:
                # Own clenup logic...
                ...
                await super().close()
        """
        if self._has_closed:
            logger.debug("Client was already set as closed. Disregarding call to close.")
            return

        self._has_closed = True
        await self._http.close()

        if self._adapter._runner_task is not None:
            try:
                await self._adapter.close()
            except Exception as e:
                logger.debug("Encountered a cleanup error while closing the Client Web Adapter: %s. Disregarding.", e)
                pass

        sockets: list[Websocket] = [w for p in self._websockets.values() for w in p.values()]
        logger.debug("Attempting cleanup on %d EventSub websocket connection(s).", len(sockets))

        for socket in sockets:
            await socket.close()

        save_tokens = options.get("save_tokens")
        save = save_tokens if save_tokens is not None else self._save_tokens

        if save:
            async with self._http._token_lock:
                await self.save_tokens()

        self._http.cleanup()
        self.__waiter.set()
        logger.debug("Cleanup completed on %r.", self.__class__.__name__)

    async def wait_until_ready(self) -> None:
        """|coro|

        Method which suspends the current coroutine and waits for "event_ready" to be dispatched.

        If "event_ready" has previously been dispatched, this method returns immediately.

        "event_ready" is dispatched after the HTTP Client has successfully logged in, tokens have sucessfully been loaded,
        and :meth:`.setup_hook` has completed execution.

        .. warning::

            Since this method directly relies on :meth:`.setup_hook` completing, using it in :meth:`.setup_hook` or in any
            call :meth:`.setup_hook` is waiting for execution to complete, will completely deadlock the Client.
        """
        await self._ready_event.wait()

    async def wait_for(self, event: str, *, timeout: float | None = None, predicate: WaitPredicateT | None = None) -> Any:
        """|coro|

        Method which waits for any known dispatched event and returns the payload associated with the event.

        This method can be used with a predicate check to determine whether the `wait_for` should stop listening and return
        the event payload.

        Parameters
        ----------
        event: str
            The name of the event/listener to wait for. This should be the name of the event minus the `event_` prefix.

            E.g. `chat_message`
        timeout: float | None
            An optional `float` to pass that this method will wait for a valid event. If `None` `wait_for` won't timeout.
            Defaults to `None`.

            If this method does timeout, the `TimeoutError` will be raised and propagated back.
        predicate: WaitPredicateT
            An optional `coroutine` to use as a check to determine whether this method should stop listening and return the
            event payload. This coroutine should always return a bool.

            The predicate function should take in the same payload as the event you are waiting for.


        Examples
        --------

        .. code:: python3

            async def predicate(payload: twitchio.ChatMessage) -> bool:
                # Only wait for a message sent by "chillymosh"
                return payload.chatter.name == "chillymosh"

            payload: twitchio.ChatMessage = await client.wait_for("chat_message", predicate=predicate)
            print(f"Chillymosh said: {payload.text}")


        Raises
        ------
        TimeoutError
            Raised when waiting for an event that meets the requirements and passes the predicate check exceeds the timeout.

        Returns
        -------
        Any
            The payload associated with the event being listened to.
        """
        name: str = "event_" + event.lower()

        set_ = self._wait_fors[name]
        waiter: EventWaiter = EventWaiter(event=name, predicate=predicate, timeout=timeout)

        waiter._set = set_
        set_.add(waiter)

        return await waiter.wait()

    async def add_token(self, token: str, refresh: str) -> ValidateTokenPayload:
        """|coro|

        Adds a token and refresh-token pair to the client to be automatically managed.

        After successfully adding a token to the client, the token will be automatically revalidated and refreshed both when
        required and periodically.

        This method is automatically called in the :func:`~twitchio.events.event_oauth_authorized` event,
        when a token is authorized by a user via the built-in OAuth adapter.

        You can override the :func:`~twitchio.events.event_oauth_authorized` or this method to
        implement custom functionality such as storing the token in a database.

        Storing your tokens safely is highly recommended and required to prevent users needing to reauthorize
        your application after restarts.

        .. note::

            Both `token` and `refresh` are required parameters.

        Parameters
        ----------
        token: str
            The User-Access token to add.
        refresh: str
            The refresh token associated with the User-Access token to add.

        Examples
        --------

        .. code:: python3

            class Client(twitchio.Client):

                async def add_token(self, token: str, refresh: str) -> None:
                    # Code to add token to database here...
                    ...

                    # Adds the token to the client...
                    await super().add_token(token, refresh)

        """
        return await self._http.add_token(token, refresh)

    async def remove_token(self, user_id: str, /) -> TokenMappingData | None:
        """|coro|

        Removes a token for the specified `user-ID` from the `Client`.

        Removing a token will ensure the client stops managing the token.

        This method has been made `async` for convenience when overriding the default functionality.

        You can override this method to implement custom logic, such as removing a token from your database.

        Parameters
        ----------
        user_id: str
            The user-ID for the token to remove from the client. This argument is `positional-only`.

        Returns
        -------
        TokenMappingData
            The token data assoicated with the user-id that was successfully removed.
        None
            The user-id was not managed by the client.
        """
        return self._http.remove_token(user_id)

    async def load_tokens(self, path: str | None = None, /) -> None:
        """|coro|

        Method used to load tokens when the :class:`~Client` starts.

        .. note::

            This method is called by the client during :meth:`~.login` but **before**
            :meth:`~.setup_hook` when the ``load_tokens`` keyword-argument
            is ``True`` in either, :meth:`.run`, :meth:`.start` or :meth:`.login` (Default).

        You can override this method to implement your own token loading logic into the client, such as from a database.

        By default this method loads tokens from a file named `".tio.tokens.json"` if it is present;
        always present if you use the default method of saving tokens.

        **However**, it is preferred you would override this function to load your tokens from a database,
        as this has far less chance of being corrupted, damaged or lost.

        Parameters
        ----------
        path: str | None
            The path to load tokens from, if this is `None` and the method has not been overriden, this will default to
            `.tio.tokens.json`. Defaults to `None`.

        Examples
        --------

        .. code:: python3

            class Client(twitchio.Client):

                async def load_tokens(self, path: str | None = None) -> None:
                    # Code to fetch all tokens from the database here...
                    ...

                    for row in tokens:
                        await self.add_token(row["token"], row["refresh"])

        """
        await self._http.load_tokens(name=path)

    async def save_tokens(self, path: str | None = None, /) -> None:
        """|coro|

        Method which saves all the added OAuth tokens currently managed by this Client.

        .. note::

            This method is called by the client when it is gracefully closed and the ``save_tokens`` keyword-argument
            is ``True`` in either, :meth:`.run`, :meth:`.start` or :meth:`.login` (Default).

        .. note::

            By default this method saves to a JSON file named `".tio.tokens.json"`.

        You can override this method to implement your own custom logic, such as saving tokens to a database, however
        it is preferred to use :meth:`~.add_token` to ensure the tokens are handled as they are added.

        Parameters
        ----------
        path: str | None
            The path of the file to save to. Defaults to `.tio.tokens.json`.
        """
        await self._http.save(path)

    def add_listener(self, listener: Callable[..., Coroutine[Any, Any, None]], *, event: str | None = None) -> None:
        """Method to add an event listener to the client.

        See: :meth:`.listen` for more information on event listeners and for a decorator version of this function.

        Parameters
        ----------
        listener: Callable[..., Coroutine[Any, Any, None]]
            The coroutine to assign as the callback for the listener.
        event: str | None
            An optional :class:`str` which indicates which event to listen to. This should include the ``event_`` prefix.
            Defaults to ``None`` which uses the coroutine function name passed instead.

        Raises
        ------
        ValueError
            The ``event`` string passed should start with ``event_``.
        ValueError
            The ``event`` string passed must not == ``event_``.
        TypeError
            The listener callback must be a coroutine function.
        """
        name: str = event or listener.__name__

        if not name.startswith("event_"):
            raise ValueError('Listener and event names must start with "event_".')

        if name == "event_":
            raise ValueError('Listener and event names cannot be named "event_".')

        if not asyncio.iscoroutinefunction(listener):
            raise TypeError("Listeners and Events must be coroutines.")

        self._listeners[name].add(listener)

    def remove_listener(
        self,
        listener: Callable[..., Coroutine[Any, Any, None]],
    ) -> Callable[..., Coroutine[Any, Any, None]] | None:
        """Method to remove a currently registered listener from the client.

        Parameters
        ----------
        listener: Callable[..., Coroutine[Any, Any, None]]
            The coroutine wrapped with :meth:`.listen` or added via :meth:`.add_listener` to remove as a listener.

        Returns
        -------
        Callable[..., Coroutine[Any, Any, None]]
            If a listener was removed, the coroutine function will be returned.
        None
            Returns ``None`` when no listener was removed.
        """
        for listeners in self._listeners.values():
            if listener in listeners:
                listeners.remove(listener)
                return listener

    def listen(self, name: str | None = None) -> Any:
        """|deco|

        A decorator that adds a coroutine as an event listener.

        Listeners listen for dispatched events on the :class:`.Client` or :class:`~.commands.Bot` and can come from multiple
        sources, such as internally, or via EventSub. Unlike the overridable events built into bot
        :class:`~Client` and :class:`~.commands.Bot`, listeners do not change the default functionality of the event,
        and can be used as many times as required.

        By default, listeners use the name of the function wrapped for the event name. This can be changed by passing the
        name parameter.

        For a list of events and their documentation, see: :ref:`Events Reference <Event Ref>`.

        For adding listeners to components, see: :meth:`~.commands.Component.listener`

        Examples
        --------

        .. code:: python3

            @bot.listen()
            async def event_message(message: twitchio.ChatMessage) -> None:
                ...

            # You can have multiple of the same event...
            @bot.listen("event_message")
            async def event_message_two(message: twitchio.ChatMessage) -> None:
                ...

        Parameters
        ----------
        name: str
            The name of the event to listen to, E.g. ``"event_message"`` or simply ``"message"``.
        """

        def wrapper(func: Callable[..., Coroutine[Any, Any, None]]) -> Callable[..., Coroutine[Any, Any, None]]:
            name_ = name or func.__name__
            qual = f"event_{name_.removeprefix('event_')}"

            self.add_listener(func, event=qual)

            return func

        return wrapper

    def create_partialuser(self, user_id: str | int, user_login: str | None = None) -> PartialUser:
        """Helper method used to create :class:`twitchio.PartialUser` objects.

        :class:`~twitchio.PartialUser`'s are used to make HTTP requests regarding users on Twitch.

        .. versionadded:: 3.0.0

            This has been renamed from `create_user` to `create_partialuser`.

        Parameters
        ----------
        user_id: str | int
            ID of the user you wish to create a :class:`~twitchio.PartialUser` for.
        user_login: str | None
            Login name of the user you wish to create a :class:`~twitchio.PartialUser` for, if available.

        Returns
        -------
        PartialUser
            A :class:`~twitchio.PartialUser` object.
        """
        return PartialUser(user_id, user_login, http=self._http)

    async def fetch_badges(self, *, token_for: str | PartialUser | None = None) -> list[ChatBadge]:
        """|coro|

        Fetches Twitch's list of global chat badges, which users may use in any channel's chat room.

        Parameters
        ----------
        token_for: str | PartialUser | None
            |token_for|

        To fetch a specific broadcaster's chat badges, see: :meth:`~twitchio.PartialUser.fetch_badges`

        Returns
        --------
        list[twitchio.ChatBadge]
            A list of :class:`~twitchio.ChatBadge` objects
        """

        data = await self._http.get_global_chat_badges(token_for=token_for)
        return [ChatBadge(x, http=self._http) for x in data["data"]]

    async def fetch_emote_sets(
        self, emote_set_ids: list[str], *, token_for: str | PartialUser | None = None
    ) -> list[EmoteSet]:
        """|coro|

        Fetches emotes for one or more specified emote sets.

        .. note::

            An emote set groups emotes that have a similar context.
            For example, Twitch places all the subscriber emotes that a broadcaster uploads for their channel
            in the same emote set.

        Parameters
        ----------
        emote_set_ids: list[str]
            A list of the IDs that identifies the emote set to get. You may specify a maximum of **25** IDs.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        -------
        list[:class:`~twitchio.EmoteSet`]
            A list of :class:`~twitchio.EmoteSet` objects.

        Raises
        ------
        ValueError
            You can only specify a maximum of **25** emote set IDs.
        """

        if len(emote_set_ids) > 25:
            raise ValueError("You can only specify a maximum of 25 emote set IDs.")

        data = await self._http.get_emote_sets(emote_set_ids=emote_set_ids, token_for=token_for)
        template: str = data["template"]

        return [EmoteSet(d, template=template, http=self._http) for d in data["data"]]

    async def fetch_chatters_color(
        self,
        user_ids: list[str | int],
        *,
        token_for: str | PartialUser | None = None,
    ) -> list[ChatterColor]:
        """|coro|

        Fetches the color of a chatter.

        .. versionchanged:: 3.0

            Removed the `token` parameter. Added the `token_for` parameter.

        Parameters
        -----------
        user_ids: list[str | int]
            A list of user ids to fetch the colours for.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        list[:class:`~twitchio.ChatterColor`]
            A list of :class:`~twitchio.ChatterColor` objects associated with the passed user IDs.
        """
        if len(user_ids) > 100:
            raise ValueError("Maximum of 100 user_ids")

        data = await self._http.get_user_chat_color(user_ids, token_for)
        return [ChatterColor(d, http=self._http) for d in data["data"] if data]

    async def fetch_channels(
        self,
        broadcaster_ids: list[str | int],
        *,
        token_for: str | PartialUser | None = None,
    ) -> list[ChannelInfo]:
        """|coro|

        Retrieve channel information from the API.

        Parameters
        ----------
        broadcaster_ids: list[str | int]
            A list of channel IDs to request from API.
            You may specify a maximum of **100** IDs.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        list[:class:`~twitchio.ChannelInfo`]
            A list of :class:`~twitchio.ChannelInfo` objects.
        """
        if len(broadcaster_ids) > 100:
            raise ValueError("Maximum of 100 broadcaster_ids")

        data = await self._http.get_channel_info(broadcaster_ids, token_for)
        return [ChannelInfo(d, http=self._http) for d in data["data"]]

    async def fetch_channel(
        self,
        broadcaster_id: str | int,
        *,
        token_for: str | PartialUser | None = None,
    ) -> ChannelInfo | None:
        """|coro|

        Retrieve channel information from the API for a single broadcaster.

        Parameters
        ----------
        broadcaster_id: str | int
            The ID of the channel you wish to receive information for.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        :class:`~twitchio.ChannelInfo`
            Channel information as a :class:`~twitchio.ChannelInfo` object.
        None
            No channel could be found.
        """

        data = await self._http.get_channel_info([broadcaster_id], token_for)
        try:
            return ChannelInfo(data["data"][0], http=self._http)
        except IndexError:
            return None

    async def fetch_cheermotes(
        self,
        *,
        broadcaster_id: int | str | None = None,
        token_for: str | PartialUser | None = None,
    ) -> list[Cheermote]:
        """|coro|

        Fetches a list of Cheermotes that users can use to cheer Bits in any Bits-enabled channel's chat room.

        Cheermotes are animated emotes that viewers can assign Bits to.
        If a `broadcaster_id` is not specified then only global cheermotes will be returned.

        If the broadcaster uploaded Cheermotes, the type attribute will be set to `channel_custom`.

        Parameters
        -----------
        broadcaster_id: str | int | None
            The ID of the broadcaster whose custom Cheermotes you want to fetch.
            If not provided or `None` then you will fetch global Cheermotes. Defaults to `None`
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        list[:class:`~twitchio.Cheermote`]
            A list of :class:`~twitchio.Cheermote` objects.
        """
        data = await self._http.get_cheermotes(str(broadcaster_id) if broadcaster_id else None, token_for)
        return [Cheermote(d, http=self._http) for d in data["data"]]

    async def fetch_classifications(
        self, locale: str = "en-US", *, token_for: str | PartialUser | None = None
    ) -> list[ContentClassificationLabel]:
        # TODO: Docs need more info...
        """|coro|

        Fetches information about Twitch content classification labels.

        Parameters
        -----------
        locale: str
            Locale for the Content Classification Labels.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        list[:class:`~twitchio.ContentClassificationLabel`]
            A list of :class:`~twitchio.ContentClassificationLabel` objects.
        """
        data = await self._http.get_content_classification_labels(locale, token_for)
        return [ContentClassificationLabel(d) for d in data["data"]]

    def fetch_clips(
        self,
        *,
        game_id: str | None = None,
        clip_ids: list[str] | None = None,
        started_at: datetime.datetime | None = None,
        ended_at: datetime.datetime | None = None,
        featured: bool | None = None,
        token_for: str | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Clip]:
        """|aiter|

        Fetches clips by the provided clip ids or game id.

        Parameters
        -----------
        game_id: list[str | int] | None
            A game id to fetch clips from.
        clip_ids: list[str] | None
            A list of specific clip IDs to fetch.
            The Maximum amount you can request is **100**.
        started_at: datetime.datetime
            The start date used to filter clips.
        ended_at: datetime.datetime
            The end date used to filter clips. If not specified, the time window is the start date plus one week.
        featured: bool | None
            When this parameter is `True`, this method returns only clips that are featured.
            When this parameter is `False`, this method returns only clips that are not featured.

            Othwerise if this parameter is not provided or `None`, all clips will be returned. Defaults to `None`.
        token_for: str | PartialUser | None
            |token_for|
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        --------
        HTTPAsyncIterator[:class:`~twitchio.Clip`]

        Raises
        ------
        ValueError
            Only one of `game_id` or `clip_ids` can be provided.
        ValueError
            You must provide either a `game_id` *or* `clip_ids`.
        """

        provided: int = len([v for v in (game_id, clip_ids) if v])
        if provided > 1:
            raise ValueError("Only one of 'game_id' or 'clip_ids' can be provided.")
        elif provided == 0:
            raise ValueError("One of 'game_id' or 'clip_ids' must be provided.")

        first = max(1, min(100, first))

        return self._http.get_clips(
            game_id=game_id,
            clip_ids=clip_ids,
            first=first,
            started_at=started_at,
            ended_at=ended_at,
            is_featured=featured,
            max_results=max_results,
            token_for=token_for,
        )

    def fetch_extension_transactions(
        self,
        extension_id: str,
        *,
        ids: list[str] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[ExtensionTransaction]:
        # TODO: Check docs?...
        """|aiter|

        Fetches global emotes from the Twitch API.

        .. note::

            The ID in the `extension_id` parameter must match the Client-ID provided to this :class:`~Client`.

        Parameters
        -----------
        extension_id: str
            The ID of the extension whose list of transactions you want to fetch.
        ids: list[str] | None
            A transaction ID used to filter the list of transactions.
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        --------
        HTTPAsyncIterator[:class:`~twitchio.ExtensionTransaction`]
        """

        first = max(1, min(100, first))

        if ids and len(ids) > 100:
            raise ValueError("You can only provide a mximum of 100 IDs")

        return self._http.get_extension_transactions(
            extension_id=extension_id,
            ids=ids,
            first=first,
            max_results=max_results,
        )

    async def fetch_extensions(self, *, token_for: str | PartialUser) -> list[Extension]:
        """|coro|

        Fetch a list of all extensions (both active and inactive) that the broadcaster has installed.

        The user ID in the access token identifies the broadcaster.

        .. note::

            Requires a user access token that includes the `user:read:broadcast` or `user:edit:broadcast` scope.
            To include inactive extensions, you must include the `user:edit:broadcast` scope.

        Parameters
        ----------
        token_for: str | PartialUser
            The User ID, or PartialUser, that will be used to find an appropriate managed user token for this request.
            The token must inlcude the `user:read:broadcast` or `user:edit:broadcast` scope.

            See: :meth:`~.add_token` to add managed tokens to the client.
            To include inactive extensions, you must include the `user:edit:broadcast` scope.

        Returns
        -------
        list[:class:`~twitchio.UserExtension`]
            List of :class:`~twitchio.UserExtension` objects.
        """
        data = await self._http.get_user_extensions(token_for=token_for)
        return [Extension(d) for d in data["data"]]

    async def update_extensions(
        self, *, user_extensions: ActiveExtensions, token_for: str | PartialUser
    ) -> ActiveExtensions:
        """|coro|

        Update an installed extension's information for a specific broadcaster.

        You can update the extension's activation `state`, `ID`, and `version number`.
        The User-ID passed to `token_for` identifies the broadcaster whose extensions you are updating.

        .. note::

            The best way to change an installed extension's configuration is to use
            :meth:`~twitchio.PartialUser.fetch_active_extensions` to fetch the extension.

            You can then edit the approperiate extension within the `ActiveExtensions` model and pass it to this method.

        .. note::

            Requires a user access token that includes the `user:edit:broadcast` scope.
            See: :meth:`~.add_token` to add managed tokens to the client.

        Parameters
        ----------
        token_for: str | PartialUser
            The User ID, or PartialUser, that will be used to find an appropriate managed user token for this request.
            The token must inlcude the `user:edit:broadcast` scope.

            See: :meth:`~.add_token` to add managed tokens to the client.

        Returns
        -------
        ActiveExtensions
            The :class:`~twitchio.ActiveExtensions` object.
        """
        data = await self._http.put_user_extensions(user_extensions=user_extensions, token_for=token_for)
        return ActiveExtensions(data["data"])

    async def fetch_emotes(self, *, token_for: str | PartialUser | None = None) -> list[GlobalEmote]:
        """|coro|

        Fetches global emotes from the Twitch API.

        .. note::
            If you wish to fetch a specific broadcaster's chat emotes use :meth:`~twitchio.PartialUser.fetch_channel_emotes`.

        Parameters
        ----------
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        list[:class:`twitchio.GlobalEmote`]
            A list of :class:`~twitchio.GlobalEmote` objects.
        """
        data = await self._http.get_global_emotes(token_for)
        template: str = data["template"]

        return [GlobalEmote(d, template=template, http=self._http) for d in data["data"]]

    def fetch_streams(
        self,
        *,
        user_ids: list[int | str] | None = None,
        game_ids: list[int | str] | None = None,
        user_logins: list[int | str] | None = None,
        languages: list[str] | None = None,
        type: Literal["all", "live"] = "all",
        token_for: str | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Stream]:
        """|aiter|

        Fetches streams from the Twitch API.

        Parameters
        -----------
        user_ids: list[int | str] | None
            An optional list of User-IDs to fetch live stream information for.
        game_ids: list[int | str] | None
            An optional list of Game-IDs to fetch live streams for.
        user_logins: list[str] | None
            An optional list of User-Logins to fetch live stream information for.
        languages: list[str] | None
            A language code used to filter the list of streams. Returns only streams that broadcast in the specified language.
            Specify the language using an ISO 639-1 two-letter language code or other if the broadcast uses a language not in the list of `supported stream languages <https://help.twitch.tv/s/article/languages-on-twitch#streamlang>`_.
            You may specify a maximum of `100` language codes.
        type: Literal["all", "live"]
            One of `"all"` or `"live"`. Defaults to `"all"`. Specifies what type of stream to fetch.

            .. important::
                Twitch deprecated filtering streams by type. `all` and `live` both return the same data.
                This is being kept in the library in case of future additions.

        token_for: str | PartialUser | None
            |token_for|
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        --------
        HTTPAsyncIterator[:class:`twitchio.Stream`]
        """

        first = max(1, min(100, first))

        return self._http.get_streams(
            first=first,
            game_ids=game_ids,
            user_ids=user_ids,
            user_logins=user_logins,
            languages=languages,
            type=type,
            token_for=token_for,
            max_results=max_results,
        )

    async def fetch_team(
        self,
        *,
        team_name: str | None = None,
        team_id: str | None = None,
        token_for: str | PartialUser | None = None,
    ) -> Team:
        """|coro|

        Fetches information about a specific Twitch team.

        You must provide one of either `team_name` or `team_id`.

        Parameters
        -----------
        team_name: str | None
            The team name.
        team_id: str | None
            The team id.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        Team
            The :class:`twitchio.Team` object.

        Raises
        ------
        ValueError
            You can only provide either `team_name` or `team_id`, not both.
        """

        if team_name and team_id:
            raise ValueError("Only one of 'team_name' or 'team_id' should be provided, not both.")

        data = await self._http.get_teams(
            team_name=team_name,
            team_id=team_id,
            token_for=token_for,
        )

        return Team(data["data"][0], http=self._http)

    def fetch_top_games(
        self,
        *,
        token_for: str | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Game]:
        # TODO: Docs??? More info...
        """|aiter|

        Fetches information about the current top games on Twitch.

        Parameters
        -----------
        token_for: str | PartialUser | None
            |token_for|
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        --------
        HTTPAsyncIterator[:class:`twitchio.Game`]
        """

        first = max(1, min(100, first))

        return self._http.get_top_games(first=first, token_for=token_for, max_results=max_results)

    async def fetch_games(
        self,
        *,
        names: list[str] | None = None,
        ids: list[str] | None = None,
        igdb_ids: list[str] | None = None,
        token_for: str | PartialUser | None = None,
    ) -> list[Game]:
        # TODO: Docs??? More info...
        """|coro|

        Fetches information about multiple games on Twitch.

        Parameters
        -----------
        names: list[str] | None
            A list of game names to use to fetch information about. Defaults to `None`.
        ids: list[str] | None
            A list of game ids to use to fetch information about. Defaults to `None`.
        igdb_ids: list[str] | None
            A list of `igdb` ids to use to fetch information about. Defaults to `None`.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        --------
        list[:class:`twitchio.Game`]
            A list of :class:`twitchio.Game` objects.
        """

        data = await self._http.get_games(
            names=names,
            ids=ids,
            igdb_ids=igdb_ids,
            token_for=token_for,
        )

        return [Game(d, http=self._http) for d in data["data"]]

    async def fetch_game(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        igdb_id: str | None = None,
        token_for: str | PartialUser | None = None,
    ) -> Game | None:
        """|coro|

        Fetch a :class:`~twitchio.Game` object with the provided `name`, `id`, or `igdb_id`.

        One of `name`, `id`, or `igdb_id` must be provided.
        If more than one is provided or no parameters are provided, a `ValueError` will be raised.

        If no game is found, `None` will be returned.

        .. note::

            See: :meth:`~.fetch_games` to fetch multiple games at once.

            See: :meth:`~.fetch_top_games` to fetch the top games currently being streamed.

        Parameters
        ----------
        name: str | None
            The name of the game to fetch.
        id: str | None
            The id of the game to fetch.
        igdb_id: str | None
            The igdb id of the game to fetch.
        token_for: str | PartialUser | None
            |token_for|

        Returns
        -------
        Game | None
            The :class:`twitchio.Game` object if found, otherwise `None`.

        Raises
        ------
        ValueError
            Only one of the `name`, `id`, or `igdb_id` parameters can be provided.
        ValueError
            One of the `name`, `id`, or `igdb_id` parameters must be provided.
        """
        provided: int = len([v for v in (name, id, igdb_id) if v])
        if provided > 1:
            raise ValueError("Only one of 'name', 'id', or 'igdb_id' can be provided.")
        elif provided == 0:
            raise ValueError("One of 'name', 'id', or 'igdb_id' must be provided.")

        names: list[str] | None = [name] if name else None
        id_: list[str] | None = [id] if id else None
        igdb_ids: list[str] | None = [igdb_id] if igdb_id else None

        data = await self._http.get_games(names=names, ids=id_, igdb_ids=igdb_ids, token_for=token_for)
        return Game(data["data"][0], http=self._http) if data["data"] else None

    async def fetch_users(
        self,
        *,
        ids: list[str | int] | None = None,
        logins: list[str] | None = None,
        token_for: str | PartialUser | None = None,
    ) -> list[User]:
        """|coro|

        Fetch information about one or more users.

        .. note::

            You may look up users using their user ID, login name, or both but the sum total
            of the number of users you may look up is `100`.

            For example, you may specify `50` IDs and `50` names or `100` IDs or names,
            but you cannot specify `100` IDs and `100` names.

            If you don't specify IDs or login names but provide the `token_for` parameter,
            the request returns information about the user associated with the access token.

            To include the user's verified email address in the response,
            you must have a user access token that includes the `user:read:email` scope.

        Parameters
        ----------
        ids: list[str | int] | None
            The ids of the users to fetch information about.
        logins: list[str] | None
            The login names of the users to fetch information about.
        token_for: str | PartialUser | None
            |token_for|

            If this parameter is provided, the token must have the `user:read:email` scope
            in order to request the user's verified email address.

        Returns
        -------
        list[:class:`twitchio.User`]
            A list of :class:`twitchio.User` objects.

        Raises
        ------
        ValueError
            The combined number of 'ids' and 'logins' must not exceed `100` elements.
        """

        if (len(ids or []) + len(logins or [])) > 100:
            raise ValueError("The combined number of 'ids' and 'logins' must not exceed 100 elements.")

        data = await self._http.get_users(ids=ids, logins=logins, token_for=token_for)
        return [User(d, http=self._http) for d in data["data"]]

    async def fetch_user(
        self,
        *,
        id: str | int | None = None,
        login: str | None = None,
        token_for: str | PartialUser | None = None,
    ) -> User | None:
        """|coro|

        Fetch information about one user.

        .. note::

            You may look up a specific user using their user ID or login name.

            If you don't specify an ID or login name but provide the `token_for` parameter,
            the request returns information about the user associated with the access token.

            To include the user's verified email address in the response,
            you must have a user access token that includes the `user:read:email` scope.

        Parameters
        ----------
        id: str | int | None
            The id of the user to fetch information about.
        login: str | None
            The login name of the user to fetch information about.
        token_for: str | PartialUser | None
            |token_for|

            If this parameter is provided, the token must have the `user:read:email` scope
            in order to request the user's verified email address.

        Returns
        -------
        :class:`twitchio.User`
            A :class:`twitchio.User` object.

        Raises
        ------
        ValueError
            Please provide only one of `id` or `login`.
        """

        if id is not None and login is not None:
            raise ValueError("Please provide only one of `id` or `login`.")

        data = await self._http.get_users(ids=id, logins=login, token_for=token_for)
        return User(data["data"][0], http=self._http) if data["data"] else None

    def search_categories(
        self,
        query: str,
        *,
        token_for: str | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Game]:
        """|aiter|

        Searches Twitch categories via the API.

        Parameters
        -----------
        query: str
            The query to search for.
        token_for: str | PartialUser | None
            |token_for|
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        --------
        HTTPAsyncIterator[:class:`twitchio.Game`]
        """

        first = max(1, min(100, first))

        return self._http.get_search_categories(
            query=query,
            first=first,
            max_results=max_results,
            token_for=token_for,
        )

    def search_channels(
        self,
        query: str,
        *,
        live: bool = False,
        token_for: str | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[SearchChannel]:
        """|aiter|

        Searches Twitch channels that match the specified query and have streamed content within the past `6` months.

        .. note::

            If the `live` parameter is set to `False` (default), the query will look to match broadcaster login names.
            If the `live` parameter is set to `True`, the query will match on the broadcaster login names and category names.

            To match, the beginning of the broadcaster's name or category must match the query string.

            The comparison is case insensitive. If the query string is `angel_of_death`,
            it will matche all names that begin with `angel_of_death`.

            However, if the query string is a phrase like `angel of death`, it will match
            to names starting with `angelofdeath` *or* names starting with `angel_of_death`.

        Parameters
        -----------
        query: str
            The query to search for.
        live: bool
            Whether to return live channels only.
            Defaults to `False`.
        token_for: str | PartialUser  | None
            |token_for|
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        --------
        HTTPAsyncIterator[:class:`twitchio.SearchChannel`]
        """

        first = max(1, min(100, first))

        return self._http.get_search_channels(
            query=query,
            first=first,
            live=live,
            max_results=max_results,
            token_for=token_for,
        )

    def fetch_videos(
        self,
        *,
        ids: list[str | int] | None = None,
        user_id: str | int | PartialUser | None = None,
        game_id: str | int | None = None,
        language: str | None = None,
        period: Literal["all", "day", "month", "week"] = "all",
        sort: Literal["time", "trending", "views"] = "time",
        type: Literal["all", "archive", "highlight", "upload"] = "all",
        first: int = 20,
        max_results: int | None = None,
        token_for: str | PartialUser | None = None,
    ) -> HTTPAsyncIterator[Video]:
        """|aiter|

        Fetch a list of :class:`~twitchio.Video` objects with the provided `ids`, `user_id` or `game_id`.

        One of `ids`, `user_id` or `game_id` must be provided.
        If more than one is provided or no parameters are provided, a `ValueError` will be raised.

        Parameters
        ----------
        ids: list[str | int] | None
            A list of video IDs to fetch.
        user_id: str | int | PartialUser | None
            The ID of the user whose list of videos you want to fetch.
        game_id: str | int | None
            The igdb id of the game to fetch.
        language: str | None
            A filter used to filter the list of videos by the language that the video owner broadcasts in.

            For example, to get videos that were broadcast in German, set this parameter to the ISO 639-1 two-letter code for German (i.e., DE).

            For a list of supported languages, see `Supported Stream Language <https://help.twitch.tv/s/article/languages-on-twitch#streamlang>`_. If the language is not supported, use `other`.

            .. note::

                Specify this parameter only if you specify the game_id query parameter.

        period: Literal["all", "day", "month", "week"]
            A filter used to filter the list of videos by when they were published. For example, videos published in the last week.
            Possible values are: `all`, `day`, `month`, `week`.

            The default is `all`, which returns videos published in all periods.

            .. note::

                Specify this parameter only if you specify the game_id or user_id query parameter.

        sort: Literal["time", "trending", "views"]
            The order to sort the returned videos in.

            +------------+---------------------------------------------------------------+
            | Sort Key   | Description                                                   |
            +============+===============================================================+
            | time       | Sort the results in descending order by when they were        |
            |            | created (i.e., latest video first).                           |
            +------------+---------------------------------------------------------------+
            | trending   | Sort the results in descending order by biggest gains in      |
            |            | viewership (i.e., highest trending video first).              |
            +------------+---------------------------------------------------------------+
            | views      | Sort the results in descending order by most views (i.e.,     |
            |            | highest number of views first).                               |
            +------------+---------------------------------------------------------------+

            The default is `time`.

            .. note::

                Specify this parameter only if you specify the game_id or user_id query parameter.

        type: Literal["all", "archive", "highlight", "upload"]
            A filter used to filter the list of videos by the video's type.

            +-----------+-------------------------------------------------------------+
            | Type      | Description                                                 |
            +===========+=============================================================+
            | all       | Include all video types.                                    |
            +-----------+-------------------------------------------------------------+
            | archive   | On-demand videos (VODs) of past streams.                    |
            +-----------+-------------------------------------------------------------+
            | highlight | Highlight reels of past streams.                            |
            +-----------+-------------------------------------------------------------+
            | upload    | External videos that the broadcaster uploaded using the     |
            |           | Video Producer.                                             |
            +-----------+-------------------------------------------------------------+

            The default is `all`, which returns all video types.

            .. note::

                Specify this parameter only if you specify the game_id or user_id query parameter.

        token_for: str | PartialUser | None
            |token_for|
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        -------
        HTTPAsyncIterator[:class:`twitchio.Video`]

        Raises
        ------
        ValueError
            Only one of the 'ids', 'user_id', or 'game_id' parameters can be provided.
        ValueError
            One of the 'ids', 'user_id', or 'game_id' parameters must be provided.
        """
        provided: int = len([v for v in (ids, game_id, user_id) if v])
        if provided > 1:
            raise ValueError("Only one of 'ids', 'user_id', or 'game_id' can be provided.")
        elif provided == 0:
            raise ValueError("One of 'name', 'id', or 'igdb_id' must be provided.")

        first = max(1, min(100, first))

        return self._http.get_videos(
            ids=ids,
            user_id=user_id,
            game_id=game_id,
            language=language,
            period=period,
            sort=sort,
            type=type,
            first=first,
            max_results=max_results,
            token_for=token_for,
        )

    async def delete_videos(self, *, ids: list[str | int], token_for: str | PartialUser) -> list[str]:
        """|coro|

        Deletes one or more videos for a specific broadcaster.

        .. note::

            You may delete past broadcasts, highlights, or uploads.

        .. note::
            This requires a user token with the scope `channel:manage:videos`.

        The limit is to delete `5` ids at a time. When more than 5 ids are provided,
        an attempt to delete them in chunks is made.

        If any of the videos fail to delete in a chunked request, no videos will be deleted in that chunk.

        Parameters
        ----------
        ids: list[str | int] | None
            A list of video IDs to delete.
        token_for: str | PartialUser
            The User ID, or PartialUser, that will be used to find an appropriate managed user token for this request.
            The token must inlcude the `channel:manage:videos` scope.

            See: :meth:`~.add_token` to add managed tokens to the client.

        Returns
        -------
        list[str]
            A list of Video IDs that were successfully deleted.
        """
        resp: list[str] = []

        for chunk in [ids[x : x + 5] for x in range(0, len(ids), 5)]:
            data = await self._http.delete_videos(ids=chunk, token_for=token_for)
            if data:
                resp.extend(data["data"])

        return resp

    def fetch_stream_markers(
        self,
        *,
        video_id: str,
        token_for: str | PartialUser,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[VideoMarkers]:
        """|aiter|

        Fetches markers from a specific user's most recent stream or from the specified VOD/video.

        A marker is an arbitrary point in a live stream that the broadcaster or editor has marked,
        so they can return to that spot later to create video highlights.

        .. important::

            See: :meth:`~twitchio.PartialUser.fetch_stream_markers` for a more streamlined version of this method.

        .. note::

            Requires a user access token that includes the `user:read:broadcast` *or* `channel:manage:broadcast` scope.

        Parameters
        ----------
        video_id: str
            A video on demand (VOD)/video ID. The request returns the markers from this VOD/video.
            The User ID provided to `token_for` must own the video or the user must be one of the broadcaster's editors.
        token_for: str | PartialUser
            The User ID, or PartialUser, that will be used to find an appropriate managed user token for this request.
            The token must inlcude the `user:read:broadcast` *or* `channel:manage:broadcast` scope

            See: :meth:`~.add_token` to add managed tokens to the client.
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        -------
        HTTPAsyncIterator[:class:`twitchio.VideoMarkers`]
        """
        first = max(1, min(100, first))
        return self._http.get_stream_markers(
            video_id=video_id,
            token_for=token_for,
            first=first,
            max_results=max_results,
        )

    def fetch_drop_entitlements(
        self,
        *,
        token_for: str | PartialUser | None = None,
        ids: list[str] | None = None,
        user_id: str | int | PartialUser | None = None,
        game_id: str | None = None,
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Entitlement]:
        # TODO: Docs??? More info in parameters?
        """|aiter|

        Fetches an organization's list of entitlements that have been granted to a `game`, a `user`, or `both`.

        .. note::

            Entitlements returned in the response body data are not guaranteed to be sorted by any field returned by the API.

            To retrieve `CLAIMED` or `FULFILLED` entitlements, use the `fulfillment_status` query parameter to filter results.
            To retrieve entitlements for a specific game, use the `game_id` query parameter to filter results.

        .. note::

            Requires an app access token or user access token. The Client-ID associated with the token must own the game.

        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | Access token type  | Parameter        | Description                                                                                                                                                          |
        +====================+==================+======================================================================================================================================================================+
        | App                | None             | If you don't specify request parameters, the request returns all entitlements that your organization owns.                                                           |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | App                | user_id          | The request returns all entitlements for any game that the organization granted to the specified user.                                                               |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | App                | user_id, game_id | The request returns all entitlements that the specified game granted to the specified user.                                                                          |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | App                | game_id          | The request returns all entitlements that the specified game granted to all entitled users.                                                                          |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | User               | None             | If you don't specify request parameters, the request returns all entitlements for any game that the organization granted to the user identified in the access token. |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | User               | user_id          | Invalid.                                                                                                                                                             |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | User               | user_id, game_id | Invalid.                                                                                                                                                             |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | User               | game_id          | The request returns all entitlements that the specified game granted to the user identified in the access token.                                                     |
        +--------------------+------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

        Parameters
        ----------
        token_for: str | PartialUser | None
            An optional User-ID that will be used to find an appropriate managed user token for this request.
            The Client-ID associated with the token must own the game.

            See: :meth:`~.add_token` to add managed tokens to the client.
            If this paramter is not provided or `None`, the default app token is used.
        ids: list[str] | None
            A list of entitlement ids that identifies the entitlements to fetch.
        user_id: str | int | PartialUser | None
            An optional User ID of the user that was granted entitlements.
        game_id: str | None
            An ID that identifies a game that offered entitlements.
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None
            The entitlement's fulfillment status. Used to filter the list to only those with the specified status.
            Possible values are: `CLAIMED` and `FULFILLED`.
        first: int
            The maximum number of items to return per page. Defaults to **20**.
            The maximum number of items per page is **100**.
        max_results: int | None
            The maximum number of total results to return. When this parameter is set to `None`, all results are returned.
            Defaults to `None`.

        Returns
        -------
        HTTPAsyncIterator[:class:`twitchio.Entitlement`]

        Raises
        ------
        ValueError
            You may only specifiy a maximum of `100` ids.
        """
        first = max(1, min(1000, first))

        if ids is not None and len(ids) > 100:
            raise ValueError("You may specifiy a maximum of 100 ids.")

        return self._http.get_drop_entitlements(
            token_for=token_for,
            ids=ids,
            user_id=user_id,
            game_id=game_id,
            fulfillment_status=fulfillment_status,
            max_results=max_results,
        )

    async def update_entitlements(
        self,
        *,
        ids: list[str] | None = None,
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None = None,
        token_for: str | PartialUser | None = None,
    ) -> list[EntitlementStatus]:
        """|coro|

        Updates a Drop entitlement's fulfillment status.

        .. note::

            Requires an app access token or user access token.
            The Client-ID associated with the token must own the game associated with this drop entitlment.

        +--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
        | Access token type  | Updated Data                                                                                                                                            |
        +====================+=========================================================================================================================================================+
        | App                | Updates all entitlements with benefits owned by the organization in the access token.                                                                   |
        +--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+
        | User               | Updates all entitlements owned by the user in the access win the access token and where the benefits are owned by the organization in the access token. |
        +--------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------+

        Parameters
        ----------
        ids: list[str] | None
            A list of IDs that identify the entitlements to update. You may specify a maximum of **100** IDs.
        fulfillment_status: Literal[""CLAIMED", "FULFILLED"] | None
            The fulfillment status to set the entitlements to.
            Possible values are: `CLAIMED` and `FULFILLED`.
        token_for: str | PartialUser | None
            An optional User ID that will be used to find an appropriate managed user token for this request.
            The Client-ID associated with the token must own the game associated with this drop entitlment.

            See: :meth:`~.add_token` to add managed tokens to the client.
            If this paramter is not provided or `None`, the default app token is used.

        Returns
        -------
        list[:class:`twitchio.EntitlementStatus`]
            A list of :class:`twitchio.EntitlementStatus` objects.

        Raises
        ------
        ValueError
            You may only specifiy a maximum of **100** ids.
        """
        if ids is not None and len(ids) > 100:
            raise ValueError("You may specifiy a maximum of 100 ids.")

        from .models.entitlements import EntitlementStatus

        data = await self._http.patch_drop_entitlements(ids=ids, fulfillment_status=fulfillment_status, token_for=token_for)
        return [EntitlementStatus(d) for d in data["data"]]

    async def subscribe_websocket(
        self,
        payload: SubscriptionPayload,
        *,
        as_bot: bool | None = None,
        token_for: str | PartialUser | None = None,
        socket_id: str | None = None,
    ) -> SubscriptionResponse | None:
        # TODO: Complete docs...
        """|coro|

        Subscribe to an EventSub Event via Websockets.

        Parameters
        ----------
        payload: :class:`twitchio.eventsub.SubscriptionPayload`
            The payload which should include the required conditions to subscribe to.
        as_bot: bool
            Whether to subscribe to this event using the user token associated with the provided
            :attr:`Client.bot_id`. If this is set to `True` and `bot_id` has not been set, this method will
            raise `ValueError`. Defaults to `False` on :class:`Client` but will default to `True` on
            :class:`~twitchio.ext.commands.Bot`
        token_for: str | PartialUser | None
            An optional User ID, or PartialUser, that will be used to find an appropriate managed user token for this request.

            If `as_bot` is `True`, this is always the token associated with the
            :attr:`~.bot_id` account. Defaults to `None`.

            See: :meth:`~.add_token` to add managed tokens to the client.
            If this paramter is not provided or `None`, the default app token is used.
        socket_id: str | None
            An optional `str` corresponding to an exisiting and connected websocket session, to use for this subscription.
            You usually do not need to pass this parameter as TwitchIO delegates subscriptions to websockets as needed.
            Defaults to `None`.

        Returns
        -------
        SubscriptionResponse

        Raises
        ------
        ValueError
            One of the provided parameters is incorrect or incompatible.
        HTTPException
            An error was raised while making the subscription request to Twitch.
        """
        defaults = payload.default_auth

        if as_bot is None:
            as_bot = defaults.get("as_bot", False)
        if token_for is None:
            token_for = defaults.get("token_for", None)

        if as_bot and not self.bot_id:
            raise ValueError("Client is missing 'bot_id'. Provide a 'bot_id' in the Client constructor.")
        elif as_bot:
            token_for = self.bot_id

        if not token_for:
            raise ValueError("A valid User Access Token must be passed to subscribe to eventsub over websocket.")

        if isinstance(token_for, PartialUser):
            token_for = token_for.id

        sockets: dict[str, Websocket] = self._websockets[token_for]
        websocket: Websocket

        if socket_id:
            try:
                websocket = sockets[socket_id]
            except KeyError:
                raise KeyError(f"The websocket with ID '{socket_id}' does not exist.")

        elif not sockets:
            websocket = Websocket(client=self, token_for=token_for, http=self._http)
            await websocket.connect(fail_once=True)

            # session_id is guaranteed at this point.
            self._websockets[token_for] = {websocket.session_id: websocket}  # type: ignore

        else:
            sorted_: list[Websocket] = sorted(sockets.values(), key=lambda s: s.subscription_count)

            try:
                websocket = next(s for s in sorted_ if s.can_subscribe)
            except StopIteration:
                raise ValueError(
                    "No suitable websocket can be used to subscribe to this event. "
                    "You may have exahusted your 'toal_cost' allocation or max subscription count for this user token."
                )

        session_id: str | None = websocket.session_id
        if not session_id:
            # This really shouldn't ever happen that I am aware of.
            raise ValueError("Eventsub Websocket is missing 'session_id'.")

        type_ = SubscriptionType(payload.type)
        version: str = payload.version
        transport: SubscriptionCreateTransport = {"method": "websocket", "session_id": session_id}

        data: _SubscriptionData = {
            "type": type_,
            "version": version,
            "condition": payload.condition,
            "transport": transport,
            "token_for": token_for,
        }

        try:
            resp: SubscriptionResponse = await self._http.create_eventsub_subscription(**data)
        except HTTPException as e:
            if e.status == 409:
                logger.error(
                    "Disregarding HTTPException in subscribe: "
                    "A subscription already exists for the specified event type and condition combination: '%s' and '%s'",
                    payload.type,
                    str(payload.condition),
                )
                return

            raise e

        for sub in resp["data"]:
            identifier: str = sub["id"]
            websocket._subscriptions[identifier] = data

        return resp

    async def subscribe_webhook(
        self,
        payload: SubscriptionPayload,
        *,
        callback_url: str | None = None,
        eventsub_secret: str | None = None,
    ) -> SubscriptionResponse | None:
        # TODO: Complete docs...
        """|coro|

        Subscribe to an EventSub Event via Webhook.

        .. important::

            Usually you wouldn't use webhooks to subscribe to the
            :class:`~twitchio.eventsub.ChatMessageSubscription` subscription.

            Consider using :meth:`~.subscribe_websocket` for this subscription.

        Parameters
        ----------
        payload: :class:`~twitchio.eventsub.SubscriptionPayload`
            The payload which should include the required conditions to subscribe to.
        callback_url: str | None
            An optional url to use as the webhook `callback_url` for this subscription. If you are using one of the built-in
            web adapters, you should not need to set this. See: (web adapter docs link) for more info.
        eventsub_secret: str | None
            An optional `str` to use as the eventsub_secret, which is required by Twitch. If you are using one of the
            built-in web adapters, you should not need to set this. See: (web adapter docs link) for more info.

        Returns
        -------
        SubscriptionResponse

        Raises
        ------
        ValueError
            One of the provided parameters is incorrect or incompatible.
        HTTPException
            An error was raised while making the subscription request to Twitch.
        """
        if not self._adapter and not callback_url:
            raise ValueError(
                "Either a 'twitchio.web' Adapter or 'callback_url' should be provided for webhook based eventsub."
            )

        callback: str | None = callback_url or self._adapter.eventsub_url
        if not callback:
            raise ValueError(
                "A callback URL must be provided when subscribing to events via Webhook. "
                "Use 'twitchio.web' Adapter or provide a 'callback_url'."
            )

        secret: str | None = self._adapter._eventsub_secret or eventsub_secret
        if not secret:
            raise ValueError("An eventsub secret must be provided when subscribing to events via Webhook. ")

        if not 10 <= len(secret) <= 100:
            raise ValueError("The 'eventsub_secret' must be between 10 and 100 characters long.")

        type_ = SubscriptionType(payload.type)
        version: str = payload.version
        transport: SubscriptionCreateTransport = {"method": "webhook", "callback": callback, "secret": secret}

        data: _SubscriptionData = {
            "type": type_,
            "version": version,
            "condition": payload.condition,
            "transport": transport,
            "token_for": "",
        }

        try:
            resp: SubscriptionResponse = await self._http.create_eventsub_subscription(**data)
        except HTTPException as e:
            if e.status == 409:
                logger.warning(
                    "Disregarding HTTPException in subscribe: "
                    "A subscription already exists for the specified event type and condition combination: '%s' and '%s'",
                    payload.type,
                    str(payload.condition),
                )
                return

            raise e
        return resp

    async def fetch_eventsub_subscriptions(
        self,
        *,
        token_for: str | PartialUser | None = None,
        type: str | None = None,
        user_id: str | PartialUser | None = None,
        subscription_id: str | None = None,
        status: Literal[
            "enabled",
            "webhook_callback_verification_pending",
            "webhook_callback_verification_failed",
            "notification_failures_exceeded",
            "authorization_revoked",
            "moderator_removed",
            "user_removed",
            "version_removed",
            "beta_maintenance",
            "websocket_disconnected",
            "websocket_failed_ping_pong",
            "websocket_received_inbound_traffic",
            "websocket_connection_unused",
            "websocket_internal_error",
            "websocket_network_timeout",
            "websocket_network_error",
        ]
        | None = None,
        max_results: int | None = None,
    ) -> EventsubSubscriptions:
        """|coro|

        Fetches Eventsub Subscriptions for either webhook or websocket.

        .. note::
            type, status, user_id, and subscription_id are mutually exclusive and only one can be passed, otherwise ValueError will be raised.

            This endpoint returns disabled WebSocket subscriptions for a minimum of 1 minute as compared to webhooks which returns disabled subscriptions for a minimum of 10 days.

        Parameters
        -----------
        token_for: str | PartialUser | None
            By default, if this is ignored or set to None then the App Token is used. This is the case when you want to fetch webhook events.

            Provide a user ID here for when you want to fetch websocket events tied to a user.
        type: str | None
            Filter subscriptions by subscription type. e.g. ``channel.follow`` For a list of subscription types, see `Subscription Types <https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/#subscription-types>`_.
        user_id: str | PartialUser | None
            Filter subscriptions by user ID, or PartialUser. The response contains subscriptions where this ID matches a user ID that you specified in the Condition object when you created the subscription.
        subscription_id: str | None
            The specific subscription ID to fetch.
        status: str | None = None
            Filter subscriptions by its status. Possible values are:

            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | Status                                 | Description                                                                                                       |
            +========================================+===================================================================================================================+
            | enabled                                | The subscription is enabled.                                                                                      |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | webhook_callback_verification_pending  | The subscription is pending verification of the specified callback URL.                                           |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | webhook_callback_verification_failed   | The specified callback URL failed verification.                                                                   |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | notification_failures_exceeded         | The notification delivery failure rate was too high.                                                              |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | authorization_revoked                  | The authorization was revoked for one or more users specified in the Condition object.                            |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | moderator_removed                      | The moderator that authorized the subscription is no longer one of the broadcaster's moderators.                  |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | user_removed                           | One of the users specified in the Condition object was removed.                                                   |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | chat_user_banned                       | The user specified in the Condition object was banned from the broadcaster's chat.                                |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | version_removed                        | The subscription to subscription type and version is no longer supported.                                         |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | beta_maintenance                       | The subscription to the beta subscription type was removed due to maintenance.                                    |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_disconnected                 | The client closed the connection.                                                                                 |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_failed_ping_pong             | The client failed to respond to a ping message.                                                                   |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_received_inbound_traffic     | The client sent a non-pong message. Clients may only send pong messages (and only in response to a ping message). |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_connection_unused            | The client failed to subscribe to events within the required time.                                                |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_internal_error               | The Twitch WebSocket server experienced an unexpected error.                                                      |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_network_timeout              | The Twitch WebSocket server timed out writing the message to the client.                                          |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_network_error                | The Twitch WebSocket server experienced a network error writing the message to the client.                        |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
            | websocket_failed_to_reconnect          | The client failed to reconnect to the Twitch WebSocket server within the required time after a Reconnect Message. |
            +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+

        max_results: int | None
            The maximum number of total results to return. When this parameter is set to ``None``, all results are returned.
            Defaults to ``None``.

        Returns
        --------
        EventsubSubscriptions

        Raises
        ------
        ValueError
            Only one of 'status', 'user_id', 'subscription_id', or 'type' can be provided.
        """

        provided: int = len([v for v in (type, user_id, status, subscription_id) if v])
        if provided > 1:
            raise ValueError("Only one of 'status', 'user_id', 'subscription_id', or 'type' can be provided.")

        return await self._http.get_eventsub_subscription(
            type=type,
            max_results=max_results,
            token_for=token_for,
            subscription_id=subscription_id,
            user_id=user_id,
            status=status,
        )

    async def fetch_eventsub_subscription(
        self,
        subscription_id: str,
        *,
        token_for: str | PartialUser | None = None,
    ) -> EventsubSubscription | None:
        """|coro|

        Fetches a specific Eventsub Subscription for either webhook or websocket.

        .. note::
            This endpoint returns disabled WebSocket subscriptions for a minimum of 1 minute as compared to webhooks which returns disabled subscriptions for a minimum of 10 days.

        Parameters
        -----------
        subscription_id: str
            The specific subscription ID to fetch.
        token_for: str | PartialUser | None
            By default, if this is ignored or set to None then the App Token is used. This is the case when you want to fetch webhook events.

            Provide a user ID here for when you want to fetch websocket events tied to a user.

        Returns
        --------
        EventsubSubscription | None
        """

        data = await self._http.get_eventsub_subscription(
            type=None,
            max_results=None,
            token_for=token_for,
            subscription_id=subscription_id,
            user_id=None,
            status=None,
        )
        return await anext(data.subscriptions, None)

    async def delete_eventsub_subscription(self, id: str, *, token_for: str | PartialUser | None = None) -> None:
        """|coro|

        Delete an eventsub subscription.

        Parameters
        ----------
        id: str
            The ID of the eventsub subscription to delete.
        token_for: str | PartialUser | None
            Do not pass this if you wish to delete webhook subscriptions, which are what usually require deleting.

            For websocket subscriptions, provide the user ID, or PartialUser, associated with the subscription.

        """
        await self._http.delete_eventsub_subscription(id, token_for=token_for)

    def websocket_subscriptions(self) -> dict[str, WebsocketSubscriptionData]:
        """Method which returns a mapping of currently active EventSub subscriptions with a websocket transport on this
        client.

        The returned mapping contains the subscription ID as a key to a :class:`~twitchio.WebsocketSubscriptionData`
        value containing the relevant subscription data.

        Returns
        -------
        dict[:class:`str`, :class:`~twitchio.WebsocketSubscriptionData`]
            A mapping of currently active websocket subscriptions on the client.
        """
        ret: dict[str, WebsocketSubscriptionData] = {}

        for pair in self._websockets.values():
            for socket in pair.values():
                ret.update({k: WebsocketSubscriptionData(v) for k, v in socket._subscriptions.items()})

        return ret

    async def delete_websocket_subscription(self, id: str, *, force: bool = False) -> WebsocketSubscriptionData:
        """|coro|

        Delete an EventSub subsctiption with a Websocket Transport.

        This method is a helper method to remove a websocket subscription currently active on this client. This method also
        cleans up any websocket connections that have no remaining subscriptions after the subscription is removed.

        .. note::

            Make sure the subscription is currently active on this Client instance. You can check currently active websocket
            subscriptions via :meth:`.websocket_subscriptions`.

        Parameters
        ----------
        id: str
            The Eventsub subscription ID. You can view currently active subscriptions via :meth:`.websocket_subscriptions`.
        force: bool
            When set to ``True``, the subscription will be forcefully removed from the Client,
            regardless of any HTTPException's raised during the call to Twitch.

            When set to ``False``, if an exception is raised, the subscription will remain on the Client websocket.
            Defaults to ``False``.

        Returns
        -------
        :class:`~twitchio.WebsocketSubscriptionData`
            The data associated with the removed subscription.

        Raises
        ------
        ValueError
            The subscription with the provided ID could not be found on this client.
        :class:`~twitchio.HTTPException`
            Removing the subscription from Twitch failed.
        """
        # Find subscription...
        for token_for, pair in self._websockets.copy().items():
            for socket in pair.values():
                sub = socket._subscriptions.get(id, None)
                if not sub:
                    continue

                try:
                    await self._http.delete_eventsub_subscription(id, token_for=token_for)
                except HTTPException as e:
                    if not force:
                        raise e

                socket._subscriptions.pop(id, None)
                data = WebsocketSubscriptionData(sub)

                if not socket._subscriptions and not socket._closing and not socket._closed:
                    logger.info("Closing websocket '%s' due to no remaining subscriptions.", socket)
                    await socket.close()

                return data

        raise ValueError(f"Unable to find a Websocket subscription currently active on this client with ID '{id}'.")

    async def delete_all_eventsub_subscriptions(self, *, token_for: str | PartialUser | None = None) -> None:
        """|coro|

        Delete all eventsub subscriptions.

        Parameters
        ----------
        token_for: str | PartialUser | None
            Do not pass this if you wish to delete webhook subscriptions, which are what usually require deleting.

            For websocket subscriptions, provide the user ID, or PartialUser, associated with the subscription.
        """
        events = await self.fetch_eventsub_subscriptions(token_for=token_for)
        async for sub in events.subscriptions:
            await sub.delete()

    async def event_oauth_authorized(self, payload: UserTokenPayload) -> None:
        await self.add_token(payload["access_token"], payload["refresh_token"])

    async def fetch_conduit(self, conduit_id: str) -> Conduit | None:
        """|coro|

        Method which retrieves a :class:`~twitchio.Conduit` from the API, with the provided ID.

        Parameters
        ----------
        conduit_id: str
            The ID of the Conduit to retrieve.

        Returns
        -------
        Conduit
            The :class:`~twitchio.Conduit` with the associated ID, if found.
        None
            If the :class:`~twitchio.Conduit` cannnot be found ``None`` is returned.
        """
        payload = await self._http.get_conduits()
        for data in payload["data"]:
            if data["id"] == conduit_id:
                return Conduit(data, http=self._http)

    async def fetch_conduits(self) -> list[Conduit]:
        """|coro|

        Method to retrieve all :class:`~twitchio.Conduit`'s associated with this Client-ID.

        Returns
        -------
        list[:class:`~twitchio.Conduit`]
            The list of :class:`~twitchio.Conduit` associated with this application.
        """
        payload = await self._http.get_conduits()
        return [Conduit(d, http=self._http) for d in payload["data"]]

    async def create_conduit(self, shard_count: int) -> Conduit:
        """|coro|

        Method to create a :class:`~twitchio.Conduit` on the API.

        Parameters
        ----------
        shard_count: int
            The amount of shards to assign to the Conduit. Must be between ``1`` and ``20_000``.

        Raises
        ------
        ValueError
            ``shard_count`` must be between ``1`` and ``20_000``.

        Returns
        -------
        Conduit
            The newly created :class:`~twitchio.Conduit`.
        """
        if shard_count <= 0:
            raise ValueError('The provided "shard_count" must not be lower than 1.')

        elif shard_count > 20_000:
            raise ValueError('The provided "shard_count" cannot be greater than 20_000.')

        payload = await self._http.create_conduit(shard_count)
        return Conduit(payload["data"][0], http=self._http)


class ConduitInfo:
    """A special class wrapping :class:`~twitchio.Conduit` assigned only to :class:`~twitchio.AutoClient` and
    :class:`~twitchio.ext.commands.AutoBot`.

    This class serves as an abstraction layer to managing the :class:`~twitchio.Conduit` assigned to
    :class:`~twitchio.AutoClient` or :class:`~twitchio.ext.commands.AutoBot` and contains various information and helper
    methods.

    .. warning::

        The should not need to create this class yourself. Instead you can access it via
        :attr:`~twitchio.AutoClient.conduit_info`.
    """

    def __init__(self, client: AutoClient) -> None:
        self._client = client
        self._conduit: Conduit | None = None
        self._sockets: dict[str, Websocket] = {}

    def __repr__(self) -> str:
        return f'ConduitInfo(conduit="{self._conduit}", shard_count={self.shard_count})'

    @property
    def conduit(self) -> Conduit | None:
        """A property returning the :class:`~twitchio.Conduit` that the :class:`~twitchio.AutoClient` currently has
        ownership of. Could be ``None`` if a conduit has not yet been assigned, however this is usually done automatically
        during the startup stages of the :class:`~twitchio.AutoClient`.
        """
        return self._conduit

    @property
    def shard_count(self) -> int | None:
        """Property returning the amount of shards the :class:`~twitchio.AutoClient` currently contains as an ``int``.
        Could be ``None`` if a conduit has not yet been assigned, however this is usually done automatically during the
        startup stages of the :class:`~twitchio.AutoClient`.
        """
        return self._conduit.shard_count if self._conduit else None

    @property
    def id(self) -> str | None:
        """Property returning the ID of the :class:`~twitchio.Conduit` that the :class:`~twitchio.AutoClient` currently has
        ownership of. Could be ``None`` if a conduit has not yet been assigned, however this is usually done automatically
        during the startup stages of the :class:`~twitchio.AutoClient`.
        """
        return self._conduit.id if self._conduit else None

    @property
    def websockets(self) -> MappingProxyType[str, Websocket]:
        """Property returning a mapping of Websocket Shard-ID to Websocket that are currently active and assigned to the
        underlying :class:`~twitchio.Conduit`.

        .. warning::

            This property exists only for those requiring lower level access over the underlying websocket(s); however
            ideally the websocket(s) should not be altered or interfered with. The mapping and property itself cannot be
            altered.
        """
        return MappingProxyType(self._sockets)

    async def update_shard_count(self, shard_count: int, /, *, assign_transports: bool = True) -> Self:
        """|coro|

        Method wrapping :meth:`twitchio.Conduit.update` which updates the number of shards assigned to the
        :class:`~twitchio.Conduit`. This method can be used to scale the :class:`~twitchio.Conduit` up (more shards) or down
        with less shards.

        .. warning::

            Caution should be used when scaling multi-process solutions that connect to the same Conduit. In this particular
            case it is more likely appropriate to close down and restart each instance and adjust the ``shard_ids`` parameter
            on :class:`~twitchio.AutoClient` accordingly. However this method can be called with ``assign_transports=False``
            first to allow each instance to easily adjust when restarted.

        Parameters
        ----------
        shard_count: :class:`int`
            A positional-only :class:`int` which is the new amount of shards the :class:`~twitchio.Conduit` should contain.
            The amount of shards should be between ``1`` and ``20_000``.
        assign_transports: :class:`bool`
            A keyword-only :class:`bool` set which determines whether new websockets should be created and assigned to the
            Conduit. This should be set to ``False`` in multi-instance/process setups that require the
            :class:`~twitchio.AutoClient`'s to be restarted to rebalance shards accordingly. Defaults to ``True`` which is
            the best case for a single instance of :class:`~twitchio.AutoClient`.

        Raises
        ------
        MissingConduit
            No :class:`~twitchio.Conduit` has been assigned to the :class:`~twitchio.AutoClient`.
        ValueError
            The ``shard_count`` parameter cannot be lower than ``1`` and no higher than ``20_000``.
        HTTPException
            A an error occurred making the request to Twitch.

        Returns
        -------
        ConduitInfo
            Returns the updated :class:`~twitchio.ConduitInfo` and allows for chaining methods and attributes.
        """
        if not self._conduit:
            raise MissingConduit("Cannot update Conduit Shard Count as no Conduit has been assigned.")

        if shard_count <= 0:
            raise ValueError('The provided "shard_count" must not be lower than 1.')

        elif shard_count > 20_000:
            raise ValueError('The provided "shard_count" cannot be greater than 20_000.')

        self._conduit = await self._conduit.update(shard_count)
        assert self.conduit
        assert self.shard_count

        end = max(self._client._shard_ids) + 1
        shard_ids = list(range(end, end + (shard_count - len(self._client._shard_ids))))

        if assign_transports:
            if self.shard_count > len(self.websockets):
                await self._client._associate_shards(shard_ids)
            elif self.shard_count < len(self.websockets):
                remove = len(self.websockets) - self.shard_count

                async with self._client._associate_lock:
                    await self._disassociate_shards(self.shard_count, remove)

        return self

    def fetch_shards(self, *, status: ShardStatus | None = None) -> HTTPAsyncIterator[ConduitShard]:
        """|aiter|

        Method wrapping :meth:`twitchio.Conduit.fetch_shards` which returns the shard info for the Conduit retrieved from the
        Twitch API.

        .. note::

            The Shard ID's contained in the objects returned from this method may differ to the shard ID's associated with
            :attr:`~twitchio.ConduitInfo.websockets`. If you need to compare, each websocket has an attribute named
            ``session_id`` which can be used instead.

        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | Status                                    | Description                                                                                                       |
        +===========================================+===================================================================================================================+
        | ``enabled``                               | The shard is enabled.                                                                                             |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``webhook_callback_verification_pending`` | The shard is pending verification of the specified callback URL.                                                  |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``webhook_callback_verification_failed``  | The specified callback URL failed verification.                                                                   |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``notification_failures_exceeded``        | The notification delivery failure rate was too high.                                                              |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_disconnected``                | The client closed the connection.                                                                                 |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_failed_ping_pong``            | The client failed to respond to a ping message.                                                                   |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_received_inbound_traffic``    | The client sent a non-pong message. Clients may only send pong messages (and only in response to a ping message). |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_internal_error``              | The Twitch WebSocket server experienced an unexpected error.                                                      |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_network_timeout``             | The Twitch WebSocket server timed out writing the message to the client.                                          |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_network_error``               | The Twitch WebSocket server experienced a network error writing the message to the client.                        |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_failed_to_reconnect``         | The client failed to reconnect to the Twitch WebSocket server within the required time after a Reconnect Message. |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+

        Parameters
        ----------
        status: str
            An optional :class:`str` which when provided, filters the shards by their status on the API. Possible statuses
            are listed above. Defaults to ``None`` which fetches all shards.

        Returns
        -------
        HTTPAsyncIterator[:class:`~twitchio.ConduitShard`]
            An :class:`~twitchio.HTTPAsyncIterator` which can be awaited or used with ``async for`` to retrieve the
            :class:`~twitchio.ConduitShard`'s.

        Raises
        ------
        MissingConduit
            No :class:`~twitchio.Conduit` has been assigned to the :class:`~twitchio.AutoClient`.
        HTTPException
            An error occurred making the request to Twitch.
        """
        if not self._conduit:
            raise MissingConduit("Cannot fetch shards as no Conduit has been assigned.")

        return self._conduit.fetch_shards(status=status)

    async def _disassociate_shards(self, start: int, remove_count: int, /) -> None:
        closed = 0

        for n in range(start, start + remove_count):
            socket = self._sockets.pop(str(n), None)
            if not socket:
                continue

            try:
                closed += 1
                await socket.close(reassociate=False)
            except Exception as e:
                logger.debug("Ignoring exception in close of %r. It is likely a non-issue: %s", socket, e)

        logger.info(
            "Successfully scaled %r down to %d shards: Removed %d shards. %d shards remain active.",
            self,
            self.shard_count,
            closed,
            len(self.websockets),
        )

        self._client._shard_ids = sorted([int(k) for k in self._sockets])

    async def _update_shards(self, shards: list[ShardUpdateRequest]) -> Self:
        # TODO?
        if not self._conduit:
            raise MissingConduit("Cannot update Conduit Shards as no Conduit has been assigned.")

        await self._conduit.update_shards(shards)
        return self


class MultiSubscribeError(NamedTuple):
    """A special :class:`typing.NamedTuple` containing two fields available in the :class:`~twitchio.MultiSubscribePayload`,
    when a subscription to a Conduit is attempted via :meth:`~twitchio.AutoClient.multi_subscribe` and fails.

    Attributes
    ----------
    subscription: :class:`~twitchio.eventsub.SubscriptionPayload`
        The subscription payload passed to :meth:`~twitchio.AutoClient.multi_subscribe` which failed.
    error: :class:`~twitchio.HTTPException`
        The :class:`~twitchio.HTTPException` containing various information, caught while attempting to subscribe to this
        subscription.
    """

    subscription: SubscriptionPayload
    error: HTTPException


class MultiSubscribeSuccess(NamedTuple):
    """A special :class:`typing.NamedTuple` containing two fields available in the :class:`~twitchio.MultiSubscribePayload`,
    when a subscription to a Conduit is made successfully via :meth:`~twitchio.AutoClient.multi_subscribe`.

    Attributes
    ----------
    subscription: :class:`~twitchio.eventsub.SubscriptionPayload`
        The subscription payload passed to :meth:`~twitchio.AutoClient.multi_subscribe` which was successfully subscribed to.
    response: dict[str, Any]
        The response data from the subscription received from Twitch.
    """

    subscription: SubscriptionPayload
    response: SubscriptionResponse


class MultiSubscribePayload:
    """Payload received from the :meth:`~twitchio.AutoClient.multi_subscribe` method.

    This payload contains a list of :class:`~twitchio.MultiSubscribeSuccess` which are the successful subscriptions
    and another list of :class:`~twitchio.MultiSubscribeError` which are any subscriptions that failed.

    This payload is only returned when the parameters ``wait`` is set to ``True`` and ``stop_on_error`` is ``False`` in
    :meth:`~twitchio.AutoClient.multi_subscribe`.

    If the ``wait`` parameter in :meth:`~twitchio.AutoClient.multi_subscribe` is set to ``False``, you can await the returned
    :class:`asyncio.Task` later to retrieve this payload.

    Attributes
    ----------
    success: list[:class:`~twitchio.MultiSubscribeSuccess`]
        A list of :class:`~twitchio.MultiSubscribeSuccess` containing information about the successful subscriptions.
    errors: list[:class:`~twitchio.MultiSubscribeError`]
        A list of :class:`~twitchio.MultiSubscribeError` containing information about unsuccessful subscriptions.
    """

    __slots__ = ("errors", "success")

    def __init__(self, success: list[MultiSubscribeSuccess], errors: list[MultiSubscribeError]) -> None:
        self.success = success
        self.errors = errors


class AutoClient(Client):
    """The TwitchIO :class:`~twitchio.AutoClient` class used to easily manage Twitch Conduits and Shards.

    There is a ``commands.ext`` version of this class named :class:`~twitchio.ext.commands.AutoBot` which inherits from
    :class:`twitchio.ext.commands.Bot` instead of :class:`~twitchio.Client`.

    This class inherits from :class:`~twitchio.Client` and as such most attributes, properties and methods from
    :class:`~twitchio.Client` are also available.

    This or :class:`~twitchio.ext.commands.AutoBot` are the preferred clients of use when your application is either in
    multiple channels/broadcasters *or* requires subscription continuity.

    Twitch Conduits are a method of EventSub transport which allow higher throughput of events, higher
    (essentially unlimited) subscription limts (within cost), continutiy of subscriptions and scaling.

    To benefit from the subscription continuity of Conduits, your application is expected to have been connected to the
    associated Conduit within ``72 hours`` of it going offline.

    This and the :class:`~twitchio.ext.commands.AutoBot` classes make it easier to manage Conduits by implementing logic to
    aid in connection, shard association and conduit/shard scaling. There are a few common ways they can be setup, with the
    main ``3`` cases showcased below.

    The most common usecase will be case ``1``, which allows an application to connect to a new or existing Conduit
    automatically with little intervention or setup from developers, in this case the following happens:

    * If excactly ``1`` Conduit exists:
        * Your application will associate with that conduit and assign transports; existing subscriptions remain.
    * If no Conduit exists:
        * Your application will create and associate itself with the new Conduit, assigning transports and subscribing.
    * By default the amount of shards will be equal ``len(subscriptions) / max_per_shard`` or ``2`` whichever is greater **or** ``len(shard_ids)`` if passed.
        * Most applications will only require ``2`` or ``3`` shards, with the second shard mostly existing as a fallback.

    In both scenarios above your application can restart at anytime without re-subscribing, however take note of the
    following requirements.

    * Your application must reconnect within ``72 hours``.
        * If ``72 hours`` passes; your application will need to resubscribe to any eventsub subscriptions.
        * This will be done automatically if subscriptions are passed to the constructor.
    * Your application should be the only instance running. For multiple instances see case ``2`` and ``3``.
    * If you require new subscriptions since the application was restarted, they can be passed to
      :meth:`~twitchio.AutoClient.multi_subscribe` in something like :meth:`~twitchio.AutoClient.setup_hook`.

    **An example of case 1:**

    .. code:: python3

        class Bot(commands.AutoBot):

            def __init__(self, subs: list[twitchio.eventsub.SubscriptionPayload], *args, **kwargs) -> None:
                super().__init__(*args, **kwargs, subscriptions=subs)

            async def event_message(self, payload: twitchio.ChatMessage) -> None:
                print(f"Received Message: {payload}")


        async def main() -> None:
            # An example list of subscriptions; you could create this list however you need, e.g. from a database...
            # Subscribe to 3 channels messages...
            # If you require additional subscriptions after restart and 72 hours HAS NOT passed; See: multi_subscribe()

            subs = [
                eventsub.ChatMessageSubscription(broadcaster_user_id=..., user_id=...),
                eventsub.ChatMessageSubscription(broadcaster_user_id=..., user_id=...),
                eventsub.ChatMessageSubscription(broadcaster_user_id=..., user_id=...),
            ]

            async with Bot(subs=subs, client_id=..., client_secret=..., bot_id=..., prefix=...) as bot:
                await bot.start()


    Case 2 is another common scenario which allows developers to connect to a specific Conduit by providing the Conduit-ID.

    In this case the following happens:

    * Your application will connect to the provided Conduit-ID.
        * If the conduit does not exist or could not be found, an error will be raised on start-up.
        * Your application will assign the amount of transports equal to the shard count the Conduit returns from Twitch **or** the amount passed to ``len(shard_ids)``.
        * ``shard_ids`` is not a required parameter, however see below for more info.

    This case allows greater control over which Conduit your application connects to which is mostly only useful if your
    setup includes multiple Conduits and/or multiple instances of :class:`~twitchio.AutoClient` or
    :class:`~twitchio.ext.commands.AutoBot`.

    If the former is true, each instance of :class:`~twitchio.AutoClient` and :class:`~twitchio.ext.commands.AutoBot` should
    realistically connect to a different conduit each.

    When the latter is true, your application can be setup to effectively distribute shards equally accross instances by
    connecting to the same Conduit. In this scenario you will also need to pass the ``shard_ids`` parameter to each
    instance, making sure each instance is assigned shards. E.g. ``shard_ids=[0, 1, 2]`` and ``shard_ids=[3, 4, 5]`` for a
    ``2`` instance setup on a Conduit which contains ``6`` shards.

    As this case is more involved and requires much more attention; e.g. multiple instances need to be started correctly and
    connections to multiple Conduits need to be properly configured it usually wouldn't be advised for small to medium sized
    applications, suiting only larger applications that require some scaling outside of a single process.

    A single :class:`~twitchio.AutoClient` (hardware permitting) should be able to handle a large amount of subscriptions
    before needing to be scaled.

    **An example of case 2 (multiple instances on one conduit):**

    In this scenario your conduit should have ``6`` shards associated with it already. You should do this before starting
    multiple instances. The example below would simply be run twice, assigning ``3`` shards to each instance, E.g. on the
    first instance ``shard_ids=[0, 1, 2]`` and the second instance ``shard_ids=[3, 4, 5]``.

    You can prepare for this scenario by calling :meth:`twitchio.Conduit.update` on the appropriate Conduit or by calling
    :meth:`~twitchio.ConduitInfo.update_shard_count` with ``6`` shards, and keeping note of the Conduit-ID, before starting
    both processes.

    .. code:: python3

        class Bot(commands.AutoBot):

            def __init__(self, *args, **kwargs) -> None:
                super().__init__(
                    *args,
                    **kwargs,
                    subscriptions=subs,
                    conduit_id="CONDUIT_1_ID",
                    shard_ids=[...],
                )

            async def event_message(self, payload: twitchio.ChatMessage) -> None:
                print(f"Received Message: {payload}")


        async def main() -> None:
            async with Bot(client_id=..., client_secret=..., bot_id=..., prefix=...) as bot:
                await bot.start()


    For case 2 when connecting to multiple conduits instead, most of the above documentation applies, however you should
    make sure to provide a different ``conduit_id`` per instance.

    Case 3 is the least obvious and likely the least required. In this case if the ``conduit_id`` parameter is passed
    ``True``, the :class:`~twitchio.AutoClient` will create and start a new Conduit regardless of whether your application
    currently has a Conduit(s) existing on the API. Mostly for this scenario it could be used to quickly create a new Conduit
    to be used with Case 2 directly after.

    To scale up or down a single instance of :class:`~twitchio.AutoClient` see: :meth:`~twitchio.ConduitInfo.update_shard_count`.

    See: :class:`~twitchio.ConduitInfo` and :attr:`~twitchio.AutoClient.conduit_info` for the class used to manage the Conduit on the application.

    For more information on Conduits, please see: `Twitch Docs <https://dev.twitch.tv/docs/eventsub/handling-conduit-events>`_

    Parameters
    ----------
    conduit_id: str | bool | None
        An optional parameter passed, which could be the ID of the Conduit as a :class:`str` you want this instance to take
        ownership of, or ``None`` to connect to an existing Conduit or create one if none exist. You can also pass ``True``
        to this parameter, however see above for more details and examples on how this parameter affects your application.
        Defaults to ``None``, which is the most common use case.
    shard_ids: list[int]
        An optional :class:`list` of :class:`int` which sets the shard IDs this instance of :class:`~twitchio.AutoClient`
        will assign transports for. If the :class:`~twitchio.AutoClient` creates a new Conduit the length of this parameter
        will be the ``shard_count`` which the Conduit will be created with. This parameter can be used to equally distribute
        shards accross multiple instances/processes on a single Conduit. You should make sure the list of ``shard_ids`` is
        consecutive and in order. E.g. ``list(range(3))`` or ``[0, 1, 2]``. Shard ID's are ``0`` indexed.
    max_per_shard: int
        An optional parameter which allows the Client to automatically determine the amount of shards you may require based on
        the amount of ``subscriptions`` passed. The default value is ``1000`` and the algorithm used to determine shards is
        simply: ``len(subscriptons) / max_per_shard`` or ``2`` whichever is greater. Note this parameter has no effect when
        ``shard_ids`` is explicitly passed.
    subscriptions: list[twitchio.eventsub.SubscriptionPayload]
        An optional list of any combination of EventSub subscriptions (all of which inherit from
        :class:`~twitchio.eventsub.SubscriptionPayload`) the Client should attempt to subscribe to when required. The
        :class:`~twitchio.AutoClient` will only attempt to subscribe to these subscriptions when it creates a new Conduit. If
        your Client connects to an existing Conduit either by passing ``conduit_id`` or automatically, this parameter has no
        effect. In cases where you need to update an existing Conduit with new subscriptions see:
        :meth:`~twitchio.AutoClient.multi_subscribe` or the parameter ``force_subscribe``.
    force_subscribe: bool
        An optional :class:`bool` which when ``True`` will force attempt to subscribe to the subscriptions provided in the
        ``subscriptions`` parameter, regardless of whether a new conduit was created or not. Defaults to ``False``.
    force_scale: bool
        An optional :class:`bool` which when ``True`` will force the :class:`~twitchio.Conduit` associated with the
        AutoClient/Bot to scale up/down to the provided amount of shards in the ``shard_ids`` parameter if provided. If the
        ``shard_ids`` parameter is not passed, this parameter has no effect. Defaults to ``False``.
    """

    # NOTE:
    # Automatically listen to conduit.shard.disabled and maintain the state of shards
    # TODO: swap_on_failure? reduce_on_failure?
    # TODO: event_autobot?_subscribe_error
    # TODO: event_shard_disabled/revoked?
    # TODO: Periodic background check on shard-state

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str | None = None,
        **kwargs: Unpack[AutoClientOptions],
    ) -> None:
        self._shard_ids: list[int] = kwargs.pop("shard_ids", [])
        self._original_shards = self._shard_ids
        self._conduit_id: str | bool | None = kwargs.pop("conduit_id", MISSING)
        self._force_sub: bool = kwargs.pop("force_subscribe", False)
        self._force_scale: bool = kwargs.pop("force_scale", False)
        self._subbed: bool = False

        if self._conduit_id is MISSING or self._conduit_id is None:
            logger.warning(
                'No "conduit_id" was passed. If a single conduit exists we will try to take ownership. '
                'If you want to take ownership of a specific conduit, please pass the "conduit_id" parameter.'
            )

        elif self._conduit_id is True:
            logger.warning(
                '"conduit_id" was None. If possible a conduit will be created. '
                'If you want to take ownership of a specific conduit, please pass the "conduit_id" parameter.'
            )

        elif not isinstance(self._conduit_id, str):
            raise TypeError('The parameter "conduit_id" must be either a str, True or not provided.')

        self._max_per_shard = kwargs.pop("max_per_shard", 1000)
        self._initial_subs: list[SubscriptionPayload] = kwargs.pop("subscriptions", [])

        if self._max_per_shard < 1000 and not self._shard_ids:
            logger.warning('It is recommended that the "max_per_shard" parameter should not be set below 1000.')

        self._conduit_info: ConduitInfo = ConduitInfo(self)
        self._closing: bool = False
        self._background_check_task: asyncio.Task[None] | None = None
        self._associate_lock: asyncio.Lock = asyncio.Lock()

        super().__init__(client_id=client_id, client_secret=client_secret, bot_id=bot_id, **kwargs)

    def __repr__(self) -> str:
        return self.__class__.__name__

    async def _conduit_check(self) -> None:
        while True:
            await asyncio.sleep(120)
            logger.debug("Checking status of Conduit assigned to %r", self)

            try:
                conduits = await self.fetch_conduits()
            except Exception as e:
                logger.debug("Exception received fetching Conduits during Conduit checK: %s. Disregarding...", e)
                continue

            conduit: Conduit | None = None

            for c in conduits:
                if c.id == self.conduit_info.id:
                    conduit = c

            if not conduit:
                logger.debug("No conduit found during Conduit check. Disregarding...")
                continue

            broken: list[int] = []

            try:
                async for shard in conduit.fetch_shards():
                    shard_id = int(shard.id)

                    if shard_id not in self._shard_ids:
                        continue

                    if shard.callback:
                        continue

                    if shard.status.startswith("webhook"):
                        continue

                    if shard.status != "enabled":
                        broken.append(shard_id)
            except Exception as e:
                logger.debug("Exception received fetching Conduit Shards during Conduit checK: %s. Disregarding...", e)
                continue

            if not broken:
                continue

            logger.debug("Potentially broken shards found during Conduit check. Trying to re-associate: %r", broken)
            try:
                await self._associate_shards(broken)
            except Exception:
                logger.warning("An attempt to re-associate Conduit Shards: %r was unsuccessful. Consider rebalancing.")

    async def _setup(self) -> None:
        # Subscribe to "conduit.shard.disabled"

        # Listen to websocket closed
        # Unexpected closes need to be handled on the Client for Conduits as we need to determine a few things first...
        self.add_listener(self._websocket_closed, event="event_websocket_closed")

        if self._conduit_id is MISSING:
            conduits = await self.fetch_conduits()
            count = len(conduits)

            if count > 1:
                # TODO: Maybe log currernt conduit info?
                raise RuntimeError('Too many currently active conduits exist and no "conduit_id" parameter was passed.')

            if count == 0:
                logger.info("No currently active conduits. Attempting to generate a new one.")
                await self._generate_new_conduit()
            else:
                logger.info("Conduit found: %r. Attempting to take ownership of this conduit.", conduits[0])
                self._conduit_info._conduit = conduits[0]

                if not self._shard_ids:
                    self._shard_ids = list(range(self._conduit_info.shard_count))  # type: ignore

        elif self._conduit_id is True:
            logger.info("Attempting to create and take ownership of a new Conduit.")
            await self._generate_new_conduit()

        else:
            conduits = await self.fetch_conduits()

            for conduit in conduits:
                if conduit.id == self._conduit_id:
                    logger.info('Conduit with the provided ID: "%s" found. Attempting to take ownership.', self._conduit_id)
                    self._conduit_info._conduit = conduit

                    if not self._shard_ids:
                        self._shard_ids = list(range(self._conduit_info.shard_count))  # type: ignore

        if not self._conduit_info.conduit:
            # TODO: Maybe log currernt conduit info?
            raise MissingConduit("No conduit could be found with the provided ID or a new one can not be created.")

        if self._force_scale and self._original_shards:
            logger.info("Scaling %r to %d shards.", len(self._original_shards))
            await self._conduit_info.update_shard_count(len(self._original_shards), assign_transports=False)

        await self._associate_shards(self._shard_ids)
        if self._force_sub and not self._subbed:
            await self.multi_subscribe(self._initial_subs)

        await self.setup_hook()

        self._setup_called = True
        self._background_check_task = asyncio.create_task(self._conduit_check())

    async def _websocket_closed(self, payload: WebsocketClosed) -> None:
        if self._closing:
            return

        if not payload.socket._shard_id:
            return

        if not payload.reassociate:
            self._conduit_info._sockets.pop(payload.socket._shard_id, None)
            return

        if payload.socket._shard_id not in self._conduit_info._sockets:
            return

        try:
            await self._associate_shards(shard_ids=[int(payload.socket._shard_id)])
        except Exception as e:
            logger.debug("Error re-associating shards for conduit %r after websocket close: %s", self.conduit_info, e)

    async def _connect_and_welcome(self, websocket: Websocket) -> bool:
        await websocket.connect(fail_once=False)

        async def welcome_predicate(payload: WebsocketWelcome) -> bool:
            nonlocal websocket
            return websocket.session_id == payload.id

        if not websocket._session_id:
            try:
                await self.wait_for("websocket_welcome", timeout=10, predicate=welcome_predicate)
            except TimeoutError:
                return False

        return websocket._session_id is not None

    async def _associate_flow(self, websocket: Websocket) -> None:
        connected = await self._connect_and_welcome(websocket)

        if not connected:
            websocket._failed = True
            raise TimeoutError(f"{websocket!r} failed to send a Welcome Payload within the 10s timeframe.")

    async def _process_batched(self, batched: list[Websocket]) -> None:
        tasks: list[asyncio.Task[None]] = []

        for socket in batched:
            task = asyncio.create_task(self._associate_flow(socket))
            tasks.append(task)

        await asyncio.wait(tasks)

        assert self._conduit_info.conduit
        payloads: list[ShardUpdateRequest] = []

        for socket in batched:
            # Crash here; we can't continue if a shard has a critical failure
            if socket._failed or not socket.connected:
                raise RuntimeError(
                    "Unable to associate shards with Conduit. An unexpected error occurred during association."
                )

            assert socket._session_id and socket._shard_id is not None

            payload: ShardUpdateRequest = {
                "id": socket._shard_id,
                "transport": {"method": "websocket", "session_id": socket._session_id},
            }
            payloads.append(payload)

        await self._conduit_info._update_shards(payloads)
        self._conduit_info._sockets.update({str(socket._shard_id): socket for socket in batched})

        logger.info(
            "Associated shards with %r successfully. Shards: %d / %d (connected / Conduit total).",
            self._conduit_info,
            len(self._conduit_info.websockets),
            self._conduit_info.shard_count,
        )

    async def _associate_shards(self, shard_ids: list[int]) -> None:
        await self._associate_lock.acquire()

        try:
            assert self._conduit_info.conduit

            batched: list[Websocket] = []

            for i, n in enumerate(shard_ids):
                if i % 10 == 0 and i != 0:
                    await self._process_batched(batched)
                    batched.clear()

                websocket = Websocket(client=self, http=self._http, shard_id=str(n))
                batched.append(websocket)

            if batched:
                await self._process_batched(batched)

            self._shard_ids = sorted([int(k) for k in self._conduit_info._sockets])
        except:
            raise
        finally:
            self._associate_lock.release()

    async def _generate_new_conduit(self) -> Conduit:
        if not self._shard_ids:
            # Try and determine best count based on provided subscriptions with leeway...
            # Defaults to 2 shards if no subscriptions are passed...
            total_subs = len(self._initial_subs)
            self._shard_ids = list(range(clamp(math.ceil(total_subs / self._max_per_shard) + 1, 2, 20_000)))

        try:
            new = await self.create_conduit(len(self._shard_ids))
        except HTTPException as e:
            if e.status == 429:
                # TODO: Maybe log currernt conduit info?
                raise RuntimeError(
                    "Conduit limit reached. Please provide the Conduit ID you wish to take ownership of, "
                    "or remove an existing conduit."
                )

            raise e

        logger.info('Successfully generated a new Conduit: "%s". Conduit contains %d shards.', new.id, new.shard_count)

        self._conduit_info._conduit = new
        self.dispatch("autobot_conduit_created", self._conduit_info)

        # Maybe need an additional bool; will need feedback?
        if self._initial_subs:
            logger.info("Attempting to do an initial subscription on new conduit: %r.", self._conduit_info)
            await self._multi_sub(self._initial_subs, stop_on_error=False)
            self._subbed = True

        return new

    @property
    def conduit_info(self) -> ConduitInfo:
        """Property returning the :class:`~twitchio.ConduitInfo` associated with the :class:`~twitchio.AutoClient` or
        :class:`~twitchio.ext.commands.AutoBot`.
        """
        return self._conduit_info

    async def _multi_sub(
        self, subscriptions: Collection[SubscriptionPayload], *, stop_on_error: bool
    ) -> MultiSubscribePayload:
        assert self._conduit_info.conduit

        conduit = self._conduit_info.conduit
        transport: SubscriptionCreateTransport = {"method": "conduit", "conduit_id": conduit.id}

        logger.info("Attempting to subscribe to %d subscriptions on %r.", len(subscriptions), self._conduit_info)

        errors: list[MultiSubscribeError] = []
        success: list[MultiSubscribeSuccess] = []

        for payload in subscriptions:
            data: _SubscriptionData = {
                "type": SubscriptionType(payload.type),
                "version": payload.version,
                "condition": payload.condition,
                "transport": transport,
                "token_for": None,
            }

            try:
                resp: SubscriptionResponse = await self._http.create_eventsub_subscription(**data)
            except HTTPException as e:
                if stop_on_error:
                    logger.warning(
                        'An error occured in call to "%r.multi_subscribe" with "stop_on_error" set to True.', e, exc_info=e
                    )
                    raise e

                error_payload = MultiSubscribeError(subscription=payload, error=e)
                errors.append(error_payload)
            else:
                success_payload = MultiSubscribeSuccess(subscription=payload, response=resp)
                success.append(success_payload)

        return MultiSubscribePayload(success=success, errors=errors)

    @overload
    async def multi_subscribe(
        self, subscriptions: Collection[SubscriptionPayload], *, wait: Literal[True] = True, stop_on_error: bool = False
    ) -> MultiSubscribePayload: ...

    @overload
    async def multi_subscribe(
        self, subscriptions: Collection[SubscriptionPayload], *, wait: Literal[False] = False, stop_on_error: bool = False
    ) -> asyncio.Task[MultiSubscribePayload]: ...

    async def multi_subscribe(
        self,
        subscriptions: Collection[SubscriptionPayload],
        *,
        wait: bool = True,
        stop_on_error: bool = False,
    ) -> MultiSubscribePayload | asyncio.Task[MultiSubscribePayload]:
        """|coro|

        This method attempts to subscribe to the provided list of EventSub subscriptions on the Conduit associated with
        the :class:`~twitchio.AutoClient`.

        Since Conduits maintain subscriptions for up to ``72 hours`` after the Conduit/Shards go offline, calling this method
        is intended to be used to setup the :class:`~twitchio.AutoClient` initially, or after a Conduit has been offline for
        ``72 hours`` or longer; however it can be used to subscribe at any other time.

        Ideally the bulk of your subscriptions should only ever need to be subscribed to once and an Online status for the
        Conduit and associated shards should be maintained and/or kept within the ``72 hour`` limit.

        Conduit subscriptions only use `App Access Tokens <https://dev.twitch.tv/docs/authentication/>`_ (akin to webhooks);
        however the user must have authorised the App (Client-ID) with the appropriate scopes associated with subscriptions.

        An `App Access Token <https://dev.twitch.tv/docs/authentication/>`_ is generated automatically each time the
        :class:`~twitchio.AutoClient` is logged in which is called automatically with :meth:`.login`, :meth:`.start` and
        :meth:`.run`.

        To avoid some confusion and ease of use, if a list of subscriptions is passed to the :class:`~twitchio.AutoClient`
        constructor this method will be called automatically whenever it creates a **new** Conduit on startup.

        By default this method will **not** stop attempting to subscribe to subscriptions if an error is received during
        it's invocation, instead any subscriptions that failed will be included in the returned payload. This behaviour
        can be changed by setting the ``stop_on_error`` parameter to ``True``.

        If ``wait=True`` (default) this method acts like any other coroutine used with ``await``.
        Otherwise when ``wait=False`` the subscriptions will occur in a background task and you will receive the
        created :class:`asyncio.Task` instead; when ``wait=False`` you will **not** receive a payload upon
        completion, however the task can be awaited later to receive the result.

        Parameters
        ----------
        subscriptions: list[:class:`~twitchio.eventsub.SubscriptionPayload`]
            A list of :class:`~twitchio.eventsub.SubscriptionPayload` to attempt subscribing to on the associated Conduit.
        wait: bool
            Whetheer to treat this method like a standard awaited coroutine or create and return a :class:`asyncio.Task`
            instead. Defaults to ``True`` which treats the method as a standard coroutine.
        stop_on_error: bool
            Whether to stop and raise an exception when an error occurs attempting to subscribe to any subscription provided.
            Defaults to ``False``, which adds any errors to the returned :class:`~twitchio.MultiSubscribePayload` instead of
            raising.

        Returns
        -------
        MultiSubscribePayload
            The payload containing successfull subscriptions and any errors.
        :class:`asyncio.Task`
            When ``wait`` is False, the created background task is returned.

        Raises
        ------
        MissingConduit
            Cannot subscribe when no Conduit is associated with this Client.
        """
        if not self._conduit_info.conduit:
            raise MissingConduit("Unable to subscribe as a Conduit has not been associated with %r.", self)

        if wait:
            return await self._multi_sub(subscriptions, stop_on_error=stop_on_error)

        task: asyncio.Task[MultiSubscribePayload] = asyncio.create_task(
            self._multi_sub(subscriptions, stop_on_error=stop_on_error)
        )
        return task

    async def _close_sockets(self) -> None:
        socks = self._conduit_info._sockets.values()
        logger.info("Attempting to close %d associated Conduit Websockets.", len(socks))

        tasks: list[asyncio.Task[None]] = [asyncio.create_task(s.close()) for s in socks]
        await asyncio.wait(tasks)

        logger.info("Successfully closed %d Conduit Websockets on %r.", len(socks), self)

    async def close(self, **options: Any) -> None:
        if self._closing:
            return

        self._closing = True

        try:
            await self._close_sockets()
        except Exception as e:
            logger.warning("An error occurred during the cleanup of Conduit Websockets: %s", e)

        self._conduit_info._sockets.clear()

        if self._background_check_task:
            try:
                self._background_check_task.cancel()
            except Exception:
                pass

        await super().close(**options)

    async def delete_websocket_subscription(self, *args: Any, **kwargs: Any) -> Any:
        """
        .. important::

            AutoClient does not implement this method.
        """
        raise NotImplementedError("AutoClient does not implement this method.")

    def websocket_subscriptions(self) -> Any:
        """
        .. important::

            AutoClient does not implement this method.
        """
        raise NotImplementedError("AutoClient does not implement this method.")

    async def subscribe_websocket(self, *args: Any, **kwargs: Any) -> Any:
        """
        .. important::

            AutoClient does not implement this method.
        """
        raise NotImplementedError("AutoClient does not implement this method.")

    async def subscribe_webhook(self, *args: Any, **kwargs: Any) -> Any:
        """
        .. important::

            AutoClient does not implement this method.
        """
        raise NotImplementedError("AutoClient does not implement this method.")
