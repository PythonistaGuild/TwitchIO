.. _Migrating Guide:

Migrating
#########

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

- **Web Adapters:**
   - :class:`twitchio.web.AiohttpAdapter`
   - :class:`twitchio.web.StarletteAdapter`
- **Client:**
   - :attr:`twitchio.Client.tokens`
   - :meth:`twitchio.Client.add_token`
   - :meth:`twitchio.Client.remove_token`
   - :meth:`twitchio.Client.load_tokens`
   - :meth:`twitchio.Client.save_tokens`
- **Events:**
   - :func:`twitchio.event_oauth_authorized`
- **Scopes:**
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

Running a :class:`~twitchio.Client` or :class:`~twitchio.ext.commands.Bot` hasn't changed much since version 2, however both
have now implemented ``__aenter__`` and ``__aexit__`` which allows them to be used in a Async Context Manager for easier
management of close down and cleanup. These changes along with some async internals have also been reflected in :meth:`~twitchio.Client.run`.

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


- **Added:**
   - :meth:`twitchio.Client.login`
- **Changed:**
   - :meth:`twitchio.Client.start`
   - :meth:`twitchio.Client.run`


Logging
=======

Version 3 adds a logging helper which allows for a simple and easier way to setup logging formatting for your application.

As version 3 uses logging heavily and encourages developers to use logging in place of ``print`` statements where appropriate
we would encourage you to call this function. Usually you would call this helper *before* starting the client for each logger.

If you are calling this on the ``root`` logger (default), you should only need to call this function once. 

- **Added:**
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

- **Added:**
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


- **Added:**
   - :class:`twitchio.HTTPAsyncIterator`


Changelog
=========

Added
~~~~~

- :class:`twitchio.web.AiohttpAdapter`
- :class:`twitchio.web.StarletteAdapter`

Client:

- :attr:`twitchio.Client.tokens`
- :meth:`twitchio.Client.add_token`
- :meth:`twitchio.Client.remove_token`
- :meth:`twitchio.Client.load_tokens`
- :meth:`twitchio.Client.save_tokens`
- :meth:`twitchio.Client.login`

Utils/Helpers:

- :class:`twitchio.Asset`
- :class:`twitchio.Colour`
- :class:`twitchio.Color` (An alias to :class:`twitchio.Colour`)
- :func:`twitchio.utils.setup_logging()`
- :class:`twitchio.Scopes`
- :class:`twitchio.HTTPAsyncIterator`

Events:

- :func:`twitchio.event_oauth_authorized`

Changed
~~~~~~~

Client:

- :meth:`twitchio.Client.start`
- :meth:`twitchio.Client.run`