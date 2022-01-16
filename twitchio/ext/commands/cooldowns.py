# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

    default = 0
    channel = 1
    member = 2
    user = 3
    subscriber = 4
    mod = 5


class Cooldown:

    __slots__ = ("_rate", "_per", "bucket", "_window", "_tokens", "_cache")

    def __init__(self, rate: int, per: float, bucket: Bucket):
        self._rate = rate
        self._per = per
        self.bucket = bucket

        self._window = time.time() + self._per
        self._tokens = 0

        self._cache = {}

    def get_tokens(self, now=None):
        now = now or time.time()
        tokens = self._tokens

        if now > self._window + self._per:
            tokens = 0

        return tokens

    def update_bucket(self, ctx):
        now = time.time()

        self._tokens = self.get_tokens(now)

        if self._tokens == 0:
            self._window = now

        if self._tokens == self._rate:
            retry = self._per - (now - self._window)
            raise CommandOnCooldown(command=ctx.command, retry_after=retry)

        self._tokens += 1

        if self._tokens == self._rate:
            self._window = now

    def reset(self):
        self._tokens = 0
        self._window = time.time()

    def _bucket_keys(self, ctx):
        buckets = []

        for bucket in ctx.command._cooldowns:
            if bucket.bucket == Bucket.default:
                buckets.append("default")

            if bucket.bucket == Bucket.channel:
                buckets.append(ctx.channel.name)

            if bucket.bucket == Bucket.member:
                buckets.append((ctx.channel.name, ctx.author.id))
            if bucket.bucket == Bucket.user:
                buckets.append(ctx.author.id)

            if bucket.bucket == Bucket.subscriber:
                buckets.append((ctx.channel.name, ctx.author.id, 0))
            if bucket.bucket == Bucket.mod:
                buckets.append((ctx.channel.name, ctx.author.id, 1))

        return buckets

    def _update_cache(self, now=None):
        now = now or time.time()
        dead = [key for key, cooldown in self._cache.items() if now > cooldown._window + cooldown._per]

        for bucket in dead:
            del self._cache[bucket]

    def get_buckets(self, ctx):
        now = time.time()

        self._update_cache(now)

        bucket_keys = self._bucket_keys(ctx)
        buckets = []

        for index, bucket in enumerate(bucket_keys):
            if bucket not in self._cache:
                buckets.append(ctx.command._cooldowns[index])
                self._cache[bucket] = ctx.command._cooldowns[index]
            else:
                buckets.append(self._cache[bucket])

        return buckets
