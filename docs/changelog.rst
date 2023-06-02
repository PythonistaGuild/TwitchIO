:orphan:

Master
======
- TwitchIO
    - Additions
        - Added :func:`~twitchio.Client.fetch_global_chat_badges`
        - Added User method :func:`~twitchio.PartialUser.fetch_chat_badges`
        - Added repr for :class:`~twitchio.SearchUser`
        - Added two new events
            - Added :func:`~twitchio.Client.event_notice`
            - Added :func:`~twitchio.Client.event_raw_notice`
            
    - Bug fixes
        - Fix :func:`~twitchio.Client.search_categories` due to :attr:`~twitchio.Game.igdb_id` being added to :class:`~twitchio.Game`
        - Made Chatter :attr:`~twitchio.Chatter.id` property public
        - :func:`~twitchio.Client.event_token_expired` will now be called correctly when response is ``401 Invalid OAuth token``
        - Fix reconnect loop when Twitch sends a RECONNECT via IRC websocket

- Other
    - [speed] extra
        - Added wheels on external pypi index for cchardet and ciso8601
        - Bumped ciso8601 from >=2.2,<2.3 to >=2.2,<3
        - Bumped cchardet from >=2.1,<2.2 to >=2.1,<3

2.6.0
======
- TwitchIO
    - Additions
        - Added optional ``started_at`` and ``ended_at`` arguments to :func:`~twitchio.PartialUser.fetch_clips`
        - Updated docstring regarding new  HypeTrain contribution  method ``OTHER`` for :attr:`~twitchio.HypeTrainContribution.type`
        - Add support for ``ciso8601`` if installed
        - Added ``speed`` install flag (``pip install twitchio[speed]``) to install all available speedups
        - Added :attr:`~twitchio.Game.igdb_id` to :class:`~twitchio.Game`
        - Added ``igdb_ids`` argument to :func:`~twitchio.Client.fetch_games`
        - Added ``tags`` attribute to :class:`~twitchio.Stream`, :class:`~twitchio.ChannelInfo` and :class:`~twitchio.SearchUser`
        - Added :func:`~twitchio.PartialUser.fetch_shield_mode_status`
        - Added :func:`~twitchio.PartialUser.update_shield_mode_status`
        - Added :func:`~twitchio.PartialUser.fetch_followed_streams`
        - Added :func:`~twitchio.PartialUser.shoutout`
        - Added ``type`` arg to :func:`~twitchio.Client.fetch_streams`

    - Bug fixes
        - Fix :func:`~twitchio.PartialUser.fetch_bits_leaderboard` not handling ``started_at`` and :class:`~twitchio.BitsLeaderboard` not correctly parsing
        - Fix parsing :class:`~twitchio.ScheduleSegment` where :attr:`~twitchio.ScheduleSegment.end_time` is None
        - Fix auto reconnect of websocket. Created tasks by asyncio.create_task() need to be referred to prevent task disappearing (garbage collection)
        - Strip newlines from message content when sending or replying to IRC websocket
        - Removed unnessecary assert from :func:`~twitchio.Client.fetch_streams`

- ext.eventsub
    - Documentation
        - Updated quickstart example to reflect proper usage of callback
    - Additions
        - Updated docs regarding new HypeTrain contribution method ``other`` for :attr:`~twitchio.ext.eventsub.HypeTrainContributor.type`
        - Added Shield Status events
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_shield_mode_begin`
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_shield_mode_end`
        - Added Shoutout events
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_shoutout_create`
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_shoutout_receive`
        - Added :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_follows_v2`
        - Added support for ``type`` and ``user_id`` queries on :func:`~twitchio.ext.eventsub.EventSubClient.get_subscriptions`

    - Deprecations
        - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_follows`, use :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_follows_v2`


- ext.pubsub
    - Bug fixes
        - Fix forced RECONNECT messages

    - Additions
        - Added proper message when wrong type is passed to a topic argument
        - Added auth failure hook: :func:`~twitchio.ext.pubsub.PubSubPool.auth_fail_hook`
        - Added reconnect hook: :func:`~twitchio.ext.pubsub.PubSubPool.reconnect_hook`

2.5.0
======
- TwitchIO
    - Additions
        - Added :attr:`~twitchio.Message.first` to :class:`~twitchio.Message`
        - Added :func:`~twitchio.PartialUser.fetch_channel_emotes` to :class:`~twitchio.PartialUser`
        - Added :func:`~twitchio.Client.fetch_global_emotes` to :class:`~twitchio.Client`
        - Added :func:`~twitchio.Client.event_channel_join_failure` event:
            - This is dispatched when the bot fails to join a channel
            - This also makes the channel join error message in logs optional
    - Bug fixes
        - Fix AuthenticationError not being properly propagated when a bad token is given
        - Fix channel join failures causing `ValueError: list.remove(x): x not in list` when joining channels after the initial start
        - Added :attr:`~twitchio.Chatter.is_vip` property to Chatter
        - New PartialUser methods
            - :func:`~twitchio.PartialUser.fetch_follower_count` to fetch total follower count of a User
            - :func:`~twitchio.PartialUser.fetch_following_count` to fetch total following count of a User

        - Fix whispers that were not able to be parsed
        - Fix USERSTATE parsing incorrect user
        - Fix errors when event loop is started using `run_until_complete` to call methods prior to :func:`~twitchio.Client.run`
        - Improved handling of USERNOTICE messages and the tags created for :func:`~twitchio.Client.event_raw_usernotice`

- ext.routines
    - Additions
        - Added the :func:`~twitchio.ext.routines.Routine.change_interval` method.

- ext.commands
    - Bug fixes
        - Make sure double-quotes are properly tokenized for bot commands

- ext.sound
    - Bug fixes
        - Make system calls to ffmpeg are more robust (works on windows and linux)

- ext.eventsub
    - Additions
        - Goal subscriptions have been Added
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_goal_begin`
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_goal_progress`
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_goal_end`
            - :func:`~twitchio.ext.eventsub.event_eventsub_notification_channel_goal_begin`
            - :func:`~twitchio.ext.eventsub.event_eventsub_notification_channel_goal_progress`
            - :func:`~twitchio.ext.eventsub.event_eventsub_notification_channel_goal_end`

        - Channel subscription end
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_channel_subscription_end`
        - User authorization grant
            - :func:`~twitchio.ext.eventsub.EventSubClient.subscribe_user_authorization_granted`

        - HypeTrainBeginProgressData now has the :attr:`~twitchio.ext.eventsub.HypeTrainBeginProgressData.level`


    - Bug fixes
        - Correct typo in :class:`~twitchio.ext.eventsub.HypeTrainBeginProgressData` attribute :attr:`~twitchio.ext.eventsub.HypeTrainBeginProgressData.expires`
        - Correct typo "revokation" to "revocation" in server _message_types.

- ext.pubsub
    - Additions
        - Websocket automatically handles "RECONNECT" requests by Twitch
    - Bug fixes
        - "type" of :class:`~twitchio.ext.pubsub.PubSubModerationActionChannelTerms` now uses the correct type data
        - Correct typo in :class:`~twitchio.ext.eventsub.HypeTrainBeginProgressData` attribute :attr:`~twitchio.ext.eventsub.HypeTrainBeginProgressData.expires`
        - Unsubscribing from PubSub events works again
        - Fix a forgotten nonce in :func:`~twitchio.ext.pubsub.websocket._send_topics`
        - :class:`~twitchio.ext.pubsub.PubSubModerationActionChannelTerms` now uses the correct type data

2.4.0
======
- TwitchIO
    - Additions
        - Added :func:`~twitchio.Client.event_reconnect` to :class:`~twitchio.Client`
        - Add attribute docs to :class:`~twitchio.PartialUser` and :class:`~twitchio.User`
        - Added following new :class:`~twitchio.PartialUser` methods:
            - :func:`~twitchio.PartialUser.create_custom_reward`
            - :func:`~twitchio.PartialUser.chat_announcement`
            - :func:`~twitchio.PartialUser.delete_chat_messages`
            - :func:`~twitchio.PartialUser.fetch_channel_vips`
            - :func:`~twitchio.PartialUser.add_channel_vip`
            - :func:`~twitchio.PartialUser.remove_channel_vip`
            - :func:`~twitchio.PartialUser.add_channel_moderator`
            - :func:`~twitchio.PartialUser.remove_channel_moderator`
            - :func:`~twitchio.PartialUser.start_raid`
            - :func:`~twitchio.PartialUser.cancel_raid`
            - :func:`~twitchio.PartialUser.ban_user`
            - :func:`~twitchio.PartialUser.timeout_user`
            - :func:`~twitchio.PartialUser.unban_user`
            - :func:`~twitchio.PartialUser.send_whisper`
        - Added following new :class:`~twitchio.Client` methods:
            - :func:`~twitchio.Client.fetch_chatters_colors`
            - :func:`~twitchio.Client.update_chatter_color`
            - :func:`~twitchio.Client.fetch_channels`
        - Add ``duration`` and ``vod_offset`` attributes to :class:`~twitchio.Clip`
        - Added repr for :class:`~twitchio.CustomReward`
        - Added repr for :class:`~twitchio.PredictionOutcome`
        - Add extra attributes to :class:`~twitchio.UserBan`
    - Bug fixes
        - Added ``self.registered_callbacks = {}`` to :func:`~twitchio.Client.from_client_credentials`
        - Allow empty or missing initial_channels to trigger :func:`~twitchio.Client.event_ready`
        - Corrected :func:`twitchio.CustomRewardRedemption.fulfill` endpoint typo and creation
        - Corrected :func:`twitchio.CustomRewardRedemption.refund` endpoint typo and creation
        - Changed :func:`~twitchio.Client.join_channels` logic to handle bigger channel lists better
        - Corrected :class:`~twitchio.Predictor` slots and user keys, repr has also been added
        - Updated IRC parser to not strip colons from beginning of messages
        - Updated IRC parser to not remove multiple spaces when clumped together
        - Fixed :func:`twitchio.Client.start` exiting immediately
        - Chatters will now update correctly when someone leaves chat
        - Fixed a crash when twitch sends a RECONNECT notice

- ext.commands
    - Bug fixes
        - Add type conversion for variable positional arguments
        - Fixed message content while handling commands in reply messages

- ext.pubsub
    - Bug fixes
        - :class:`~twitchio.ext.pubsub.PubSubModerationAction` now handles missing keys

- ext.eventsub
    - Additions
        - Added Gift Subcriptions subscriptions for gifting other users Subs:
            - Subscribed via :func:`twitchio.ext.eventsub.EventSubClient.subscribe_channel_subscription_gifts`
            - Callback function is :func:`twitchio.ext.eventsub.event_eventsub_notification_subscription_gift`
        - Added Resubscription Message subscriptions for Resub messages:
            - Subscribed via :func:`twitchio.ext.eventsub.EventSubClient.subscribe_channel_subscription_messages`
            - Callback function is :func:`twitchio.ext.eventsub.event_eventsub_notification_subscription_message`
        - Added :func:`twitchio.ext.eventsub.EventSubClient.delete_all_active_subscriptions` for convenience
        - Created an Eventsub-specific :class:`~twitchio.ext.eventsub.CustomReward` model

2.3.0
=====
Massive documentation updates

- TwitchIO
    - Additions
        - Added ``retain_cache`` kwarg to Client and Bot. Default is True.
        - Poll endpoints added:
            - :func:`twitchio.PartialUser.fetch_polls`
            - :func:`twitchio.PartialUser.create_poll`
            - :func:`twitchio.PartialUser.end_poll`
        - Added :func:`twitchio.PartialUser.fetch_goals` method
        - Added :func:`twitchio.PartialUser.fetch_chat_settings` and :func:`twitchio.PartialUser.update_chat_settings` methods
        - Added :func:`twitchio.Client.part_channels` method
        - Added :func:`~twitchio.Client.event_channel_joined` event. This is dispatched when the bot joins a channel
        - Added first kwarg to :func:`twitchio.CustomReward.get_redemptions`

    - Bug fixes
        - Removed unexpected loop termination from ``WSConnection._close()``
        - Fix bug where # prefixed channel names and capitals in initial_channels would not trigger :func:`~twitchio.Client.event_ready`
        - Adjusted join channel rate limit handling
        - :func:`twitchio.PartialUser.create_clip` has been fixed by converting bool to string in http request
        - :attr:`~twitchio.Client.fetch_cheermotes` color attribute corrected
        - :func:`twitchio.PartialUser.fetch_channel_teams` returns empty list if no teams found rather than unhandled error
        - Fix :class:`twitchio.CustomRewardRedemption` so :func:`twitchio.CustomReward.get_redemptions` returns correctly

- ext.commands
    - :func:`twitchio.ext.commands.Bot.handle_commands` now also invokes on threads / replies
    - Cooldowns are now handled correctly per bucket.
    - Fix issue with :func:`twitchio.ext.commands.Bot.reload_module` where module is reloaded incorrectly if exception occurs
    - Additions
        - :func:`twitchio.ext.commands.Bot.handle_commands` now also invokes on threads / replies

    - Bug fixes
        - Cooldowns are now handled correctly per bucket.
        - Fix issue with :func:`twitchio.ext.Bot.reload_module` where module is reloaded incorrectly if exception occurs

- ext.pubsub
    - Channel subscription model fixes and additional type hints for Optional return values
    - :class:`~twitchio.ext.pubsub.PubSubBitsMessage` model updated to return correct data and updated typing
    - :class:`~twitchio.ext.pubsub.PubSubBitsBadgeMessage` model updated to return correct data and updated typing
    - :class:`~twitchio.ext.pubsub.PubSubChatMessage` now correctly returns a string rather than int for the Bits Events

2.2.0
=====
- ext.sounds
    - Added sounds extension. Check the :ref:`sounds-ref` documentation for more information.

- TwitchIO
    - Loosen aiohttp requirements to allow 3.8.1
    - :class:`~twitchio.Stream` was missing from ``__all__``. It is now available in the twitchio namespace.
    - Added ``.status``, ``.reason`` and ``.extra`` to :class:`HTTPException`
    - Fix ``Message._timestamp`` value when tag is not provided by twitch
    - Fix :func:`~twitchio.Client.wait_for_ready`
    - Remove loop= parameter inside :func:`~twitchio.Client.wait_for` for 3.10 compatibility
    - Add :attr:`~twitchio.Chatter.is_broadcaster` check to :class:`~twitchio.PartialChatter`. This is accessible as ``Context.author.is_broadcaster``
    - :func:`~twitchio.PartialUser.fetch_follow` will now return ``None`` if the FollowEvent does not exists
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
