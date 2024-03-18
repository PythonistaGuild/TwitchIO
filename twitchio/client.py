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
from .models import (
    ChannelInfo,
    ChatterColor,
    CheerEmote,
    Clip,
    ContentClassificationLabel,
    Game,
    GlobalEmote,
    SearchChannel,
    Stream,
    Team,
)
from .payloads import EventErrorPayload
from .web import AiohttpAdapter, WebAdapter


if TYPE_CHECKING:
    import datetime
    from collections.abc import Awaitable, Callable, Coroutine

    import aiohttp
    from typing_extensions import Self, Unpack

    from .authentication import ClientCredentialsPayload
    from .http import HTTPAsyncIterator
    from .types_.options import ClientOptions


logger: logging.Logger = logging.getLogger(__name__)


class Client:
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

        adapter: type[WebAdapter] = options.get("adapter", None) or AiohttpAdapter
        self._adapter: WebAdapter = adapter(client=self)

        # Event listeners...
        # Cog listeners should be partials with injected self...
        # When unloading/reloading cogs, the listeners should be removed and re-added to ensure upto date state...
        self._listeners: dict[str, set[Callable[..., Coroutine[Any, Any, None]]]] = defaultdict(set)

        # TODO: Temp logic for testing...
        self._blocker: asyncio.Event = asyncio.Event()

    async def event_error(self, payload: EventErrorPayload) -> None:
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

    async def setup_hook(self) -> None: ...

    async def login(self, *, token: str | None = None) -> None:
        if not token:
            payload: ClientCredentialsPayload = await self._http.client_credentials_token()
            token = payload.access_token

        self._http._app_token = token
        await self.setup_hook()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def start(self, token: str | None = None, *, with_adapter: bool = True) -> None:
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

    def add_listener(self, listener: Callable[..., Coroutine[Any, Any, None]], *, event: str | None = None) -> None:
        name: str = event or listener.__name__

        if not name.startswith("event_"):
            raise ValueError('Listener and event names must start with "event_".')

        if name == "event_":
            raise ValueError('Listener and event names cannot be named "event_".')

        if not asyncio.iscoroutinefunction(listener):
            raise ValueError("Listeners and Events must be coroutines.")

        self._listeners[name].add(listener)

    async def fetch_chatters_color(self, user_ids: list[str | int], token_for: str | None = None) -> list[ChatterColor]:
        """|coro|

        Fetches the color of a chatter.

        .. versionchanged:: 3.0
            Removed the ``token`` parameter. Added the ``token_for`` parameter.

        Parameters
        -----------
        user_ids: List[Union[:class:`int`, :class:`str]]
            List of user ids to fetch the colors for.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        Returns
        --------
            list[:class:`twitchio.ChatterColor`]
        """
        if len(user_ids) > 100:
            raise ValueError("Maximum of 100 user_ids")

        data = await self._http.get_chatters_color(user_ids, token_for)
        return [ChatterColor(d) for d in data["data"] if data]

    async def fetch_channels(self, broadcaster_ids: list[str | int], token_for: str | None = None) -> list[ChannelInfo]:
        """|coro|

        Retrieve channel information from the API.

        Parameters
        -----------
        broadcaster_ids: List[Union[:class:`int`, :class:`str]]
            A list of channel IDs to request from API.
            You may specify a maximum of 100 IDs.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        Returns
        --------
            list[:class:`twitchio.ChannelInfo`]
        """
        if len(broadcaster_ids) > 100:
            raise ValueError("Maximum of 100 broadcaster_ids")

        data = await self._http.get_channels(broadcaster_ids, token_for)
        return [ChannelInfo(d) for d in data["data"]]

    async def fetch_global_emotes(self, token_for: str | None = None) -> list[GlobalEmote]:
        """|coro|

        Fetches global emotes from the twitch API

        Returns
        --------
        List[:class:`twitchio.GlobalEmote`]
        """
        data = await self._http.get_global_emotes(token_for)
        return [GlobalEmote(d) for d in data["data"]]

    async def fetch_cheermotes(
        self, broadcaster_id: int | str | None = None, token_for: str | None = None
    ) -> list[CheerEmote]:
        """|coro|

        Fetches a list of Cheermotes that users can use to cheer Bits in any Bits-enabled channel's chat room. Cheermotes are animated emotes that viewers can assign Bits to.
        If a broadcaster_id is not specified then only global cheermotes will be returned.
        If the broadcaster uploaded Cheermotes, the type attribute will be set to channel_custom.

        Parameters
        -----------
        broadcaster_id: Optional[Union[:class:`int`, :class:`str]]
            The id of the broadcaster who has uploaded Cheermotes.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.

        Returns
        --------
        List[:class:`twitchio.CheerEmote`]
        """
        data = await self._http.get_cheermotes(str(broadcaster_id) if broadcaster_id else None, token_for)
        return [CheerEmote(d) for d in data["data"]]

    async def fetch_content_classification_labels(
        self, locale: str = "en-US", *, token_for: str | None = None
    ) -> list[ContentClassificationLabel]:
        """|coro|

        Fetches information about Twitch content classification labels.

        Parameters
        -----------
        locale: :class:`str`
            Locale for the Content Classification Labels.

        Returns
        --------
        List[:class:`twitchio.ContentClassificationLabel`]
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
        """|coro|

        Fetches clips by clip id or game id.

        Parameters
        -----------
        broadcaster_id: :class:`str`
            An ID of a broadcaster to fetch clips from.
        game_id: Optional[List[Union[:class:`int`, :class:`str`]]]
            A game id to fetch clips from.
        clip_ids: Optional[List[:class:`str`]]
            A list of specific clip IDs to fetch.
            Maximum amount you can request is 100.
        started_at: :class:`datetime.datetime`
            The start date used to filter clips.
        ended_at: :class:`datetime.datetime`
            The end date used to filter clips. If not specified, the time window is the start date plus one week.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        first: :class:`int`
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        :class:`~twitchio.HTTPAsyncIterator`[:class:`~twitchio.Clip`]
        """

        if sum(x is not None for x in [broadcaster_id, game_id, clip_ids]) > 1:
            raise ValueError("The parameters 'broadcaster_id', 'game_id', and 'ids' are mutually exclusive.")

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
        """|coro|

        Fetches live streams from the helix API

        Parameters
        -----------
        user_ids: Optional[List[Union[:class:`int`, :class:`str`]]]
            user ids of people whose streams to fetch
        game_ids: Optional[List[Union[:class:`int`, :class:`str`]]]
            game ids of streams to fetch
        user_logins: Optional[List[:class:`str`]]
            user login names of people whose streams to fetch
        languages: Optional[List[:class:`str`]]
            language for the stream(s). ISO 639-1 or two letter code for supported stream language
        type: Literal["all", "live"]
            One of ``"all"`` or ``"live"``. Defaults to ``"all"``. Specifies what type of stream to fetch.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        first: :class:`int`
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        :class:`~twitchio.HTTPAsyncIterator`[:class:`~twitchio.Stream`]
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
        """|coro|

        Fetches information about a specific Twitch team. You must provide one of either ``team_name`` or ``team_id``.

        Parameters
        -----------
        team_name: :class:`str`
            The team name.
        team_id: :class:`str`
            The team id.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        Returns
        --------
            :class:`~twitchio.Team`
        """

        if team_name and team_id:
            raise ValueError("Only one of 'team_name' or 'team_id' should be provided, not both.")

        data = await self._http.get_teams(
            team_name=team_name,
            team_id=team_id,
            token_for=token_for,
        )

        return Team(data)

    async def fetch_top_games(
        self,
        *,
        token_for: str | None = None,
        first: int = 20,
    ) -> HTTPAsyncIterator[Game]:
        """|coro|

        Fetches information about all broadcasts on Twitch.

        Parameters
        -----------
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        first: :class:`int`
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        :class:`~twitchio.HTTPAsyncIterator`[:class:`~twitchio.Game`]
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
        """|coro|

        Fetches information about all broadcasts on Twitch.

        Parameters
        -----------
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        first: :class:`int`
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        :class:`List`[:class:`~twitchio.Game`]
        """

        data = await self._http.get_games(
            names=names,
            ids=ids,
            igdb_ids=igdb_ids,
            token_for=token_for,
        )

        return [Game(d) for d in data["data"]]

    async def search_categories(
        self, query: str, *, token_for: str | None = None, first: int = 20
    ) -> HTTPAsyncIterator[Game]:
        """|coro|

        Searches Twitch categories.

        Parameters
        -----------
        query: :class:`str`
            The query to search for.
        first: :class:`int`
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        Returns
        --------
            :class:`~twitchio.HTTPAsyncIterator`[:class:`~twitchio.Game`]
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
        """|coro|

        Searches Twitch categories.

        Parameters
        -----------
        query: :class:`str`
            The query to search for.
        live: :class:`bool`
            Whether to return live channels only.
            Default is False.
        first: :class:`int`
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        token_for: Optional[:class:`str`]
            An optional User OAuth token to use instead of the default app token.
        Returns
        --------
            :class:`~twitchio.HTTPAsyncIterator`[:class:`~twitchio.SearchChannel`]
        """

        first = max(1, min(100, first))

        return await self._http.get_search_channels(
            query=query,
            first=first,
            live=live,
            token_for=token_for,
        )
