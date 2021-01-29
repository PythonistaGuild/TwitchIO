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
    "convert_User"
)

async def convert_Chatter(ctx: "Context", arg: str):
    """
    Converts the argument into a chatter in the chat. If the chatter is not found, BadArgument is raised.
    """
    arg = arg.lstrip("@")
    resp = [x for x in filter(lambda c: c.name == arg, ctx.chatters)]
    if not resp:
        raise BadArgument(f"The user '{arg}' was not found in {ctx.channel.name}'s chat.")

    return resp[0]

async def convert_PartialChatter(ctx: "Context", arg: str):
    """
    Actually a shorthand to :ref:`~convert_Chatter`
    """
    return convert_Chatter(ctx, arg)

async def convert_Clip(ctx: "Context", arg: str):
    finder = re.search(r"(https://clips.twitch.tv/)?(?P<slug>.*)", arg)
    slug = finder.group('slug')
    clips = await ctx.bot.fetch_clips([slug])
    if not clips:
        raise BadArgument(f"Clip '{slug}' was not found")

    return clips[0]

async def convert_User(ctx: "Context", arg: str):
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

async def convert_PartialUser(ctx: "Context", arg: str):
    """
    This is simply a shorthand to :ref:`~convert_User`, as fetching from the api will return a full user model
    """
    return await convert_User(ctx, arg)

async def convert_Channel(ctx: "Context", arg: str):
    if arg not in ctx.bot._connection._cache:
        raise BadArgument(f"Not connected to channel '{arg}'")

    return ctx.bot.get_channel(arg)

_mapping = {
    User: convert_User,
    PartialUser: convert_PartialUser,
    Channel: convert_Channel,
    Chatter: convert_Chatter,
    PartialChatter: convert_PartialChatter,
    Clip: convert_Clip
}