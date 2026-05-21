"""
MIT License

Copyright (c) 2017 - Present TwitchIO, PythonistaGuild

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
import logging
import time
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, ClassVar

import aiohttp
from aiohttp import WSMsgType

import twitchio

from ..backoff import Backoff
from ..eventsub.subscriptions import _SUB_MAPPING
from ..models.eventsub_ import WebsocketWelcome, create_event_instance
from ..utils import MISSING, PY_314, _from_json as JSON_LOADS


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Coroutine

    from ..authentication.tokens import ManagedHTTPClient
    from ..client import Client
    from ..types_.conduits import (
        NotificationMessage,
        RevocationMessage,
        WebsocketMessages,
        WelcomeMessage,
        WelcomePayload,
    )
    from ..types_.eventsub import _SubscriptionData


LOGGER: logging.Logger = logging.getLogger(__name__)
WSS: str = "wss://eventsub.wss.twitch.tv/ws"


class WebsocketClosed:
    # TODO: Docs...

    def __init__(self, *, socket: Websocket, reassociate: bool) -> None:
        self.socket: Websocket = socket
        self.reassociate = reassociate


class WelcomeCondition:
    TIMEOUT: ClassVar[int] = 10

    def __init__(self) -> None:
        self._event: asyncio.Event = asyncio.Event()
        self._previous: str | None = None
        self._session: str | None = None

    @property
    def completed(self) -> bool:
        return self._session is not None

    @property
    def session(self) -> str | None:
        return self._session

    @property
    def previous(self) -> str | None:
        return self._previous

    @asynccontextmanager
    async def wait(self) -> AsyncGenerator[None]:
        try:
            async with asyncio.timeout(self.TIMEOUT + 1):
                yield
                await self._event.wait()
        except TimeoutError:
            raise
        finally:
            self._event.clear()

    def set(self) -> None:
        self._event.set()

    def clear(self) -> None:
        self._event.clear()

    def reset(self) -> None:
        self._event.clear()
        self._previous = None
        self._session = None

    def complete(self, session: str, /) -> None:
        self._event.set()
        self._previous = self._session
        self._session = session


class Websocket:
    def __init__(
        self,
        *,
        keep_alive_timeout: float = 10,
        reconnect_attempts: int | None = MISSING,
        client: Client | None = None,
        shard_id: str | None = None,
        token_for: str | None = None,
        http: ManagedHTTPClient,
    ) -> None:
        self._client: Client | None = client
        self._http: ManagedHTTPClient = http
        self._listener: WebsocketListener = MISSING
        self._condition: WelcomeCondition = WelcomeCondition()
        self._backoff: Backoff = Backoff(base=3, maximum_time=90)

        self._shard_id = shard_id
        self._keep_alive_timeout: int = max(10, min(int(keep_alive_timeout), 600))
        self._attempts = float("inf") if reconnect_attempts is MISSING else reconnect_attempts or 0
        self._token_for: str | None = token_for
        self._subscriptions: dict[str, _SubscriptionData] = {}
        self._failed: bool = False

        self._closing: bool = False
        self._closed: bool = False

        self._reconnect_task: asyncio.Task[None] | None = None

        if not client:
            LOGGER.warning("Event dispatching is disabled for %s. 'Client' is missing.", repr(self))

    def __repr__(self) -> str:
        return (
            f"Websocket(conduit={self._shard_id is not None}, shard={self._shard_id}, session={self._condition.session!r})"
        )

    def __str__(self) -> str:
        return f"Websocket({self._condition.session!r})"

    @property
    def session_id(self) -> str | None:
        return self._condition.session

    @property
    def connected(self) -> bool:
        return bool(self._listener and not self._listener.transport.closed)

    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)

    @property
    def can_subscribe(self) -> bool:
        if self._shard_id is not None:
            return False

        return self.subscription_count < 300

    async def connect(self, *, url: str = MISSING) -> ...:
        gurl = url if url is not MISSING else f"{WSS}?keepalive_timeout_seconds={self._keep_alive_timeout}"

        if self._listener:
            await self._listener.close()

        listener = WebsocketListener(self)

        try:
            async with self._condition.wait():
                await listener.connect(gurl, keep_alive=self._keep_alive_timeout)
        except TimeoutError:
            # TODO ...
            return
        except Exception:
            # TODO ...
            return

        self._listener = listener

        msg = "Successfully resumed connection on %s." if url is not MISSING else "Sucessfully connected %s."
        LOGGER.info(msg, repr(self))

    def _reconnect(self, *, url: str = MISSING) -> None:
        if self._reconnect_task:
            return

        self._reconnect_task = asyncio.create_task(self.reconnect(url=url))

    async def _try_connect(self, url: str = MISSING, /) -> None:
        if not self._shard_id:
            return await self.connect(url=url)

        assert isinstance(self._client, twitchio.AutoClient)
        await self._client._associate_shards(shard_ids=[int(self._shard_id)])

    async def reconnect(self, *, url: str = MISSING) -> None:
        LOGGER.warning("Attempting to reconnect %s.", repr(self))

        attempts = self._attempts
        while attempts > 0:
            try:
                await self._try_connect(url)
                self._reconnect_task = None
                return
            except Exception as e:
                LOGGER.error("%s failed to connect: %s", repr(self), e, exc_info=e)

            attempts -= 1
            if attempts == 0:
                break

            delay = self._backoff.calculate()

            LOGGER.warning(
                "Reconnection failed for %s. Backing off... Retrying connection in %d seconds.", repr(self), delay
            )
            await asyncio.sleep(delay)

        LOGGER.warning("Reconnection attempts exhausted for %s. Destroying websocket.", repr(self))
        self._reconnect_task = None
        # TODO: Cleanup...

    async def close(self) -> None:
        if self._closing or self._closed:
            return

        self._closing = True

        if self._reconnect_task:
            try:
                self._reconnect_task.cancel()
            except:
                pass

        await self._listener.close()
        self._condition.reset()
        self._subscriptions = {}
        self._closed = True

    async def receive(self, data: WebsocketMessages) -> ...:
        LOGGER.debug("Processing received MESSAGE from Twitch on %s.", repr(self))

        match data:
            case {"metadata": {"message_type": "notification"}}:
                self._notification_message(data)
            case {"metadata": {"message_type": "session_welcome"}}:
                self._welcome_message(data)
            case {"metadata": {"message_type": "session_reconnect"}}:
                return await self.reconnect(url=data["payload"]["session"]["reconnect_url"])
            case {"metadata": {"message_type": "revocation"}}:
                revocation: RevocationMessage = data
                # TODO ...
            case {"metadata": {"message_type": "session_keepalive"}}:
                LOGGER.debug("Received SESSION_KEEPALIVE on %s: %s", repr(self), data)
            case _:
                LOGGER.debug("Received unhandled or unknown message on %s: %s", repr(self), data)

    def _welcome_message(self, data: WelcomeMessage) -> None:
        LOGGER.debug("Received SESSION_WELCOME on %s: %s", repr(self), data)

        welcome_payload: WelcomePayload = data["payload"]
        session = welcome_payload["session"]["id"]

        self._condition.complete(session)
        if not self._client:
            return

        event = WebsocketWelcome(welcome_payload["session"])
        self._client.dispatch("websocket_welcome", payload=event)

        if not self._token_for or self._shard_id:
            return

        sockets = self._client._websockets.get(self._token_for, {})
        sockets.pop(self._condition.previous or "", None)
        sockets[session] = self

    def _notification_message(self, data: NotificationMessage) -> None:
        LOGGER.debug("Received NOTIFICATION on %s: %s", repr(self), data)

        sub_type = data["metadata"]["subscription_type"]
        event = _SUB_MAPPING.get(sub_type, sub_type.removeprefix("channel.")).replace(".", "_")

        try:
            payload_class = create_event_instance(sub_type, data, http=self._http)
        except ValueError:
            LOGGER.warning("%s received an unhandled eventsub event: '%s'.", repr(self), event)
            return

        if self._client:
            self._client.dispatch(event=event, payload=payload_class)


class WebsocketListener:
    UNEXPECTED_ERROR: ClassVar[int] = 3009
    RECONNECT_CODES: ClassVar[tuple[int, ...]] = (1001, 1005, 1006, 1011, 1012, 1013)

    def __init__(self, sock: Websocket) -> None:
        self.sock = sock
        self.transport: aiohttp.ClientWebSocketResponse = MISSING

        self._listener_task: asyncio.Task[None] | None = None
        self._keep_alive_task: asyncio.Task[None] | None = None
        self._tasks: set[asyncio.Task[None]] = set()

        self._reconnecting: bool = False
        self._closed: bool = False
        self._closing: bool = False
        self._timeout: int = 30
        self._ack: float = time.time()

    def __repr__(self) -> str:
        return f"WebsocketListener<{self.sock}>"

    async def connect(self, url: str, /, *, keep_alive: int) -> ...:
        self._timeout = keep_alive

        sess = self.sock._http._session
        self.transport = await sess.ws_connect(url, heartbeat=10)
        self.listen()

    async def reconnect(self) -> None:
        if self._reconnecting or self._closed or self._closing:
            return

        self._reconnecting = True
        self.sock._reconnect()
        await self.close()

    def listen(self) -> None:
        if self._listener_task is not None:
            raise RuntimeError("Unable to start listener. A listener is already running.")

        if self._closed:
            raise RuntimeError("Cannot listen. %s is closed.", repr(self))

        LOGGER.debug("Starting listener task for %s.", repr(self))
        self._listener_task = asyncio.create_task(self._listener())
        self._keep_alive_task = asyncio.create_task(self._keep_alive())

    def _dispatch(self, coro: Coroutine[Any, Any, None]) -> None:
        LOGGER.debug("Dispatching message frame on %s.", repr(self))

        # NOTE: Typechecker sucks here...
        task = asyncio.create_task(coro, eager_start=True) if PY_314 else asyncio.create_task(coro)  # type: ignore
        self._tasks.add(task)  # type: ignore
        task.add_done_callback(self._tasks.discard)  # type: ignore

    async def _keep_alive(self) -> ...:
        LOGGER.debug("Starting keep alive on %s.", repr(self))

        while True:
            await asyncio.sleep(self._timeout)

            if self._ack + self._timeout <= time.time():
                LOGGER.debug("%s was not kept alive. Did not receive a message within timeout.", repr(self))
                return await self.reconnect()

    async def _listener(self) -> None:
        should_exit = False
        msg: aiohttp.WSMessage

        while not should_exit:
            try:
                msg = await self.transport.receive()
                self._ack: float = time.time()
            except (OSError, ConnectionResetError, aiohttp.ClientError) as e:
                LOGGER.error("Unexpected error occurred on %s. Attempting to reconnect.", repr(self))

                coro = self.handle_close(self.UNEXPECTED_ERROR, extra=str(e))
                self._dispatch(coro)
                break

            except asyncio.CancelledError:
                LOGGER.debug("Task cancelled while listening on %s.", repr(self))
                break

            except RuntimeError:
                LOGGER.error("Websocket transport for %s has too many listeners. Cannot recover or reconnect.", repr(self))
                await self.close()
                break

            if msg.type is WSMsgType.TEXT:
                LOGGER.debug("Received TEXT message frame on %s. Dispatching data.", repr(self))
                coro = self.handle_message(msg.data)

            elif msg.type is WSMsgType.BINARY:
                LOGGER.debug("Received BYTES message frame on %s. Attempting to convert and dispatch.", repr(self))

                try:
                    data = msg.data.decode("UTF-8")
                except Exception as e:
                    LOGGER.debug("Received BYTES on %s could not be decoded: %s. Disregarding.", repr(self), e)
                    continue

                coro = self.handle_message(data)

            elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED):
                LOGGER.debug("Received CLOSE message frame on %s. Dispatching for close or reconnect.", repr(self))

                coro = self.handle_close(msg.data)
                should_exit = True

            elif msg.type in (WSMsgType.CLOSING, WSMsgType.ERROR):
                LOGGER.debug("Received ERROR or CLOSING frame on %s. Dispatching for close or reconnect.", repr(self))

                coro = self.handle_close(self.UNEXPECTED_ERROR)
                should_exit = True

            else:
                LOGGER.debug("Received UNKNOWN or UNHANDLED message frame on %s. Disregarding: %s.", repr(self), msg)
                continue

            self._dispatch(coro)

    async def handle_close(self, code: int, *, extra: str | None = None) -> None:
        LOGGER.debug("Attempting to handle close frame on %s.", repr(self))

        if code == 1000:
            return self.cleanup()

        elif code in self.RECONNECT_CODES:
            LOGGER.debug("%s received close code: %s -> %s.", repr(self), code, extra or "...")
            return await self.reconnect()
        else:
            return await self.reconnect()

    async def handle_message(self, raw: str) -> None:
        LOGGER.debug("Attempting to handle data frame on %s.", repr(self))

        try:
            data = JSON_LOADS(raw)
        except Exception as e:
            LOGGER.warning(
                "Received invalid or corrupt data on %s. Further errors will result in reconnection: %s.", repr(self), e
            )
            return

        await self.sock.receive(data)

    def cleanup(self) -> None:
        if self._listener_task:
            try:
                self._listener_task.cancel()
            except Exception as e:
                LOGGER.debug(
                    "Unknown error occurred during listener task cancellation on %s. Disregarding: %s.", repr(self), e
                )

        if self._keep_alive_task:
            try:
                self._keep_alive_task.cancel()
            except Exception as e:
                LOGGER.debug(
                    "Unknown error occurred during keep-alive task cancellation on %s. Disregarding: %s.", repr(self), e
                )

    async def close(self) -> None:
        if self._closing or self._closed:
            return

        self._closing = True

        try:
            await self.transport.close(code=1000)
        except Exception as e:
            LOGGER.debug("Unknown exception during transport close on %s: %s", repr(self), e)

        self.cleanup()
        self._closed = True
        LOGGER.debug("Successfully closed %s.", repr(self))
