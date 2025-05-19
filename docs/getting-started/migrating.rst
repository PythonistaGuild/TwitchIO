.. _Migrating Guide:

Migrating from Twitchio 2.x to 3.x
##################################

.. warning::

   This document is a work in progress.


Version 2 to version 3 has many breaking changes, new systems, new implementations and new designs that will require rewriting
any existing applications. Some of these changes will feel similar (such as ext.commands), while others have been completely
removed (such as IRC, see: :ref:`FAQ <irc_faq>`), or are new or significantly changed. This document serves to hopefully make
it easier to move over to version 3.


Python Version Changes
======================

TwitchIO version 3 uses a minimum Python version of ``3.11``. See: :ref:`Installing <installing>` for more information.


Token Management and OAuth
==========================

One of the main focuses of version 3 was to make it easier for developers to manage authentication tokens.

When starting or restarting the :class:`twitchio.Client` a new ``App Token`` is automatically (re)generated. This behaviour can be
changed by passing an ``App Token`` to :meth:`~twitchio.Client.start`, :meth:`~twitchio.Client.run` or :meth:`~twitchio.Client.login`
however since there are no ratelimits on this endpoint, it is generally safer and easier to use the deafult.

The following systems have been added to help aid in token management in version 3:

**Web Adapters:**

- :class:`twitchio.web.AiohttpAdapter`
- :class:`twitchio.web.StarletteAdapter`

**Client:**

- :attr:`twitchio.Client.tokens`
- :meth:`twitchio.Client.add_token`
- :meth:`twitchio.Client.remove_token`
- :meth:`twitchio.Client.load_tokens`
- :meth:`twitchio.Client.save_tokens`

**Events:**

- :func:`twitchio.event_oauth_authorized`
- :func:`twitchio.event_token_refreshed`

**Scopes:**

- :class:`twitchio.Scopes`


By default a web adapter is started and ran alongside your application when it starts. The web adapters are ready with 
batteries-included to handle OAuth and EventSub via webhooks. 

The default redirect URL for OAuth is ``http://localhost:4343/oauth/callback``
which can be added to your application in the `Twitch Developer Console <https://dev.twitch.tv/console>`_. You can then
visit ``http://localhost:4343/oauth?scopes=`` with a list of provided scopes to authenticate and add the ``User Token`` to the
:class:`~twitchio.Client`. 

After closing the :class:`~twitchio.Client` gracefully, all tokens currently managed will be 
saved to a file named ``.tio.tokens.json``. This same file is also read and loaded when the :class:`~twitchio.Client` starts.

Consider reading the :ref:`Quickstart Guide <quickstart>` for an example on this flow, and implementing a SQL Database as 
an alternative for token storage.

Internally version 3 also implements a Managed HTTPClient which handles validating and refreshing loaded tokens automatically.

Another benefit of the Managed HTTPClient is it attempts to find and use the appropriate token for each request, unless explicitly
overriden, which can be done on most on methods that allow it via the ``token_for`` or ``token`` parameters.


Running a Client/Bot
====================

Running a :class:`~twitchio.Client` or :class:`~twitchio.ext.commands.Bot` hasn't changed much since version 2, however there are
some major differences that should be taken into consideration:

- IRC was removed from the core of TwitchIO. This means subscribing to chat and other chat related events is now done via ``EventSub``. This results in the removal of constructor parameters ``initial_channels``, ``heartbeat`` and ``retain_cache``.
- Instead of listing the usernames of the channels you want the bot to join, you let the web adapter listen for when a user wants to give you ``channel:bot`` permissions; then you subscribe to messages for that channel with ``subscribe_webhook()`` or ``subscribe_websockes()``. For example: ``subscribe_websocket(payload=eventsub.ChatMessageSubscription(broadcaster_user_id=..., user_id=...)``.
- If you *really* need to send messages to a channel that hasn't explicitly granted you the ``channel:bot`` scope, you can use the ``token_for`` option to override the token twitchio would normally choose. But note that you'll only be able to connect up to 100 channels simuntaniously; a limit that wouldn't apply when using ``channel:bot`` instead. More info on Twitch-imposed rate limits here: https://dev.twitch.tv/docs/chat/#rate-limits
- ``App Tokens`` are generated automatically on start-up and there is rarely a need to provide one. However the option still exists via :meth:`~twitchio.Client.start` and :meth:`~twitchio.Client.login`.
- TwitchIO 3 uses a much more modern asyncio design which results in the removal of any ``loop`` semantics including the constructor parameter ``loop``. Internally the start and close of the bot has also been changed, resulting in a more user-friendly interface.
- Implemented ``__aenter__`` and ``__aexit__`` which allows them to be used in a Async Context Manager for easier management of close down and cleanup. These changes along with some async internals have also been reflected in :meth:`~twitchio.Client.run`.

You can also :meth:`~twitchio.Client.login` the :class:`~twitchio.Client` without running a continuous asyncio event loop, E.g.
for making HTTP Requests only or for using the :class:`~twitchio.Client` in an already running event loop.

However we recommend following the below as a simple and modern way of starting your Client/Bot:

.. code:: python3

    import asyncio

    ...


    if __name__ == "__main__":

        async def main() -> None:
            twitchio.utils.setup_logging()

            async with Bot() as bot:
                await bot.start()
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            ...


In addition to the above changes, the :class:`~twitchio.Client` has undergone other various changes:

- Added the :meth:`~twitchio.Client.setup_hook` callback which allows async setup on the :class:`~twitchio.Client` after ``login`` but before the :class:`~twitchio.Client` starts completely.
- EventSub is fully managed on the :class:`~twitchio.Client`. See: :meth:`~twitchio.Client.subscribe_websocket` and :meth:`~twitchio.Client.subscribe_webhook`.
- ``fetch_*`` methods no longer accept a ``token`` parameter. Instead you can pass ``token_for`` which is the ``user ID`` of the token you wish to use. However this is rarely needed as TwitchIO will select the most appropriate token for the call.
- Some ``fetch_*`` methods which require pagination return a :class:`twitchio.HTTPAsyncIterator` for ease of use.


.. note::

   Remember: :class:`~twitchio.ext.commands.Bot` subclasses :class:`~twitchio.Client` and should be treated as a :class:`~twitchio.Client` with additional features.


**Added:**

- Parameter ``bot_id``
- Parameter ``redirect_uri``
- Parameter ``scopes``
- Parameter ``session``
- Parameter ``adapter``
- Parameter ``fetch_client_user``
- :attr:`twitchio.Client.bot_id`
- :attr:`twitchio.Client.tokens`
- :attr:`twitchio.Client.user`
- :meth:`twitchio.Client.add_listener`
- :meth:`twitchio.Client.add_token`
- :meth:`twitchio.Client.delete_all_eventsub_subscriptions`
- :meth:`twitchio.Client.delete_eventsub_subscription`
- :meth:`twitchio.Client.delete_websocket_subscription`
- :meth:`twitchio.Client.fetch_badges`
- :meth:`twitchio.Client.fetch_drop_entitlements`
- :meth:`twitchio.Client.fetch_emote_sets`
- :meth:`twitchio.Client.fetch_emotes`
- :meth:`twitchio.Client.fetch_eventsub_subscriptions`
- :meth:`twitchio.Client.fetch_extension_transactions`
- :meth:`twitchio.Client.fetch_extensions`
- :meth:`twitchio.Client.fetch_game`
- :meth:`twitchio.Client.fetch_stream_markers`
- :meth:`twitchio.Client.fetch_team`
- :meth:`twitchio.Client.listen`
- :meth:`twitchio.Client.load_tokens`
- :meth:`twitchio.Client.login`
- :meth:`twitchio.Client.remove_listener`
- :meth:`twitchio.Client.remove_token`
- :meth:`twitchio.Client.save_tokens`
- :meth:`twitchio.Client.setup_hook`
- :meth:`twitchio.Client.subscribe_webhook`
- :meth:`twitchio.Client.subscribe_websocket`
- :meth:`twitchio.Client.update_entitlements`
- :meth:`twitchio.Client.update_extensions`
- :meth:`twitchio.Client.websocket_subscriptions`


**Changed:**

- :meth:`twitchio.Client.start`
- :meth:`twitchio.Client.run`
- :meth:`twitchio.Client.wait_for`
   - ``predicate`` and ``timeout`` are now both keyword-only arguments.
   - ``predicate`` is now async.
- ``Client.wait_for_ready`` is now :meth:`twitchio.Client.wait_until_ready`
- ``Client.create_user`` is now :meth:`twitchio.Client.create_partialuser`
- ``Client.fetch_chatters_colors`` is now :meth:`~twitchio.Client.fetch_chatters_color`
- ``Client.fetch_content_classification_labels`` is now :meth:`~twitchio.Client.fetch_classifications`


**Removed:**

- Client parameter ``initial_channels``
- Client parameter ``heartbeat``
- Client parameter ``retain_cache``
- Client parameter ``loop``
- ``Client.connected_channels``
- ``Client.loop``
- ``Client.nick``
- ``Client.user_id``
- ``Client.events``
- ``Client.connect()``
- ``Client.event_channel_join_failure()``
- ``Client.event_channel_joined()``
- ``Client.event_join()``
- ``Client.event_mode()``
- ``Client.event_notice()``
- ``Client.event_part()``
- ``Client.event_raw_data()``
- ``Client.event_raw_notice()``
- ``Client.event_raw_usernotice()``
- ``Client.event_reconnect()``
- ``Client.event_token_expired()``
- ``Client.event_usernotice_subscription()``
- ``Client.event_userstate()``
- ``Client.get_channel()``
- ``Client.get_webhook_subscriptions()``
- ``Client.join_channels()``
- ``Client.part_channels()``
- ``Client.update_chatter_color()``
- ``Client.from_client_credentials()``
- ``Client.fetch_global_chat_badges()``
- ``Client.fetch_global_emotes()``


Logging
=======

Version 3 adds a logging helper which allows for a simple and easier way to setup logging formatting for your application.

As version 3 uses logging heavily and encourages developers to use logging in place of ``print`` statements where appropriate
we would encourage you to call this function. Usually you would call this helper *before* starting the client for each logger.

If you are calling this on the ``root`` logger (default), you should only need to call this function once. 

**Added:**

- :func:`twitchio.utils.setup_logging()`


Assets and Colours
==================

In version 2, all images, colour/hex codes and other assets were usually just strings of the hex or a URL pointing to the 
asset.

In version 3 all assets are now a special class :class:`twitchio.Asset` which can be used to download, save and manage 
the various assets available from Twitch such as :attr:`twitchio.Game.box_art`.

Any colour that Twitch returns as a valid HEX or RGB code is also a special class :class:`twitchio.Colour`. This class 
implements various dunders such as ``__format__`` which will help in using the :class:`~twitchio.Colour` in strings,
other helpers to convert the colour data to different formats, and classmethod helpers to retrieve default colours.

**Added:**

- :class:`twitchio.Asset`
- :class:`twitchio.Colour`
- :class:`twitchio.Color` (An alias to :class:`twitchio.Colour`)


HTTP Async Iterator
===================

In previous versions all requests made to Twitch were made in a single call and did not have an option to paginate.

With version 3 you will notice paginated endpoints now return a :class:`twitchio.HTTPAsyncIterator`. This class is a async
iterator which allows the following semantics:

``await method(...)``

**or**

``async for item in method(...)``

This allows fetching a flattened list of the first page of results only (``await``) or making paginated requests as an iterator
(``async for``).

You can flatten a paginated request by using a list comprehension.

.. code-block:: python3

   # Flatten and return first page (20 results)
   streams = await bot.fetch_streams()

   # Flatten and return up to 1000 results (max 100 per page) which equates to 10 requests...
   streams = [stream async for stream in bot.fetch_streams(first=100, max_results=1000)]

   # Loop over results until we manually stop...
   async for item in bot.fetch_streams(first=100, max_results=1000):
      # Some logic...
      ...
      break

Twitch endpoints only allow a max of ``100`` results per page, with a default of ``20``.

You can identify endpoints which support the :class:`twitchio.HTTPAsyncIterator` by looking for the following on top of the
function in the docs:

.. raw:: html

   <div class="sig sig-object py">
      <div class="sig-usagetable">
         <span class="pre">
            <em>await </em>
            <span class="sig-name">.endpoint(...)</span>
            <span>-&gt; </span>
            <a href="https://docs.python.org/3/library/stdtypes.html#list">list</a>[T]<br>
            <em>async for</em> item in <span class="sig-name">.endpoint(...)</span>:
         </span>
      </div>
   </div>
   </br>


**Added:**

- :class:`twitchio.HTTPAsyncIterator`

Events
======

Events in version 3 have changed internally, however user facing should be fairly similar. One main difference to note
is that all events accept exactly one argument, a payload containing relevant event data, with the exception of 
:func:`twitchio.event_ready` which accepts exactly ``0`` arguments, and some command events which accept
:class:`twitchio.ext.commands.Context` only.

For a list of events and their relevant payloads see the :ref:`Event Reference <Event Ref>`.

**Changed:**

- :ref:`Events <Event Ref>` now accept a single argument, ``payload`` or :class:`~twitchio.ext.commands.Context`, with one exception (:func:`twitchio.event_ready`).


Wait For
========

:meth:`twitchio.Client.wait_for` has changed internally however should act similiary to previous versions with some notes:

- ``predicate`` and ``timeout`` are now both keyword-only arguments.
- ``predicate`` is now async.

:meth:`twitchio.Client.wait_for` returns the payload of the waiting event.

To wait until the bot is ready, consider using :meth:`twitchio.Client.wait_until_ready`.

**Changed:**

- :meth:`twitchio.Client.wait_for`
   - ``predicate`` and ``timeout`` are now both keyword-only arguments.
   - ``predicate`` is now async.
- ``Client.wait_for_ready`` is now :meth:`twitchio.Client.wait_until_ready`



Changelog
=========

Environment
~~~~~~~~~~~

Python:

- Minimum Python version changed from ``3.7`` to ``3.11``.

Dependencies:

- Bumped ``aiohttp`` minimum version to ``3.9.1``
- Added Optional ``[starlette]``
- Added Optional ``[docs]`` (For developing the documentation)
- Added Optional ``[dev]`` (Required tools for development)
- Removed ``iso8601``
- Removed ``typing-extensions``
- Removed Optional ``[sounds]``
- Removed Optional ``[speed]``


Added
~~~~~

- :class:`twitchio.web.AiohttpAdapter`
- :class:`twitchio.web.StarletteAdapter`

Client:

- Parameter ``bot_id``
- Parameter ``redirect_uri``
- Parameter ``scopes``
- Parameter ``session``
- Parameter ``adapter``
- Parameter ``fetch_client_user``
- :attr:`twitchio.Client.bot_id`
- :attr:`twitchio.Client.tokens`
- :attr:`twitchio.Client.user`
- :meth:`twitchio.Client.add_listener`
- :meth:`twitchio.Client.add_token`
- :meth:`twitchio.Client.delete_all_eventsub_subscriptions`
- :meth:`twitchio.Client.delete_eventsub_subscription`
- :meth:`twitchio.Client.delete_websocket_subscription`
- :meth:`twitchio.Client.fetch_badges`
- :meth:`twitchio.Client.fetch_drop_entitlements`
- :meth:`twitchio.Client.fetch_emote_sets`
- :meth:`twitchio.Client.fetch_emotes`
- :meth:`twitchio.Client.fetch_eventsub_subscriptions`
- :meth:`twitchio.Client.fetch_extension_transactions`
- :meth:`twitchio.Client.fetch_extensions`
- :meth:`twitchio.Client.fetch_game`
- :meth:`twitchio.Client.fetch_stream_markers`
- :meth:`twitchio.Client.fetch_team`
- :meth:`twitchio.Client.listen`
- :meth:`twitchio.Client.load_tokens`
- :meth:`twitchio.Client.login`
- :meth:`twitchio.Client.remove_listener`
- :meth:`twitchio.Client.remove_token`
- :meth:`twitchio.Client.save_tokens`
- :meth:`twitchio.Client.setup_hook`
- :meth:`twitchio.Client.subscribe_webhook`
- :meth:`twitchio.Client.subscribe_websocket`
- :meth:`twitchio.Client.update_entitlements`
- :meth:`twitchio.Client.update_extensions`
- :meth:`twitchio.Client.websocket_subscriptions`

Utils/Helpers:

- :class:`twitchio.Asset`
- :class:`twitchio.Colour`
- :class:`twitchio.Color` (An alias to :class:`twitchio.Colour`)
- :func:`twitchio.utils.setup_logging()`
- :class:`twitchio.Scopes`
- :class:`twitchio.HTTPAsyncIterator`

Events:

- :func:`twitchio.event_oauth_authorized`
- :func:`twitchio.event_token_refreshed`

Changed
~~~~~~~

Client:

- :meth:`twitchio.Client.start`
- :meth:`twitchio.Client.run`
- :meth:`twitchio.Client.wait_for`
   - ``predicate`` and ``timeout`` are now both keyword-only arguments.
   - ``predicate`` is now async.
- ``Client.wait_for_ready`` is now :meth:`twitchio.Client.wait_until_ready`
- ``Client.create_user`` is now :meth:`twitchio.Client.create_partialuser`
- ``Client.fetch_chatters_colors`` is now :meth:`~twitchio.Client.fetch_chatters_color`
- ``Client.fetch_content_classification_labels`` is now :meth:`~twitchio.Client.fetch_classifications`

Removed
~~~~~~~

- ``twitchio.ext.pubsub``
   - Twitch no longer supports PubSub.
- ``IRC``
   - See: :ref:`FAQ <irc_faq>` for more information.

Client:

- Client parameter ``initial_channels``
- Client parameter ``heartbeat``
- Client parameter ``retain_cache``
- Client parameter ``loop``
- ``Client.connected_channels``
- ``Client.loop``
- ``Client.nick``
- ``Client.user_id``
- ``Client.events``
- ``Client.connect()``
- ``Client.event_channel_join_failure()``
- ``Client.event_channel_joined()``
- ``Client.event_join()``
- ``Client.event_mode()``
- ``Client.event_notice()``
- ``Client.event_part()``
- ``Client.event_raw_data()``
- ``Client.event_raw_notice()``
- ``Client.event_raw_usernotice()``
- ``Client.event_reconnect()``
- ``Client.event_token_expired()``
- ``Client.event_usernotice_subscription()``
- ``Client.event_userstate()``
- ``Client.get_channel()``
- ``Client.get_webhook_subscriptions()``
- ``Client.join_channels()``
- ``Client.part_channels()``
- ``Client.update_chatter_color()``
- ``Client.from_client_credentials()``
- ``Client.fetch_global_chat_badges()``
- ``Client.fetch_global_emotes()``