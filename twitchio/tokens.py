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
from typing import Optional, Union, Dict, Any, Set, List, TYPE_CHECKING

import aiohttp
import time
from yarl import URL

from .exceptions import InvalidToken, RefreshFailure
from .utils import json_loader

if TYPE_CHECKING:
    #from .user import PartialUser, User
    #from .http import Route
    User = PartialUser = HTTPHandler = Any

VALIDATE_URL = URL("https://id.twitch.tv/oauth2/validate")
REFRESH_URL = URL("https://id.twitch.tv/oauth2/refresh")

class Token:
    def __init__(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        self.access_token: str = access_token
        self.refresh_token: Optional[str] = refresh_token
        self._user: Optional[PartialUser] = None
        self._scopes: List[str] = []
        self._last_validation: Optional[float] = None
    
    async def refresh(self, http: HTTPHandler, session: aiohttp.ClientSession) -> None:
        """|coro|
        Refreshes the access token, if a refresh token has been provided.
        If one hasn't been provided, this will raise :class:`~twitchio.InvalidToken`.

        Parameters
        -----------
        http: Any
            TODO
        session: :class:`~aiohttp.ClientSession`
            The session to use to refresh the token
        
        Raises
        -------
        :error:`~twitchio.InvalidToken`
            The refresh token is missing or invalid
        """
        
        if not http.has_client_credentials:
            raise RefreshFailure("Cannot refresh OAuth tokens without client credentials passed to Client")
        
        client_id, client_secret = await http.get_client_credentials()

        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        async with session.get(REFRESH_URL, data=payload) as resp:
            data = await resp.json(loads=json_loader)
            if data['status'] == 401:
                raise RefreshFailure(data['message'])
            
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']

    
    async def validate(self, http: HTTPHandler, session: aiohttp.ClientSession) -> None:
        """|coro|
        Validates the token, caching information on how this token is to be used.
        Tokens must be validated every hour, as per the `dev docs <https://dev.twitch.tv/docs/authentication/validate-tokens>`_.

        Parameters
        -----------
        http: Any
            TODO
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
                    await self.refresh(http, session)
                except Exception as e:
                    raise InvalidToken("The token is invalid, and a new one could not be generated") from e
            
            data = await resp.json(loads=json_loader)
        
        if "login" not in data:
            raise InvalidToken("The token provided is an app access token. These cannot be used with the Token object")

        else:
            self._scopes = data['scopes']
            self._user = PartialUser(http, data['user_id'], data['login'])
    
    async def get(self, http: HTTPHandler, session: aiohttp.ClientSession) -> str:
        """|coro|
        Ensures the token is still within the validation period, and then returns the current access token.

        Parameters
        -----------
        http: Any
            TODO
        session: :class:`~aiohttp.ClientSession`
            The session to use for validating the token
        
        Raises
        -------
        :error:`~twitchio.InvalidToken`
            This token is invalid
        """
        if not self._last_validation or self._last_validation < (time.time() - 3600):
            await self.validate(http, session)
        
        return self.access_token


class BaseTokenHandler:
    """
    A base class to manage user tokens.
    Ill fill this in later
    """

    def __init__(self) -> None:
        self.__cache: Dict[Union[User, PartialUser], Set[Token]] = {}

    async def get_user_token(self, user: Union[User, PartialUser], scope: Optional[str]) -> Token:
        ...
    
    async def get_client_token(self) -> str:
        ...
    
    async def _client_get_user_token(self, http: HTTPHandler, user: Union[PartialUser, User], scope: Optional[str], *, no_cache: bool = False) -> Token:
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
            await token.validate(http, http.session)
        except Exception as e:
            # TODO fire error handlers
            raise
        
        if user not in self.__cache:
            self.__cache[user] = set()
        
        self.__cache[user].add(token)
        return token

class SimpleTokenHandler(BaseTokenHandler):
    """
    A simple token handler, it takes an access token (and optionally a refresh token), and uses that access token for every request.
    You may also pass a client_token, which will be used for all requests that do not use a user token.
    If not provided, the user access token will be used for all requests.
    """
    def __init__(self, access_token: str, refresh_token: Optional[str] = None, client_token: Optional[str] = None) -> None:
        super().__init__()
        self.user_token = Token(access_token, refresh_token)
        self.client_token = client_token
    
    async def get_user_token(self, user: Union[User, PartialUser], scope: Optional[str]) -> Token:
        return self.user_token
    
    async def get_client_token(self) -> str:
        if self.client_token:
            return self.client_token
        
        return self.user_token.access_token
