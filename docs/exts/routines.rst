.. currentmodule:: twitchio.ext.routines

.. _routines-ref:


Routines Ext
===========================

Routines are helpers designed to make running async background tasks in TwitchIO easier.
Overall Routines are a QoL and are designed to be simple and easy to use.

Recipes
---------------------------

**A simple routine:**

This routine will run every 5 seconds for 5 iterations.

.. code-block:: python3

    from twitchio.ext import routines


    @routines.routine(seconds=5.0, iterations=5)
    async def hello(arg: str):
        print(f'Hello {arg}!')


    hello.start('World')


**Routine with a before/after_routine hook:**

This routine will run a hook before starting, this can be useful for setting up state before the routine runs.
The `before_routine` hook will only be called once. Similarly `after_routine` will be called once at the end of the
routine.

.. code-block:: python3

    from twitchio.ext import routines


    @routines.routine(hours=1)
    async def hello():
        print('Hello World!)

    @hello.before_routine()
    async def hello_before():
        print('I am run first!')


    @hello.start()


API Reference
---------------------------

.. attributetable:: Routine

.. autoclass:: Routine
    :members:

.. autofunction:: twitchio.ext.routines.routine
