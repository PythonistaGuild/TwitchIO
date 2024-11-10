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

from typing import TYPE_CHECKING, Any

from twitchio.user import User

from .exceptions import *


if TYPE_CHECKING:
    from .bot import Bot
    from .context import Context

__all__ = ("_BaseConverter",)

_BOOL_MAPPING: dict[str, bool] = {
    "true": True,
    "false": False,
    "t": True,
    "f": False,
    "1": True,
    "0": False,
    "y": True,
    "n": False,
    "yes": True,
    "no": False,
}


class _BaseConverter:
    def __init__(self, client: Bot) -> None:
        self.__client: Bot = client

        self._MAPPING: dict[Any, Any] = {User: self._user}
        self._DEFAULTS: dict[type, Any] = {str: str, int: int, float: float, bool: self._bool, type(None): type(None)}

    def _bool(self, arg: str) -> bool:
        try:
            result = _BOOL_MAPPING[arg.lower()]
        except KeyError:
            pretty: str = " | ".join(f'"{k}"' for k in _BOOL_MAPPING)
            raise BadArgument(f'Failed to convert "{arg}" to type bool. Expected any: [{pretty}]', value=arg)

        return result

    async def _user(self, context: Context, arg: str) -> User:
        arg = arg.lower()
        users: list[User]
        msg: str = 'Failed to convert "{}" to User. A User with the ID or login could not be found.'

        if arg.startswith("@"):
            arg = arg.removeprefix("@")
            users = await self.__client.fetch_users(logins=[arg])

            if not users:
                raise BadArgument(msg.format(arg), value=arg)

        if arg.isdigit():
            users = await self.__client.fetch_users(logins=[arg], ids=[arg])
        else:
            users = await self.__client.fetch_users(logins=[arg])

        potential: list[User] = []

        for user in users:
            # ID's should be taken into consideration first...
            if user.id == arg:
                return user

            elif user.name == arg:
                potential.append(user)

        if potential:
            return potential[0]

        raise BadArgument(msg.format(arg), value=arg)
