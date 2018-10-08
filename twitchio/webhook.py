import asyncio
import json
import uuid

from aiohttp import web

from twitchio.errors import TwitchHTTPException


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
