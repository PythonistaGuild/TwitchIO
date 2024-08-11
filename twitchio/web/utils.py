"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import hashlib
import hmac
import logging
from typing import TYPE_CHECKING

from aiohttp import web
from starlette.requests import Request


if TYPE_CHECKING:
    from ..types_.eventsub import EventSubHeaders


logger: logging.Logger = logging.getLogger(__name__)


MESSAGE_TYPES = ["notification", "webhook_callback_verification", "revocation"]


async def verify_message(*, request: Request | web.Request, secret: str) -> bytes:
    body: bytes
    headers: EventSubHeaders = request.headers  # type: ignore

    if isinstance(request, web.Request):
        body = await request.read()
    else:
        body = await request.body()

    msg_id: str = headers.get("Twitch-Eventsub-Message-Id", "")
    timestamp: str = headers.get("Twitch-Eventsub-Message-Timestamp", "")
    signature: str = headers.get("Twitch-Eventsub-Message-Signature", "")

    if not all((msg_id, timestamp, signature)):
        logger.warning("TwitchIO can not verify the EventSub HMAC signature. Invalid headers were provided.")
        raise ValueError

    hmac_payload: bytes = f"{msg_id}{timestamp}{body.decode('utf-8')}".encode()
    secret_: bytes = secret.encode("utf-8")

    hmac_: hmac.HMAC = hmac.new(secret_, digestmod=hashlib.sha256)
    hmac_.update(hmac_payload)

    if not hmac.compare_digest(hmac_.hexdigest(), signature[7:]):
        logger.warning("TwitchIO can not verify the EventSub HMAC signature. Unknown EventSub Signature received.")
        raise ValueError

    return body
