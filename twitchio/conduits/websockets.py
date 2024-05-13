"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

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
import datetime
import logging
from typing import cast

import aiohttp

from ..types_.conduits import (
    KeepAliveMessage,
    MessageTypes,
    MetaData,
    NotificationMessage,
    ReconnectMessage,
    RevocationMessage,
    WebsocketMessages,
    WelcomeMessage,
    WelcomePayload,
)
from ..utils import _from_json, a_timeout, parse_timestamp  # type: ignore
from ..exceptions import WebsocketTimeoutException


logger: logging.Logger = logging.getLogger(__name__)


WSS: str = "wss://eventsub.wss.twitch.tv/ws"


class Websocket:
    def __init__(
        self, *, keep_alive_timeout: float = 60, session: aiohttp.ClientSession | None = None, id: int
    ) -> None:
        self._keep_alive_timeout: int = max(10, min(int(keep_alive_timeout), 600))
        self._session: aiohttp.ClientSession | None = session
        self._id: int = id
        self._session_id: str | None = None

        self._socket: aiohttp.ClientWebSocketResponse | None = None
        self._listen_task: asyncio.Task[None] | None = None

        self._ready: asyncio.Event = asyncio.Event()
        self._last_keepalive: datetime.datetime | None = None

    @property
    def keep_alive_timeout(self) -> int:
        return self._keep_alive_timeout

    @property
    def connected(self) -> bool:
        return bool(self._socket and not self._socket.closed)

    @property
    def id(self) -> int:
        return self._id

    async def connect(self) -> None:
        url: str = f"{WSS}?keepalive_timeout_seconds={self._keep_alive_timeout}"

        if self.connected:
            logger.warning("Trying to connect to an already running conduit websocket with ID: %s.", self._session_id)
            return

        if not self._session:
            self._session = aiohttp.ClientSession()

        self._socket = await self._session.ws_connect(url)
        self._listen_task = asyncio.create_task(self._listen())

        self._ready.clear()
        
        try:
            async with a_timeout(10):
                await self._ready.wait()
        except TimeoutError:
            raise WebsocketTimeoutException

    async def _listen(self) -> None:
        assert self._socket

        while True:
            try:
                message: aiohttp.WSMessage = await self._socket.receive()
            except Exception:
                # TODO: Proper error handling...
                return await self.close()

            type_: aiohttp.WSMsgType = message.type
            if type_ in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                logger.debug("Received close message on conduit websocket: %s", self._session_id)
                return await self.close()

            if type_ is not aiohttp.WSMsgType.TEXT:
                logger.debug("Received unknown message from conduit websocket: %s", self._session_id)
                continue

            try:
                data: WebsocketMessages = cast(WebsocketMessages, _from_json(message.data))
            except Exception:
                logger.warning("Unable to parse JSON in conduit websocket: %s", self._session_id)
                continue

            metadata: MetaData = data["metadata"]
            message_type: MessageTypes = metadata["message_type"]

            if message_type == "session_welcome":
                welcome_data: WelcomeMessage = cast(WelcomeMessage, data)
                await self._process_welcome(welcome_data)

            elif message_type == "session_reconnect":
                logger.debug('Received "session_reconnect" message from conduit websocket: %s', self._session_id)
                reconnect_data: ReconnectMessage = cast(ReconnectMessage, data)
                await self._process_reconnect(reconnect_data)

            elif message_type == "session_keepalive":
                logger.debug('Received "session_keepalive" message from conduit websocket: %s', self._session_id)
                
                keepalive_data: KeepAliveMessage = cast(KeepAliveMessage, data)
                await self._process_keepalive(keepalive_data)

            elif message_type == "revocation":
                logger.debug('Received "revocation" message from conduit websocket: %s', self._session_id)
                
                revocation_data: RevocationMessage = cast(RevocationMessage, data)
                await self._process_revocation(revocation_data)

            elif message_type == "notification":
                logger.debug('Received "notification" message from conduit websocket: %s', self._session_id)
                
                notification_data: NotificationMessage = cast(NotificationMessage, data)
                await self._process_notification(notification_data)

            else:
                logger.warning("Received an unknown message type in conduit websocket: %s", self._session_id)

    async def _process_welcome(self, data: WelcomeMessage) -> None:
        payload: WelcomePayload = data["payload"]
        self._session_id = payload["session"]["id"]
        self._ready.set()
        
        logger.debug('Received "session_welcome" message from conduit websocket: %s', self._session_id)

    async def _process_reconnect(self, data: ReconnectMessage) -> None: ...

    async def _process_keepalive(self, data: KeepAliveMessage) -> None:
        now: datetime.datetime = datetime.datetime.now()
        
        if self._last_keepalive and self._last_keepalive + datetime.timedelta(seconds=self._keep_alive_timeout) < now:
            # TODO: Reconnect and resubscribe
            return await self.close()

        self._last_keepalive = now

    async def _process_revocation(self, data: RevocationMessage) -> None: ...

    async def _process_notification(self, data: NotificationMessage) -> None: ...

    async def close(self) -> None:
        if self._socket:
            try:
                await self._socket.close()
            except Exception:
                ...

        if self._session:
            try:
                await self._session.close()
            except Exception:
                ...

        if self._listen_task:
            try:
                self._listen_task.cancel()
            except Exception:
                ...
        
        logger.debug("Successfully closed conduit websocket: %s", self._session_id)
