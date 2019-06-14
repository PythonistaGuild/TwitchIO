.. image:: https://i.imgur.com/B0nvk2w.png?raw=true
    :align: center

.. image:: https://img.shields.io/badge/Python-3.6%20%7C%203.7-blue.svg
    :target: https://www.python.org

.. image:: https://img.shields.io/github/license/TwitchIO/TwitchIO.svg
    :target: LICENSE
    
.. image:: https://api.codacy.com/project/badge/Grade/61e9d573b4af415a809068333d6b437b
    :target: https://app.codacy.com/project/mysterialpy/TwitchIO/dashboard

.. image:: https://api.codeclimate.com/v1/badges/1d1a6d3e8e3e3e29109e/maintainability
    :target: https://codeclimate.com/github/TwitchIO/TwitchIO
    :alt: Maintainability


An Asynchronous IRC/API Wrapper currently in Development for TwitchBots made in Python!

Documentation
---------------------------
Official Documentation: `Click Here! <https://twitchio.readthedocs.io/en/rewrite/twitchio.html>`_

Support
---------------------------
For support using TwitchIO, please join the official `support server
<https://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com/>`_.

Installation
---------------------------
The following commands are currently the valid ways of installing TwitchIO.

**TwitchIO requires Python 3.6 or higher.**

**Windows**

.. code:: sh

    py -version -m pip install twitchio

**Linux**

.. code:: sh

    python3 -m pip install twitchio

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

    from twitchio.ext import commands


    class Bot(commands.Bot):

        def __init__(self):
            super().__init__(irc_token='...', client_id='...', nick='...', prefix='!',
                             initial_channels=['...'])

        # Events don't need decorators when subclassed
        async def event_ready(self):
            print(f'Ready | {self.nick}')

        async def event_message(self, message):
            print(message.content)
            await self.handle_commands(message)

        # Commands use a different decorator
        @commands.command(name='test')
        async def my_command(self, ctx):
            await ctx.send(f'Hello {ctx.author.name}!')


    bot = Bot()
    bot.run()
    
    
`Become a patron <https://www.patreon.com/twitchio>`_ and help support TwitchIO's development <3.

All Twitch logos used are owned by Twitch.tv respectively. Use of the Twitch logos does not imply any affiliation with or endorsement by them.
