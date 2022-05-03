from __future__ import annotations

import asyncio
from typing import Coroutine, Dict, List, Optional, Union

from .commands import Command
from .components import Component
from twitchio import Client


class Bot(Client):

    def __init__(self, prefix: Union[list, callable, Coroutine], *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__commands: Dict[str, Component] = {}
        self.__components: Dict[str, Command] = {}

        self._unassigned_prefixes = prefix
        self._prefixes: List[str] = []

        self._in_context: bool = False

    async def __aenter__(self) -> Bot:
        self._in_context = True

        await self._prepare_prefixes()
        await super().__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._in_context = False

        await super().__aexit__(exc_type, exc_val, exc_tb)

    def run(self, token: Optional[str] = None) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._prepare_prefixes())

        super().run(token=token)

    async def start(self, token: Optional[str] = None) -> None:
        if not self._in_context:
            raise RuntimeError('"bot.start" can only be used within the bot async context manager.')

        await super().start(token=token)

    @property
    def prefixes(self) -> List[str]:
        return self._prefixes

    async def _prepare_prefixes(self) -> None:
        if asyncio.iscoroutine(self._unassigned_prefixes):
            prefixes = await self._unassigned_prefixes(self)

        elif callable(self._unassigned_prefixes):
            prefixes = self._unassigned_prefixes(self)

        else:
            prefixes = self._unassigned_prefixes

        if isinstance(prefixes, str):
            self._prefixes = [prefixes]

        elif isinstance(prefixes, list):
            if not all(isinstance(prefix, str) for prefix in prefixes):
                raise TypeError('prefix parameter must be a str, list of str or callable/coroutine returning either.')
            self._prefixes = prefixes

        else:
            raise TypeError('prefix parameter must be a str, list of str or callable/coroutine returning either.')

    async def add_component(self, component: Component) -> None:
        pass

    async def remove_component(self, component: Component) -> None:
        pass

    async def load_extension(self):
        pass

    async def unload_extension(self):
        pass

    async def reload_extension(self):
        pass







