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
