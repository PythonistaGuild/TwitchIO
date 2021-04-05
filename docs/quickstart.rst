Quickstart
=============
This mini tutorial will serve as an entry point into TwitchIO 2.
After it you should have a small working bot and a basic understanding of TwitchIO.

If you haven't already installed TwitchIO 2, check out :doc:`installing`.


Tokens and Scopes
-------------------
For the purpose of this tutorial we will only be using an OAuth Token with permissions to read and write to chat.
If you require custom scopes, please make sure you select them.

Visit `Token Generator <https://twitchtokengenerator.com/>`_ and select the Bot Chat Token.
After selecting this you can copy your Access Token somewhere safe.


Basic Bot
-----------
TwitchIO 2 can be run in multiple different ways, (as a client only, as a bot using extensions, with HTTP requests etc).
Here we will be using the commands extension of TwitchIO to create a Chat Bot.

.. note::

    The TwitchIO commands extension has all the functionality of the Client and HTTPClient, plus more.

.. code:: python

    from twitchio.ext import commands


    class Bot(commands.Bot):

        def __init__(self):
            # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
            # prefix can be a callable, which returns a list of strings or a string...
            # initial_channels can also be a callable which returns a list of strings...
            super().__init__(token='ACCESS_TOKEN', prefix='?', initial_channels=['...'])

        async def event_ready(self):
            # Notify us when everything is ready!
            # We are logged in and ready to chat and use commands...
            print(f'Logged in as | {self.nick}')

        @commands.command()
        async def hello(self, ctx: commands.Context):
            # Here we have a command hello, we can invoke our command with our prefix and command name
            # e.g ?hello
            # We can also give our commands aliases (different names) to invoke with.

            # Send a hello back!
            # Sending a reply back to the channel is easy... Below is an example.
            await ctx.send(f'Hello {ctx.author.name}!')


    bot = Bot()
    bot.run()
    # bot.run() is blocking and will stop execution of any below code here until stopped or closed.


The above example listens to one event, `event_ready`. If we want to listen to other events,
we can simply add them to our Bot class.

For an exhaustive list of events, visit: `Event Reference <https://twitchio.readthedocs.io/en/2.0/twitchio.html#event-reference>`_

**Let's add an** `event_message` **which will listen for all messages the bot can see:**

.. code:: py

    from twitchio.ext import commands


    class Bot(commands.Bot):

        def __init__(self):
            # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
            # prefix can be a callable, which returns a list of strings or a string...
            # initial_channels can also be a callable which returns a list of strings...
            super().__init__(token='ACCESS_TOKEN', prefix='?', initial_channels=['...'])

        async def event_ready(self):
            # Notify us when everything is ready!
            # We are logged in and ready to chat and use commands...
            print(f'Logged in as | {self.nick}')

        async def event_message(self, message):
            # Messages with echo set to True are messages sent by the bot...
            # For now we just want to ignore them...
            if message.echo:
                return

            # Print the contents of our message to console...
            print(message.content)

            # Since we have commands and are overriding the default `event_message`
            # We must let the bot know we want to handle and invoke our commands...
            await self.handle_commands(message)

        @commands.command()
        async def hello(self, ctx: commands.Context):
            # Here we have a command hello, we can invoke our command with our prefix and command name
            # e.g ?hello
            # We can also give our commands aliases (different names) to invoke with.

            # Send a hello back!
            # Sending a reply back to the channel is easy... Below is an example.
            await ctx.send(f'Hello {ctx.author.name}!')


    bot = Bot()
    bot.run()
    # bot.run() is blocking and will stop execution of any below code here until stopped or closed.


The above example is similar to our original code, though this time we have added in a common event, `event_message`.
When using `event_message`, as shown above, some things need to be taken into consideration.

Mainly echo messages and the handling of commands. If you do not handle these appropriately you may have undesired
effects on your bot.

You should now have a working Twitch Chat Bot that prints messages to console, and responds to the command `?hello`.
If you are stuck, please visit the :doc:`faq` page or `Join our Discord <https://discord.gg/RAKc3HF>`_.