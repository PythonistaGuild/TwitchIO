from twitchio.client import *
from twitchio.errors import *
from twitchio.dataclasses import Context
from .errors import *
from .stringparser import StringParser
from .command import Command


class TwitchBot(Client):
    # todo

    def __init__(self, prefix: (callable, list, tuple), *args, **kwargs):
        super().__init__(*args, **kwargs, prefix=prefix, _bot=self)

        self.prefixes = prefix
        self.commands = {}
        self.get_commands()

    def get_commands(self):
        coms = inspect.getmembers(self)

        for name, func in coms:
            if isinstance(func, Command):
                self.commands[name] = func

    async def get_prefix(self, message):
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

    async def get_context(self, message, channel, user, command, parsed):

        args, kwargs = await command.parse_args(parsed)
        context = Context(message=message, channel=channel, user=user, Command=command, args=args, kwargs=kwargs)

        return context

    async def event_command_error(self, ctx, exception):

        print('Ignoring exception: {0} in command: {1}:'.format(exception, ctx.command.name), file=sys.stderr)
        traceback.print_exc()

    async def process_commands(self, message, channel, user):

        prefixes = await self.get_prefix(message)

        if not isinstance(prefixes, (list, tuple)):
            raise TwitchInvalidPrefix(type(prefixes))

        prefix = None
        msg = message.content

        for pre in prefixes:
            if msg.startswith(pre):
                prefix = pre

        if not prefix:
            return

        msg = msg.strip(prefix)
        parsed = StringParser().process_string(msg)
        command = parsed.pop(0)

        if command not in self.commands:
            if not command:
                return
            raise TwitchCommandNotFound(command)
        else:
            command = self.commands[command]

        try:
            ctx = await self.get_context(message, channel, user, command, parsed)
            await ctx.command.func(self, ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            await self.event_error(e.__class__.__name__)

        # TODO Proper command invocation and error handling













