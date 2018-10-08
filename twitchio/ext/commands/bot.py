import asyncio
import inspect
import sys
import threading
import traceback
import uuid

from typing import Union

from .core import TwitchCommand
from .errors import TwitchIOCommandError, TwitchCommandNotFound
from .stringparser import StringParser
from twitchio.client import TwitchClient
from twitchio.dataclasses import Context
from twitchio.errors import ClientError
from twitchio.webhook import TwitchWebhookServer
from twitchio.websocket import WebsocketConnection


class TwitchBot(TwitchClient):
    """
    .. note::

        To enable the webhook server, the webhook_server parameter must be True.
        A local_host, external_host and port must also be provided.

        An optional parameter `callback` may be passed. This should be the page Twitch sends data to.
        A long random string, such as hex, is advised e.g `2t389hth892t3h898hweiogtieo`
    """

    def __init__(self, irc_token: str, api_token: str=None, *, client_id: str=None, prefix: Union[list, tuple, str],
                 nick: str, loop: asyncio.BaseEventLoop=None, initial_channels: Union[list, tuple]=None,
                 webhook_server: bool=False, local_host: str=None, external_host: str=None, callback: str=None,
                 port: int=None, **attrs):

        self.loop = loop or asyncio.get_event_loop()
        super().__init__(loop=self.loop, client_id=client_id, **attrs)

        self._ws = WebsocketConnection(bot=self, loop=self.loop, http=self.http, irc_token=irc_token,
                                       nick=nick, initial_channels=initial_channels, **attrs)

        self._webhook_server = None
        if webhook_server:
            self._webhook_server = TwitchWebhookServer(bot=self,
                                                       local=local_host,
                                                       external=external_host,
                                                       callback=callback,
                                                       port=port)
            loop = asyncio.new_event_loop()
            thread = threading.Thread(target=self._webhook_server.run_server, args=(loop, ))
            thread.start()

        self.loop.create_task(self._prefix_setter(prefix))

        self.extra_listeners = {}
        self.commands = {}
        self._aliases = {}
        self.prefixes = None

        self._init_methods()

    def _init_methods(self):
        commands = inspect.getmembers(self)

        for _, obj in commands:
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
            raise TypeError('Commands passed my be a subclass of TwitchCommand.')
        elif command.name in self.commands:
            raise TwitchIOCommandError(f'Failed to load command <{command.name}>, a command with that name already exists')
        elif not inspect.iscoroutinefunction(command._callback):
            raise TwitchIOCommandError(f'Failed to load command <{command.name}>. Commands must be coroutines.')

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
        """A blocking call that initializes the IRC Bot event loop.

        This should be the last function to be called.

        .. warning::
            You do not need to use this function unless you are accessing the IRC Endpoints.
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

        This should only be used when integrating Twitch Bots with Discord Bots.
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

    async def webhook_subscribe(self, topic: str, callback: str=None):
        """|coro|

        Subscribe to WebHook topics.

        Parameters
        ------------
        topic: str [Required]
            The topic you would like to subscribe to.
        callback: str [Optional]
            The callback the subscription flow should use. If you are using the built-in server, you don't need
            to worry about this. The callback must be a full address. e.g http://twitch.io/callback

        Raises
        --------
        ClientError
            No callback was able to be used.

        Returns
        ---------
        response
            The response received from the POST request.

        Notes
        -------

        .. note::

            A list of topics can be found here: https://dev.twitch.tv/docs/api/webhooks-reference/
        """
        if not self._webhook_server and callback:
            raise ClientError('A valid callback is required to subscribe to webhook events.')

        if not callback:
            callback = f'{self._webhook_server.external}:{self._webhook_server.port}/{self._webhook_server.callback}'

        payload = {"hub.mode": "subscribe",
                   "hub.topic": topic,
                   "hub.callback": callback,
                   "hub.lease_seconds": 864000}

        async with self.http._session.post('https://api.twitch.tv/helix/webhooks/hub', data=payload) as resp:
            return resp

    async def event_webhook(self, data):
        """|coro|

        Event which is fired when a message from a Webhook subscription is received.

        Parameters
        ------------
        data: dict
            The webhook data as JSON.
        """
        pass

    async def event_raw_pubsub(self, data):
        """|coro|

        Event which fires when a PubSub subscription event is received.

        Parameters
        ------------
        data:
            The raw data received from the PubSub event.

        Notes
        -------
        .. note::

            No parsing is done on the JSON and thus the data will be raw.
            A new event which parses the JSON will be released at a later date.
        """
        pass

    async def event_pubsub(self, data):
        raise NotImplementedError

    async def pubsub_subscribe(self, token: str, *topics):
        """|coro|

        Method which sends a LISTEN event over PubSub. This subscribes you to the topics provided.

        Parameters
        ------------
        token: str [Required]
            The oAuth token to use to subscribe.
        \*topics: Union[str] [Required]
            The topics to subscribe to.

        Raises
        --------
        WSConnectionFailure
            The PubSub websocket failed to connect.
        ClientError
            You reached the maximum amount of PubSub connections/Subscriptions.

        Returns
        ---------
        nonce: str
            The nonce associated with this subscription. Useful for validating responses.
        """
        nonce = uuid.uuid4().hex

        connection = await self._ws._pubsub_pool.delegate(*topics)
        await connection.subscribe(token, nonce, *topics)

        return nonce

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

        Event called when an error occurs while processing data.

        Parameters
        ------------
        error: Exception
            The exception raised.
        data: str
            The raw data received from Twitch. Depending on how this is called, this could be None.

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_error(error, data):
                traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        """
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    async def event_ready(self):
        """|coro|

        Event called when the Bot has logged in and is ready.

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_ready():
                print(f'Logged into Twitch | {bot.nick}')
        """
        pass

    async def event_raw_data(self, data):
        """|coro|

        Event called with the raw data received by Twitch.

        Parameters
        ------------
        data: str
            The raw data received from Twitch.

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_raw_data(data):
                print(data)
        """
        pass

    def command(self, *, name: str=None, aliases: Union[list, tuple]=None, cls=None):
        """Decorator which registers a command on the bot.

        Commands must be coroutines.

        Parameters
        ------------
        name: str [Optional]
            The name of the command. By default if this is not supplied, the function name will be used.
        aliases: Union[list, tuple] [Optional]
            The command aliases. This must be a list or tuple.
        cls: class [Optional]
            The custom command class to override the default class. This must be similar to :class:`.Command`.
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

        Example
        ---------
        .. code:: py

            @bot.event
            async def event_raw_data(data):
                print(data)

            @bot.event
            async def event_message(message):
                print(message.content)
                await bot.process_commands(message)
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
        event: str [Optional]
            The event to listen to in the form of a string. E.g "event_message".

        Example
        ----------
        .. code:: py

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
