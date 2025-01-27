import asyncio
import logging
from typing import TYPE_CHECKING

import asqlite

import twitchio
from twitchio import eventsub
from twitchio.ext import commands


if TYPE_CHECKING:
    import sqlite3


LOGGER: logging.Logger = logging.getLogger("Bot")

# Simple example for TwitchIO V3 Alpha...
# Instructions:

# You need to install: https://github.com/Rapptz/asqlite
# pip install -U git+https://github.com/Rapptz/asqlite.git

# 1.) Comment out lines: 54-60 (The subscriptions)
# 2.) Add the Twitch Developer Console and Create an Application
# 3.) Add: http://localhost:4343/oauth/callback as the callback URL
# 4.) Enter your CLIENT_ID, CLIENT_SECRET, BOT_ID and OWNER_ID
# 5.) Run the bot.
# 6.) Logged in the bots user account, visit: http://localhost:4343/oauth?scopes=user:read:chat%20user:write:chat%20user:bot
# 7.) Logged in as your personal user account, visit: http://localhost:4343/oauth?scopes=channel:bot
# 8.) Uncomment lines: 54-60 (The subscriptions)
# 9.) Restart the bot.
# You only have to do the above once for this example.


CLIENT_ID: str = "..."
CLIENT_SECRET: str = "..."
BOT_ID = "..."
OWNER_ID = "..."


class Bot(commands.Bot):
    def __init__(self, *, token_database: asqlite.Pool) -> None:
        self.token_database = token_database
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="!",
        )

    async def setup_hook(self) -> None:     
        # Subscribe to read chat (event_message) from our channel as the bot...
        # This creates and opens a websocket to Twitch EventSub...
        subscription = eventsub.ChatMessageSubscription(broadcaster_user_id=OWNER_ID, user_id=BOT_ID)
        await self.subscribe_websocket(payload=subscription)

        # Subscribe and listen to when a stream goes live..
        # For this example listen to our own stream...
        subscription = eventsub.StreamOnlineSubscription(broadcaster_user_id=OWNER_ID)
        await self.subscribe_websocket(payload=subscription)
        
        # Load the module that contains our component, commands, and listeners.
        # Modules can have multiple components.
        await self.load_module("components.owner_cmds")
        await self.load_module("components.cmds")

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET 
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def load_tokens(self, path: str | None = None) -> None:
        # We don't need to call this manually, it is called in .login() from .start() internally...

        async with self.token_database.acquire() as connection:
            rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        for row in rows:
            await self.add_token(row["token"], row["refresh"])

    async def setup_database(self) -> None:
        # Create our token table, if it doesn't exist..
        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with self.token_database.acquire() as connection:
            await connection.execute(query)

    async def event_ready(self) -> None:
        LOGGER.info("Successfully logged in as: %s", self.bot_id)



def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb, Bot(token_database=tdb) as bot:
            await bot.setup_database()
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()
