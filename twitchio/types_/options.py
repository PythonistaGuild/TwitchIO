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

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict


if TYPE_CHECKING:
    import aiohttp

    from ..authentication import Scopes
    from ..eventsub.subscriptions import SubscriptionPayload
    from ..web.utils import BaseAdapter


__all__ = ("AutoClientOptions", "ClientOptions", "WaitPredicateT")


class ClientOptions(TypedDict, total=False):
    redirect_uri: str | None
    scopes: Scopes | None
    session: aiohttp.ClientSession | None
    adapter: NotRequired[BaseAdapter]
    fetch_client_user: NotRequired[bool]


class AutoClientOptions(ClientOptions, total=False):
    conduit_id: str
    shard_ids: list[int]
    max_per_shard: int
    subscriptions: list[SubscriptionPayload]
    force_subscribe: bool
    force_scale: bool


WaitPredicateT = Callable[..., Coroutine[Any, Any, bool]]
