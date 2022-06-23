"""MIT License

Copyright (c) 2017-2021 TwitchIO

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

__all__ = (
    "IRCRateLimiter",
    "HTTPRateLimiter",
    "RateLimitBucket",
)
import asyncio
import time
from typing import TYPE_CHECKING, Dict, Literal, Optional, TypeVar, Union, cast

import aiohttp

from .utils import MISSING

if TYPE_CHECKING:
    from .models import PartialUser, User

    UserT = Union[PartialUser, User]
    E = TypeVar("E", bound=BaseException)


class IRCRateLimiter:

    buckets = {
        "verified": {"messages": 100, "joins": 2000},
        "moderator": {"messages": 100, "joins": 20},
        "user": {"messages": 20, "joins": 20},
    }

    def __init__(self, *, status: str, bucket: str):
        self.bucket = self.buckets[status]
        self.tokens = self.bucket[bucket]

        self._tokens = self.tokens

        self.per = 30 if bucket == "messages" else 10
        self.time = time.time() + self.per

    def check_limit(self, *, time_: Optional[float] = None, update: bool = True) -> float:
        """Check and update the RateLimiter."""
        time_ = time_ or time.time()

        if time_ > self.time:
            self.tokens = self._tokens
            self.time = time.time() + self.per

        if update:
            self.tokens -= 1

        if self.tokens <= 0:
            return self.time - time.time()

        return 0.0

    async def wait_for(self, *, time_: Optional[float] = None) -> None:
        """Wait for the RateLimiter to cooldown."""
        time_ = time_ or time.time()

        await asyncio.sleep(self.check_limit(time_=time_, update=False))


class RateLimitBucket:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.reset_at: float = MISSING
        self.tokens: int = MISSING
        self.max_tokens: int = MISSING
        self.lock = asyncio.Lock()

    async def __aenter__(self) -> None:
        return await self.lock.__aenter__()

    async def __aexit__(self, *args) -> None:
        return await self.lock.__aexit__(*args)

    async def acquire(self) -> Literal[True]:
        return await self.lock.acquire()

    async def release(self) -> None:
        self.lock.release()

    def update(self, response: aiohttp.ClientResponse) -> None:
        self.reset_at = float(response.headers["ratelimit-reset"])
        self.tokens = int(response.headers["ratelimit-remaining"])
        self.max_tokens = int(response.headers["ratelimit-limit"])

    def _update_times(self) -> None:
        if self.reset_at <= time.time():
            self.tokens = self.max_tokens

    def hit(self, tokens: int) -> bool:
        if self.tokens is MISSING:
            return True  # we havent made a request yet, so it must be ok

        self._update_times()

        if tokens > self.max_tokens:
            raise ValueError("Cannot hit with more tokens than max available tokens")

        if self.tokens - tokens <= 0:
            return False

        self.tokens -= tokens
        return True

    async def wait(self, tokens: int) -> None:
        if not self.hit(tokens):
            await asyncio.sleep(self.reset_at - time.time())
            self.hit(tokens)


class HTTPRateLimiter:
    def __init__(self) -> None:
        self.buckets: Dict[Optional[UserT], RateLimitBucket] = {}

    def get_bucket(self, user: Optional[UserT]) -> RateLimitBucket:
        if user in self.buckets:
            return self.buckets[user]

        name: str
        if user:
            name = cast(str, user.name)
        else:
            name = "Client-Credential"

        bucket = RateLimitBucket(name)
        self.buckets[user] = bucket
        return bucket
