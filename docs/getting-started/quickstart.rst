.. _quickstart:


Quickstart
###########

This mini tutorial will serve as an entry point into TwitchIO 3. After it you should have a small working bot and a basic understanding of TwitchIO.

If you haven't already installed TwitchIO 3, please check :doc:`installing`.


Creating a Twitch Application
==============================

#. Browse to `Twitch Developer Console <https://dev.twitch.tv/console>`_ and Create an Application
#. Add: http://localhost:4343/oauth/callback as the callback URL
#. Make a note of your CLIENT_ID and CLIENT_SECRET.

A Minimal bot
==============

For this example we will be using sqlite3 as our token database. 
Since TwitchIO 3 is fully asynchronous we will be using `asqlite` as our library of choice.

.. code:: shell 
    
    pip install -U git+https://github.com/Rapptz/asqlite.git

Before running the code below, there just a couple more steps we need to take.

#. Create a new Twitch account. This will be the dedicated bot account.
#. Enter your CLIENT_ID, CLIENT_SECRET, BOT_ID and OWNER_ID into the placeholders in the below example.
#. Comment out everything in ``setup_hook``.
#. Run the bot.
#. Open a new browser / incognito mode, log in as the bot account and visit http://localhost:4343/oauth?scopes=user:read:chat%20user:write:chat%20user:bot
#. In your main browser whilst logged in as your account, visit http://localhost:4343/oauth?scopes=channel:bot
#. Stop the bot and uncomment everything in ``setup_hook``.
#. Start the bot.

.. note::
    If you are unsure how to get the user IDs for BOT_ID and OWNER_ID, please check the `FAQ here </getting-started/faq.html#how-do-i-get-the-user-ids-for-bot-id-and-owner-id>`_.


**You only have to do this sequence of steps once. Or if the scopes need to change.**

.. code:: python3

    import asyncio
    import logging
    import sqlite3

    import asqlite
    import twitchio
    from twitchio.ext import commands
    from twitchio import eventsub


    LOGGER: logging.Logger = logging.getLogger("Bot")

    CLIENT_ID: str = "..." # The CLIENT ID from the Twitch Dev Console
    CLIENT_SECRET: str = "..." # The CLIENT SECRET from the Twitch Dev Console
    BOT_ID = "..."  # The Account ID of the bot user...
    OWNER_ID = "..."  # Your personal User ID..


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
            # Add our component which contains our commands...
            await self.add_component(MyComponent(self))

            # Subscribe to read chat (event_message) from our channel as the bot...
            # This creates and opens a websocket to Twitch EventSub...
            subscription = eventsub.ChatMessageSubscription(broadcaster_user_id=OWNER_ID, user_id=BOT_ID)
            await self.subscribe_websocket(payload=subscription)

            # Subscribe and listen to when a stream goes live..
            # For this example listen to our own stream...
            subscription = eventsub.StreamOnlineSubscription(broadcaster_user_id=OWNER_ID)
            await self.subscribe_websocket(payload=subscription)

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


    class MyComponent(commands.Component):
        def __init__(self, bot: Bot):
            # Passing args is not required...
            # We pass bot here as an example...
            self.bot = bot
    
        # We use a listener in our Component to display the messages received.
        @commands.Component.listener()
        async def event_message(self, payload: twitchio.ChatMessage) -> None:
            print(f"[{payload.broadcaster.name}] - {payload.chatter.name}: {payload.text}")

        @commands.command(aliases=["hello", "howdy", "hey"])
        async def hi(self, ctx: commands.Context) -> None:
            """Simple command that says hello!

            !hi, !hello, !howdy, !hey
            """
            await ctx.reply(f"Hello {ctx.chatter.mention}!")

        @commands.group(invoke_fallback=True)
        async def socials(self, ctx: commands.Context) -> None:
            """Group command for our social links.

            !socials
            """
            await ctx.send("discord.gg/..., youtube.com/..., twitch.tv/...")

        @socials.command(name="discord")
        async def socials_discord(self, ctx: commands.Context) -> None:
            """Sub command of socials that sends only our discord invite.

            !socials discord
            """
            await ctx.send("discord.gg/...")

        @commands.command(aliases=["repeat"])
        @commands.is_moderator()
        async def say(self, ctx: commands.Context, *, content: str) -> None:
            """Moderator only command which repeats back what you say.

            !say hello world, !repeat I am cool LUL
            """
            await ctx.send(content)

        @commands.Component.listener()
        async def event_stream_online(self, payload: twitchio.StreamOnline) -> None:
            # Event dispatched when a user goes live from the subscription we made above...

            # Keep in mind we are assuming this is for ourselves
            # others may not want your bot randomly sending messages...
            await payload.broadcaster.send_message(
                sender=self.bot.bot_id,
                message=f"Hi... {payload.broadcaster}! You are live!",
            )


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