from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Type, Union, Optional
from ...http import Route

from . import models

if TYPE_CHECKING:
    from .server import EventSubClient
    from .models import EventData, Subscription

__all__ = ("EventSubHTTP",)


class EventSubHTTP:
    def __init__(self, client: EventSubClient, token: Optional[str]):
        self._client = client
        self._http = client.client._http
        self._token = token

    async def create_subscription(self, event_type: Tuple[str, int, Type[EventData]], condition: Dict[str, str]):
        payload = {
            "type": event_type[0],
            "version": str(event_type[1]),
            "condition": condition,
            "transport": {"method": "webhook", "callback": self._client.route, "secret": self._client.secret},
        }
        route = Route("POST", "eventsub/subscriptions", body=payload, token=self._token)
        return await self._http.request(route, paginate=False, force_app_token=True)

    async def delete_subscription(self, substription: Union[str, Subscription]):
        if isinstance(substription, models.Subscription):
            return await self._http.request(
                Route("DELETE", "eventsub/subscriptions", query=[("id", substription.id)]), paginate=False
            )
        return await self._http.request(
            Route("DELETE", "eventsub/subscriptions", query=[("id", substription)]), paginate=False
        )

    async def get_subscriptions(self, status: str = None):
        qs = []
        if status:
            qs.append(("status", status))

        return [
            models.Subscription(d)
            for d in await self._http.request(Route("GET", "eventsub/subscriptions", query=qs), paginate=False)
        ]

    async def get_status(self, status: str = None):
        qs = []
        if status:
            qs.append(("status", status))

        v = await self._http.request(Route("GET", "eventsub/subscriptions", query=qs), paginate=False, full_body=True)
        del v["data"]
        del v["pagination"]
        return v
