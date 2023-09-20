.. currentmodule:: twitchio.ext.commands

.. _commands-ref:

Commands Ext
===========================


Walkthrough
------------

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
- :class:`~twitchio.Clip` - takes a clip URL.

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

With that 3.10 syntax in mind, we could also replace that ``None`` for another type. Maybe we want a clip, or any URL.
We could accomplish this using the Union syntax (as it's known). We'll make use of ``yarl`` here to parse URLs.

.. note::
    If you're using anything below 3.10, you can use ``typing.Union`` as a substitute for that syntax, like so:

    .. code-block:: python

        from typing import Union

        def foo(argument: Union[str, int]) -> None:
            ...

At the same time, we'll introduce custom converters. While the library handles basic types and certain twitch types for you,
you may wish to make your own converters at some point. The library allows you to do this by passing a callable function to the typehint.
Additionally, you can use ``typing.Annotated`` to transform the argument for the type checker. This feature was introduced in Python 3.9,
if you wish to use this feature on lower versions consider installing ``typing_extensions`` to use it from there.
Using Annotated is not required, however it will help your type checker distinguish between converters and types.

Lets take a look at custom converters and Annotated:

.. code-block:: python

    import yarl
    import twitchio
    from typing import Annotated
    from twitchio.ext import commands

    def url_converter(ctx: commands.Context, arg: str) -> yarl.URL:
        return yarl.URL(arg) # this will raise if its an invalid URL.

    @bot.command(name="share")
    async def share_command(ctx: commands.Context, url: Annotated[yarl.URL, url_converter]) -> None:
        await ctx.send(f"{ctx.author.name} wants to share a link on {url.host}: {url}")

Now that we've seen how custom converters work, let's combine them with the Union syntax to create a command that 
will take either a :class:`~twitchio.Clip` or a URL.
I've spread the command definition out over multiple lines to make it more readable.

.. code-block:: python

    import yarl
    import twitchio
    from typing import Annotated
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    def url_converter(ctx: commands.Context, arg: str) -> yarl.URL:
        return yarl.URL(arg) # this will raise if its an invalid URL.

    @bot.command(name="share")
    async def share_command(
        ctx: commands.Context,
        url: twitchio.Clip | Annotated[yarl.URL, url_converter]
    ) -> None:
        if isinstance(url, twitchio.Clip):
            await ctx.send(f"{ctx.author.name} wants to share a clip from {url.broadcaster.name}: {url.url}")
        else:
            await ctx.send(f"{ctx.author.name} wants to share a link on {url.host}: {url}")
    
    bot.run()


.. image:: /images/commands_arguments_5.png

___

Let's take a look at the different ways you can pass strings to your commands.
We'll use this example code:

.. code-block:: python

    import twitchio
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="echo")
    async def echo(ctx: commands.Context, phrase: str, other_phrase: str | None) -> None:
        response = f"Echo! {phrase}"
        if other_phrase:
            response += f". You also said: {other_phrase}"
        
        await ctx.send(response)
    
    bot.run()

At it's most basic, we can simply pass a word, and get a word back:

.. image:: /images/commands_parsing_1.png

However what do we do when we want to pass a sentence or multiple words to one argument?
If change nothing here, and add a second word, we'll get some unwanted behaviour:

.. image:: /images/commands_parsing_2.png

However, there are two workarounds we can do.

First, we can tell our users to quote their argument:

.. image:: /images/commands_parsing_3.png

However, if we want to work around it on the bot side, we can change our code to use a special *positional only* argument.
In python, positional only arguments are ones that you must specify explicitly when calling the function.
However, twitchio interprets them to mean "pass me the rest of the input". This means that you can only have **one** of these arguments.
This must also be the last argument, because it consumes the rest of the input.

Let's see how this would look:

.. code-block:: python

    import twitchio
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    @bot.command(name="echo")
    async def echo(ctx: commands.Context, *, phrase: str) -> None:
        response = f"Echo! {phrase}"
        
        await ctx.send(response)
    
    bot.run()

And how it turns out:

.. image:: /images/commands_parsing_4.png


___

Now, let's clean up our errors a bit. To do this, we'll take a mix of the code examples from above:

.. code-block:: python

    import yarl
    import twitchio
    from typing import Annotated
    from twitchio.ext import commands

    bot = commands.Bot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    def youtube_converter(ctx: commands.Context, arg: str) -> yarl.URL:
        url = yarl.URL(arg) # this will raise if its an invalid URL.
        if url.host not in ("youtube.com", "youtu.be"): 
            raise RuntimeError("Not a youtube link!")
        
        return url

    @bot.command(name="share")
    async def share_command(
        ctx: commands.Context,
        url: Annotated[yarl.URL, youtube_converter],
        hype: int,
        *,
        comment: str
    ) -> None:
        hype_level = "hype" if 0 < hype < 5 else "very hype"
        await ctx.send(f"{ctx.author.name} wants to share a {hype_level} link on {url.host}: {comment}")
    
    bot.run()

Currently, any errors that are raised will simply go directly into our console, but that's not really ideal behaviour.
We want to choose errors to ignore, errors to print, and errors to send to the user. We can do this by subclassing our Bot, and overriding the command_error event.
Let's take a look at that specifically:

.. code-block:: python

    from twitchio.ext import commands

    class MyBot(commands.Bot):
        async def event_command_error(self, context: commands.Context, error: Exception):
            print(error)

    bot = MyBot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    # SNIP: command
    
    bot.run()

Great, we've switched from the default behaviour to a custom behaviour. However, we can improve on it.

There are a couple errors that you are garaunteed to encounter. CommandNotFound is probably the most annoying one, so let's start there:

.. code-block:: python

    class MyBot(commands.Bot):
        async def event_command_error(self, context: commands.Context, error: Exception):
            if isinstance(error, commands.CommandNotFound):
                return
            
            print(error)

    # SNIP: everything else

Now we will no longer see that pesky command not found error in our console every time someone mistypes a command.
Next, we can handle some of the errors we saw earlier, like ArgumentParsingFailed:

.. code-block:: python

    class MyBot(commands.Bot):
        async def event_command_error(self, context: commands.Context, error: Exception):
            if isinstance(error, commands.CommandNotFound):
                return
            
            elif isinstance(error, commands.ArgumentParsingFailed):
                await context.send(error.message)
            
            else:
                print(error)

    # SNIP: everything else

Now we send argument parsing errors directly to the user, so they can adjust their input.
Let's try combining this subclass with our existing code:

.. code-block:: python

    import yarl
    import twitchio
    from typing import Annotated
    from twitchio.ext import commands

    class MyBot(commands.Bot):
        async def event_command_error(self, context: commands.Context, error: Exception):
            if isinstance(error, commands.CommandNotFound):
                return
            
            elif isinstance(error, commands.ArgumentParsingFailed):
                await context.send(error.message)
            
            else:
                print(error)

    bot = MyBot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    def youtube_converter(ctx: commands.Context, arg: str) -> yarl.URL:
        url = yarl.URL(arg) # this will raise if its an invalid URL.
        if url.host not in ("youtube.com", "youtu.be"): 
            raise RuntimeError("Not a youtube link!")
        
        return url

    @bot.command(name="share")
    async def share_command(
        ctx: commands.Context,
        url: Annotated[yarl.URL, youtube_converter],
        hype: int,
        *,
        comment: str
    ) -> None:
        hype_level = "hype" if 0 < hype < 5 else "very hype"
        await ctx.send(f"{ctx.author.name} wants to share a {hype_level} link on {url.host}: {comment}")
    
    bot.run()

Now, let's pass it some bad arguments and see what happens.

.. image:: /images/commands_errors_1.png

Now, that isn't very user intuitive, but for the purpose of this walkthrough, it'll do just fine. You can tweak that as you want!
Let's fill this out with some more common errors:

.. code-block:: python
    
    class MyBot(commands.Bot):
        async def event_command_error(self, context: commands.Context, error: Exception):
            if isinstance(error, commands.CommandNotFound):
                return
            
            elif isinstance(error, commands.ArgumentParsingFailed):
                await context.send(error.message)
            
            elif isinstance(error, commands.MissingRequiredArgument):
                await context.send("You're missing an argument: " + error.name)
            
            elif isinstance(error, commands.CheckFailure): # we'll explain checks later, but lets include it for now.
                await context.send("Sorry, you cant run that command: " + error.args[0])
            
            else:
                print(error)

Now when we run our code we get some actual errors in our chat!

.. image:: /images/commands_errors_2.png

To create your own errors to handle here from arguments, subclass :class:`BadArgument` and raise that custom exception in your argument parser.
If you want to raise errors from your commands, subclass :class:`TwitchCommandError` instead. As an example, let's change the youtube converter to use a custom error:

 .. code-block:: python

    import yarl
    import twitchio
    from typing import Annotated
    from twitchio.ext import commands

    class MyBot(commands.Bot):
        async def event_command_error(self, context: commands.Context, error: Exception):
            if isinstance(error, commands.CommandNotFound):
                return
            
            elif isinstance(error, commands.ArgumentParsingFailed):
                await context.send(error.message)
            
            elif isinstance(error, commands.MissingRequiredArgument):
                await context.send("You're missing an argument: " + error.name)
            
            elif isinstance(error, commands.CheckFailure): # we'll explain checks later, but lets include it for now.
                await context.send("Sorry, you cant run that command: " + error.args[0])
            
            elif isinstance(error, YoutubeConverterError):
                await context.send(f"{error.link} is not a valid youtube URL!")
            
            else:
                print(error)

    bot = MyBot(token="...", prefix="!", initial_channels=["iamtomahawkx", "chillymosh", "mystypy"])

    class YoutubeConverterError(commands.BadArgument):
        def __init__(self, link: yarl.URL):
            self.link = link
            super().__init__("Bad link!")

    def youtube_converter(ctx: commands.Context, arg: str) -> yarl.URL:
        url = yarl.URL(arg) # this will raise if its an invalid URL.
        if url.host not in ("youtube.com", "youtu.be"): 
            raise YoutubeConverterError(url)
        
        return url

    @bot.command(name="share")
    async def share_command(
        ctx: commands.Context,
        url: Annotated[yarl.URL, youtube_converter],
        hype: int,
        *,
        comment: str
    ) -> None:
        hype_level = "hype" if 0 < hype < 5 else "very hype"
        await ctx.send(f"{ctx.author.name} wants to share a {hype_level} link on {url.host}: {comment}")
    
    bot.run()

Now, let's pass a bad URL to it:

.. image:: /images/commands_errors_3.png

Great, we get our custom error! That's our basic error handling, anything more complex is beyond this walkthrough.

.. tip::

    Many Twitchio errors have additional context contained within them.
    If you wish to build your own error messages instead of the defaults, try checking the error's attributes.

___


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
