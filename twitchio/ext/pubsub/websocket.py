import asyncio
import logging
from itertools import groupby
import time
from typing import Optional, List

import aiohttp
from twitchio import Client
from .topics import Topic
from . import models

try:
    import ujson as json
except:
    import json

logger = logging.getLogger("twitchio.ext.pubsub.websocket")

class PubSubWebsocket:
    __slots__ = "session", "topics", "client", "connection", "_latency", "timeout", "_task", "_poll"
    ENDPOINT = "wss://pubsub-edge.twitch.tv"

    def __init__(self, client: Client):
        self.session = None
        self.connection: aiohttp.ClientWebSocketResponse = None
        self.topics: List[Topic] = []
        self.client = client
        self._latency = None
        self.timeout = asyncio.Event(loop=self.client.loop)

    @property
    def latency(self) -> Optional[float]:
        return self._latency

    async def connect(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

        self.connection = await self.session.ws_connect(self.ENDPOINT)
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
        await self.connect()

    async def _send_initial_topics(self):
        await self._send_topics(self.topics)

    async def _send_topics(self, topics: List[Topic]):
        for tok, _topics in groupby(topics, key=lambda val: val.token):
            payload = {
                "type": "LISTEN",
                "data": {
                    "topics": [x.present for x in _topics],
                    "auth_token": tok
                }
            }
            await self.send(payload)

    async def subscribe_topic(self, topics: List[Topic]):
        if len(self.topics) + len(topics) > 50:
            raise ValueError("Cannot have more than 50 topics on one websocket")

        self.topics += topics
        if not self.connection or self.connection.closed:
            return

        await self._send_topics(topics)

    async def poll(self):
        while not self.connection.closed:
            data = await self.connection.receive_json(loads=json.loads)
            handle = getattr(self, "handle_"+data['type'].lower().replace("-", "_"), None)
            if handle:
                self.client.loop.create_task(handle(data))
            else:
                print(data)
                logger.debug(f"Pubsub event referencing unknown event '{data['type']}'. Discarding")

    async def ping_pong(self):
        while self.connection and not self.connection.closed:
            await asyncio.sleep(240)
            self.timeout.clear()
            await self.send({"type": "PING"})
            t = time.time()
            try:
                await asyncio.wait_for(self.timeout.wait(), 10)
            except asyncio.TimeoutError:
                await asyncio.shield(self.reconnect()) # we're going to get cancelled, so shield the coro
            else:
                self._latency = time.time() - t

    async def send(self, data: dict):
        data = json.dumps(data)
        await self.connection.send_str(data)

    async def handle_pong(self, msg: dict):
        self.timeout.set()

    async def handle_message(self, message):
        message['data']['message'] = json.loads(message['data']['message'])
        msg = models.PubSubMessage(self.client, message['data']['topic'], message['data']['message'])
        self.client.run_event("pubsub_message", msg) # generic one

        self.client.run_event(*models.create_message(self.client, message))

    async def handle_reward_redeem(self, message):
        msg = models.PubSubChannelPointsMessage(self.client, message['data'])
        self.client.run_event("pubsub_message", msg) # generic one
        self.client.run_event("pubsub_channel_points", msg)
