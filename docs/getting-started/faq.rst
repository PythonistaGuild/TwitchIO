.. _faqs:

FAQ
###


Frequently asked Questions
--------------------------


How do I send a message to a specific channel?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To send a message to a specific channel/broadcaster you should use :meth:`~twitchio.PartialUser.send_message` on
:class:`~twitchio.PartialUser`. You can create a :class:`~twitchio.PartialUser` with only the users ID with
:meth:`~twitchio.Client.create_partialuser` on :class:`~twitchio.Client` or :class:`~twitchio.ext.commands.Bot`.

.. code:: python3

    user = bot.create_partialuser(id="...")
    await user.send_message(sender=bot.user, message="Hello World!")

If you are inside of a :class:`~twitchio.ext.commands.Command`, 
consider using the available :class:`~twitchio.ext.commands.Context` instead.


.. _irc_faq:

Why was IRC functionality removed from the core library?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Twitch has started recommending developers use EventSub in-place of IRC for Chat Bots.

IRC (especially the Twitch version; which doesn't adhere strictly to the RFC) can be complicated to parse, and ultimately
offers a less stable and less performant interface to interact with chat. On top of this Twitch has recently started
adding more and more restrictions to IRC Chat Bots (including harsher ratelimits on JOINs and Sends).

Most applications will use EventSub already for various other subscriptions, and adding chat/messages on top of this is 
a straight forward and easy process. The benefits to developers is TwitchIO does less parsing of raw, 
(undocumented in a lot of cases) strings and can now easily create usable, sane objects from JSON sent over either websocket
or webhook; this means less bugs, and less maintenance.

While indeed there is a small discrepancy between features of EventSub messages and IRC messages, the overall experience
is more performant and easier to use. Twitch is also actively working on adding more data to these message payloads, and
when they do, there will be a faster and easier turn-around for this data to be added into the library.

In the future, we are looking to devlop an ext that will run IRC, however the core lib going forward will stay with EventSub.


What is the difference between Client and Bot?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`twitchio.ext.commands.Bot` subclasses :class:`~twitchio.Client`, which means that everything :class:`~twitchio.Client`
can do, and everything belonging to :class:`~twitchio.Client` is also possible and available on :class:`~twitchio.ext.commands.Bot`.

The benefit of :class:`~twitchio.ext.commands.Bot` is that it is part of the `ext.commands <https://twitchio.dev/en/latest/exts/commands/index.html#commands>`_
extension. This extension is a powerful and easy to use package that allows the creation of :class:`~twitchio.ext.commands.Command`'s' and
:class:`~twitchio.ext.commands.Component`'s which allow you to easily create chat based commands and sub-commands, 
with argument parsing and converters, guards for fine-grained permission control, cooldowns, 
the use of :class:`~twitchio.ext.commands.Context` (featureful context around the invocation of commands; with many helpers)
and more.

Used with :class:`~twitchio.ext.commands.Component`'s and hot-reloading extension support you can easily manage your applications
codebase with multiple modules and/or pacakges, with minimal down-time.


Why does TwitchIO use PartialUser in-place of a full User object?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The large majority of both Helix endpoints and EventSub subscriptions from Twitch only send partial data relating to the user.

Creating a complete :class:`~twitchio.User` on all these events and endpoints would mean making an extra HTTP request,
which is both needlessly slow and consumes ratelimit tokens.

Since Twitch only requires the ``ID`` of users to perform actions and make requests, :class:`~twitchio.PartialUser` is an
inexpensive way of having an object that can perform actions for or against the user. However if you need extra data about the
user (such as profile image) you can always fetch the full data via :meth:`twitchio.PartialUser.user`. Since the
:class:`~twitchio.User` subclasses :class:`~twitchio.PartialUser`, all the methods available on :class:`~twitchio.PartialUser`
are also available on :class:`~twitchio.User`.

You can also create a :class:`~twitchio.PartialUser` with :meth:`~twitchio.Client.create_partialuser`.

If you are using :class:`~twitchio.ext.commands.Command`'s or anywhere :class:`~twitchio.ext.commands.Context` is available,
or are receiving a :class:`~twitchio.ChatMessage`, consider looking at :class:`~twitchio.Chatter` for a more complete object
with more information and helpers.

.. _bot-id-owner-id:

How do I get the user IDs for BOT_ID and OWNER_ID?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not know your user ID you can quickly fetch it using the :meth:`~twitchio.Client.fetch_users` method.

.. code:: python3

    import asyncio
    import twitchio

    CLIENT_ID: str = "..."
    CLIENT_SECRET: str = "..."

    async def main() -> None:
        async with twitchio.Client(client_id=CLIENT_ID, client_secret=CLIENT_SECRET) as client:
            await client.login()
            user = await client.fetch_users(logins=["chillymosh", "my_bot"])
            for u in user:
                print(f"User: {u.name} - ID: {u.id}")

    if __name__ == "__main__":
        asyncio.run(main())


How do I create a custom prefix(es) for Bot/AutoBot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~twitchio.ext.commands.Bot` and :class:`~twitchio.ext.commands.AutoBot` both allow a custom co-routine to be used
to determine the prefix for Chat Commands. This coroutine can be used to assign prefixes based on channel, chatter or other 
variables. A small example is shown below:

.. code:: python3

    from typing import Self

    import twitchio
    from twitchio.ext import commands

    class Bot(commands.Bot):
        def __init__(self) -> None:
            super().__init__(..., prefix=self.custom_prefix)
        
        async def custom_prefix(self, bot: Self, message: twitchio.ChatMessage) -> None:
            # The prefix will be ? if the chatters name startswith "cool"
            # Otherwise it will default to "!"
            # This coroutine can be used to connect to a cache or database etc to provide
            # custom settable prefixes for example...

            if message.chatter.name.startswith("cool"):
                return "?"

            return "!"


The prefix can also be passed as or returned from this function as a list of :class:`str` to allow multiple prefixes to be used.


Why do my tokens in ``.tio.tokens.json`` occasionally go missing?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is usually caused by force closing the client while it is attempting to write to the file. If you use ``Ctrl + C`` to close
your client, make sure you only do this once, and wait for up to ``5`` seconds.

Alternatively, and highly recommended, you should look at storing your tokens in a different medium, such as a SQL Database.