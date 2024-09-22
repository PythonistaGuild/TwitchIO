# -*- coding: utf-8 -*-

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
import enum
import time

from .errors import *


__all__ = (
    "Bucket",
    "Cooldown",
)


class Bucket(enum.Enum):
    """
    Enum values for the different cooldown buckets.

    Parameters
    ------------
    default: :class:`enum.Enum`
        The default bucket.
    channel: :class:`enum.Enum`
        Cooldown is shared amongst all chatters per channel.
    user: :class:`enum.Enum`
        Cooldown operates on a per user basis across all channels.
    member: :class:`enum.Enum`
        Cooldown operates on a per channel basis per user.
    turbo: :class:`enum.Enum`
        Cooldown for turbo users.
    subscriber: :class:`enum.Enum`
        Cooldown for subscribers.
    vip: :class:`enum.Enum`
        Cooldown for VIPs.
    mod: :class:`enum.Enum`
        Cooldown for mods.
    broadcaster: :class:`enum.Enum`
        Cooldown for the broadcaster.
    """

    default = 0
    channel = 1
    user = 2
    member = 3
    turbo = 4
    subscriber = 5
    vip = 6
    mod = 7
    broadcaster = 8


class Cooldown:
    """
    Cooldown decorator values.

    Parameters
    ------------
    rate: :class:`int`
        How many times the command can be invoked before triggering a cooldown inside a time frame.
    per: :class:`float`
        The amount of time in seconds to wait for a cooldown when triggered.
    bucket: :class:`Bucket`
        The bucket that the cooldown is in.

    Examples
    ----------

    .. code:: py

        # Restrict a command to once every 10 seconds on a per channel basis.
        @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
        @commands.command()
        async def my_command(self, ctx: commands.Context):
            pass

        # Restrict a command to once every 30 seconds for each individual channel a user is in.
        @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.member)
        @commands.command()
        async def my_command(self, ctx: commands.Context):
            pass

        # Restrict a command to 5 times every 60 seconds globally for a user.
        @commands.cooldown(rate=5, per=60, bucket=commands.Bucket.user)
        @commands.command()
        async def my_command(self, ctx: commands.Context):
            pass

        # Restrict a command to 5 times every 60 seconds globally for a user,
        # 5 times every 30 seconds if the user is turbo,
        # and 1 time every 1 second if they're the channel broadcaster
        @commands.cooldown(rate=5, per=60, bucket=commands.Bucket.user)
        @commands.cooldown(rate=5, per=30, bucket=commands.Bucket.turbo)
        @commands.cooldown(rate=1, per=1, bucket=commands.Bucket.broadcaster)
        @commands.command()
        async def my_command(self, ctx: commands.Context):
            pass
    """

    __slots__ = ("_rate", "_per", "bucket", "_cache")

    def __init__(self, rate: int, per: float, bucket: Bucket) -> None:
        self._rate = rate
        self._per = per
        self.bucket = bucket

        self._cache = {}

    def _update_cooldown(self, key, now) -> int | None:
        cooldown = self._cache[key]

        if cooldown["tokens"] == self._rate:
            retry = self._per - (now - cooldown["start_time"])
            return retry

        if cooldown["tokens"] == 1 and self._rate > 1:
            cooldown["next_start_time"] = now

        cooldown["tokens"] += 1

        if cooldown["tokens"] == self._rate and not self._rate == 1:
            cooldown["start_time"] = cooldown["next_start_time"]

        self._cache[key] = cooldown

    def reset(self) -> None:
        self._cache = {}

    def _key(self, ctx):
        key = None

        if self.bucket == Bucket.default:
            key = "default"
        elif self.bucket == Bucket.channel:
            key = ctx.channel.name
        elif self.bucket == Bucket.user:
            key = ctx.author.id
        elif self.bucket == Bucket.member:
            key = (ctx.channel.name, ctx.author.id)
        elif self.bucket == Bucket.turbo and ctx.author.is_turbo:
            key = (ctx.channel.name, ctx.author.id)
        elif self.bucket == Bucket.subscriber and ctx.author.is_subscriber:
            key = (ctx.channel.name, ctx.author.id)
        elif self.bucket == Bucket.vip and ctx.author.is_vip:
            key = (ctx.channel.name, ctx.author.id)
        elif self.bucket == Bucket.mod and ctx.author.is_mod:
            key = (ctx.channel.name, ctx.author.id)
        elif self.bucket == Bucket.broadcaster and ctx.author.is_broadcaster:
            key = (ctx.channel.name, ctx.author.id)

        return key

    def _update_cache(self, now) -> None:
        expired = []
        for key, cooldown in self._cache.items():
            if now > cooldown["start_time"] + self._per:
                if cooldown["tokens"] > 1:
                    cooldown["tokens"] -= 1
                    cooldown["start_time"] = cooldown["next_start_time"]
                    cooldown["next_start_time"] = now
                else:
                    expired.append(key)
        for key in expired:
            del self._cache[key]

    def on_cooldown(self, ctx) -> None:
        now = time.time()

        self._update_cache(now)

        key = self._key(ctx)
        if key:
            if not key in self._cache:
                self._cache[key] = {"tokens": 0, "start_time": now, "next_start_time": None}

            return self._update_cooldown(key, now)
