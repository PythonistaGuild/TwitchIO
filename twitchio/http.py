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
import copy
import datetime
import logging
import sys
import urllib.parse
from collections import deque
from collections.abc import AsyncIterator, Callable
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, Self, TypeAlias, TypeVar, Unpack

import aiohttp

from . import __version__
from .exceptions import HTTPException
from .models.analytics import ExtensionAnalytics, GameAnalytics
from .models.bits import ExtensionTransaction
from .models.channel_points import CustomRewardRedemption
from .models.channels import ChannelFollowerEvent, ChannelFollowers, FollowedChannels, FollowedChannelsEvent
from .models.charity import CharityDonation
from .models.chat import Chatters, UserEmote
from .models.clips import Clip
from .models.entitlements import Entitlement
from .models.eventsub_ import ConduitShard, EventsubSubscription, EventsubSubscriptions
from .models.games import Game
from .models.hype_train import HypeTrainEvent
from .models.moderation import BannedUser, BlockedTerm, UnbanRequest
from .models.polls import Poll
from .models.predictions import Prediction
from .models.schedule import Schedule
from .models.search import SearchChannel
from .models.streams import Stream, VideoMarkers
from .models.subscriptions import BroadcasterSubscription, BroadcasterSubscriptions
from .models.videos import Video
from .user import ActiveExtensions, PartialUser
from .utils import MISSING, Colour, _from_json, date_to_datetime_with_z, handle_user_ids, url_encode_datetime  # type: ignore


if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from twitchio.types_.responses import ConduitPayload

    from .assets import Asset
    from .eventsub.enums import SubscriptionType
    from .models.channel_points import CustomReward
    from .models.moderation import AutomodCheckMessage, AutomodSettings
    from .types_.conduits import Condition, ShardData, ShardUpdateRequest
    from .types_.eventsub import (
        SubscriptionCreateRequest,
        SubscriptionCreateTransport,
        SubscriptionResponse,
        _SubscriptionData,
    )
    from .types_.requests import APIRequestKwargs, HTTPMethod, ParamMapping
    from .types_.responses import (
        AddBlockedTermResponse,
        AdScheduleResponse,
        AutomodSettingsResponse,
        BannedUsersResponseData,
        BanUserResponse,
        BitsLeaderboardResponse,
        BlockedTermsResponseData,
        BroadcasterSubscriptionsResponseData,
        ChannelChatBadgesResponse,
        ChannelEditorsResponse,
        ChannelEmotesResponse,
        ChannelFollowersResponseData,
        ChannelInformationResponse,
        ChannelStreamScheduleResponse,
        ChannelTeamsResponse,
        CharityCampaignDonationsResponseData,
        CharityCampaignResponse,
        ChatSettingsResponse,
        ChattersResponseData,
        CheckAutomodStatusResponse,
        CheckUserSubscriptionResponse,
        CheermotesResponse,
        ClipsResponseData,
        ContentClassificationLabelsResponse,
        CreateChannelStreamScheduleSegmentResponse,
        CreateClipResponse,
        CreateStreamMarkerResponse,
        CreatorGoalsResponse,
        CustomRewardRedemptionResponse,
        CustomRewardRedemptionResponseData,
        CustomRewardsResponse,
        DeleteVideosResponse,
        DropsEntitlementsResponseData,
        EmoteSetsResponse,
        EventsubSubscriptionResponseData,
        ExtensionAnalyticsResponseData,
        ExtensionTransactionsResponseData,
        FollowedChannelsResponseData,
        GameAnalyticsResponseData,
        GamesResponse,
        GamesResponseData,
        GlobalChatBadgesResponse,
        GlobalEmotesResponse,
        HypeTrainEventsResponseData,
        ModeratedChannelsResponseData,
        ModeratorsResponseData,
        PollsResponse,
        PollsResponseData,
        PredictionsResponse,
        PredictionsResponseData,
        RawResponse,
        ResolveUnbanRequestsResponse,
        SearchChannelsResponseData,
        SendChatMessageResponse,
        SharedChatSessionResponse,
        ShieldModeStatusResponse,
        SnoozeNextAdResponse,
        StartARaidResponse,
        StartCommercialResponse,
        StreamKeyResponse,
        StreamMarkersResponseData,
        StreamsResponseData,
        TeamsResponse,
        TopGamesResponseData,
        UnbanRequestsResponseData,
        UpdateChannelStreamScheduleSegmentResponse,
        UpdateDropsEntitlementsResponse,
        UpdateUserExtensionsResponse,
        UpdateUserResponse,
        UserActiveExtensionsResponse,
        UserBlockListResponseData,
        UserChatColorResponse,
        UserEmotesResponseData,
        UserExtensionsResponse,
        UsersResponse,
        VideosResponseData,
        WarnChatUserResponse,
    )


logger: logging.Logger = logging.getLogger(__name__)


T = TypeVar("T")
PaginatedConverter: TypeAlias = Callable[..., T] | None


async def json_or_text(resp: aiohttp.ClientResponse) -> dict[str, Any] | str:
    text: str = await resp.text()

    try:
        if resp.headers["Content-Type"].startswith("application/json"):
            return _from_json(text)  # type: ignore
    except KeyError:
        pass

    return text


class Route:
    """Route class used by TwitchIO to prepare HTTP requests to Twitch.

    .. warning::

        You should not change or instantiate this class manually, as it is used internally.

    Attributes
    ----------
    params: dict[str, Any]
        A mapping of parameters used in the request.
    json: dict[Any, Any]
        The JSON used in the body of the request. Could be an empty :class:`dict`.
    headers: dict[str, str]
        The headers used in the request.
    token_for: str
        The User ID that was used to gather a token for authentication. Could be an empty :class:`str`.
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT', 'TRACE']
        The request method used.
    path: str
        The API endpoint requested.
    """

    __slots__ = (
        "_base_url",
        "_url",
        "data",
        "headers",
        "json",
        "method",
        "packed",
        "params",
        "path",
        "token_for",
        "use_id",
    )

    BASE: ClassVar[str] = "https://api.twitch.tv/helix/"
    ID_BASE: ClassVar[str] = "https://id.twitch.tv/"

    def __init__(
        self,
        method: HTTPMethod,
        path: str,
        *,
        use_id: bool = False,
        **kwargs: Unpack[APIRequestKwargs],
    ) -> None:
        self.params: ParamMapping = kwargs.pop("params", {})
        self.json: Any = kwargs.get("json", {})
        self.headers: dict[str, str] = kwargs.get("headers", {})
        self.token_for: str = str(kwargs.get("token_for", ""))

        self.use_id = use_id
        self.method = method
        self.path = path

        self._base_url: str = ""
        self._url: str = self.build_url(duplicate_key=not use_id)

    def __str__(self) -> str:
        return str(self._url)

    def __repr__(self) -> str:
        return f"{self.method}[{self.base_url}]"

    def build_url(self, *, remove_none: bool = True, duplicate_key: bool = True) -> str:
        base = self.ID_BASE if self.use_id else self.BASE
        self.path = self.path.lstrip("/").rstrip("/")

        url: str = f"{base}{self.path}"
        self._base_url = url

        if not self.params:
            return url

        url += "?"

        # We expect a dict so keys should be unique...
        for key, value in copy.copy(self.params).items():
            if value is None:
                if remove_none:
                    del self.params[key]
                continue

            if isinstance(value, (str, int)):
                url += f"{key}={self.encode(str(value), safe='+', plus=True)}&"
            elif duplicate_key:
                for v in value:
                    url += f"{key}={self.encode(str(v), safe='+', plus=True)}&"
            else:
                joined: str = "+".join([self.encode(str(v), safe="+") for v in value])
                url += f"{key}={joined}&"

        return url.rstrip("&")

    @classmethod
    def encode(cls, value: str, /, safe: str = "", plus: bool = False) -> str:
        method = urllib.parse.quote_plus if plus else urllib.parse.quote
        unquote = urllib.parse.unquote_plus if plus else urllib.parse.unquote

        return method(value, safe=safe) if unquote(value) == value else value

    @property
    def url(self) -> str:
        """Property returning the URL used to make a request. Could include query parameters."""
        return self._url

    @property
    def base_url(self) -> str:
        """Property returning the URL used to make a request without query parameters."""
        return self._base_url

    def update_params(self, params: ParamMapping, *, remove_none: bool = True) -> str:
        self.params.update(params)
        self._url = self.build_url(remove_none=remove_none)

        return self.url

    def update_headers(self, headers: dict[str, str]) -> None:
        self.headers.update(headers)


class HTTPAsyncIterator(Generic[T]):
    """TwitchIO async iterator for HTTP requests.

    When a method or function returns this iterator you should call the returning function in one of the following two ways:

    ``await method(...)``

    **or**

    ``async for item in method(...)``

    When awaited the iterator will return a flattened list of all the items returned via the request for the first page only.
    If the endpoint is paginated, it is preferred you use ``async for item in method(...)`` in a list comprehension.

    When used with ``async for`` the iterator will return the next item available until no items remain or you break from the
    loop manually, E.g. with ``break`` or ``return`` etc.

    ``async for item in method(...)`` will continue making requests on paginated endpoints to the next page as needed
    and when available.

    You can create a flattened list of all pages with a list comprehension.

    Examples
    --------

    .. code-block:: python3

        # Flatten and return first page (20 results)
        streams = await bot.fetch_streams()

        # Flatten and return up to 1000 results (max 100 per page) which equates to 10 requests...
        streams = [stream async for stream in bot.fetch_streams(first=100, max_results=1000)]

        # Loop over results until we manually stop...
        async for item in bot.fetch_streams(first=100, max_results=1000):
            # Some logic...
            ...
            break


    .. important::

        Everything in this class is private internals, and should not be modified.
    """

    __slots__ = (
        "_buffer",
        "_converter",
        "_cursor",
        "_first",
        "_http",
        "_max_results",
        "_nested_key",
        "_route",
    )

    def __init__(
        self,
        http: HTTPClient,
        route: Route,
        max_results: int | None = None,
        converter: PaginatedConverter[T] = None,
        nested_key: str | None = None,
    ) -> None:
        self._http = http
        self._route = route

        self._cursor: str | None | bool = None
        self._first: int = int(route.params.get("first", 20))  # 20 is twitch default
        self._max_results: int | None = max_results

        if self._max_results is not None and self._max_results < self._first:
            self._first = self._max_results

        self._converter = converter or self._base_converter
        self._buffer: deque[T] = deque()
        self._nested_key: str | None = nested_key

    def _base_converter(self, data: Any, *, raw: Any = None) -> T:
        if raw is None:
            raw = {}

        return data

    async def _call_next(self) -> None:
        if self._cursor is False:
            raise StopAsyncIteration

        if self._max_results is not None and self._max_results <= 0:
            raise StopAsyncIteration

        self._route.update_params({"after": self._cursor})
        data: RawResponse = await self._http.request_json(self._route)
        self._cursor = data.get("pagination", {}).get("cursor", False)

        try:
            inner: list[RawResponse] = data["data"] if self._nested_key is None else data["data"][self._nested_key]
        except KeyError as e:
            raise HTTPException('Expected "data" key not found.', route=self._route, status=500, extra="") from e

        if not self._nested_key:
            for value in inner:
                if self._max_results is None:
                    self._buffer.append(await self._do_conversion(value, raw=data))
                    continue

                self._max_results -= 1  # If this is causing issues, it's just pylance bugged/desynced...
                if self._max_results < 0:
                    return

                self._buffer.append(await self._do_conversion(value, raw=data))
        else:
            if self._max_results is not None:
                self._max_results -= 1  # If this is causing issues, it's just pylance bugged/desynced...
                if self._max_results < 0:
                    return
            self._buffer.append(await self._do_conversion(inner[0], raw=data))

    async def _do_conversion(self, data: RawResponse, *, raw: RawResponse) -> T:
        return self._converter(data, raw=raw)

    async def _flatten(self) -> list[T]:
        if not self._buffer:
            await self._call_next()

        return list(self._buffer)

    def __await__(self) -> Generator[Any, None, list[T]]:
        return self._flatten().__await__()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> T:
        if not self._buffer:
            await self._call_next()

        try:
            data = self._buffer.popleft()
        except IndexError as e:
            raise StopAsyncIteration from e

        return data


class HTTPClient:
    __slots__ = ("_client_id", "_session", "_session_set", "_should_close", "user_agent")

    def __init__(self, session: aiohttp.ClientSession = MISSING, *, client_id: str) -> None:
        self._session: aiohttp.ClientSession = session
        self._should_close: bool = session is MISSING
        self._session_set: bool = False

        self._client_id: str = client_id

        # User Agent...
        pyver = f"{sys.version_info[0]}.{sys.version_info[1]}"
        ua = "TwitchioClient (https://github.com/PythonistaGuild/TwitchIO {0}) Python/{1} aiohttp/{2}"
        self.user_agent: str = ua.format(__version__, pyver, aiohttp.__version__)

    @property
    def headers(self) -> dict[str, str]:
        # If the user somehow gets a client_id passed that isn't a str
        # this will allow Twitch to throw a reasonable HTTPException

        return {"User-Agent": self.user_agent, "Client-ID": str(self._client_id)}

    async def _init_session(self) -> None:
        if self._session_set:
            return

        self._session_set = True

        if self._session is not MISSING:
            return

        logger.debug("Initialising ClientSession on %s.", self.__class__.__qualname__)
        self._session = aiohttp.ClientSession(headers=self.headers)

    def clear(self) -> None:
        if self._session and self._session.closed:
            logger.debug(
                "Clearing %s session. A new session will be created on the next request.", self.__class__.__qualname__
            )
            self._session = MISSING
            self._session_set = False

    async def close(self) -> None:
        if not self._should_close:
            return

        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                logger.debug("Ignoring exception caught while closing %s session: %s.", self.__class__.__qualname__, e)

            self.clear()
            logger.debug("%s session closed successfully.", self.__class__.__qualname__)

    async def request(self, route: Route) -> RawResponse | str | None:
        if not self._session_set:
            await self._init_session()

        assert self._session is not None

        logger.debug("Attempting a request to %r with %s.", route, self.__class__.__qualname__)
        route.headers.update(self.headers)

        failed: bool = False
        while True:
            async with self._session.request(
                route.method,
                route.url,
                headers=route.headers,
                json=route.json or None,
            ) as resp:
                data: RawResponse | str = await json_or_text(resp)
                logger.debug("Request to %r with %s returned: status=%d", route, self.__class__.__qualname__, resp.status)

                if resp.status == 503 and not failed:
                    # Twitch recommends retrying 1 time after a 503...
                    failed = True
                    logger.debug("Retrying request to %r (1) times after 3 seconds.", route)

                    await asyncio.sleep(3)
                    continue

                if resp.status >= 400:
                    raise HTTPException(
                        f"Request {route} failed with status {resp.status}: {data}",
                        route=route,
                        status=resp.status,
                        extra=data,
                    )

                if resp.status == 204:
                    return None

            return data

    async def request_json(self, route: Route) -> Any:
        route.headers.update({"Accept": "application/json"})
        data = await self.request(route)

        if isinstance(data, str):
            raise HTTPException("Expected JSON data, but received text data.", status=500, extra=data)

        return data

    async def _request_asset_head(self, url: str) -> dict[str, str]:
        if not self._session_set:
            await self._init_session()

        assert self._session is not None

        logger.debug('Attempting to request headers for asset "%s" with %s.', url, self.__class__.__qualname__)

        async with self._session.head(url) as resp:
            if resp.status != 200:
                msg = f'Failed to header for asset at "{url}" with status {resp.status}.'
                raise HTTPException(msg, status=resp.status, extra=await resp.text())

            return dict(resp.headers)

    async def _request_asset(self, asset: Asset, *, chunk_size: int = 1024) -> AsyncIterator[bytes]:
        if not self._session_set:
            await self._init_session()

        assert self._session is not None

        logger.debug('Attempting a request to asset "%r" with %s.', asset, self.__class__.__qualname__)

        async with self._session.get(asset.url) as resp:
            if resp.status != 200:
                msg = f'Failed to get asset at "{asset.url}" with status {resp.status}.'
                raise HTTPException(msg, status=resp.status, extra=await resp.text())

            headers: dict[str, str] = dict(resp.headers)
            asset._set_ext(headers)

            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    def request_paginated(
        self,
        route: Route,
        max_results: int | None = None,
        *,
        converter: PaginatedConverter[T] | None = None,
        nested_key: str | None = None,
    ) -> HTTPAsyncIterator[T]:
        iterator: HTTPAsyncIterator[T] = HTTPAsyncIterator(
            self, route, max_results, converter=converter, nested_key=nested_key
        )
        return iterator

    ### Ads ###

    async def start_commercial(self, broadcaster_id: str | int, length: int, token_for: str) -> StartCommercialResponse:
        data = {"broadcaster_id": broadcaster_id, "length": length}

        route: Route = Route("POST", "channels/commercial", json=data, token_for=token_for)
        return await self.request_json(route)

    async def get_ad_schedule(self, broadcaster_id: str | int, token_for: str) -> AdScheduleResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "channels/ads", params=params, token_for=token_for)
        return await self.request_json(route)

    async def post_snooze_ad(self, broadcaster_id: str | int, token_for: str) -> SnoozeNextAdResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("POST", "channels/ads/snooze", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Analytics ###

    @handle_user_ids()
    def get_extension_analytics(
        self,
        *,
        token_for: str | PartialUser,
        extension_id: str | None = None,
        type: Literal["overview_v2"] = "overview_v2",
        started_at: datetime.date | None = None,
        ended_at: datetime.date | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[ExtensionAnalytics]:
        params = {"type": type, "First": first}

        if extension_id:
            params["extension_id"] = extension_id

        if started_at and ended_at:
            params["started_at"] = date_to_datetime_with_z(started_at)
            params["ended_at"] = date_to_datetime_with_z(ended_at)

        route: Route = Route("GET", "analytics/extensions", params=params, token_for=token_for)

        def converter(data: ExtensionAnalyticsResponseData, *, raw: Any) -> ExtensionAnalytics:
            return ExtensionAnalytics(data)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    def get_game_analytics(
        self,
        *,
        token_for: str | PartialUser,
        game_id: str | None = None,
        type: Literal["overview_v2"] = "overview_v2",
        started_at: datetime.date | None = None,
        ended_at: datetime.date | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[GameAnalytics]:
        params = {"type": type, "First": first}

        if game_id:
            params["game_id"] = game_id

        if started_at and ended_at:
            params["started_at"] = date_to_datetime_with_z(started_at)
            params["ended_at"] = date_to_datetime_with_z(ended_at)

        route: Route = Route("GET", "analytics/games", params=params, token_for=token_for)

        def converter(data: GameAnalyticsResponseData, *, raw: Any) -> GameAnalytics:
            return GameAnalytics(data)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    ### Bits ###
    @handle_user_ids()
    async def get_bits_leaderboard(
        self,
        *,
        token_for: str | PartialUser,
        count: int = 10,
        period: Literal["day", "week", "month", "year", "all"] = "all",
        started_at: datetime.datetime | None = None,
        user_id: str | int | PartialUser | None = None,
    ) -> BitsLeaderboardResponse:
        params: dict[str, str | int | datetime.datetime] = {
            "count": count,
            "period": period,
        }

        if started_at is not None:
            params["started_at"] = url_encode_datetime(started_at)
        if user_id is not None:
            params["user_id"] = str(user_id)

        route: Route = Route("GET", "bits/leaderboard", params=params, token_for=str(token_for))
        return await self.request_json(route)

    @handle_user_ids()
    async def get_cheermotes(
        self,
        broadcaster_id: str | int | None = None,
        token_for: str | PartialUser | None = None,
    ) -> CheermotesResponse:
        params = {"broadcaster_id": broadcaster_id} if broadcaster_id is not None else {}

        route: Route = Route("GET", "bits/cheermotes", params=params, token_for=token_for)
        return await self.request_json(route)

    def get_extension_transactions(
        self,
        *,
        extension_id: str,
        ids: list[str] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[ExtensionTransaction]:
        params: dict[str, str | int | list[str]] = {"extension_id": extension_id, "first": first}
        if ids:
            params["id"] = ids

        route: Route = Route("GET", "extensions/transactions", params=params)

        def converter(data: ExtensionTransactionsResponseData, *, raw: Any) -> ExtensionTransaction:
            return ExtensionTransaction(data, http=self)

        iterator: HTTPAsyncIterator[ExtensionTransaction] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    ### Channels ###

    @handle_user_ids()
    async def get_channel_info(
        self,
        broadcaster_ids: list[str | int],
        token_for: str | PartialUser | None = None,
    ) -> ChannelInformationResponse:
        params = {"broadcaster_id": broadcaster_ids}

        route: Route = Route("GET", "channels", params=params, token_for=token_for)
        return await self.request_json(route)

    async def patch_channel_info(
        self,
        *,
        broadcaster_id: str | int,
        token_for: str,
        game_id: str | int | None = None,
        language: str | None = None,
        title: str | None = None,
        delay: int | None = None,
        tags: list[str] | None = None,
        branded_content: bool | None = None,
        classification_labels: list[
            dict[
                Literal[
                    "DebatedSocialIssuesAndPolitics",
                    "MatureGame",
                    "DrugsIntoxication",
                    "SexualThemes",
                    "ViolentGraphic",
                    "Gambling",
                    "ProfanityVulgarity",
                ],
                bool,
            ]
        ]
        | None = None,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id}

        data: dict[str, str | int | list[str] | list[dict[str, str | bool]]] = {
            k: v
            for k, v in {
                "game_id": game_id,
                "broadcaster_language": language,
                "title": title,
                "delay": delay,
                "tags": tags,
                "is_branded_content": branded_content,
            }.items()
            if v is not None
        }

        if classification_labels is not None:
            converted_labels = [
                {"id": label, "is_enabled": enabled} for item in classification_labels for label, enabled in item.items()
            ]
            data["content_classification_labels"] = converted_labels

        route: Route = Route("PATCH", "channels", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    async def get_channel_editors(self, broadcaster_id: str | int, token_for: str) -> ChannelEditorsResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "channels/editors", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_followed_channels(
        self,
        *,
        user_id: str | int,
        token_for: str,
        broadcaster_id: str | int | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> FollowedChannels:
        first = max(1, min(100, first))
        params = {"first": first, "user_id": user_id}

        if broadcaster_id is not None:
            params["broadcaster_id"] = str(broadcaster_id)

        route = Route("GET", "channels/followed", params=params, token_for=token_for)

        def converter(data: FollowedChannelsResponseData, *, raw: Any) -> FollowedChannelsEvent:
            return FollowedChannelsEvent(data, http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        data = await self.request_json(route)

        return FollowedChannels(data, iterator)

    @handle_user_ids()
    async def get_channel_followers(
        self,
        *,
        broadcaster_id: str | int,
        token_for: str,
        user_id: str | int | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> ChannelFollowers:
        first = max(1, min(100, first))
        params = {"first": first, "broadcaster_id": broadcaster_id}

        if user_id is not None:
            params["user_id"] = str(user_id)

        route = Route("GET", "channels/followers", params=params, token_for=token_for)

        def converter(data: ChannelFollowersResponseData, *, raw: Any) -> ChannelFollowerEvent:
            return ChannelFollowerEvent(data, http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        data = await self.request_json(route)

        return ChannelFollowers(data, iterator)

    ### Channel Points ###

    async def post_custom_reward(
        self,
        *,
        broadcaster_id: str,
        token_for: str,
        title: str,
        cost: int,
        prompt: str | None = None,
        enabled: bool = True,
        background_color: str | Colour | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        skip_queue: bool = False,
    ) -> CustomRewardsResponse:
        params = {"broadcaster_id": broadcaster_id}
        data = {
            "title": title,
            "cost": cost,
            "is_enabled": enabled,
            "should_redemptions_skip_request_queue": skip_queue,
        }

        if prompt is not None:
            data["prompt"] = prompt
            data["is_user_input_required"] = True

        if background_color:
            if isinstance(background_color, Colour):
                background_color = str(background_color)
            data["background_color"] = background_color

        if max_per_stream:
            data["max_per_stream"] = max_per_stream
            data["is_max_per_stream_enabled"] = True

        if max_per_user:
            data["max_per_user_per_stream"] = max_per_user
            data["is_max_per_user_per_stream_enabled"] = True

        if global_cooldown:
            data["global_cooldown_seconds"] = global_cooldown
            data["is_global_cooldown_enabled"] = True

        route: Route = Route("POST", "channel_points/custom_rewards", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    async def delete_custom_reward(self, broadcaster_id: str, reward_id: str, token_for: str) -> None:
        params = {"broadcaster_id": broadcaster_id, "id": reward_id}

        route: Route = Route("DELETE", "channel_points/custom_rewards", params=params, token_for=token_for)
        return await self.request_json(route)

    async def get_custom_reward(
        self,
        *,
        broadcaster_id: str,
        token_for: str,
        reward_ids: list[str] | None = None,
        manageable: bool = False,
    ) -> CustomRewardsResponse:
        params: dict[str, str | bool | list[str]] = {
            "broadcaster_id": broadcaster_id,
            "only_manageable_rewards": manageable,
        }

        if reward_ids is not None:
            params["id"] = reward_ids

        route: Route = Route("GET", "channel_points/custom_rewards", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def patch_custom_reward(
        self,
        *,
        broadcaster_id: str,
        token_for: str | PartialUser,
        reward_id: str,
        title: str | None = None,
        cost: int | None = None,
        prompt: str | None = None,
        enabled: bool | None = None,
        background_color: str | Colour | None = None,
        user_input_required: bool | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        paused: bool | None = None,
        skip_queue: bool | None = None,
    ) -> CustomRewardsResponse:
        params = {
            "broadcaster_id": broadcaster_id,
            "id": reward_id,
        }

        data: dict[str, str | int | bool] = {}

        if title is not None:
            data["title"] = title

        if cost is not None:
            data["cost"] = cost

        if prompt is not None:
            data["prompt"] = prompt
            data["user_input_required"] = True

        if enabled is not None:
            data["is_enabled"] = enabled

        if background_color:
            if isinstance(background_color, Colour):
                background_color = str(background_color)
            data["background_color"] = background_color

        if user_input_required is not None:
            data["is_user_input_required"] = user_input_required

        if skip_queue is not None:
            data["should_redemptions_skip_request_queue"] = skip_queue

        if max_per_stream is not None:
            data["max_per_stream"] = max_per_stream
            data["is_max_per_stream_enabled"] = max_per_stream != 0

        if max_per_user is not None:
            data["max_per_user_per_stream"] = max_per_user
            data["is_max_per_user_per_stream_enabled"] = max_per_user != 0

        if paused is not None:
            data["is_paused"] = paused

        if global_cooldown is not None:
            data["global_cooldown_seconds"] = global_cooldown
            data["is_global_cooldown_enabled"] = global_cooldown != 0

        route: Route = Route("PATCH", "channel_points/custom_rewards", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    def get_custom_reward_redemptions(
        self,
        *,
        broadcaster_id: str,
        token_for: str | PartialUser,
        reward_id: str,
        parent_reward: CustomReward,
        status: Literal["CANCELED", "FULFILLED", "UNFULFILLED"] | None = None,
        ids: list[str] | None = None,
        sort: Literal["OLDEST", "NEWEST"] = "OLDEST",
        first: int = 20,
    ) -> HTTPAsyncIterator[CustomRewardRedemption]:
        params: dict[str, str | int | list[str]] = {
            "broadcaster_id": broadcaster_id,
            "reward_id": reward_id,
            "sort": sort,
            "First": first,
        }
        if ids is None and status is None:
            raise ValueError("You must provide at least a status if not providing any ids.")

        if ids is not None:
            params["id"] = ids
        if status is not None:
            params["status"] = status

        route: Route = Route("GET", "channel_points/custom_rewards/redemptions", params=params, token_for=token_for)

        def converter(data: CustomRewardRedemptionResponseData, *, raw: Any) -> CustomRewardRedemption:
            return CustomRewardRedemption(data, parent_reward=parent_reward, http=self)

        iterator = self.request_paginated(route, converter=converter)
        return iterator

    @handle_user_ids()
    async def patch_custom_reward_redemption(
        self,
        *,
        broadcaster_id: str,
        token_for: str | PartialUser,
        reward_id: str,
        id: str,
        status: Literal["CANCELED", "FULFILLED"],
    ) -> CustomRewardRedemptionResponse:
        params = {"broadcaster_id": broadcaster_id, "reward_id": reward_id, "id": id}
        data = {"status": status}

        route: Route = Route(
            "PATCH",
            "channel_points/custom_rewards/redemptions",
            params=params,
            json=data,
            token_for=token_for,
        )

        return await self.request_json(route)

    ### Charity ###

    async def get_charity_campaign(self, broadcaster_id: str, token_for: str) -> CharityCampaignResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "charity/campaigns", params=params, token_for=token_for)
        return await self.request_json(route)

    def get_charity_donations(
        self,
        broadcaster_id: str,
        token_for: str,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[CharityDonation]:
        params = {"broadcaster_id": broadcaster_id, "first": first}
        route: Route = Route("GET", "charity/donations", params=params, token_for=token_for)

        def converter(data: CharityCampaignDonationsResponseData, *, raw: Any) -> CharityDonation:
            return CharityDonation(data, http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    ### Chat ###

    @handle_user_ids()
    async def get_chatters(
        self,
        token_for: str | PartialUser,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        first: int = 100,
        max_results: int | None = None,
    ) -> Chatters:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id, "first": first}
        route: Route = Route("GET", "chat/chatters", params=params, token_for=token_for)

        def converter(data: ChattersResponseData, *, raw: Any) -> PartialUser:
            return PartialUser(data["user_id"], data["user_login"], http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        data = await self.request_json(route)

        return Chatters(iterator, data)

    @handle_user_ids()
    async def get_global_chat_badges(self, token_for: str | PartialUser | None = None) -> GlobalChatBadgesResponse:
        route: Route = Route("GET", "chat/badges/global", token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_user_chat_color(
        self,
        user_ids: list[str | int],
        token_for: str | PartialUser | None = None,
    ) -> UserChatColorResponse:
        params: dict[str, list[str | int]] = {"user_id": user_ids}

        route: Route = Route("GET", "chat/color", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_channel_emotes(
        self,
        broadcaster_id: str | int,
        token_for: str | PartialUser | None = None,
    ) -> ChannelEmotesResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "chat/emotes", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_global_emotes(self, token_for: str | PartialUser | None = None) -> GlobalEmotesResponse:
        route: Route = Route("GET", "chat/emotes/global", token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_emote_sets(
        self, emote_set_ids: list[str], token_for: str | PartialUser | None = None
    ) -> EmoteSetsResponse:
        params = {"emote_set_id": emote_set_ids}

        route: Route = Route("GET", "chat/emotes/set", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_channel_chat_badges(
        self,
        broadcaster_id: str,
        token_for: str | PartialUser | None = None,
    ) -> ChannelChatBadgesResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "chat/badges", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_channel_chat_settings(
        self,
        broadcaster_id: str,
        moderator_id: str | int | PartialUser | None = None,
        token_for: str | PartialUser | None = None,
    ) -> ChatSettingsResponse:
        params = {"broadcaster_id": broadcaster_id}
        if moderator_id is not None:
            params["moderator_id"] = str(moderator_id)

        route: Route = Route("GET", "chat/settings", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    def get_user_emotes(
        self,
        user_id: str,
        token_for: str,
        broadcaster_id: str | int | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[UserEmote]:
        params = {"user_id": user_id}
        if broadcaster_id is not None:
            params["broadcaster_id"] = str(broadcaster_id)

        route: Route = Route("GET", "chat/emotes/user", params=params, token_for=token_for)

        def converter(data: UserEmotesResponseData, *, raw: Any) -> UserEmote:
            return UserEmote(data, template=raw["template"], http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    async def patch_chat_settings(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        emote_mode: bool | None = None,
        follower_mode: bool | None = None,
        follower_mode_duration: int | None = None,
        slow_mode: bool | None = None,
        slow_mode_wait_time: int | None = None,
        subscriber_mode: bool | None = None,
        unique_chat_mode: bool | None = None,
        non_moderator_chat_delay: bool | None = None,
        non_moderator_chat_delay_duration: Literal[2, 4, 6] | None = None,
    ) -> ChatSettingsResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}

        _data = {
            "emote_mode": emote_mode,
            "follower_mode": follower_mode,
            "follower_mode_duration": follower_mode_duration,
            "slow_mode": slow_mode,
            "slow_mode_wait_time": slow_mode_wait_time,
            "subscriber_mode": subscriber_mode,
            "unique_chat_mode": unique_chat_mode,
            "non_moderator_chat_delay": non_moderator_chat_delay,
            "non_moderator_chat_delay_duration": non_moderator_chat_delay_duration,
        }
        data = {k: v for k, v in _data.items() if v is not None}

        route: Route = Route("PATCH", "chat/settings", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_shared_chat_session(
        self, broadcaster_id: str | int, *, token_for: str | PartialUser | None = None
    ) -> SharedChatSessionResponse:
        params = {"broadcaster_id": broadcaster_id}
        route: Route = Route("POST", "chat/shared_chat/session", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def post_chat_announcement(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        message: str,
        color: Literal["blue", "green", "orange", "purple", "primary"] = "primary",
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        data = {"color": color, "message": message}

        route: Route = Route("POST", "chat/announcements", json=data, params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def post_chat_shoutout(
        self,
        broadcaster_id: str | int,
        to_broadcaster_id: str | int | PartialUser,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
    ) -> None:
        params = {
            "from_broadcaster_id": broadcaster_id,
            "moderator_id": moderator_id,
            "to_broadcaster_id": to_broadcaster_id,
        }

        route: Route = Route("POST", "chat/shoutouts", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def post_chat_message(
        self,
        broadcaster_id: str,
        sender_id: str | int | PartialUser,
        message: str,
        token_for: str | PartialUser | None,
        reply_to_message_id: str | None = None,
        source_only: bool | None = None,
    ) -> SendChatMessageResponse:
        data = {"broadcaster_id": broadcaster_id, "sender_id": sender_id, "message": message}
        if reply_to_message_id is not None:
            data["reply_parent_message_id"] = reply_to_message_id
        if source_only is not None:
            data["for_source_only"] = source_only

        route: Route = Route("POST", "chat/messages", json=data, token_for=token_for)
        return await self.request_json(route)

    async def put_user_chat_color(self, user_id: str | int, color: str, token_for: str) -> None:
        params = {"user_id": user_id, "color": color}

        route: Route = Route("PUT", "chat/color", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Clips ###

    @handle_user_ids()
    def get_clips(
        self,
        *,
        first: int,
        broadcaster_id: str | None = None,
        game_id: str | None = None,
        clip_ids: list[str] | None = None,
        started_at: datetime.datetime | None = None,
        ended_at: datetime.datetime | None = None,
        is_featured: bool | None = None,
        token_for: str | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Clip]:
        params: dict[str, str | int | list[str]] = {"first": first}

        if broadcaster_id:
            params["broadcaster_id"] = broadcaster_id
        elif game_id:
            params["game_id"] = game_id
        elif clip_ids:
            params["id"] = clip_ids

        if started_at:
            params["started_at"] = url_encode_datetime(started_at)
        if ended_at:
            params["ended_at"] = url_encode_datetime(ended_at)
        if is_featured is not None:
            params["is_featured"] = is_featured

        route: Route = Route("GET", "clips", params=params, token_for=token_for)

        def converter(data: ClipsResponseData, *, raw: Any) -> Clip:
            return Clip(data, http=self)

        iterator: HTTPAsyncIterator[Clip] = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    async def post_create_clip(
        self,
        *,
        broadcaster_id: str | int,
        token_for: str | PartialUser,
        has_delay: bool = False,
    ) -> CreateClipResponse:
        params = {"broadcaster_id": broadcaster_id, "has_delay": has_delay}

        route: Route = Route("POST", "clips", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Conduits ###

    async def delete_conduit(self, conduit_id: str, /) -> None:
        params = {"id": conduit_id}

        route = Route("DELETE", "eventsub/conduits", params=params)
        await self.request(route)

    async def update_conduit_shards(self, conduit_id: str, /, *, shards: list[ShardUpdateRequest]) -> ...:
        params = {"conduit_id": conduit_id}
        body = {"shards": shards}

        route = Route("PATCH", "eventsub/conduits/shards", params=params, json=body)
        return await self.request_json(route)

    async def create_conduit(self, shard_count: int, /) -> ConduitPayload:
        params = {"shard_count": shard_count}

        route: Route = Route("POST", "eventsub/conduits", params=params)
        return await self.request_json(route)

    async def get_conduits(self) -> ConduitPayload:
        route = Route("GET", "eventsub/conduits")
        return await self.request_json(route)

    def get_conduit_shards(self, conduit_id: str, /, *, status: str | None = None) -> HTTPAsyncIterator[ConduitShard]:
        params = {"conduit_id": conduit_id, "first": 100}
        if status:
            params["status"] = status

        def converter(data: ShardData, *, raw: Any) -> ConduitShard:
            return ConduitShard(data=data)

        route: Route = Route("GET", "eventsub/conduits/shards", params=params)
        iterator = self.request_paginated(route, converter=converter)

        return iterator

    async def update_conduits(self, id: str, /, shard_count: int) -> ConduitPayload:
        params = {"id": id, "shard_count": shard_count}

        route: Route = Route("PATCH", "eventsub/conduits", params=params)
        return await self.request_json(route)

    ### CCLs ###

    @handle_user_ids()
    async def get_content_classification_labels(
        self,
        locale: str,
        token_for: str | PartialUser | None = None,
    ) -> ContentClassificationLabelsResponse:
        params: dict[str, str] = {"locale": locale}

        route: Route = Route("GET", "content_classification_labels", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Entitlements ###

    @handle_user_ids()
    def get_drop_entitlements(
        self,
        token_for: str | PartialUser | None = None,
        ids: list[str] | None = None,
        user_id: str | PartialUser | int | None = None,
        game_id: str | None = None,
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Entitlement]:
        params: dict[str, str | int | list[str]] = {"first": first}
        if ids is not None:
            params["id"] = ids
        if user_id is not None:
            params["user_id"] = str(user_id)
        if game_id is not None:
            params["game_id"] = game_id
        if fulfillment_status is not None:
            params["fulfillment_status"] = fulfillment_status

        route: Route = Route("GET", "entitlements/drops", params=params, token_for=token_for)

        def converter(data: DropsEntitlementsResponseData, *, raw: Any) -> Entitlement:
            return Entitlement(data, http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    async def patch_drop_entitlements(
        self,
        ids: list[str] | None = None,
        fulfillment_status: Literal["CLAIMED", "FULFILLED"] | None = None,
        token_for: str | PartialUser | None = None,
    ) -> UpdateDropsEntitlementsResponse:
        data: dict[str, list[str] | str] = {}
        if ids is not None:
            data["entitlement_ids"] = ids
        if fulfillment_status is not None:
            data["fulfillment_status"] = fulfillment_status

        route: Route = Route("PATCH", "entitlements/drops", json=data, token_for=token_for)

        return await self.request_json(route)

    ### Extensions ###

    ### EventSub ###

    # MARK
    async def create_eventsub_subscription(self, **kwargs: Unpack[_SubscriptionData]) -> SubscriptionResponse:
        token: str | None = None

        _type: SubscriptionType = kwargs["type"]
        version: str = kwargs["version"]
        condition: Condition = kwargs["condition"]
        transport: SubscriptionCreateTransport = kwargs["transport"]
        token_for: str | None = kwargs["token_for"]

        method: str = transport["method"]
        if method in ("webhook", "conduit"):
            # Webhook/conduit must use app tokens...
            token_for = None

        elif method == "websocket" and not token_for and not token:
            raise ValueError("A valid User Access token must be passed for websocket subscriptions.")

        data: SubscriptionCreateRequest = {
            "type": _type.value,
            "version": version,
            "condition": condition,
            "transport": transport,
        }

        route: Route = Route("POST", "eventsub/subscriptions", token_for=token_for, json=data)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_eventsub_subscription(
        self,
        *,
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
        user_id: str | PartialUser | None = None,
        subscription_id: str | None = None,
        type: str | None = None,
        max_results: int | None = None,
        token_for: str | PartialUser | None = None,
    ) -> EventsubSubscriptions:
        params: dict[str, str] = {}

        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        if user_id is not None:
            params["user_id"] = str(user_id)
        if subscription_id is not None:
            params["subscription_id"] = subscription_id

        route: Route = Route("GET", "eventsub/subscriptions", params=params, token_for=token_for)

        def converter(data: EventsubSubscriptionResponseData, *, raw: Any) -> EventsubSubscription:
            return EventsubSubscription(data, http=self)

        iterator: HTTPAsyncIterator[EventsubSubscription] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )
        data = await self.request_json(route)

        return EventsubSubscriptions(data, iterator)

    @handle_user_ids()
    async def delete_eventsub_subscription(self, id: str, *, token_for: str | PartialUser | None = None) -> None:
        params = {"id": id}
        route: Route = Route("DELETE", "eventsub/subscriptions", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Games ###

    @handle_user_ids()
    def get_top_games(
        self,
        first: int,
        token_for: str | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Game]:
        params: dict[str, int] = {"first": first}

        route: Route = Route("GET", "games/top", params=params, token_for=token_for)

        def converter(data: TopGamesResponseData, *, raw: Any) -> Game:
            return Game(data, http=self)

        iterator: HTTPAsyncIterator[Game] = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    async def get_games(
        self,
        *,
        names: list[str] | None = None,
        ids: list[str] | None = None,
        igdb_ids: list[str] | None = None,
        token_for: str | PartialUser | None = None,
    ) -> GamesResponse:
        params: dict[str, list[str]] = {}

        if names is not None:
            params["name"] = names
        if ids is not None:
            params["id"] = ids
        if igdb_ids is not None:
            params["igdb_id"] = igdb_ids

        route: Route = Route("GET", "games", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Goals ###

    async def get_creator_goals(self, broadcaster_id: str | int, token_for: str) -> CreatorGoalsResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "goals", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Guest Start ###

    ### Hype Train ###

    def get_hype_train_events(
        self,
        broadcaster_id: str | int,
        token_for: str,
        first: int = 1,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[HypeTrainEvent]:
        params = {"broadcaster_id": broadcaster_id, "first": first}

        route: Route = Route("GET", "hypetrain/events", params=params, token_for=token_for)

        def converter(data: HypeTrainEventsResponseData, *, raw: Any) -> HypeTrainEvent:
            return HypeTrainEvent(data, http=self)

        iterator: HTTPAsyncIterator[HypeTrainEvent] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    ### Moderation ###

    @handle_user_ids()
    async def post_check_automod_status(
        self,
        broadcaster_id: str | int,
        messages: list[AutomodCheckMessage],
        token_for: str | PartialUser,
    ) -> CheckAutomodStatusResponse:
        params = {"broadcaster_id": broadcaster_id}
        msg = [x._to_dict() for x in messages]
        data = {"data": msg}

        route: Route = Route("POST", "moderation/enforcements/status", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    async def post_manage_automod_messages(
        self,
        user_id: str | int,
        msg_id: str,
        action: Literal["ALLOW", "DENY"],
        token_for: str,
    ) -> None:
        data = {"user_id": user_id, "msg_id": msg_id, "action": action}

        route: Route = Route("POST", "moderation/automod/message", json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_automod_settings(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
    ) -> AutomodSettingsResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}

        route: Route = Route("GET", "moderation/automod/settings", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def put_automod_settings(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        settings: AutomodSettings,
        token_for: str | PartialUser,
    ) -> AutomodSettingsResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        data = settings.to_dict()

        route: Route = Route("PUT", "moderation/automod/settings", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    def get_banned_users(
        self,
        broadcaster_id: str | int,
        token_for: str,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[BannedUser]:
        params: dict[str, str | int | list[str | int]] = {"broadcaster_id": broadcaster_id, "first": first}
        if user_ids is not None:
            params["user_id"] = user_ids

        route: Route = Route("GET", "moderation/banned", params=params, token_for=token_for)

        def converter(data: BannedUsersResponseData, *, raw: Any) -> BannedUser:
            return BannedUser(data, http=self)

        iterator: HTTPAsyncIterator[BannedUser] = self.request_paginated(route, converter=converter, max_results=max_results)

        return iterator

    @handle_user_ids()
    async def post_ban_user(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        user_id: str | int | PartialUser,
        duration: int | None = None,
        reason: str | None = None,
    ) -> BanUserResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        data = {"data": {"user_id": user_id}}

        if duration is not None:
            data["data"]["duration"] = duration
        if reason is not None:
            data["data"]["reason"] = reason

        route: Route = Route("POST", "moderation/bans", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def delete_unban_user(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        user_id: str | int | PartialUser,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id, "user_id": user_id}

        route: Route = Route("DELETE", "moderation/bans", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    def get_unban_requests(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        status: Literal["pending", "approved", "denied", "acknowledged", "canceled"],
        user_id: str | int | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[UnbanRequest]:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id, "status": status, "first": first}
        if user_id is not None:
            params["user_id"] = user_id

        route: Route = Route("GET", "moderation/unban_requests", params=params, token_for=token_for)

        def converter(data: UnbanRequestsResponseData, *, raw: Any) -> UnbanRequest:
            return UnbanRequest(data, http=self)

        iterator: HTTPAsyncIterator[UnbanRequest] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    @handle_user_ids()
    async def patch_unban_requests(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        status: Literal["approved", "denied"],
        unban_request_id: str,
        resolution_text: str | None = None,
    ) -> ResolveUnbanRequestsResponse:
        params = {
            "broadcaster_id": broadcaster_id,
            "moderator_id": moderator_id,
            "status": status,
            "unban_request_id": unban_request_id,
        }
        if resolution_text is not None:
            params["resolution_text"] = resolution_text

        route: Route = Route("PATCH", "moderation/unban_requests", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    def get_blocked_terms(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[BlockedTerm]:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id, "first": first}

        route: Route = Route("GET", "moderation/blocked_terms", params=params, token_for=token_for)

        def converter(data: BlockedTermsResponseData, *, raw: Any) -> BlockedTerm:
            return BlockedTerm(data, http=self)

        iterator: HTTPAsyncIterator[BlockedTerm] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    @handle_user_ids()
    async def post_blocked_term(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        text: str,
    ) -> AddBlockedTermResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        data = {"text": text}

        route: Route = Route("POST", "moderation/blocked_terms", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def delete_blocked_term(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        id: str,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id, "id": id}

        route: Route = Route("DELETE", "moderation/blocked_terms", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def delete_chat_message(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        message_id: str | None = None,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        if message_id is not None:
            params["message_id"] = message_id

        route: Route = Route("DELETE", "moderation/chat", params=params, token_for=token_for)
        return await self.request_json(route)

    def get_moderated_channels(
        self,
        user_id: str | int,
        token_for: str,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[PartialUser]:
        params = {"user_id": user_id, "first": first}

        route: Route = Route("GET", "moderation/channels", params=params, token_for=token_for)

        def converter(data: ModeratedChannelsResponseData, *, raw: Any) -> PartialUser:
            return PartialUser(data["broadcaster_id"], data["broadcaster_login"], http=self)

        iterator: HTTPAsyncIterator[PartialUser] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    def get_moderators(
        self,
        broadcaster_id: str | int,
        token_for: str,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[PartialUser]:
        params: dict[str, str | int | list[str | int]] = {"broadcaster_id": broadcaster_id, "first": first}

        if user_ids is not None:
            params["user_id"] = user_ids

        route: Route = Route("GET", "moderation/moderators", params=params, token_for=token_for)

        def converter(data: ModeratorsResponseData, *, raw: Any) -> PartialUser:
            return PartialUser(data["user_id"], data["user_login"], http=self)

        iterator: HTTPAsyncIterator[PartialUser] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    @handle_user_ids()
    async def post_channel_moderator(
        self,
        broadcaster_id: str | int,
        token_for: str,
        user_id: str | int | PartialUser,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "user_id": user_id}

        route: Route = Route("POST", "moderation/moderators", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def delete_channel_moderator(
        self,
        broadcaster_id: str | int,
        token_for: str | PartialUser,
        user_id: str | int,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "user_id": user_id}

        route: Route = Route("DELETE", "moderation/moderators", params=params, token_for=token_for)
        return await self.request_json(route)

    def get_vips(
        self,
        broadcaster_id: str | int,
        token_for: str,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[PartialUser]:
        params: dict[str, str | int | list[str | int]] = {"broadcaster_id": broadcaster_id, "first": first}

        if user_ids is not None:
            params["user_id"] = user_ids

        route: Route = Route("GET", "channels/vips", params=params, token_for=token_for)

        def converter(data: ModeratorsResponseData, *, raw: Any) -> PartialUser:
            return PartialUser(data["user_id"], data["user_login"], http=self)

        iterator: HTTPAsyncIterator[PartialUser] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    @handle_user_ids()
    async def add_vip(
        self,
        broadcaster_id: str | int,
        token_for: str,
        user_id: str | int | PartialUser,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "user_id": user_id}

        route: Route = Route("POST", "channels/vips", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def delete_vip(
        self,
        broadcaster_id: str | int,
        token_for: str,
        user_id: str | int | PartialUser,
    ) -> None:
        params = {"broadcaster_id": broadcaster_id, "user_id": user_id}

        route: Route = Route("DELETE", "channels/vips", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def put_shield_mode_status(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
        active: bool,
    ) -> ShieldModeStatusResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        data = {"is_active": active}

        route: Route = Route("PUT", "moderation/shield_mode", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_shield_mode_status(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        token_for: str | PartialUser,
    ) -> ShieldModeStatusResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}

        route: Route = Route("GET", "moderation/shield_mode", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def post_warn_chat_user(
        self,
        broadcaster_id: str | int,
        moderator_id: str | int | PartialUser,
        user_id: str | int | PartialUser,
        reason: str,
        token_for: str | PartialUser,
    ) -> WarnChatUserResponse:
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id}
        data = {"data": {"user_id": user_id, "reason": reason}}

        route: Route = Route("POST", "moderation/warnings", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    ### Polls ###

    def get_polls(
        self,
        broadcaster_id: str | int,
        token_for: str,
        ids: list[str] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Poll]:
        params: dict[str, str | int | list[str]] = {"broadcaster_id": broadcaster_id, "first": first}

        if ids is not None:
            params["id"] = ids

        route: Route = Route("GET", "polls", params=params, token_for=token_for)

        def converter(data: PollsResponseData, *, raw: Any) -> Poll:
            return Poll(data, http=self)

        iterator: HTTPAsyncIterator[Poll] = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    async def post_poll(
        self,
        broadcaster_id: str | int,
        title: str,
        choices: list[str],
        duration: int,
        token_for: str,
        channel_points_voting_enabled: bool = False,
        channel_points_per_vote: int | None = None,
    ) -> PollsResponse:
        _choices = [{"title": t} for t in choices]
        data = {
            "broadcaster_id": broadcaster_id,
            "title": title,
            "choices": _choices,
            "duration": duration,
            "channel_points_voting_enabled": channel_points_voting_enabled,
        }

        if channel_points_per_vote is not None:
            data["channel_points_per_vote"] = channel_points_per_vote

        route: Route = Route("POST", "polls", json=data, token_for=token_for)
        return await self.request_json(route)

    async def patch_poll(
        self,
        broadcaster_id: str | int,
        id: str,
        status: Literal["ARCHIVED", "TERMINATED"],
        token_for: str,
    ) -> PollsResponse:
        data = {
            "broadcaster_id": broadcaster_id,
            "id": id,
            "status": status,
        }

        route: Route = Route("PATCH", "polls", json=data, token_for=token_for)
        return await self.request_json(route)

    ### Predictions ###

    def get_predictions(
        self,
        broadcaster_id: str | int,
        token_for: str,
        ids: list[str] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Prediction]:
        params: dict[str, str | int | list[str]] = {"broadcaster_id": broadcaster_id, "first": first}

        if ids is not None:
            params["id"] = ids

        route: Route = Route("GET", "predictions", params=params, token_for=token_for)

        def converter(data: PredictionsResponseData, *, raw: Any) -> Prediction:
            return Prediction(data, http=self)

        iterator: HTTPAsyncIterator[Prediction] = self.request_paginated(route, converter=converter, max_results=max_results)

        return iterator

    async def post_prediction(
        self,
        broadcaster_id: str | int,
        title: str,
        outcomes: list[str],
        prediction_window: int,
        token_for: str,
    ) -> PredictionsResponse:
        _outcomes = [{"title": t} for t in outcomes]

        data = {
            "broadcaster_id": broadcaster_id,
            "title": title,
            "outcomes": _outcomes,
            "prediction_window": prediction_window,
        }

        route: Route = Route("POST", "predictions", json=data, token_for=token_for)
        return await self.request_json(route)

    async def patch_prediction(
        self,
        broadcaster_id: str | int,
        id: str,
        status: Literal["RESOLVED", "CANCELED", "LOCKED"],
        token_for: str,
        winning_outcome_id: str | None = None,
    ) -> PredictionsResponse:
        data = {
            "broadcaster_id": broadcaster_id,
            "id": id,
            "status": status,
        }

        if winning_outcome_id is not None:
            data["winning_outcome_id"] = winning_outcome_id

        route: Route = Route("PATCH", "predictions", json=data, token_for=token_for)
        return await self.request_json(route)

    ### Raids ###

    @handle_user_ids()
    async def post_raid(
        self,
        from_broadcaster_id: str | int,
        to_broadcaster_id: str | int | PartialUser,
        token_for: str,
    ) -> StartARaidResponse:
        params = {"from_broadcaster_id": from_broadcaster_id, "to_broadcaster_id": to_broadcaster_id}
        route: Route = Route("POST", "raids", params=params, token_for=token_for)

        return await self.request_json(route)

    async def delete_raid(self, broadcaster_id: str | int, token_for: str) -> None:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("DELETE", "raids", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Schedule ###

    @handle_user_ids()
    def get_channel_stream_schedule(
        self,
        *,
        broadcaster_id: str | int,
        ids: list[str] | None = None,
        start_time: datetime.datetime | None = None,
        first: int = 20,
        token_for: str | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Schedule]:
        params: dict[str, str | int | list[str]] = {
            "broadcaster_id": broadcaster_id,
            "first": first,
        }

        if ids is not None:
            params["id"] = ids
        if start_time is not None:
            params["start_time"] = url_encode_datetime(start_time)

        route: Route = Route("GET", "schedule", params=params, token_for=token_for)

        def converter(data: str, *, raw: ChannelStreamScheduleResponse) -> Schedule:
            return Schedule(raw["data"], http=self)

        iterator: HTTPAsyncIterator[Schedule] = self.request_paginated(
            route=route, max_results=max_results, converter=converter, nested_key="segments"
        )
        return iterator

    async def patch_channel_stream_schedule(
        self,
        broadcaster_id: str | int,
        vacation: bool,
        token_for: str,
        vacation_start_time: datetime.datetime | None = None,
        vacation_end_time: datetime.datetime | None = None,
        timezone: str | None = None,
    ) -> None:
        params = {
            "broadcaster_id": broadcaster_id,
            "is_vacation_enabled": vacation,
        }

        if vacation and vacation_start_time is not None and vacation_end_time is not None and timezone is not None:
            params["vacation_start_time"] = url_encode_datetime(vacation_start_time)
            params["vacation_end_time"] = url_encode_datetime(vacation_end_time)
            params["timezone"] = timezone

        route: Route = Route("PATCH", "schedule/settings", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def post_channel_stream_schedule_segment(
        self,
        broadcaster_id: str | int,
        token_for: str | PartialUser,
        start_time: datetime.datetime,
        timezone: str,
        duration: int,
        recurring: bool = True,
        category_id: str | None = None,
        title: str | None = None,
    ) -> CreateChannelStreamScheduleSegmentResponse:
        params = {"broadcaster_id": broadcaster_id}

        _start_time = (
            start_time.isoformat() if start_time.tzinfo is not None else start_time.replace(tzinfo=datetime.UTC).isoformat()
        )

        data = {
            "start_time": _start_time,
            "timezone": timezone,
            "duration": duration,
            "is_recurring": recurring,
        }

        if category_id is not None:
            data["category_id"] = category_id
        if title is not None:
            data["title"] = title

        route: Route = Route("POST", "schedule/segment", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    async def patch_channel_stream_schedule_segment(
        self,
        broadcaster_id: str | int,
        token_for: str,
        id: str,
        start_time: datetime.datetime | None = None,
        timezone: str | None = None,
        duration: int | None = None,
        canceled: bool | None = None,
        category_id: str | None = None,
        title: str | None = None,
    ) -> UpdateChannelStreamScheduleSegmentResponse:
        params = {"broadcaster_id": broadcaster_id, "id": id}

        data: dict[str, str | int | bool] = {}

        if start_time is not None:
            _start_time = (
                start_time.isoformat()
                if start_time.tzinfo is not None
                else start_time.replace(tzinfo=datetime.UTC).isoformat()
            )
            data["start_time"] = _start_time
        if category_id is not None:
            data["category_id"] = category_id
        if title is not None:
            data["title"] = title
        if timezone is not None:
            data["timezone"] = timezone
        if duration is not None:
            data["duration"] = duration
        if canceled is not None:
            data["is_canceled"] = canceled

        route: Route = Route("PATCH", "schedule/segment", params=params, json=data, token_for=token_for)
        return await self.request_json(route)

    async def delete_channel_stream_schedule_segment(self, broadcaster_id: str | int, id: str, token_for: str) -> None:
        params = {"broadcaster_id": broadcaster_id, "id": id}
        route: Route = Route("DELETE", "schedule/segment", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Search ###

    @handle_user_ids()
    def get_search_categories(
        self,
        *,
        query: str,
        first: int,
        token_for: str | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Game]:
        params: dict[str, str | int | Sequence[str | int]] = {
            "query": query,
            "first": first,
        }
        route: Route = Route("GET", "search/categories", params=params, token_for=token_for)

        def converter(data: GamesResponseData, *, raw: Any) -> Game:
            return Game(data, http=self)

        iterator: HTTPAsyncIterator[Game] = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    def get_search_channels(
        self,
        *,
        query: str,
        first: int,
        live: bool = False,
        token_for: str | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[SearchChannel]:
        params: dict[str, str | int] = {"query": query, "live_only": live, "first": first}
        route: Route = Route("GET", "search/channels", params=params, token_for=token_for)

        def converter(data: SearchChannelsResponseData, *, raw: Any) -> SearchChannel:
            return SearchChannel(data, http=self)

        iterator: HTTPAsyncIterator[SearchChannel] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    ### Streams ###

    @handle_user_ids()
    def get_streams(
        self,
        *,
        first: int = 20,
        user_ids: list[int | str] | None = None,
        game_ids: list[int | str] | None = None,
        user_logins: list[int | str] | None = None,
        languages: list[str] | None = None,
        token_for: str | PartialUser | None = None,
        type: Literal["all", "live"] = "all",
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Stream]:
        params: dict[str, str | int | Sequence[str | int]] = {
            "type": type,
            "first": first,
        }

        if user_ids is not None:
            params["user_id"] = user_ids
        if game_ids is not None:
            params["game_ids"] = game_ids
        if user_logins is not None:
            params["user_login"] = user_logins
        if languages is not None:
            params["language"] = languages

        route: Route = Route("GET", "streams", params=params, token_for=token_for)

        def converter(data: StreamsResponseData, *, raw: Any) -> Stream:
            return Stream(data, http=self)

        iterator: HTTPAsyncIterator[Stream] = self.request_paginated(route, converter=converter, max_results=max_results)

        return iterator

    async def get_stream_key(self, broadcaster_id: str | int, token_for: str | PartialUser) -> StreamKeyResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "streams/key", params=params, token_for=token_for)
        return await self.request_json(route)

    def get_followed_streams(
        self,
        *,
        user_id: str | int,
        token_for: str,
        first: int = 100,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Stream]:
        params = {
            "user_id": user_id,
            "first": first,
        }

        route: Route = Route("GET", "streams/followed", params=params, token_for=token_for)

        def converter(data: StreamsResponseData, *, raw: Any) -> Stream:
            return Stream(data, http=self)

        iterator: HTTPAsyncIterator[Stream] = self.request_paginated(route, converter=converter, max_results=max_results)

        return iterator

    @handle_user_ids()
    async def post_stream_marker(
        self,
        user_id: str | int,
        token_for: str | PartialUser,
        description: str | None = None,
    ) -> CreateStreamMarkerResponse:
        data = {"user_id": user_id}
        if description is not None:
            data["description"] = description

        route: Route = Route("POST", "streams/markers", json=data, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    def get_stream_markers(
        self,
        *,
        user_id: str | int | None = None,
        video_id: str | None = None,
        token_for: str | PartialUser,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[VideoMarkers]:
        params: dict[str, str | int] = {"first": first}

        if user_id is not None:
            params["user_id"] = user_id
        if video_id is not None:
            params["video_id"] = video_id

        route: Route = Route("GET", "streams/markers", params=params, token_for=token_for)

        def converter(data: StreamMarkersResponseData, *, raw: Any) -> VideoMarkers:
            return VideoMarkers(data, http=self)

        iterator: HTTPAsyncIterator[VideoMarkers] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    ### Subscriptions ###

    @handle_user_ids()
    async def get_user_subscription(
        self,
        broadcaster_id: str | int,
        user_id: str | int,
        token_for: str,
    ) -> CheckUserSubscriptionResponse:
        params = {"broadcaster_id": broadcaster_id, "user_id": user_id}

        route: Route = Route("GET", "subscriptions/user", params=params, token_for=token_for)
        return await self.request_json(route)

    async def get_broadcaster_subscriptions(
        self,
        token_for: str,
        broadcaster_id: str | int,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> BroadcasterSubscriptions:
        params: dict[str, list[str | int] | str | int] = {"broadcaster_id": broadcaster_id, "first": first}
        if user_ids is not None:
            params["user_id"] = user_ids

        route: Route = Route("GET", "subscriptions", params=params, token_for=token_for)

        def converter(data: BroadcasterSubscriptionsResponseData, *, raw: Any) -> BroadcasterSubscription:
            return BroadcasterSubscription(data, http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        data = await self.request_json(route)

        return BroadcasterSubscriptions(data, iterator)

    ### Tags ###

    ### Teams ###

    @handle_user_ids()
    async def get_teams(
        self,
        *,
        team_name: str | None = None,
        team_id: str | None = None,
        token_for: str | PartialUser | None = None,
    ) -> TeamsResponse:
        params: dict[str, str] = {}

        if team_name:
            params = params = {"name": team_name}
        elif team_id:
            params = {"id": team_id}

        route: Route = Route("GET", "teams", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_channel_teams(
        self,
        *,
        broadcaster_id: str,
        token_for: str | PartialUser | None = None,
    ) -> ChannelTeamsResponse:
        params = {"broadcaster_id": broadcaster_id}

        route: Route = Route("GET", "teams/channel", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Users ###

    @handle_user_ids()
    async def get_users(
        self, ids: list[str | int] | None = None, logins: list[str] | None = None, token_for: str | PartialUser | None = None
    ) -> UsersResponse:
        params = {"id": ids, "login": logins}
        route: Route = Route("GET", "users", params=params, token_for=token_for)
        return await self.request_json(route)

    async def put_user(self, token_for: str, description: str | None) -> UpdateUserResponse:
        params = {"description": description} if description is not None else {"description": ""}
        route: Route = Route("PUT", "users", params=params, token_for=token_for)
        return await self.request_json(route)

    def get_user_block_list(
        self, broadcaster_id: str | int, token_for: str, first: int = 20, max_results: int | None = None
    ) -> HTTPAsyncIterator[PartialUser]:
        params = {"broadcaster_id": broadcaster_id, "first": first}

        route: Route = Route("GET", "users/blocks", params=params, token_for=token_for)

        def converter(data: UserBlockListResponseData, *, raw: Any) -> PartialUser:
            return PartialUser(data["user_id"], data["user_login"], http=self)

        iterator: HTTPAsyncIterator[PartialUser] = self.request_paginated(
            route, converter=converter, max_results=max_results
        )

        return iterator

    @handle_user_ids()
    async def put_block_user(
        self,
        user_id: str | int | PartialUser,
        token_for: str | PartialUser,
        source: Literal["chat", "whisper"] | None = None,
        reason: Literal["harassment", "spam", "other"] | None = None,
    ) -> None:
        params = {"target_user_id": user_id}
        if source is not None:
            params["source_context"] = source
        if reason is not None:
            params["reason"] = reason
        route: Route = Route("PUT", "users/blocks", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def delete_block_user(
        self,
        user_id: str | int | PartialUser,
        token_for: str,
    ) -> None:
        params = {"target_user_id": user_id}
        route: Route = Route("DELETE", "users/blocks", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_user_extensions(self, token_for: str | PartialUser) -> UserExtensionsResponse:
        route: Route = Route("GET", "users/extensions/list", token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def get_active_user_extensions(
        self, *, user_id: str | int | None = None, token_for: str | PartialUser | None = None
    ) -> UserActiveExtensionsResponse:
        params: dict[str, str | int] = {"user_id": user_id} if user_id is not None else {}
        route: Route = Route("GET", "users/extensions", params=params, token_for=token_for)
        return await self.request_json(route)

    @handle_user_ids()
    async def put_user_extensions(
        self, *, user_extensions: ActiveExtensions, token_for: str | PartialUser
    ) -> UpdateUserExtensionsResponse:
        data = {"data": user_extensions._to_dict()}
        route: Route = Route("PUT", "users/extensions", json=data, token_for=token_for)
        return await self.request_json(route)

    ### Videos ###

    @handle_user_ids()
    def get_videos(
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
        params: dict[str, int | str | list[str | int]] = {"first": first, "period": period, "sort": sort, "type": type}

        if ids is not None:
            params["id"] = ids
        if user_id is not None:
            params["user_id"] = str(user_id)
        if game_id is not None:
            params["game_id"] = game_id
        if language is not None:
            params["language"] = language

        route = Route("GET", "videos", params=params, token_for=token_for)

        def converter(data: VideosResponseData, *, raw: Any) -> Video:
            return Video(data, http=self)

        iterator = self.request_paginated(route, converter=converter, max_results=max_results)
        return iterator

    @handle_user_ids()
    async def delete_videos(self, ids: list[str | int], token_for: str | PartialUser) -> DeleteVideosResponse:
        params = {"id": ids}

        route: Route = Route("DELETE", "videos", params=params, token_for=token_for)
        return await self.request_json(route)

    ### Whispers ###

    @handle_user_ids()
    async def post_whisper(
        self, from_user_id: str | int, to_user_id: str | int | PartialUser, token_for: str | PartialUser, message: str
    ) -> None:
        params = {"from_user_id": from_user_id, "to_user_id": to_user_id}
        data = {"message": message}

        route: Route = Route("POST", "whispers", params=params, json=data, token_for=token_for)
        return await self.request_json(route)
