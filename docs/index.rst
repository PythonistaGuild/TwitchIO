.. raw:: html

   <img src="https://raw.githubusercontent.com/TwitchIO/TwitchIO/main/logo.png" class="indexLogo"></img>


TwitchIO
#########

.. warning::

   This is a beta release. Please take care using this release in production ready applications.


.. important::

   This documentation is for **Version 3**. For **Version 2.10** see: `2.10 Docs <https://twitchio.dev/en/historical-2.10.0/>`_.


TwitchIO is a powerful async Python library for the twitch API and EventSub. Fully featured, modern Object-Orientated design
with stateful objects.

TwitchIO provides ease of use when accessing the Twitch API with powerful extensions and hot-reloadable modules to help create
and manage applications on twitch. TwitchIO is inspired by `discord.py <https://github.com/Rapptz/discord.py>`_.


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
   references/enums_etc

.. toctree::
   :maxdepth: 1
   :caption: Utils

   references/utils
