from typing import List, Optional

from twitchio import Client
from .websocket import PubSubWebsocket
from .topics import Topic
from . import models

__all__ = "PubSubPool",

class PubSubPool:
    def __init__(self, client: Client, *, max_pool_size=10, max_connection_topics=50, mode="group"):
        self.client = client
        self._pool: List[PubSubWebsocket] = []
        self.map = {}
        self._mode = mode
        self._max_size = max_pool_size
        self._max_connection_topics = max_connection_topics

    async def subscribe_topics(self, topics: List[Topic]):
        node = self._find_node(topics)
        if node is None:
            node = PubSubWebsocket(self.client, max_topics=self._max_connection_topics)
            await node.connect()

        await node.subscribe_topic(topics)

    async def unsubscribe_topics(self, topics: List[Topic]):
        ... # todo

    def _find_node(self, topics: List[Topic]) -> Optional[PubSubWebsocket]:
        if self._mode == "group":
            for p in self._pool:
                if len(p.max_topics) + len(topics) <= p.max_topics:
                    return p

            if len(self._pool) < self._max_size:
                return None
            else:
                raise models.PoolFull(f"The pubsub pool has reached maximum topics. Unable to allocate a group of {len(topics)} topics.")

        else:
            raise ValueError("group is the only supported mode.")
