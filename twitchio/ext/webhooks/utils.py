import collections
import enum
import hashlib
import hmac
import logging

from sanic import response, blueprints, request

log = logging.getLogger(__name__)


recent_notification_ids = collections.deque(maxlen=100)


class Topic(enum.Enum):

    stream_changed = 'StreamChanged'
    user_changed = 'UserChanged'
    user_follows = 'UserFollows'


class Notification:
    """Twitch webhook notification dataclass."""

    __slots__ = ()
    valid_params = ()

    def __init__(self, **params):
        for param, value in params.items():
            setattr(self, param, value)


class StreamChangedNotification(Notification):
    """Twitch 'StreamChanged' webhook notification dataclass."""

    __slots__ = ('id', 'login', 'display_name', 'type', 'broadcaster_type', 'description', 'profile_image_url',
                 'offline_image_url', 'view_count')
    valid_params = ('user_id',)


class UserChangedNotification(Notification):
    """Twitch 'UserChanged' webhook notification dataclass."""

    __slots__ = ('id', 'login', 'display_name', 'type', 'broadcaster_type', 'description', 'profile_image_url',
                 'offline_image_url', 'view_count')
    valid_params = ('id',)


class UserFollowsNotification(Notification):
    """Twitch 'UserFollows' webhook notification dataclass."""

    __slots__ = ("from_id", "from_name", "to_id", "to_name", "followed_at")
    valid_params = ('from_id', 'to_id')


def verify_payload(route: blueprints.FutureRoute):
    """
    Decorator which verifies that a request was been sent from Twitch by comparing the 'X-Hub-Signature'
    header.
    """
    async def inner(request: request.Request, *args, **kwargs):

        secret = getattr(request.app.config, 'TWITCH_WEBHOOK_SECRET', None)

        if secret:

            secret = secret.encode('utf-8')
            digest = hmac.new(secret, msg=request.body, digestmod=hashlib.sha256).hexdigest()

            if not hmac.compare_digest(digest, request.headers.get('X-Hub-Signature', '')[7:]):
                log.warning("The hash for this notification is invalid")
                return response.text(None, status=403)

        return await route(request, *args, **kwargs)

    return inner


def remove_duplicates(route: blueprints.FutureRoute):
    """Decorator which prevents duplicate notifications being processed more than once."""

    async def inner(request: request.Request, *args, **kwargs):
        notification_id = request.headers.get('Twitch-Notification-ID')

        if notification_id in recent_notification_ids:
            log.warning(f'Received duplicate notification with ID {notification_id}, discarding.')

            return response.text(None, status=204)

        recent_notification_ids.append(notification_id)
        return await route(request, *args, **kwargs)

    return inner
