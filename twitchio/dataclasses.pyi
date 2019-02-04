import datetime
from typing import *

from .abcs import Messageable
from .http import HTTPSession
from .websocket import WebsocketConnection
from twitchio.ext.commands.core import Command

class Message:
    __slots__ = ('_author', '_channel', '_raw_data', 'content', 'clean_content', '_tags', '_timestamp')

    def author(self) -> User: ...

    def channel(self) -> Channel: ...

    def raw_data(self) -> str: ...

    def tags(self) -> Optional[dict]: ...

    def timestamp(self) -> datetime.datetime.timestamp: ...


class Channel(Messageable):
    __slots__ = ('_channel', '_ws', '_http', '_echo', )

    def __init__(self, name: str, ws: WebsocketConnection, http: HTTPSession): ...

    def name(self) -> str: ...

    def _get_channel(self) -> Tuple[Callable[str], None]: ...

    def _get_method(self) -> str: ...

    def _get_socket(self) -> WebsocketConnection: ...

    async def get_stream(self) -> dict: ...

    async def get_chatters(self) -> NamedTuple:


class User:
    __slots__ = ('_name', '_channel', '_tags', 'display_name', '_id', 'type',
                 '_colour', 'subscriber', 'turbo', '_badges', '_ws', '_mod')

    def __init__(self, ws: WebsocketConnection, **attrs):
        self._name: Optional[str]
        self._channel: Union[Channel, str]
        self._tags: Optional[dict]
        self._ws: WebsocketConnection
        self.display_name: str
        self._id: int
        self.type: str
        self._colour: Optional[str]
        self.subscriber: Optional[str]
        self.turbo: Optional[str]
        self._badges: Optional[dict]
        self._mod: int

    def name(self) -> str: ...

    def id(self) -> int: ...

    def channel(self) -> Channel: ...

    def colour(self) -> Optional[str]: ...

    def color(self) -> Optional[Callable[str]]: ...

    def is_turbo(self) -> bool: ...

    def is_subscriber(self) -> bool: ...

    def badges(self) -> str: ...

    def tags(self) -> dict: ...

    def is_mod(self) -> bool: ...

class Context(Messageable):
    def __init__(self, message: Message, channel: Channel, user: User, **attrs):
        self.message: Message = message
        self.channel: Channel = channel
        self.content: str = message.content
        self.author: User = user
        self.prefix: Optional[str] = attrs.get('prefix', None)

        self._ws: WebsocketConnection = self.channel._ws

        self.command: Optional[Command] = attrs.get('Command', None)
        self.args: Optional[tuple] = attrs.get('args', None)
        self.kwargs: Optional[dict] = attrs.get('kwargs', None)

    def _get_channel(self) -> Tuple[Callable[str], None]: ...

    def _get_method(self) -> str: ...

    def _get_socket(self) -> WebsocketConnection: ...

    async def get_stream(self) -> dict: ...

    async def get_chatters(self) -> dict: ...