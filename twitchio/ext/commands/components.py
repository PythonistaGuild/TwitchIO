from typing import Dict

from .commands import Command

__all__ = ("Component",)


class Component:
    def __new__(cls, *args, **kwargs):
        new = super().__new__(cls)
        new.__dict__["__component_name__"] = cls.__name__
        # noinspection PyTypeHints
        new.__commands: dict[str, Command] = {}

        for name, value in cls.__dict__.items():

            if isinstance(value, Command):
                if name.startswith("component_"):
                    raise TypeError('Command callbacks must not start with "component_" or "bot".')

                value._component = new
                new.__commands[value._name] = value

        return new

    @property
    def name(self) -> str:
        # noinspection PyUnresolvedReferences
        return self.__component_name__

    @property
    def commands(self) -> dict[str, Command]:
        return self.__commands.copy()

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
