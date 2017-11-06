import abc
from .errors import InvalidContent


class Messageable(metaclass=abc.ABCMeta):

    __slots__ = ()

    _invalid = ('ban', 'unban', 'timeout', 'me', 'w', 'colour', 'color', 'mod',
                'unmod', 'clear', 'subscribers', 'subscriberoff', 'slow', 'slowoff',
                'r9k', 'r9koff', 'emoteonly', 'emoteonlyoff', 'host', 'unhost')

    @abc.abstractmethod
    async def _get_channel(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_writer(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_method(self):
        raise NotImplementedError

    async def send(self, content):

        channel, user = await self._get_channel()
        writer = await self._get_writer()
        method = await self._get_method()

        if not channel:
            raise InvalidContent('Invalid channel for Messageable. Must be channel or channel/user.')

        if len(content) > 500:
            raise InvalidContent('Length of message can not be > 500.')

        original = content

        if content.startswith('.'):
            content = content.lstrip('.')

        if content.startswith(self._invalid):
            raise InvalidContent('UnAuthorised chat command for send. Use built in method(s).')
        else:
            content = original

        content = content.replace('\n', ' ')

        if method != 'User':
            writer.write('PRIVMSG #{} :{}\r\n'.format(channel, content).encode('utf-8'))

        # Currently unavailable
        # writer.write('PRIVMSG #{} :.w {} {}\r\n'.format(channel, user, content).encode('utf-8'))

