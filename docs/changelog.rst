:orphan:

Master
=======
Massive documentation updates

- TwitchIO
    - Removed unexpected loop termination from `WSConnection._close()`
    - Fix bug where # prefixed channel names in initial_channels would not trigger :func:`twitchio.Client.event_ready`
    - :func:`User.create_clip` has been fixed by converting bool to string in http request
    - Poll endpoints added :func:`User.fetch_polls` :func:`User.create_poll` and :func:`User.end_poll`

- ext.commands
    - :func:`Bot.handle_commands` now also invokes on threads / replies
    - Cooldowns are now handled correctly per bucket.
    - Fix issue with :func:`Bot.reload_module` where module is reloaded incorrectly if exception occurs

- ext.pubsub
    - Channel subscription model fixes.

2.2.0
=====
- ext.sounds
    - Added sounds extension. Check the :ref:`sounds-ref` documentation for more information.

- TwitchIO
    - Loosen aiohttp requirements to allow 3.8.1
    - :class:`twitchio.Stream` was missing from ``__all__``. It is now available in the twitchio namespace.
    - Added ``.status``, ``.reason`` and ``.extra`` to :class:`HTTPException`
    - Fix ``Message._timestamp`` value when tag is not provided by twitch
    - Fix :func:`twitchio.Client.wait_for_ready`
    - Remove loop= parameter inside :func:`twitchio.Client.wait_for` for 3.10 compatibility
    - Add ``is_broadcaster`` check to :class:`twitchio.PartialChatter`. This is accessible as ``Context.author.is_broadcaster``
    - :func:`User.fetch_follow` will now return ``None`` if the FollowEvent does not exists
    - TwitchIO will now correctly handle error raised when only the prefix is typed in chat
    - Fix paginate logic in :func:`TwitchHTTP.request`

- ext.commands
    - Fixed an issue (`GH#273 <https://github.com/TwitchIO/TwitchIO/issues/273>`_) where cog listeners were not ejected when unloading a module

- ext.pubsub
    - Add channel subscription pubsub model.

- ext.eventsub
    - Add support for the following subscription types
        - :class:`twitchio.ext.eventsub.PollBeginProgressData`
            - ``channel.poll.begin``:
            - ``channel.poll.progress``
        - :class:`twitchio.ext.eventsub.PollEndData`
            - ``channel.poll.end``
        - :class:`twitchio.ext.eventsub.PredictionBeginProgressData`
            - ``channel.prediction.begin``
            - ``channel.prediction.progress``
        - :class:`twitchio.ext.eventsub.PredictionLockData`
            - ``channel.prediction.lock``
        - :class:`twitchio.ext.eventsub.PredictionEndData`
            - ``channel.prediction.end``

2.1.5
=====
- TwitchIO
    - Add ``user_id`` property to Client
    - Change id_cache to only cache if a value is not ``None``
    - Add :func:`Client.wait_for_ready`

2.1.4
======
- TwitchIO
    - Chatter.is_mod now uses name instead of display_name
    - Added ChannelInfo to slots
    - Remove loop= parameter for asyncio.Event in websocket for 3.10 compatibility

- ext.eventsub
    - ChannelCheerData now returns user if is_anonymous is False else None

2.1.3
======
- TwitchIO
    - Fix bug where chatter never checked for founder in is_subscriber
    - Fix rewards model so it can now handle pubsub and helix callbacks

- ext.commands
    - Fix TypeError in Bot.from_client_credentials

2.1.2
======
New logo!

- TwitchIO
    - Add :func:`Chatter.mention`
    - Re-add ``raw_usernotice`` from V1.x
    - Fix echo messages for replies
    - Fix a bug where the wrong user would be whispered
    - Fix a bug inside :func:`User.modify_stream` where the game_id key would be specified as ``"None"`` if not provided (GH#237)
    - Add support for teams and channelteams API routes
        - :class:`Team`, :class:`ChannelTeams`
        - :func:`Client.fetch_teams`
        - :func:`PartialUser.fetch_channel_teams`

- ext.commands
    - Fix issue where Bot.from_client_credentials would result in an inoperable Bot instance (GH#239)

- ext.pubsub
    - Added :func:`ext.pubsub.Websocket.pubsub_error` to support being notified of pubsub errors
    - Added :func:`ext.pubsub.Websocket.pubsub_nonce` to support being notified of pubsub nonces

- ext.eventsub
    - Patch 2.1.1 bug which breaks library on 3.7 for ext.eventsub

2.1.1
======
- TwitchIO
    - Patch a bug introduced in 2.1.0 that broke the library on python 3.7

2.1.0
======
- TwitchIO
    - Type the :class:`User` class
    - Update the library to use a proper ISO datetime parser
    - Add event_raw_usernotice event (GH#229)
    - :class:`User` fixed an issue where the User class couldn't fetch rewards (GH#214)
    - :class:`Chatter` fixed the docstring for the `badges` property
    - :func:`Chatter.is_subscriber` will now return True for founders
    - :class:`Client` change docstring on `fetch_channel`
    - Add support for the predictions API routes
        - :class:`Prediction`, :class:`Predictor`, :class:`PredictionOutcome`
        - :func:`PartialUser.end_prediction`, :func:`PartialUser.get_prediction`, :func:`PartialUser.create_prediction`
    - Add support for the schedules API routes
        - :class:`Schedule`, :class:`ScheduleSegment`, :class:`ScheduleCategory`, :class:`ScheduleVacation`
        - :func:`PartialUser.fetch_schedule`
    - Add :func:`PartialUser.modify_stream`
    - Fix bug where chatter cache would not be created
    - Fix bug where :func:`Client.wait_for` would cause internal asyncio.InvalidState errors

- ext.commands
    - General typing improvements
    - :func:`ext.commands.builtin_converters.convert_Clip` - Raise error when the regex doesn't match to appease linters. This should never be raised.
    - Added :func:`ext.commands.Context.reply` to support message replies

- ext.pubsub
    - Fixed bug with Pool.unsubscribe_topics caused by typo

- ext.eventsub
    - fix :class:`ext.eventsub.models.ChannelBanData`'s ``permanent`` attribute accessing nonexistent attrs from the event payload
    - Add documentation
