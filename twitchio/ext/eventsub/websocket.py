from __future__ import annotations

import asyncio
import logging

import aiohttp
from typing import Optional, TYPE_CHECKING, Tuple, Type, Dict, Callable, Generic, TypeVar, Awaitable, Union, cast, List
from . import models, http
from .models import _loads
from twitchio import PartialUser, Unauthorized, HTTPException

if TYPE_CHECKING:
    from typing_extensions import Literal
    from twitchio import Client

logger = logging.getLogger("twitchio.ext.eventsub.ws")

_message_types = {
    "notification": models.NotificationEvent,
    "revocation": models.RevokationEvent,
    "session_reconnect": models.ReconnectEvent,
    "session_keepalive": models.KeepAliveEvent,
}
_messages = Union[models.NotificationEvent, models.RevokationEvent, models.ReconnectEvent, models.KeepAliveEvent]


class _Subscription:
    __slots__ = "event", "condition", "token", "subscription_id", "cost", "created"

    def __init__(self, event_type: Tuple[str, int, Type[models.EventData]], condition: Dict[str, str], token: str):
        self.event = event_type
        self.condition = condition
        self.token = token
        self.subscription_id: Optional[str] = None
        self.cost: Optional[int] = None
        self.created: asyncio.Future[Tuple[Literal[False], int] | Tuple[Literal[True], None]] | None = asyncio.Future()


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
        except:  # don't wake the waiters if theres no loop
            pass

    def _wakeup_pop(self, obj: _T) -> None:
        try:
            loop = asyncio.get_running_loop()
            for cb in self._pop_waiters:
                loop.create_task(cb(obj))
        except:  # don't wake the waiters
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
        self._target_user_id: int | None = None  # each websocket can only have one authenticated user on it for some bizzare reason, but this isnt documented anywhere
        self.remaining_slots: int = 300  # default to 300

    def __hash__(self) -> int:
        return hash(self.session_id)

    def __eq__(self, __value: object) -> bool:
        return __value is self

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def is_connected(self) -> bool:
        return self._sock is not None and not self._sock.closed

    async def _subscribe(self, obj: _Subscription) -> dict | None:
        try:
            resp = await self._http.create_websocket_subscription(obj.event, obj.condition, self._session_id, obj.token)
        except HTTPException as e:
            if obj.created:
                obj.created.set_result((False, e.status))

            else:
                logger.error(
                    "An error (%s %s) occurred while attempting to resubscribe to an event on reconnect: %s",
                    e.status,
                    e.reason,
                    e.message,
                )

            return None

        if obj.created:
            obj.created.set_result((True, None))

        data = resp["data"][0]
        self.remaining_slots = resp["max_total_cost"] - resp["total_cost"]
        obj.cost = data["cost"]

        return data

    def add_subscription(self, sub: _Subscription) -> None:
        self._subscription_pool.append(sub)

    async def _wakeup_and_connect(self, obj: _Subscription):
        if self.is_connected:
            await self._subscribe(obj)
            return

    async def connect(self, reconnect_url: Optional[str] = None):
        async with aiohttp.ClientSession() as session:
            sock = self._sock = await session.ws_connect(reconnect_url or self.URL)
            session.detach()

        welcome = await sock.receive_json(loads=_loads, timeout=3)
        logger.debug("Received websocket payload: %s", welcome)
        self._session_id = welcome["payload"]["session"]["id"]
        self._timeout = welcome["payload"]["session"]["keepalive_timeout_seconds"]

        logger.debug("Created websocket connection with session ID: %s and timeout %s", self._session_id, self._timeout)

        self._pump_task = self.client.loop.create_task(self.pump())

        if reconnect_url:  # don't resubscribe to events
            return

        for sub in self._subscription_pool:
            await self._subscribe(sub)

    async def pump(self) -> None:
        sock: aiohttp.ClientWebSocketResponse = cast(aiohttp.ClientWebSocketResponse, self._sock)
        while self.is_connected:
            try:
                msg = await sock.receive_str(
                    timeout=self._timeout + 1
                )  # extra jitter on the timeout in case of network lag
                if not msg:
                    logger.warning("Received empty payload ")

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
                    self._sock = None
                    await self.connect(frame.reconnect_url)
                    await sock.close(code=aiohttp.WSCloseCode.GOING_AWAY, message=b"reconnecting")
                    return

            except asyncio.TimeoutError:
                logger.warning(f"Websocket timed out (timeout: {self._timeout}), reconnecting")
                await cast(aiohttp.ClientWebSocketResponse, self._sock).close(
                    code=aiohttp.WSCloseCode.ABNORMAL_CLOSURE, message=b"timeout surpassed"
                )
                await self.connect()
                return

            except TypeError as e:
                logger.warning(f"Received bad frame: {e.args[0]}")

                if "257" in e.args[0]:  # websocket was closed, reconnect
                    logger.info("Known bad frame, restarting connection")
                    await self.connect()
                    return

            except Exception as e:
                logger.error("Exception in the pump function!", exc_info=e)
                raise

    def parse_frame(self, frame: dict) -> _messages:
        type_: str = frame["metadata"]["message_type"]
        return _message_types[type_](self, frame, None)


class EventSubWSClient:
    def __init__(self, client: Client):
        self.client = client
        self._http: http.EventSubHTTP = http.EventSubHTTP(self, token=None)

        self._sockets: List[Websocket] = []
        self._ready_to_subscribe: List[_Subscription] = []

    async def _assign_subscription(self, sub: _Subscription) -> None:
        if not self._sockets:
            w = Websocket(self.client, self._http)
            await w.connect()

            self._sockets.append(w)

        success = False
        bad_sockets: set[Websocket] | None = None  # dont allocate unless we need it

        while not success:
            s: Websocket | None = None  # really it'll never be none after this point, but ok pyright

            if bad_sockets is not None:
                socks = filter(lambda sock: sock not in bad_sockets, self._sockets)  # type: ignore
            else:
                socks = self._sockets

            for s in socks:
                if s.remaining_slots > 0:
                    s.add_subscription(sub)
                    break

            else:  # there are no sockets, create one and break
                s = Websocket(self.client, self._http)
                await s.connect()

                s.add_subscription(sub)
                return

            assert sub.created is not None  # go away pyright

            success, status = await sub.created

            if not success and status == 400:
                # can't be on that socket due to someone else being on it, try again on a different one
                if bad_sockets is None:
                    bad_sockets = set()

                bad_sockets.add(s)
                sub.created = asyncio.Future()
                continue

            elif not success and status in (401, 403):
                raise Unauthorized("You are not authorized to make this subscription", status=status)

            elif not success:
                raise RuntimeError(f"Subscription failed, reason unknown. Status: {status}")

            else:
                sub.created = None  # don't need that future to sit in memory
                break

    async def subscribe_user_updated(self, user: Union[PartialUser, str, int], token: str):
        if isinstance(user, PartialUser):
            user = user.id

        user = str(user)
        sub = _Subscription(models.SubscriptionTypes.user_update, {"user_id": user}, token)
        await self._assign_subscription(sub)

    async def subscribe_channel_raid(
        self,
        token: str,
        from_broadcaster: Union[PartialUser, str, int] = None,
        to_broadcaster: Union[PartialUser, str, int] = None,
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
        await self._assign_subscription(sub)

    async def _subscribe_channel_points_reward(
        self,
        event: Tuple[str, int, Type[models._DataType]],
        broadcaster: Union[PartialUser, str, int],
        token: str,
        reward_id: str = None,
    ):
        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id

        broadcaster = str(broadcaster)
        data = {"broadcaster_user_id": broadcaster}
        if reward_id:
            data["reward_id"] = reward_id

        sub = _Subscription(event, data, token)
        await self._assign_subscription(sub)

    async def _subscribe_with_broadcaster(
        self, event: Tuple[str, int, Type[models._DataType]], broadcaster: Union[PartialUser, str, int], token: str
    ):
        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id

        broadcaster = str(broadcaster)
        sub = _Subscription(event, {"broadcaster_user_id": broadcaster}, token)
        await self._assign_subscription(sub)

    async def _subscribe_with_broadcaster_moderator(
        self,
        event: Tuple[str, int, Type[models._DataType]],
        broadcaster: Union[PartialUser, str, int],
        moderator: Union[PartialUser, str, int],
        token: str,
    ):
        if isinstance(broadcaster, PartialUser):
            broadcaster = broadcaster.id
        if isinstance(moderator, PartialUser):
            moderator = moderator.id

        broadcaster = str(broadcaster)
        moderator = str(moderator)
        sub = _Subscription(event, {"broadcaster_user_id": broadcaster, "moderator_user_id": moderator}, token)
        await self._assign_subscription(sub)

    async def subscribe_channel_bans(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.ban, broadcaster, token)

    async def subscribe_channel_unbans(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.unban, broadcaster, token)

    async def subscribe_channel_subscriptions(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription, broadcaster, token)

    async def subscribe_channel_subscription_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription_end, broadcaster, token)

    async def subscribe_channel_subscription_gifts(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription_gift, broadcaster, token)

    async def subscribe_channel_subscription_messages(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.subscription_message, broadcaster, token)

    async def subscribe_channel_cheers(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.cheer, broadcaster, token)

    async def subscribe_channel_update(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_update, broadcaster, token)

    async def subscribe_channel_follows(self, broadcaster: Union[PartialUser, str, int], token: str):
        raise RuntimeError("This subscription has been removed by twitch, please use subscribe_channel_follows_v2")

    async def subscribe_channel_follows_v2(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.followV2, broadcaster, moderator, token
        )

    async def subscribe_channel_moderators_add(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_moderator_add, broadcaster, token)

    async def subscribe_channel_moderators_remove(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_moderator_remove, broadcaster, token)

    async def subscribe_channel_goal_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_goal_begin, broadcaster, token)

    async def subscribe_channel_goal_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_goal_progress, broadcaster, token)

    async def subscribe_channel_goal_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_goal_end, broadcaster, token)

    async def subscribe_channel_hypetrain_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.hypetrain_begin, broadcaster, token)

    async def subscribe_channel_hypetrain_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.hypetrain_progress, broadcaster, token)

    async def subscribe_channel_hypetrain_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.hypetrain_end, broadcaster, token)

    async def subscribe_channel_stream_start(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.stream_start, broadcaster, token)

    async def subscribe_channel_stream_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.stream_end, broadcaster, token)

    async def subscribe_channel_points_reward_added(
        self, broadcaster: Union[PartialUser, str, int], reward_id: str, token: str
    ):
        await self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_add, broadcaster, token, reward_id
        )

    async def subscribe_channel_points_reward_updated(
        self, broadcaster: Union[PartialUser, str, int], reward_id: str, token: str
    ):
        await self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_update, broadcaster, token, reward_id
        )

    async def subscribe_channel_points_reward_removed(
        self, broadcaster: Union[PartialUser, str, int], reward_id: str, token: str
    ):
        await self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_remove, broadcaster, token, reward_id
        )

    async def subscribe_channel_points_redeemed(
        self, broadcaster: Union[PartialUser, str, int], token: str, reward_id: str = None
    ):
        await self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_redeem, broadcaster, token, reward_id
        )

    async def subscribe_channel_points_redeem_updated(
        self, broadcaster: Union[PartialUser, str, int], token: str, reward_id: str = None
    ):
        await self._subscribe_channel_points_reward(
            models.SubscriptionTypes.channel_reward_redeem_updated, broadcaster, token, reward_id
        )

    async def subscribe_channel_poll_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.poll_begin, broadcaster, token)

    async def subscribe_channel_poll_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.poll_progress, broadcaster, token)

    async def subscribe_channel_poll_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.poll_end, broadcaster, token)

    async def subscribe_channel_prediction_begin(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_begin, broadcaster, token)

    async def subscribe_channel_prediction_progress(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_progress, broadcaster, token)

    async def subscribe_channel_prediction_lock(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_lock, broadcaster, token)

    async def subscribe_channel_prediction_end(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.prediction_end, broadcaster, token)

    async def subscribe_channel_auto_reward_redeem(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.auto_reward_redeem, broadcaster, token)

    async def subscribe_channel_shield_mode_begin(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shield_mode_begin, broadcaster, moderator, token
        )

    async def subscribe_channel_shield_mode_end(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shield_mode_end, broadcaster, moderator, token
        )

    async def subscribe_channel_shoutout_create(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shoutout_create, broadcaster, moderator, token
        )

    async def subscribe_channel_shoutout_receive(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_shoutout_receive, broadcaster, moderator, token
        )

    async def subscribe_channel_charity_donate(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_charity_donate, broadcaster, token)

    async def subscribe_channel_unban_request_create(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.unban_request_create, broadcaster, moderator, token
        )

    async def subscribe_channel_unban_request_resolve(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.unban_request_resolve, broadcaster, moderator, token
        )

    async def subscribe_automod_message_hold(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.automod_message_hold, broadcaster, moderator, token
        )

    async def subscribe_automod_message_update(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.automod_message_update, broadcaster, moderator, token
        )

    async def subscribe_automod_settings_update(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.automod_settings_update, broadcaster, moderator, token
        )

    async def subscribe_automod_terms_update(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.automod_terms_update, broadcaster, moderator, token
        )

    async def subscribe_suspicious_user_update(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.suspicious_user_update, broadcaster, moderator, token
        )

    async def subscribe_channel_moderate(
        self, broadcaster: Union[PartialUser, str, int], moderator: Union[PartialUser, str, int], token: str
    ):
        await self._subscribe_with_broadcaster_moderator(
            models.SubscriptionTypes.channel_moderate, broadcaster, moderator, token
        )

    async def subscribe_channel_vip_add(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_vip_add, broadcaster, token)

    async def subscribe_channel_vip_remove(self, broadcaster: Union[PartialUser, str, int], token: str):
        await self._subscribe_with_broadcaster(models.SubscriptionTypes.channel_vip_remove, broadcaster, token)
