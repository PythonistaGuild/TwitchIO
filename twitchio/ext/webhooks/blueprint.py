import logging

import sanic
from sanic import request

from twitchio.ext.webhooks.utils import remove_duplicates, verify_payload, Topic
from twitchio.ext.webhooks.dispatcher import WebhookEventDispatcher

log = logging.getLogger(__name__)


dispatcher = WebhookEventDispatcher._registered_dispatcher
bp = sanic.Blueprint("Twitchio Webhooks", url_prefix="/webhooks")


@bp.route('/streams', ['GET'])
async def handle_stream_changed_get(request: request.Request):
    """Route receiving the challenge requests for the topic StreamChanged

    Parameters
    ----------
    request: sanic.request.Request
        The challenge request received from Twitch
    """
    return dispatcher().accept_subscription(request, Topic.stream_changed)


@bp.route('/streams', ['POST'])
@remove_duplicates
@verify_payload
async def handle_stream_changed_post(request: request.Request):
    """Route receiving the notifications for the topic StreamChanged

    Parameters
    ----------
    request: sanic.request.Request
        The challenge request received from Twitch
    """
    return await dispatcher().bulk_process_notification(request, Topic.stream_changed)


@bp.route('/users', ['GET'])
async def handle_user_changed_get(request: request.Request):
    """Route receiving the challenge requests for the topic UserChanged

    Parameters
    ----------
    request: sanic.request.Request
        The challenge request received from Twitch
    """
    return dispatcher().accept_subscription(request, Topic.user_changed)


@bp.route('/users', ['POST'])
@remove_duplicates
@verify_payload
async def handle_user_changed_post(request: request.Request):
    """Route receiving the notifications for the topic UserChanged

    Parameters
    ----------
    request: sanic.request.Request
        The challenge request received from Twitch
    """
    return await dispatcher().bulk_process_notification(request, Topic.user_changed)


@bp.route('/users/follows', ['GET'])
async def handle_user_follows_get(request: request.Request):
    """Route receiving the challenge requests for the topic UserFollows

    Parameters
    ----------
    request: sanic.request.Request
        The challenge request received from Twitch
    """
    return dispatcher().accept_subscription(request, Topic.user_follows)


@bp.route('/users/follows', ['POST'])
@remove_duplicates
@verify_payload
async def handle_user_follows_post(request: request.Request):
    """Route receiving the notifications for the topic UserFollows

    Parameters
    ----------
    request: sanic.request.Request
        The challenge request received from Twitch
    """
    return await dispatcher().bulk_process_notification(request, Topic.user_follows)
