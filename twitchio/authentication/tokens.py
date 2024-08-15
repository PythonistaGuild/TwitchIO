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

import asyncio
import datetime
import json
import logging
from typing import TYPE_CHECKING, Any, TypeVar

import aiohttp

from twitchio.http import Route
from twitchio.types_.responses import RawResponse

from ..exceptions import HTTPException, InvalidTokenException
from ..http import HTTPAsyncIterator, PaginatedConverter
from ..types_.tokens import TokenMappingData
from .oauth import OAuth
from .payloads import ClientCredentialsPayload, ValidateTokenPayload
from .scopes import Scopes


if TYPE_CHECKING:
    from ..types_.tokens import TokenMapping
    from .payloads import RefreshTokenPayload


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
        session: aiohttp.ClientSession | None = None,
        nested_key: str | None = None,
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
        self._validate_task: asyncio.Task[None] | None = None
        self._nested_key: str | None = None

    async def _attempt_refresh_on_add(self, token: str, refresh: str) -> ValidateTokenPayload:
        logger.debug("Token was invalid when attempting to add it to the token manager. Attempting to refresh.")

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
            logger.info("Refreshed token is not a user token. Adding to TokenManager as an app token.")
            self._app_token = resp.access_token

            return valid_resp

        self._tokens[valid_resp.user_id] = {
            "user_id": valid_resp.user_id,
            "token": resp.access_token,
            "refresh": resp.refresh_token,
            "last_validated": datetime.datetime.now().isoformat(),
        }

        logger.info('Token successfully added to TokenManager after refresh: "%s"', valid_resp.user_id)
        return valid_resp

    async def add_token(self, token: str, refresh: str) -> ValidateTokenPayload:
        try:
            resp: ValidateTokenPayload = await self.__isolated.validate_token(token)
        except HTTPException as e:
            if e.status != 401:
                msg: str = "Token was invalid. Please check the token or re-authenticate user with a new token."
                raise InvalidTokenException(msg, token=token, refresh=refresh, type_="token", original=e)

            return await self._attempt_refresh_on_add(token, refresh)

        if not resp.login or not resp.user_id:
            logger.info("Added token is not a user token. Adding to TokenManager as an app token.")
            self._app_token = token

            return resp

        self._tokens[resp.user_id] = {
            "user_id": resp.user_id,
            "token": token,
            "refresh": refresh,
            "last_validated": datetime.datetime.now().isoformat(),
        }

        logger.debug('Token successfully added to TokenManager: "%s"', resp.user_id)
        return resp

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
        if not self._session:
            await self._init_session()

        old: TokenMappingData | None | str = self._find_token(route)
        if old:
            token: str = old if isinstance(old, str) else old["token"]
            route.update_headers({"Authorization": f"Bearer {token}"})

        try:
            data: RawResponse | str | None = await super().request(route)
        except HTTPException as e:
            if not old or e.status != 401:
                raise e

            if e.extra.get("message", "").lower() != "invalid access token":
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

    async def __validate_loop(self) -> None:
        logger.debug("Started the token validation loop on %s.", self.__class__.__qualname__)

        if not self._session:
            await self._init_session()

        while self._session and not self._session.closed:
            for data in self._tokens.copy().values():
                last_validated: datetime.datetime = datetime.datetime.fromisoformat(data["last_validated"])
                if last_validated + datetime.timedelta(minutes=60) > datetime.datetime.now():
                    continue

                try:
                    await self.__isolated.validate_token(data["token"])
                    # logger.debug('Token for "%s" was successfully re-validated.', data["user_id"])
                except HTTPException as e:
                    if e.status >= 500:
                        logger.warning("Received invalid response from Twitch when re-validating token.")

                        # backoff for 60 seconds to and try again...
                        # There's really not much else we can do here...
                        await asyncio.sleep(60)
                        continue

                    logger.debug('Token for "%s" was invalid or expired. Attempting to refresh token.', data["user_id"])

                    try:
                        refresh: RefreshTokenPayload = await self.__isolated.refresh_token(data["refresh"])
                    except HTTPException as e:
                        self._tokens.pop(data["user_id"], None)
                        logger.warning('Token for "%s" was invalid and could not be refreshed.', data["user_id"])
                        continue

                    logger.debug('Token for "%s" was successfully refreshed.', data["user_id"])

                    self._tokens[data["user_id"]] = {
                        "user_id": data["user_id"],
                        "token": refresh.access_token,
                        "refresh": refresh.refresh_token,
                        "last_validated": datetime.datetime.now().isoformat(),
                    }

                    continue

            await asyncio.sleep(60)

    async def _init_session(self) -> None:
        await super()._init_session()

        if not self._validate_task:
            self._validate_task = asyncio.create_task(self.__validate_loop())

    async def close(self) -> None:
        self._tokens.clear()

        if self._validate_task:
            try:
                self._validate_task.cancel()
            except Exception:
                pass

            self._validate_task = None

        await super().close()
        await self.__isolated.close()

    async def dump(self, name: str | None = None) -> None:
        name = name or ".tio.tokens.json"

        with open(name, "w+", encoding="UTF-8") as fp:
            json.dump(self._tokens, fp)

        logger.info('Tokens from %s have been saved to: "%s".', self.__class__.__qualname__, name)

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

        logger.info("Loaded %s tokens into the Token Manager.", loaded)
        if failed:
            msg: str = f"The following users tokens failed to load: {', '.join(failed)}"
            logger.warning(msg)
