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

from typing import Unpack

from twitchio.client import Client
from twitchio.eventsub.enums import TransportMethod
from twitchio.eventsub.payloads import SubscriptionPayload
from twitchio.types_.options import ClientOptions


class Bot(Client):
    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        bot_id: str,
        **options: Unpack[ClientOptions],
    ) -> None:
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            bot_id=bot_id,
            **options,
        )

    @property
    def bot_id(self) -> str:
        assert self._bot_id
        return self._bot_id

    async def subscribe(
        self,
        method: TransportMethod,
        payload: SubscriptionPayload,
        as_bot: bool = True,
        token_for: str | None = None,
        socket_id: str | None = None,
        callback_url: str | None = None,
        eventsub_secret: str | None = None,
    ) -> ...:
        return await super().subscribe(
            method,
            payload,
            as_bot,
            token_for,
            socket_id=socket_id,
            callback_url=callback_url,
            eventsub_secret=eventsub_secret,
        )
