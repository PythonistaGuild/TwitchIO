"""MIT License

Copyright (c) 2017-present TwitchIO

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
import audioop
import dataclasses
import io
import logging
import subprocess
import threading
import time
from functools import partial
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar, Union

import pyaudio
from yt_dlp import YoutubeDL


__all__ = ("Sound", "AudioPlayer")


logger = logging.getLogger(__name__)


AP = TypeVar("AP", bound="AudioPlayer")

ffmpeg_bin: Optional[str] = None
try:
    proc = subprocess.Popen(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    try:
        proc = subprocess.Popen(["ffmpeg.exe", "-version"])
    except FileNotFoundError:
        ffmpeg_bin = None
    else:
        ffmpeg_bin = "ffmpeg.exe"
else:
    ffmpeg_bin = "ffmpeg"


__all__ = ("Sound", "AudioPlayer")


@dataclasses.dataclass
class OutputDevice:
    """Class which represents an OutputDevice usable with :class:`AudioPlayer` .

    Pass this into the appropriate :class:`AudioPlayer` method to set or change device.

    Attributes
    ----------
    name: :class:`str`
        The name of the device.
    index: :class:`int`
        The index of the device.
    channels: :class:`int`
        The amount of available channels this device has.
    """

    name: str
    index: int
    channels: int


class Sound:
    """TwitchIO Sound Source.

    This is the class that represents a TwitchIO Sound, able to be played in :class:`AudioPlayer`.


    .. warning::

        This class is still in Beta stages and currently only supports generating sounds via :meth:`ytdl_search`
        or locally downloaded audio files. Future versions will have support for file like objects.

    Parameters
    __________
    source: Optional[Union[str, io.BufferedIOBase]]
        The source to play. Could be a string representing a local file or bytes.
        To search YouTube, use :meth:`ytdl_search` instead.
    info: Optional[dict]
        The info dict provided via ytdl. Only available when searching via YouTube. Do not pass this directly.

    Attributes
    ----------
    title: str
        The title of the track. Will be None if :class:`io.BufferedIOBase` is supplied as a source.
    url: Optional[str]
        The url of the track searched via YouTube. Will be None if source is supplied.
    """

    CODECS = (
        "mp3",
        "aac",
        "flv",
        "wav",
        "opus",
    )

    YTDLOPTS = {
        "format": "bestaudio/best",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "progress": False,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",  # ipv6 addresses cause issues sometimes
    }

    YTDL = YoutubeDL(YTDLOPTS)

    def __init__(
        self,
        source: Optional[Union[str, io.BufferedIOBase]] = None,
        *,
        info: Optional[dict] = None,
    ):
        self.title = None
        self.url = None

        self.proc = None

        if ffmpeg_bin is None:
            raise RuntimeError("ffmpeg is required to create and play Sounds. Check your is present in your Path")

        if info:
            self.proc = subprocess.Popen(
                [
                    ffmpeg_bin,
                    "-reconnect",
                    "1",
                    "-reconnect_streamed",
                    "1",
                    "-reconnect_delay_max",
                    "5",
                    "-i",
                    info["url"],
                    "-loglevel",
                    "panic",
                    "-vn",
                    "-f",
                    "s16le",
                    "pipe:1",
                ],
                stdout=subprocess.PIPE,
            )

            self.title = info.get("title", None)
            self.url = info.get("url", None)

        elif isinstance(source, str):
            self.title = source

            self.proc = subprocess.Popen(
                [
                    ffmpeg_bin,
                    "-i",
                    source,
                    "-loglevel",
                    "panic",
                    "-vn",
                    "-f",
                    "s16le",
                    "pipe:1",
                ],
                stdout=subprocess.PIPE,
            )

        self._channels = 2
        self._rate = 48000

    @classmethod
    async def ytdl_search(cls, search: str, *, loop: Optional[asyncio.BaseEventLoop] = None):
        """|coro|

        Search songs via YouTube ready to be played.
        """
        loop = loop or asyncio.get_event_loop()

        to_run = partial(cls.YTDL.extract_info, url=search, download=False)
        data = await loop.run_in_executor(None, to_run)

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        data["time"] = time.time()

        return cls(info=data)

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

        if self.proc:
            self.proc.kill()


class AudioPlayer:
    """TwitchIO Sounds Audio Player.

    Use this class to control and play sounds generated with :class:`Sound` .

    Parameters
    ----------
    callback: Coroutine
        The coroutine called when a Sound has finished playing.


    .. note ::

        To use this player with the system non default output device, see :meth:`with_device`, or
        :attr:`active_device`. The output device can be changed live by setting `active_device` with an
        :class:`OutputDevice`.
    """

    def __init__(self, *, callback: Callable[..., Coroutine[Any, Any, None]]):
        self._pa = pyaudio.PyAudio()
        self._stream = None

        self._current: Sound = None  # type: ignore

        self._paused: bool = False
        self._playing: bool = False
        self._volume = 100

        self._callback = callback
        self._thread: threading.Thread = None  # type: ignore

        self._loop = asyncio.get_event_loop()

        self._devices: Dict[int, OutputDevice] = {}
        self._get_devices()

        self._active_devices: List[OutputDevice] = []
        self._use_device: Optional[OutputDevice] = None

    def _get_devices(self):
        for index in range(self._pa.get_device_count()):
            device = self._pa.get_device_info_by_index(index)

            if device["maxInputChannels"] != 0:
                continue

            self._devices[index] = OutputDevice(
                name=device["name"],
                index=device["index"],
                channels=device["maxOutputChannels"],
            )

    def play(self, sound: Sound, *, replace: bool = False) -> None:
        """Play a :class:`Sound` object.

        When play has finished playing, the event :meth:`event_player_finished` is called.
        """
        if not isinstance(sound, Sound):
            raise TypeError("sound parameter must be of type <Sound>.")

        if self._playing and replace:
            self.stop()
        elif self._playing and not replace:
            return

        self._thread = threading.Thread(target=self._play_run, args=([sound]), daemon=True)
        self._thread.start()

    def _play_run(self, sound: Sound):
        self._current = sound

        device = self._use_device.index if self._use_device else None
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            output=True,
            channels=sound.channels,
            rate=sound.rate,
            output_device_index=device,
        )

        bytes_ = sound.proc.stdout.read(4096)

        self._playing = True
        while self._playing:
            while self._paused:
                time.sleep(0.1)

            if self._playing is False:
                break

            if not bytes_:
                break

            self._stream.write(audioop.mul(bytes_, 2, self._volume / 100))
            bytes_ = sound.proc.stdout.read(4096)

        self._clean(sound)
        asyncio.run_coroutine_threadsafe(self._callback(), loop=self._loop)

    def _clean(self, sound: Sound):
        sound.proc.kill()
        self._stream = None

        self._current = None
        self._paused = False
        self._playing = False

    @property
    def source(self):
        """The currently playing :class:`Sound` object."""
        return self._current

    @property
    def current(self):
        """An alias to :meth:`source`."""
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

    @property
    def volume(self) -> int:
        """Property which returns the current volume.

        This property can also be set with a volume between 1 and 100, to change the volume.
        """
        return self._volume

    @volume.setter
    def volume(self, level: int) -> None:
        if level > 100 or level < 1:
            raise ValueError("Volume must be between 1 and 100")

        self._volume = level

    @property
    def devices(self) -> Dict[int, OutputDevice]:
        """Return a dict of :class:`OutputDevice` that can be used to output audio."""
        return self._devices

    @property
    def active_device(self) -> Optional[OutputDevice]:
        """Return the active output device for this player. Could be None if default is being used.

        This property can also be set with a new :class:`OutputDevice` to change audio output.
        """
        return self._use_device

    @active_device.setter
    def active_device(self, device: OutputDevice) -> None:
        if not isinstance(device, OutputDevice):
            raise TypeError(f"Parameter <device> must be of type <{type(OutputDevice)}> not <{type(device)}>.")

        self._use_device = device
        if not self._stream:
            return

        if self._playing:
            self._paused = True

        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            output=True,
            channels=self._current.channels,
            rate=self._current.rate,
            output_device_index=device.index,
        )

        self._paused = False

    @classmethod
    def with_device(cls, *, callback: Callable[..., Coroutine[Any, Any, None]], device: OutputDevice) -> AP:
        """Method which returns a player ready to be used with the given :class:`OutputDevice`.

        Returns
        -------
            :class:`OutputDevice`
        """
        if not isinstance(device, OutputDevice):
            raise TypeError(f"Parameter <device> must be of type <{type(OutputDevice)}> not <{type(device)}>.")

        self = cls(callback=callback)
        self._use_device = device

        return self
