import asyncio
import time


class RateBucket:

    HTTPLIMIT = 30
    IRCLIMIT = 5
    MODLIMIT = 5

    HTTP = 60
    IRC = 30

    def __init__(self, *, method: str):
        self.method = method

        if method == 'irc':
            self.reset_time = self.IRC
            self.limit = self.IRCLIMIT
        elif method == 'mod':
            self.reset_time = self.IRC
            self.limit = self.MODLIMIT
        else:
            self.reset_time = self.HTTP
            self.limit = self.HTTPLIMIT

        self.tokens = 0
        self._reset = time.time() + self.reset_time

    @property
    def limited(self):
        return self.tokens == self.limit

    def reset(self):
        self.tokens = 0
        self._reset = time.time() + self.reset_time

    def update(self, *, reset=None, remaining=None):
        now = time.time()

        if self._reset <= now:
            self.reset()

        if reset:
            self._reset = int(reset)

        if remaining:
            self.tokens = self.limit - int(remaining)
        else:
            self.tokens += 1

    async def wait_reset(self):
        now = time.time()

        await asyncio.sleep(self._reset - now)
        self.reset()