import asyncio
from twitchio.ext import sounds
from typing import Optional, List


class AudioQueueManager:
    """
    Manages a queue of audio files to be played sequentially with optional repeat and pause functionalities.

    Attributes
    ----------
    queue: asyncio.Queue[:class:`str`]
        A queue to hold paths of audio files to be played.
    is_playing: :class:`bool`
        Indicates whether an audio file is currently being played.
    repeat_queue: :class:`bool`
        If True, adds the current playing audio file back to the queue after playing.
    queue_paused: :class:`bool`
        If True, pauses the processing of the queue.
    player: :class:`sounds.AudioPlayer`
        An instance of AudioPlayer to play audio files.
    current_sound: :class:`str`
        Path of the currently playing audio file.
    """

    def __init__(self, repeat_queue: Optional[bool]=True) -> None:
        """
        Initializes an instance of AudioQueueManager with an empty queue and default settings.

        Parameters
        ----------
        repeat_queue: Optional[:class:`bool`]
            If True, adds the current playing audio file back to the queue after playing, by default True
        """
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.is_playing: bool = False
        self.repeat_queue: bool = repeat_queue
        self.queue_paused: bool = False
        self.player: sounds.AudioPlayer = sounds.AudioPlayer(callback=self.player_done)
        self.current_sound: str = ""

    async def player_done(self) -> None:
        """
        |coro|

        Callback method called when the player finishes playing an audio file.
        Resets the is_playing flag and marks the current task as done in the queue.
        """
        self.is_playing = False
        self.queue.task_done()

    async def add_audio(self, sound_path: str) -> None:
        """
        |coro|

        Adds a new audio file to the queue.

        Parameters
        ----------
        sound_path: :class:`str`
            Path of the audio file to add to the queue.
        """
        await self.queue.put(sound_path)

    async def play_next(self) -> None:
        """
        |coro|

        Plays the next audio file in the queue if the queue is not empty and not paused.
        Sets the is_playing flag, retrieves the next audio file from the queue, and plays it.
        If repeat_queue is True, adds the current audio file back to the queue after playing.
        """
        if not self.queue.empty() and not self.queue_paused:
            self.is_playing = True
            sound_path = await self.queue.get()
            self.current_sound = sound_path
            sound = sounds.Sound(source=sound_path)
            self.player.play(sound)
            if self.repeat_queue:
                await self.queue.put(self.current_sound)

    def skip_audio(self) -> None:
        """
        Stops the currently playing audio file if there is one.
        """
        if self.is_playing:
            self.player.stop()
            self.is_playing = False

    def stop_audio(self) -> None:
        """
        Stops the currently playing audio file.
        Resets the playing flag but leaves the queue intact.
        """
        if self.is_playing:
            self.player.stop()
            self.is_playing = False

    def pause_audio(self) -> None:
        """
        Pauses the currently playing audio file.
        """
        self.player.pause()

    def resume_audio(self) -> None:
        """
        Resumes the currently paused audio file.
        """
        self.player.resume()

    async def clear_queue(self) -> None:
        """
        |coro|

        Clears all audio files from the queue.
        """
        while not self.queue.empty():
            await self.queue.get()
            self.queue.task_done()

    def pause_queue(self) -> None:
        """
        Pauses the processing of the queue.
        """
        self.queue_paused = True

    def resume_queue(self) -> None:
        """
        Resumes the processing of the queue.
        """
        self.queue_paused = False

    def get_queue_contents(self) -> List[str]:
        """
        Retrieves the current contents of the queue as a list.

        Returns
        -------
        List[:class:`str`]
        """
        return list(self.queue._queue)

    async def queue_loop(self) -> None:
        """
        |coro|

        Continuously checks the queue and plays the next audio file if not currently playing and not paused.
        """
        try:
            while True:
                await asyncio.sleep(0.2)
                if not self.is_playing and not self.queue.empty() and not self.queue_paused:
                    await self.play_next()
        finally:
            return