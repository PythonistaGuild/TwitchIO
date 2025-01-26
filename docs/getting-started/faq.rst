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