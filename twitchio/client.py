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

from .parser import IRCPayload
from .websocket import Websocket


class Client:

    def __init__(self,
                 token: typing.Optional[str] = None,
                 heartbeat: typing.Optional[float] = 30.0,
                 verified: typing.Optional[bool] = False,
                 join_timeout: typing.Optional[float] = 15.0,
                 initial_channels=None
                 ):
        # TODO INITIAL_CHANNEL LOGIC
        self._token: str = token.removeprefix('oauth:') if token else token
        self._websocket = Websocket(
            client=self,
            heartbeat=heartbeat,
            verified=verified,
            join_timeout=join_timeout,
            initial_channels=initial_channels
        )

    def run(self, token: str) -> None:
        self._token = self._websocket._token = token.removeprefix('oauth:')
        loop = asyncio.get_event_loop()

        try:
            loop.create_task(self._websocket._connect())
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(self.close())

    async def start(self, token: str) -> None:
        self._token = self._websocket._token = token.removeprefix('oauth:')

        await self._websocket._connect()

    async def close(self) -> None:
        await self._websocket.close()

    @property
    def nick(self):
        """The bots nickname"""
        return self._websocket.nick

    nickname = nick

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



