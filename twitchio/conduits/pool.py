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

import logging
from types import MappingProxyType
from typing import TYPE_CHECKING, Self

from twitchio.eventsub.enums import ShardStatus, TransportMethod
from twitchio.types_.conduits import ShardData

from ..utils import parse_timestamp


if TYPE_CHECKING:
    import datetime
    from collections.abc import Mapping

    from ..client import Client
    from ..eventsub.websockets import Websocket
    from ..ext.commands import Bot
    from ..types_.conduits import ConduitData, ShardData, ShardTransport


logger: logging.Logger = logging.getLogger(__name__)


class ShardInfo:
    def __init__(self, data: ShardData) -> None:
        self._id: str = data["id"]
        self._status: ShardStatus = ShardStatus(data["status"])

        transport: ShardTransport = data["transport"]
        self._method: TransportMethod = TransportMethod(transport["method"])
        self._callback: str | None = transport.get("callback", None)
        self._session_id: str | None = transport.get("session_id", None)

        connected: str | None = transport.get("connected_at", None)
        disconnected: str | None = transport.get("disconnected_at", None)
        self._connected_at: datetime.datetime | None = parse_timestamp(connected) if connected else None
        self._disconnected_at: datetime.datetime | None = parse_timestamp(disconnected) if disconnected else None

    @property
    def id(self) -> str:
        return self._id

    @property
    def status(self) -> ShardStatus:
        return self._status

    @property
    def method(self) -> TransportMethod:
        return self._method

    @property
    def transport(self) -> TransportMethod:
        return self._method

    @property
    def callback(self) -> str | None:
        return self._callback

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def connected_at(self) -> datetime.datetime | None:
        return self._connected_at

    @property
    def disconnected_at(self) -> datetime.datetime | None:
        return self._disconnected_at


class Shard(ShardInfo):
    def __init__(self, data: ShardData, *, connection: Websocket | None = None) -> None:
        super().__init__(data)

        self._connection: Websocket | None = connection

    async def update_transport(self, method: TransportMethod) -> Self: ...


class Conduit:
    def __init__(self, *, data: ConduitData, pool: ConduitPool) -> None:
        self._pool: ConduitPool = pool

        self._id: str = data["id"]
        self._shard_count: int = data["shard_count"]

        self._shards: dict[str, Shard] = {}

    @property
    def id(self) -> str:
        return self._id

    async def update(self, shard_count: int, /) -> None: ...

    async def delete(self) -> None: ...

    async def fetch_shards(self) -> ...: ...

    async def update_shards(self, shards: list[Shard]) -> ...: ...


class ConduitPool:
    def __init__(self, *, client: Client | Bot) -> None:
        self._client: Client | Bot = client
        self._conduits: dict[str, Conduit] = {}

    @property
    def conduits(self) -> Mapping[str, Conduit]:
        return MappingProxyType(self._conduits)  # thanks lilly
