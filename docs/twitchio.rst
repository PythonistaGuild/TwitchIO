TwitchIO
================

Support
---------------------------
For support using TwitchIO, please join the official `support server
<https://discord.me/twitch-api>`_ on `Discord <https://discordapp.com/>`_.

Installation
---------------------------
TwitchIO is currently not on PyPI and thus needs to be installed using git.
The following commands are currently the valid ways of installing TwitchIO.

**TwitchIO requires Python 3.6 or higher.**

**Windows**

.. code:: sh

    py -version -m pip install git+https://github.com/MysterialPy/TwitchIO.git

**Linux**

.. code:: sh

    python3 -m pip install git+https://github.com/MysterialPy/TwitchIO.git

Getting Started
----------------------------
TwitchIO uses many endpoints which may require different tokens and IDs.

1. IRC endpoints which require an OAuth token.
    To get a token, log in to Twitch with the bot's account and visit:
    https://twitchapps.com/tmi/

2. HTTP endpoints which require a client ID.
    *To be documented.*

3. HTTP endpoints which require an OAuth token and certain scopes.
    *To be documented.*

All 3 endpoints may be used at the same time. Otherwise, you may choose to use any or some of the endpoints.

Currently, TwitchIO's development is at a phase which has emphasis on the IRC endpoint and creating a framework around it.
Once this is implemented, the other 2 endpoints will be developed further.

A quick and easy bot example:

.. code:: py

    from twitchio import commands


    class Bot(commands.TwitchBot):

        def __init__(self):
            super().__init__(irc_token='...', client_id='...', nick='...', prefix='!',
                             initial_channels=['...'])

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

Client
----------------------------

.. autoclass:: twitchio.client.TwitchClient
    :members:

Dataclasses
----------------------------
Dataclasses belonging to TwitchIO.

.. note::
    These should not be created by the user. Instead, you should use the ones
    passed to event listeners or returned from properties and methods of TwitchIO's objects.

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

Module Contents
---------------

.. automodule:: twitchio
    :members:
    :show-inheritance:
