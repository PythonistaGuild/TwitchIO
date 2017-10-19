from twitchio.client import *


class Bot(Client):
    # todo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands = {}
