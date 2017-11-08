.. image:: logo.png?raw=true
    :align: center

An Asynchronous IRC/API Wrapper currently in Development for TwitchBots.
Official Documentation: `Click Here! <http://twitchio.readthedocs.io/en/latest/twitchio.html>`_

Installation
------------
TwitchIO requires Python 3.5+

**Windows**

.. code:: sh

    py -version -m pip install git+https://github.com/MysterialPy/TwitchIO.git

**Linux**

.. code:: sh

    python3 -m pip install git+https://github.com/MysterialPy/TwitchIO.git

Simple Usage
____________
Please keep in mind TwitchIO is currently in very early **Alpha-Stages**. It will come with it's serveral kinks, flaws and bugs.
One of those flaws is that the Command System(TwitchBot) currently only works when subclassed.

Standalone
~~~~~~~~~~
.. code:: py
    
    from twitchio import commands as tcommands


    class Botto(tcommands.TwitchBot):
        """Create our IRC Twitch Bot.
        api_token is optional, but without it, you will not be able to make certain calls to the API."""
        
        def __init__(self):
            super().__init__(prefix=['!', '?'], token='IRC_TOKEN', api_token='API_TOKEN', client_id='CLIENT_ID',
                             nick='mycoolircnick', initial_channels=['my_channel'])
        
        async def event_ready(self):
            """Event called when the bot is ready to go!"""
            print('READY!')
        
        async def event_message(self, message):
            """Event called when a message is sent to a channel you are in."""
            if message.content == 'Hello':
                await message.send('World!')
        
        @tcommands.twitch_command(aliases=['silly'])
        async def silly_command(self, ctx):
            """A simple command, which sends a message back to the channel!"""
            await ctx.send('Hai there {0} Kappa.'.format(ctx.author.name))


    bot = Botto()
    bot.run()
