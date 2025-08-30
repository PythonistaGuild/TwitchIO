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

import abc
import logging
import secrets
from typing import TYPE_CHECKING, Any

from aiohttp import web

from twitchio.web import AiohttpAdapter, BaseAdapter

from .exceptions import *


if TYPE_CHECKING:
    from .core import Overlay


LOGGER: logging.Logger = logging.getLogger(__name__)


__all__ = ("AiohttpOverlayAdapter", "BaseOverlayAdapter")


class BaseOverlayAdapter(BaseAdapter):
    @abc.abstractmethod
    async def _overlay_callback(self, request: Any) -> ...: ...


class AiohttpOverlayAdapter(BaseOverlayAdapter, AiohttpAdapter):
    # TODO: Type args/kwargs

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._overlays: dict[str, Overlay] = {}

        self.router.add_route("GET", "/overlays/{secret}", self.overlay_route)
        self.router.add_route("POST", "/overlays/{secret}/callback", self._overlay_callback)
        self.router.add_route("GET", "/overlays/{secret}/connect", self.websocket_connect)

    async def add_overlay(self, overlay: Overlay) -> Overlay:
        try:
            await overlay.setup()
        except Exception as e:
            raise OverlayLoadError(f"An error occurred during setup in {overlay!r}.") from e

        if not overlay.secret:
            raise OverlayLoadError(f"No secret was provided for {overlay!r}.")

        elif overlay.secret in self._overlays:
            raise OverlayLoadError("An overlay has already been loaded with the provided secret.")

        self._overlays[overlay.secret] = overlay
        return overlay

    async def overlay_route(self, request: web.Request) -> web.Response:
        info = request.match_info
        secret = info.get("secret")

        if not secret:
            return web.Response(text="No overlay path was provided.", status=400)

        overlay = self._overlays.get(secret)
        if not overlay:
            return web.Response(text=f"Overlay '{secret}' not found.", status=404)

        headers = {"Content-Type": "text/html"}
        return web.Response(body=overlay.generate_html(), headers=headers)

    async def _overlay_callback(self, request: web.Request) -> web.Response:
        print(await request.text())
        return web.Response(body="Hi! CALLBACK")

    async def _ws_gen(self, overlay: Overlay, id: str, ws: web.WebSocketResponse) -> None:
        while True:
            msg = await ws.receive()
            print(msg)

            if msg.type == web.WSMsgType.CLOSED:
                break

        try:
            overlay.__sockets__.pop(id, None)
        except ValueError:
            pass

    async def close(self, *args: Any, **kwargs: Any) -> None:
        for overlay in self._overlays.values():
            await overlay.close()

        return await super().close(*args, **kwargs)

    async def websocket_connect(self, request: web.Request) -> web.WebSocketResponse | web.Response:
        info = request.match_info
        secret = info.get("secret")

        if not secret:
            return web.Response(text="No overlay path was provided.", status=400)

        overlay = self._overlays.get(secret)
        if not overlay:
            return web.Response(text=f"Overlay '{secret}' not found.", status=404)

        ws = web.WebSocketResponse(heartbeat=10)
        await ws.prepare(request)

        socket_id = secrets.token_urlsafe(16)
        overlay.__sockets__[socket_id] = ws

        try:
            await self._ws_gen(overlay, socket_id, ws)
        except Exception as e:
            LOGGER.warning(e)

        return ws
