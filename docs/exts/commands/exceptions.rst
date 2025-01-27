.. currentmodule:: twitchio.ext.commands

Exceptions
##########

Payloads
--------

.. attributetable:: twitchio.ext.commands.CommandErrorPayload

.. autoclass:: twitchio.ext.commands.CommandErrorPayload
    :members:


Exceptions
----------

.. autoexception:: twitchio.ext.commands.CommandError

.. autoexception:: twitchio.ext.commands.ComponentLoadError

.. autoexception:: twitchio.ext.commands.CommandInvokeError

.. autoexception:: twitchio.ext.commands.CommandHookError

.. autoexception:: twitchio.ext.commands.CommandNotFound

.. autoexception:: twitchio.ext.commands.CommandExistsError

.. autoexception:: twitchio.ext.commands.PrefixError

.. autoexception:: twitchio.ext.commands.InputError

.. autoexception:: twitchio.ext.commands.ArgumentError

.. autoexception:: twitchio.ext.commands.ConversionError

.. autoexception:: twitchio.ext.commands.BadArgument

.. autoexception:: twitchio.ext.commands.MissingRequiredArgument

.. autoexception:: twitchio.ext.commands.UnexpectedQuoteError

.. autoexception:: twitchio.ext.commands.InvalidEndOfQuotedStringError

.. autoexception:: twitchio.ext.commands.ExpectedClosingQuoteError

.. autoexception:: twitchio.ext.commands.GuardFailure

.. autoexception:: twitchio.ext.commands.CommandOnCooldown

.. autoexception:: twitchio.ext.commands.ModuleLoadFailure

.. autoexception:: twitchio.ext.commands.ModuleAlreadyLoadedError

.. autoexception:: twitchio.ext.commands.ModuleNotLoadedError

.. autoexception:: twitchio.ext.commands.NoEntryPointError


Exception Hierarchy
~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`CommandError`
        - :exc:`ComponentLoadError`
        - :exc:`CommandInvokeError`
            - :exc:`CommandHookError`
        - :exc:`CommandNotFound`
        - :exc:`CommandExistsError`
        - :exc:`PrefixError`
        - :exc:`InputError`
            - :exc:`ArgumentError`
                - :exc:`ConversionError`
                    - :exc:`BadArgument`
                - :exc:`MissingRequiredArgument`
                - :exc:`UnexpectedQuoteError`
                - :exc:`InvalidEndOfQuotedStringError`
                - :exc:`ExpectedClosingQuoteError`
        - :exc:`GuardFailure`
            - :exc:`CommandOnCooldown`
    - :exc:`ModuleError`
        - :exc:`ModuleLoadFailure`
        - :exc:`ModuleAlreadyLoadedError`
        - :exc:`ModuleNotLoadedError`
        - :exc:`NoEntryPointError`