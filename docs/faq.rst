:orphan:

Frequently Asked Questions
==================================
Frequently asked questions for TwitchIO 2.

.. rst-class:: this-will-duplicate-information-and-it-is-still-useful-here
.. contents:: Questions
    :local:


How can I run something on a schedule in the background?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TwitchIO has a helper extension named routines. Routines are asyncio tasks that run on a schedule in the background.
Consider reading through the :doc:`exts/routines` documentation.

How can I send a message?
~~~~~~~~~~~~~~~~~~~~~~~~~
TwitchIO is an object orientated library with stateful objects. To send a message simply use ``await .send('Hello World!)``
on any ``Messageable`` class. E.g :class:`twitchio.PartialChatter`, :class:`twitchio.Channel` or :class:`twitchio.ext.commands.Context`.
