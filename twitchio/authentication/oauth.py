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

import urllib.parse
from typing import TYPE_CHECKING, ClassVar

from ..http import HTTPClient, Route
from .payloads import *


if TYPE_CHECKING:
    from ..types_.responses import (
        ClientCredentialsResponse,
        RefreshTokenResponse,
        UserTokenResponse,
        ValidateTokenResponse,
    )
    from .scopes import Scopes


class OAuth(HTTPClient):
    CONTENT_TYPE_HEADER: ClassVar[dict[str, str]] = {"Content-Type": "application/x-www-form-urlencoded"}

    def __init__(self, *, client_id: str, client_secret: str, redirect_uri: str | None = None) -> None:
        super().__init__()

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    async def validate_token(self, token: str, /) -> ValidateTokenPayload:
        token = token.removeprefix("Bearer ").removeprefix("OAuth ")

        headers: dict[str, str] = {"Authorization": f"OAuth {token}"}
        route: Route = Route("GET", "/oauth2/validate", use_id=True, headers=headers)

        data: ValidateTokenResponse = await self.request_json(route)
        return ValidateTokenPayload(data)

    async def refresh_token(self, refresh_token: str, /) -> RefreshTokenPayload:
        params = self._create_params(
            {
                "grant_type": "refresh_token",
                "refresh_token": urllib.parse.quote(refresh_token, safe=""),
            }
        )

        route: Route = Route("POST", "/oauth2/token", use_id=True, headers=self.CONTENT_TYPE_HEADER, params=params)
        data: RefreshTokenResponse = await self.request_json(route)

        return RefreshTokenPayload(data)

    async def user_access_token(self, code: str, /) -> UserTokenPayload:
        if not self.redirect_uri:
            raise ValueError("Missing redirect_uri")

        params = self._create_params(
            {
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                # "scope": " ".join(SCOPES), #TODO
                # "state": #TODO
            }
        )

        route: Route = Route("POST", "/oauth2/token", use_id=True, headers=self.CONTENT_TYPE_HEADER, params=params)
        data: UserTokenResponse = await self.request_json(route)

        return UserTokenPayload(data)

    async def revoke_token(self, token: str, /) -> None:
        params = self._create_params({"token": token})

        route: Route = Route("POST", "/oauth2/revoke", use_id=True, headers=self.CONTENT_TYPE_HEADER, params=params)
        await self.request_json(route)

    async def client_credentials_token(self) -> ClientCredentialsPayload:
        params = self._create_params({"grant_type": "client_credentials"})

        route: Route = Route("POST", "/oauth2/token", use_id=True, headers=self.CONTENT_TYPE_HEADER, params=params)
        data: ClientCredentialsResponse = await self.request_json(route)

        return ClientCredentialsPayload(data)

    def get_authorization_url(self, scopes: Scopes, state: str = "") -> str:
        if not self.redirect_uri:
            raise ValueError("Missing redirect_uri")

        params = {
            "client_id": self.client_id,
            "redirect_uri": urllib.parse.quote(self.redirect_uri),
            "response_type": "code",
            "scope": scopes.urlsafe(),
            "state": state,
        }

        route: Route = Route("GET", "/oauth2/authorize", use_id=True, params=params)
        return route.url

    def _create_params(self, extra_params: dict[str, str]) -> dict[str, str]:
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        params.update(extra_params)
        return params
