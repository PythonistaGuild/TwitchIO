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

from __future__ import annotations

import asyncio
import datetime
import logging
from collections import deque
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import unquote_plus

from aiohttp import web

from ..authentication import Scopes
from ..eventsub.subscriptions import _SUB_MAPPING
from ..models.eventsub_ import SubscriptionRevoked, create_event_instance
from ..types_.eventsub import EventSubHeaders
from ..utils import _from_json, parse_timestamp  # type: ignore
from .utils import MESSAGE_TYPES, BaseAdapter, verify_message


if TYPE_CHECKING:
    from ..authentication import AuthorizationURLPayload, UserTokenPayload
    from ..client import Client


__all__ = ("AiohttpAdapter",)


logger: logging.Logger = logging.getLogger(__name__)


class AiohttpAdapter(BaseAdapter, web.Application):
    """The AiohttpAdapter for OAuth and Webhook based EventSub.

    This adapter uses ``aiohttp`` which is a base dependency and should be installed and available with Twitchio.

    Optionally you can use `Starlette <https://www.starlette.io/>`_ with `Uvicorn <https://www.uvicorn.org/>`_ by using the
    :class:`StarletteAdapter`. This will require additional dependencies.

    An adapter will always be started and is ran alongside the :class:`~twitchio.Client` or
    :class:`~twitchio.ext.commands.Bot` by default. You can disable starting the adapter by passing ``with_adapter=False``
    to :meth:`twitchio.Client.start` or :meth:`twitchio.Client.run`.

    The adapter can be used to authenticate users via OAuth, and supports webhooks for EventSub, with in-built event
    dispatching to the :class:`~twitchio.Client`.

    The default callbacks for OAuth are:

    - ``/oauth`` E.g. ``http://localhost:4343/oauth`` or ``https://mydomain.org/oauth``.
        - Should be used with the ``?scopes=`` query parameter to pass a URL encoded list of scopes.
           See: :class:`~twitchio.Scopes` for a helper class for generating scopes.

    - ``/oauth/callback`` E.g. ``http://localhost:4343/oauth/callback`` or ``https://mydomain.org/oauth/callback``.
        - The redirect URL for OAuth request. This should be set in the developer console of your application on Twitch.

    The default callbacks for EventSub are:

    - ``/callback`` E.g. ``http://localhost:4343/callback`` or ``https://mydomain.org/callback``.


    This class handles processing and validating EventSub requests for you, and dispatches any events identical to
    the websocket equivalent.

    Parameters
    ----------
    host: str | None
        An optional :class:`str` passed to bind as the host address. Defaults to ``localhost``.
    port: int | None
        An optional :class:`int` passed to bind as the port for the host address. Defaults to ``4343``.
    domain: str | None
        An optional :class:`str` passed used to identify the external domain used, if any. If passed, the domain will be used
        for the redirect URL in OAuth and for validation in EventSub. It must be publicly accessible and support HTTPS.
    eventsub_path: str | None
        An optional :class:`str` passed to use as the path to the eventsub callback. Defaults to ``/callback``. E.g.
        ``http://localhost:4343/callback`` or ``https://mydomain.org/callback``.
    eventsub_secret: str | None
        An optional :class:`str` passed to use as the EventSub secret. It is recommended you pass this parameter when using
        an adapter for EventSub, as it will reset upon restarting otherwise. You can generate token safe secrets with the
        :mod:`secrets` module.

    Examples
    --------

    .. code-block:: python3

        import twitchio
        from twitchio import web
        from twitchio.ext import commands


        class Bot(commands.Bot):

            def __init__(self) -> None:
                # Requests will be sent to, as an example:
                # http://bot.twitchio.dev
                # You DO NOT need to pass a domain, however not passing a domain will mean only you can authenticate
                # via OAuth and Webhooks will not be supported...
                # The domain should support HTTPS and be publicly accessible...
                # An easy way to do this is add your domain to a CDN like Cloudflare and set SSL to Flexible.
                #
                # Visit: http://localhost:8080/oauth?scopes=channel:bot as the broadcaster as an example.
                # Visit: https://bot.twitchio.dev?scopes=channel:bot as the broadcaster as an example.

                adapter = web.AiohttpAdapter(domain="bot.twitchio.dev", port=8080)
                super().__init__(adapter=adapter)
    """

    client: Client

    def __init__(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        domain: str | None = None,
        eventsub_path: str | None = None,
        eventsub_secret: str | None = None,
    ) -> None:
        super().__init__()
        self._runner: web.AppRunner | None = None

        self._host: str = host or "localhost"
        self._port: int = port or 4343

        self._eventsub_secret: str | None = eventsub_secret
        if eventsub_secret and not 10 <= len(eventsub_secret) <= 100:
            raise ValueError("Eventsub Secret must be between 10 and 100 characters long.")

        self._domain: str | None = None
        if domain:
            domain_ = domain.removeprefix("http://").removeprefix("https://").removesuffix("/")
            self._domain = f"https://{domain_}"
        else:
            self._domain = f"http://{self._host}:{self._port}"

        path: str = eventsub_path.removeprefix("/").removesuffix("/") if eventsub_path else "callback"
        self._eventsub_path: str = f"/{path}"

        self._runner_task: asyncio.Task[None] | None = None
        self.startup = self.event_startup
        self.shutdown = self.event_shutdown

        self.router.add_route("GET", "/oauth/callback", self.oauth_callback)
        self.router.add_route("GET", "/oauth", self.oauth_redirect)
        self.router.add_route("POST", self._eventsub_path, self.eventsub_callback)

        self._responded: deque[str] = deque(maxlen=5000)

    def __init_subclass__(cls: type[AiohttpAdapter]) -> None:
        return

    @property
    def eventsub_url(self) -> str:
        """Property returning the fully qualified URL to the EventSub callback."""
        return f"{self._domain}{self._eventsub_path}"

    @property
    def redirect_url(self) -> str:
        """Property returning the fully qualified URL to the OAuth callback."""
        return f"{self._domain}/oauth/callback"

    async def event_startup(self) -> None:
        logger.info("Starting TwitchIO AiohttpAdapter on http://%s:%s.", self._host, self._port)

    async def event_shutdown(self) -> None:
        logger.info("Successfully shutdown TwitchIO <%s>.", self.__class__.__qualname__)

    async def close(self) -> None:
        if self._runner_task is not None:
            try:
                self._runner_task.cancel()
            except Exception as e:
                logger.debug(
                    "Ignoring exception raised while cancelling runner in <%s>: %s.",
                    self.__class__.__qualname__,
                    e,
                )

        if self._runner is not None:
            await self._runner.cleanup()

        self._runner = None
        self._runner_task = None

    async def run(self, host: str | None = None, port: int | None = None) -> None:
        self._runner = web.AppRunner(self, access_log=None, handle_signals=True)
        await self._runner.setup()

        site: web.TCPSite = web.TCPSite(self._runner, host or self._host, port or self._port)
        self._runner_task = asyncio.create_task(site.start(), name=f"twitchio-web-adapter:{self.__class__.__qualname__}")

    async def eventsub_callback(self, request: web.Request) -> web.Response:
        headers: EventSubHeaders = cast(EventSubHeaders, request.headers)
        msg_type: str | None = headers.get("Twitch-Eventsub-Message-Type")

        if not msg_type or msg_type not in MESSAGE_TYPES:
            logger.debug("Eventsub Webhook received an unknown Message-Type header value.")
            return web.Response(status=400)

        if not self._eventsub_secret:
            msg: str = f"Eventsub Webhook '{self!r}' must be passed a secret. See: ... for more info.'"
            return web.Response(text=msg, status=400)

        msg_id: str | None = headers.get("Twitch-Eventsub-Message-Id", None)
        timestamp: str | None = headers.get("Twitch-Eventsub-Message-Timestamp", None)

        if not msg_id or not timestamp:
            return web.Response(text="Bad Request. Invalid Message-ID or Message-Timestamp.", status=400)

        if msg_id in self._responded:
            return web.Response(text="Previously responded to Message.", status=400)

        self._responded.append(msg_id)

        try:
            resp: bytes = await verify_message(request=request, secret=self._eventsub_secret)
        except ValueError:
            return web.Response(text="Challenge Failed. Failed to verify the integrity of the message.", status=400)
        except Exception as e:
            return web.Response(text=f"Challenge Failed. Failed to verify the integrity of the message: {e}", status=400)

        data: Any = _from_json(resp)  # type: ignore
        sent: datetime.datetime = parse_timestamp(timestamp)
        now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)

        if sent + datetime.timedelta(minutes=10) <= now:
            return web.Response(text="Message has expired.", status=400)

        if msg_type == "webhook_callback_verification":
            return web.Response(text=data["challenge"], status=200, headers={"Content-Type": "text/plain"})

        elif msg_type == "notification":
            sub_type: str = data["subscription"]["type"]
            event = _SUB_MAPPING.get(sub_type, sub_type.removeprefix("channel.")).replace(".", "_")

            try:
                payload_class = create_event_instance(sub_type, data, http=self.client._http, headers=headers)
            except ValueError:
                logger.warning("Webhook '%s' received an unhandled eventsub event: '%s'.", self, event)
                return web.Response(status=200)

            self.client.dispatch(event=event, payload=payload_class)
            return web.Response(status=200)

        elif msg_type == "revocation":
            payload: SubscriptionRevoked = SubscriptionRevoked(data["subscription"])
            self.client.dispatch(event="subscription_revoked", payload=payload)

            return web.Response(status=204)

    async def fetch_token(self, request: web.Request) -> web.Response:
        if "code" not in request.query:
            return web.Response(status=400)

        try:
            payload: UserTokenPayload = await self.client._http.user_access_token(
                request.query["code"],
                redirect_uri=self.redirect_url,
            )
        except Exception as e:
            logger.error("Exception raised while fetching Token in <%s>: %s", self.__class__.__qualname__, e)
            return web.Response(status=500)

        self.client.dispatch(event="oauth_authorized", payload=payload)
        return web.Response(body="Success. You can leave this page.", status=200)

    async def oauth_callback(self, request: web.Request) -> web.Response:
        logger.debug("Received OAuth callback request in <%s>.", self.oauth_callback.__qualname__)

        response: web.Response = await self.fetch_token(request)
        return response

    async def oauth_redirect(self, request: web.Request) -> web.Response:
        scopes: str | None = request.query.get("scopes", None)
        force_verify: bool = request.query.get("force_verify", "false").lower() == "true"

        if not scopes:
            scopes = str(self.client._http.scopes) if self.client._http.scopes else None

        if not scopes:
            logger.warning(
                "No scopes provided in request to <%s>. Scopes are a required parameter that is missing.",
                self.oauth_redirect.__qualname__,
            )
            return web.Response(text="No scopes were provided. Scopes must be provided.", status=400)

        scopes_: Scopes = Scopes(unquote_plus(scopes).split())

        try:
            payload: AuthorizationURLPayload = self.client._http.get_authorization_url(
                scopes=scopes_,
                redirect_uri=self.redirect_url,
                force_verify=force_verify,
            )
        except Exception as e:
            logger.error("Exception raised while fetching Authorization URL in <%s>: %s", self.__class__.__qualname__, e)
            return web.Response(status=500)

        raise web.HTTPPermanentRedirect(payload["url"])
