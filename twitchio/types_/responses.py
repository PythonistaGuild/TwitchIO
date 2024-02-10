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
from typing import TypeAlias, TypedDict


__all__ = (
    "RefreshTokenResponse",
    "ValidateTokenResponse",
    "ClientCredentialsResponse",
    "OAuthResponses",
    "UserTokenResponse",
)


class RefreshTokenResponse(TypedDict):
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str | list[str]
    token_type: str


class UserTokenResponse(TypedDict):
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str | list[str]
    token_type: str


class ValidateTokenResponse(TypedDict):
    client_id: str
    login: str
    scopes: list[str]
    user_id: str
    expires_in: int


class ClientCredentialsResponse(TypedDict):
    access_token: str
    expires_in: int
    token_type: str


OAuthResponses: TypeAlias = RefreshTokenResponse | ValidateTokenResponse | ClientCredentialsResponse | UserTokenResponse
