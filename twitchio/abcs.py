import abc
from .errors import *


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

        content = content.replace('\n', ' ')

        if method != 'User':
            await self._get_socket.send(f'PRIVMSG #{channel} :{content}\r\n')
        else:
            await self._get_socket.send(f'PRIVMSG #{channel} :.w {user} {content}\r\n')

