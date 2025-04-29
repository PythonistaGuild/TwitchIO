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
from collections import defaultdict
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Self, Unpack

from .authentication import ManagedHTTPClient, Scopes, UserTokenPayload
from .eventsub.enums import SubscriptionType
from .eventsub.websockets import Websocket
from .exceptions import HTTPException
from .http import HTTPAsyncIterator
from .models.bits import Cheermote, ExtensionTransaction
from .models.ccls import ContentClassificationLabel
from .models.channels import ChannelInfo
from .models.chat import ChatBadge, ChatterColor, EmoteSet, GlobalEmote
from .models.games import Game
from .models.teams import Team
from .payloads import EventErrorPayload, WebsocketSubscriptionData
from .user import ActiveExtensions, Extension, PartialUser, User
from .utils import MISSING, EventWaiter, unwrap_function
from .web import AiohttpAdapter
from .web.utils import BaseAdapter
from .eventsub.conduits import ConduitMixin


if TYPE_CHECKING:
    import datetime
    from collections.abc import Awaitable, Callable, Coroutine

    import aiohttp

    from .authentication import ClientCredentialsPayload, ValidateTokenPayload
    from .eventsub.subscriptions import SubscriptionPayload
    from .http import HTTPAsyncIterator
    from .models.clips import Clip
    from .models.entitlements import Entitlement, EntitlementStatus
    from .models.eventsub_ import EventsubSubscriptions
    from .models.search import SearchChannel
    from .models.streams import Stream, VideoMarkers
    from .models.videos import Video
    from .types_.eventsub import SubscriptionCreateTransport, SubscriptionResponse, _SubscriptionData
    from .types_.options import ClientOptions, WaitPredicateT
    from .types_.tokens import TokenMappingData


logger: logging.Logger = logging.getLogger(__name__)


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
        return MappingProxyType(self._http._tokens)

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

        if self._bot_id:
            logger.debug("Fetching Clients self user for %r", self)
            partial = PartialUser(id=self._bot_id, http=self._http)
            self._user = await partial.user() if self._fetch_self else partial

        await self.setup_hook()

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
            Whether to start and run a web adapter. Defaults to `True`. See: ... for more information.
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

        if with_adapter:
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
            Whether to start and run a web adapter. Defaults to `True`. See: ... for more information.
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
        logger.debug("Cleanup completed on %r.", self)

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

        .. note::

            See: ... for more information and recipes on using eventsub.

        Parameters
        ----------
        payload: :class:`twitchio.SubscriptionPayload`
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

        .. note::

            For more information on how to setup your bot with webhooks, see: ...

        .. important::

            Usually you wouldn't use webhooks to subscribe to the
            :class:`~twitchio.eventsub.ChatMessageSubscription` subscription.

            Consider using :meth:`~.subscribe_websocket` for this subscription.

        Parameters
        ----------
        payload: :class:`~twitchio.SubscriptionPayload`
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
            type, status and user_id are mutually exclusive and only one can be passed, otherwise ValueError will be raised.

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
            Only one of 'status', 'user_id', or 'type' can be provided.
        """

        provided: int = len([v for v in (type, user_id, status) if v])
        if provided > 1:
            raise ValueError("Only one of 'status', 'user_id', or 'type' can be provided.")

        return await self._http.get_eventsub_subscription(
            type=type,
            max_results=max_results,
            token_for=token_for,
        )

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


class AutoClient(Client, ConduitMixin): ...
