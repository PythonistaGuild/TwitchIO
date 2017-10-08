from twitchio.client import *


class Bot(Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)