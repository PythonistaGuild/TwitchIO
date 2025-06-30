"""An example of connecting to a conduit and subscribing to EventSub when a User Authorizes the application.

This bot can be restarted as many times without needing to subscribe or worry about tokens:
- Tokens are stored in '.tio.tokens.json' by default
- Subscriptions last 72 hours after the bot is disconnected and refresh when the bot starts.

1. Fill out the constants below; CLIENT_ID etc...
2. Start the bot
3. Visit (Logged in on the BOT Account): http://localhost:4343/oauth?scopes=user:read:chat%20user:write:chat%20user:bot
 - You only need to do this once usually ^
4. You can log in as any user and visit: http://localhost:4343/oauth?scopes=channel:bot to allow this bot to chat/commands

Note: you can adjust the scopes however you need.
"""

import asyncio
import json
import logging

import twitchio
from twitchio import eventsub
from twitchio.ext import commands


LOGGER: logging.Logger = logging.getLogger(__name__)


# Store and retrieve these from a .env or similar, but for example showcase you can just full out the below:
CLIENT_ID = ""
CLIENT_SECRET = ""
BOT_ID = ""
OWNER_ID = ""


class Bot(commands.AutoBot):
    # AutoBot will automatically create and connect to a Conduit for us, ensuring there are an appropriate number of shards.
    # Conduits make it easier to manage subscriptions to EventSub as they only require App Tokens and we don't need to
    # ...subscribe continually: The Bot will maintain subscriptions for 72 hours after shutting down.

    def __init__(self, subs: list[eventsub.SubscriptionPayload]) -> None:
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
            subscriptions=subs,
        )

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.user)

    async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
            eventsub.StreamOnlineSubscription(broadcaster_user_id=payload.user_id),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            LOGGER.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        # Just for example purposes...
        LOGGER.info("[%s]: %s", payload.chatter, payload.text)
        await super().event_message(payload)


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    # For example purposes we are just using the default token storage, but you could store in a database etc..
    # Generate a list of subscriptions for each user token we have...
    subs: list[eventsub.SubscriptionPayload] = []

    with open(".tio.tokens.json", "rb") as fp:
        tokens = json.load(fp)
        for user_id in tokens:
            subs.extend(
                [
                    eventsub.ChatMessageSubscription(broadcaster_user_id=user_id, user_id=BOT_ID),
                    eventsub.StreamOnlineSubscription(broadcaster_user_id=user_id),
                ]
            )

    async def runner() -> None:
        async with Bot(subs=subs) as bot:
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt.")


if __name__ == "__main__":
    main()
