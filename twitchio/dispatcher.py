"""MIT License

Copyright (c) 2025 - Present Evie. P., Chillymosh and TwitchIO

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
import inspect
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from twitchio.utils import MISSING


LOGGER: logging.Logger = logging.getLogger("EventDispatcher")


type CB = Callable[..., Coroutine[Any, Any, None]]  # Listener callback
type ListenerMap = dict[str, set[CB]]


class EventDispatcher:
    def __init__(self) -> None:
        self._listeners: ListenerMap = defaultdict(set)
        self._waiters: ListenerMap = defaultdict(set)
        self.__tasks: set[asyncio.Task[None]] = set()

    def subscribe(self, *, name: str, listener: CB) -> None:
        name = name.lower()

        if not name.startswith("event_"):
            raise ValueError("Subscribed listeners names must start with 'event_'.")
        if not inspect.iscoroutinefunction(listener):
            raise TypeError("Subscribed listeners must be coroutine functions.")

        self._listeners[name].add(listener)

    def unsubscribe(self, listener: CB, /) -> CB | None:
        for listeners in self._listeners.values():
            if listener in listeners:
                listeners.remove(listener)
                return listener

    def publish(self, name: str, /, *, safe: bool = False, payload: Any = MISSING) -> None:
        name = name.lower()
        name = f"event_{name}"
        name = name if not safe else f"safe_{name}"

        listeners = self._listeners[name]
        if not listeners:
            return

        t = asyncio.create_task(self.dispatch(listeners, name=name, payload=payload), name="EventDispatcher:dispatch-task")
        self.__tasks.add(t)
        t.add_done_callback(self.__tasks.discard)

    async def dispatch(self, listeners: set[CB], *, name: str, payload: Any) -> None:
        name = f"EventDispatcher:{name}-task"
        tasks = [
            asyncio.create_task(self.wrap_event(listener=listener, payload=payload), name=f"{name}-{i}")
            for i, listener in enumerate(listeners)
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def wrap_event(self, *, listener: CB, payload: Any) -> None:
        try:
            coro = listener(payload) if payload is not MISSING else listener()
            await coro
        except Exception as e:
            print(e)
            # TODO event_error dispatching...
            ...
