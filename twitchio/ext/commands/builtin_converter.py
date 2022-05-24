"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

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

from __future__ import annotations
import re
from typing import TYPE_CHECKING

from twitchio import User, PartialUser, Chatter, PartialChatter, Channel, Clip
from .errors import BadArgument

if TYPE_CHECKING:
    from .core import Context


__all__ = (
    "convert_Chatter",
    "convert_Clip",
    "convert_Channel",
    "convert_PartialChatter",
    "convert_PartialUser",
    "convert_User",
)


async def convert_Chatter(ctx: Context, arg: str) -> Chatter:
    """
    Converts the argument into a chatter in the chat. If the chatter is not found, BadArgument is raised.
    """
    arg = arg.lstrip("@")
    resp = [x for x in filter(lambda c: c.name == arg, ctx.chatters or tuple())]
    if not resp:
        raise BadArgument(f"The user '{arg}' was not found in {ctx.channel.name}'s chat.")

    return resp[0]


async def convert_PartialChatter(ctx: Context, arg: str) -> Chatter:
    """
    Actually a shorthand to :ref:`~convert_Chatter`
    """
    return await convert_Chatter(ctx, arg)


async def convert_Clip(ctx: Context, arg: str) -> Clip:
    finder = re.search(r"(https://clips.twitch.tv/)?(?P<slug>.*)", arg)
    if not finder:
        raise RuntimeError(
            "regex failed to match"
        )  # this should never ever raise, but its here to make type checkers happy

    slug = finder.group("slug")
    clips = await ctx.bot.fetch_clips([slug])
    if not clips:
        raise BadArgument(f"Clip '{slug}' was not found")

    return clips[0]


async def convert_User(ctx: Context, arg: str) -> User:
    """
    Similar to convert_Chatter, but fetches from the twitch API instead,
    returning a :class:`twitchio.User` instead of a :class:`twitchio.Chatter`.
    To use this, you most have a valid client id and API token or client secret
    """
    arg = arg.lstrip("@")
    user = await ctx.bot.fetch_users(names=[arg])
    if not user:
        raise BadArgument(f"User '{arg}' was not found.")
    return user[0]


async def convert_PartialUser(ctx: Context, arg: str) -> User:
    """
    This is simply a shorthand to :ref:`~convert_User`, as fetching from the api will return a full user model
    """
    return await convert_User(ctx, arg)


async def convert_Channel(ctx: Context, arg: str) -> Channel:
    if arg not in ctx.bot._connection._cache:
        raise BadArgument(f"Not connected to channel '{arg}'")

    return ctx.bot.get_channel(arg)


_mapping = {
    User: convert_User,
    PartialUser: convert_PartialUser,
    Channel: convert_Channel,
    Chatter: convert_Chatter,
    PartialChatter: convert_PartialChatter,
    Clip: convert_Clip,
}
