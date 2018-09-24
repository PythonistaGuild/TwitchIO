.. image:: logo.png?raw=true
    :align: center

An Asynchronous IRC/API Wrapper currently in Development for TwitchBots made in Python!

Official Documentation: `Click Here! <https://twitchio.readthedocs.io/en/rewrite/twitchio.html>`_
Official Support Server: `Click Here! <https://discord.me/twitch-api>`_

Current Development and Goals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TwitchIO has **three** main initial goals in mind. All of which will hopefully, combine to make the
eventual release version of TwitchIO.

1. **An IRC Bot framework for Twitch:** This will be the basis of TwitchIO. A framework which is easy to use, and is
able to provide a solid base for designing a bot on Twitch.

2. **A non-IRC related API Wrapper:** The goal here is to have a wrapper which will allow users to access non-IRC
endpoints with ease, whilst of course, providing flawless use by the TwitchIO bot framework.

3. **Integration into a Discord Bot:** Having a framework which allows for a Twitchbot, and Discord bot to be easily
developed alongside and integrated into eachother, is a main focus of TwitchIO. As such, TwitchIO focuses on using
methods and other conventions which will hopefully minimize conflicts. Although TwitchIO is not affiliated with the
target discord library (discord.py), it is the library which suits best, and has been a great influence in TwitchIO's
design.

With all that being said, please enjoy the library (in it's current state), and feel free to suggest changes or fixes
as and where you see fit. Special thanks should be made to Rapptz(https://github.com/Rapptz/discord.py) and
Discord.py for providing a high quality and very well structured library and code (better than I could ever do)
which has certainly influenced the design of TwitchIO.


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
