from twitchio.client import *
from twitchio.errors import *


class TwitchBot(Client):
    # todo

    def __init__(self, prefix: (callable, list, tuple), *args, **kwargs):
        super().__init__(*args, **kwargs, prefix=prefix, _bot=self)

        self.prefixes = prefix
        self.commands = {}

    async def command(self):
        pass

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

    async def process_commands(self, message):

        prefixes = await self.get_prefix(message)

        if not isinstance(prefixes, (list, tuple)):
            raise ClientError('Invalid prefix provided. Prefix must be a List, Tuple or String.')

        prefix = None
        msg = message.content

        for pre in prefixes:
            if msg.startswith(pre):
                prefix = pre

        if not prefix:
            return



















