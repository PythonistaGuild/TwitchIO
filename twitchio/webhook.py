import asyncio
import json
import uuid

from aiohttp import web

from twitchio.errors import TwitchHTTPException


__all__ = (
    'WebhookTopic', 'UserFollows', 'StreamChanged', 'UserChanged', 'GameAnalytics', 'ExtensionAnalytics',
    'TwitchWebhookServer'
)


class TwitchWebhookServer:

    def __init__(self, *, bot, local: str, external, port: int, callback: str=None):
        self._bot = bot
        self.local = local
        self.external = external
        self.port = port
        self.callback = callback or uuid.uuid4().hex
        self.app = web.Application()
        self.app.add_routes([web.get(f'/{self.callback}', self.handle_callback),
                             web.post(f'/{self.callback}', self.handle_callback_post)])

        self.loop = None

    def run_server(self, loop):
        asyncio.set_event_loop(loop)
        self.loop = loop

        handler = self.app.make_handler()
        server = loop.create_server(handler, host=self.local, port=self.port)

        loop.run_until_complete(server)
        loop.run_forever()

    async def handle_callback_post(self, request):
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.Response(text='Bad Request', status=400)

        asyncio.run_coroutine_threadsafe(self._bot.event_webhook(data), loop=self.loop)

        return web.Response(text='200: OK', status=200)

    async def handle_callback(self, request):
        query = request.query

        try:
            if query['hub.mode'] == 'denied':
                asyncio.run_coroutine_threadsafe(self._bot._ws.event_error(
                    TwitchHTTPException(f'Webhook subscription denied | {query["hub.reason"]}')), loop=self.loop)
                return web.Response(text='200: OK', status=200)

            if query['hub.challenge']:
                asyncio.run_coroutine_threadsafe(self._bot.event_webhook(query), loop=self.loop)
                return web.Response(body=query['hub.challenge'],
                                    content_type='application/json')
        except KeyError:
            web.Response(text='Bad Request', status=400)

        return web.Response(text='200: OK', status=200)


class WebhookTopic:
    URL = None

    __slots__ = ()

    @property
    def parameters(self):
        return [x for x in self.__slots__ if getattr(self, x, None) is not None]

    def as_uri(self):
        params = '&'.join(f'{name}={getattr(self, name)}' for name in self.parameters)
        return f'{self.URL}?{params}'


class UserFollows(WebhookTopic):
    URL = 'https://api.twitch.tv/helix/users/follows'

    __slots__ = ('first', 'from_id', 'to_id')

    def __init__(self, first=1, from_id=None, to_id=None):
        self.first = first
        self.from_id = from_id
        self.to_id = to_id


class StreamChanged(WebhookTopic):
    URL = 'https://api.twitch.tv/helix/streams'

    __slots__ = ('user_id',)

    def __init__(self, user_id):
        self.user_id = user_id


class UserChanged(WebhookTopic):
    URL = 'https://api.twitch.tv/helix/users'

    __slots__ = ('id',)

    def __iter__(self, id):
        self.id = id


class GameAnalytics(WebhookTopic):
    URL = 'https://api.twitch.tv/helix/analytics/games'

    __slots__ = ('game_id',)

    def __int__(self, game_id):
        self.game_id = game_id


class ExtensionAnalytics(WebhookTopic):
    URL = 'https://api.twitch.tv/helix/analytics/extensions'

    __slots__ = ('extension_id',)

    def __init__(self, extension_id):
        self.extension_id = extension_id
