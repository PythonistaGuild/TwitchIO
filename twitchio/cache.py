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

import time
import functools
from typing import Hashable


__all__ = ("TimedCache", "user_cache", "id_cache")


class TimedCache(dict):
    def __init__(self, seconds: int):
        self.__timeout = seconds
        super().__init__()

    def _verify_cache(self):
        now = time.monotonic()
        to_remove = [key for (key, (_, exp)) in self.items() if now > (exp + self.__timeout)]
        for k in to_remove:
            del self[k]

    def __getitem__(self, key):
        self._verify_cache()
        return super().__getitem__(key)[0]

    def __setitem__(self, key, value):
        super().__setitem__(key, (value, time.monotonic()))

    def __contains__(self, key):
        self._verify_cache()
        return {a: b[0] for a, b in self.items()}.__contains__(key)


def user_cache(timer=300):
    cache = TimedCache(timer)

    def wraps(func):
        @functools.wraps(func)
        async def _wraps(cls, names: list = None, ids: list = None, force=False, token=None):
            if not force:
                existing = []
                if names:
                    existing.extend([cache[x] for x in names if x in cache])

                if ids:
                    existing.extend([cache[x] for x in ids if x in cache])

                if len(existing) == (len(names) if names else 0) + (len(ids) if ids else 0):
                    return existing

            values = await func(cls, names=names, ids=ids, token=token)
            for v in values:
                cache[v.id] = v
                cache[v.name] = v

            return values

        return _wraps

    return wraps


def id_cache(timer=300):
    cache = TimedCache(timer)

    def wraps(func):
        @functools.wraps(func)
        def _wraps(cls, id: Hashable):
            if id in cache:
                return cache[id]

            value = func(cls, id)
            if value is not None:
                cache[id] = value

            return value

        return _wraps

    return wraps
