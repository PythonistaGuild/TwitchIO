import typing

if typing.TYPE_CHECKING:
    from .websocket import Websocket


class ShardInfo:

    def __init__(self, **kwargs):
        self._websocket: Websocket = kwargs.get('websocket')

        self._number: int = kwargs.get('number')
        self._channels: list = kwargs.get('channels')
        self._ready: bool = False

    @property
    def number(self) -> int:
        """Returns the Shard number."""
        return self._number

    @property
    def index(self) -> int:
        """An alias to :func:`number`."""
        return self._number

    @property
    def channels(self) -> list:
        """Returns the channels associated with the Shard."""
        return self._channels

    @property
    def ready(self) -> bool:
        """Returns a bool indicating whether the Shard is in a ready state."""
        return self._ready
