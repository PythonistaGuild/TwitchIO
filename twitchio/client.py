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
from typing import TYPE_CHECKING, Any, Literal

from twitchio.http import HTTPAsyncIterator

from .authentication import ManagedHTTPClient, Scopes
from .conduits import Conduit, ConduitPool
from .models.bits import Cheermote, ExtensionTransaction
from .models.ccls import ContentClassificationLabel
from .models.channels import ChannelInfo
from .models.chat import ChatBadge, ChatterColor, EmoteSet, GlobalEmote
from .models.games import Game
from .models.teams import Team
from .payloads import EventErrorPayload
from .web import AiohttpAdapter


if TYPE_CHECKING:
    import datetime
    from collections.abc import Awaitable, Callable, Coroutine

    import aiohttp
    from typing_extensions import Self, Unpack

    from .authentication import ClientCredentialsPayload, ValidateTokenPayload
    from .http import HTTPAsyncIterator
    from .models.clips import Clip
    from .models.search import SearchChannel
    from .models.streams import Stream
    from .models.videos import Video
    from .types_.options import ClientOptions
    from .types_.responses import ConduitPayload


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
    """

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        **options: Unpack[ClientOptions],
    ) -> None:
        redirect_uri: str | None = options.get("redirect_uri", None)
        scopes: Scopes | None = options.get("scopes", None)
        session: aiohttp.ClientSession | None = options.get("session", None)

        self._http = ManagedHTTPClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
        )

        adapter: Any = options.get("adapter", None) or AiohttpAdapter
        self._adapter: Any = adapter(client=self)

        # Conduits...
        self._pool: ConduitPool = ConduitPool(client=self)

        # Event listeners...
        # Cog listeners should be partials with injected self...
        # When unloading/reloading cogs, the listeners should be removed and re-added to ensure upto date state...
        self._listeners: dict[str, set[Callable[..., Coroutine[Any, Any, None]]]] = defaultdict(set)

        # TODO: Temp logic for testing...
        self._blocker: asyncio.Event = asyncio.Event()
        self._login_called: bool = False
        self._dump_tokens: bool = True
        self._has_closed: bool = False

    @property
    def pool(self) -> ConduitPool:
        return self._pool

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

    async def _dispatch(
        self, listener: Callable[..., Coroutine[Any, Any, None]], *, original: Any | None = None
    ) -> None:
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
        # TODO: Proper payload type...
        name: str = "event_" + event.removeprefix("event_")

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

            logger.info("Generated App Token for Client: %s", validated.client_id)

        await self.load_tokens()

        self._http._app_token = token
        await self.setup_hook()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start(self, token: str | None = None, *, with_adapter: bool = True, dump_tokens: bool = True) -> None:
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
        dump_tokens: bool
            Whether to call the [`.dump_tokens`][twitchio.Client.dump_tokens] method when the Client shuts down.
            Defaults to `True`.
        """
        if self._has_closed:
            raise RuntimeError("Can not start an already closed Client.")

        self._dump_tokens = dump_tokens

        await self.login(token=token)

        if with_adapter:
            await self._adapter.run()

        await self._block()

    async def _block(self) -> None:
        # TODO: Temp METHOD for testing...

        try:
            await self._blocker.wait()
        except KeyboardInterrupt:
            await self.close()

    async def close(self) -> None:
        if self._has_closed:
            return

        self._has_closed = True

        if self._dump_tokens:
            await self.dump_tokens()

        await self._http.close()

        if self._adapter._runner_task is not None:
            try:
                await self._adapter.close()
            except Exception:
                pass

        # TODO: Temp logic for testing...
        self._blocker.set()

    async def add_token(self, token: str, refresh: str) -> None:
        await self._http.add_token(token, refresh)

    async def load_tokens(self, path: str | None = None, /) -> None:
        await self._http.load_tokens(name=path)

    async def dump_tokens(self, path: str | None = None, /) -> None:
        """
        Method which dumps all the added OAuth tokens currently managed by this Client.

        !!! info
            By default this method dumps to a JSON file named `".tio.tokens.json"`.

        You can override this method to implement your own custom logic, such as saving tokens to a database.

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
        token_for : str | None, optional
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
        self, user_ids: list[str | int], *, token_for: str | None = None
    ) -> list[ChatterColor]:
        """
        Fetches the color of a chatter.

        .. versionchanged:: 3.0
            Removed the ``token`` parameter. Added the ``token_for`` parameter.

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

        data = await self._http.get_chatters_color(user_ids, token_for)
        return [ChatterColor(d, http=self._http) for d in data["data"] if data]

    async def fetch_channels(
        self, broadcaster_ids: list[str | int], *, token_for: str | None = None
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
        self, *, broadcaster_id: int | str | None = None, token_for: str | None = None
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

    async def fetch_clips(
        self,
        *,
        broadcaster_id: str | None = None,
        game_id: str | None = None,
        clip_ids: list[str] | None = None,
        started_at: datetime.datetime | None = None,
        ended_at: datetime.datetime | None = None,
        is_featured: bool | None = None,
        token_for: str | None = None,
        first: int = 20,
    ) -> HTTPAsyncIterator[Clip]:
        """
        Fetches clips by clip id or game id.

        Parameters
        -----------
        broadcaster_id: str
            An ID of a broadcaster to fetch clips from.
        game_id: Optional[list[str | int]]
            A game id to fetch clips from.
        clip_ids: list[str] | None
            A list of specific clip IDs to fetch.
            Maximum amount you can request is 100.
        started_at: datetime.datetime`
            The start date used to filter clips.
        ended_at: datetime.datetime`
            The end date used to filter clips. If not specified, the time window is the start date plus one week.
        token_for: str | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Clip]
        """

        provided: int = len([v for v in (broadcaster_id, game_id, clip_ids) if v])
        if provided > 1:
            raise ValueError("Only one of 'name', 'id', or 'igdb_id' can be provided.")
        elif provided == 0:
            raise ValueError("One of 'name', 'id', or 'igdb_id' must be provided.")

        first = max(1, min(100, first))

        return await self._http.get_clips(
            broadcaster_id=broadcaster_id,
            game_id=game_id,
            clip_ids=clip_ids,
            first=first,
            started_at=started_at,
            ended_at=ended_at,
            is_featured=is_featured,
            token_for=token_for,
        )

    async def fetch_extension_transactions(
        self, extension_id: str, *, ids: list[str] | None = None, first: int = 20
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

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.ExtensionTransaction]
        """

        first = max(1, min(100, first))

        if ids and len(ids) > 100:
            raise ValueError("You can only provide a mximum of 100 IDs")

        return await self._http.get_extension_transactions(
            extension_id=extension_id,
            ids=ids,
            first=first,
        )

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

    async def fetch_streams(
        self,
        *,
        user_ids: list[int | str] | None = None,
        game_ids: list[int | str] | None = None,
        user_logins: list[int | str] | None = None,
        languages: list[str] | None = None,
        type: Literal["all", "live"] = "all",
        token_for: str | None = None,
        first: int = 20,
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
            One of ``"all"`` or ``"live"``. Defaults to ``"all"``. Specifies what type of stream to fetch.
        token_for: str | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Stream]
        """

        first = max(1, min(100, first))

        return await self._http.get_streams(
            first=first,
            game_ids=game_ids,
            user_ids=user_ids,
            user_logins=user_logins,
            languages=languages,
            type=type,
            token_for=token_for,
        )

    async def fetch_team(
        self, *, team_name: str | None = None, team_id: str | None = None, token_for: str | None = None
    ) -> Team:
        """
        Fetches information about a specific Twitch team. You must provide one of either ``team_name`` or ``team_id``.

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

    async def fetch_top_games(
        self,
        *,
        token_for: str | None = None,
        first: int = 20,
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

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Game]
        """

        first = max(1, min(100, first))

        return await self._http.get_top_games(
            first=first,
            token_for=token_for,
        )

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

    async def search_categories(
        self, query: str, *, token_for: str | None = None, first: int = 20
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
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Game]
        """

        first = max(1, min(100, first))

        return await self._http.get_search_categories(
            query=query,
            first=first,
            token_for=token_for,
        )

    async def search_channels(
        self, query: str, *, live: bool = False, token_for: str | None = None, first: int = 20
    ) -> HTTPAsyncIterator[SearchChannel]:
        """
        Searches Twitch categories.

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
        token_for: str | None
            An optional user token to use instead of the default app token.
        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.SearchChannel]
        """

        first = max(1, min(100, first))

        return await self._http.get_search_channels(
            query=query,
            first=first,
            live=live,
            token_for=token_for,
        )

    async def fetch_videos(
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

        return await self._http.get_videos(
            ids=ids,
            user_id=user_id,
            game_id=game_id,
            language=language,
            period=period,
            sort=sort,
            type=type,
            first=first,
            token_for=token_for,
        )

    async def delete_videos(self, *, ids: list[str | int], token_for: str) -> list[str]:
        """
        Deletes one or more videos. You may delete past broadcasts, highlights, or uploads.

        This requires a user token with the scope ``channel:manage:videos``.
        The limit is to delete 5 ids at a time, so if more than 5 ids are provided we will attempt to delete them in chunks.
        If any of the videos fail to delete in the request then none will be deleted in that chunk.

        Parameters
        ----------
        ids: list[str | int] | None
            A list of video IDs to fetch.
        token_for: str
            User token with the scope ``channel:manage:videos``.

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

    async def _create_conduit(self, shard_count: int, /) -> list[Conduit]:
        data: ConduitPayload = await self._http.create_conduit(shard_count)
        return [Conduit(data=c, pool=self._pool) for c in data["data"]]

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
