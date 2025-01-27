TwitchIO
#########

.. warning::

   This is a beta release. Please take care using this release in production ready applications.


TwitchIO is a powerful, asynchronous Python library for `twitch.tv <https://twitch.tv>`_.

TwitchIO aims to be intuitive and easy to use, using modern async Python and following strict typing with stateful objects
and plug-and-play extensions.

TwitchIO is more than a simple wrapper, providing ease of use when accessing the Twitch API with powerful extensions
to help create and manage applications and Twitch Chat Bots. TwitchIO is inspired by `discord.py <https://github.com/Rapptz/discord.py>`_.


**Features:**

- Modern ``async`` Python using ``asyncio``
- Fully annotated and complies with the ``pyright`` strict type-checker
- Intuitive with ease of use, using modern object orientated design
- Feature full including extensions for ``chat bots``, running ``routine tasks`` and ``playing sounds`` on stream (Conduits support soon...)
- Easily manage ``OAuth Tokens`` and data
- Built-in ``EventSub`` support via both ``Webhook`` and ``Websockets``


Help and support
----------------

- For issues or bugs please visit: `GitHub <https://github.com/PythonistaGuild/TwitchIO/issues>`_
- See our :ref:`faqs`
- Visit our `Discord <https://discord.gg/RAKc3HF>`_ for help using TwitchIO


.. warning::

   This document is a work in progress.


Getting Started
---------------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting-started/installing
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
   references/events
   references/user
   references/eventsub_subscriptions
   references/web
   references/exceptions

.. toctree::
   :maxdepth: 1
   :caption: Extension References

   exts/commands/index
   exts/routines/index
   exts/sounds/index

.. toctree::
   :maxdepth: 1
   :caption: Models

   references/eventsub_models
   references/helix_models

.. toctree::
   :maxdepth: 1
   :caption: Utils

   references/utils
