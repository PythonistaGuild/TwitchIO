.. raw:: html

   <img src="https://raw.githubusercontent.com/TwitchIO/TwitchIO/main/logo.png" class="indexLogo"></img>


TwitchIO
#########

A fully featured, powerful async Python library for the Twitch API and EventSub with modern Object-Orientated design
and stateful objects.

TwitchIO provides ease of use when accessing the Twitch API with powerful extensions for chat commands, web-frameworks and overlays 
with hot-reloadable modules to help create and manage bots, backends, websites and other applications on Twitch.

**Features:**

- Modern ``async`` Python using ``asyncio``
- Fully annotated and complies with the ``pyright`` strict type-checker
- Intuitive with ease of use, using modern object orientated design
- Conduit support for scaling and EventSub continuity
- Feature full including extensions for ``chat bots``, running ``routine tasks`` and ``overlays`` on stream
- Easily manage ``OAuth Tokens`` and data
- Built-in ``EventSub`` support via ``Webhook``, ``Websockets`` and :ref:`Conduits<Conduit Ref>`.

TwitchIO is a powerful async Python library for the twitch API and EventSub. Fully featured, modern Object-Orientated design
with stateful objects. TwitchIO is inspired by `discord.py <https://github.com/Rapptz/discord.py>`_.


Help and support
----------------

- For issues or bugs please visit: `GitHub <https://github.com/PythonistaGuild/TwitchIO/issues>`_
- See our :ref:`faqs`
- Visit our `Discord <https://discord.gg/RAKc3HF>`_ for help using TwitchIO


Getting Started
---------------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting-started/installing
   getting-started/debugging
   getting-started/migrating
   getting-started/quickstart
   getting-started/changelog
   getting-started/faq


References
----------

.. toctree::
   :maxdepth: 1
   :caption: API References

   references/client
   references/conduits/index
   references/events/index
   references/users/index
   references/eventsub_subscriptions
   references/web
   references/exceptions

.. toctree::
   :maxdepth: 1
   :caption: Extension References

   exts/commands/index
   exts/routines/index
   exts/overlays/index

.. toctree::
   :maxdepth: 1
   :caption: Models

   references/eventsub/index
   references/helix/index
   references/enums_etc

.. toctree::
   :maxdepth: 1
   :caption: Utils

   references/utils
