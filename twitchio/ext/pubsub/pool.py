"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

import itertools
from typing import List, Optional

from twitchio import Client
from .websocket import PubSubWebsocket
from .topics import Topic
from . import models


__all__ = ("PubSubPool",)


class PubSubPool:
    """
    The pool that manages connections to the pubsub server, and handles distributing topics across the connections.

    Attributes
    -----------
    client: :class:`twitchio.Client`
        The client that the pool will dispatch events to.
    """

    def __init__(self, client: Client, *, max_pool_size=10, max_connection_topics=50, mode="group"):
        self.client = client
        self._pool: List[PubSubWebsocket] = []
        self._topics = {}
        self._mode = mode
        self._max_size = max_pool_size
        self._max_connection_topics = max_connection_topics

    async def subscribe_topics(self, topics: List[Topic]):
        """|coro|
        Subscribes to a list of topics.

        Parameters
        -----------
        topics: List[:class:`Topic`]
            The topics to subscribe to

        """
        node = self._find_node(topics)
        if node is None:
            node = PubSubWebsocket(self.client, max_topics=self._max_connection_topics)
            await node.connect()

        await node.subscribe_topics(topics)
        self._topics.update({t: node for t in topics})

    async def unsubscribe_topics(self, topics: List[Topic]):
        """|coro|
        Unsubscribes from a list of topics.

        Parameters
        -----------
        topics: List[:class:`Topic`]
            The topics to unsubscribe from

        """
        for node, vals in itertools.groupby(topics, lambda t: self._topics[t]):
            await node.unsubscribe_topic(vals)
            if not node.topics:
                await node.disconnect()
                self._pool.remove(node)

    def _find_node(self, topics: List[Topic]) -> Optional[PubSubWebsocket]:
        if self._mode != "group":
            raise ValueError("group is the only supported mode.")

        for p in self._pool:
            if len(p.max_topics) + len(topics) <= p.max_topics:
                return p

        if len(self._pool) < self._max_size:
            return None
        else:
            raise models.PoolFull(
                f"The pubsub pool has reached maximum topics. Unable to allocate a group of {len(topics)} topics."
            )
