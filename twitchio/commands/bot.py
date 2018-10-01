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


class TwitchBot:

    def __init__(self, irc_token: str, api_token: str=None, *, prefix: Union[list, tuple, str],
                 nick: str, loop: asyncio.BaseEventLoop=None, initial_channels: Union[list, tuple]=None,
                 client_id: str=None, **attrs):

        self.loop = loop or asyncio.get_event_loop()
        self._ws = WebsocketConnection(bot=self, irc_token=irc_token, api_token=api_token
                                       , initial_channels=initial_channels, loop=self.loop, nick=nick,
                                       client_id=client_id, **attrs)

        self.loop.create_task(self._prefix_setter(prefix))

        self.extra_listeners = {}
        self.commands = {}
        self._aliases = {}
        self.prefixes = None

        self._init_methods()

    def _init_methods(self):
        commands = inspect.getmembers(self)

        for name, obj in commands:
            if not isinstance(obj, TwitchCommand):
                continue

            obj.instance = self

            try:
                self.add_command(obj)
            except TwitchIOCommandError:
                traceback.print_exc()
                continue

    def add_command(self, command):
        if not isinstance(command, TwitchCommand):
            raise TypeError('Commands passed my be a subclass of TwitchCommand')
        elif command.name in self.commands:
            raise TwitchIOCommandError(f'Failed to load command <{command.name}>, a command with that name already exists')
        elif not inspect.iscoroutinefunction(command._callback):
            raise TwitchIOCommandError(f'Failed to load command <{command.name}>. Commands must be coroutines')

        self.commands[command.name] = command

        if not command.aliases:
            return

        for alias in command.aliases:
            if alias in self.commands:
                del self.commands[command.name]
                raise TwitchIOCommandError(
                    f'Failed to load command <{command.name}>, a command with that name/alias already exists.')

            self._aliases[alias] = command.name

    def run(self):
        """A blocking call the initializes the IRC Bot event loop.

        This should be the last function to be called.

        .. warning::
            You do not need to use this function unless are accessing the IRC Endpoints.
        .. warning::
            You do not use this function if you are using :meth:`.start`
        """
        loop = self.loop or asyncio.get_event_loop()

        loop.run_until_complete(self._ws._connect())

        try:
            loop.run_until_complete(self._ws._listen())
        except KeyboardInterrupt:
            pass
        finally:
            self.teardown()

    async def start(self):
        """|coro|

        An asynchronous call which starts the IRC Bot event loop.

        This should only be used when integrating Twitch Bots with Discords Bots.
        :meth:`.run` should be used instead.

        .. warning::
            Do not use this function if you are using :meth:`.run`
        """
        await self._ws._connect()

        try:
            await self._ws._listen()
        except KeyboardInterrupt:
            pass
        finally:
            self.teardown()

    def teardown(self):
        pass

    async def _prefix_setter(self, item):
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
        """|coro|

        A function which creates context with the given message.
        A custom context class can be passed.

        Parameters
        ------------
        message: :class:`.Message`
            The message to create context from.
        cls: Optional
            The optional custom class to create Context.

        Returns
        ---------
        :class:`.Context`
            The context created.
        """
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
                return await self.event_error(e, message.raw_data)

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

        ctx.command = command
        instance = ctx.command.instance

        try:
            ctx.args, ctx.kwargs = await command.parse_args(instance, parsed)

            if ctx.command._before_invoke:
                await ctx.command._before_invoke(instance, ctx)

            if instance:
                await ctx.command._callback(instance, ctx, *ctx.args, **ctx.kwargs)
            else:
                await ctx.command._callback(ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            if ctx.command.on_error:
                await ctx.command.on_error(instance, ctx, e)

            await self.event_command_error(ctx, e)

    async def event_command_error(self, ctx, error):
        """|coro|

        Event called when an error occurs during command invocation.

        Parameters
        ------------
        ctx: :class:`.Context`
            The command context.
        error: :class:`.Exception`
            The exception raised while trying to invoke the command.
        """
        print('Ignoring exception in command: {0}:'.format(error), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_mode(self, channel, user, status):
        """|coro|

        Event called when a MODE is received from Twitch.

        Parameters
        ------------
        channel: :class:`.Channel`
            Channel object relevant to the MODE event.
        user: :class:`.User`
            User object containing relevant information to the MODE.
        status: str
            The JTV status received by Twitch. Could be either o+ or o-.
            Indicates a moderation promotion/demotion to the :class:`.User`
        """
        pass

    async def event_userstate(self, user):
        """|coro|

        Event called when a USERSTATE is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the USERSTATE.
        """
        pass

    async def event_part(self, user):
        """|coro|

        Event called when a PART is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the PART.
        """
        pass

    async def event_join(self, user):
        """|coro|

        Event called when a JOIN is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the JOIN.
        """
        pass

    async def event_message(self, message):
        """|coro|

        Event called when a PRIVMSG is received from Twitch.

        Parameters
        ------------
        message: :class:`.Message`
            Message object containing relevant information.
        """
        await self.process_commands(message)

    async def event_error(self, error: Exception, data=None):
        """|coro|

        Event called when an error occurs processing data.

        Parameters
        ------------
        error: Exception
            The exception raised.
        data: str
            The raw data received from Twitch. Depending on how this is called, this could be None.
        """
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_ready(self):
        """|coro|

        Event called when the Bot has logged in and is ready.
        """
        pass

    async def event_raw_data(self, data):
        """|coro|

        Event called with the raw data received by Twitch.

        Parameters
        ------------
        data: str
            The raw data received from Twitch.
        """
        pass

    def command(self, *, name: str=None, aliases: Union[list, tuple]=None, cls=None):
        """Decorator which registers a command with the bot.
        """
        if cls and not inspect.isclass(cls):
            raise TypeError(f'cls must be of type <class> not <{type(cls)}>')

        cls = cls or TwitchCommand

        def decorator(func):
            fname = name or func.__name__

            command = cls(name=fname, func=func, aliases=aliases, instance=None)
            self.add_command(command)
        return decorator

    def event(self, func):
        """Decorator which adds an event listener to the bot.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Events must be coroutines.')

        setattr(self, func.__name__, func)
        return func

    def add_listener(self, func, name: str=None):
        """Method which adds a coroutine as an extra listener.

        This can be used to add extra event listeners to the bot.

        Parameters
        ------------
        func: coro [Required]
            The coroutine to assign as a listener.
        name: str [Required]
            The event to register. E.g "event_message".
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Events must be coroutines.')

        name = name or func.__name__

        if name not in self.extra_listeners:
            self.extra_listeners[name] = [func]
        else:
            self.extra_listeners[name].append(func)

    def listen(self, event: str=None):
        """Decorator which adds a coroutine as a listener to an event.

        This can be used in place of :meth:`.event` or when more than one of the same event is required.

        Parameters
        ------------
        event: str
            The event to listen to in form of a string. E.g "event_message".

        Examples
        ----------
            @bot.event()
            async def event_message(message):
                print(message.content)

            @bot.listen("event_message")
            async def extra_message(message):
                print(message.content)
        """
        def wrapper(func):
            self.add_listener(func, event)

            return func
        return wrapper
