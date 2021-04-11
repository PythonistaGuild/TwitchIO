from typing import TYPE_CHECKING, Tuple, Dict, Type
from ...http import Route

if TYPE_CHECKING:
    from .server import EventSubClient
    from .models import EventData

class EventSubHTTP:
    URL = "https://api.twitch.tv/helix/eventsub/"

    def __init__(self, client: "EventSubClient"):
        self._client = client
        self._http = client.client._http

    async def create_subscription(self, event_type: Tuple[str, int, Type[EventData]], condition: Dict[str, str]):
        payload = {
            "type": event_type[0],
            "version": str(event_type[1]),
            "condition": condition,
            "transport": {
                "method": "webhook",
                "callback": self._client.route,
                "secret": self._client.secret
            }
        }
        route = Route("POST", self.URL + "subscriptions", body=payload)
        return await self._http.request(route)
