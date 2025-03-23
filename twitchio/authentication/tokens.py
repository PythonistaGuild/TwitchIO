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
import datetime
import json
import logging
from typing import TYPE_CHECKING, Any, TypeVar

import aiohttp

from ..backoff import Backoff
from ..exceptions import HTTPException, InvalidTokenException
from ..http import HTTPAsyncIterator, PaginatedConverter
from ..payloads import TokenRefreshedPayload
from ..utils import MISSING
from .oauth import OAuth
from .scopes import Scopes


if TYPE_CHECKING:
    from twitchio.http import Route
    from twitchio.types_.responses import RawResponse

    from ..client import Client
    from ..types_.tokens import TokenMapping, TokenMappingData, _TokenRefreshedPayload
    from .payloads import ClientCredentialsPayload, RefreshTokenPayload, ValidateTokenPayload


logger: logging.Logger = logging.getLogger(__name__)


T = TypeVar("T")


class ManagedHTTPClient(OAuth):
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
        scopes: Scopes | None = None,
        session: aiohttp.ClientSession = MISSING,
        nested_key: str | None = None,
        client: Client | None = None,
    ) -> None:
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
        )
        self.__isolated: OAuth = OAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            session=session,
        )

        self._tokens: TokenMapping = {}
        self._app_token: str | None = None
        self._nested_key: str | None = None

        self._token_lock: asyncio.Lock = asyncio.Lock()
        self._has_loaded: bool = False
        self._backoff: Backoff = Backoff(base=3, maximum_time=90)

        self._validate_task: asyncio.Task[None] | None = None
        self._client = client

    def __repr__(self) -> str:
        return self.__class__.__qualname__

    def _dispatch_event(self, user_id: str, payload: RefreshTokenPayload) -> None:
        if not self._client:
            return

        data: _TokenRefreshedPayload = {
            "user_id": user_id,
            "refresh_token": payload.refresh_token,
            "token": payload.access_token,
            "scopes": Scopes(payload.scope),
            "expires_in": payload.expires_in,
        }

        self._client.dispatch("token_refreshed", TokenRefreshedPayload(data=data))

    async def _attempt_refresh_on_add(self, token: str, refresh: str) -> ValidateTokenPayload:
        try:
            resp: RefreshTokenPayload = await self.__isolated.refresh_token(refresh)
        except HTTPException as e:
            msg: str = f'Token was invalid and cannot be refreshed. Please re-authenticate user with token: "{token}"'
            raise InvalidTokenException(msg, token=token, refresh=refresh, type_="refresh", original=e)

        try:
            valid_resp: ValidateTokenPayload = await self.__isolated.validate_token(resp["access_token"])
        except HTTPException as e:
            msg: str = f'Refreshed token was invalid. Please re-authenticate user with token: "{token}"'
            raise InvalidTokenException(msg, token=token, refresh=refresh, type_="token", original=e)

        if not valid_resp.login or not valid_resp.user_id:
            logger.info("Refreshed token is not a user token. Adding to %r as an app token.", self)
            self._app_token = resp.access_token

            return valid_resp

        self._tokens[valid_resp.user_id] = {
            "user_id": valid_resp.user_id,
            "token": resp.access_token,
            "refresh": resp.refresh_token,
            "last_validated": datetime.datetime.now().isoformat(),
        }

        self._dispatch_event(valid_resp.user_id, resp)
        logger.info('Token successfully added to %r after refresh: "%s"', self, valid_resp.user_id)
        return valid_resp

    async def add_token(self, token: str, refresh: str) -> ValidateTokenPayload:
        if not self._validate_task:
            self._validate_task = asyncio.create_task(self.__validate_loop())

        try:
            resp: ValidateTokenPayload = await self.__isolated.validate_token(token)
        except HTTPException as e:
            if e.status != 401:
                msg: str = "Token was invalid. Please check the token or re-authenticate user with a new token."
                raise InvalidTokenException(msg, token=token, refresh=refresh, type_="token", original=e)

            logger.debug("Token was invalid when attempting to add it to %r. Attempting to refresh.", self)
            return await self._attempt_refresh_on_add(token, refresh)

        if not resp.login or not resp.user_id:
            logger.info("Added token is not a user token. Adding to %r as an app token.", self)
            self._app_token = token

            return resp

        if resp.expires_in <= 3600:
            logger.debug("Token expires in %s seconds. Attempting to refresh.", resp.expires_in)
            return await self._attempt_refresh_on_add(token, refresh)

        self._tokens[resp.user_id] = {
            "user_id": resp.user_id,
            "token": token,
            "refresh": refresh,
            "last_validated": datetime.datetime.now().isoformat(),
        }

        logger.debug('Token successfully added to %r: "%s"', self, resp.user_id)
        return resp

    def remove_token(self, user_id: str) -> TokenMappingData | None:
        data: TokenMappingData | None = self._tokens.pop(user_id, None)
        return data

    def _find_token(self, route: Route) -> TokenMappingData | None | str:
        token: str | None = route.headers.get("Authorization")
        if token:
            token = token.removeprefix("Bearer ").removeprefix("OAuth ")

        if token == self._app_token:
            return token

        if route.token_for and not token:
            scoped: TokenMappingData | None = self._tokens.get(route.token_for, None)
            if scoped:
                return scoped

        for data in self._tokens.values():
            if data["token"] == token:
                return data

        return token or self._app_token

    async def request(self, route: Route) -> RawResponse | str | None:
        old: TokenMappingData | None | str = self._find_token(route)
        if old:
            token: str = old if isinstance(old, str) else old["token"]
            route.update_headers({"Authorization": f"Bearer {token}"})

        try:
            data: RawResponse | str | None = await super().request(route)
        except HTTPException as e:
            if not old or e.status != 401:
                raise e

            if e.extra.get("message", "").lower() not in ("invalid access token", "invalid oauth token"):
                raise e

            if isinstance(old, str):
                payload: ClientCredentialsPayload = await self.client_credentials_token()
                self._app_token = payload.access_token
                route.update_headers({"Authorization": f"Bearer {payload.access_token}"})

                return await self.request(route)

            logger.debug('Token for "%s" was invalid or expired. Attempting to refresh token.', old["user_id"])
            refresh: RefreshTokenPayload = await self.__isolated.refresh_token(old["refresh"])
            logger.debug('Token for "%s" was successfully refreshed.', old["user_id"])

            self._tokens[old["user_id"]] = {
                "user_id": old["user_id"],
                "token": refresh.access_token,
                "refresh": refresh.refresh_token,
                "last_validated": datetime.datetime.now().isoformat(),
            }

            self._dispatch_event(old["user_id"], refresh)
            route.update_headers({"Authorization": f"Bearer {refresh.access_token}"})
            return await self.request(route)

        return data

    def request_paginated(
        self,
        route: Route,
        max_results: int | None = None,
        *,
        converter: PaginatedConverter[T] | None = None,
        nested_key: str | None = None,
    ) -> HTTPAsyncIterator[T]:
        iterator: HTTPAsyncIterator[T] = HTTPAsyncIterator(
            self,
            route,
            max_results,
            converter=converter,
            nested_key=nested_key,
        )
        return iterator

    async def _refresh_token(self, user_id: str, refresh: str) -> None:
        try:
            resp: RefreshTokenPayload = await self.__isolated.refresh_token(refresh)
        except HTTPException as e:
            if e.status >= 500:
                raise

            self._tokens.pop(user_id, None)
            logger.warning('Token for "%s" was invalid and could not be refreshed.', user_id)
        else:
            logger.debug('Token for "%s" was successfully refreshed.', user_id)

            self._tokens[user_id] = {
                "user_id": user_id,
                "token": resp.access_token,
                "refresh": resp.refresh_token,
                "last_validated": datetime.datetime.now().isoformat(),
            }

            self._dispatch_event(user_id, resp)

    async def _revalidate_all(self) -> None:
        logger.debug("Attempting to revalidate all tokens that have passed the timeout on %r.", self)

        for data in self._tokens.copy().values():
            user_id: str = data["user_id"]
            token: str = data["token"]
            refresh: str = data["refresh"]

            last_validated: datetime.datetime = datetime.datetime.fromisoformat(data["last_validated"])
            if last_validated + datetime.timedelta(minutes=55) > datetime.datetime.now():
                continue

            try:
                valid_resp: ValidateTokenPayload = await self.__isolated.validate_token(token)
            except HTTPException as e:
                if e.status >= 500:
                    raise

                logger.debug('Token for "%s" was invalid or expired. Attempting to refresh token.', user_id)
                await self._refresh_token(user_id, refresh)
            else:
                if valid_resp.expires_in <= 3600:
                    logger.debug(
                        'Token for "%s" expires in %s seconds. Attempting to refresh token.', user_id, valid_resp.expires_in
                    )

                    await self._refresh_token(user_id, refresh)
                    continue

                self._tokens[user_id]["last_validated"] = datetime.datetime.now().isoformat()

    async def __validate_loop(self) -> None:
        logger.debug("Started the token validation loop on %r.", self)

        while True:
            try:
                await self._revalidate_all()
            except (ConnectionError, aiohttp.ClientConnectorError, HTTPException) as e:
                wait: float = self._backoff.calculate()
                logger.debug("Unable to reach Twitch to revalidate tokens: %s. Retrying in %s's", e, wait)

                await asyncio.sleep(wait)
                continue

            await asyncio.sleep(60)

    def cleanup(self) -> None:
        self._tokens.clear()

    async def close(self) -> None:
        if self._validate_task:
            try:
                self._validate_task.cancel()
            except Exception:
                pass

            self._validate_task = None

        await super().close()
        await self.__isolated.close()

    async def save(self, name: str | None = None) -> None:
        if not self._has_loaded:
            return

        name = name or ".tio.tokens.json"

        with open(name, "w+", encoding="UTF-8") as fp:
            json.dump(self._tokens, fp)

        logger.info('Tokens from %r have been saved to: "%s".', self, name)

    async def load_tokens(self, name: str | None = None) -> None:
        name = name or ".tio.tokens.json"
        data: dict[str, Any] = {}
        failed: list[str] = []
        loaded: int = 0

        try:
            with open(name, "r+", encoding="UTF-8") as fp:
                data = json.load(fp)
        except FileNotFoundError:
            pass

        for key, value in data.items():
            try:
                await self.add_token(token=value["token"], refresh=value["refresh"])
                loaded += 1
            except InvalidTokenException:
                failed.append(key)

        logger.info("Loaded %s tokens into %r.", loaded, self)
        if failed:
            msg: str = f"The following users tokens failed to load: {', '.join(failed)}"
            logger.warning(msg)

        self._has_loaded = True
