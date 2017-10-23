import asyncio
import re
import logging
import sys, traceback

try:
    from socket import socketpair
except ImportError:
    from asyncio.windows_utils import socketpair

from .dataclasses import Context, User
from .errors import *


log = logging.getLogger(__name__)
# todo Actual logger


class BaseConnection:
    # todo Update Docstrings.
    """Base Connection class used for handling incoming and outgoing requests from Twitch."""

    def __init__(self, loop, host: str, port: int, nick: str, token: str, modes: (tuple, list), autojoin: bool=True):
        self.loop = loop
        self._host = host
        self._port = port
        self._nick = nick.lower()
        self._token = token
        self.channels = None

        self._reader = None
        self._writer = None
        self._is_connected = None
        self._is_ready = asyncio.Event()

        self.auto_join = autojoin
        self.modes = modes

        self.channel_cache = set()
        self._mod_token = 0
        self._channel_token = 0
        self._rate_status = None

        self.regex = {
            "data": re.compile(
                r"^(?:@(?P<tags>\S+)\s)?:(?P<data>\S+)(?:\s)"
                r"(?P<action>[A-Z]+)(?:\s#)(?P<channel>\S+)"
                r"(?:\s(?::)?(?P<content>.+))?"),
            "ping": re.compile("PING (?P<content>.+)"),
            "author": re.compile(
                "(?P<author>[a-zA-Z0-9_]+)!(?P=author)"
                "@(?P=author).tmi.twitch.tv"),
            "mode": re.compile("(?P<mode>[\+\-])o (?P<user>.+)"),
            "host": re.compile(
                "(?P<channel>[a-zA-Z0-9_]+) "
                "(?P<count>[0-9\-]+)"),
            'code': re.compile(r"tmi.twitch.tv (?P<code>[0-9]{3}) "), }

        self._groups = ('action', 'data', 'content', 'channel', 'author')

    @property
    def host(self):
        """The host address used to connect to Twitch."""
        return self._host

    @property
    def port(self):
        """The port used to connect to Twitch."""
        return self._port

    @property
    def nick(self):
        """The username used to connect to Twitch."""
        return self._nick

    async def auth_seq(self, channels):
        """An Automated Authentication process which provides Twitch
        with the given PASS and NICK.

        If Authentication is successful, we will attempt to join the provided channels. """

        self._writer.write("PASS {}\r\n".format(self._token).encode('utf-8'))
        self._writer.write("NICK {}\r\n".format(self.nick).encode('utf-8'))

        for mode in self.modes:
            self._writer.write(bytes("CAP REQ :twitch.tv/{}\r\n".format(mode), "UTF-8"))

        await self.join_channels(channels)

    async def send_auth(self):
        """Send an Authentication request to Twitch.
         Only useful if the Automated sequence was not used.
         """
        self._writer.write("PASS {}\r\n".format(self._token).encode('utf-8'))

    async def send_nick(self):
        """Send an NICK request to Twitch.
         Only useful if the Automated sequence was not used.
         """
        self._writer.write("NICK {}\r\n".format(self.nick).encode('utf-8'))

    async def _send_privmsg(self, channel, content):
        """Send a PRIVMSG to Twitch.

         Using this is unadvised.
         """
        content = content.replace("\n", " ")
        self._writer.write("PRIVMSG #{} :{}\r\n".format(channel, content).encode('utf-8'))

    async def join_channels(self, channels: (list, tuple)):

        for entry in channels:
            channel = re.sub('[#\s]', '', entry)
            self._writer.write("JOIN #{}\r\n".format(channel).encode('utf-8'))

            self.channel_cache.add(entry)

    async def _update_limit(self):

        while True:
            if self._mod_token == len(self.channel_cache):
                self._rate_status = 1
            else:
                self._rate_status = 0

            await asyncio.sleep(60)

    async def _token_update(self, user):
        if 'moderator/1' in user.badges:
            self._mod_token += 1
        else:
            if self._mod_token <= 0:
                return
            self._mod_token -= 1

        if self._mod_token == len(self.channel_cache):
            self._rate_status = 1
        else:
            self._rate_status = 0

    async def keep_alive(self, channels):
        # todo docstrings, other logic
        self._is_ready.clear()

        try:
            self._reader, self._writer = await asyncio.open_connection(self.host, self.port, loop=self.loop)
        except:
            raise HostConnectionFailure(self.host, self.port)
        else:
            self._is_connected = True
            self._is_ready.set()

        self.loop.create_task(self._update_limit())

        if self.auto_join:
            await self.auth_seq(channels)
        else:
            await self.send_auth()
            await self.send_nick()

        await self._is_ready.wait()
        await self.event_ready()

        while self._is_connected:
            data = (await self._reader.readline()).decode("utf-8").strip()
            if not data:
                await asyncio.sleep(0)
                continue
            try:
                await self.process_data(data)
            except Exception as e:
                await self.event_error(e.__class__.__name__)

    async def process_data(self, data):
        # todo docs, other logic

        await self.event_raw_data(data)

        try:
            code = int(self.regex['code'].match(data).group('code'))
        except:
            code = None

        if code == 376:
            print('\n\033[92mSuccessful Authentication: {0._host}:{0._port}\033[0m\n'.format(self))
            # todo logging

        elif data == ':tmi.twitch.tv NOTICE * :Login authentication failed':
            # todo Disconnection/Reconnection Logic.
            return

        _groupsdict = {}

        if data.startswith("PING"):
            match = self.regex["ping"]
        else:
            match = self.regex["data"]

        result = match.match(data)

        try:
            tags = result.group("tags")

            tagdict = {}
            for tag in str(tags).split(";"):
                t = tag.split("=")
                if t[1].isnumeric():
                    t[1] = int(t[1])
                tagdict[t[0]] = t[1]
            tags = tagdict
        except:
            tags = None

        for group in self._groups:
            try:
                res = result.group(group)
                _groupsdict[group] = res
            except:
                pass

        await self.process_actions(_groupsdict, tags)

    async def process_ping(self, resp):
            self._writer.write("PONG {}\r\n".format(resp).encode('utf-8'))

    async def process_actions(self, groups, tags=None):

        # todo add remaining actions, docs

        action = groups.pop('action', 'PING')
        data = groups.pop('data', None)
        content = groups.pop('content', None)
        channel = groups.pop('channel', None)

        try:
            author = self.regex["author"].match(data).group("author")
        except:
            author = None

        if action == 'RECONNECT':
            # TODO Disconnection/Reconnection Logic.
            return

        elif action == 'JOIN':
            user = User(author=author, channel=channel, tags=tags, _writer=self._writer)

            if author == self._nick:
                self.channel_cache.add(channel)
                self._channel_token += 1

            await self.event_join(user)

        elif action == 'PART':
            user = User(author=author, channel=channel, tags=tags, _writer=self._writer)

            if author == self._nick:
                self.channel_cache.remove(channel)
                self._channel_token -= 1

            await self.event_part(user)

        elif action == 'PING':
            await self.process_ping(content)

        elif action == 'PRIVMSG':
            user = User(author=author, channel=channel, tags=tags, _writer=self._writer)
            message = Context(author=user, content=content, channel=channel, raw_data=data, tags=tags,
                              _writer=self._writer)
            await self.event_message(message)

        elif action == 'USERSTATE':
            user = User(author=author, channel=channel, tags=tags, _writer=self._writer)
            try:
                user.display_name
            except AttributeError:
                pass
            else:
                if user.display_name.lower() == self._nick.lower():
                    await self._token_update(user)
            finally:
                await self.event_userstate(user)

    async def event_ready(self):
        pass

    async def event_error(self, error_name, *args, **kwargs):

        print('Ignoring exception in {}:'.format(error_name), file=sys.stderr)
        traceback.print_exc()

    async def event_raw_data(self, data):
        pass

    async def event_message(self, message):
        pass

    async def event_join(self, user):
        pass

    async def event_part(self, user):
        pass

    async def event_userstate(self, user):
        pass
