"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import copy
import datetime
import logging
from typing import TYPE_CHECKING, Union, List, Tuple, Any, Dict, Optional
from typing_extensions import Literal

import aiohttp
from yarl import URL

from . import errors
from .cooldowns import RateBucket

try:
    import ujson as json
except Exception:
    import json
if TYPE_CHECKING:
    from .client import Client
logger = logging.getLogger("twitchio.http")


class Route:
    BASE_URL = "https://api.twitch.tv/helix"

    __slots__ = "path", "body", "headers", "query", "method"

    def __init__(
        self,
        method: str,
        path: Union[str, URL],
        body: Union[str, dict] = None,
        query: List[Tuple[str, Any]] = None,
        headers: dict = None,
        token: str = None,
    ):
        self.headers = headers or {}
        self.method = method
        self.query = query

        if token:
            self.headers["Authorization"] = "Bearer " + token
        if isinstance(path, URL):
            self.path = path
        else:
            self.path = URL(self.BASE_URL + "/" + path.rstrip("/"))
        if query:
            self.path = self.path.with_query(query)
        if isinstance(body, dict):
            self.body = json.dumps(body)
            self.headers["Content-Type"] = "application/json"
        else:
            self.body = body


class TwitchHTTP:
    TOKEN_BASE = "https://id.twitch.tv/oauth2/token"

    def __init__(
        self, client: "Client", *, api_token: str = None, client_secret: str = None, client_id: str = None, **kwargs
    ):
        self.client = client
        self.session = None
        self.token = api_token
        self.app_token = None
        self._refresh_token = None
        self.client_secret = client_secret
        self.client_id = client_id
        self.nick = None
        self.user_id: Optional[int] = None

        self.bucket = RateBucket(method="http")
        self.scopes = kwargs.get("scopes", [])

    async def request(self, route: Route, *, paginate=True, limit=100, full_body=False, force_app_token=False):
        """
        Fulfills an API request

        Parameters
        -----------
        route : :class:`twitchio.http.Route`
            The route to follow
        paginate : :class:`bool`
            whether or not to paginate the requests where possible. Defaults to True
        limit : :class:`int`
            The data limit per request when paginating. Defaults to 100
        full_body : class:`bool`
            Whether to return the full response body or to accumulate the `data` key. Defaults to False. `paginate` must be False if this is True.
        force_app_token : :class:`bool`
            Forcibly use the client_id and client_secret generated token, if available. Otherwise fail the request immediately
        """
        if full_body:
            assert not paginate
        if (not self.client_id or not self.nick) and self.token:
            await self.validate(token=self.token)
        if not self.client_id:
            raise errors.NoClientID("A Client ID is required to use the Twitch API")
        headers = route.headers or {}

        if force_app_token and "Authorization" not in headers:
            if not self.client_secret:
                raise errors.NoToken(
                    "An app access token is required for this route, please provide a client id and client secret"
                )
            if self.app_token is None:
                await self._generate_login()
                headers["Authorization"] = f"Bearer {self.app_token}"
        elif not self.token and not self.client_secret and "Authorization" not in headers:
            raise errors.NoToken(
                "Authorization is required to use the Twitch API. Pass token and/or client_secret to the Client constructor"
            )
        if "Authorization" not in headers:
            if not self.token:
                await self._generate_login()
            headers["Authorization"] = f"Bearer {self.token}"
        headers["Client-ID"] = self.client_id

        if not self.session:
            self.session = aiohttp.ClientSession()
        if self.bucket.limited:
            await self.bucket
        cursor = None
        data = []

        def reached_limit():
            return limit and len(data) >= limit

        def get_limit():
            if limit is None:
                return "100"
            to_get = limit - len(data)
            return str(to_get) if to_get < 100 else "100"

        is_finished = False
        while not is_finished:
            path = copy.copy(route.path)

            if limit is not None and paginate:
                q = route.query or []
                if cursor is not None:
                    q = [("after", cursor), *q]
                q = [("first", get_limit()), *q]
                path = path.with_query(q)
            body, is_text = await self._request(route, path, headers)
            if is_text:
                return body
            if full_body:
                return body
            data += body["data"]

            try:
                cursor = body["pagination"].get("cursor", None)
            except KeyError:
                break
            else:
                if not cursor:
                    break
            is_finished = reached_limit() if limit is not None else True if paginate else True
        return data

    async def _request(self, route, path, headers, utilize_bucket=True):
        reason = None

        for attempt in range(5):
            if utilize_bucket and self.bucket.limited:
                await self.bucket.wait_reset()
            async with self.session.request(route.method, path, headers=headers, data=route.body) as resp:
                try:
                    logger.debug(f"Received a response from a request with status {resp.status}: {await resp.json()}")
                except Exception:
                    logger.debug(f"Received a response from a request with status {resp.status} and without body")
                if 500 <= resp.status <= 504:
                    reason = resp.reason
                    await asyncio.sleep(2**attempt + 1)
                    continue
                if utilize_bucket:
                    reset = resp.headers.get("Ratelimit-Reset")
                    remaining = resp.headers.get("Ratelimit-Remaining")

                    self.bucket.update(reset=reset, remaining=remaining)
                if 200 <= resp.status < 300:
                    if resp.content_type == "application/json":
                        return await resp.json(), False
                    return await resp.text(encoding="utf-8"), True
                if resp.status == 401:
                    if "WWW-Authenticate" in resp.headers:
                        try:
                            await self._generate_login()
                        except:
                            raise errors.Unauthorized(
                                "Your oauth token is invalid, and a new one could not be generated"
                            )
                    print(resp.reason, await resp.json(), resp)
                    raise errors.Unauthorized("You're not authorized to use this route.")
                if resp.status == 429:
                    reason = "Ratelimit Reached"

                    if not utilize_bucket:  # non Helix APIs don't have ratelimit headers
                        await asyncio.sleep(3**attempt + 1)
                    continue
                raise errors.HTTPException(
                    f"Failed to fulfil request ({resp.status}).", reason=resp.reason, status=resp.status
                )
        raise errors.HTTPException("Failed to reach Twitch API", reason=reason, status=resp.status)

    async def _generate_login(self):
        try:
            token = await self.client.event_token_expired()
            if token is not None:
                assert isinstance(token, str), TypeError(f"Expected a string, got {type(token)}")
                self.token = self.app_token = token
                return
        except Exception as e:
            self.client.run_event("error", e)
        if not self.client_id or not self.client_secret:
            raise errors.HTTPException("Unable to generate a token, client id and/or client secret not given")
        if self._refresh_token:
            url = (
                self.TOKEN_BASE
                + "?grant_type=refresh_token&refresh_token={0}&client_id={1}&client_secret={2}".format(
                    self._refresh_token, self.client_id, self.client_secret
                )
            )
        else:
            url = self.TOKEN_BASE + "?client_id={0}&client_secret={1}&grant_type=client_credentials".format(
                self.client_id, self.client_secret
            )
            if self.scopes:
                url += "&scope=" + " ".join(self.scopes)
        if not self.session:
            self.session = aiohttp.ClientSession()
        async with self.session.post(url) as resp:
            if resp.status > 300 or resp.status < 200:
                raise errors.HTTPException("Unable to generate a token: " + await resp.text())
            data = await resp.json()
            self.token = self.app_token = data["access_token"]
            self._refresh_token = data.get("refresh_token", None)
            logger.info("Invalid or no token found, generated new token: %s", self.token)

    async def validate(self, *, token: str = None) -> dict:
        if not token:
            token = self.token
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = "https://id.twitch.tv/oauth2/validate"
        headers = {"Authorization": f"OAuth {token}"}

        async with self.session.get(url, headers=headers) as resp:
            if resp.status == 401:
                raise errors.AuthenticationError("Invalid or unauthorized Access Token passed.")
            if resp.status > 300 or resp.status < 200:
                raise errors.HTTPException("Unable to validate Access Token: " + await resp.text())
            data: dict = await resp.json()
        if not self.nick:
            self.nick = data.get("login")
            self.user_id = data.get("user_id") and int(data["user_id"])
            self.client_id = data.get("client_id")
        return data

    async def post_commercial(self, token: str, broadcaster_id: str, length: int):
        assert length in {30, 60, 90, 120, 150, 180}
        data = await self.request(
            Route(
                "POST", "channels/commercial", body={"broadcaster_id": broadcaster_id, "length": length}, token=token
            ),
            paginate=False,
        )
        data = data[0]
        if data["message"]:
            raise errors.HTTPException(data["message"], extra=data["retry_after"])

    async def get_extension_analytics(
        self,
        token: str,
        extension_id: str = None,
        type: str = None,
        started_at: datetime.datetime = None,
        ended_at: datetime.datetime = None,
    ):
        raise NotImplementedError  # TODO

    async def get_game_analytics(
        self,
        token: str,
        game_id: str = None,
        type: str = None,
        started_at: datetime.datetime = None,
        ended_at: datetime.datetime = None,
    ):
        raise NotImplementedError  # TODO

    async def get_bits_board(
        self,
        token: str,
        period: str = "all",
        user_id: Optional[str] = None,
        started_at: Optional[datetime.datetime] = None,
    ):
        assert period in {"all", "day", "week", "month", "year"}
        query = [
            ("period", period),
            ("started_at", started_at.isoformat() if started_at else None),
            ("user_id", user_id),
        ]

        route = Route(
            "GET",
            "bits/leaderboard",
            "",
            query=[q for q in query if q[1] is not None],
            token=token,
        )
        return await self.request(route, full_body=True, paginate=False)

    async def get_cheermotes(self, broadcaster_id: str):
        return await self.request(Route("GET", "bits/cheermotes", "", query=[("broadcaster_id", broadcaster_id)]))

    async def get_channel_emotes(self, broadcaster_id: str):
        return await self.request(Route("GET", "chat/emotes", "", query=[("broadcaster_id", broadcaster_id)]))

    async def get_global_emotes(self):
        return await self.request(Route("GET", "chat/emotes/global", ""))

    async def get_extension_transactions(self, extension_id: str, ids: List[Any] = None):
        q = [("extension_id", extension_id)]
        if ids:
            q.extend(("id", id) for id in ids)
        return await self.request(Route("GET", "extensions/transactions", "", query=q))

    async def create_reward(
        self,
        token: str,
        broadcaster_id: int,
        title: str,
        cost: int,
        prompt: Optional[str] = None,
        is_enabled: Optional[bool] = True,
        background_color: Optional[str] = None,
        user_input_required: Optional[bool] = False,
        max_per_stream: Optional[int] = None,
        max_per_user: Optional[int] = None,
        global_cooldown: Optional[int] = None,
        fufill_immediatly: Optional[bool] = False,
    ):
        params = [("broadcaster_id", str(broadcaster_id))]
        data = {
            "title": title,
            "cost": cost,
            "prompt": prompt,
            "is_enabled": is_enabled,
            "is_user_input_required": user_input_required,
            "should_redemptions_skip_request_queue": fufill_immediatly,
        }
        if max_per_stream:
            data["max_per_stream"] = max_per_stream
            data["is_max_per_stream_enabled"] = True
        if max_per_user:
            data["max_per_user_per_stream"] = max_per_user
            data["is_max_per_user_per_stream_enabled"] = True
        if background_color:
            data["background_color"] = background_color
        if global_cooldown:
            data["global_cooldown_seconds"] = global_cooldown
            data["is_global_cooldown_enabled"] = True
        return await self.request(Route("POST", "channel_points/custom_rewards", query=params, body=data, token=token))

    async def get_rewards(self, token: str, broadcaster_id: int, only_manageable: bool = False, ids: List[int] = None):
        params = [("broadcaster_id", str(broadcaster_id)), ("only_manageable_rewards", str(only_manageable))]

        if ids:
            params.extend(("id", str(id)) for id in ids)
        return await self.request(Route("GET", "channel_points/custom_rewards", query=params, token=token))

    async def update_reward(
        self,
        token: str,
        broadcaster_id: int,
        reward_id: str,
        title: Optional[str] = None,
        prompt: Optional[str] = None,
        cost: Optional[int] = None,
        background_color: Optional[str] = None,
        enabled: Optional[bool] = None,
        input_required: Optional[bool] = None,
        max_per_stream_enabled: Optional[bool] = None,
        max_per_stream: Optional[int] = None,
        max_per_user_per_stream_enabled: Optional[bool] = None,
        max_per_user_per_stream: Optional[int] = None,
        global_cooldown_enabled: Optional[bool] = None,
        global_cooldown: Optional[int] = None,
        paused: Optional[bool] = None,
        redemptions_skip_queue: Optional[bool] = None,
    ):
        data = {
            "title": title,
            "prompt": prompt,
            "cost": cost,
            "background_color": background_color,
            "enabled": enabled,
            "is_user_input_required": input_required,
            "is_max_per_stream_enabled": max_per_stream_enabled,
            "max_per_stream": max_per_stream,
            "is_max_per_user_per_stream_enabled": max_per_user_per_stream_enabled,
            "max_per_user_per_stream": max_per_user_per_stream,
            "is_global_cooldown_enabled": global_cooldown_enabled,
            "global_cooldown_seconds": global_cooldown,
            "is_paused": paused,
            "should_redemptions_skip_request_queue": redemptions_skip_queue,
        }

        data = {k: v for k, v in data.items() if v is not None}

        if not data:
            raise ValueError("Nothing changed!")
        params = [("broadcaster_id", str(broadcaster_id)), ("id", str(reward_id))]
        return await self.request(
            Route(
                "PATCH",
                "channel_points/custom_rewards",
                query=params,
                headers={"Authorization": f"Bearer {token}"},
                body=data,
            )
        )

    async def delete_custom_reward(self, token: str, broadcaster_id: int, reward_id: str):
        params = [("broadcaster_id", str(broadcaster_id)), ("id", reward_id)]
        return await self.request(Route("DELETE", "channel_points/custom_rewards", query=params, token=token))

    async def get_reward_redemptions(
        self,
        token: str,
        broadcaster_id: int,
        reward_id: str,
        redemption_id: Optional[str] = None,
        status: Optional[str] = None,
        sort: str = "OLDEST",
        first: int = 20,
    ):
        params = [("broadcaster_id", str(broadcaster_id)), ("reward_id", reward_id), ("first", first)]
        if redemption_id:
            params.append(("id", redemption_id))
        if status:
            params.append(("status", status))
        if sort:
            params.append(("sort", sort))
        return await self.request(Route("GET", "channel_points/custom_rewards/redemptions", query=params, token=token))

    async def update_reward_redemption_status(
        self, token: str, broadcaster_id: int, reward_id: str, custom_reward_id: str, status: bool
    ):
        params = [("id", reward_id), ("broadcaster_id", str(broadcaster_id)), ("reward_id", custom_reward_id)]
        status = "FULFILLED" if status else "CANCELED"
        return await self.request(
            Route(
                "PATCH",
                "channel_points/custom_rewards/redemptions",
                query=params,
                body={"status": status},
                token=token,
            )
        )

    async def get_predictions(
        self,
        token: str,
        broadcaster_id: int,
        prediction_id: Optional[str] = None,
    ):
        params = [("broadcaster_id", str(broadcaster_id))]

        if prediction_id:
            params.extend(("prediction_id", prediction_id))
        return await self.request(Route("GET", "predictions", query=params, token=token), paginate=False)

    async def patch_prediction(
        self, token: str, broadcaster_id: str, prediction_id: str, status: str, winning_outcome_id: Optional[str] = None
    ):
        body = {
            "broadcaster_id": broadcaster_id,
            "id": prediction_id,
            "status": status,
        }

        if status == "RESOLVED" and winning_outcome_id:
            body["winning_outcome_id"] = winning_outcome_id

        return await self.request(
            Route(
                "PATCH",
                "predictions",
                body=body,
                token=token,
            )
        )

    async def post_prediction(
        self, token: str, broadcaster_id: int, title: str, blue_outcome: str, pink_outcome: str, prediction_window: int
    ):
        body = {
            "broadcaster_id": broadcaster_id,
            "title": title,
            "prediction_window": prediction_window,
            "outcomes": [
                {
                    "title": blue_outcome,
                },
                {
                    "title": pink_outcome,
                },
            ],
        }
        return await self.request(
            Route("POST", "predictions", body=body, token=token),
            paginate=False,
        )

    async def post_create_clip(self, token: str, broadcaster_id: int, has_delay=False):
        return await self.request(
            Route(
                "POST", "clips", query=[("broadcaster_id", broadcaster_id), ("has_delay", str(has_delay))], token=token
            ),
            paginate=False,
        )

    async def get_clips(
        self,
        broadcaster_id: int = None,
        game_id: str = None,
        ids: Optional[List[str]] = None,
        started_at: Optional[datetime.datetime] = None,
        ended_at: Optional[datetime.datetime] = None,
        token: Optional[str] = None,
    ):
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=datetime.timezone.utc)
        if ended_at and ended_at.tzinfo is None:
            ended_at = ended_at.replace(tzinfo=datetime.timezone.utc)

        q = [
            ("broadcaster_id", broadcaster_id),
            ("game_id", game_id),
            ("started_at", started_at.isoformat() if started_at else None),
            ("ended_at", ended_at.isoformat() if ended_at else None),
        ]
        if ids:
            q.extend(("id", id) for id in ids)
        query = [x for x in q if x[1] is not None]

        return await self.request(Route("GET", "clips", query=query, token=token))

    async def post_entitlements_upload(self, manifest_id: str, type="bulk_drops_grant"):
        return await self.request(
            Route("POST", "entitlements/upload", query=[("manifest_id", manifest_id), ("type", type)])
        )

    async def get_entitlements(self, id: str = None, user_id: str = None, game_id: str = None):
        return await self.request(
            Route("GET", "entitlements/drops", query=[("id", id), ("user_id", user_id), ("game_id", game_id)])
        )

    async def get_code_status(self, codes: List[str], user_id: int):
        q = [("user_id", user_id)]
        q.extend(("code", code) for code in codes)

        return await self.request(Route("GET", "entitlements/codes", query=q))

    async def post_redeem_code(self, user_id: int, codes: List[str]):
        q = [("user_id", user_id)]
        q.extend(("code", c) for c in codes)

        return await self.request(Route("POST", "entitlements/code", query=q))

    async def get_top_games(self):
        return await self.request(Route("GET", "games/top"))

    async def get_games(
        self, game_ids: Optional[List[Any]], game_names: Optional[List[str]], igdb_ids: Optional[List[int]]
    ):
        if not any((game_ids, game_names, igdb_ids)):
            raise ValueError("At least one of game id, name or IGDB id must be provided.")
        q = []
        if game_ids:
            q.extend(("id", id) for id in game_ids)
        if game_names:
            q.extend(("name", name) for name in game_names)
        if igdb_ids:
            q.extend(("igdb_id", id) for id in igdb_ids)
        return await self.request(Route("GET", "games", query=q))

    async def get_hype_train(self, broadcaster_id: str, id: Optional[str] = None, token: str = None):
        return await self.request(
            Route(
                "GET",
                "hypetrain/events",
                query=[x for x in [("broadcaster_id", broadcaster_id), ("id", id)] if x[1] is not None],
                token=token,
            )
        )

    async def post_automod_check(self, token: str, broadcaster_id: str, *msgs: List[Dict[str, str]]):
        print(msgs)
        return await self.request(
            Route(
                "POST",
                "moderation/enforcements/status",
                query=[("broadcaster_id", broadcaster_id)],
                body={"data": msgs},
                token=token,
            )
        )

    async def get_channel_ban_unban_events(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            q.extend(("user_id", id) for id in user_ids)
        return await self.request(Route("GET", "moderation/banned/events", query=q, token=token))

    async def get_channel_bans(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            q.extend(("user_id", id) for id in user_ids)
        return await self.request(Route("GET", "moderation/banned", query=q, token=token))

    async def get_channel_moderators(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            q.extend(("user_id", id) for id in user_ids)
        return await self.request(Route("GET", "moderation/moderators", query=q, token=token))

    async def get_channel_mod_events(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        q.extend(("user_id", id) for id in user_ids)

        return await self.request(Route("GET", "moderation/moderators/events", query=q, token=token))

    async def get_search_categories(self, query: str, token: str = None):
        return await self.request(Route("GET", "search/categories", query=[("query", query)], token=token))

    async def get_search_channels(self, query: str, token: str = None, live: bool = False):
        return await self.request(
            Route("GET", "search/channels", query=[("query", query), ("live_only", str(live))], token=token)
        )

    async def get_stream_key(self, token: str, broadcaster_id: str):
        return await self.request(
            Route("GET", "streams/key", query=[("broadcaster_id", broadcaster_id)], token=token), paginate=False
        )

    async def get_streams(
        self,
        game_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None,
        user_logins: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        type_: Literal["all", "live"] = "all",
        token: Optional[str] = None,
    ):
        q = [("type", type_)]
        if game_ids:
            q.extend(("game_id", str(g)) for g in game_ids)
        if user_ids:
            q.extend(("user_id", str(u)) for u in user_ids)
        if user_logins:
            q.extend(("user_login", l) for l in user_logins)
        if languages:
            q.extend(("language", l) for l in languages)
        return await self.request(Route("GET", "streams", query=q, token=token))

    async def post_stream_marker(self, token: str, user_id: str, description: str = None):
        return await self.request(
            Route("POST", "streams/markers", body={"user_id": user_id, "description": description}, token=token)
        )

    async def get_stream_markers(self, token: str, user_id: str = None, video_id: str = None):
        return await self.request(
            Route(
                "GET",
                "streams/markers",
                query=[x for x in [("user_id", user_id), ("video_id", video_id)] if x[1] is not None],
                token=token,
            )
        )

    async def get_channels(self, broadcaster_id: str, token: Optional[str] = None):
        return await self.request(Route("GET", "channels", query=[("broadcaster_id", broadcaster_id)], token=token))

    async def get_channels_new(self, broadcaster_ids: List[int], token: Optional[str] = None):
        if len(broadcaster_ids) > 100:
            raise ValueError("Maximum of 100 broadcaster_ids")
        q = [("broadcaster_id", str(broadcaster_id)) for broadcaster_id in broadcaster_ids]
        return await self.request(Route("GET", "channels", query=q, token=token))

    async def patch_channel(
        self, token: str, broadcaster_id: str, game_id: str = None, language: str = None, title: str = None
    ):
        assert any((game_id, language, title))
        body = {
            k: v
            for k, v in {"game_id": game_id, "broadcaster_language": language, "title": title}.items()
            if v is not None
        }

        return await self.request(
            Route("PATCH", "channels", query=[("broadcaster_id", broadcaster_id)], body=body, token=token)
        )

    async def get_channel_schedule(
        self,
        broadcaster_id: str,
        segment_ids: Optional[List[str]] = None,
        start_time: Optional[datetime.datetime] = None,
        utc_offset: Optional[int] = None,
        first: int = 20,
    ):
        if first > 25 or first < 1:
            raise ValueError("The parameter 'first' was malformed: the value must be less than or equal to 25")
        if segment_ids is not None and len(segment_ids) > 100:
            raise ValueError("segment_id can only have 100 entries")
        if start_time:
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if utc_offset:
            utc_offset = str(utc_offset)
        q = [
            x
            for x in [
                ("broadcaster_id", broadcaster_id),
                ("first", first),
                ("start_time", start_time),
                ("utc_offset", utc_offset),
            ]
            if x[1] is not None
        ]

        if segment_ids:
            q.extend(("id", id) for id in segment_ids)
        return await self.request(Route("GET", "schedule", query=q), paginate=False, full_body=True)

    async def get_channel_subscriptions(self, token: str, broadcaster_id: str, user_ids: Optional[List[str]] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            q.extend(("user_id", u) for u in user_ids)
        return await self.request(Route("GET", "subscriptions", query=q, token=token))

    async def get_stream_tags(self, tag_ids: Optional[List[str]] = None):
        q = []
        if tag_ids:
            q.extend(("tag_id", u) for u in tag_ids)
        return await self.request(Route("GET", "tags/streams", query=q or None))

    async def get_channel_tags(self, broadcaster_id: str):
        return await self.request(Route("GET", "streams/tags", query=[("broadcaster_id", broadcaster_id)]))

    async def put_replace_channel_tags(self, token: str, broadcaster_id: str, tag_ids: List[str] = None):
        return await self.request(
            Route(
                "PUT",
                "streams/tags",
                query=[("broadcaster_id", broadcaster_id)],
                body={"tag_ids": tag_ids},
                token=token,
            )
        )

    async def post_follow_channel(self, token: str, from_id: str, to_id: str, notifications=False):
        return await self.request(
            Route(
                "POST",
                "users/follows",
                query=[("from_id", from_id), ("to_id", to_id), ("allow_notifications", str(notifications))],
                token=token,
            )
        )

    async def delete_unfollow_channel(self, token: str, from_id: str, to_id: str):
        return await self.request(
            Route("DELETE", "users/follows", query=[("from_id", from_id), ("to_id", to_id)], token=token)
        )

    async def get_users(self, ids: List[int], logins: List[str], token: Optional[str] = None):
        q = []
        if ids:
            q.extend(("id", id) for id in ids)
        if logins:
            q.extend(("login", login) for login in logins)
        return await self.request(Route("GET", "users", query=q, token=token))

    async def get_user_follows(
        self, from_id: Optional[str] = None, to_id: Optional[str] = None, token: Optional[str] = None
    ):
        return await self.request(
            Route(
                "GET",
                "users/follows",
                query=[x for x in [("from_id", from_id), ("to_id", to_id)] if x[1] is not None],
                token=token,
            )
        )

    async def put_update_user(self, token: str, description: str):
        return await self.request(Route("PUT", "users", query=[("description", description)], token=token))

    async def get_channel_extensions(self, token: str):
        return await self.request(Route("GET", "users/extensions/list", token=token))

    async def get_user_active_extensions(self, token: str, user_id: str = None):
        return (
            await self.request(
                Route("GET", "users/extensions", query=[("user_id", user_id)], token=token),
                paginate=False,
                full_body=True,
            )
        )["data"]

    async def put_user_extensions(self, token: str, data: Dict[str, Any]):
        return (
            await self.request(
                Route("PUT", "users/extensions", token=token, body={"data": data}), paginate=False, full_body=True
            )
        )["data"]

    async def get_videos(
        self,
        ids: List[str] = None,
        user_id: str = None,
        game_id: str = None,
        sort: str = "time",
        type: str = "all",
        period: str = "all",
        language: str = None,
        token: str = None,
    ):
        q = [
            x
            for x in [
                ("user_id", user_id),
                ("game_id", game_id),
                ("sort", sort),
                ("type", type),
                ("period", period),
                ("lanaguage", language),
            ]
            if x[1] is not None
        ]

        if ids:
            q.extend(("id", id) for id in ids)
        return await self.request(Route("GET", "videos", query=q, token=token))

    async def delete_videos(self, token: str, ids: List[int]):
        q = [("id", str(x)) for x in ids]

        return (await self.request(Route("DELETE", "videos", query=q, token=token), paginate=False, full_body=True))[
            "data"
        ]

    async def get_webhook_subs(self):
        return await self.request(Route("GET", "webhooks/subscriptions"))

    async def get_teams(self, team_name: Optional[str] = None, team_id: Optional[str] = None):
        if team_name:
            q = [("name", team_name)]
        elif team_id:
            q = [("id", team_id)]
        else:
            raise ValueError("You need to provide a team name or id")
        return await self.request(Route("GET", "teams", query=q))

    async def get_channel_teams(self, broadcaster_id: str):
        q = [("broadcaster_id", broadcaster_id)]
        return await self.request(Route("GET", "teams/channel", query=q), paginate=False, full_body=True)

    async def get_polls(
        self,
        broadcaster_id: str,
        token: str,
        poll_ids: Optional[List[str]] = None,
        first: Optional[int] = 20,
    ):
        if poll_ids and len(poll_ids) > 100:
            raise ValueError("poll_ids can only have up to 100 entries")
        if first and (first > 25 or first < 1):
            raise ValueError("first can only be between 1 and 20")
        q = [("broadcaster_id", broadcaster_id), ("first", first)]

        if poll_ids:
            q.extend(("id", poll_id) for poll_id in poll_ids)
        return await self.request(Route("GET", "polls", query=q, token=token), paginate=False, full_body=True)

    async def post_poll(
        self,
        broadcaster_id: str,
        token: str,
        title: str,
        choices,
        duration: int,
        bits_voting_enabled: Optional[bool] = False,
        bits_per_vote: Optional[int] = None,
        channel_points_voting_enabled: Optional[bool] = False,
        channel_points_per_vote: Optional[int] = None,
    ):
        if len(title) > 60:
            raise ValueError("title must be less than or equal to 60 characters")
        if len(choices) < 2 or len(choices) > 5:
            raise ValueError("You must have between 2 and 5 choices")
        for c in choices:
            if len(c) > 25:
                raise ValueError("choice title must be less than or equal to 25 characters")
        if duration < 15 or duration > 1800:
            raise ValueError("duration must be between 15 and 1800 seconds")
        if bits_per_vote and bits_per_vote > 10000:
            raise ValueError("bits_per_vote must bebetween 0 and 10000")
        if channel_points_per_vote and channel_points_per_vote > 1000000:
            raise ValueError("channel_points_per_vote must bebetween 0 and 1000000")
        body = {
            "broadcaster_id": broadcaster_id,
            "title": title,
            "choices": [{"title": choice} for choice in choices],
            "duration": duration,
            "bits_voting_enabled": str(bits_voting_enabled),
            "channel_points_voting_enabled": str(channel_points_voting_enabled),
        }
        if bits_voting_enabled and bits_per_vote:
            body["bits_per_vote"] = bits_per_vote
        if channel_points_voting_enabled and channel_points_per_vote:
            body["channel_points_per_vote"] = channel_points_per_vote
        return await self.request(Route("POST", "polls", body=body, token=token))

    async def patch_poll(self, broadcaster_id: str, token: str, id: str, status: str):
        body = {"broadcaster_id": broadcaster_id, "id": id, "status": status}
        return await self.request(Route("PATCH", "polls", body=body, token=token))

    async def get_goals(self, broadcaster_id: str, token: str):
        return await self.request(Route("GET", "goals", query=[("broadcaster_id", broadcaster_id)], token=token))

    async def get_chat_settings(
        self, broadcaster_id: str, token: Optional[str] = None, moderator_id: Optional[str] = None
    ):
        q = [("broadcaster_id", broadcaster_id)]
        if moderator_id and token:
            q.append(("moderator_id", moderator_id))
        return await self.request(Route("GET", "chat/settings", query=q, token=token))

    async def patch_chat_settings(
        self,
        token: str,
        broadcaster_id: str,
        moderator_id: str,
        emote_mode: Optional[bool] = None,
        follower_mode: Optional[bool] = None,
        follower_mode_duration: Optional[int] = None,
        slow_mode: Optional[bool] = None,
        slow_mode_wait_time: Optional[int] = None,
        subscriber_mode: Optional[bool] = None,
        unique_chat_mode: Optional[bool] = None,
        non_moderator_chat_delay: Optional[bool] = None,
        non_moderator_chat_delay_duration: Optional[int] = None,
    ):
        if follower_mode_duration and follower_mode_duration > 129600:
            raise ValueError("follower_mode_duration must be below 129600")
        if slow_mode_wait_time and (slow_mode_wait_time < 3 or slow_mode_wait_time > 120):
            raise ValueError("slow_mode_wait_time must be between 3 and 120")
        if non_moderator_chat_delay_duration and non_moderator_chat_delay_duration not in {2, 4, 6}:
            raise ValueError("non_moderator_chat_delay_duration must be 2, 4 or 6")
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id)]
        data = {
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
        data = {k: v for k, v in data.items() if v is not None}
        return await self.request(Route("PATCH", "chat/settings", query=q, body=data, token=token))

    async def post_chat_announcement(
        self, token: str, broadcaster_id: str, moderator_id: str, message: str, color: Optional[str] = "primary"
    ):
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id)]
        body = {"message": message, "color": color}
        return await self.request(Route("POST", "chat/announcements", query=q, body=body, token=token))

    async def delete_chat_messages(
        self, token: str, broadcaster_id: str, moderator_id: str, message_id: Optional[str] = None
    ):
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id)]
        if message_id:
            q.append(("message_id", message_id))
        return await self.request(Route("DELETE", "moderation/chat", query=q, token=token))

    async def put_user_chat_color(self, token: str, user_id: str, color: str):
        q = [("user_id", user_id), ("color", color)]
        return await self.request(Route("PUT", "chat/color", query=q, token=token))

    async def get_user_chat_color(self, user_ids: List[int], token: Optional[str] = None):
        if len(user_ids) > 100:
            raise ValueError("You can only get up to 100 user chat colors at once")
        q = [("user_id", str(user_id)) for user_id in user_ids]
        return await self.request(Route("GET", "chat/color", query=q, token=token))

    async def post_channel_moderator(self, token: str, broadcaster_id: str, user_id: str):
        q = [("broadcaster_id", broadcaster_id), ("user_id", user_id)]
        return await self.request(Route("POST", "moderation/moderators", query=q, token=token))

    async def delete_channel_moderator(self, token: str, broadcaster_id: str, user_id: str):
        q = [("broadcaster_id", broadcaster_id), ("user_id", user_id)]
        return await self.request(Route("DELETE", "moderation/moderators", query=q, token=token))

    async def get_channel_vips(
        self, token: str, broadcaster_id: str, first: int = 20, user_ids: Optional[List[int]] = None
    ):
        q = [("broadcaster_id", broadcaster_id), ("first", first)]
        if first > 100:
            raise ValueError("You can only get up to 100 VIPs at once")
        if user_ids:
            if len(user_ids) > 100:
                raise ValueError("You can can only specify up to 100 VIPs")
            q.extend(("user_id", str(user_id)) for user_id in user_ids)
        return await self.request(Route("GET", "channels/vips", query=q, token=token))

    async def post_channel_vip(self, token: str, broadcaster_id: str, user_id: str):
        q = [("broadcaster_id", broadcaster_id), ("user_id", user_id)]
        return await self.request(Route("POST", "channels/vips", query=q, token=token))

    async def delete_channel_vip(self, token: str, broadcaster_id: str, user_id: str):
        q = [("broadcaster_id", broadcaster_id), ("user_id", user_id)]
        return await self.request(Route("DELETE", "channels/vips", query=q, token=token))

    async def post_whisper(self, token: str, from_user_id: str, to_user_id: str, message: str):
        q = [("from_user_id", from_user_id), ("to_user_id", to_user_id)]
        body = {"message": message}
        return await self.request(Route("POST", "whispers", query=q, body=body, token=token))

    async def post_raid(self, token: str, from_broadcaster_id: str, to_broadcaster_id: str):
        q = [("from_broadcaster_id", from_broadcaster_id), ("to_broadcaster_id", to_broadcaster_id)]
        return await self.request(Route("POST", "raids", query=q, token=token))

    async def delete_raid(self, token: str, broadcaster_id: str):
        q = [("broadcaster_id", broadcaster_id)]
        return await self.request(Route("DELETE", "raids", query=q, token=token))

    async def post_ban_timeout_user(
        self,
        token: str,
        broadcaster_id: str,
        moderator_id: str,
        user_id: str,
        reason: str,
        duration: Optional[int] = None,
    ):
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id)]
        body = {"data": {"user_id": user_id, "reason": reason}}
        if duration:
            if duration < 1 or duration > 1209600:
                raise ValueError("Duration must be between 1 and 1209600 seconds")
            body["data"]["duration"] = str(duration)
        return await self.request(Route("POST", "moderation/bans", query=q, body=body, token=token))

    async def delete_ban_timeout_user(
        self,
        token: str,
        broadcaster_id: str,
        moderator_id: str,
        user_id: str,
    ):
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id), ("user_id", user_id)]
        return await self.request(Route("DELETE", "moderation/bans", query=q, token=token))

    async def get_follow_count(
        self, from_id: Optional[str] = None, to_id: Optional[str] = None, token: Optional[str] = None
    ):
        return await self.request(
            Route(
                "GET",
                "users/follows",
                query=[x for x in [("from_id", from_id), ("to_id", to_id)] if x[1] is not None],
                token=token,
            ),
            full_body=True,
            paginate=False,
        )

    async def get_shield_mode_status(self, token: str, broadcaster_id: str, moderator_id: str):
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id)]
        return await self.request(
            Route("GET", "moderation/shield_mode", query=q, token=token), paginate=False, full_body=False
        )

    async def put_shield_mode_status(self, token: str, broadcaster_id: str, moderator_id: str, is_active: bool):
        q = [("broadcaster_id", broadcaster_id), ("moderator_id", moderator_id)]
        body = {"is_active": is_active}
        return await self.request(Route("PUT", "moderation/shield_mode", query=q, body=body, token=token))

    async def get_followed_streams(self, broadcaster_id: str, token: str):
        return await self.request(Route("GET", "streams/followed", query=[("user_id", broadcaster_id)], token=token))

    async def post_shoutout(self, token: str, broadcaster_id: str, moderator_id: str, to_broadcaster_id: str):
        q = [
            ("from_broadcaster_id", broadcaster_id),
            ("moderator_id", moderator_id),
            ("to_broadcaster_id", to_broadcaster_id),
        ]
        return await self.request(Route("POST", "chat/shoutouts", query=q, token=token))
