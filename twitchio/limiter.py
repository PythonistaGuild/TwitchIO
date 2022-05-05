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
import asyncio
import time

from typing import Optional

class IRCRateLimiter:

    buckets = {'verified': {'messages': 100, 'joins': 2000},
               'moderator': {'messages': 100, 'joins': 20},
               'user': {'messages': 20, 'joins': 20}}

    def __init__(self, *, status: str, bucket: str):
        self.bucket = self.buckets[status]
        self.tokens = self.bucket[bucket]

        self._tokens = self.tokens

        self.per = 30 if bucket == 'messages' else 10
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
