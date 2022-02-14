"""MIT License

Copyright (c) 2017-2022 TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import io
import logging
import os
import pathlib
import shlex
import subprocess
import threading
import time
from functools import partial
from typing import Optional, Union

import pyaudio
import pydub
from pydub.utils import make_chunks
from yt_dlp import YoutubeDL


__all__ = ('Sound', 'AudioPlayer')


logger = logging.getLogger(__name__)


has_ffmpeg: bool
try:
    subprocess.Popen('ffmpeg -version', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    has_ffmpeg = False
else:
    has_ffmpeg = True


__all__ = ('Sound', 'AudioPlayer')


_TEMP = pathlib.Path(str(pathlib.Path().cwd()) + '/_temp')

try:
    _TEMP.mkdir()
except FileExistsError:
    pass


class Sound:
    """TwitchIO Sound Source.

    This is the class that represents a TwitchIO Sound, able to be played in `class`:AudioPlayer:.

    Parameters
    __________
    source: Union[str, io.BufferedIOBase]
        The source to play. Could be a string representing a local file or bytes.
        To search YouTube, use `meth`:ytdl_search: instead.
    info: Optional[dict]
        The info dict provided via ytdl. Only available when searching via YouTube.

    Attributes
    ----------
    ...
    """

    CODECS = ('mp3',
              'aac',
              'flv',
              'wav',
              'opus',)

    YTDLOPTS = {
        'format': 'bestaudio/best',
        'outtmpl': f'{_TEMP}/%(id)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'progress': False,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
    }

    YTDL = YoutubeDL(YTDLOPTS)

    def __init__(self, source: Union[str, io.BufferedIOBase], *, info: Optional[dict]):

        if not has_ffmpeg:
            raise RuntimeError('ffmpeg is required to create and play Sounds. For more information visit: ...')

        self._original = source

        if isinstance(source, str):
            codec = source.split('.')[-1]

            if codec not in self.CODECS:
                source = pathlib.Path(source).absolute().as_posix()
                source_ = source.removesuffix(f'.{codec}')

                proc = subprocess.Popen(shlex.split(f'ffmpeg '
                                                    f'-hide_banner '
                                                    f'-loglevel quiet '
                                                    f'-i '
                                                    f'{source} '
                                                    f'-vn '
                                                    f'-y '
                                                    f'{source_}.opus'))
                proc.wait()
                os.remove(source)

                source = f'{source_}.opus'
                self._source = pydub.AudioSegment.from_file(source, codec='opus')
                self._original = source

                proc.kill()

            else:
                self._source = pydub.AudioSegment.from_file(source, codec=codec)
        else:
            raise NotImplementedError

        if info:
            self.title = info.get('title', None)
            self.url = info.get('url', None)

        self._sample_width = self._source.sample_width
        self._channels = self._source.channels
        self._rate = self._source.frame_rate

    @classmethod
    async def ytdl_search(cls, search: str, *, loop: Optional[asyncio.BaseEventLoop] = None):
        """|coro|

        Search and download songs via YouTube ready to be played.

        Please note this currently downloads to a temp folder in your CWD. This behaviour may change in the future.
        """
        loop = loop or asyncio.get_event_loop()

        to_run = partial(cls.YTDL.extract_info, url=search, download=True)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        source = cls.YTDL.prepare_filename(data)
        return cls(source=source, info=data)

    @property
    def sample_width(self):
        """The audio source sample width."""
        return self._sample_width

    @property
    def channels(self):
        """The audio source channels."""
        return self._channels

    @property
    def rate(self):
        """The audio source sample rate."""
        return self._rate

    @property
    def source(self):
        """The raw audio source."""
        return self._source

    def __del__(self):
        self._source = None


class AudioPlayer:

    MS_CHUNK = 20 / 1000.0

    def __init__(self, *, callback: callable):
        self._pa = pyaudio.PyAudio()

        self._volume: float = 100.0
        self._current: Sound = None  # type: ignore

        self._length = 0
        self._source_chunk = None
        self._time = 0

        self._paused: bool = False
        self._playing: bool = False

        self._callback = callback
        self._thread: threading.Thread = None  #type: ignore

        self._loop = asyncio.get_event_loop()

    def play(self, sound: Sound, *, replace: bool = False) -> None:
        """Play a :class:`Sound` object.

        When play has finished playing, the event `meth`:event_player_finished: is called.
        """
        if not isinstance(sound, Sound):
            raise TypeError('sound parameter must be of type <Sound>.')

        if self._playing and replace:
            self.stop()
        elif self._playing and not replace:
            return

        self._thread = threading.Thread(target=self._play_run, args=([sound]), daemon=True)
        self._thread.start()

    def _play_run(self, sound: Sound):
        self._current = sound
        stream = self._pa.open(format=self._pa.get_format_from_width(sound.sample_width),
                               output=True,
                               channels=sound.channels,
                               rate=sound.rate)

        self._time = start = 0
        self._length = sound._source.duration_seconds
        # TODO: VOLUME CHANGER...
        self._source_chunk = sound._source[start * 1000.0:(start + self._length) * 1000.0] - (60 - (60 * (100 / 100.0)))

        self._playing = True
        while self._playing:
            self._time = start

            for chunks in make_chunks(self._source_chunk, self.MS_CHUNK * 1000):
                while self._paused:
                    time.sleep(0.1)

                if self._playing is False:
                    break

                self._time += self.MS_CHUNK
                stream.write(chunks._data)

                if self._time >= start + self._length:
                    break

            self._clean()
            asyncio.run_coroutine_threadsafe(self._callback(), loop=self._loop)
            break

    def _clean(self):
        if self._current._original.startswith(str(_TEMP.as_posix())):
            try:
                os.remove(self._current._original)
            except FileNotFoundError:
                pass

        self._current = None
        self._paused = False
        self._playing = False

    @property
    def source(self):
        """The currently playing `class`:Sound: object."""
        return self._current

    @property
    def current(self):
        """An alias to `meth`:source:."""
        return self.source

    def pause(self):
        """Method which pauses the player."""
        self._paused = True

    def resume(self):
        """Method which resumes the player."""
        self._paused = False

    @property
    def is_paused(self) -> bool:
        """Property which returns whether the player is currently paused."""
        return self._paused

    def stop(self):
        """Stops the player and clears the source."""
        self._playing = False

    @property
    def is_playing(self):
        """Property which returns whether the player is currently playing."""
        return self._playing
