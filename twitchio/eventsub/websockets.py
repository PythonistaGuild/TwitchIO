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

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, cast

import aiohttp

from ..backoff import Backoff
from ..exceptions import WebsocketConnectionException
from ..models.eventsub import BaseEvent
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
from ..utils import (
    MISSING,
    _from_json,  # type: ignore
)


if TYPE_CHECKING:
    from ..client import Client
    from ..http import HTTPClient


logger: logging.Logger = logging.getLogger(__name__)


WSS: str = "wss://eventsub.wss.twitch.tv/ws"


class Websocket:
    __slots__ = (
        "_keep_alive_timeout",
        "_last_keepalive",
        "_keep_alive_task",
        "_session",
        "_session_id",
        "_socket",
        "_listen_task",
        "_ready",
        "_reconnect_attempts",
        "_backoff",
        "__subscription_count",
        "_client",
        "_token_for",
        "_http",
    )

    def __init__(
        self,
        *,
        keep_alive_timeout: float = 60,
        session: aiohttp.ClientSession | None = None,
        reconnect_attempts: int | None = MISSING,
        client: Client | None = None,
        token_for: str,
        http: HTTPClient,
    ) -> None:
        self._keep_alive_timeout: int = max(10, min(int(keep_alive_timeout), 600))
        self._last_keepalive: datetime.datetime | None = None
        self._keep_alive_task: asyncio.Task[None] | None = None

        self._session: aiohttp.ClientSession | None = session
        self._session_id: str | None = None

        self._socket: aiohttp.ClientWebSocketResponse | None = None
        self._listen_task: asyncio.Task[None] | None = None

        self._ready: asyncio.Event = asyncio.Event()

        attempts: int | None = (
            0 if reconnect_attempts is None else None if reconnect_attempts is MISSING else reconnect_attempts
        )
        self._reconnect_attempts = attempts
        self._backoff: Backoff = Backoff()

        self.__subscription_count: int = 0

        self._client: Client | None = client
        self._token_for: str = token_for
        self._http: HTTPClient = http

        if not client:
            logger.warning(
                "Eventsub Websocket is being used without a Client/Bot. Event dispatching is disabled for this websocket."
            )

    def __repr__(self) -> str:
        return f"EventsubWebsocket(session_id={self._session_id})"

    @property
    def keep_alive_timeout(self) -> int:
        return self._keep_alive_timeout

    @property
    def connected(self) -> bool:
        return bool(self._socket and not self._socket.closed)

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def can_subscribe(self) -> bool:
        # TODO: Track subscriptions on this websocket...
        return True

    @property
    def subscription_count(self) -> int:
        # TODO: Track subscriptions on this websocket...
        return self.__subscription_count

    async def connect(
        self, *, reconnect_url: str | None = None, reconnect: bool = False, fail_once: bool = False
    ) -> None:
        url: str = reconnect_url or f"{WSS}?keepalive_timeout_seconds={self._keep_alive_timeout}"

        if self.connected and not reconnect_url:
            logger.warning("Trying to connect to an already running eventsub websocket: <%r>.", self)
            return

        if not self._session:
            self._session = aiohttp.ClientSession()

        self._ready.clear()

        retries: int | None = self._reconnect_attempts
        if retries == 0 and reconnect:
            logger.info("<%r> was closed unexepectedly, but is flagged as 'should not reconnect'.", self)

            await self.close()
            return

        while True:
            try:
                self._socket = await self._session.ws_connect(url, heartbeat=15.0)
            except Exception as e:
                logger.debug("Failed to connect to eventsub websocket <%r>: %s.", self, e)

                if fail_once:
                    await self.close()
                    raise WebsocketConnectionException from e

            if self.connected:
                break

            if retries == 0:
                await self.close()

                raise WebsocketConnectionException(
                    "Failed to connect to eventsub websocket <%r> after %s retries. "
                    "Please attempt to reconnect or re-subscribe this eventsub connection.",
                    self,
                    self._reconnect_attempts,
                )

            if retries is not None:
                retries -= 1

            delay: float = self._backoff.calculate()
            logger.info('<%r> retrying to reconnect websocket connection in "%s" seconds.', self, delay)

            await asyncio.sleep(delay)

        if not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())

        try:
            async with asyncio.timeout(10 + 1):
                await self._ready.wait()
        except TimeoutError:
            await self.close()

            raise WebsocketConnectionException(
                "<%r> did not receive a welcome message from Twitch within the allowed timeframe. "
                "Please attempt to reconnect or re-subscribe this eventsub connection.",
                self,
            )

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
                return await self.connect(reconnect=True)

            type_: aiohttp.WSMsgType = message.type
            if type_ in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                logger.debug("Received close message [%s] on eventsub websocket: <%r>", self._socket.close_code, self)

                if self._socket.close_code == 4001:
                    logger.critical(
                        "<%r> attempted to send an outgoing message to Twitch. "
                        "Twitch prohibits sending outgoing messages to the server, this will result in a disconnect. "
                        "This websocket will NOT attempt to reconnect.",
                        self,
                    )
                    return await self.close()

                elif self._socket.close_code == 4003:
                    return await self.close()

                return await self.connect(reconnect=True)

            if type_ is not aiohttp.WSMsgType.TEXT:
                logger.debug("Received unknown message from eventsub websocket: <%r>", self)
                continue

            self._last_keepalive = datetime.datetime.now()

            try:
                data: WebsocketMessages = cast(WebsocketMessages, _from_json(message.data))
            except Exception:
                logger.warning("Unable to parse JSON in eventsub websocket: <%r>", self)
                continue

            metadata: MetaData = data["metadata"]
            message_type: MessageTypes = metadata["message_type"]

            if message_type == "session_welcome":
                welcome_data: WelcomeMessage = cast(WelcomeMessage, data)
                await self._process_welcome(welcome_data)

            elif message_type == "session_reconnect":
                logger.debug('Received "session_reconnect" message from eventsub websocket: <%r>', self)
                reconnect_data: ReconnectMessage = cast(ReconnectMessage, data)
                await self._process_reconnect(reconnect_data)

            elif message_type == "session_keepalive":
                logger.debug('Received "session_keepalive" message from eventsub websocket: <%r>', self)

            elif message_type == "revocation":
                logger.debug('Received "revocation" message from eventsub websocket: <%r>', self)

                revocation_data: RevocationMessage = cast(RevocationMessage, data)
                await self._process_revocation(revocation_data)

            elif message_type == "notification":
                logger.debug('Received "notification" message from eventsub websocket: <%r>. %s', self, data)

                notification_data: NotificationMessage = cast(NotificationMessage, data)
                await self._process_notification(notification_data)

            else:
                logger.warning("Received an unknown message type in eventsub websocket: <%r>", self)

    async def _process_keepalive(self) -> None:
        assert self._last_keepalive
        logger.debug("Started keep_alive task on eventsub websocket: <%r>", self)

        while True:
            await asyncio.sleep(self._keep_alive_timeout)

            now: datetime.datetime = datetime.datetime.now()
            if self._last_keepalive + datetime.timedelta(seconds=self._keep_alive_timeout + 5) < now:
                return await self.close()

    async def _process_welcome(self, data: WelcomeMessage) -> None:
        payload: WelcomePayload = data["payload"]
        self._session_id = payload["session"]["id"]
        self._ready.set()

        assert self._listen_task
        self._listen_task.set_name(f"EventsubWebsocketListener: {self._session_id}")

        logger.info('Received "session_welcome" message from eventsub websocket: <%r>', self)

    async def _process_reconnect(self, data: ReconnectMessage) -> None:
        logger.info("Attempting to reconnect eventsub websocket due to a reconnect message from Twitch: <%r>", self)
        await self.connect(reconnect_url=data["payload"]["session"]["reconnect_url"])

    async def _process_revocation(self, data: RevocationMessage) -> None: ...

    async def _process_notification(self, data: NotificationMessage) -> None:
        # TODO: Proper dispatch...
        subscription_type = data["metadata"]["subscription_type"]
        event: str = subscription_type.replace(".", "_")
        payload_class = BaseEvent.create_instance(subscription_type, data["payload"]["event"], http=self._http)

        if self._client:
            self._client.dispatch(event=event, payload=payload_class)

    async def close(self) -> None:
        if self._listen_task:
            try:
                self._listen_task.cancel()
            except Exception:
                pass

        if self._keep_alive_task:
            try:
                self._keep_alive_task.cancel()
            except Exception:
                pass

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

        if self._client:
            sockets = self._client._websockets.get(self._token_for, {})
            sockets.pop(self.session_id or "", None)

        logger.debug("Successfully closed eventsub websocket: <%r>", self)