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
from .eventsub.enums import SubscriptionType, TransportMethod
from .eventsub.websockets import Websocket
from .exceptions import HTTPException
from .http import HTTPAsyncIterator
from .models.bits import Cheermote, ExtensionTransaction
from .models.ccls import ContentClassificationLabel
from .models.channels import ChannelInfo
from .models.chat import ChatBadge, ChatterColor, EmoteSet, GlobalEmote
from .models.games import Game
from .models.teams import Team
from .payloads import EventErrorPayload
from .user import ActiveExtensions, Extension, PartialUser, User
from .web import AiohttpAdapter
from .web.utils import BaseAdapter


if TYPE_CHECKING:
    import datetime
    from collections.abc import Awaitable, Callable, Coroutine

    import aiohttp

    from .authentication import ClientCredentialsPayload, ValidateTokenPayload
    from .eventsub.payloads import SubscriptionPayload
    from .http import HTTPAsyncIterator
    from .models.clips import Clip
    from .models.entitlements import Entitlement, EntitlementStatus
    from .models.search import SearchChannel
    from .models.streams import Stream, VideoMarkers
    from .models.videos import Video
    from .types_.eventsub import SubscriptionCreateTransport, SubscriptionResponse, _SubscriptionData
    from .types_.options import AdapterOT, ClientOptions
    from .types_.tokens import TokenMappingData


logger: logging.Logger = logging.getLogger(__name__)


class Client:
    """Client.

    Parameters
    -----------
    client_id: str
        The client ID of the application you registered on the Twitch Developer Portal.
    client_secret: str
        The client secret of the application you registered on the Twitch Developer Portal.
        This must be associated with the same `client_id`.
    bot_id: str | None
        An optional `str` which should be the User ID associated with the Bot Account. It is highly recommended setting this
        parameter.
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str | None = None,
        **options: Unpack[ClientOptions],
    ) -> None:
        redirect_uri: str | None = options.get("redirect_uri", None)
        scopes: Scopes | None = options.get("scopes", None)
        session: aiohttp.ClientSession | None = options.get("session", None)

        self._bot_id: str | None = bot_id

        self._http = ManagedHTTPClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
        )

        # TODO: Note, adapter must be subclassed to use with ES...
        adapter: AdapterOT = options.get("adapter", AiohttpAdapter)
        if isinstance(adapter, BaseAdapter):
            adapter.client = self
            self._adapter = adapter
        else:
            self._adapter = adapter()
            self._adapter.client = self

        self._listeners: dict[str, set[Callable[..., Coroutine[Any, Any, None]]]] = defaultdict(set)

        self._login_called: bool = False
        self._has_closed: bool = False

        # Websockets for EventSub
        self._websockets: dict[str, dict[str, Websocket]] = defaultdict(dict)

        self.__waiter: asyncio.Event = asyncio.Event()

    @property
    def tokens(self) -> MappingProxyType[str, TokenMappingData]:
        """Property which returns a read-only mapping of the tokens that are managed by the client.

        See:

        - [`.add_token`][twitchio.Client.add_token]

        - [`.remove_token`][twitchio.Client.remove_token]

        - [`.load_tokens`][twitchio.Client.load_tokens]

        - [`.dump_tokens`][twitchio.Client.dump_tokens]

        For various methods of managing the tokens on the client.

        !!! danger
            This method returns sensitive information such as user-tokens. You should take care not to expose these tokens.
        """
        return MappingProxyType(self._http._tokens)

    @property
    def bot_id(self) -> str | None:
        """Property which returns the User-ID associated with this Client if set, or `None`.

        This can be set using the `bot_id` parameter on [`Client`][twitchio.Client]
        """
        return self._bot_id

    async def event_error(self, payload: EventErrorPayload) -> None:
        """
        Event called when an error occurs in an event or event listener.

        This event can be overriden to handle event errors differently.
        By default, this method logs the error and ignores it.

        !!! warning
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
                payload: EventErrorPayload = EventErrorPayload(error=e, listener=listener, original=original)
                await self.event_error(payload)
            except Exception as inner:
                logger.error('Ignoring Exception in listener "%s.event_error":\n', self.__qualname__, exc_info=inner)

    def dispatch(self, event: str, payload: Any | None = None) -> None:
        name: str = "event_" + event

        listeners: set[Callable[..., Coroutine[Any, Any, None]]] = self._listeners[name]
        extra: Callable[..., Coroutine[Any, Any, None]] | None = getattr(self, name, None)
        if extra:
            listeners.add(extra)

        _ = [asyncio.create_task(self._dispatch(listener, original=payload)) for listener in listeners]

    async def setup_hook(self) -> None:
        """
        Method called after [`.login`][twitchio.Client.login] has been called but before the client is started.

        [`.start`][twitchio.Client.start] calls [`.login`][twitchio.Client.login] internally for you, so when using
        [`.start`][twitchio.Client.start] this method will be called after the client has generated and validated an
        app token. The client won't complete start up until this method has completed.

        This method is intended to be overriden to provide an async environment for any setup required.

        By default, this method does not implement any logic.
        """
        ...

    async def login(self, *, token: str | None = None) -> None:
        """
        Method to login the client and generate or store an app token.

        This method is called automatically when using [`.start`][twitchio.Client.start].
        You should not call this method if you are using [`.start`][twitchio.Client.start].

        This method calls [`.setup_hook`][twitchio.Client.setup_hook].

        !!! note
            If no token is provided, the client will attempt to generate a new app token for you.

        Parameters
        ----------
        token: str | None
            An optional app token to use instead of generating one automatically.
        """
        if self._login_called:
            return

        self._login_called = True

        if not token:
            payload: ClientCredentialsPayload = await self._http.client_credentials_token()
            validated: ValidateTokenPayload = await self._http.validate_token(payload.access_token)
            token = payload.access_token

            logger.info("Generated App Token for Client-ID: %s", validated.client_id)

        async with self._http._token_lock:
            await self.load_tokens()

        self._http._app_token = token
        await self.setup_hook()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start(self, token: str | None = None, *, with_adapter: bool = True) -> None:
        """
        Method to login the client and create a continuously running event loop.

        You should not call [`.login`][twitchio.Client.login] if you are using this method as it is called internally
        for you.

        !!! note
            This method blocks asynchronously until the client is closed.

        Parameters
        ----------
        token: str | None
            An optional app token to use instead of generating one automatically.
        with_adapter: bool
            Whether to start and run a web adapter. Defaults to `True`. See: ... for more information.
        """
        self.__waiter.clear()
        await self.login(token=token)

        if with_adapter:
            await self._adapter.run()

        # Dispatch ready event... May change places in the future.
        self.dispatch("ready")

        try:
            await self.__waiter.wait()
        finally:
            await self.close()

    def run(self, token: str | None = None, *, with_adapter: bool = True) -> None:
        # TODO: Docs...

        async def run() -> None:
            async with self:
                await self.start(token=token, with_adapter=with_adapter)

        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            pass

    async def close(self) -> None:
        # TODO: Docs...
        if self._has_closed:
            return

        self._has_closed = True
        await self._http.close()

        if self._adapter._runner_task is not None:
            try:
                await self._adapter.close()
            except Exception:
                pass

        sockets: list[Websocket] = [w for p in self._websockets.values() for w in p.values()]
        for socket in sockets:
            await socket.close()

        async with self._http._token_lock:
            await self.dump_tokens()

        self._http.cleanup()
        self.__waiter.set()

    async def add_token(self, token: str, refresh: str) -> None:
        """Adds a token/refresh pair to the client to be automatically managed.

        After successfully adding a token to the client, the token will be automatically revalidated and refreshed when
        required.

        This method is automatically called in the [`event_oauth_authorized`][twitchio.events.event_oauth_authorized] event,
        when a token is via the built-in OAuth.

        You can override the [`event_oauth_authorized`][twitchio.events.event_oauth_authorized] or this method to
        implement custom functionality such as storing the token in a database.

        ??? note

            Both `token` and `refresh` are required parameters.

        Parameters
        ----------
        token: str
            The User-Access token to add.
        refresh: str
            The refresh token associated with the User-Access token to add.

        Example
        -------

        ```python
        class Client(twitchio.Client):

            async def add_token(self, token: str, refresh: str) -> None:
                # Code to add token to database here...
                ...

                # Adds the token to the client...
                await super().add_token(token, refresh)
        ```
        """
        await self._http.add_token(token, refresh)

    async def remove_token(self, user_id: str, /) -> TokenMappingData | None:
        """Removes a token for the specified user-ID from the Client.

        Removing a token will ensure the client stops managing the token.

        This method has been made `async` for convenience when overriding the default functionality.

        You can use override this method to implement custom logic, such as removing a token from your database.

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
        """Method used to load tokens when the client starts.

        !!! info
            This method is always called by the client during `login` but **before** `setup_hook`.

        You can override this method to implement your own token loading logic into the client, such as from a database.

        By default this method loads tokens from a file named `".tio.tokens.json"` if it is present; usually if you use
        the default method of dumping tokens. **However**, it is preferred you would override this function to load your
        tokens from a database, as this has far less chance of being corrupted, damaged or lost.

        Parameters
        ----------
        path: Optional[str | None]
            The path to load tokens from, if this is `None` and the method has not been overriden, this will default to
            `.tio.tokens.json`. Defaults to `None`.

        Example
        -------

        ```python
        class Client(twitchio.Client):

            async def load_tokens(self, path: str | None = None) -> None:
                # Code to fetch all tokens from the database here...
                ...

                for row in tokens:
                    await self.add_token(row["token"], row["refresh"])
        ```
        """
        await self._http.load_tokens(name=path)

    async def dump_tokens(self, path: str | None = None, /) -> None:
        """
        Method which dumps all the added OAuth tokens currently managed by this Client.

        !!! info
            This method is always called by the client when it is gracefully closed.

        ??? note
            By default this method dumps to a JSON file named `".tio.tokens.json"`.

        You can override this method to implement your own custom logic, such as saving tokens to a database, however
        it is preferred to use [`.add_token`][twitchio.Client.add_token] to ensure the tokens are handled as they are added.

        Parameters
        ----------
        path: str | None
            The path of the file to save to. Defaults to `.tio.tokens.json`.
        """
        await self._http.dump(path)

    def add_listener(self, listener: Callable[..., Coroutine[Any, Any, None]], *, event: str | None = None) -> None:
        name: str = event or listener.__name__

        if not name.startswith("event_"):
            raise ValueError('Listener and event names must start with "event_".')

        if name == "event_":
            raise ValueError('Listener and event names cannot be named "event_".')

        if not asyncio.iscoroutinefunction(listener):
            raise ValueError("Listeners and Events must be coroutines.")

        self._listeners[name].add(listener)

    def create_partialuser(self, user_id: str | int, user_login: str | None = None) -> PartialUser:
        """Helper method to create a PartialUser.

        !!! version "3.0.0"
            This has been renamed from `create_user` to `create_partialuser`.

        Parameters
        ----------
        user_id: str | int
            ID of the user you wish to create a PartialUser for.
        user_login: str | None
            Login name of the user you wish to create a PartialUser for, if available.

        Returns
        -------
        PartialUser
            A PartialUser object.
        """
        return PartialUser(user_id, user_login, http=self._http)

    async def fetch_chat_badges(self) -> list[ChatBadge]:
        """
        Fetches Twitch's list of global chat badges, which users may use in any channel's chat room.

        If you wish to fetch a specific broadcaster's chat badges use [`fetch_chat_badges`][twitchio.user.fetch_chat_badges]

        Returns
        --------
        list[twitchio.ChatBadge]
            A list of ChatBadge objects
        """

        data = await self._http.get_global_chat_badges()
        return [ChatBadge(x, http=self._http) for x in data["data"]]

    async def fetch_emote_sets(self, emote_set_ids: list[str], *, token_for: str | None = None) -> list[EmoteSet]:
        """
        Fetches emotes for one or more specified emote sets.

        ??? tip
            An emote set groups emotes that have a similar context.
            For example, Twitch places all the subscriber emotes that a broadcaster uploads for their channel in the same emote set.

        Parameters
        ----------
        emote_set_ids: list[str]
            List of IDs that identifies the emote set to get. You may specify a maximum of 25 IDs.
        token_for: str | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        list[EmoteSet]
            A list of EmoteSet objects.

        Raises
        ------
        ValueError
            You can only specify a maximum of 25 emote set IDs.
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
        token_for: str | None = None,
    ) -> list[ChatterColor]:
        """
        Fetches the color of a chatter.

        .. versionchanged:: 3.0
            Removed the `token` parameter. Added the `token_for` parameter.

        Parameters
        -----------
        user_ids: list[str | int]
            List of user ids to fetch the colors for.
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        list[twitchio.ChatterColor]
            A list of ChatterColor objects for the requested users.
        """
        if len(user_ids) > 100:
            raise ValueError("Maximum of 100 user_ids")

        data = await self._http.get_user_chat_color(user_ids, token_for)
        return [ChatterColor(d, http=self._http) for d in data["data"] if data]

    async def fetch_channels(
        self,
        broadcaster_ids: list[str | int],
        *,
        token_for: str | None = None,
    ) -> list[ChannelInfo]:
        """
        Retrieve channel information from the API.

        Parameters
        -----------
        broadcaster_ids: list[str | int]
            A list of channel IDs to request from API.
            You may specify a maximum of 100 IDs.
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        list[twitchio.ChannelInfo]
            A list of ChannelInfo objects.
        """
        if len(broadcaster_ids) > 100:
            raise ValueError("Maximum of 100 broadcaster_ids")

        data = await self._http.get_channel_info(broadcaster_ids, token_for)
        return [ChannelInfo(d, http=self._http) for d in data["data"]]

    async def fetch_cheermotes(
        self,
        *,
        broadcaster_id: int | str | None = None,
        token_for: str | None = None,
    ) -> list[Cheermote]:
        """
        Fetches a list of Cheermotes that users can use to cheer Bits in any Bits-enabled channel's chat room. Cheermotes are animated emotes that viewers can assign Bits to.
        If a broadcaster_id is not specified then only global cheermotes will be returned.
        If the broadcaster uploaded Cheermotes, the type attribute will be set to channel_custom.

        Parameters
        -----------
        broadcaster_id: str | int | None
            The ID of the broadcaster whose custom Cheermotes you want to get. If not provided then you will fetch global Cheermotes.
        token_for: str | None
            An optional user token to use instead of the default app token.

        Returns
        --------
        list[twitchio.Cheermote]
            A list of Cheermote objects.
        """
        data = await self._http.get_cheermotes(str(broadcaster_id) if broadcaster_id else None, token_for)
        return [Cheermote(d, http=self._http) for d in data["data"]]

    async def fetch_classifications(
        self, locale: str = "en-US", *, token_for: str | None = None
    ) -> list[ContentClassificationLabel]:
        """
        Fetches information about Twitch content classification labels.

        Parameters
        -----------
        locale: str
            Locale for the Content Classification Labels.

        Returns
        --------
        list[twitchio.ContentClassificationLabel]
            A list of Content Classification Labels objects.
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
        token_for: str | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Clip]:
        """
        Fetches clips by clip id or game id.

        Parameters
        -----------
        game_id: list[str | int] | None
            A game id to fetch clips from.
        clip_ids: list[str] | None
            A list of specific clip IDs to fetch.
            Maximum amount you can request is 100.
        started_at: datetime.datetime
            The start date used to filter clips.
        ended_at: datetime.datetime
            The end date used to filter clips. If not specified, the time window is the start date plus one week.
        featured: bool | None = None
            If True, returns only clips that are featured.
            If False, returns only clips that aren't featured.
            All clips are returned if this parameter is not provided.
        token_for: str | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.


        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Clip]

        Raises
        ------
        ValueError
            Only one of `game_id` or `clip_ids` can be provided.
        ValueError
            One of `game_id` or `clip_ids` must be provided.
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
        """
        Fetches global emotes from the twitch API

        !!! note
            The ID in the extension_id query parameter must match the provided client ID.

        Parameters
        -----------
        extension_id: str
            The ID of the extension whose list of transactions you want to get. You may specify a maximum of 100 IDs.
        ids: list[str] | None
            A transaction ID used to filter the list of transactions.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.ExtensionTransaction]
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

    async def fetch_extensions(self, *, token_for: str) -> list[Extension]:
        """
        Fetch a list of all extensions (both active and inactive) that the broadcaster has installed. The user ID in the access token identifies the broadcaster.

        The user ID in the access token identifies the broadcaster.

        !!! info
            Requires a user access token that includes the `user:read:broadcast` or `user:edit:broadcast` scope.
            To include inactive extensions, you must include the `user:edit:broadcast` scope.

        Parameters
        ----------
        token_for: str
            User access token that includes the `user:read:broadcast` or `user:edit:broadcast` scope.
            To include inactive extensions, you must include the `user:edit:broadcast` scope.

        Returns
        -------
        list[UserExtension]
            List of UserExtension objects.
        """
        data = await self._http.get_user_extensions(token_for=token_for)
        return [Extension(d) for d in data["data"]]

    async def update_extensions(self, *, user_extensions: ActiveExtensions, token_for: str) -> ActiveExtensions:
        """
        Updates an installed extension's information. You can update the extension's activation state, ID, and version number.

        The user ID in the access token identifies the broadcaster whose extensions you're updating.

        !!! tip
            The best way to change an installed extension's configuration is to use [`fetch_active_extensions`][twitchio.user.fetch_active_extensions].
            You can then edit the approperiate extension within the `ActiveExtensions` model and pass it to this method.

        ??? info
            Requires a user access token that includes the `user:edit:broadcast` scope.

        Parameters
        ----------
        token_for: str
            User access token that includes the `user:edit:broadcast` scope.

        Returns
        -------
        ActiveExtensions
            ActiveExtensions object.
        """
        data = await self._http.put_user_extensions(user_extensions=user_extensions, token_for=token_for)
        return ActiveExtensions(data["data"])

    async def fetch_emotes(self, *, token_for: str | None = None) -> list[GlobalEmote]:
        """
        Fetches global emotes from the twitch API

        If you wish to fetch a specific broadcaster's chat badges use [`fetch_channel_emotes`][twitchio.user.fetch_channel_emotes]

        Returns
        --------
        list[twitchio.GlobalEmote]
            A list of GlobalEmotes objects.
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
        token_for: str | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Stream]:
        """
        Fetches live streams from the helix API

        Parameters
        -----------
        user_ids: list[int | str] | None
            user ids of people whose streams to fetch
        game_ids: list[int | str] | None
            game ids of streams to fetch
        user_logins: list[str] | None
            user login names of people whose streams to fetch
        languages: list[str] | None
            language for the stream(s). ISO 639-1 or two letter code for supported stream language
        type: Literal["all", "live"]
            One of `"all"` or `"live"`. Defaults to `"all"`. Specifies what type of stream to fetch.
        token_for: str | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Stream]
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
        token_for: str | None = None,
    ) -> Team:
        """
        Fetches information about a specific Twitch team. You must provide one of either `team_name` or `team_id`.

        Parameters
        -----------
        team_name: str
            The team name.
        team_id: str
            The team id.
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        twitchio.Team
            A Team object.
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
        token_for: str | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Game]:
        """
        Fetches information about all broadcasts on Twitch.

        Parameters
        -----------
        token_for: str | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Game]
        """

        first = max(1, min(100, first))

        return self._http.get_top_games(first=first, token_for=token_for, max_results=max_results)

    async def fetch_games(
        self,
        *,
        names: list[str] | None = None,
        ids: list[str] | None = None,
        igdb_ids: list[str] | None = None,
        token_for: str | None = None,
    ) -> list[Game]:
        """
        Fetches information about all broadcasts on Twitch.

        Parameters
        -----------
        token_for: str | None
            An optional user token to use instead of the default app token.

        Returns
        --------
        list[twitchio.Game]
            A list of Game objects
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
        token_for: str | None = None,
    ) -> Game | None:
        """
        Fetch a [`twitchio.Game`][twitchio.Game] object with the provided `name`, `id`, or `igdb_id`.

        One of `name`, `id`, or `igdb_id` must be provided.
        If more than one is provided or no parameters are provided, a `ValueError` will be raised.

        If no game is found, `None` will be returned.

        ??? tip
            See: [`Client.fetch_games`][twitchio.Client.fetch_games] to fetch multiple games at once.

            See: [`Client.fetch_top_games`][twitchio.Client.fetch_top_games] to fetch the top games currently being streamed.

        Parameters
        ----------
        name: str | None
            The name of the game to fetch.
        id: str | None
            The id of the game to fetch.
        igdb_id: str | None
            The igdb_id of the game to fetch.
        token_for: str | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        Game | None
            The Game object if found, otherwise `None`.

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
        if not data["data"]:
            return None

        return Game(data["data"][0], http=self._http)

    async def fetch_users(
        self, *, ids: list[str | int] | None = None, logins: list[str] | None = None, token_for: str | None = None
    ) -> list[User]:
        """
        Fetch information about one or more users.

        !!! info
            You may look up users using their user ID, login name, or both but the sum total of the number of users you may look up is 100.
            For example, you may specify 50 IDs and 50 names or 100 IDs or names, but you cannot specify 100 IDs and 100 names.

            If you don't specify IDs or login names but provide a user token, the request returns information about the user in the access token.

            To include the user's verified email address in the response, you must use a user access token that includes the `user:read:email` scope.

        Parameters
        ----------
        ids: list[str | int] | None
            The ids of the users to fetch information about.
        logins: list[str] | None
            The login names of the users to fetch information about.
        token_for: str | None
            Optional token, with `user:read:email` scope, to request the user's verified email address.

        Returns
        -------
        list[User]
            List of User objects.

        Raises
        ------
        ValueError
            The combined number of 'ids' and 'logins' must not exceed 100 elements.
        """

        if (len(ids or []) + len(logins or [])) > 100:
            raise ValueError("The combined number of 'ids' and 'logins' must not exceed 100 elements.")

        data = await self._http.get_users(ids=ids, logins=logins, token_for=token_for)
        return [User(d, http=self._http) for d in data["data"]]

    def search_categories(
        self,
        query: str,
        *,
        token_for: str | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Game]:
        """
        Searches Twitch categories.

        Parameters
        -----------
        query: str
            The query to search for.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Game]
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
        token_for: str | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[SearchChannel]:
        """
        Searches Twitch channels that match the specified query and have streamed content within the past 6 months.

        !!! info
            If `live` is set to False (default) then the query will look to match broadcaster login names.
            If `live` is set to True then the query will match on the broadcaster login names and category names.

            To match, the beginning of the broadcaster's name or category must match the query string.
            The comparison is case insensitive. If the query string is angel_of_death, it matches all names that begin with angel_of_death.
            However, if the query string is a phrase like angel of death, it matches to names starting with angelofdeath or names starting with angel_of_death.

        Parameters
        -----------
        query: str
            The query to search for.
        live: bool
            Whether to return live channels only.
            Default is False.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.SearchChannel]
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
        user_id: str | int | None = None,
        game_id: str | int | None = None,
        language: str | None = None,
        period: Literal["all", "day", "month", "week"] = "all",
        sort: Literal["time", "trending", "views"] = "time",
        type: Literal["all", "archive", "highlight", "upload"] = "all",
        first: int = 20,
        max_results: int | None = None,
        token_for: str | None = None,
    ) -> HTTPAsyncIterator[Video]:
        """
        Fetch a list of [`twitchio.Video`][twitchio.Video] objects with the provided `ids`, `user_id` or `game_id`.

        One of `ids`, `user_id` or `game_id` must be provided.
        If more than one is provided or no parameters are provided, a `ValueError` will be raised.

        Parameters
        ----------
        ids: list[str | int] | None
            A list of video IDs to fetch.
        user_id: str | int | None
            The ID of the user whose list of videos you want to get.
        game_id: str | int | None
            The igdb_id of the game to fetch.
        language: str | None
        period: Literal["all", "day", "month", "week"]
        sort: Literal["time", "trending", "views"]
        type: Literal["all", "archive", "highlight", "upload"]
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.
        token_for: str | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        list[Video]
            A list of Video objects if found.

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

    async def delete_videos(self, *, ids: list[str | int], token_for: str) -> list[str]:
        """
        Deletes one or more videos. You may delete past broadcasts, highlights, or uploads.

        This requires a user token with the scope `channel:manage:videos`.
        The limit is to delete 5 ids at a time, so if more than 5 ids are provided we will attempt to delete them in chunks.
        If any of the videos fail to delete in the request then none will be deleted in that chunk.

        Parameters
        ----------
        ids: list[str | int] | None
            A list of video IDs to fetch.
        token_for: str
            User token with the scope `channel:manage:videos`.

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
        token_for: str,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[VideoMarkers]:
        """
        Fetches markers from the user's most recent stream or from the specified VOD/video.
        A marker is an arbitrary point in a live stream that the broadcaster or editor marked, so they can return to that spot later to create video highlights

        !!! info
            To fetch by user please use [`fetch_stream_markers`][twitchio.user.PartialUser.fetch_stream_markers]

        ??? note
            Requires a user access token that includes the `user:read:broadcast` or `channel:manage:broadcast scope`.

        Parameters
        ----------
        video_id: str
            A video on demand (VOD)/video ID. The request returns the markers from this VOD/video.
            The user in the access token must own the video or the user must be one of the broadcaster's editors.
        token_for: str
            User access token that includes the `user:read:broadcast` or `channel:manage:broadcast scope`.
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[VideoMarkers]
            HTTPAsyncIterator of VideoMarkers objects.
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
        token_for: str | None = None,
        ids: list[str] | None = None,
        user_id: str | int | None = None,
        game_id: str | None = None,
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Entitlement]:
        """
        Fetches an organization's list of entitlements that have been granted to a game, a user, or both.

        !!! info
            Entitlements returned in the response body data are not guaranteed to be sorted by any field returned by the API.
            To retrieve `CLAIMED` or `FULFILLED` entitlements, use the fulfillment_status query parameter to filter results.
            To retrieve entitlements for a specific game, use the game_id query parameter to filter results.

        !!! note
            Requires an app access token or user access token. The client ID in the access token must own the game.

        | Access token type | Parameter          | Description                                                                                                           |
        |-------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
        | App               | None               | If you don't specify request parameters, the request returns all entitlements that your organization owns.             |
        | App               | user_id            | The request returns all entitlements for any game that the organization granted to the specified user.                |
        | App               | user_id, game_id   | The request returns all entitlements that the specified game granted to the specified user.                            |
        | App               | game_id            | The request returns all entitlements that the specified game granted to all entitled users.                            |
        | User              | None               | If you don't specify request parameters, the request returns all entitlements for any game that the organization granted to the user identified in the access token. |
        | User              | user_id            | Invalid.                                                                                                              |
        | User              | user_id, game_id   | Invalid.                                                                                                              |
        | User              | game_id            | The request returns all entitlements that the specified game granted to the user identified in the access token.      |


        Parameters
        ----------
        token_for: str | None
            User access token. The client ID in the access token must own the game.
            If not provided then default app token is used.
            `The client ID in the access token must own the game.`
        ids: list[str] | None
            List of entitlement ids that identifies the entitlements to get.
        user_id: str | int | None
            User that was granted entitlements.
        game_id: str | None
            An ID that identifies a game that offered entitlements.
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None
            The entitlement's fulfillment status. Used to filter the list to only those with the specified status.
            Possible values are: `CLAIMED` and `FULFILLED`.
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 1000 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[Entitlement]
            HTTPAsyncIterator of Entitlement objects.

        Raises
        ------
        ValueError
            You may specifiy a maximum of 100 ids.
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
        token_for: str | None = None,
    ) -> list[EntitlementStatus]:
        """
        Updates the Drop entitlement's fulfillment status.

        !!! note
            Requires an app access token or user access token. The client ID in the access token must own the game.

        | Access token type | Data that's updated                                                                                                            |
        |-------------------|--------------------------------------------------------------------------------------------------------------------------------|
        | App               | Updates all entitlements with benefits owned by the organization in the access token.                                          |
        | User              | Updates all entitlements owned by the user in the access win the access token and where the benefits are owned by the organization in the access token. |


        Parameters
        ----------
        ids: list[str] | None
            A list of IDs that identify the entitlements to update. You may specify a maximum of 100 IDs.
        fulfillment_status: Literal[""CLAIMED", "FULFILLED"] | None
            The fulfillment status to set the entitlements to.
            Possible values are: `CLAIMED` and `FULFILLED`.
        token_for: str | None
            User access token. The client ID in the access token must own the game.

        Returns
        -------
        list[EntitlementStatus]
            List of EntitlementStatus objects.

        Raises
        ------
        ValueError
            You may specifiy a maximum of 100 ids.
        """
        if ids is not None and len(ids) > 100:
            raise ValueError("You may specifiy a maximum of 100 ids.")

        from .models.entitlements import EntitlementStatus

        data = await self._http.patch_drop_entitlements(ids=ids, fulfillment_status=fulfillment_status, token_for=token_for)
        return [EntitlementStatus(d) for d in data["data"]]

    async def _subscribe(
        self,
        method: TransportMethod,
        payload: SubscriptionPayload,
        as_bot: bool = False,
        token_for: str | None = None,
        socket_id: str | None = None,
        callback_url: str | None = None,
        eventsub_secret: str | None = None,
    ) -> SubscriptionResponse | None:
        if method is TransportMethod.WEBSOCKET:
            return await self.subscribe_websocket(payload=payload, as_bot=as_bot, token_for=token_for, socket_id=socket_id)

        elif method is TransportMethod.WEBHOOK:
            return await self.subscribe_webhook(
                payload=payload,
                as_bot=as_bot,
                token_for=token_for,
                callback_url=callback_url,
                eventsub_secret=eventsub_secret,
            )

    async def subscribe_websocket(
        self,
        *,
        payload: SubscriptionPayload,
        as_bot: bool = False,
        token_for: str | None = None,
        socket_id: str | None = None,
    ) -> SubscriptionResponse | None:
        # TODO: Complete docs...
        """Subscribe to an EventSub Event via Websockets.

        !!! tip
            See: ... for more information and recipes on using eventsub.

        Parameters
        ----------
        payload: SubscriptionPayload
            The payload which should include the required conditions to subscribe to.
        as_bot: bool
            Whether to subscribe to this event using the token associated with the provided
            [`bot_id`][twitchio.Client.bot_id]. If this is set to `True` and `bot_id` has not been set, this method will
            raise `ValueError`. Defaults to `False` on [`Client`][twitchio.Client] but will default to `True` on
            [`Bot`][twitchio.ext.commands.Bot].
        token_for: str | None
            An optional user ID to use to subscribe. If `as_bot` is passed, this is always the token associated with the
            [`bot_id`][twitchio.Client.bot_id] account. Defaults to `None`.
        socket_id: str | None
            An optional `str` corresponding to an exisiting and connected websocket session, to use for this subscription.
            You usually do not need to pass this parameter as TwitchIO delegates subscriptions to websockets as needed.
            Defaults to `None`.

        Returns
        -------
        SubscriptionResponse
            ...

        Raises
        ------
        ValueError
            One of the provided parameters is incorrect or incompatible.
        HTTPException
            An error was raised while making the subscription request to Twitch.
        """
        if as_bot and not self.bot_id:
            raise ValueError("Client is missing 'bot_id'. Provide a 'bot_id' in the Client constructor.")

        elif as_bot:
            token_for = self.bot_id

        if not token_for:
            raise ValueError("A valid User Access Token must be passed to subscribe to eventsub over websocket.")

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
        *,
        payload: SubscriptionPayload,
        as_bot: bool = False,
        token_for: str | None = None,
        callback_url: str | None = None,
        eventsub_secret: str | None = None,
    ) -> SubscriptionResponse | None:
        # TODO: Complete docs...
        """Subscribe to an EventSub Event via Webhook.

        !!! tip
            For more information on how to setup your bot with webhooks, see: ...

        ??? warning
            Usually you wouldn't use webhooks to subscribe to the
            [`Channel Chat Message`][twitchio.eventsub.ChatMessageSubscription] subscription.
            Consider using [`.subscribe_websocket`][twitchio.Client.subscribe_websocket] for this subscription.

        Parameters
        ----------
        payload: SubscriptionPayload
            The payload which should include the required conditions to subscribe to.
        as_bot: bool
            Whether to subscribe to this event using the token associated with the provided
            [`bot_id`][twitchio.Client.bot_id]. If this is set to `True` and `bot_id` has not been set, this method will
            raise `ValueError`. Defaults to `False` on [`Client`][twitchio.Client] but will default to `True` on
            [`Bot`][twitchio.ext.commands.Bot].
        token_for: str | None
            An optional user ID to use to subscribe. If `as_bot` is passed, this is always the token associated with the
            [`bot_id`][twitchio.Client.bot_id] account. Defaults to `None`.
        callback_url: str | None
            An optional url to use as the webhook `callback_url` for this subscription. If you are using one of the built-in
            web adapters, you should not need to set this. See: (web adapter docs link) for more info.
        eventsub_secret: str | None
            An optional `str` to use as the eventsub_secret, which is required by Twitch. If you are using one of the
            built-in web adapters, you should not need to set this. See: (web adapter docs link) for more info.

        Returns
        -------
        SubscriptionResponse
            ...

        Raises
        ------
        ValueError
            One of the provided parameters is incorrect or incompatible.
        HTTPException
            An error was raised while making the subscription request to Twitch.
        """
        if as_bot and not self.bot_id:
            raise ValueError("Client is missing 'bot_id'. Provide a 'bot_id' in the Client constructor.")

        elif as_bot:
            token_for = self.bot_id

        if not token_for:
            raise ValueError("A valid User Access Token must be passed to subscribe to eventsub over websocket.")

        if not self._adapter and not callback_url:
            raise ValueError(
                "Either a 'twitchio.web' Adapter or 'callback_url' should be provided for webhook based eventsub."
            )

        callback: str | None = self._adapter.eventsub_url or callback_url
        if not callback:
            raise ValueError(
                "A callback URL must be provided when subscribing to events via Webhook. "
                "Use 'twitchio.web' Adapter or provide a 'callback_url'."
            )

        secret: str | None = self._adapter._eventsub_secret or eventsub_secret
        if not secret:
            raise ValueError("An eventsub secret must be provided when subscribing to events via Webhook. ")

        if secret and not 10 <= len(secret) <= 100:
            raise ValueError("The 'eventsub_secret' must be between 10 and 100 characters long.")

        type_ = SubscriptionType(payload.type)
        version: str = payload.version
        transport: SubscriptionCreateTransport = {"method": "webhook", "callback": callback, "secret": secret}

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
                logger.warning(
                    "Disregarding HTTPException in subscribe: "
                    "A subscription already exists for the specified event type and condition combination: '%s' and '%s'",
                    payload.type,
                    str(payload.condition),
                )
                return

            raise e
        return resp

    async def event_oauth_authorized(self, payload: UserTokenPayload) -> None:
        await self.add_token(payload["access_token"], payload["refresh_token"])

    def doc_test(self, thing: int = 1) -> int:
        """
        This is a test method to test and view certain elements of the mkdocs style documentation.

        For more information see: [`Material Docs`](https://squidfunk.github.io/mkdocs-material/reference/)

        **Linking to another method/object:** [`twitchio.Client.fetch_channels`][]

        **Linking to another method/object with custom name:** [`fetch_channels`][twitchio.Client.fetch_channels]

        !!! warning
            This is a warning block.

        !!! note
            This is a note block.

        !!! tip
            This is a tip block.

        !!! danger
            This is a danger block.

        !!! example
            This is an example block.

        !!! info
            This is an info block.

        !!! question
            This is a question block.

        !!! quote
            This is a quote block.

        !!! abstract
            This is an abstract block.

        !!! note "This is a block with a custom title xD"
            This is a custom note block.

        !!! warning "Don't need content!"

        Pythonista also adds a version block:

        !!! version "3.0.0"
            **Added** the [`fetch_channels`][twitchio.Client.fetch_channels] method.

        **Tables:**

        | Example          | Some other col |
        | -----------      | -------------- |
        | This is a test   | 123            |
        | This is a test   | 321            |

        **Pythonista Tags:**
        :fontawesome-solid-triangle-exclamation:{ .icon-warning .pythonista-tag title="Put a message here" }
        :fontawesome-solid-check:{ .icon-check .pythonista-tag title="Put a message here" }
        :fontawesome-solid-question:{ .icon-unknown .pythonista-tag title="Put a message here" }


        **Code Blocks:**

        ```python
        # This is a python code block
        print("Hello World!")
        ```


        **Content Blocks:**

        === "Some Code"

            ```python
            # This is a python code block
            print("Hello World!")
            ```

        === "Some Other Code"

            ```python
            import twitchio

            client = twitchio.Client()
            ```

        === "Wow!"

            Cool!


        **Emojis:**

        :sweat_smile: -  Mainly used if we need an icon for something.


        **Images:**

        ![Some Image](https://dummyimage.com/600x400/eee/aaa)


        **Lists:**

        - This is a list item 1
        - This is a list item 2
            * An inner list item
            * Another inner list item
        - This is a list item 3

        **Checklists:**

        - [x] This is a checked list item
        - [ ] This is an unchecked list item
            * [x] An inner checked list item
            * [ ] An inner unchecked list item


        **Tool Tips:**

        [Some ToolTip](# "This is a tooltip")

        :octicons-bug-24:{ title="This is a tooltip with an icon" } <-- Hover little bug guy


        **Abbreviations:**

        If TIO3 defined in the docstring like below, it will be linked to the abbreviation.

        *[TIO3]: TwitchIO 3.0 - The latest version of TwitchIO.


        **Annotations:**

        These are supper annoying to add to the docstring (1), but they are useful sometimes I guess... (2)
        { .annotate }

        1. Directly after the block you want to annotate, add the annotation. These sometimes break in certain blocks.
        2. If you don't add the { .annotate } to the end of the block, the annotation will not be added.

        <p class="pythonista-docs-heading">Attributes</p>
        Attributes
        ----------
        test: int
            This should link to test attribute and attribute type. You wouldn't see this in a method signature.
            Properties don't need to be included in this attributes section.

            There is no heading for the attributes section, because mkdocs-strings adds it with summaries on the class.

            If for some reason we need the Attributes heading, we can add it manually as seen above with HTML.

        Returns
        -------
        int
            The same as numpy.
        """
        ...
