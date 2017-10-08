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
        self.tags = attrs.pop('tags', None)
        self._writer = attrs.pop('_writer')
        self._channel = attrs.pop('channel', None)

        if self.tags:
            self._display_name = self.tags['display-name']
            self._id = int(self.tags['user-id'])
            self._type = self.tags['user-type'] if self.tags['user-type'] else 'Standard User'
            self._colour = self.tags['color']
            self._subscriber = True if self.tags['subscriber'] == 1 else False
            self._turbo = True if self.tags['turbo'] == 1 else False
            self._badges = self.tags['badges'].split(',')

    def __repr__(self):
        return '<User name={0.name} id={0.id} channel={0._channel}>'.format(self)

    async def _get_channel(self):
        return self._channel, self._name

    async def _get_writer(self):
        return self._writer

    async def _get_method(self):
        return self.__class__.__name__

    @property
    def display_name(self):
        return self._display_name

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def user_type(self):
        return self._type

    @property
    def colour(self):
        return self._colour

    @property
    def color(self):
        return self._colour

    @property
    def is_subscriber(self):
        return self._subscriber

    @property
    def is_turbo(self):
        return self._turbo

    @property
    def badges(self):
        return self._badges

