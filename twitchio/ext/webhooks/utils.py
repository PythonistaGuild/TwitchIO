import collections
import enum
import hashlib
import hmac
import logging

from sanic import response, router, request

log = logging.getLogger(__name__)


recent_notification_ids = collections.deque(maxlen=100)


class Topic(enum.Enum):

    stream_changed = 'StreamChanged'
    user_changed = 'UserChanged'
    user_follows = 'UserFollows'


StreamChangedNotification = collections.namedtuple('StreamChangedNotification',
                                                   ['community_ids', 'game_id', 'id', 'language', 'started_at',
                                                    'tag_ids', 'thumbnail_url', 'title', 'type', 'user_id', 'user_name',
                                                    'viewer_count'])

UserChangedNotification = collections.namedtuple('UserChangedNotification',
                                                 ['id', 'login', 'display_name', 'type', 'broadcaster_type',
                                                  'description', 'profile_image_url', 'offline_image_url',
                                                  'view_count'])

UserFollowsNotification = collections.namedtuple('UserFollowsNotification',
                                                 ["from_id", "from_name", "to_id", "to_name", "followed_at"])


def verify_payload(route: router.Route):
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


def remove_duplicates(route):
    """Decorator which prevents duplicate notifications being processed more than once."""

    async def inner(request, *args, **kwargs):
        notification_id = request.headers.get('Twitch-Notification-ID')

        if notification_id in recent_notification_ids:
            log.warning(f'Received duplicate notification with ID {notification_id}, discarding.')

            return response.text(None, status=204)

        recent_notification_ids.append(notification_id)
        return await route(request, *args, **kwargs)

    return inner
