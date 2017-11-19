from twitchio.client import *
from twitchio.errors import *
from twitchio.dataclasses import Context, Message
from .errors import *
from .stringparser import StringParser
from .command import Command


class TwitchBot(Client):
    # todo

    def __init__(self, prefix: (callable, list, tuple), *args, **kwargs):
        super().__init__(*args, **kwargs, prefix=prefix, _bot=self)

        self.prefixes = prefix
        self.commands = {}
        self._command_aliases = {}
        self._init_commands()

    def _init_commands(self):
        coms = inspect.getmembers(self)

        for name, func in coms:
            if isinstance(func, Command):
                self.commands[name] = func

                if isinstance(func.aliases, list):
                    for a in func.aliases:
                        if a in self.commands.keys() or a in self._command_aliases.keys():
                            raise ClientError('{0} is already a command.'.format(a))
                        else:
                            self._command_aliases[a] = name

        # TODO This is actually so bad...But for now as a base let's just roll with it :')

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

    async def process_parameters(self, message, channel, user, parsed, prefix):
        message.clean_content = ' '.join(parsed.values())
        context = Context(message=message, channel=channel, user=user, prefix=prefix)

        return context

    async def process_commands(self, message, channel, user):

        prefixes = await self.get_prefix(message)

        if not isinstance(prefixes, (list, tuple)):
            raise TwitchInvalidPrefix(type(prefixes))

        prefix = None
        msg = message.content

        for pre in prefixes:
            if msg.startswith(pre):
                prefix = pre
                break

        if not prefix:
            return

        msg = msg[len(prefix)::].lstrip(' ')
        parsed = StringParser().process_string(msg)

        try:
            ctx = await self.process_parameters(message, channel, user, parsed, prefix)
        except Exception as e:
            return await self.event_error(e.__class__.__name__)

        try:
            command = parsed.pop(0)
        except KeyError:
            return

        try:
            command = self._command_aliases[command]
        except KeyError:
            pass

        try:
            if command not in self.commands:
                if not command:
                    return
                raise TwitchCommandNotFound(command)
            else:
                command = self.commands[command]
        except Exception as e:
            ctx.command = None
            return await self.event_command_error(ctx, e)
        else:
            ctx.command = command
            ctx.args, ctx.kwargs = await command.parse_args(parsed)

        try:
            await ctx.command.func(self, ctx, *ctx.args, **ctx.kwargs)
        except Exception as e:
            await self.event_command_error(ctx, e)

    async def event_command_error(self, ctx, exception):

        print('Ignoring exception in command: {0}:'.format(exception), file=sys.stderr)
        traceback.print_exc()













