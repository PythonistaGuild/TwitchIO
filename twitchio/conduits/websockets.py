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

from ..exceptions import WebsocketTimeoutException
from ..types_.conduits import (
    MessageTypes,
    MetaData,
    NotificationMessage,
    ReconnectMessage,
    RevocationMessage,
    WebsocketMessages,
    WelcomeMessage,
    WelcomePayload,
)
from ..utils import _from_json  # type: ignore


logger: logging.Logger = logging.getLogger(__name__)


WSS: str = "wss://eventsub.wss.twitch.tv/ws"


class Websocket:
    def __init__(
        self,
        *,
        keep_alive_timeout: float = 60,
        session: aiohttp.ClientSession | None = None,
        id: str,
    ) -> None:
        self._keep_alive_timeout: int = max(10, min(int(keep_alive_timeout), 600))
        self._last_keepalive: datetime.datetime | None = None
        self._keep_alive_task: asyncio.Task[None] | None = None

        self._session: aiohttp.ClientSession | None = session
        self._id: str = id
        self._session_id: str | None = None

        self._socket: aiohttp.ClientWebSocketResponse | None = None
        self._listen_task: asyncio.Task[None] | None = None

        self._ready: asyncio.Event = asyncio.Event()

    @property
    def keep_alive_timeout(self) -> int:
        return self._keep_alive_timeout

    @property
    def connected(self) -> bool:
        return bool(self._socket and not self._socket.closed)

    @property
    def id(self) -> str:
        return self._id

    async def connect(self, *, reconnect_url: str | None = None) -> None:
        url: str = reconnect_url or f"{WSS}?keepalive_timeout_seconds={self._keep_alive_timeout}"

        if self.connected:
            logger.warning("Trying to connect to an already running eventsub websocket with ID: %s.", self._session_id)
            return

        if not self._session:
            self._session = aiohttp.ClientSession()

        self._ready.clear()
        self._socket = await self._session.ws_connect(url, heartbeat=15.0)

        if not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())

        try:
            async with asyncio.timeout(10):
                await self._ready.wait()
        except TimeoutError:
            raise WebsocketTimeoutException

        if self._keep_alive_task:
            try:
                self._keep_alive_task.cancel()
            except Exception:
                pass

        self._keep_alive_task = asyncio.create_task(self._process_keepalive())

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
                logger.debug(
                    "Received close message [%s] on eventsub websocket: %s",
                    self._socket.close_code,
                    self._session_id,
                )
                return await self.close()

            if type_ is not aiohttp.WSMsgType.TEXT:
                logger.debug("Received unknown message from eventsub websocket: %s", self._session_id)
                continue

            self._last_keepalive = datetime.datetime.now()

            try:
                data: WebsocketMessages = cast(WebsocketMessages, _from_json(message.data))
            except Exception:
                logger.warning("Unable to parse JSON in eventsub websocket: %s", self._session_id)
                continue

            metadata: MetaData = data["metadata"]
            message_type: MessageTypes = metadata["message_type"]

            if message_type == "session_welcome":
                welcome_data: WelcomeMessage = cast(WelcomeMessage, data)
                await self._process_welcome(welcome_data)

            elif message_type == "session_reconnect":
                logger.debug('Received "session_reconnect" message from eventsub websocket: %s', self._session_id)
                reconnect_data: ReconnectMessage = cast(ReconnectMessage, data)
                await self._process_reconnect(reconnect_data)

            elif message_type == "session_keepalive":
                logger.debug('Received "session_keepalive" message from eventsub websocket: %s', self._session_id)

            elif message_type == "revocation":
                logger.debug('Received "revocation" message from eventsub websocket: %s', self._session_id)

                revocation_data: RevocationMessage = cast(RevocationMessage, data)
                await self._process_revocation(revocation_data)

            elif message_type == "notification":
                logger.debug('Received "notification" message from eventsub websocket: %s', self._session_id)

                notification_data: NotificationMessage = cast(NotificationMessage, data)
                await self._process_notification(notification_data)

            else:
                logger.warning("Received an unknown message type in eventsub websocket: %s", self._session_id)

    async def _process_keepalive(self) -> None:
        assert self._last_keepalive
        logger.debug("Started keep_alive task on eventsub websocket: %s", self._session_id)

        while True:
            await asyncio.sleep(self._keep_alive_timeout)

            now: datetime.datetime = datetime.datetime.now()
            if self._last_keepalive + datetime.timedelta(seconds=self._keep_alive_timeout + 5) < now:
                return await self.close()

    async def _process_welcome(self, data: WelcomeMessage) -> None:
        payload: WelcomePayload = data["payload"]
        self._session_id = payload["session"]["id"]
        self._ready.set()

        logger.debug('Received "session_welcome" message from eventsub websocket: %s', self._session_id)

    async def _process_reconnect(self, data: ReconnectMessage) -> None:
        logger.info("Attempting to reconnect eventsub websocket: '%s'", self._id)
        await self.connect(reconnect_url=data["payload"]["session"]["reconnect_url"])

    async def _process_revocation(self, data: RevocationMessage) -> None: ...

    async def _process_notification(self, data: NotificationMessage) -> None: ...

    async def close(self) -> None:
        if self._socket:
            try:
                await self._socket.close()
            except Exception:
                pass

        if self._session:
            try:
                await self._session.close()
            except Exception:
                pass

        if self._listen_task:
            try:
                self._listen_task.cancel()
            except Exception:
                pass

        logger.debug("Successfully closed eventsub websocket: %s", self._session_id)
