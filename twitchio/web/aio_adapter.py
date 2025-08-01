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

from twitchio.authentication.payloads import ValidateTokenPayload

from ..authentication import Scopes
from ..eventsub.subscriptions import _SUB_MAPPING
from ..exceptions import HTTPException
from ..models.eventsub_ import SubscriptionRevoked, create_event_instance
from ..utils import _from_json, parse_timestamp  # type: ignore
from .utils import MESSAGE_TYPES, BaseAdapter, FetchTokenPayload, verify_message


if TYPE_CHECKING:
    from ssl import SSLContext

    from ..authentication import AuthorizationURLPayload, UserTokenPayload, ValidateTokenPayload
    from ..client import Client
    from ..types_.eventsub import EventSubHeaders


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
    ssl_context: SSLContext | None
        An optional :class:`SSLContext` passed to the adapter. If SSL is setup via a front-facing web server such as NGINX, you should leave this as None.

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
        ssl_context: SSLContext | None = None,
    ) -> None:
        super().__init__()
        self._runner: web.AppRunner | None = None

        self._host: str = host or "localhost"
        self._port: int = port or 4343

        self._eventsub_secret: str | None = eventsub_secret
        if eventsub_secret and not 10 <= len(eventsub_secret) <= 100:
            raise ValueError("Eventsub Secret must be between 10 and 100 characters long.")

        self._ssl_context: SSLContext | None = ssl_context
        self._proto = "https" if (ssl_context or domain) else "http"

        if domain:
            domain_ = domain.removeprefix("http://").removeprefix("https://").removesuffix("/")
            self._domain = f"{self._proto}://{domain_}"
        else:
            self._domain = f"{self._proto}://{self._host}:{self._port}"

        path: str = eventsub_path.removeprefix("/").removesuffix("/") if eventsub_path else "callback"
        self._eventsub_path: str = f"/{path}"

        self._runner_task: asyncio.Task[None] | None = None
        self.startup = self.event_startup
        self.shutdown = self.event_shutdown

        self.router.add_route("GET", "/oauth/callback", self.oauth_callback)
        self.router.add_route("GET", "/oauth", self.oauth_redirect)
        self.router.add_route("POST", self._eventsub_path, self.eventsub_callback)

        self._responded: deque[str] = deque(maxlen=5000)
        self._running: bool = False

    def __init_subclass__(cls: type[AiohttpAdapter]) -> None:
        return

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(host="{self._host}", port={self._port})'

    @property
    def eventsub_url(self) -> str:
        """Property returning the fully qualified URL to the EventSub callback."""
        return f"{self._domain}{self._eventsub_path}"

    @property
    def redirect_url(self) -> str:
        """Property returning the fully qualified URL to the OAuth callback."""
        return f"{self._domain}/oauth/callback"

    async def event_startup(self) -> None:
        logger.info("Starting %r on %s://%s:%s.", self, self._proto, self._host, self._port)

    async def event_shutdown(self) -> None:
        logger.info("Successfully shutdown TwitchIO <%s>.", self.__class__.__qualname__)

    async def close(self, *args: Any, **kwargs: Any) -> None:
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
        self._running = False

    def _task_callback(self, task: asyncio.Task[None]) -> None:
        if not task.done():
            return

        if e := task.exception():
            raise e

    async def run(self, host: str | None = None, port: int | None = None) -> None:
        self._running = True

        self._runner = web.AppRunner(self, access_log=None, handle_signals=True)
        await self._runner.setup()

        site: web.TCPSite = web.TCPSite(self._runner, host or self._host, port or self._port, ssl_context=self._ssl_context)
        self._runner_task = asyncio.create_task(site.start(), name=f"twitchio-web-adapter:{self.__class__.__qualname__}")
        self._runner_task.add_done_callback(self._task_callback)

    async def eventsub_callback(self, request: web.Request) -> web.Response:
        headers: EventSubHeaders = cast("EventSubHeaders", request.headers)
        msg_type: str | None = headers.get("Twitch-Eventsub-Message-Type")

        if not msg_type or msg_type not in MESSAGE_TYPES:
            logger.debug("Eventsub Webhook received an unknown Message-Type header value.")
            return web.Response(status=400)

        if not self._eventsub_secret:
            msg: str = f"Eventsub Webhook '{self!r}' must be passed a secret.'"
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

    async def fetch_token(self, request: web.Request) -> FetchTokenPayload:
        """This method handles sending the provided code to Twitch to receive a User Access and Refresh Token pair, and
        later, if successful, dispatches :func:`~twitchio.event_oauth_authorized`.

        To call this coroutine you should pass the request received in the :meth:`oauth_callback`. This method is called by
        default, however when overriding :meth:`oauth_callback` you should always call this method.

        Parameters
        ----------
        request: aiohttp.web.Request
            The request received in :meth:`oauth_callback`.

        Returns
        -------
        FetchTokenPayload
            The payload containing various information about the authentication request to Twitch.
        """
        if "code" not in request.query:
            return FetchTokenPayload(400, response=web.Response(status=400, text="No 'code' parameter provided."))

        redirect = self._find_redirect(request)

        try:
            resp: UserTokenPayload = await self.client._http.user_access_token(
                request.query["code"],
                redirect_uri=redirect,
            )
        except HTTPException as e:
            logger.error("Exception raised while fetching Token in <%s>: %s", self.__class__.__qualname__, e)
            status: int = e.status
            return FetchTokenPayload(status=status, response=web.Response(status=status), exception=e)

        validated: ValidateTokenPayload = await self.client._http.validate_token(resp.access_token)
        resp._user_id = validated.user_id
        resp._user_login = validated.login

        self.client.dispatch(event="oauth_authorized", payload=resp)

        return FetchTokenPayload(
            status=20,
            response=web.Response(body="Success. You can leave this page.", status=200),
            payload=resp,
        )

    async def oauth_callback(self, request: web.Request) -> web.Response:
        """Default route callback for the OAuth Authentication redirect URL.

        You can override this method to alter the responses sent to the user.

        This callback should always return a valid response. See: `aiohttp docs <https://docs.aiohttp.org/en/stable/web.html>`_
        for more information.

        .. important::

            You should always call :meth:`.fetch_token` when overriding this method.

        Parameters
        ----------
        request: aiohttp.web.Request
            The original request received via aiohttp.

        Examples
        --------

        .. code:: python3

            async def oauth_callback(self, request: web.Request) -> web.Response:
                payload: FetchTokenPayload = await self.fetch_token(request)

                # Change the default success response to no content...
                if payload.status == 200:
                    return web.Response(status=204)

                # Return the default error responses...
                return payload.response
        """
        logger.debug("Received OAuth callback request in <%s>.", self.oauth_callback.__qualname__)

        payload: FetchTokenPayload = await self.fetch_token(request)
        if not isinstance(payload.response, web.Response):
            raise ValueError(f"Responses in AiohttpAdapter should be {type(web.Response)!r} not {type(payload.response)!r}")

        return payload.response

    def _find_redirect(self, request: web.Request) -> str:
        stripped = self._domain.removeprefix(f"{self._proto}://")
        local = f"{self._proto}://{self._host}"

        if request.host.startswith((self._domain, stripped)):
            redirect = self.redirect_url
        elif request.host.startswith((self._host, local)):
            redirect = f"{local}/oauth/callback"
        else:
            redirect = f"{request.scheme}://{request.host}/oauth/callback"

        return redirect

    async def oauth_redirect(self, request: web.Request) -> web.Response:
        redirect = self._find_redirect(request)

        scopes: str | None = request.query.get("scopes", request.query.get("scope", None))
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
                redirect_uri=redirect,
                force_verify=force_verify,
            )
        except Exception as e:
            logger.error("Exception raised while fetching Authorization URL in <%s>: %s", self.__class__.__qualname__, e)
            return web.Response(status=500)

        raise web.HTTPPermanentRedirect(payload["url"])

    def get_authorization_url(self, *, scopes: Scopes, force_verify: bool = False) -> str:
        """Method used to create a OAuth URL with the given options and scopes for users to authenticate the application with.

        Parameters
        ----------
        scopes: :class:`twitchio.Scopes`
            A :class:`twitchio.Scopes` object with the desired scopes.
        force_verify: :class:`bool`
            A :class:`bool` indicating whether the user should forcefully re-authenticate. When set to `True` the user must
            explicitly re-auth the application after visiting the URL. Defaults to `False`.

        Returns
        -------
        str
            The URL which can be provided to user(s) to authenticate your application.

        Raises
        ------
        ValueError
            Scopes is a required parameter.
        """
        if not scopes:
            raise ValueError('"scopes" is a required parameter or attribute which is missing.')

        return f"{self._domain}/oauth?scopes={scopes.urlsafe()}&force_verify={str(force_verify).lower()}"
