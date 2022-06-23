"""MIT License

Copyright (c) 2017-2022 TwitchIO

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

import time
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from yarl import URL

from .exceptions import InvalidToken, RefreshFailure
from .utils import json_loader

if TYPE_CHECKING:
    from .client import Client
    from .http import HTTPHandler
    from .models import PartialUser, User

__all__ = ("BaseToken", "Token", "BaseTokenHandler", "SimpleTokenHandler")

VALIDATE_URL = URL("https://id.twitch.tv/oauth2/validate")
REFRESH_URL = URL("https://id.twitch.tv/oauth2/refresh")


class BaseToken:
    """
    A base token container.
    This base class takes an access token, and does no validation on it before allowing it to be used for requests.
    This is useful for passing app access tokens.

    Attributes
    -----------
    access_token: :class:`str`
        The access token to use

    .. versionadded:: 3.0
    """

    def __init__(self, access_token: str) -> None:
        self.access_token: str = access_token

    async def get(self, http: HTTPHandler, handler: BaseTokenHandler, session: aiohttp.ClientSession) -> str:
        """|coro|
        Ensures the token is still within the validation period, and then returns the current access token.

        Parameters
        -----------
        http: :class:`~twitchio.http.HTTPHandler`
            The HTTP session
        handler: :class:`BaseTokenHandler`
            The handler passed to your Client/Bot
        session: :class:`~aiohttp.ClientSession`
            The session to use for validating the token

        Raises
        -------
        :error:`~twitchio.InvalidToken`
            This token is invalid

        Returns
        --------
        :class:`str`
            The access token
        """
        return self.access_token


class Token(BaseToken):
    """
    A container around user OAuth tokens.
    This class will automatically ensure tokens are valid before allowing the library to use them, and will refresh tokens if possible.

    Attributes
    -----------
    access_token: :class:`str`
        The token itself. This should **not** be prefixed with ``oauth:``!
    refresh_token: Optional[:class:`str`]
        The reresh token associated with the access token. This is not useful unless you have passed ``client_secret`` to your :class:`~twitchio.Client`/:class:`~twitchio.ext.commands.Bot`

    """

    def __init__(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        super().__init__(access_token)
        self.refresh_token: Optional[str] = refresh_token
        self._user: Optional[PartialUser] = None
        self._scopes: List[str] = []
        self._last_validation: Optional[float] = None

    async def refresh(self, handler: BaseTokenHandler, session: aiohttp.ClientSession) -> None:
        """|coro|
        Refreshes the access token, if a refresh token has been provided.
        If one hasn't been provided, this will raise :class:`~twitchio.InvalidToken`.

        Parameters
        -----------
        handler: :class:`BaseTokenHandler`
            The token handler being used to refresh this token. This should be the same handler that was passed to your Client/Bot
        session: :class:`~aiohttp.ClientSession`
            The session to use to refresh the token

        Raises
        -------
        :error:`~twitchio.InvalidToken`
            The refresh token is missing or invalid
        """
        client_id, client_secret = await handler.get_client_credentials()

        if not client_id or not client_secret:
            raise RefreshFailure("Cannot refresh user tokens without a client ID and client secret present")

        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }

        async with session.get(REFRESH_URL, data=payload) as resp:
            data = await resp.json(loads=json_loader)
            if data["status"] == 401:
                raise RefreshFailure(data["message"])

            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]

    async def validate(self, http: HTTPHandler, handler: BaseTokenHandler, session: aiohttp.ClientSession) -> None:
        """|coro|
        Validates the token, caching information on how this token is to be used.
        Tokens must be validated every hour, as per the `dev docs <https://dev.twitch.tv/docs/authentication/validate-tokens>`_.

        Parameters
        -----------
        http: :class:`~twitchio.http.HTTPManager
            The HTTP session
        handler: :class:`BaseTokenHandler`
            The handler that was passed to your Client/Bot
        session: :class:`~aiohttp.ClientSession`
            The session to use for validating the token

        Raises
        -------
        :error:`~twitchio.InvalidToken`
            This token is invalid
        """

        async with session.get(VALIDATE_URL, headers={"Authorization": f"OAuth {self.access_token}"}) as resp:
            if resp.status == 401:
                try:
                    await self.refresh(handler, session)
                except Exception as e:
                    raise InvalidToken("The token is invalid, and a new one could not be generated") from e

            data = await resp.json(loads=json_loader)

        if "login" not in data:
            raise InvalidToken("The token provided is an app access token. These cannot be used with the Token object")

        else:
            from .models import PartialUser

            self._scopes = data["scopes"]
            self._user = PartialUser(http, data["user_id"], data["login"])

    async def get(self, http: HTTPHandler, handler: BaseTokenHandler, session: aiohttp.ClientSession) -> str:
        """|coro|
        Ensures the token is still within the validation period, and then returns the current access token.

        Parameters
        -----------
        http: :class:`~twitchio.http.HTTPHandler`
            The HTTP session
        handler: :class:`BaseTokenHandler`
            The handler passed to your Client/Bot
        session: :class:`~aiohttp.ClientSession`
            The session to use for validating the token

        Raises
        -------
        :error:`~twitchio.InvalidToken`
            This token is invalid

        Returns
        --------
        :class:`str`
            The access token
        """
        if not self._last_validation or self._last_validation < (time.time() - 3600):
            await self.validate(http, handler, session)

        return self.access_token

    def has_scope(self, scope: str) -> Optional[bool]:
        """
        A helper function which determines whether the given token has a given scope or not.
        If the token has not previously been validated, this function will return ``None``

        Parameters
        -----------
        scope: :class:`str`
            The scope to check this token for

        Returns
        --------
        Optional[:class:`bool`]
            Whether this token has the scope or not
        """
        if not self._scopes:
            return None

        return scope in self._scopes


class BaseTokenHandler:
    """
    A base class to manage user tokens.
    Ill fill this in later
    """

    def __init__(self) -> None:
        self.__cache: Dict[Union[User, PartialUser], Set[Token]] = {}

    async def get_user_token(self, user: Union[User, PartialUser], scopes: List[str]) -> Token:
        """|coro|
        Method to be overriden in a subclass.
        This function receives a user and a list of scopes that the request needs any one of to make the request.
        It should return a :class:`Token` object.

        .. note::
            It is a good idea to pass a refresh token if you have one available,
            the library will automatically handle refreshing tokens if one is provided.

        Parameters
        -----------
        user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
            The user that a token is expected for.
        scopes: List[:class:`str`]
            A list of scopes that the endpoint needs one of. Any one or more of the scopes must be present on the returned token to successfully make the request

        Returns
        --------
        :class:`Token`
            The token for the associated user.
        """
        raise NotImplementedError

    async def get_client_token(self) -> str:
        raise NotImplementedError

    async def _client_get_user_token(
        self, http: HTTPHandler, user: Union[PartialUser, User], scope: List[str], *, no_cache: bool = False
    ) -> Token:
        if not no_cache and user in self.__cache:
            if not self.__cache[user]:
                del self.__cache[user]

            elif scope:
                for token in self.__cache[user]:
                    if scope in token._scopes:
                        return token

            else:
                return next(iter(self.__cache[user]))

        try:
            token = await self.get_user_token(user, scope)
            if not http._session:
                await http.prepare()

            await token.validate(http, self, http._session)  # type: ignore
        except Exception as e:
            # TODO fire error handlers
            raise

        if user not in self.__cache:
            self.__cache[user] = set()

        self.__cache[user].add(token)
        return token

    async def _client_get_client_token(self) -> BaseToken:
        try:
            return BaseToken(await self.get_client_token())
        except Exception as e:
            # TODO fire error handlers
            raise

    async def _client_get_irc_login(self, client: Client, shard_id: int) -> Tuple[str, PartialUser]:
        try:
            token = await self.get_irc_token(shard_id)
        except Exception as e:
            raise  # TODO fire error handlers

        if not client._http._session:
            await client._http.prepare()

        resp = await token.get(client._http, self, client._http._session)  # type: ignore

        if not token.has_scope("chat:login") and not token.has_scope("chat:read"):
            raise InvalidToken(
                f"The token given for user {token._user} does not have the chat:login or chat:read scope."
            )

        return resp, token._user  # type: ignore

    async def get_client_credentials(self) -> Tuple[str, Optional[str]]:
        """|coro|
        Method to be overriden in a subclass.
        This should return a :class:`tuple` of (client id, client secret).
        The client secret is not required, however the client id is required to make requests to the twitch API.
        The client secret is required to automatically refresh user tokens when they expire, however it is not required to access the twitch API.
        """
        raise NotImplementedError

    async def get_irc_token(self, shard_id: int) -> Token:
        """|coro|
        Method to be overriden in a subclass.
        This should return a :class:`Token` containing an OAuth token with the ``chat:login`` scope.

        Parameters
        -----------
        shard_id: :class:`int`
            The shard that is attempting to connect.

        Returns
        -------
        :class:`Token`
            The token with which to connect
        """
        raise NotImplementedError


class SimpleTokenHandler(BaseTokenHandler):
    """
    A simple token handler, it takes an access token (and optionally a refresh token), and uses that access token for every request.
    You may also pass a client_token, which will be used for all requests that do not use a user token.
    If not provided, the user access token will be used for all requests.

    Attributes
    -----------
    user_token: :class:`Token`
        The token to use for all requests
    client_token: Optional[:class:`str`]
        The token to use for all client credential requests (requests that don't require user authorization)
    client_id: :class:`str`
        The client id associated with all tokens
    client_secret: Optional[:class:`str`]
        The client secret associated with the client id. This can be used to refresh tokens if they expire
    """

    def __init__(
        self,
        access_token: str,
        client_id: str,
        refresh_token: Optional[str] = None,
        client_token: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.user_token = Token(access_token, refresh_token)
        self.client_token = client_token
        self.client_id: str = client_id
        self.client_secret: Optional[str] = client_secret

    async def get_user_token(self, user: Union[User, PartialUser], scope: Optional[str]) -> Token:
        return self.user_token

    async def get_client_token(self) -> str:
        if self.client_token:
            return self.client_token

        return self.user_token.access_token

    async def get_client_credentials(self) -> Tuple[str, Optional[str]]:
        return self.client_id, self.client_secret

    async def get_irc_token(self, shard_id: int) -> Token:
        return self.user_token
