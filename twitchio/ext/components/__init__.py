import inspect

from ..commands import Bot, command, collection


__all__ = ('Component', 'ComponentMeta')


class ComponentMeta:

    _bot: Bot = None

    __special_members__ = ('cog_event_error',
                           'cog_before_invoke',
                           'cog_after_invoke',
                           'cog_check',
                           'name',
                           'event',
                           'commands')

    def __init_subclass__(cls, **kwargs):

        for name, elem in inspect.getmembers(cls):
            if isinstance(elem, command):
                if name in cls.__special_members__:
                    raise RuntimeError(f'The method <{name}> is protected and cannot be used as an event or command.')

            elif isinstance(elem, command) and not command._parent:
                cls._bot.add_command(command)



class Component(ComponentMeta):
    pass