.. currentmodule:: twitchio.ext.sounds

.. _sounds-ref:


Sounds Ext
===========================

Sounds is an extension to easily play sounds on your local machine plugged directly into your bot.
Sounds is currently a Beta release, and as such should be treated so.

Currently sounds supports local files and YouTube searches. See below for more details.

Sounds requires a few extra steps to get started, below is a short guide on how to get started with sounds:

**Installation:**

**1 -** First install TwitchIO with the following commands:

**Windows:**

.. code:: sh

    py -3.9 -m pip install -U twitchio[sounds]

**Linux:**

.. code:: sh

    python3.9 -m pip install -U twitchio[sounds]


If you are on Linux you can skip to step **3**.


**2 -** Windows users require an extra step to get sounds working, in your console run the following commands:

.. code:: sh

    py -3.9 -m pip install -U pipwin


Then:

.. code:: sh

    pipwin install pyaudio


**3 -** If you are on windows, download ffmpeg and make sure you add it your path. You can find the .exe required in
the /bin folder. Alternatively copy and paste ffmpeg.exe into your bots Working Directory.

Linux/MacOS users should use their package manager to download and install ffmpeg on their system.

Recipes
---------------------------

**A simple Bot with an AudioPlayer:**

This bot will search YouTube for a relevant video and playback its audio.

.. code-block:: python3

    from twitchio.ext import commands, sounds


    class Bot(commands.Bot):

        def __init__(self):
            super().__init__(token='...', prefix='!', initial_channels=['...'])

            self.player = sounds.AudioPlayer(callback=self.player_done)

        async def event_ready(self) -> None:
            print('Successfully logged in!')

        async def player_done(self):
            print('Finished playing song!')

        @commands.command()
        async def play(self, ctx: commands.Context, *, search: str) -> None:
            track = await sounds.Sound.ytdl_search(search)
            self.player.play(track)

            await ctx.send(f'Now playing: {track.title}')


    bot = Bot()
    bot.run()


**Sound with a Local File:**

This Sound will target a local file on your machine. Just pass the location to source.

.. code-block:: python3

    sound = sounds.Sound(source='my_audio.mp3')


**Multiple Players:**

This example shows how to setup multiple players. Useful for playing music in addition to sounds on events!


.. code-block:: python3

    import twitchio
    from twitchio.ext import commands, sounds


    class Bot(commands.Bot):

        def __init__(self):
            super().__init__(token='...', prefix='!', initial_channels=['...'])

            self.music_player = sounds.AudioPlayer(callback=self.music_done)
            self.event_player = sounds.AudioPlayer(callback=self.sound_done)

        async def event_ready(self) -> None:
            print('Successfully logged in!')

        async def music_done(self):
            print('Finished playing song!')

        async def sound_done(self):
            print('Finished playing sound!')

        @commands.command()
        async def play(self, ctx: commands.Context, *, search: str) -> None:
            track = await sounds.Sound.ytdl_search(search)
            self.music_player.play(track)

            await ctx.send(f'Now playing: {track.title}')

        async def event_message(self, message: twitchio.Message) -> None:
            # This is just an example only...
            # Playing a sound on every message could get extremely spammy...
            sound = sounds.Sound(source='beep.mp3')
            self.event_player.play(sound)


    bot = Bot()
    bot.run()


**Common AudioPlayer actions:**

.. code-block:: python3

    # Set the volume of the player...
    player.volume = 50

    # Pause the player...
    player.pause()

    # Resume the player...
    player.resume()

    # Stop the player...
    player.stop()

    # Check if the player is playing...
    player.is_playing


API Reference
---------------------------

.. attributetable:: OutputDevice

.. autoclass:: OutputDevice
    :members:

.. attributetable:: Sound

.. autoclass:: Sound
    :members:

.. attributetable:: AudioPlayer

.. autoclass:: AudioPlayer
    :members:
