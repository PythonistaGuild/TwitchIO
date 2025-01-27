.. currentmodule:: twitchio

Commands
########

.. attributetable:: twitchio.ext.commands.Command

.. autoclass:: twitchio.ext.commands.Command
    :members:

.. attributetable:: twitchio.ext.commands.Group

.. autoclass:: twitchio.ext.commands.Group
    :members:

.. attributetable:: twitchio.ext.commands.Context

.. autoclass:: twitchio.ext.commands.Context
    :members:


Decorators
##########

.. autofunction:: twitchio.ext.commands.command

.. autofunction:: twitchio.ext.commands.group

.. autofunction:: twitchio.ext.commands.cooldown(*, base: BaseCooldown, rate: int, per: float, key: Callable[[Any], Hashable] | Callable[[Any], Coroutine[Any, Any, Hashable]] | BucketType, **kwargs: ~typing.Any)


Guards
######

.. autofunction:: twitchio.ext.commands.guard

.. autofunction:: twitchio.ext.commands.is_owner

.. autofunction:: twitchio.ext.commands.is_staff

.. autofunction:: twitchio.ext.commands.is_broadcaster

.. autofunction:: twitchio.ext.commands.is_moderator

.. autofunction:: twitchio.ext.commands.is_vip

.. autofunction:: twitchio.ext.commands.is_elevated


Cooldowns
#########

.. autoclass:: twitchio.ext.commands.BaseCooldown
    :members:

.. autoclass:: twitchio.ext.commands.Cooldown

.. autoclass:: twitchio.ext.commands.GCRACooldown

.. attributetable:: twitchio.ext.commands.BucketType()
.. autoclass:: twitchio.ext.commands.BucketType()
