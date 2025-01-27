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
from ..exceptions import HTTPException, WebsocketConnectionException
from ..models.eventsub_ import SubscriptionRevoked, create_event_instance
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
from .subscriptions import _SUB_MAPPING


if TYPE_CHECKING:
    from ..authentication.tokens import ManagedHTTPClient
    from ..client import Client
    from ..types_.conduits import Condition
    from ..types_.eventsub import SubscriptionResponse, _SubscriptionData


logger: logging.Logger = logging.getLogger(__name__)


WSS: str = "wss://eventsub.wss.twitch.tv/ws"


class Websocket:
    __slots__ = (
        "__subscription_cost",
        "_backoff",
        "_client",
        "_closed",
        "_connecting",
        "_connection_tasks",
        "_heartbeat",
        "_http",
        "_keep_alive_task",
        "_keep_alive_timeout",
        "_last_keepalive",
        "_listen_task",
        "_original_attempts",
        "_ready",
        "_reconnect_attempts",
        "_session_id",
        "_socket",
        "_subscriptions",
        "_token_for",
    )

    def __init__(
        self,
        *,
        keep_alive_timeout: float = 10,
        reconnect_attempts: int | None = MISSING,
        client: Client | None = None,
        token_for: str,
        http: ManagedHTTPClient,
    ) -> None:
        self._keep_alive_timeout: int = max(10, min(int(keep_alive_timeout), 600))
        self._heartbeat: int = min(self._keep_alive_timeout, 25) + 5
        self._last_keepalive: datetime.datetime | None = None
        self._keep_alive_task: asyncio.Task[None] | None = None

        self._session_id: str | None = None

        self._socket: aiohttp.ClientWebSocketResponse | None = None
        self._listen_task: asyncio.Task[None] | None = None

        self._ready: asyncio.Event = asyncio.Event()

        attempts: int | None = (
            0 if reconnect_attempts is None else None if reconnect_attempts is MISSING else reconnect_attempts
        )
        self._original_attempts = reconnect_attempts
        self._reconnect_attempts = attempts
        self._backoff: Backoff = Backoff(base=3, maximum_time=90)

        self.__subscription_cost: int = 0

        self._client: Client | None = client
        self._token_for: str = token_for
        self._http: ManagedHTTPClient = http
        self._subscriptions: dict[str, _SubscriptionData] = {}

        self._connecting: bool = False
        self._closed: bool = False

        self._connection_tasks: set[asyncio.Task[None]] = set()

        msg = "Websocket %s is being used without a Client/Bot. Event dispatching is disabled for this websocket."
        if not client:
            logger.warning(msg, self)

    def __repr__(self) -> str:
        return f"EventsubWebsocket(session_id={self._session_id})"

    def __str__(self) -> str:
        return f"{self._session_id}"

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
        return self.subscription_count < 300

    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)

    async def connect(self, *, url: str | None = None, reconnect: bool = False, fail_once: bool = False) -> None:
        if self._closed or self._connecting:
            return

        self._connecting = True
        url_: str = url or f"{WSS}?keepalive_timeout_seconds={self._keep_alive_timeout}"

        self._ready.clear()

        retries: int | None = self._reconnect_attempts
        if retries == 0 and reconnect:
            logger.info("Websocket <%s> was closed unexepectedly, but is flagged as 'should not reconnect'.", self)
            return await self.close()

        if reconnect:
            # We have to ensure that the tokens we need for resubscribing have been recently refreshed as
            # we only have 10 seconds to subscribe after we receive the welcome message...
            await self._http._validated_event.wait()

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    new = await session.ws_connect(url_, heartbeat=self._heartbeat)
                    session.detach()
            except Exception as e:
                logger.debug("Failed to connect to eventsub websocket <%s>: %s.", self, e)

                if fail_once:
                    await self.close()
                    raise WebsocketConnectionException from e
            else:
                break

            if retries == 0:
                await self.close()

                raise WebsocketConnectionException(
                    "Failed to connect to eventsub websocket <%s> after %s retries. "
                    "Please attempt to reconnect or re-subscribe this eventsub connection.",
                    self,
                    self._reconnect_attempts,
                )

            if retries is not None:
                retries -= 1

            delay: float = self._backoff.calculate()
            logger.info('Websocket <%s> retrying to reconnect websocket connection in "%s" seconds.', self, delay)

            await asyncio.sleep(delay)

        if reconnect:
            await self.close(cleanup=False)

        self._socket = new

        if not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen())

        try:
            async with asyncio.timeout(10 + 1):
                await self._ready.wait()
        except TimeoutError:
            await self.close()

            raise WebsocketConnectionException(
                "Websocket <%s> did not receive a welcome message from Twitch within the allowed timeframe. "
                "Please attempt to reconnect or re-subscribe this eventsub connection.",
                self,
            )

        self._keep_alive_task = asyncio.create_task(self._process_keepalive())

        if reconnect:
            await self._resubscribe()

        self._connecting = False

    async def _resubscribe(self) -> None:
        assert self._session_id

        for identifier, sub in self._subscriptions.copy().items():
            sub["transport"]["session_id"] = self._session_id

            try:
                resp: SubscriptionResponse = await self._http.create_eventsub_subscription(**sub)
            except HTTPException as e:
                if e.status == 409:
                    # This should never happen here...
                    # But we may as well handle it in-case of edge cases instead of being noisy...

                    msg: str = "Disregarding. Websocket '%s' tried to resubscribe to subscription '%s' but failed with 409."
                    logger.debug(msg, self, identifier)
                    continue

                logger.error("Unable to resubscribe to subscription '%s' on websocket '%s': %s", identifier, self, e)
                continue

            for new in resp["data"]:
                self._subscriptions[new["id"]] = sub

            type_: str = sub["type"].value
            version: str = sub["version"]
            condition: Condition = sub["condition"]

            msg: str = "Websocket '%s' successfully resubscribed to subscription '%s:%s' after reconnect: %s"
            logger.debug(msg, self, type_, version, condition)

    async def _reconnect(self, url: str) -> None:
        socket: Websocket = Websocket(
            keep_alive_timeout=self._keep_alive_timeout,
            reconnect_attempts=self._original_attempts,
            client=self._client,
            token_for=self._token_for,
            http=self._http,
        )

        socket._subscriptions = self._subscriptions

        try:
            await socket.connect(url=url, reconnect=False, fail_once=True)
        except Exception:
            return await self.connect(reconnect=True)

        if self._client:
            self._client._websockets[self._token_for][socket.session_id] = socket  # type: ignore

        await self.close()

    def _create_connection_task(self) -> None:
        task = asyncio.create_task(self.connect(reconnect=True))
        self._connection_tasks.add(task)
        task.add_done_callback(self._connection_tasks.discard)

    async def _listen(self) -> None:
        assert self._socket

        while True:
            try:
                message: aiohttp.WSMessage = await self._socket.receive()
            except Exception:
                self._create_connection_task()
                break

            type_: aiohttp.WSMsgType = message.type
            if type_ in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING):
                logger.debug("Received close message [%s] on eventsub websocket: <%s>", self._socket.close_code, self)

                if self._socket.close_code == 4001:
                    logger.critical(
                        "Websocket <%s> attempted to send an outgoing message to Twitch. "
                        "Twitch prohibits sending outgoing messages to the server, this will result in a disconnect. "
                        "This websocket will NOT attempt to reconnect.",
                        self,
                    )
                    return await self.close()

                elif self._socket.close_code == 4003:
                    return await self.close()

                self._create_connection_task()
                break

            if type_ is not aiohttp.WSMsgType.TEXT:
                logger.debug("Received unknown message from eventsub websocket: <%s>", self)
                continue

            self._last_keepalive = datetime.datetime.now()

            try:
                data: WebsocketMessages = cast(WebsocketMessages, _from_json(message.data))
            except Exception:
                logger.warning("Unable to parse JSON in eventsub websocket: <%s>", self)
                continue

            metadata: MetaData = data["metadata"]
            message_type: MessageTypes = metadata["message_type"]

            if message_type == "session_welcome":
                welcome_data: WelcomeMessage = cast(WelcomeMessage, data)

                await self._process_welcome(welcome_data)

            elif message_type == "session_reconnect":
                logger.debug('Received "session_reconnect" message from eventsub websocket: <%s>', self)
                reconnect_data: ReconnectMessage = cast(ReconnectMessage, data)

                await self._process_reconnect(reconnect_data)

            elif message_type == "session_keepalive":
                logger.debug('Received "session_keepalive" message from eventsub websocket: <%s>', self)

            elif message_type == "revocation":
                logger.debug('Received "revocation" message from eventsub websocket: <%s>', self)

                revocation_data: RevocationMessage = cast(RevocationMessage, data)
                await self._process_revocation(revocation_data)

            elif message_type == "notification":
                logger.debug('Received "notification" message from eventsub websocket: <%s>. %s', self, data)
                notification_data: NotificationMessage = cast(NotificationMessage, data)

                try:
                    await self._process_notification(notification_data)
                except Exception as e:
                    msg = "Caught an unknown exception while proccessing a websocket 'notification' event:\n%s\n"
                    logger.critical(msg, str(e), exc_info=e)

            else:
                logger.warning("Received an unknown message type in eventsub websocket: <%s>", self)

    async def _process_keepalive(self) -> None:
        assert self._last_keepalive
        logger.debug("Started keep_alive task on eventsub websocket: <%s>", self)

        while True:
            await asyncio.sleep(self._keep_alive_timeout)
            now: datetime.datetime = datetime.datetime.now()

            if self._last_keepalive + datetime.timedelta(seconds=self._keep_alive_timeout + 5) < now:
                self._create_connection_task()
                return

    async def _process_welcome(self, data: WelcomeMessage) -> None:
        payload: WelcomePayload = data["payload"]
        new_id: str = payload["session"]["id"]

        if self._session_id:
            self._cleanup(closed=False)
            self._client._websockets[self._token_for] = {self.session_id: self}  # type: ignore

        self._session_id = new_id
        self._ready.set()

        assert self._listen_task

        self._listen_task.set_name(f"EventsubWebsocketListener: {self._session_id}")
        logger.info('Received "session_welcome" message from eventsub websocket: <%s>', self)

    async def _process_reconnect(self, data: ReconnectMessage) -> None:
        logger.info("Attempting to reconnect eventsub websocket due to a reconnect message from Twitch: <%s>", self)
        await self._reconnect(url=data["payload"]["session"]["reconnect_url"])

    async def _process_revocation(self, data: RevocationMessage) -> None:
        payload: SubscriptionRevoked = SubscriptionRevoked(data=data["payload"]["subscription"])

        if self._client:
            self._client.dispatch(event="subscription_revoked", payload=payload)

        self._subscriptions.pop(payload.id, None)

    async def _process_notification(self, data: NotificationMessage) -> None:
        sub_type = data["metadata"]["subscription_type"]
        event = _SUB_MAPPING.get(sub_type, sub_type.removeprefix("channel.")).replace(".", "_")

        try:
            payload_class = create_event_instance(sub_type, data, http=self._http)
        except ValueError:
            logger.warning("Websocket '%s' received an unhandled eventsub event: '%s'.", self, event)
            return

        if self._client:
            self._client.dispatch(event=event, payload=payload_class)

    def _cleanup(self, closed: bool = True) -> None:
        self._closed = closed

        if self._client:
            sockets = self._client._websockets.get(self._token_for, {})
            sockets.pop(self.session_id or "", None)

    async def close(self, cleanup: bool = True) -> None:
        if cleanup:
            self._cleanup()

        if self._keep_alive_task:
            try:
                self._keep_alive_task.cancel()
            except Exception:
                pass

        if self._listen_task:
            try:
                self._listen_task.cancel()
            except Exception:
                pass

        if self._socket:
            try:
                await self._socket.close()
            except Exception:
                pass

        self._keep_alive_task = None
        self._listen_task = None
        self._socket = None

        logger.debug("Successfully closed eventsub websocket: <%s>", self)
