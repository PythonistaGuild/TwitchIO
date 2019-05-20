import datetime
import time


class Message:

    __slots__ = ('_raw_data', 'content', '_author', 'echo', '_timestamp', '_channel', '_tags')

    def __init__(self, **kwargs):
        self._raw_data = kwargs.get('raw_data')
        self.content = kwargs.get('content')
        self._author = kwargs.get('author')
        self._channel = kwargs.get('channel')
        self._tags = kwargs.get('tags')
        self.echo = False

        try:
            self._timestamp = self._tags['tmi-sent-ts']
        except KeyError:
            self._timestamp = time.time()

    @property
    def author(self):
        """The User object associated with the Message."""
        return self._author

    @property
    def channel(self):  # stub
        """The Channel object associated with the Message."""
        return self._channel

    @property
    def raw_data(self) -> str:
        """The raw data received from Twitch for this Message."""
        return self._raw_data

    @property
    def tags(self):
        """The tags associated with the Message.

        Could be None.
        """
        return self._tags

    @property
    def timestamp(self) -> datetime.datetime.timestamp:
        """The Twitch timestamp for this Message.

        Returns
        ---------
        timestamp:
            UTC datetime object of the Twitch timestamp.
        """
        timestamp = datetime.datetime.utcfromtimestamp(int(self._timestamp) / 1000)
        return timestamp
