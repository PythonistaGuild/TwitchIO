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

from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from ..types_.responses import *


__all__ = (
    "AuthorizationURLPayload",
    "ClientCredentialsPayload",
    "RefreshTokenPayload",
    "UserTokenPayload",
    "ValidateTokenPayload",
)


class BasePayload(Mapping[str, Any]):
    __slots__ = ("raw_data",)

    def __init__(self, raw: OAuthResponses, /) -> None:
        self.raw_data = raw

    def __getitem__(self, key: str) -> Any:
        return self.raw_data[key]  # type: ignore

    def __iter__(self) -> Iterator[str]:
        return iter(self.raw_data)

    def __len__(self) -> int:
        return len(self.raw_data)


class RefreshTokenPayload(BasePayload):
    __slots__ = ("access_token", "expires_in", "refresh_token", "scope", "token_type")

    def __init__(self, raw: RefreshTokenResponse, /) -> None:
        super().__init__(raw)

        self.access_token: str = raw["access_token"]
        self.refresh_token: str = raw["refresh_token"]
        self.expires_in: int = raw["expires_in"]
        self.scope: str | list[str] = raw["scope"]
        self.token_type: str = raw["token_type"]


class ValidateTokenPayload(BasePayload):
    __slots__ = ("client_id", "expires_in", "login", "scopes", "user_id")

    def __init__(self, raw: ValidateTokenResponse, /) -> None:
        super().__init__(raw)

        self.client_id: str = raw["client_id"]
        self.login: str | None = raw.get("login", None)
        self.scopes: list[str] = raw["scopes"]
        self.user_id: str | None = raw.get("user_id", None)
        self.expires_in: int = raw["expires_in"]


class UserTokenPayload(BasePayload):
    """OAuth model received when a user successfully authenticates your application on Twitch.

    This is a raw container class.

    Attributes
    ----------
    access_token: str
        The user access token.
    refresh_token: str
        The user refresh token for this access token.
    expires_in: int
        The amount of time this token is valid before expiring as seconds.
    scope: str | list[str]
        A ``str`` or ``list[str]`` containing the scopes the user authenticated with.
    token_type: str
        The type of token provided. Usually ``bearer``.
    user_id: str | None
        An optional :class:`str` representing the ID of the User who authorized your application. This could be ``None``.
    user_login: str | None
        An optional :class:`str` representing the user name of the User who authorized your application.
        This could be ``None``.
    """

    __slots__ = ("_user_id", "_user_login", "access_token", "expires_in", "refresh_token", "scope", "token_type")

    def __init__(self, raw: UserTokenResponse, /) -> None:
        super().__init__(raw)

        self.access_token: str = raw["access_token"]
        self.refresh_token: str = raw["refresh_token"]
        self.expires_in: int = raw["expires_in"]
        self.scope: str | list[str] = raw["scope"]
        self.token_type: str = raw["token_type"]
        self._user_id: str | None = None
        self._user_login: str | None = None

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @user_id.setter
    def user_id(self, other: str) -> None:
        self._user_id = other

    @property
    def user_login(self) -> str | None:
        return self._user_login

    @user_login.setter
    def user_login(self, other: str) -> None:
        self._user_login = other


class ClientCredentialsPayload(BasePayload):
    __slots__ = ("access_token", "expires_in", "token_type")

    def __init__(self, raw: ClientCredentialsResponse, /) -> None:
        super().__init__(raw)

        self.access_token: str = raw["access_token"]
        self.expires_in: int = raw["expires_in"]
        self.token_type: str = raw["token_type"]


class AuthorizationURLPayload(BasePayload):
    __slots__ = ("client_id", "force_verify", "redirect_uri", "response_type", "scopes", "state", "url")

    def __init__(self, raw: AuthorizationURLResponse, /) -> None:
        super().__init__(raw)

        self.url: str = raw["url"]
        self.client_id: str = raw["client_id"]
        self.redirect_uri: str = raw["redirect_uri"]
        self.response_type: str = raw["response_type"]
        self.scopes: list[str] = raw["scopes"]
        self.force_verify: bool = raw["force_verify"]
        self.state: str = raw["state"]

    def __str__(self) -> str:
        return self.url
