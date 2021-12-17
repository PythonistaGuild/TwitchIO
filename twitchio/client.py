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
import typing

from .limiter import IRCRateLimiter
from .parser import IRCPayload
from .shards import ShardInfo
from .websocket import Websocket


class Client:

    def __init__(self,
                 token: typing.Optional[str] = None,
                 heartbeat: typing.Optional[float] = 30.0,
                 verified: typing.Optional[bool] = False,
                 join_timeout: typing.Optional[float] = 15.0,
                 initial_channels: typing.Optional[typing.Union[list, tuple, callable, typing.Coroutine]] = [],
                 shard_limit: int = 100,
                 ):
        self._token: str = token.removeprefix('oauth:') if token else token

        self._heartbeat = heartbeat
        self._verified = verified
        self._join_timeout = join_timeout

        self._shards = {}
        self._shard_limit = shard_limit
        self._initial_channels = initial_channels

        self._limiter = IRCRateLimiter(status='verified' if verified else 'user', bucket='joins')

    async def _shard(self):
        if asyncio.iscoroutinefunction(self._initial_channels):
            channels = await self._initial_channels()

        elif callable(self._initial_channels):
            channels = self._initial_channels()

        elif isinstance(self._initial_channels, (list, tuple)):
            channels = self._initial_channels
        else:
            raise TypeError('initial_channels must be a list, tuple, callable or coroutine returning a list or tuple.')

        if not isinstance(channels, (list, tuple)):
            raise TypeError('initial_channels must return a list or tuple of str.')

        chunked = [channels[x:x+self._shard_limit] for x in range(0, len(channels), self._shard_limit)]

        for index, chunk in enumerate(chunked, 1):
            self._shards[index] = ShardInfo(number=index,
                                            channels=channels,
                                            websocket=Websocket(
                                                client=self,
                                                limiter=self._limiter,
                                                shard_index=index,
                                                heartbeat=self._heartbeat,
                                                join_timeout=self._join_timeout,
                                                initial_channels=chunk))

    def run(self, token: str) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._shard())

        self._token = token.removeprefix('oauth:')

        for shard in self._shards.values():
            shard._websocket._token = self._token
            loop.create_task(shard._websocket._connect())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(self.close())

    async def start(self, token: str) -> None:
        await self._shard()

        self._token = token.removeprefix('oauth:')

        for shard in self._shards.values():
            shard._websocket._token = self._token
            await shard._websocket._connect()

    async def close(self) -> None:
        for shard in self._shards.values():
            await shard._websocket.close()

    @property
    def shards(self) -> dict[int, ShardInfo]:
        return self._shards

    @property
    def nick(self):
        """The bots nickname"""
        return self._shards[1]._websocket.nick

    nickname = nick

    async def event_shard_ready(self, number: int) -> None:
        pass

    async def event_ready(self) -> None:
        pass

    async def event_error(self) -> None:
        pass

    async def event_raw_data(self, data: str) -> None:
        pass

    async def event_raw_payload(self, payload: IRCPayload) -> None:
        pass

    async def event_message(self, message) -> None:
        pass



