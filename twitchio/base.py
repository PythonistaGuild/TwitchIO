import asyncio
import aiohttp
import re
import logging
import sys, traceback

try:
    from socket import socketpair
except ImportError:
    from asyncio.windows_utils import socketpair

from .dataclasses import Message, User, Channel
from .http import HttpSession
from .errors import *

log = logging.getLogger(__name__)
# todo Actual logger


class BaseConnection:
    # todo Update Docstrings.
    """Base Connection class used for handling incoming and outgoing requests from Twitch."""

    def __init__(self, **kwargs):
        self.loop = kwargs.get('loop', asyncio.get_event_loop())
        self._host = kwargs.get('host', 'irc.chat.twitch.tv')
        self._port = kwargs.get('port', 6667)
        self._nick = kwargs.get('nick', '').lower()
        self._token = kwargs.get('token', None)
        self._api_token = kwargs.get('api_token', None)
        self._id = kwargs.get('client_id', None)
        self._integ = kwargs.get('integrated', False)
        self.channels = None

        self._reader = None
        self._writer = None
        self._is_connected = None
        self._is_ready = asyncio.Event()

        self.auto_join = kwargs.get('autojoin', True)
        self.modes = kwargs.get('modes', None)

        self.channel_cache = set()
        self._mod_token = 0
        self._channel_token = 0
        self._rate_status = None
        self._bot = kwargs.get('_bot', None)

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
            'code': re.compile(r":tmi\.twitch\.tv\s(?P<code>[0-9]{3}).*?"), }

        self._groups = ('action', 'data', 'content', 'channel', 'author')

        self.loop.create_task(self.async_init())

    async def async_init(self):
        self._http = HttpSession(session=aiohttp.ClientSession(loop=self.loop), apitok=self._api_token,
                                 cid=self._id)

    @property
    def host(self):
        """Host address used to connect the IRC Server."""
        return self._host

    @property
    def port(self):
        """Port used to connect to the IRC Server."""
        return self._port

    @property
    def nick(self):
        """Username used to connect to the IRC Server."""
        return self._nick

    async def auth_seq(self, channels=(list, tuple)):
        """|coro|

        Automated Authentication process.

        Attempts to authenticate on the Twitch servers with the provided
        nickname and IRC Token(pass).

        On successful authentication, an attempt to join the provided channels is made.

        Parameters
        ------------
        channels: list or tuple
            A list or tuple of channels to attempt joining.
        """

        self._writer.write("PASS {}\r\n".format(self._token).encode('utf-8'))
        self._writer.write("NICK {}\r\n".format(self.nick).encode('utf-8'))

        for mode in self.modes:
            self._writer.write(bytes("CAP REQ :twitch.tv/{}\r\n".format(mode), "UTF-8"))

        await self.join_channels(channels)

    async def send_auth(self):
        """|coro|

        Sends a PASS request to the Twitch IRC Endpoint.

        This should only be used if :func:`auth_seq` was not used.
        """
        self._writer.write("PASS {}\r\n".format(self._token).encode('utf-8'))

    async def send_nick(self):
        """|coro|

        Sends a NICK request to the Twitch IRC Endpoint.

        This should only be used if :func:`auth_seq` was not used.
        """
        self._writer.write("NICK {}\r\n".format(self.nick).encode('utf-8'))

    async def send_privmsg(self, channel, content):
        """|coro|

        Sends a PRIVMSG to the Twitch IRC Endpoint.

        This should only be used in rare circumstances where a :class:`twitchio.abcs.Messageable` is not available.
        """
        content = content.replace("\n", " ")
        self._writer.write("PRIVMSG #{} :{}\r\n".format(channel, content).encode('utf-8'))

    async def join_channels(self, channels: (list, tuple)):
        """|coro|

        Attempt to join the provided channels.

        Parameters
        ------------
        channels: list or tuple
            A list of channels to attempt joining.
        """

        for entry in channels:
            channel = re.sub('[#\s]', '', entry)
            self._writer.write("JOIN #{}\r\n".format(channel).encode('utf-8'))

    async def _update_limit(self):

        while True:
            if self._mod_token == len(self.channel_cache):
                self._rate_status = 1
            else:
                self._rate_status = 0

            await asyncio.sleep(60)

    async def _token_update(self, status):
        if '+o' in status:
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

        while self._is_connected:
            data = (await self._reader.readline()).decode("utf-8").strip()
            if not data:
                continue
            try:
                await self.process_data(data)
            except Exception as e:
                await self.event_error(e.__class__.__name__)

    async def process_data(self, data):
        await self.event_raw_data(data)

        try:
            code = int(self.regex['code'].match(data).group('code'))
        except AttributeError:
            code = None

        if code == 376:
            await self.event_ready()
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
        except (AttributeError, IndexError, KeyError):
            tags = None

        for group in self._groups:
            try:
                res = result.group(group)
                _groupsdict[group] = res
            except (AttributeError, KeyError, IndexError):
                pass

        await self.process_actions(data, _groupsdict, tags)

    async def process_ping(self, resp):
            self._writer.write("PONG {}\r\n".format(resp).encode('utf-8'))

    async def process_actions(self, raw, groups, tags=None):

        # todo add remaining actions, docs

        action = groups.pop('action', 'PING')
        data = groups.pop('data', None)
        content = groups.pop('content', None)
        channel = groups.pop('channel', None)

        try:
            author = self.regex["author"].match(data).group("author")
        except:
            author = None

        if channel:
            channel = Channel(name=channel, _writer=self._writer, _http=self._http)

        try:
            user = User(author=author, channel=channel, tags=tags, _writer=self._writer)
        except (TypeError, KeyError):
            user = None

        try:
            message = Message(author=user, content=content, channel=channel, raw_data=data, tags=tags,
                              _writer=self._writer)
        except (TypeError, KeyError):
            message = None

        if action == 'RECONNECT':
            # TODO Disconnection/Reconnection Logic.
            return

        elif action == 'JOIN':
            if author == self._nick:
                self.channel_cache.add(channel.name)
                self._channel_token += 1

            await self.event_join(user)

        elif action == 'PART':
            if author == self._nick:
                self.channel_cache.remove(channel.name)
                self._channel_token -= 1

            await self.event_part(user)

        elif action == 'PING':
            await self.process_ping(content)

        elif action == 'PRIVMSG':
            await self.event_message(message)

            # TODO Handle this differently
            if self._bot:
                await self._bot.process_commands(message, channel, user)

        elif action == 'USERSTATE':
            await self.event_userstate(user)

        elif action == 'MODE':
            mdata = re.match(r':jtv MODE #(?P<channel>.+?[a-z0-9])\s(?P<status>[\+\-]o)\s(?P<user>.*[a-z0-9])', raw)
            mstatus = mdata.group('status')

            user = User(author=mdata.group('user'), channel=channel, tags=tags, _writer=self._writer)

            if user._name.lower() == self._nick.lower():
                await self._token_update(mstatus)

            await self.event_mode(channel, user, mstatus)

    async def event_ready(self):
        """|coro|

        Event called when the :class:`.Client` has successfully authenticated
        on the Twitch server.
        """

        print('\033[92mSuccessful Authentication: {0._host}:{0._port}\033[0m'.format(self))

    async def event_error(self, error_name, *args, **kwargs):
        """|coro|

        Default error handler for the TwitchIO Client.

        This could be overridden to implement custom error handling.
        """

        print('Ignoring exception in {}:'.format(error_name), file=sys.stderr)
        traceback.print_exc()

    async def event_raw_data(self, data):
        """|coro|

        Event called when any message or notification is received from Twitch.

        This should be used sparingly, and only when needed, as the client already aims to break
        this down for you.

        Parameters
        ------------
        data: str
            The raw data received from Twitch. Decoded as UTF-8.
        """
        pass

    async def event_message(self, message):
        """|coro|

        Event called when a PRIVMSG is received from Twitch.

        Parameters
        ------------
        message: :class:`.Message`
            Message object containing relevant information.
        """
        pass

    async def event_join(self, user):
        """|coro|

        Event called when a JOIN is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the JOIN.
        """
        pass

    async def event_part(self, user):
        """|coro|

        Event called when a PART is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the PART.
        """
        pass

    async def event_userstate(self, user):
        """|coro|

        Event called when a USERSTATE is received from Twitch.

        Parameters
        ------------
        user: :class:`.User`
            User object containing relevant information to the USERSTATE.
        """
        pass

    async def event_mode(self, channel, user, status):
        """|coro|

        Event called when a MODE is received from Twitch.

        Parameters
        ------------
        channel: :class:`.Channel`
            Channel object relevant to the MODE event.
        user: :class:`.User`
            User object containing relevant information to the MODE.
        status: str
            The JTV status received by Twitch. Could be either o+ or o-.
            Indicates a moderation promotion/demotion to the :class:`.User`
        """
        pass
