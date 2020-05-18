import asyncio
import enum
import logging

import sanic
from sanic import request
from sanic import response

from twitchio.ext.webhooks.utils import remove_duplicates, verify_payload, Topic, StreamChangedNotification, \
    UserChangedNotification, UserFollowsNotification

log = logging.getLogger(__name__)


NOTIFICATION_TYPE_BY_TOPIC = {
    Topic.stream_changed: StreamChangedNotification,
    Topic.user_changed: UserChangedNotification,
    Topic.user_follows: UserFollowsNotification
}


class WebhookEventDispatcher:

    __instances = set()
    __dispatcher = None

    def __init__(self, loop: asyncio.AbstractEventLoop = None):
        self.__instances.add(self)
        self.loop = loop or asyncio.get_event_loop()

    def __init_subclass__(cls, **kwargs):
        cls._registered_dispatcher(cls)

    @classmethod
    def _registered_dispatcher(cls, new_cls=None):
        if new_cls:
            WebhookEventDispatcher.__dispatcher = new_cls
        return WebhookEventDispatcher.__dispatcher

    @staticmethod
    def accept_subscription(request: request.Request, topic: enum.Enum):
        try:
            mode = request.args['hub.mode'][0]
        except KeyError:
            return response.HTTPResponse(status=400)

        if mode == 'subscribe' or mode == 'unsubscribe':
            try:
                return response.text(request.args['hub.challenge'][0], status=200)
            except KeyError:
                return response.HTTPResponse(status=400)
        elif mode == 'denied':
            reason = request.args.get('hub.reason', 'no reason')
            log.warning(f'{topic.name} webhook subscribe request denied ({request.args}) , reason: {reason}.')

            return response.HTTPResponse(status=204)

    @classmethod
    async def bulk_process_notification(cls, topic: Topic, data: dict, params: dict):
        if topic not in NOTIFICATION_TYPE_BY_TOPIC:
            log.error(f'Invalid topic "{topic.name}" with params "{params}", the notification has been ignored')
            return

        for instance in cls.__instances:
            await instance.process_notification(topic, data, params)

    async def process_notification(self, topic: Topic, data: dict, params: dict):

        cls = NOTIFICATION_TYPE_BY_TOPIC[topic]
        notification = cls(**{field: data.get(field) for field in cls._fields})
        try:
            if cls == StreamChangedNotification:
                if data:
                    await self.event_stream_online(params, notification)
                else:
                    await self.event_stream_offline(params, notification)
            elif cls == UserChangedNotification:
                await self.event_user_changed(params, notification)
            elif cls == UserFollowsNotification:
                if 'from_id' not in params:
                    await self.event_following_user(params, notification)
                else:
                    await self.event_followed_by_user(params, notification)

        except Exception as error:
            self.loop.create_task(self.webhook_notification_error(topic, data, params, error))

    async def webhook_notification_error(self, topic: enum.Enum, data: dict, params: dict, error: Exception):
        log.error(f"Exception '{type(error).__name__}' raised for topic  '{topic.name}' (params={params})",
                  exc_info=(type(error), error, error.__traceback__))

    async def event_stream_online(self, params: dict, notification: StreamChangedNotification):
        pass

    async def event_stream_offline(self, params: dict, notification: StreamChangedNotification):
        pass

    async def event_user_changed(self, params: dict, notification: UserChangedNotification):
        pass

    async def event_following_user(self, params: dict, notification: UserFollowsNotification):
        pass

    async def event_followed_by_user(self, params: dict, notification: UserFollowsNotification):
        pass


dispatcher = WebhookEventDispatcher._registered_dispatcher
bp = sanic.Blueprint("Twitchio Webhooks", url_prefix="/webhooks")


@bp.route('/streams', ['GET'])
async def handle_stream_changed_get(request: request.Request):
    return dispatcher().accept_subscription(request, Topic.stream_changed)


@bp.route('/streams', ['POST'])
@remove_duplicates
@verify_payload
async def handle_stream_changed_post(request: request.Request):
    try:
        params = {'user_id': request.args['user_id']}
        request.app.loop.create_task(dispatcher().bulk_process_notification(Topic.user_changed, request.json['data'][0],
                                                                            params))
    except KeyError:
        return response.HTTPResponse(status=400)

    return response.HTTPResponse(status=202)


@bp.route('/users', ['GET'])
async def handle_user_changed_get(request: request.Request):
    return dispatcher().accept_subscription(request, Topic.user_changed)


@bp.route('/users', ['POST'])
@remove_duplicates
@verify_payload
async def handle_user_changed_post(request: request.Request):
    try:
        params = {'id': request.args['id']}
        request.app.loop.create_task(dispatcher().bulk_process_notification(Topic.user_changed, request.json['data'][0],
                                                                            params))
    except KeyError:
        return response.HTTPResponse(status=400)

    return response.HTTPResponse(status=202)


@bp.route('/user/follows', ['GET'])
async def handle_user_follows_get(request: request.Request):
    return dispatcher().accept_subscription(request, Topic.user_follows)


@bp.route('/user/follows', ['POST'])
@remove_duplicates
@verify_payload
async def handle_user_follows_post(request: request.Request):

    params = {'from_id': request.args.get('from_id'), 'to_id': request.args.get('to_id')}
    if not (params['from_id'] or params['to_id']):
        # One of them needs to be set at least
        return response.HTTPResponse(status=400)

    try:
        request.app.loop.create_task(dispatcher().bulk_process_notification(Topic.user_follows, request.json['data'][0],
                                                                            params))
    except KeyError:
        return response.HTTPResponse(status=400)

    return response.HTTPResponse(status=202)
