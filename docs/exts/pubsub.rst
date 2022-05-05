.. currentmodule:: twitchio.ext.pubsub

.. _pubsub-ref:

PubSub Ext
===========

The PubSub Ext is designed to make receiving events from twitch's PubSub websocket simple.
This ext handles all the necessary connection management, authorizing, and dispatching events through
TwitchIO's Client event system.

A quick example
----------------

.. code-block:: python3

    import twitchio
    import asyncio
    from twitchio.ext import pubsub

    my_token = "..."
    users_oauth_token = "..."
    users_channel_id = 12345
    client = twitchio.Client(token=my_token)
    client.pubsub = pubsub.PubSubPool(client)

    @client.event()
    async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
        pass # do stuff on bit redemptions

    @client.event()
    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        pass # do stuff on channel point redemptions

    async def main():
        topics = [
            pubsub.channel_points(users_oauth_token)[users_channel_id],
            pubsub.bits(users_oauth_token)[users_channel_id]
        ]
        await client.pubsub.subscribe_topics(topics)
        await client.start()

    client.loop.run_until_complete(main())

This will connect to to the pubsub server, and subscribe to the channel points and bits events
for user 12345, using the oauth token they have given us with the corresponding scopes.

Topics
-------

Each of the topics below needs to first be called with a user oauth token, and then needs channel id(s) passed to it, as such:

.. code-block:: python3

    from twitchio.ext import pubsub
    user_token = "..."
    user_channel_id = 12345
    topic = pubsub.bits(user_token)[user_channel_id]

If the topic requires multiple channel ids, they should be passed as such:

.. code-block:: python3

    from twitchio.ext import pubsub
    user_token = "..."
    user_channel_id = 12345 # the channel to listen to
    mods_channel_id = 67890 # the mod to listen for actions from
    topic = pubsub.moderation_user_action(user_token)[user_channel_id][mods_channel_id]


.. function:: bits(oauth_token: str)

    This topic listens for bit redemptions on the given channel.
    This topic dispatches the ``pubsub_bits`` client event.
    This topic takes one channel id, the channel to listen on, e.g.:

    .. code-block:: python3

        from twitchio.ext import pubsub
        user_token = "..."
        user_channel_id = 12345
        topic = pubsub.bits(user_token)[user_channel_id]

    This can be received via the following:

    .. code-block:: python3

        import twitchio
        from twitchio.ext import pubsub

        client = twitchio.Client(token="...")

        @client.event()
        async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
            ...


.. function:: bits_badge(oauth_token: str)

    This topic listens for bit badge upgrades on the given channel.
    This topic dispatches the ``pubsub_bits_badge`` client event.
    This topic takes one channel id, the channel to listen on, e.g.:

    .. code-block:: python3

        from twitchio.ext import pubsub
        user_token = "..."
        user_channel_id = 12345
        topic = pubsub.bits_badge(user_token)[user_channel_id]

    This can be received via the following:

    .. code-block:: python3

        import twitchio
        from twitchio.ext import pubsub

        client = twitchio.Client(token="...")

        @client.event()
        async def event_pubsub_bits_badge(event: pubsub.PubSubBitsBadgeMessage):
            ...


.. function:: channel_points(oauth_token: str)

    This topic listens for channel point redemptions on the given channel.
    This topic dispatches the ``pubsub_channel_points`` client event.
    This topic takes one channel id, the channel to listen on, e.g.:

    .. code-block:: python3

        from twitchio.ext import pubsub
        user_token = "..."
        user_channel_id = 12345
        topic = pubsub.channel_points(user_token)[user_channel_id]

    This can be received via the following:

    .. code-block:: python3

        import twitchio
        from twitchio.ext import pubsub

        client = twitchio.Client(token="...")

        @client.event()
        async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
            ...


.. function:: channel_subscriptions(oauth_token: str)

    This topic listens for subscriptions on the given channel.
    This topic dispatches the ``pubsub_subscription`` client event.
    This topic takes one channel id, the channel to listen on, e.g.:

    .. code-block:: python3

        from twitchio.ext import pubsub
        user_token = "..."
        user_channel_id = 12345
        topic = pubsub.channel_subscriptions(user_token)[user_channel_id]


.. function:: moderation_user_action(oauth_token: str)

    This topic listens for moderation actions on the given channel.
    This topic dispatches the ``pubsub_moderation`` client event.
    This topic takes two channel ids, the channel to listen on, and the user to listen to, e.g.:

    .. code-block:: python3

        from twitchio.ext import pubsub
        user_token = "..."
        user_channel_id = 12345
        moderator_id = 67890
        topic = pubsub.bits_badge(user_token)[user_channel_id][moderator_id]

    This event can receive many different events; :class:`PubSubModerationActionBanRequest`,
    :class:`PubSubModerationActionChannelTerms`, :class:`PubSubModerationActionModeratorAdd`, or
    :class:`PubSubModerationAction`

    It can be received via the following:

    .. code-block:: python3

        import twitchio
        from twitchio.ext import pubsub

        client = twitchio.Client(token="...")

        @client.event()
        async def event_pubsub_moderation(event):
            ...


.. function:: whispers(oauth_token: str)

    .. warning::

        This does not have a model created yet, and will error when a whisper event is received

    This topic listens for bit badge upgrades on the given channel.
    This topic dispatches the `pubsub_whisper` client event.
    This topic takes one channel id, the channel to listen to whispers from, e.g.:

    .. code-block:: python3

        from twitchio.ext import pubsub
        user_token = "..."
        listen_to_id = 12345
        topic = pubsub.whispers(user_token)[listen_to_id]

Api Reference
--------------

.. attributetable:: Topic

.. autoclass:: Topic
    :members:
    :inherited-members:

.. attributetable:: PubSubPool

.. autoclass:: PubSubPool
    :members:

.. attributetable:: PubSubChatMessage

.. autoclass:: PubSubChatMessage
    :members:

.. attributetable:: PubSubBadgeEntitlement

.. autoclass:: PubSubBadgeEntitlement
    :members:

.. attributetable:: PubSubMessage

.. autoclass:: PubSubMessage
    :members:

.. attributetable:: PubSubBitsMessage

.. autoclass:: PubSubBitsMessage
    :members:
    :inherited-members:

.. attributetable:: PubSubBitsBadgeMessage

.. autoclass:: PubSubBitsBadgeMessage
    :members:
    :inherited-members:

.. attributetable:: PubSubChannelPointsMessage

.. autoclass:: PubSubChannelPointsMessage
    :members:
    :inherited-members:

.. attributetable:: PubSubModerationAction

.. autoclass:: PubSubModerationAction
    :members:
    :inherited-members:

.. attributetable:: PubSubModerationActionBanRequest

.. autoclass:: PubSubModerationActionBanRequest
    :members:
    :inherited-members:

.. attributetable:: PubSubModerationActionChannelTerms

.. autoclass:: PubSubModerationActionChannelTerms
    :members:
    :inherited-members:

.. attributetable:: PubSubModerationActionModeratorAdd

.. autoclass:: PubSubModerationActionModeratorAdd
    :members:
    :inherited-members:
