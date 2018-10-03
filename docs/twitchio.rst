TwitchIO
================

Support
---------------------------
For support with TwitchIO, please join the official `Support Server
<https://discord.me/twitch-api>`_.

Installation
---------------------------
TwitchIO is not currently on Pypi and thus needs to be installed using git. The following commands are the currently
valid ways of installing TwitchIO.

**TwitchIO requires Python 3.5.2+**

**Windows**

.. code:: sh

    py -version -m pip install git+https://github.com/MysterialPy/TwitchIO.git

**Linux**

.. code:: sh

    python3 -m pip install git+https://github.com/MysterialPy/TwitchIO.git

Getting Started
----------------------------
TwitchIO has many endpoint some which require different tokens and ID's.

1. IRC (IRC Token)
    To get an IRC token easily, log in to Twitch with your account made especially for your bot,
    and visit: https://twitchapps.com/tmi/

2. HTTP-Endpoints which require only a Client-ID.
    Info coming soon...

3. HTTP-Endpoints which require a token and scopes.
    Info coming soon...

All 3 endpoints may be used at the same time. Or you may decided to use either one as a standalone.

Currently TwitchIO is at a phase which has emphasis on the IRC endpoint, and creating a framework around it.
Once this is implemented, the other 2 endpoints will be developed further.

A quick and easy bot example:

.. code:: py

    from twitchio import commands


    class Bot(commands.TwitchBot):

        def __init__(self):
            super().__init__(irc_token='...', api_token='...', nick='mysterialpy', prefix='!',
                             initial_channels=['mysterialpy'])

        # Events don't need decorators when subclassed
        async def event_ready(self):
            print(f'Ready | {self.nick}')

        async def event_message(self, message):
            print(message.content)
            await self.process_commands(message)

        # Commands use a different decorator
        @commands.twitch_command(name='test')
        async def my_command(self, ctx):
            await ctx.send(f'Hello {ctx.author.name}!')


    bot = Bot()
    bot.run()

Dataclasses
----------------------------
Dataclasses belonging to TwitchIO.

.. note::
    These should not be created. Instead you should use the ones available
    through the various events and the commands extension.

.. autoclass:: twitchio.dataclasses.Message
    :members:
    :inherited-members:
    :show-inheritance:

.. autoclass:: twitchio.dataclasses.Channel
    :members:
    :inherited-members:
    :show-inheritance:

.. autoclass:: twitchio.dataclasses.User
    :members:
    :inherited-members:
    :show-inheritance:

.. autoclass:: twitchio.dataclasses.Context
    :members:
    :inherited-members:
    :show-inheritance:

Errors
-----------------------

.. automodule:: twitchio.errors
    :members:
    :show-inheritance:

Module contents
---------------

.. automodule:: twitchio
    :members:
    :show-inheritance:
