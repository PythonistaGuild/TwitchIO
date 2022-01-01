__all__ = ('Command', 'Collection')


class Command:

    def __init__(self, **attrs):
        self._callback = attrs.get('func')
        self._name = attrs.get('name')
        self._aliases = attrs.get('aliases', [])

        self._parent = attrs.get('parent')
        self._extras = []

    @classmethod
    def __call__(cls, func, /, *, name: str = None, aliases: list = []):
        name = name if name else func.__name__

        return cls(func=func, name=name, aliases=aliases)


class Collection(Command):

    def __init__(self, **attrs):
        self._callback = attrs.get('func')
        self._name = attrs.get('name')
        self._aliases = attrs.get('aliases', [])

        self._extras = []

    @classmethod
    def __call__(cls, func, /, *, name: str = None, aliases: list = []):
        name = name if name else func.__name__
        self_ = cls()

        return Collection(func=func, name=name, aliases=aliases, parent=self_)

    def command(self, *, name: str = None, aliases: list = []):
        name_ = name
        self_ = self

        def wrapped(func):
            name = name_ or func.__name__

            self_._extras.append(Command(func=func, name=name, aliases=aliases, parent=self_))
            return Command(func=func, name=name, aliases=aliases, parent=self_)
        return wrapped

    def collection(self, *, name: str = None, aliases: list = []):
        name_ = name
        self_ = self

        def wrapped(func):
            name = name_ or func.__name__

            self_._extras.append(Collection(func=func, name=name, aliases=aliases, parent=self_))
            return Collection(func=func, name=name, aliases=aliases,parent=self_)
        return wrapped


class Collections:

    def __init__(self):
        self.collections = []

    def append(self, param):
        self.collections.append(param)


class Listener:

    def __init__(self, **attrs):
        self.callback = attrs.get('func')
        self.name = attrs.get('name')
