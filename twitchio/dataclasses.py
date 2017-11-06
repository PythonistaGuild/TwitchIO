from .abcs import Messageable


class Message(Messageable):

    def __init__(self, **attrs):
        self._author = attrs.pop('author', None)
        self._channel = attrs.pop('channel', None)
        self._raw_data = attrs.pop('raw_data', None)
        self._writer = attrs.pop('_writer', None)
        self.content = attrs.pop('content', None)
        self.tags = attrs.pop('tags', None)
        try:
            self.timestamp = self.tags['sent-ts']
        except:
            self.timestamp = self.tags['tmi-sent-ts']

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
        return str(self._channel)

    @property
    def raw_data(self):
        return self._raw_data


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
        self.tags = attrs.pop('tags', None)

        if not self.tags:
            self.tags = {'None': 'None'}

        self.display_name = self.tags.get('display-name', self._name)
        self.id = int(self.tags.get('user-id', 0))
        self.type = self.tags.get('user-type', 'Empty')
        self.colour = self.tags.get('color', None)
        self.subscriber = self.tags.get('subscriber', None)
        self.turbo = self.tags.get('turbo', None)
        self.badges = self.tags.get('badges', ',').split(',')

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
    def channel(self):
        return str(self._channel)

    @property
    def is_turbo(self):
        return self.turbo

    @property
    def is_subscriber(self):
        return self.subscriber


class Context(Messageable):

    def __init__(self, message: Message, channel: Channel, user: User, **attrs):
        self.message = message
        self.channel = channel
        self.user = user

        self.content = message.content
        self.author = self.user

        self._writer = self.channel._writer

        self.command = attrs.get('Command', None)
        self.args = attrs.get('args')
        self.kwargs = attrs.get('kwargs')

    async def _get_channel(self):
        return self.channel.name, None

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__