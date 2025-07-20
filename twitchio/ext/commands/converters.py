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

from typing import TYPE_CHECKING, Any, Protocol, TypeVar, runtime_checkable

from twitchio.user import User
from twitchio.utils import Color, Colour

from .exceptions import *


if TYPE_CHECKING:
    from .context import Context


__all__ = ("ColorConverter", "ColourConverter", "Converter", "UserConverter")


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


T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class Converter(Protocol[T_co]):
    """Base class used to create custom argument converters in :class:`~twitchio.ext.commands.Command`'s.

    To create a custom converter and do conversion logic on an argument you must override the :meth:`.convert` method.
    :meth:`.convert` must be a coroutine.

    Examples
    --------

    .. code:: python3

        class LowerCaseConverter(commands.Converter[str]):

            async def convert(self, ctx: commands.Context, arg: str) -> str:
                return arg.lower()


        @commands.command()
        async def test(ctx: commands.Context, arg: LowerCaseConverter) -> None: ...


    .. versionadded:: 3.1
    """

    async def convert(self, ctx: Context[Any], arg: str) -> T_co:
        """|coro|

        Method used on converters to implement conversion logic.

        Parameters
        ----------
        ctx: :class:`~twitchio.ext.commands.Context`
            The context provided to the converter after command invocation has started.
        arg: str
            The argument received in raw form as a :class:`str` and passed to the converter to do conversion logic on.
        """
        raise NotImplementedError("Classes that derive from Converter must implement this method.")


class UserConverter(Converter[User]):
    """The converter used to convert command arguments to a :class:`twitchio.User`.

    This is a default converter which can be used in commands by annotating arguments with the :class:`twitchio.User` type.

    .. note::

        This converter uses an API call to attempt to fetch a valid :class:`twitchio.User`.


    Example
    -------

    .. code:: python3

        @commands.command()
        async def test(ctx: commands.Context, *, user: twitchio.User) -> None: ...
    """

    async def convert(self, ctx: Context[Any], arg: str) -> User:
        client = ctx.bot

        arg = arg.lower()
        users: list[User]
        msg: str = 'Failed to convert "{}" to User. A User with the ID or login could not be found.'

        if arg.startswith("@"):
            arg = arg.removeprefix("@")
            users = await client.fetch_users(logins=[arg])

            if not users:
                raise BadArgument(msg.format(arg), value=arg)

        if arg.isdigit():
            users = await client.fetch_users(logins=[arg], ids=[arg])
        else:
            users = await client.fetch_users(logins=[arg])

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


class ColourConverter(Converter[Colour]):
    """The converter used to convert command arguments to a :class:`~twitchio.utils.Colour` object.

    This is a default converter which can be used in commands by annotating arguments with the :class:`twitchio.utils.Colour` type.

    This converter, attempts to convert ``hex`` and ``int`` type values only in the following formats:

    - `"#FFDD00"`
    - `"FFDD00"`
    - `"0xFFDD00"`
    - `16768256`


    ``hex`` values are attempted first, followed by ``int``.

    .. note::

        There is an alias to this converter named ``ColorConverter``.

    Example
    -------

    .. code:: python3

        @commands.command()
        async def test(ctx: commands.Context, *, colour: twitchio.utils.Colour) -> None: ...

    .. versionadded:: 3.1
    """

    async def convert(self, ctx: Context[Any], arg: str) -> Colour:
        try:
            result = Colour.from_hex(arg)
        except Exception:
            pass
        else:
            return result

        try:
            result = Colour.from_int(int(arg))
        except Exception:
            raise ConversionError(f"Unable to convert to Colour. {arg!r} is not a valid hex or colour integer value.")

        return result


ColorConverter = ColourConverter


def _bool(arg: str) -> bool:
    try:
        result = _BOOL_MAPPING[arg.lower()]
    except KeyError:
        pretty: str = " | ".join(f'"{k}"' for k in _BOOL_MAPPING)
        raise BadArgument(f'Failed to convert "{arg}" to type bool. Expected any: [{pretty}]', value=arg)

    return result


DEFAULT_CONVERTERS: dict[type, Any] = {str: str, int: int, float: float, bool: _bool, type(None): type(None)}
CONVERTER_MAPPING: dict[Any, Converter[Any] | type[Converter[Any]]] = {
    User: UserConverter,
    Colour: ColourConverter,
    Color: ColourConverter,
}
