from .abcs import Messageable


class Context(Messageable):

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
        return self._channel

    @property
    def raw_data(self):
        return self._raw_data


class User(Messageable):

    def __init__(self, **attrs):
        self._name = attrs.pop('author', None)
        self._writer = attrs.pop('_writer')
        self._channel = attrs.pop('channel', None)
        tags = attrs.pop('tags', None)

        if not tags:
            return

        self.display_name = tags['display-name']
        self.id = int(tags['user-id'])
        self.type = tags['user-type'] if tags['user-type'] else 'Standard User'
        self.colour = tags['color']
        self.subscriber = tags['subscriber'] == 1
        self.turbo = tags['turbo'] == 1
        self.badges = tags['badges'].split(',')

    def __repr__(self):
        return '<User name={0.name} channel={0._channel}>'.format(self)

    async def _get_channel(self):
        return self._channel, self._name

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__

    @property
    def name(self):
        return self._name

    @property
    def channel(self):
        return self._channel
