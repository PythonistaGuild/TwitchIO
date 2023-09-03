.. currentmodule:: twitchio.ext.commands

.. _commands-ref:

Commands Ext
===========================

The commands ext is meant purely for creating twitch chatbots. It gives you powerful tools, including dynamic loading/unloading/reloading
of modules, organization of code using Cogs, and of course, commands.

The base of this ext revolves around the :class:`Bot`. :class:`Bot` is a subclass of :class:`~twitchio.Client`, which means it has all the functionality
of :class:`~twitchio.Client`, while also adding on the features needed for command handling. 

.. note::
    Because :class:`Bot` is a subclass of :class:`~twitchio.Client`, you do not need to use :class:`~twitchio.Client` at all.
    All of the functionality you're looking for is contained within :class:`Bot`.
    The only exception for this rule is when using the :ref:`Eventsub Ext <eventsub_ref>`.

To set up your bot for commands, the first thing we'll do is create a :class:`Bot`.

.. code-block:: python

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!")

    bot.run()

:class:`Bot` has two required arguments, ``token`` and ``prefix``. ``token`` is the same as for :class:`~twitchio.Client`, 
and ``prefix`` is a new argument, specific to commands. You can pass many different things as a prefix, for example:

.. code-block:: python

    import twitchio
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!")

    bot = commands.Bot(token="...", prefix=("!", "?"))

    def prefix_callback(bot: commands.Bot, message: twitchio.Message) -> str:
        if message.channel.name == "iamtomahawkx":
            return "!"
        elif message.channel.name == "chillymosh":
            return "?"
        else:
            return ">>"
    
    bot = commands.Bot(token="...", prefix=prefix_callback)

    bot.run()

All of those methods are valid prefixes, you can even pass an async function if needed. For this demo, we'll stick to using ``!``.
We'll also be passing 3 initial channels to our bot, so that we can send commands right away on them:

.. code-block:: python

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    bot.run()
___

To create a command, we'll use the following code:

.. code-block:: python

    async def cookie(ctx: commands.Context) -> None:
        await ctx.send(f"{ctx.author.name} gets a cookie!")

Every command takes a ``ctx`` argument, which gives you information on the command, who called it, from what channel, etc.
You can read more about the ctx argument :ref:`Here <context_ref>`.

Once we've made our function, we can tie it into our bot like this:

.. code-block:: python

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command()
    async def cookie(ctx: commands.Context) -> None:
        await ctx.send(f"{ctx.author.name} gets a cookie!")
    
    bot.run()

And then we can use it like this:

.. image:: /images/commands_basic_1.png

We've made use of a decorator here to make the ``cookie`` function a command that will be called
whenever someone types ``!cookie`` in one of our twitch channels. But sometimes we'll want our function to be named something different
than our command, or we'll want aliases so that multiple things trigger our command. We can do that by passing arguments to the decorator, like so:

.. code-block:: python

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="cookie", aliases=("cookies", "biscuits"))
    async def cookie_command(ctx: commands.Context) -> None:
        await ctx.send(f"{ctx.author.name} gets a cookie!")
    
    bot.run()

Now our command can be triggered with any of ``!cookie``, ``!cookies``, or ``!biscuits``. But it `cannot` be triggered with ``!cookie_command``:

.. image:: /images/commands_basic_2.png

You may notice that if you try to run ``!cookie_command``, you get an error in your console about the command not being found. 
Don't worry, we'll hide that later, when we cover error handling.

___

Now let's say we want to take an argument for our command. We want to specify how many cookies the bot will give out.
Fortunately, twitchio has that functionality built right in! We can simply add an argument to our function, and the argument will be added.

.. code-block:: python

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="cookie", aliases=("cookies", "biscuits"))
    async def cookie_command(ctx: commands.Context, amount) -> None:
        await ctx.send(f"{ctx.author.name} gets {amount} cookie(s)!")
    
    bot.run()

.. image:: /images/commands_arguments_1.png

Now, you'll notice that I passed ``words?`` as the argument in the image, and the code handled it fine.
While it's good that it didn't error, we actually want it to error here, as our code should only take numbers!
Good news, twitchio's argument handling goes beyond simple positional arguments. We can use python's typehints to tell the parser to **only** accept integers:

.. code-block:: python

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="cookie", aliases=("cookies", "biscuits"))
    async def cookie_command(ctx: commands.Context, amount: int) -> None:
        await ctx.send(f"{ctx.author.name} gets {amount} cookie(s)!")
    
    bot.run()

.. image:: /images/commands_arguments_2.png

Good, the command didn't accept the word where the number should be. 
We've got a messy error in our console, that looks like this: 

.. code::

    twitchio.ext.commands.errors.ArgumentParsingFailed: Invalid argument parsed at `amount` in command `cookie`. Expected type <class 'int'> got <class 'str'>.

but we'll clean that up when we cover error handling.

Twitchio allows for many kinds of typehints to be used, including built in types like ``str`` (the default), ``int``, and ``bool``.
It also allows for some Twitchio models to be hinted. For instance, you can grab another user like this:

.. code-block:: python

    import twitchio
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="cookie", aliases=("cookies", "biscuits"))
    async def cookie_command(ctx: commands.Context, amount: int, user: twitchio.User) -> None:
        await ctx.send(f"{user.name} gets {amount} cookie(s)!")
    
    bot.run()

.. image:: /images/commands_arguments_3.png

Note that an error is raised for the last message, because "anfkednfowinoi" does not exist.

.. code-block::

    twitchio.ext.commands.errors.BadArgument: User 'anfkednfowinoi' was not found.

The built in models that you can use include:
- :class:`~twitchio.PartialChatter` - cache independent.
- :class:`~twitchio.Chatter` - dependent on cache, will fail if the user is not cached.
- :class:`~twitchio.PartialUser` - makes an API call, use :class:`~twitchio.PartialChatter` instead when possible.
- :class:`~twitchio.User` - makes an API call, use :class:`~twitchio.Chatter` instead when possible.
- :class:`~twitchio.Channel` - another channel that your bot has joined.
- :class:`~twithio.Clip` - takes a clip URL.

.. note::
    The :class:`~twitchio.User` / :class:`~twitchio.PartialUser` converters do make an API call, so they should only be used
    in cases where you need to ensure the user exists (as an error will be raised when they don't exist).
    For most usages of finding another user, you can simply use ``str`` or :class:`twitchio.PartialChatter`.

    Because of this downside, we'll be using :class:`~twitchio.PartialChatter` for the remainder of this walkthrough.

___

Now, let's say we want to have the option to pass a chatter, but we want it to be optional. If a chatter isn't passed, we use the author instead.
We can accomplish this through the use of Python's ``typing`` module:

.. code-block:: python

    import twitchio

    from typing import Optional
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="cookie", aliases=("cookies", "biscuits"))
    async def cookie_command(ctx: commands.Context, amount: int, user: Optional[twitchio.PartialChatter]) -> None:
        if user is None:
            user = ctx.author
        
        await ctx.send(f"{user.name} gets {amount} cookie(s)!")
    
    bot.run()

If you're on Python 3.10+, you could also structure it like this:

.. code-block:: python

    import twitchio

    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="cookie", aliases=("cookies", "biscuits"))
    async def cookie_command(ctx: commands.Context, amount: int, user: twitchio.PartialChatter | None) -> None:
        if user is None:
            user = ctx.author
        
        await ctx.send(f"{user.name} gets {amount} cookie(s)!")
    
    bot.run()

.. image:: /images/commands_arguments_4.png

NEXT: UNION PARSING

 
API Reference
--------------

Bot
++++
.. attributetable:: Bot

.. autoclass:: Bot
    :members:
    :inherited-members:

.. _context_ref:

Context
++++++++
.. attributetable:: Context

.. autoclass:: Context
    :members:
    :inherited-members:

Command
++++++++
.. attributetable:: Command

.. autoclass:: Command
    :members:
    :inherited-members:

Cog
++++
.. attributetable:: Cog

.. autoclass:: Cog
    :members:
    :inherited-members:


Cooldowns
++++++++++
.. autoclass:: Bucket
    :members:

.. autoclass:: Cooldown
    :members:
    :inherited-members:
