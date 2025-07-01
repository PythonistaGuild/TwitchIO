.. _quickstart:


Quickstart
###########

Consider reading through the `GitHub Examples <https://github.com/PythonistaGuild/TwitchIO/tree/main/examples>`_

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
#. Enter your CLIENT_ID, CLIENT_SECRET, BOT_ID and OWNER_ID into the placeholders in the below example. See :ref:`faqs` on how to retrieve the ``BOT_ID`` and ``OWNER_ID``.
#. Run and start the bot from the code below.
#. Open a new browser / incognito mode, log in as the ``BOT ACCOUNT`` and visit http://localhost:4343/oauth?scopes=user:read:chat%20user:write:chat%20user:bot&force_verify=true
#. In your main browser whilst logged in as ``YOUR ACCOUNT``, visit http://localhost:4343/oauth?scopes=channel:bot&force_verify=true
#. You can now use chat commands in your channel!

.. note::
    If you are unsure how to get the user IDs for BOT_ID and OWNER_ID, please check :ref:`bot-id-owner-id`

**You only have to do this sequence of steps once. Or if the scopes need to change.**

.. code:: python3

    """An example of connecting to a conduit and subscribing to EventSub when a User Authorizes the application.

    This bot can be restarted as many times without needing to subscribe or worry about tokens:
    - Tokens are stored in '.tio.tokens.json' by default
    - Subscriptions last 72 hours after the bot is disconnected and refresh when the bot starts.

    Consider reading through the documentation for AutoBot for more in depth explanations.
    """

    import asyncio
    import logging
    import random
    from typing import TYPE_CHECKING

    import asqlite

    import twitchio
    from twitchio import eventsub
    from twitchio.ext import commands


    if TYPE_CHECKING:
        import sqlite3


    LOGGER: logging.Logger = logging.getLogger("Bot")

    # Consider using a .env or another form of Configuration file!
    CLIENT_ID: str = "..."  # The CLIENT ID from the Twitch Dev Console
    CLIENT_SECRET: str = "..."  # The CLIENT SECRET from the Twitch Dev Console
    BOT_ID = "..."  # The Account ID of the bot user...
    OWNER_ID = "..."  # Your personal User ID..


    class Bot(commands.AutoBot):
        def __init__(self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]) -> None:
            self.token_database = token_database

            super().__init__(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                bot_id=BOT_ID,
                owner_id=OWNER_ID,
                prefix="!",
                subscriptions=subs,
            )

        async def setup_hook(self) -> None:
            # Add our component which contains our commands...
            await self.add_component(MyComponent(self))

        async def event_oauth_authorized(self, payload: twitchio.authentication.UserTokenPayload) -> None:
            await self.add_token(payload.access_token, payload.refresh_token)

            if not payload.user_id:
                return

            if payload.user_id == self.bot_id:
                # We usually don't want subscribe to events on the bots channel...
                return

            # A list of subscriptions we would like to make to the newly authorized channel...
            subs: list[eventsub.SubscriptionPayload] = [
                eventsub.ChatMessageSubscription(broadcaster_user_id=payload.user_id, user_id=self.bot_id),
            ]

            resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
            if resp.errors:
                LOGGER.warning("Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id)

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

        async def event_ready(self) -> None:
            LOGGER.info("Successfully logged in as: %s", self.bot_id)


    class MyComponent(commands.Component):
        # An example of a Component with some simple commands and listeners
        # You can use Components within modules for a more organized codebase and hot-reloading.

        def __init__(self, bot: Bot) -> None:
            # Passing args is not required...
            # We pass bot here as an example...
            self.bot = bot

        # An example of listening to an event
        # We use a listener in our Component to display the messages received.
        @commands.Component.listener()
        async def event_message(self, payload: twitchio.ChatMessage) -> None:
            print(f"[{payload.broadcaster.name}] - {payload.chatter.name}: {payload.text}")

        @commands.command()
        async def hi(self, ctx: commands.Context) -> None:
            """Command that replys to the invoker with Hi <name>!

            !hi
            """
            await ctx.reply(f"Hi {ctx.chatter}!")

        @commands.command()
        async def say(self, ctx: commands.Context, *, message: str) -> None:
            """Command which repeats what the invoker sends.

            !say <message>
            """
            await ctx.send(message)

        @commands.command()
        async def add(self, ctx: commands.Context, left: int, right: int) -> None:
            """Command which adds to integers together.

            !add <number> <number>
            """
            await ctx.reply(f"{left} + {right} = {left + right}")

        @commands.command()
        async def choice(self, ctx: commands.Context, *choices: str) -> None:
            """Command which takes in an arbitrary amount of choices and randomly chooses one.

            !choice <choice_1> <choice_2> <choice_3> ...
            """
            await ctx.reply(f"You provided {len(choices)} choices, I choose: {random.choice(choices)}")

        @commands.command(aliases=["thanks", "thank"])
        async def give(self, ctx: commands.Context, user: twitchio.User, amount: int, *, message: str | None = None) -> None:
            """A more advanced example of a command which has makes use of the powerful argument parsing, argument converters and
            aliases.

            The first argument will be attempted to be converted to a User.
            The second argument will be converted to an integer if possible.
            The third argument is optional and will consume the reast of the message.

            !give <@user|user_name> <number> [message]
            !thank <@user|user_name> <number> [message]
            !thanks <@user|user_name> <number> [message]
            """
            msg = f"with message: {message}" if message else ""
            await ctx.send(f"{ctx.chatter.mention} gave {amount} thanks to {user.mention} {msg}")

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


    async def setup_database(db: asqlite.Pool) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
        # Create our token table, if it doesn't exist..
        # You should add the created files to .gitignore or potentially store them somewhere safer
        # This is just for example purposes...

        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with db.acquire() as connection:
            await connection.execute(query)

            # Fetch any existing tokens...
            rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

            tokens: list[tuple[str, str]] = []
            subs: list[eventsub.SubscriptionPayload] = []

            for row in rows:
                tokens.append((row["token"], row["refresh"]))
                subs.extend([eventsub.ChatMessageSubscription(broadcaster_user_id=row["user_id"], user_id=BOT_ID)])

        return tokens, subs


    # Our main entry point for our Bot
    # Best to setup_logging here, before anything starts
    def main() -> None:
        twitchio.utils.setup_logging(level=logging.INFO)

        async def runner() -> None:
            async with asqlite.create_pool("tokens.db") as tdb:
                tokens, subs = await setup_database(tdb)

                async with Bot(token_database=tdb, subs=subs) as bot:
                    for pair in tokens:
                        await bot.add_token(*pair)

                    await bot.start(load_tokens=False)

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            LOGGER.warning("Shutting down due to KeyboardInterrupt")


    if __name__ == "__main__":
        main()
