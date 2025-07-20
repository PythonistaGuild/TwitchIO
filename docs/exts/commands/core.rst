.. currentmodule:: twitchio

Commands
########

.. attributetable:: twitchio.ext.commands.Command

.. autoclass:: twitchio.ext.commands.Command()
    :members:

.. attributetable:: twitchio.ext.commands.Group

.. autoclass:: twitchio.ext.commands.Group()
    :members:


Reward Commands
###############

.. attributetable:: twitchio.ext.commands.RewardCommand

.. autoclass:: twitchio.ext.commands.RewardCommand()
    :members:
    :inherited-members:

.. attributetable:: twitchio.ext.commands.RewardStatus

.. autoclass:: twitchio.ext.commands.RewardStatus()
    :members:


Context
#######

.. attributetable:: twitchio.ext.commands.Context

.. autoclass:: twitchio.ext.commands.Context
    :members:

.. attributetable:: twitchio.ext.commands.ContextType

.. autoclass:: twitchio.ext.commands.ContextType()
    :members:


Decorators
##########

.. autofunction:: twitchio.ext.commands.command

.. autofunction:: twitchio.ext.commands.group

.. autofunction:: twitchio.ext.commands.reward_command

.. autofunction:: twitchio.ext.commands.cooldown(*, base: BaseCooldown, rate: int, per: float, key: Callable[[Any], Hashable] | Callable[[Any], Coroutine[Any, Any, Hashable]] | BucketType, **kwargs: ~typing.Any)


Guards
######

.. autofunction:: twitchio.ext.commands.guard(predicate: Callable[..., bool] | Callable[..., Coroutine[Any, Any, bool]])

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


Converters
##########

.. autoclass:: twitchio.ext.commands.Converter()
    :members:

.. autoclass:: twitchio.ext.commands.UserConverter()
    :members:

.. autoclass:: twitchio.ext.commands.ColourConverter()
    :members: