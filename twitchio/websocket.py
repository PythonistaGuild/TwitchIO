"""MIT License

Copyright (c) 2017-2022 TwitchIO

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
from typing import TYPE_CHECKING, Optional, cast

import aiohttp
import logging

from .backoff import ExponentialBackoff
from .cache import Cache
from .channel import Channel
from .exceptions import *
from .limiter import IRCRateLimiter
from .message import Message
from .parser import IRCPayload
from .chatter import PartialChatter

if TYPE_CHECKING:
    from .client import Client
    from .limiter import IRCRateLimiter


logger = logging.getLogger(__name__)

HOST = 'wss://irc-ws.chat.twitch.tv:443'


class Websocket:

    def __init__(self,
                 client: 'Client',
                 limiter: IRCRateLimiter,
                 shard_index: int = 1,
                 heartbeat: Optional[float] = 30.0,
                 join_timeout: Optional[float] = 10.0,
                 initial_channels: Optional[list] = None,
                 cache_size: Optional[int] = None,
                 ):
        self.client = client

        self.ws: aiohttp.ClientWebSocketResponse = None  # type: ignore
        self.heartbeat = heartbeat

        self.join_limiter = limiter
        self.join_cache = {}
        self.join_timeout = join_timeout

        self._token = client._token
        self.shard_index = shard_index
        self.nick: str = None  # type: ignore
        self.initial_channels = initial_channels

        self._backoff = ExponentialBackoff()

        self.closing = False
        self._ready_event = asyncio.Event()
        self._keep_alive_task: asyncio.Task = None  # type: ignore

        self._channel_cache = Cache(size=cache_size)
        self._message_cache = Cache(size=cache_size)

    def is_connected(self) -> bool:
        return self.ws is not None and not self.ws.closed

    async def _connect(self) -> None:
        if self.closing:
            return

        self._ready_event.clear()

        if self.is_connected():
            await self.ws.close()

        async with aiohttp.ClientSession() as session:
            try:
                self.ws = await session.ws_connect(url=HOST, heartbeat=self.heartbeat)
            except Exception as e:
                retry = self._backoff.delay()
                logger.error(f'Websocket could not connect. {e}. Attempting reconnect in {retry} seconds.')

                await asyncio.sleep(retry)
                return await self._connect()

            headers = {'Authorization': f'Bearer {self._token}'}
            async with session.get(url='https://id.twitch.tv/oauth2/validate', headers=headers) as resp:
                if resp.status == 401:
                    raise AuthenticationError('Invalid token passed. Check your token and scopes and try again.')

                data = await resp.json()
                self.nick = data['login']

            session.detach()

        self._keep_alive_task = asyncio.create_task(self._keep_alive())

        await self.authentication_sequence()

        while self.join_cache:
            await asyncio.sleep(0.1)

        await self.dispatch(event='shard_ready', number=self.shard_index)
        self.client._shards[self.shard_index]._ready = True

        if all(s.ready for s in self.client._shards.values()):
            await self.dispatch(event='ready')

        await asyncio.wait_for(self._keep_alive_task, timeout=None)

    async def _keep_alive(self) -> None:
        while True:
            message: aiohttp.WSMessage = await self.ws.receive()

            if message.type is aiohttp.WSMsgType.CLOSED:
                if not self.closing:
                    logger.error(f"Websocket was unexpectedly closed. {message.extra or ''}")
                break

            data = message.data

            payloads = IRCPayload.parse(data=data)
            await self.dispatch('raw_data', data)

            for payload in payloads:
                payload: IRCPayload

                await self.dispatch('raw_payload', payload)

                if payload.code == 200:
                    event = self.get_event(cast(str, payload.action))
                    asyncio.create_task(event(payload)) if event else None

                elif payload.code == 1:
                    self._ready_event.set()
                    logger.info(f'Successful authentication on Twitch Websocket with nick: {self.nick}.')

        return await self._connect()

    async def authentication_sequence(self) -> None:
        await self.send(f'PASS oauth:{self._token}')
        await self.send(f'NICK {self.nick}')

        await self.send('CAP REQ :twitch.tv/membership')
        await self.send('CAP REQ :twitch.tv/tags')
        await self.send('CAP REQ :twitch.tv/commands')

        if self.initial_channels:
            await self.join_channels(self.initial_channels)

    async def join_timeout_task(self, channel: str) -> None:
        if self.join_timeout:
            await asyncio.sleep(self.join_timeout)

        del self.join_cache[channel]
        raise JoinFailed(f'The channel <{channel}> was not able be to be joined. Check the name and try again.')

    async def join_channels(self, channels: list) -> None:
        await self._ready_event.wait()

        channels = [c.removeprefix('#').lower() for c in channels]

        for channel in channels:
            self.join_cache[channel] = asyncio.create_task(self.join_timeout_task(channel), name=channel)

            await self.send(f'JOIN #{channel.lower()}')
            if cd := self.join_limiter.check_limit():
                await self.join_limiter.wait_for()

    async def send(self, message: str) -> None:
        message = message.strip('\r\n')

        try:
            await self.ws.send_str(f'{message}\r\n')
        except Exception as e:
            print(e)

    def dispatch_callback(self, task: asyncio.Task) -> None:
        if exc := task.exception():
            asyncio.create_task(self.dispatch('error', exc))

    async def dispatch(self, event: str, *args, **kwargs) -> None:
        if not event:
            return None

        event = event.lower()
        coro = getattr(self.client, f'event_{event}')

        if not coro:
            raise EventNotFound(f'The event <{event}> was not found.')
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('Events must be coroutines.')

        task = asyncio.create_task(coro(*args, **kwargs))
        task.add_done_callback(self.dispatch_callback)

    def get_event(self, action: str):
        if not action:
            return None

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

    async def privmsg_event(self, payload: IRCPayload) -> None:
        logger.debug(f'Received PRIVMSG from Twitch: '
                     f'channel={payload.channel}, '
                     f'chatter={payload.user}, '
                     f'content={payload.message}')
        channel = self._channel_cache.get(payload.channel, default=None)

        if channel is None:
            channel = Channel(name=payload.channel, websocket=self)
            self._channel_cache[channel.name] = channel

        chatter = PartialChatter(payload=payload)
        message = Message(payload=payload, channel=channel, echo=False, chatter=chatter)

        self._message_cache[message.id] = message
        channel._chatters[chatter.name] = chatter

        await self.dispatch('message', message)

    async def reconnect_event(self, payload: IRCPayload) -> None:
        asyncio.create_task(self._connect())

    async def ping_event(self, payload: IRCPayload) -> None:
        logger.info('Received PING from Twitch, sending reply PONG.')
        await self.send('PONG :tmi.twitch.tv')

    async def join_event(self, payload: IRCPayload) -> None:
        channel = Channel(name=payload.channel, websocket=self)

        if payload.channel in self.join_cache:
            self.remove_join_cache(channel.name)
            self._channel_cache[channel.name] = channel

        chatter = PartialChatter(payload=payload)  # TODO...

        if payload.user == self.nick:
            self._channel_cache[channel.name] = channel

        await self.dispatch('join', channel, chatter)

    async def part_event(self, payload: IRCPayload) -> None:
        if payload.user == self.nick:
            channel: Optional[Channel] = self._channel_cache.pop(payload.channel)
        else:
            channel = Channel(name=payload.channel, websocket=self)

        chatter = PartialChatter(payload=payload)  # TODO

        await self.dispatch('part', channel, chatter)

    async def cap_event(self, payload: IRCPayload) -> None:
        pass

    async def userstate_event(self, payload: IRCPayload) -> None:
        pass

    async def roomstate_event(self, payload: IRCPayload) -> None:
        pass

    async def whisper_event(self, payload: IRCPayload) -> None:
        pass

    async def close(self):
        self.closing = True

        await self.ws.close()

        try:
            self._keep_alive_task.cancel()
        except Exception:
            pass

        for task in self.join_cache.values():
            try:
                task.cancel()
            except Exception:
                pass
