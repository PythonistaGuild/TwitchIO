from __future__ import annotations
from typing import Optional, List, Callable

__all__ = ('Command', 'Collection')


class Command:

    def __init__(self, callback, *, name: str, aliases: Optional[List[str]] = None, parent: Optional[Collection] = None):
        self._callback = callback
        self._name = name
        self._aliases = aliases or []

        self._parent = parent

    @classmethod
    def __call__(cls, func, /, *, name: str = None, aliases: Optional[list] = None):
        name = name if name else func.__name__

        return cls(func, name=name, aliases=aliases)


class Collection(Command):

    def __init__(self, callback, name: str, aliases: Optional[List[str]] = None, parent: Optional[Collection] = None):
        super().__init__(
            callback,
            name=name,
            aliases=aliases,
            parent=parent
        )

        self._children = {}

    @classmethod
    def __call__(cls, func, /, *, name: str = None, aliases: Optional[list] = None):
        name = name if name else func.__name__
        self_ = cls(func, name)

        return Collection(func, name=name, aliases=aliases, parent=self_)

    def command(self, name: Optional[str] = None, *, aliases: Optional[list] = None):
        def wrapped(func):
            nonlocal self
            _name = name or func.__name__

            self._children[name] = cmd = Command(func, name=name, aliases=aliases, parent=self)
            return cmd

        return wrapped

    def collection(self, *, name: str = None, aliases: list = None):
        def wrapped(func):
            nonlocal self
            _name = name or func.__name__
            self._children[_name] = cmd = Collection(func, name=_name, aliases=aliases, parent=self)

            return cmd

        return wrapped


class Listener:

    def __init__(self, **attrs):
        self.callback = attrs.get('func')
        self.name = attrs.get('name')
