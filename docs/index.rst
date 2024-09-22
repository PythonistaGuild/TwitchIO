TwitchIO
#########

.. warning::

   This is an alpha release. Please do not use this release in production ready applications.


.. important::

   The information in this documentation is subject to change before an official production ready release.


.. important::

   TwitchIO 3 has removed support for IRC and instead uses EventSub by default. Find more on the reasons here: ...


TwitchIO is a powerful, asynchronous Python library for `twitch.tv <https://twitch.tv>`_.

TwitchIO aims to be intuitive and easy to use, using modern async Python and following strict typing with stateful objects
and plug-and-play extensions.


**Features:**

- Modern ``async`` Python using ``asyncio``
- Fully annotated and complies with the ``pyright`` strict type-checker
- Intuitive with ease of use, using modern object orientated design
- Feature full including extensions for ``chat bots``, running ``routine tasks`` and ``playing sounds`` on stream (Conduits support soon...)
- Easily manage ``OAuth Tokens`` and data
- Built-in ``EventSub`` support via ``Webhook`` and ``Websockets``


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
   getting-started/migrating
   getting-started/quickstart
   getting-started/faq



References
----------

.. toctree::
   :maxdepth: 1
   :caption: API References

   references/client
   references/user
   references/eventsub_subscriptions

.. toctree::
   :maxdepth: 1
   :caption: Models

   references/models

.. toctree::
   :maxdepth: 1
   :caption: Utils

   references/utils

.. toctree::
   :maxdepth: 1
   :caption: Extension References

   exts/commands/api