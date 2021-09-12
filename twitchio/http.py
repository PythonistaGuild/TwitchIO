"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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
from typing import TYPE_CHECKING, Union, List, Tuple, Any, Dict

import aiohttp
from yarl import URL

from . import errors
from .cooldowns import RateBucket

try:
    import ujson as json
except:
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
                if cursor is not None:
                    if route.query:
                        q = [("after", cursor), *route.query]
                    else:
                        q = [("after", cursor)]
                    path = path.with_query(q)

                if route.query:
                    q = [("first", get_limit()), *route.query]
                else:
                    q = [("first", get_limit())]

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
                    await asyncio.sleep(2 ** attempt + 1)
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
                        await asyncio.sleep(3 ** attempt + 1)
                    continue

                raise errors.HTTPException(f"Failed to fulfil request ({resp.status}).", resp.reason, resp.status)

        raise errors.HTTPException("Failed to reach Twitch API", reason, resp.status)

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
            raise errors.HTTPException(data["message"], data["retry_after"])

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
        self, token: str, period: str = "all", user_id: str = None, started_at: datetime.datetime = None
    ):
        assert period in {"all", "day", "week", "month", "year"}
        route = Route(
            "GET",
            "bits/leaderboard",
            "",
            query=[
                ("period", period),
                ("started_at", started_at.isoformat() if started_at else None),
                ("user_id", user_id),
            ],
            token=token,
        )
        return await self.request(route, full_body=True, paginate=False)

    async def get_cheermotes(self, broadcaster_id: str):
        return await self.request(Route("GET", "bits/cheermotes", "", query=[("broadcaster_id", broadcaster_id)]))

    async def get_extension_transactions(self, extension_id: str, ids: List[Any] = None):
        q = [("extension_id", extension_id)]
        if ids:
            for id in ids:
                q.append(("id", id))

        return await self.request(Route("GET", "extensions/transactions", "", query=q))

    async def create_reward(
        self,
        token: str,
        broadcaster_id: int,
        title: str,
        cost: int,
        prompt: str = None,
        is_enabled: bool = True,
        background_color: str = None,
        user_input_required: bool = False,
        max_per_stream: int = None,
        max_per_user: int = None,
        global_cooldown: int = None,
        fufill_immediatly: bool = False,
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
            data["max_per_stream_enabled"] = True

        if max_per_user:
            data["max_per_user_per_stream"] = max_per_user
            data["max_per_user_per_stream_enabled"] = True

        if background_color:
            data["background_color"] = background_color

        if global_cooldown:
            data["global_cooldown_seconds"] = global_cooldown
            data["is_global_cooldown_enabled"] = True

        return await self.request(Route("POST", "channel_points/custom_rewards", query=params, body=data, token=token))

    async def get_rewards(self, token: str, broadcaster_id: int, only_manageable: bool = False, ids: List[int] = None):
        params = [("broadcaster_id", str(broadcaster_id)), ("only_manageable_rewards", str(only_manageable))]

        if ids:
            for id in ids:
                params.append(("id", str(id)))

        return await self.request(Route("GET", "channel_points/custom_rewards", query=params, token=token))

    async def update_reward(
        self,
        token: str,
        broadcaster_id: int,
        reward_id: str,
        title: str = None,
        prompt: str = None,
        cost: int = None,
        background_color: str = None,
        enabled: bool = None,
        input_required: bool = None,
        max_per_stream_enabled: bool = None,
        max_per_stream: int = None,
        max_per_user_per_stream_enabled: bool = None,
        max_per_user_per_stream: int = None,
        global_cooldown_enabled: bool = None,
        global_cooldown: int = None,
        paused: bool = None,
        redemptions_skip_queue: bool = None,
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
        redemption_id: str = None,
        status: str = None,
        sort: str = None,
    ):
        params = [("broadcaster_id", str(broadcaster_id)), ("reward_id", reward_id)]

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
        params = [("id", custom_reward_id), ("broadcaster_id", str(broadcaster_id)), ("reward_id", reward_id)]
        status = "FULFILLED" if status else "CANCELLED"
        return await self.request(
            Route(
                "PATCH",
                "/channel_points/custom_rewards/redemptions",
                query=params,
                body={"status": status},
                token=token,
            )
        )

    async def get_predictions(
        self,
        token: str,
        broadcaster_id: int,
        prediction_id: str = None,
    ):
        params = [("broadcaster_id", str(broadcaster_id))]

        if prediction_id:
            params.extend(("prediction_id", prediction_id))

        return await self.request(Route("GET", "predictions", query=params, token=token), paginate=False)

    async def patch_prediction(
        self, token: str, broadcaster_id: int, prediction_id: str, status: str, winning_outcome_id: str = None
    ):
        body = {
            "broadcaster_id": str(broadcaster_id),
            "id": prediction_id,
            "status": status,
        }

        if status == "RESOLVED":
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
            Route("POST", "clips", query=[("broadcaster_id", broadcaster_id), ("has_delay", has_delay)], token=token),
            paginate=False,
        )

    async def get_clips(
        self,
        broadcaster_id: int = None,
        game_id: str = None,
        ids: List[str] = None,
        started_at: datetime.datetime = None,
        ended_at: datetime.datetime = None,
        token: str = None,
    ):
        q = [
            ("broadcaster_id", broadcaster_id),
            ("game_id", game_id),
            ("started_at", started_at.isoformat() if started_at else None),
            ("ended_at", ended_at.isoformat() if ended_at else None),
        ]
        for id in ids:
            q.append(("id", id))

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
        for code in codes:
            q.append(("code", code))

        return await self.request(Route("GET", "entitlements/codes", query=q))

    async def post_redeem_code(self, user_id: int, codes: List[str]):
        q = [("user_id", user_id)]
        for c in codes:
            q.append(("code", c))

        return await self.request(Route("POST", "entitlements/code", query=q))

    async def get_top_games(self):
        return await self.request(Route("GET", "games/top"))

    async def get_games(self, game_ids: List[Any], game_names: List[str]):
        q = []
        if game_ids:
            for id in game_ids:
                q.append(("id", id))
        if game_names:
            for name in game_names:
                q.append(("name", name))

        return await self.request(Route("GET", "games", query=q))

    async def get_hype_train(self, broadcaster_id: str, id: str = None, token: str = None):
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
            for id in user_ids:
                q.append(("user_id", id))

        return await self.request(Route("GET", "moderation/banned/events", query=q, token=token))

    async def get_channel_bans(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            for id in user_ids:
                q.append(("user_id", id))

        return await self.request(Route("GET", "moderation/banned", query=q, token=token))

    async def get_channel_moderators(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            for id in user_ids:
                q.append(("user_id", id))

        return await self.request(Route("GET", "moderation/moderators", query=q, token=token))

    async def get_channel_mod_events(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        for id in user_ids:
            q.append(("user_id", id))

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
        game_ids: List[str] = None,
        user_ids: List[str] = None,
        user_logins: List[str] = None,
        languages: List[str] = None,
        token: str = None,
    ):
        q = []
        if game_ids:
            for g in game_ids:
                q.append(("game_id", g))

        if user_ids:
            for u in user_ids:
                q.append(("user_id", u))

        if user_logins:
            for l in user_logins:
                q.append(("user_login", l))

        if languages:
            for l in languages:
                q.append(("language", l))

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

    async def get_channels(self, broadcaster_id: str, token: str = None):
        return await self.request(Route("GET", "channels", query=[("broadcaster_id", broadcaster_id)], token=token))

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
        segment_ids: List[str] = None,
        start_time: datetime.datetime = None,
        utc_offset: int = None,
        first: int = 20,
    ):

        if first is not None and (first > 25 or first < 1):
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
            for id in segment_ids:
                q.append(
                    ("id", id),
                )

        return await self.request(Route("GET", "schedule", query=q), paginate=False, full_body=True)

    async def get_channel_subscriptions(self, token: str, broadcaster_id: str, user_ids: List[str] = None):
        q = [("broadcaster_id", broadcaster_id)]
        if user_ids:
            for u in user_ids:
                q.append(("user_id", u))

        return await self.request(Route("GET", "subscriptions", query=q, token=token))

    async def get_stream_tags(self, tag_ids: List[str] = None):
        q = []
        if tag_ids:
            for u in tag_ids:
                q.append(("tag_id", u))

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

    async def get_users(self, ids: List[int], logins: List[str], token: str = None):
        q = []
        if ids:
            for id in ids:
                q.append(("id", id))

        if logins:
            for login in logins:
                q.append(("login", login))

        return await self.request(Route("GET", "users", query=q, token=token))

    async def get_user_follows(self, from_id: str = None, to_id: str = None, token: str = None):
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
            for id in ids:
                q.append(("id", id))

        return await self.request(Route("GET", "videos", query=q, token=token))

    async def delete_videos(self, token: str, ids: List[int]):
        q = [("id", str(x)) for x in ids]

        return (await self.request(Route("DELETE", "videos", query=q, token=token), paginate=False, full_body=True))[
            "data"
        ]

    async def get_webhook_subs(self):
        return await self.request(Route("GET", "webhooks/subscriptions"))

    async def get_teams(self, team_name: str = None, team_id: str = None):
        if team_name:
            q = [("name", team_name)]
        elif team_id:
            q = [("id", team_id)]
        else:
            raise ValueError("You need to provide a team name or id")
        return await self.request(Route("GET", "teams", query=q))

    async def get_channel_teams(self, broadcaster_id: str):
        q = [("broadcaster_id", broadcaster_id)]
        return await self.request(Route("GET", "teams/channel", query=q))
