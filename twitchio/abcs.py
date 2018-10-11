import abc
import time

from .cooldowns import RateBucket
from .errors import *


class IRCLimiterMapping:

    def __init__(self):
        self.buckets = {}

    def get_bucket(self, channel: str, method: str):
        try:
            bucket = self.buckets[channel]
        except KeyError:
            bucket = RateBucket(method=method)
            self.buckets[channel] = bucket

        if bucket.method != method:
            bucket.method = method
            if method == 'mod':
                bucket.limit = bucket.MODLIMIT
            else:
                bucket.limit = bucket.IRCLIMIT

            self.buckets[channel] = bucket

        return bucket


limiter = IRCLimiterMapping()


class Messageable(metaclass=abc.ABCMeta):

    __slots__ = ()

    __invalid__ = ('ban', 'unban', 'timeout', 'w', 'colour', 'color', 'mod',
                   'unmod', 'clear', 'subscribers', 'subscriberoff', 'slow', 'slowoff',
                   'r9k', 'r9koff', 'emoteonly', 'emoteonlyoff', 'host', 'unhost')

    @abc.abstractmethod
    def _get_channel(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def _get_socket(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _get_method(self):
        raise NotImplementedError

    async def send(self, content: str):
        """Send a message to the destination associated with the dataclass.

        Destination will either be a channel or user.
        Chat commands are not allowed to be invoked with this method.

        Parameters
        ------------
        content: str
            The content you wish to send as a message. The content must be a string.

        Raises
        --------
        TwitchIOBException
            Invalid destination.
        InvalidContent
            Invalid content.
        """
        content = str(content)

        channel, user = self._get_channel()
        method = self._get_method()

        if not channel:
            raise TwitchIOBException('Invalid channel for Messageable. Must be channel or user.')

        if len(content) > 500:
            raise InvalidContent('Length of message can not be > 500.')

        original = content

        if content.startswith('.') or content.startswith('/'):
            content = content.lstrip('.').lstrip('/')

            if content.startswith(self.__invalid__):
                raise InvalidContent('UnAuthorised chat command for send. Use built in method(s).')
            else:
                content = original

        ws = self._get_socket._websocket
        bot = self._get_socket._channel_cache[channel]['bot']

        if bot.is_mod:
            bucket = limiter.get_bucket(channel=channel, method='mod')
        else:
            bucket = limiter.get_bucket(channel=channel, method='irc')

        now = time.time()
        bucket.update()

        if bucket.limited:
            raise TwitchIOBException(f'IRC Message rate limit reached for channel <{channel}>.'
                                     f' Please try again in {bucket._reset - now:.2f}s')

        content = content.replace('\n', ' ')

        if method != 'User':
            await ws.send(f'PRIVMSG #{channel} :{content}\r\n')
        else:
            await ws.send(f'PRIVMSG #{channel} :.w {user} {content}\r\n')


