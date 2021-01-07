# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

__all__ = (
    'Topic',
    'UserFollows',
    'StreamChanged',
    'UserChanged',
    'GameAnalytics',
    'ExtensionAnalytics',
    'TwitchWebhookServer',
)


import abc
import asyncio
import json
import uuid

from aiohttp import web

from twitchio.errors import HTTPException


class TwitchWebhookServer:

    def __init__(self, *, bot, local: str, external: str, port: int, callback: str=None):
        self._bot = bot
        self.local = local
        self.external = external
        self.port = port
        self.callback = callback or uuid.uuid4().hex
        self.app = web.Application()
        self.app.add_routes([web.get(f'/{self.callback}', self.handle_callback),
                             web.post(f'/{self.callback}', self.handle_callback_post)])

        self.loop = None

    def stop(self):
        self.loop.stop()

    def run_server(self, loop: asyncio.BaseEventLoop):
        asyncio.set_event_loop(loop)
        self.loop = loop

        handler = self.app.make_handler()
        server = loop.create_server(handler, host=self.local, port=self.port)

        loop.run_until_complete(server)
        loop.run_forever()

    async def handle_callback_post(self, request) -> web.Response:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.Response(text='Bad Request', status=400)

        asyncio.run_coroutine_threadsafe(self._bot.event_webhook(data), loop=self.loop)

        return web.Response(text='200: OK', status=200)

    async def handle_callback(self, request) -> web.Response:
        query = request.query

        try:
            if query['hub.mode'] == 'denied':
                asyncio.run_coroutine_threadsafe(self._bot._ws.event_error(
                    HTTPException(f'Webhook subscription denied | {query["hub.reason"]}')), loop=self.loop)
                return web.Response(text='200: OK', status=200)

            if query['hub.challenge']:
                asyncio.run_coroutine_threadsafe(self._bot.event_webhook(query), loop=self.loop)
                return web.Response(body=query['hub.challenge'],
                                    content_type='application/json')
        except KeyError:
            web.Response(text='Bad Request', status=400)

        return web.Response(text='200: OK', status=200)


class Topic(abc.ABC):
    """
    Represents a Topic which can be used to modify a Webhook subscription.

    .. note::
        You can not create an instance of this class, use one of the derived ones instead.
    """

    URL = None

    __slots__ = ()

    @property
    def _parameters(self):
        return [x for x in self.__slots__ if getattr(self, x) is not None]

    def as_uri(self):
        """
        Converts the Topic into the URI which can be used to create a Webhook subscription.

        Returns
        -------
        str
            The Topic as an URI.
        """

        params = '&'.join(f'{name}={getattr(self, name)}' for name in self._parameters)
        return f'{self.URL}?{params}'


class UserFollows(Topic):
    """
    This Topic notifies you whenever a user follows someone or someone is being followed.

    Parameters
    ----------
    first: Optional[int]
        This needs to be 1. Please see the Twitch documentation for more information.
    from_id: Optional[int]
        User ID for the user that's following other Twitch channels.
    to_id: Optional[int]
        User ID for the channel that other Twitch users follow.

    Raises
    ------
    TypeError
        Neither the `from_id` or `to_id` parameter were given.
    """

    URL = 'https://api.twitch.tv/helix/users/follows'

    __slots__ = ('first', 'from_id', 'to_id')

    def __init__(self, *, first=1, from_id=None, to_id=None):
        self.first = first

        if from_id is None and to_id is None:
            raise TypeError('Missing either "from_id" or "to_id" argument.')

        self.from_id = from_id
        self.to_id = to_id


class StreamChanged(Topic):
    """
    This Topic notifies you whenever a Stream starts, is modified or stops.

    Parameters
    ----------
    user_id: int
        The channel to receive notifications for.
    """

    URL = 'https://api.twitch.tv/helix/streams'

    __slots__ = ('user_id',)

    def __init__(self, user_id):
        self.user_id = user_id


class UserChanged(Topic):
    """
    This Topic notifies you whenever a user updates their profile.

    Parameters
    ----------
    user_id: int
        The user to receive information for.
    """

    URL = 'https://api.twitch.tv/helix/users'

    __slots__ = ('id',)

    def __init__(self, user_id):
        self.id = user_id


class GameAnalytics(Topic):
    """
    This Topic notifies you whenever a new game analytics report is available.

    .. note::
        This Topic requires the `analytics:read:games` OAuth scope.

    Parameters
    ----------
    game_id: int
        The game to receive notifications for.
    """

    URL = 'https://api.twitch.tv/helix/analytics/games'

    __slots__ = ('game_id',)

    def __init__(self, game_id):
        self.game_id = game_id


class ExtensionAnalytics(Topic):
    """
    This Topic notifies you whenever a new extension analytics report is available.

    ..note ::
        This Topic requires the `analytics:read:extensions` OAuth scope.

    Parameters
    ----------
    extension_id: int
        The extension to receive notifications for.
    """

    URL = 'https://api.twitch.tv/helix/analytics/extensions'

    __slots__ = ('extension_id',)

    def __init__(self, extension_id):
        self.extension_id = extension_id
