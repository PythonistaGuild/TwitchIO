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

import aiohttp
import logging

from .backoff import ExponentialBackoff
from .exceptions import AuthenticationError, JoinFailed
from .limiter import IRCRateLimiter
from .parser import IRCPayload


logger = logging.getLogger(__name__)

HOST = 'wss://irc-ws.chat.twitch.tv:443'


class Websocket:

    def __init__(self,
                 token: str,
                 heartbeat: typing.Optional[float] = 30.0,
                 verified: typing.Optional[bool] = False,
                 join_timeout: typing.Optional[float] = 30.0,
                 initial_channels: list = ['evieepy']
                 ):
        self.ws: aiohttp.ClientWebSocketResponse = None  # type: ignore
        self.heartbeat = heartbeat

        self.join_limiter = IRCRateLimiter(status='verified' if verified else 'user', bucket='joins')
        self.join_cache = {}
        self.join_timeout = join_timeout

        self._token = token.removeprefix("oauth:")
        self.nick: str = None  # type: ignore
        self.initial_channels = initial_channels

        self._backoff = ExponentialBackoff()

        self._ready_event = asyncio.Event()
        self._keep_alive_task: asyncio.Task = None  # type: ignore

    def is_connected(self) -> bool:
        return self.ws is not None and not self.ws.closed

    async def _connect(self) -> None:
        self._ready_event.clear()

        if self.is_connected():
            await self.ws.close()

        if self._keep_alive_task:
            try:
                self._keep_alive_task.cancel()
            except Exception as e:
                logger.debug(e)

            self._keep_alive_task = None

        async with aiohttp.ClientSession() as session:
            try:
                self.ws = await session.ws_connect(url=HOST, heartbeat=self.heartbeat)
            except Exception as e:
                retry = self._backoff.delay()
                logger.error(f'Websocket could not connect. {e}. Attempting reconnect in {retry} seconds.')

                await asyncio.sleep(retry)
                asyncio.create_task(self._connect())

                return

            headers = {'Authorization': f'Bearer {self._token}'}
            async with session.get(url='https://id.twitch.tv/oauth2/validate', headers=headers) as resp:
                if resp.status == 401:
                    raise AuthenticationError('Invalid token passed. Check your token and scopes and try again.')

                data = await resp.json()
                self.nick = data['login']

            session.detach()

        self._keep_alive_task = asyncio.create_task(self._keep_alive())
        await self.authentication_sequence()

    async def _keep_alive(self) -> None:
        while True:
            message: aiohttp.WSMessage = await self.ws.receive()

            if message.type is aiohttp.WSMsgType.CLOSED:
                logger.error(f'Websocket was unexpectedly closed. {message.extra}')
                break

            data = message.data
            payloads = IRCPayload.parse(data=data)

            # TODO REMOVE PRINT
            print(data)

            for payload in payloads:
                match payload.code:
                    case 200:
                        event = self.get_event(payload.action)
                        asyncio.create_task(event(payload)) if event else None
                        break
                    case 1:
                        self._ready_event.set()
                        logger.info(f'Successful authentication on Twitch Websocket with nick: {self.nick}.')
                        break
                    case _:
                        break

        asyncio.create_task(self._connect())

    async def authentication_sequence(self) -> None:
        await self.send(f'PASS oauth:{self._token}')
        await self.send(f'NICK {self.nick}')

        await self.send('CAP REQ :twitch.tv/membership')
        await self.send('CAP REQ :twitch.tv/tags')
        await self.send('CAP REQ :twitch.tv/commands')

        await self.join_channels(self.initial_channels)

    async def join_timeout_task(self, channel: str) -> None:
        await asyncio.sleep(self.join_timeout)

        del self.join_cache[channel]
        raise JoinFailed(f'The channel <{channel}> was not able be to be joined. Check the name and try again.')

    async def join_channels(self, channels: list) -> None:
        await self._ready_event.wait()
        await asyncio.sleep(10)

        channels = [c.removeprefix('#') for c in channels]

        for channel in channels:
            self.join_cache[channel] = asyncio.create_task(self.join_timeout_task(channel), name=channel)

            await self.send(f'JOIN #{channel.lower()}')
            cd = self.join_limiter.check_limit()

            if cd:
                await self.join_limiter.wait_for()

    async def send(self, message: str) -> None:
        message = message.strip('\r\n')

        await self.ws.send_str(f'{message}\r\n')

    def get_event(self, action: str):
        action = action.lower()

        return getattr(self, f'{action}_event')

    def remove_join_cache(self, channel: str) -> None:
        try:
            task = self.join_cache[channel]
        except KeyError:
            return

        try:
            task.cancel()
        except Exception as e:
            logger.debug(f'An error occurred cancelling a join task. {e}')

        del self.join_cache[channel]

    async def reconnect_event(self, payload: IRCPayload) -> None:
        pass

    async def ping_event(self, payload: IRCPayload) -> None:
        await self.send('PONG :tmi.twitch.tv')

    async def join_event(self, payload: IRCPayload) -> None:
        self.remove_join_cache(payload.channel)
