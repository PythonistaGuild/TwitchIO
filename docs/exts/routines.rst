.. currentmodule:: twitchio.ext.routines

.. _routines-ref:


Routines Ext
===========================

Routines are helpers designed to make running async background tasks in TwitchIO easier.
Overall Routines are a QoL and are designed to be simple and easy to use.

Recipes
---------------------------

A simple routine.

.. code-block:: python3

    from twitchio.ext import routines


    @routines.routine(seconds=5.0, iterations=5)
    async def hello(arg: str):
        print(f'Hello {arg}!')

    hello.start('World')


API Reference
---------------------------

.. attributetable:: Routine

.. autoclass:: Routine
    :members:

.. autofunction:: twitchio.ext.routines.routine
