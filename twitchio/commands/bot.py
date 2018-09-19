import asyncio
import inspect
import sys
import traceback

from typing import Union

from .core import TwitchCommand
from .errors import TwitchIOCommandError, TwitchCommandNotFound
from .stringparser import StringParser
from ..dataclasses import Context
from ..errors import ClientError
from ..websocket import WebsocketConnection


class TwitchBot(WebsocketConnection):

    def __init__(self, irc_token: str, api_token: str, *, prefix: Union[list, tuple, str],
                 nick: str, loop: asyncio.BaseEventLoop=None, channels: Union[list, tuple]=None, **attrs):
        self.loop = loop or asyncio.get_event_loop()
        super().__init__(token=irc_token, api_token=api_token, initial_channels=channels,
                         loop=self.loop, nick=nick, **attrs)

        self.loop.create_task(self.prefix_setter(prefix))

        self.listeners = {}
        self.extra_listeners = {}
        self.commands = {}
        self._aliases = {}
        self.prefixes = None

        self._init_methods()

    def _init_methods(self):
        commands = inspect.getmembers(self)

        for name, obj in commands:
            if name.startswith('event_'):
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

    async def prefix_setter(self, item):
        if inspect.iscoroutinefunction(item):
            item = await item()
        elif callable(item):
            item = item()

        if isinstance(item, (list, tuple)):
            self.prefixes = item
        elif isinstance(item, str):
            self.prefixes = [item]
        else:
            raise ClientError('Invalid prefix provided. A list, tuple, str or callable returning either should be used.')

    async def _get_prefixes(self, message):
        prefix = ret = self.prefixes
        if callable(prefix):
            ret = prefix(self, message.content)
            if inspect.isawaitable(ret):
                ret = await ret

        if isinstance(ret, (list, tuple)):
            ret = [p for p in ret if p]

        if isinstance(ret, str):
            ret = [ret]

        if not ret:
            raise ClientError('Invalid prefix provided.')

        return ret

    async def get_prefix(self, message):
        prefixes = await self._get_prefixes(message)

        prefix = None
        content = message.content

        for pre in prefixes:
            if content.startswith(pre):
                prefix = pre
                break

        return prefix

    async def get_context(self, message, cls=None):
        prefix = await self.get_prefix(message)

        if not cls:
            cls = Context

        ctx = cls(message=message, channel=message.channel, user=message.author, prefix=prefix)
        return ctx

    # async def process_parameters(self, message, channel, user, parsed, prefix):
        # message.clean_content = ' '.join(parsed.values())
        # context = Context(message=message, channel=channel, user=user, prefix=prefix)

        # return context

    async def process_commands(self, message, ctx=None):
        if ctx is None:
            try:
                ctx = await self.get_context(message)
            except Exception as e:
                return await self.event_error(message.raw_data, e)

        if not ctx.prefix:
            return

        content = message.content
        content = content[len(ctx.prefix)::].lstrip(' ')
        parsed = StringParser().process_string(content)

        message.clean_content = ' '.join(parsed.values())

        try:
            command = parsed.pop(0)
        except KeyError:
            return

        try:
            command = self._aliases[command]
        except KeyError:
            pass

        try:
            if command not in self.commands:
                if not command:
                    return
                raise TwitchCommandNotFound(f'<{command}> was not found.')
            else:
                command = self.commands[command]
        except Exception as e:
            ctx.command = None
            return await self.event_command_error(ctx, e)
        else:
            ctx.command = command
            ctx.args, ctx.kwargs = await command.parse_args(parsed)

        try:
            await ctx.command.callback(self, ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            await self.event_command_error(ctx, e)

    async def event_command_error(self, ctx, exception):

        print('Ignoring exception in command: {0}:'.format(exception), file=sys.stderr)
        traceback.print_exc()
