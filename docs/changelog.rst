.. currentmodule:: twitchio

2.1.0
======
- TwitchIO
    - Type the :class:`User` class
    - Update the library to use a proper ISO datetime parser.
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
    - Added :func:`ext.pubsub.Websocket.pubsub_error` to support being notified of pubsub errors
    - Added :func:`ext.pubsub.Websocket.pubsub_nonce` to support being notified of pubsub nonces

- ext.eventsub
    - fix :class:`ext.eventsub.models.ChannelBanData`'s ``permanent`` attribute accessing nonexistent attrs from the event payload
    - Add documentation
