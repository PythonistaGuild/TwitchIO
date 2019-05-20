from .abcs import Messageable


class PartialUser(Messageable):

    def __init__(self, websocket, **kwargs):
        self._name = kwargs.get('name')
        self._ws = websocket
        self._bot = kwargs.get('bot')
        self._channel = kwargs.get('channel', self._name)

    def __str__(self):
        return self._name

    def __repr__(self):
        return f'<PartialUser name: {self._name}, channel: {self._channel}>'

    def __eq__(self, other):
        return other.name == self.name and other.channel.name == other.channel.name

    def __hash__(self):
        return hash(self.name + self.channel.name)

    @property
    def name(self):
        return self._name

    @property
    def channel(self):
        return self._channel

    def _fetch_channel(self):
        return self._name   # Abstract method

    def _fetch_websocket(self):
        return self._ws    # Abstract method

    def _fetch_bot(self):
        return self._bot   # Abstract method


class User(Messageable):

    __slots__ = ('_name', '_channel', '_tags', '_ws', '_bot', 'id', '_turbo', '_sub', '_mod',
                 '_display_name', '_colour')

    def __init__(self, websocket, **kwargs):
        self._name = kwargs.get('name')
        self._channel = kwargs.get('channel', self._name)
        self._tags = kwargs.get('tags', None)
        self._ws = websocket
        self._bot = kwargs.get('bot')

        if not self._tags:
            return

        self.id = self._tags['user-id']
        self._turbo = self._tags['turbo']
        self._sub = self._tags['subscriber']
        self._mod = self._tags['mod']
        self._display_name = self._tags['display-name']
        self._colour = self._tags['color']

    def __str__(self):
        return self._name

    def __repr__(self):
        return f'<User name: {self._name}, channel: {self._channel}>'

    def __eq__(self, other):
        return other.name == self.name and other.channel.name == other.channel.name

    def __hash__(self):
        return hash(self.name + self.channel.name)

    def _fetch_channel(self):
        return self   # Abstract method

    def _fetch_websocket(self):
        return self._ws    # Abstract method

    def _fetch_bot(self):
        return self._bot   # Abstract method

    @property
    def channel(self):
        return self._channel

    @property
    def name(self):
        return self._name

    @property
    def display_name(self):
        return self._display_name

    @property
    def colour(self):
        """The users colour. Alias to color."""
        return self._colour

    @property
    def color(self):
        """The users color."""
        return self.colour

    @property
    def is_mod(self) -> bool:
        """A boolean indicating whether the User is a moderator of the current channel."""
        if self._mod == 1:
            return True
        if self.channel.name == self.display_name.lower():
            return True
        else:
            return False

    @property
    def is_turbo(self) -> bool:
        """A boolean indicating whether the User is Turbo.

        Could be None if no Tags were received.
        """
        return self._turbo

    @property
    def is_subscriber(self) -> bool:
        """A boolean indicating whether the User is a subscriber of the current channel.

        Could be None if no Tags were received.
        """
        return self._sub