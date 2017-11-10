from .abcs import Messageable


class Message(Messageable):

    def __init__(self, **attrs):
        self._author = attrs.pop('author', None)
        self._channel = attrs.pop('channel', None)
        self._raw_data = attrs.pop('raw_data', None)
        self._writer = attrs.pop('_writer', None)
        self.content = attrs.pop('content', None)
        self._tags = attrs.pop('tags', None)
        try:
            self._timestamp = self.tags['sent-ts']
        except KeyError:
            self._timestamp = self.tags['tmi-sent-ts']

    def __repr__(self):
        return '<Message author={0.author} channel={0.channel}>'.format(self)

    async def _get_channel(self):
        return self.channel, None

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__

    @property
    def author(self):
        return self._author

    @property
    def channel(self):
        return self._channel

    @property
    def raw_data(self):
        return self._raw_data

    @property
    def tags(self):
        return self._tags

    @property
    def timestamp(self):
        return self._timestamp


class Channel(Messageable):

    def __init__(self, channel, _writer):
        self._channel = channel
        self._writer = _writer

    def __repr__(self):
        return self._channel

    @property
    def name(self):
        return self._channel

    async def _get_channel(self):
        return self.name, None

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__


class User(Messageable):

    def __init__(self, **attrs):
        self._name = attrs.pop('author', None)
        self._writer = attrs.pop('_writer')
        self._channel = attrs.pop('channel', None)
        self._tags = attrs.pop('tags', None)

        if not self._tags:
            self._tags = {'None': 'None'}

        self.display_name = self._tags.get('display-name', self._name)
        self._id = int(self._tags.get('user-id', 0))
        self.type = self._tags.get('user-type', 'Empty')
        self._colour = self._tags.get('color', None)
        self.subscriber = self._tags.get('subscriber', None)
        self.turbo = self._tags.get('turbo', None)
        self._badges = self._tags.get('badges', ',').split(',')

    def __repr__(self):
        return '<User name={0.name} channel={0._channel}>'.format(self)

    async def _get_channel(self):
        return self.channel, self._name

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def channel(self):
        return str(self._channel)

    @property
    def colour(self):
        return self._colour

    @property
    def color(self):
        return self.colour

    @property
    def is_turbo(self):
        return self.turbo

    @property
    def is_subscriber(self):
        return self.subscriber

    @property
    def badges(self):
        return self._badges

    @property
    def tags(self):
        return self._tags


class Context(Messageable):

    def __init__(self, message: Message, channel: Channel, user: User, **attrs):
        self.message = message
        self.channel = channel
        self.content = message.content
        self.author = user

        self._writer = self.channel._writer

        self.command = attrs.get('Command', None)
        self.args = attrs.get('args', None)
        self.kwargs = attrs.get('kwargs', None)

    async def _get_channel(self):
        return self.channel.name, None

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__