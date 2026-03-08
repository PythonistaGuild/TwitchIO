"""
A basic example of using DCF (Device Code Flow) with a commands.Bot and an eventsub subscription
to the authorized users chat, to run commands.

!note: DCF should only be used when you cannot safely store a client_secert: E.g. a users phone, tv, etc...

Your application should be set to "Public" in the Twitch Developer Console.
"""
import asyncio
import logging

import twitchio
from twitchio import eventsub
from twitchio.ext import commands


LOGGER: logging.Logger = logging.getLogger(__name__)
CLIENT_ID = "..."

SCOPES = twitchio.Scopes()
SCOPES.user_read_chat = True
SCOPES.user_write_chat = True


class Bot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(client_id=CLIENT_ID, scopes=SCOPES, prefix="!")

    async def setup_hook(self) -> None:
        await self.add_component(MyComponent(self))

    async def event_ready(self) -> None:
        # Usually we would do this in the setup_hook; however DCF deviates from our traditional flow slightly...
        # Since we have to wait for the user to authorize, it's safer to subscribe in event_ready...
        chat = eventsub.ChatMessageSubscription(broadcaster_user_id=self.bot_id, user_id=self.bot_id)
        await self.subscribe_websocket(chat, as_bot=True)

    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        await self.process_commands(payload)


class MyComponent(commands.Component):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.command()
    async def hi(self, ctx: commands.Context[Bot]) -> None:
        await ctx.send(f"Hello {ctx.chatter.mention}!")


def main() -> None:
    twitchio.utils.setup_logging()

    async def runner() -> None:
        async with Bot() as bot:
            resp = (await bot.login_dcf()) or {}
            device_code = resp.get("device_code")
            interval = resp.get("interval", 5)

            # Print URI to visit to authenticate
            print(resp.get("verification_uri", ""))

            await bot.start_dcf(device_code=device_code, interval=interval)

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt.")


if __name__ == "__main__":
    main()
