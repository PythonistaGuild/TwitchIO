"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from itertools import groupby
from typing import Optional, List, TYPE_CHECKING

import aiohttp

from twitchio import Client
from .topics import Topic
from . import models

if TYPE_CHECKING:
    from .pool import PubSubPool

try:
    import ujson as json
except:
    import json


logger = logging.getLogger("twitchio.ext.pubsub.websocket")


__all__ = ("PubSubWebsocket",)


class PubSubWebsocket:
    __slots__ = (
        "session",
        "topics",
        "pool",
        "client",
        "connection",
        "_latency",
        "timeout",
        "_task",
        "_poll",
        "max_topics",
        "_closing",
    )

    ENDPOINT = "wss://pubsub-edge.twitch.tv"

    def __init__(self, client: Client, pool: PubSubPool, *, max_topics=50):
        self.max_topics = max_topics
        self.session = None
        self.connection: Optional[aiohttp.ClientWebSocketResponse] = None
        self.topics: List[Topic] = []
        self.pool = pool
        self.client = client
        self._latency = None
        self._closing = False
        self.timeout = asyncio.Event()

    @property
    def latency(self) -> Optional[float]:
        return self._latency

    async def connect(self):
        self.connection = None
        if self.session is None:
            self.session = aiohttp.ClientSession()

        logger.debug(f"Websocket connecting to {self.ENDPOINT}")
        backoff = 2
        for attempt in range(5):
            try:
                self.connection = await self.session.ws_connect(self.ENDPOINT)
                break
            except aiohttp.ClientConnectionError:
                logger.warning(f"Failed to connect to pubsub edge. Retrying in {backoff} seconds (attempt {attempt}/5)")
                await asyncio.sleep(backoff)
                backoff **= 2

        if not self.connection:
            raise models.ConnectionFailure("Failed to connect to pubsub edge")

        self._task = self.client.loop.create_task(self.ping_pong())
        self._poll = self.client.loop.create_task(self.poll())
        await self._send_initial_topics()

    async def disconnect(self):
        if not self.session or not self.connection or self.connection.closed:
            return

        await self.connection.close(code=1000)
        self._task.cancel()
        self._poll.cancel()

    async def reconnect(self):
        await self.disconnect()
        await self.pool._process_reconnect_hook(self)
        await self.connect()

    async def _send_initial_topics(self):
        await self._send_topics(self.topics)

    async def _send_topics(self, topics: List[Topic], type="LISTEN"):
        for tok, _topics in groupby(topics, key=lambda val: val.token):
            nonce = ("%032x" % uuid.uuid4().int)[:8]

            payload = {
                "type": type,
                "nonce": nonce,
                "data": {"topics": [x._present_set_nonce(nonce) for x in _topics], "auth_token": tok},
            }
            logger.debug(f"Sending {type} payload with nonce '{nonce}': {payload}")
            await self.send(payload)

    async def subscribe_topics(self, topics: List[Topic]):
        if len(self.topics) + len(topics) > self.max_topics:
            raise ValueError(f"Cannot have more than {self.max_topics} topics on one websocket")

        self.topics += topics
        if not self.connection or self.connection.closed:
            return

        await self._send_topics(topics)

    async def unsubscribe_topic(self, topics: List[Topic]):
        if any(t not in self.topics for t in topics):
            raise ValueError("Topics were given that have not been subscribed to")

        await self._send_topics(topics, type="UNLISTEN")
        for t in topics:
            self.topics.remove(t)

    async def poll(self):
        while not self.connection.closed:
            data = await self.connection.receive_json(loads=json.loads)

            handle = getattr(self, "handle_" + data["type"].lower().replace("-", "_"), None)
            if handle:
                self.client.loop.create_task(handle(data), name=f"pubsub-handle-event: {data['type']}")
            else:
                print(data)
                logger.debug(f"Pubsub event referencing unknown event '{data['type']}'. Discarding")

        if not self._closing:
            logger.warning("Unexpected disconnect from pubsub edge! Attempting to reconnect")
            self._task.cancel()
            await self.connect()

    async def ping_pong(self):
        while self.connection and not self.connection.closed:
            await asyncio.sleep(240)
            self.timeout.clear()
            await self.send({"type": "PING"})
            t = time.time()
            try:
                await asyncio.wait_for(self.timeout.wait(), 10)
            except asyncio.TimeoutError:
                await asyncio.shield(self.reconnect())  # we're going to get cancelled, so shield the coro
            else:
                self._latency = time.time() - t

    async def send(self, data: dict):
        data = json.dumps(data)
        await self.connection.send_str(data)

    async def handle_pong(self, _):
        self.timeout.set()
        self.client.run_event("pubsub_pong")

    async def handle_message(self, message: dict):
        message["data"]["message"] = json.loads(message["data"]["message"])
        msg = models.PubSubMessage(self.client, message["data"]["topic"], message["data"]["message"])
        self.client.run_event("pubsub_message", msg)  # generic one

        self.client.run_event(*models.create_message(self.client, message))

    async def handle_reward_redeem(self, message: dict):
        msg = models.PubSubChannelPointsMessage(self.client, message["data"])
        self.client.run_event("pubsub_message", msg)  # generic one
        self.client.run_event("pubsub_channel_points", msg)

    async def handle_response(self, message: dict):
        if message["error"]:
            logger.error(f"Received errored response for nonce {message['nonce']}: {message['error']}")
            self.client.run_event("pubsub_error", message)
            if message["error"] == "ERR_BADAUTH":
                nonce = message["nonce"]
                await self.pool._process_auth_fail(nonce, self)

        elif message["type"] == "RECONNECT":
            logger.warning("Received RECONNECT response from pubsub edge. Reconnecting")
            await asyncio.shield(self.reconnect())
        elif message["nonce"]:
            logger.debug(f"Received OK response for nonce {message['nonce']}")
            self.client.run_event("pubsub_nonce", message)

    async def handle_reconnect(self, message: dict):
        logger.warning("Received RECONNECT response from pubsub edge. Reconnecting")
        await asyncio.shield(self.reconnect())
