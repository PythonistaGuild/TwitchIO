from __future__ import annotations

import asyncio
import logging

import aiohttp
from typing import Optional, TYPE_CHECKING, Tuple, Type, Dict, Callable, Generic, TypeVar, Awaitable, Union, cast, List
from . import models, http
from .models import _loads
from twitchio import PartialUser

if TYPE_CHECKING:
    from twitchio import Client

logger = logging.getLogger("twitchio.ext.eventsub.ws")

_message_types = {
    "notification": models.NotificationEvent,
    "revocation": models.RevokationEvent,
    "reconnect": models.ReconnectEvent,
    "session_keepalive": models.KeepAliveEvent
}
_messages = Union[models.NotificationEvent, models.RevokationEvent, models.ReconnectEvent, models.KeepAliveEvent]


class _Subscription:
    __slots__ = "event", "condition", "token", "subscription_id", "cost"
    def __init__(self, event_type: Tuple[str, int, Type[models.EventData]], condition: Dict[str, str], token: str):
        self.event = event_type
        self.condition = condition
        self.token = token
        self.subscription_id: Optional[str] = None
        self.cost: Optional[int] = None

_T = TypeVar("_T")

class _WakeupList(list, Generic[_T]):
    def __init__(self, *args):
        super().__init__(*args)
        self._append_waiters = []
        self._pop_waiters = []

    def _wakeup_append(self, obj: _T) -> None:
        try:
            loop = asyncio.get_running_loop()
            for cb in self._append_waiters:
                loop.create_task(cb(obj))
        except: # don't wake the waiters if theres no loop
            pass

    def _wakeup_pop(self, obj: _T) -> None:
        try:
            loop = asyncio.get_running_loop()
            for cb in self._pop_waiters:
                loop.create_task(cb(obj))
        except: # don't wake the waiters
            pass

    def append(self, obj: _T) -> None:
        self._wakeup_append(obj)
        super().append(obj)

    def insert(self, index: int, obj: _T) -> None:
        self._wakeup_append(obj)
        super().insert(index, obj)

    def __delitem__(self, key: int):
        self._wakeup_pop(self[key])
        super().__delitem__(key)

    def pop(self, index: int = ...) -> _T:
        resp = super().pop(index)
        self._wakeup_pop(resp)
        return resp

    def add_append_callback(self, cb: Callable[[_T], Awaitable[None]]) -> None:
        self._append_waiters.append(cb)

    def add_pop_callback(self, cb: Callable[[_T], Awaitable[None]]) -> None:
        self._pop_waiters.append(cb)


class Websocket:
    URL = "wss://eventsub.wss.twitch.tv/ws"

    def __init__(self, client: Client, http: http.EventSubHTTP):
        self.client = client
        self._http = http
        self._subscription_pool = _WakeupList[_Subscription]()
        self._subscription_pool.add_append_callback(self._wakeup_and_connect)
        self._sock: Optional[aiohttp.ClientWebSocketResponse] = None
        self._pump_task: Optional[asyncio.Task] = None
        self._timeout: Optional[int] = None
        self._session_id: Optional[str] = None

        self.remaining_slots: int = 100 # default to 100

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def is_connected(self) -> bool:
        return self._sock is not None and not self._sock.closed

    async def _subscribe(self, obj: _Subscription) -> dict:
        resp = await self._http.create_websocket_subscription(obj.event, obj.condition, self._session_id, obj.token)
        data = resp["data"][0]
        cost = data["cost"]
        self.remaining_slots = resp["total_cost"] - resp["max_total_cost"] # FIXME: twitch is pretty vague about these, check back on their values later
        obj.cost = cost

        return data

    def add_subscription(self, sub: _Subscription) -> None:
        self._subscription_pool.append(sub)

    async def _wakeup_and_connect(self, obj: _Subscription):
        if self.is_connected:
            await self._subscribe(obj)
            return

    async def connect(self, reconnect_url: Optional[str] = None):
        if not self._subscription_pool:
            return # TODO: should this raise?

        async with aiohttp.ClientSession() as session:
            sock = self._sock = await session.ws_connect(reconnect_url or self.URL)
            session.detach()

        welcome = await sock.receive_json(loads=_loads, timeout=3)
        logger.debug("Received websocket payload: %s", welcome)
        self._session_id = welcome["payload"]["session"]["id"]
        self._timeout = welcome["payload"]["session"]["keepalive_timeout_seconds"]

        logger.debug("Created websocket connection with session ID: %s and timeout %s", self._session_id, self._timeout)

        self._pump_task = self.client.loop.create_task(self.pump())

        if reconnect_url: # don't resubscribe to events
            return

        for sub in self._subscription_pool:
            await self._subscribe(sub) # TODO: how do I return this to the end user (do I bother?)

    async def pump(self) -> None:
        while self.is_connected:
            try:
                msg = await cast(aiohttp.ClientWebSocketResponse, self._sock).receive_str(timeout=self._timeout+1) # extra jitter on the timeout in case of network lag
                if not msg:
                    continue # TODO: should this raise?

                logger.debug("Received websocket payload: %s", msg)
                frame: _messages = self.parse_frame(_loads(msg))
                self.client.run_event("eventsub_debug", frame)

                if isinstance(frame, models.NotificationEvent):
                    self.client.run_event(
                        f"eventsub_notification_{models.SubscriptionTypes._name_map[frame.subscription.type]}", frame
                    )
                    self.client.run_event("eventsub_notification", frame)

                elif isinstance(frame, models.RevokationEvent):
                    self.client.run_event("eventsub_revokation", frame)

                elif isinstance(frame, models.KeepAliveEvent):
                    self.client.run_event("eventsub_keepalive", frame)

                elif isinstance(frame, models.ReconnectEvent):
                    self.client.run_event("eventsub_reconnect", frame)
                    sock = self._sock
                    self._sock = None
                    await self.connect(frame.reconnect_url)
                    await cast(aiohttp.ClientWebSocketResponse, sock).close(code=aiohttp.WSCloseCode.GOING_AWAY, message=b"reconnecting")
                    return

            except asyncio.TimeoutError:
                logger.warning(f"Websocket timed out (timeout: {self._timeout}), reconnecting")
                await cast(aiohttp.ClientWebSocketResponse, self._sock).close(code=aiohttp.WSCloseCode.ABNORMAL_CLOSURE, message=b"timeout surpassed")
                await self.connect()
                return

            except Exception as e:
                logger.error("Exception in the pump function!", exc_info=e)

    def parse_frame(self, frame: dict) -> _messages:
        type_: str = frame["metadata"]["message_type"]
        return _message_types[type_](self, frame, None)


class EventSubWSClient:
    def __init__(self, client: Client):
        self.client = client
        self._http: http.EventSubHTTP = http.EventSubHTTP(self, token=None)

        self._sockets: List[Websocket] = []

    async def start(self):
        for socket in self._sockets:
            await socket.connect()

    def _assign_subscription(self, sub: _Subscription) -> None:
        if not self._sockets:
            self._sockets.append(Websocket(self.client, self._http))

        for s in self._sockets:
            if s.remaining_slots > 0:
                s.add_subscription(sub)
                return

        raise RuntimeError("No available sockets :(")

    def subscribe_user_updated(self, user: Union[PartialUser, str, int], token: str):
        if isinstance(user, PartialUser):
            user = user.id

        user = str(user)
        sub = _Subscription(models.SubscriptionTypes.user_update, {"user_id": user}, token)
        self._assign_subscription(sub)

    def subscribe_channel_raid(
        self, token: str, from_broadcaster: Union[PartialUser, str, int] = None, to_broadcaster: Union[PartialUser, str, int] = None
    ):
        if (not from_broadcaster and not to_broadcaster) or (from_broadcaster and to_broadcaster):
            raise ValueError("Expected 1 of from_broadcaster or to_broadcaster")

        if from_broadcaster:
            who = "from_broadcaster_user_id"
            broadcaster = from_broadcaster
        else:
            who = "to_broadcaster_user_id"
            broadcaster = to_broadcaster

        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id

        broadcaster = str(broadcaster)
        sub = _Subscription(models.SubscriptionTypes.raid, {who: broadcaster}, token)
        self._assign_subscription(sub)

    def _subscribe_channel_points_reward(
        self, event: Tuple[str, int, Type[models._DataType]], broadcaster: Union[PartialUser, str, int], token: str, reward_id: str = None
    ):
        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id

        broadcaster = str(broadcaster)
        data = {"broadcaster_user_id": broadcaster}
        if reward_id:
            data["reward_id"] = reward_id

        sub = _Subscription(event, data, token)
        self._assign_subscription(sub)

    def _subscribe_with_broadcaster(
        self, event: Tuple[str, int, Type[models._DataType]], broadcaster: Union[PartialUser, str, int], token: str
    ):
        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id

        broadcaster = str(broadcaster)
        sub = _Subscription(event, {"broadcaster_user_id": broadcaster}, token)
        self._assign_subscription(sub)
    
    def _subscribe_with_broadcaster_moderator(
        self,
        event: Tuple[str, int, Type[models._DataType]],
        broadcaster: Union[PartialUser, str, int],
        moderator: Union[PartialUser, str, int],
        token: str
    ):
        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id
        if isinstance(moderator, PartialUser):
            moderator = moderator.id

        broadcaster = str(broadcaster)
        moderator = str(moderator)
        sub = _Subscription(event, {"broadcaster_user_id": broadcaster, "moderator_user_id": moderator}, token)
        self._assign_subscription(sub)


    def subscribe_channel_bans(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.ban, broadcaster, token)

    def subscribe_channel_unbans(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.unban, broadcaster, token)

    def subscribe_channel_subscriptions(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription, broadcaster, token)

    def subscribe_channel_subscription_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription_end, broadcaster, token)

    def subscribe_channel_subscription_gifts(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription_gift, broadcaster, token)

    def subscribe_channel_subscription_messages(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription_message, broadcaster, token)

    def subscribe_channel_cheers(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.cheer, broadcaster, token)

    def subscribe_channel_update(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_update, broadcaster, token)

    def subscribe_channel_follows(self, broadcaster: Union[PartialUser, str, int], token: str):
        raise RuntimeError("This subscription has been removed by twitch, please use subscribe_channel_follows_v2")

    def subscribe_channel_follows_v2(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        return self._subscribe_with_broadcaster_moderator(models.SubscriptionTypes.followV2, broadcaster, moderator, token)

    def subscribe_channel_moderators_add(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_moderator_add, broadcaster, token)

    def subscribe_channel_moderators_remove(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_moderator_remove, broadcaster, token)

    def subscribe_channel_goal_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_goal_begin, broadcaster, token)

    def subscribe_channel_goal_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_goal_progress, broadcaster, token)

    def subscribe_channel_goal_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_goal_end, broadcaster, token)

    def subscribe_channel_hypetrain_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.hypetrain_begin, broadcaster, token)

    def subscribe_channel_hypetrain_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.hypetrain_progress, broadcaster, token)

    def subscribe_channel_hypetrain_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.hypetrain_end, broadcaster, token)

    def subscribe_channel_stream_start(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.stream_start, broadcaster, token)

    def subscribe_channel_stream_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.stream_end, broadcaster, token)

    def subscribe_channel_points_reward_added(self, broadcaster: Union[PartialUser, str, int], reward_id: str, token: str):
        return self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_add, broadcaster, token, reward_id
        )

    def subscribe_channel_points_reward_updated(self, broadcaster: Union[PartialUser, str, int], reward_id: str, token: str):
        return self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_update, broadcaster, token, reward_id
        )

    def subscribe_channel_points_reward_removed(self, broadcaster: Union[PartialUser, str, int], reward_id: str, token: str):
        return self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_remove, broadcaster, token, reward_id
        )

    def subscribe_channel_points_redeemed(self, broadcaster: Union[PartialUser, str, int], token: str, reward_id: str = None):
        return self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_redeem, broadcaster, token, reward_id
        )

    def subscribe_channel_points_redeem_updated(self, broadcaster: Union[PartialUser, str, int], token: str, reward_id: str = None):
        return self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_redeem_updated, broadcaster, token, reward_id
        )

    def subscribe_channel_poll_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.poll_begin, broadcaster, token)

    def subscribe_channel_poll_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.poll_progress, broadcaster, token)

    def subscribe_channel_poll_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.poll_end, broadcaster, token)

    def subscribe_channel_prediction_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_begin, broadcaster, token)

    def subscribe_channel_prediction_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_progress, broadcaster, token)

    def subscribe_channel_prediction_lock(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_lock, broadcaster, token)

    def subscribe_channel_prediction_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        return self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_end, broadcaster, token)

    
    def subscribe_channel_shield_mode_begin(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        return self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shield_mode_begin, broadcaster, moderator, token
        )

    def subscribe_channel_shield_mode_end(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        return self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shield_mode_end, broadcaster, moderator, token
        )

    def subscribe_channel_shoutout_create(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        return self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shoutout_create, broadcaster, moderator, token
        )

    def subscribe_channel_shoutout_receive(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        return self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shoutout_receive, broadcaster, moderator, token
        )
