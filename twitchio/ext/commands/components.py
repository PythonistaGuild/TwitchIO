from typing import Dict

from .commands import Command


__all__ = ('Component', 'ComponentMeta')


class ComponentMeta(type):

    def __new__(mcs, name, bases, attrs, **kwargs):
        attrs['__component_name__'] = name

        cls = super().__new__(mcs, name, bases, attrs, **kwargs)

        for base in reversed(cls.__mro__):
            for name, value in base.__dict__.items():

                if isinstance(value, Command):
                    if name.startswith('component_'):
                        raise TypeError('Command callbacks must not start with "component_" or "bot".')

                    value._component = base
                    base._commands[value._name] = value

        return cls


class Component(metaclass=ComponentMeta):

    _commands: Dict[str, Command] = {}

    @property
    def name(self) -> str:
        # noinspection PyUnresolvedReferences
        return self.__component_name__

    @property
    def commands(self) -> dict[str, Command]:
        raise NotImplementedError

    @property
    def events(self) -> dict:
        raise NotImplementedError

    async def component_check(self) -> bool:
        pass

    async def component_on_load(self) -> None:
        pass

    async def component_on_unload(self) -> None:
        pass

    async def component_before_invoke(self) -> None:
        pass

    async def component_after_invoke(self) -> None:
        pass

    async def component_command_error(self) -> None:
        pass
