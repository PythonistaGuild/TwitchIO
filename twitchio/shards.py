import typing

if typing.TYPE_CHECKING:
    from .websocket import Websocket


class ShardInfo:

    def __init__(self, **kwargs):
        self._websocket: Websocket = kwargs.get('websocket')

        self.number: int = kwargs.get('number')
        self.channels: list = kwargs.get('channels')
        self.ready: bool = False
