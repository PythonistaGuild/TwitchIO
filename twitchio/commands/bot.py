import asyncio
import inspect
import sys
from typing import Union

from .core import TwitchCommand
from ..websocket import WebsocketConnection


class TwitchBot(WebsocketConnection):

    def __init__(self, irc_token: str, api_token: str, *, prefix, nick: str, loop: asyncio.BaseEventLoop=None,
                 channels: Union[list, tuple]=None, **attrs):
        self.loop = loop or asyncio.get_event_loop()
        super().__init__(token=irc_token, api_token=api_token, initial_channels=channels,
                         loop=self.loop, nick=nick, **attrs)

        self.prefix = prefix

        self.listeners = {}
        self.extra_listeners = {}
        self.commands = {}
        self._aliases = {}

        self._init_methods()

    def _init_methods(self):
        commands = inspect.getmembers(self)

        for name, obj in commands:
            if name.startswith('event'):
                self.listeners[name] = obj

            if not isinstance(obj, TwitchCommand):
                continue

            if obj.name in self.commands:
                print(f'Failed to load command <{obj.name}> a command with that name/alias already exists',
                      file=sys.stderr)
                continue

            if not inspect.iscoroutinefunction(obj.callback):
                print(f'Failed to load command <{obj.name}>. Commands must coroutines.', file=sys.stderr)

            self.commands[obj.name] = obj

            if not obj.aliases:
                continue

            for alias in obj.aliases:
                if alias in self.commands:
                    print(f'Failed to load command <{obj.name}>, a command with that name/alias already exists.',
                          file=sys.stderr)
                    del self.commands[obj.name]
                    continue

                self._aliases[alias] = obj.name

    def run(self):
        """A blocking call the initializes the IRC Bot event loop.

        This should be the last function to be called.

        .. warning::
            You do not need to use this function unless are accessing the IRC Endpoints.
        .. warning::
            You do not use this function if you are using :meth:`start`
        """
        loop = self.loop or asyncio.get_event_loop()

        loop.run_until_complete(self._connect())

        try:
            loop.run_until_complete(self._listen())
        except KeyboardInterrupt:
            pass
        finally:
            self.teardown()

    async def start(self):
        """|coro|
        An asynchronous call which starts the IRC Bot event loop.

        This should only be used when integrating Twitch Bots with Discords Bots.
        :meth:`run` should be used instead.
        """
        await self._connect()

        try:
            await self._listen()
        except KeyboardInterrupt:
            pass
        finally:
            self.teardown()

    def teardown(self):
        pass

    async def process_commands(self, message, channel, user):
        print('In command')
