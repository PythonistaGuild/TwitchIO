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
        print('Hello World!')

    @hello.before_routine
    async def hello_before():
        print('I am run first!')


    hello.start()


**Routine with an error handler:**

This example shows a routine with a non-default error handler; by default all routines will stop on error.
You can change this behaviour by adding `stop_on_error=False` to your routine start function.


.. code-block:: python3

    from twitchio.ext import routines


    @routines.routine(minutes=10)
    async def hello(arg: str):
        raise RuntimeError

    @hello.error
    async def hello_on_error(error: Exception):
        print(f'Hello routine raised: {error}.')


    hello.start('World', stop_on_error=True)


**Routine which runs at a specific time:**

This routine will run at the same time everyday.
If a naive datetime is provided, your system local time is used.

The below example shows a routine which will first be ran on the **1st, June 2021 at 9:30am** system local time.
It will then be ran every 24 hours after the initial date, until stopped.


If the **date** has already passed, the routine will run at the next specified time.
For example: If today was the **2nd, June 2021 8:30am** and your datetime was scheduled to run on the
**1st, June 2021 at 9:30am**, your routine will first run on **2nd, June 2021 at 9:30am**.

In simpler terms, datetimes in the past only care about the time, not the date. This can be useful when scheduling
routines that don't need to be started on a specific date.


.. code-block:: python3

    import datetime

    from twitchio.ext import routines


    @routines.routine(time=datetime.datetime(year=2021, month=6, day=1, hour=9, minute=30))
    async def hello(arg: str):
        print(f'Hello {arg}!')


    hello.start('World')

API Reference
---------------------------

.. attributetable:: Routine

.. autoclass:: Routine
    :members:

.. autofunction:: twitchio.ext.routines.routine
