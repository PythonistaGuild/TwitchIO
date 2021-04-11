import logging

from aiohttp import web

from ... import Client
from . import models

__all__ = (
    "EventSubClient",
)

logger = logging.getLogger("twitchio.ext.eventsub")

_message_types = {
    "webhook_callback_verification": models.ChallengeEvent,
    "notification": models.NotificationEvent,
    "revokation": models.RevokationEvent
}


class EventSubClient(web.Application):
    def __init__(self, client: Client):
        self.client = client
        self.secret: str = None
        self.route: str = None
        super(EventSubClient, self).__init__()

    async def _callback(self, request: web.Request) -> web.Response:
        payload = await request.text()
        typ = request.headers.get("Twitch-Eventsub-Message-Type", "")
        if not typ:
            return web.Response(status=404)

        if typ not in _message_types:
            logger.warning(f"Unexpected message typ: {typ}")
            return web.Response(status=400)

        event = _message_types[typ](self, payload, request)
        response = event.verify()

        if typ == "notification":
            self.client.run_event(f"eventsub_notification_{models.SubscriptionTypes._name_map[event.subscription.type]}", event)
        elif typ == "revokation":
            self.client.run_event("eventsub_revokation", event)

        return response
