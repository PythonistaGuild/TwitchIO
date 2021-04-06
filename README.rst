.. image:: ./logo.png?raw=true
    :align: center
    
    
.. image:: https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9-blue.svg
    :target: https://www.python.org


.. image:: https://img.shields.io/github/license/TwitchIO/TwitchIO.svg
    :target: ./LICENSE


.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black


TwitchIO 2.0 is currently in BETA stage looking for testers and users. 2.0 supercedes the current 1.x version.

Although not classified as Stable you should be able to use this release for testing purposes. **Use in production is at your own risk**.

TwitchIO is an asynchronous Python wrapper around the Twitch API and IRC, with a powerful command extension for creating Twitch Chat Bots. TwitchIO 2 will cover 100% of the new Twitch API and will feature support for commands, PubSub and Webhooks.

TwitchIO 2.0 will be buggy, will be lacking some features and you will run into problems here and there, that is the nature of BETA software, by using 2.0 you are helping test and develop TwitchIO by providing us with valuable feedback, feature requests and bug reports.

Documentation
---------------------------
For the Official Documentation: `Click Here! <https://twitchio.readthedocs.io/en/2.0/index.html>`_

Support
---------------------------
For support using TwitchIO, please join the official `support server
<https://discord.gg/RAKc3HF>`_ on `Discord <https://discordapp.com/>`_.

|Discord|

.. |Discord| image:: https://img.shields.io/discord/490948346773635102?color=%237289DA&label=Pythonista&logo=discord&logoColor=white
   :target: https://discord.gg/RAKc3HF
   
Installation
---------------------------
TwitchIO 2 requires **Python 3.7+**. You can download the latest version of Python  `here <https://www.python.org/downloads/>`_.

**Windows**

.. code:: sh

    py -3.9 -m pip install -U twitchio --pre

**Linux**

.. code:: sh

    python3.9 -m pip install -U twitchio --pre

Access Tokens
---------------------------
Visit `Token Generator <https://twitchtokengenerator.com/>`_ for a simple way to generate tokens for use with TwitchIO.

Getting Started
---------------------------
A simple Chat Bot.

.. code:: python

    from twitchio.ext import commands


    class Bot(commands.Bot):

        def __init__(self):
            # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
            super().__init__(token='ACCESS_TOKEN', prefix='?', initial_channels=['...'])

        async def event_ready(self):
            # We are logged in and ready to chat and use commands...
            print(f'Logged in as | {self.nick}')

        @commands.command()
        async def hello(self, ctx: commands.Context):
            # Send a hello back!
            await ctx.send(f'Hello {ctx.author.name}!')


    bot = Bot()
    bot.run()


Contributing
---------------------------
TwitchIO 2.0 currently uses the `Black <https://black.readthedocs.io/en/stable/index.html/>`_ formatter to enforce sensible style formatting.


Before creating a Pull Request it is encouraged you install and run black on your code.

The Line Length limit for TwitchIO 2.0 is **120**.


For installation and usage of Black visit: `Black Formatter <https://black.readthedocs.io/en/stable/installation_and_usage.html/>`_

For integrating Black into your IDE visit: `Black IDE Usage <https://black.readthedocs.io/en/stable/editor_integration.html/>`_

Special Thanks
---------------------------
Thank you to all those who contribute and help TwitchIO grow.

Special thanks to:

`SnowyLuma <https://github.com/SnowyLuma>`_

`Harmon <https://github.com/Harmon758>`_

`Tom <https://github.com/IAmTomahawkx>`_

`Tesence <https://github.com/tesence>`_

`Adure <https://github.com/Adure>`_

`Scragly <https://github.com/scragly>`_


If I have forgotten anyone please let me know <3: `EvieePy <https://github.com/EvieePy>`_
