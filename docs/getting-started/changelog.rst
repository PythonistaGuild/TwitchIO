:orphan:

.. _changes:


Changelog
##########

3.3.0b

- twitchio
    - Additions
        - Added - :class:`~twitchio.SuspiciousChatUser` model.
        - Added - :func:`~twitchio.PartialUser.add_suspicious_chat_user` to :class:`~twitchio.PartialUser`.
        - Added - :func:`~twitchio.PartialUser.remove_suspicious_chat_user` to :class:`~twitchio.PartialUser`.

3.2.0
======
- twitchio
    - Additions
        - Added - :class:`~twitchio.UserAuthorisation` model.
        - Added - :func:`~twitchio.Client.fetch_auth_by_users` to :class:`~twitchio.Client`.
        - Added - :func:`~twitchio.PartialUser.fetch_auth` to :class:`~twitchio.PartialUser`.
        - Added - :func:`~twitchio.PartialUser.fetch_stream` to :class:`~twitchio.PartialUser` as a helper method.
        - Added - :func:`~twitchio.PartialUser.fetch_hype_train_status` to :class:`~twitchio.PartialUser`. 
            This replaces :func:`~twitchio.PartialUser.fetch_hype_train_events` which has been deprecated.
        - Added - :attr:`~twitchio.Chatter.lead_moderator`.
        - Added - :func:`~twitchio.ext.commands.is_lead_moderator` guard.
        - Added - New optional title and duration arguments for :func:`~twitchio.PartialUser.create_clip`.
        - Added - :func:`twitchio.ChatMessage.delete` method.
        - Added - :func:`twitchio.Chatter.delete_message` method.
        - Added - ``client`` keyword-only argument to web adapters; allowing adapters to have a :class:`~twitchio.Client` available at initialization.
        - Added - web adapters are now ``Generic`` and accept a :class:`~twitchio.Client` or any derivative/subclass.
        - Added - :func:`twitchio.Scopes.from_url` classmethod.
        - Added the ``oauth_path`` and ``redirect_path`` arguments to web adapters.

    - Changes
        - :attr:`~twitchio.Chatter.moderator` returns True for Lead Moderator role.
        - :func:`~twitchio.PartialUser.create_clip` `has_delay` argument has been deprecated.

    - Bug fixes
        - Fix :func:`~twitchio.utils.setup_logging` breaking coloured formatting on ``CRITICAL`` logging level.
        - Fix :class:`~models.eventsub_.ChannelPointsAutoRedeemAdd` now accounts for attribute message in payload to be None.
        - Fix :class:`~models.eventsub_.ChannelBitsUse` now accounts for attribute message in payload to be None.
        - Fix some typing issues with adapters in :class:`~twitchio.Client`.
        - Fixed a bug causing conduit websockets to be treated as eventsub websockets and fail after a reconnect attempt.
        - Fixed incorrect documentation in :func:`~twitchio.PartialUser.fetch_moderators`.


3.1.0
=====

- twitchio
    - Additions
        - Added ``__hash__`` to :class:`twitchio.PartialUser` allowing it to be used as a key.
        - Added the ``--create-new`` interactive script to ``__main__`` allowing boiler-plate to be generated for a new Bot.

    - Changes
        - Adjusted the Starlette logging warning wording.
        - Delayed the Starlette logging warning and removed it from ``web/__init__.py``.
        - :class:`twitchio.PartialUser`, :class:`twitchio.User` and :class:`twitchio.Chatter` now have ``__hash__`` implementations derived from :class:`~twitchio.PartialUser`, which use the unique ID.

    - Bug fixes
        - :meth:`twitchio.Clip.fetch_video` now properly returns ``None`` when the :class:`twitchio.Clip` has no ``video_id``.
        - :class:`twitchio.ChatterColor` no longer errors whan no valid hex is provided by Twitch.
        - Some general typing/spelling errors cleaned up in Documentation and Logging.
        - Removed some redundant logging.
        - Fixed internal parsing of the payload received in :meth:`twitchio.PartialUser.warn_user` which was resulting in an error.

- twitchio.Client
    - Bug fixes
        - Fixed tokens not being saved properly when ``load_tokens`` was ``False`` in :meth:`twitchio.Client.login`

- twitchio.AutoClient
    - Additions
        - Added ``force_subscribe`` keyword argument to :class:`twitchio.AutoClient`, allowing subscriptions passed to be made everytime the client is started.
        - Added ``force_scale`` keyword argument to :class:`twitchio.AutoClient`, allowing the associated Conduit to be scaled up/down on startup.
        - Added more informative logging in places.

    - Changes
        - Optimised the cleanup of conduit websockets. This largely only affects applications connected to large amounts of shards.

- twitchio.ext.commands.AutoBot
    - Updates are identical to the updates made in the ``twitchio.AutoClient`` changelog above.

- twitchio.eventsub
    - Additions
        - Added :meth:`twitchio.AutomodMessageHold.respond`
        - Added :meth:`twitchio.AutomodSettingsUpdate.respond`
        - Added :meth:`twitchio.AutomodTermsUpdate.respond`
        - Added :meth:`twitchio.ChannelBitsUse.respond`
        - Added :meth:`twitchio.ChannelUpdate.respond`
        - Added :meth:`twitchio.ChannelFollow.respond`
        - Added :meth:`twitchio.ChannelAdBreakBegin.respond`
        - Added :meth:`twitchio.ChannelChatClear.respond`
        - Added :meth:`twitchio.ChannelChatClearUserMessages.respond`
        - Added :meth:`twitchio.ChatMessage.respond`
        - Added :meth:`twitchio.ChatNotification.respond`
        - Added :meth:`twitchio.ChatMessageDelete.respond`
        - Added :meth:`twitchio.ChatSettingsUpdate.respond`
        - Added :meth:`twitchio.SharedChatSessionBegin.respond`
        - Added :meth:`twitchio.SharedChatSessionUpdate.respond`
        - Added :meth:`twitchio.SharedChatSessionEnd.respond`
        - Added :meth:`twitchio.ChannelSubscribe.respond`
        - Added :meth:`twitchio.ChannelSubscriptionEnd.respond`
        - Added :meth:`twitchio.ChannelSubscriptionGift.respond`
        - Added :meth:`twitchio.ChannelSubscriptionMessage.respond`
        - Added :meth:`twitchio.ChannelCheer.respond`
        - Added :meth:`twitchio.ChannelBan.respond`
        - Added :meth:`twitchio.ChannelUnban.respond`
        - Added :meth:`twitchio.ChannelUnbanRequest.respond`
        - Added :meth:`twitchio.ChannelUnbanRequestResolve.respond`
        - Added :meth:`twitchio.ChannelModerate.respond`
        - Added :meth:`twitchio.ChannelModeratorAdd.respond`
        - Added :meth:`twitchio.ChannelModeratorRemove.respond`
        - Added :meth:`twitchio.ChannelPointsAutoRedeemAdd.respond`
        - Added :meth:`twitchio.ChannelPointsReward.respond`
        - Added :meth:`twitchio.ChannelPointsRedemptionAdd.respond`
        - Added :meth:`twitchio.ChannelPointsRedemptionUpdate.respond`
        - Added :meth:`twitchio.ChannelPollBegin.respond`
        - Added :meth:`twitchio.ChannelPollProgress.respond`
        - Added :meth:`twitchio.ChannelPollEnd.respond`
        - Added :meth:`twitchio.ChannelPredictionBegin.respond`
        - Added :meth:`twitchio.ChannelPredictionProgress.respond`
        - Added :meth:`twitchio.ChannelPredictionLock.respond`
        - Added :meth:`twitchio.ChannelPredictionEnd.respond`
        - Added :meth:`twitchio.SuspiciousUserUpdate.respond`
        - Added :meth:`twitchio.SuspiciousUserMessage.respond`
        - Added :meth:`twitchio.ChannelVIPAdd.respond`
        - Added :meth:`twitchio.ChannelVIPRemove.respond`
        - Added :meth:`twitchio.ChannelWarningAcknowledge.respond`
        - Added :meth:`twitchio.ChannelWarningSend.respond`
        - Added :meth:`twitchio.BaseCharityCampaign.respond`
        - Added :meth:`twitchio.CharityCampaignDonation.respond`
        - Added :meth:`twitchio.GoalBegin.respond`
        - Added :meth:`twitchio.GoalProgress.respond`
        - Added :meth:`twitchio.GoalEnd.respond`
        - Added :meth:`twitchio.HypeTrainBegin.respond`
        - Added :meth:`twitchio.HypeTrainProgress.respond`
        - Added :meth:`twitchio.HypeTrainEnd.respond`
        - Added :meth:`twitchio.ShieldModeBegin.respond`
        - Added :meth:`twitchio.ShieldModeEnd.respond`
        - Added :meth:`twitchio.ShoutoutCreate.respond`
        - Added :meth:`twitchio.ShoutoutReceive.respond`
        - Added :meth:`twitchio.StreamOnline.respond`
        - Added :meth:`twitchio.StreamOffline.respond`

    - Bug fixes
        - Remove the unnecessary ``token_for`` parameter from :meth:`twitchio.ChannelPointsReward.fetch_reward`. `#510 <https://github.com/PythonistaGuild/TwitchIO/pull/510>`_

- twitchio.web.AiohttpAdapter
    - Bug fixes
        - Fixed the redirect URL not allowing HOST/PORT when a custom domain was passed.
            - The redirect URL is now determined based on where the request came from.
        - Now correctly changes the protocol to ``https`` when SSL is used directly on the adapter.

- twitchio.web.StarletteAdapter
    - Additions
        - Added the ``timeout_graceful_shutdown`` keyword parameter which allows controlling how long ``Starlette/Uvicorn`` will wait to gracefully close.
        - Added the ``timeout_keep_alive`` keyword parameter which allows controlling how long ``Uvicorn`` will wait until closing Keep-Alive connections after not receiving any data.

    - Bug fixes
        - Fixed the redirect URL not allowing HOST/PORT when a custom domain was passed.
            - The redirect URL is now determined based on where the request came from.
        - Fixed Uvicorn hanging the process when attempting to close the :class:`asyncio.Loop` on **Windows**.
            - After a default of ``3 seconds`` Uvicorn will be forced closed if it cannot gracefully close in this time. This time can be changed with the ``timeout_graceful_shutdown`` parameter.
        - Now correctly changes the protocol to ``https`` when SSL is used directly on the adapter.

- ext.commands
    - Additions
        - Added :class:`~twitchio.ext.commands.Translator`
        - Added :func:`~twitchio.ext.commands.translator`
        - Added :attr:`twitchio.ext.commands.Command.translator`
        - Added :meth:`twitchio.ext.commands.Context.send_translated`
        - Added :meth:`twitchio.ext.commands.Context.reply_translated`
        - Added :attr:`twitchio.ext.commands.Context.translator`
        - Added :class:`~twitchio.ext.commands.Converter`
        - Added :class:`~twitchio.ext.commands.UserConverter`
        - Added :class:`~twitchio.ext.commands.ColourConverter`
        - Added :class:`~twitchio.ext.commands.ColorConverter` alias.
        - Added :attr:`twitchio.ext.commands.Command.signature` which is a POSIX-like signature for the command.
        - Added :attr:`twitchio.ext.commands.Command.parameters` which is a mapping of parameter name to :class:`inspect.Parameter` associated with the command callback.
        - Added :attr:`twitchio.ext.commands.Command.help` which is the docstring of the command callback.
        - Added ``__doc__`` to :class:`~twitchio.ext.commands.Command` which takes from the callback ``__doc__``.
        - Added :meth:`twitchio.ext.commands.Command.run_guards`
        - Added :meth:`twitchio.ext.commands.Context.fetch_command`
        - :class:`~twitchio.ext.commands.Context` is now ``Generic`` and accepts a generic argument bound to :class:`~twitchio.ext.commands.Bot` or :class:`~twitchio.ext.commands.AutoBot`.

    - Bug fixes
        - Prevent multiple :class:`~twitchio.ext.commands.Component`'s of the same name being added to a bot resulting in one overriding the other.


3.0.0
======

The changelog for this version is too large to display. Please see :ref:`Migrating Guide` for more information.

2.10.0
=======
- TwitchIO
    - Bug fixes
        - fix: :func:`~twitchio.PartialUser.fetch_markers` was passing list of one element from payload, now just passes element

- ext.commands
    - Changes
        - Added which alias failed to load in the error raised by :func:`~twitchio.ext.commands.Bot.add_command`

    - Bug fixes
        - fix string parser not properly parsing specific quoted strings

- ext.eventsub
    - Additions
        - Added :meth:`EventSubClient.subscribe_channel_unban_request_create <twitchio.ext.eventsub.EventSubClient.subscribe_channel_unban_request_create>` /
            :meth:`EventSubWSClient.subscribe_channel_unban_request_create <twitchio.ext.eventsub.EventSubWSClient.subscribe_channel_unban_request_create>`
        - Added :meth:`EventSubClient.subscribe_channel_unban_request_resolve <twitchio.ext.eventsub.EventSubClient.subscribe_channel_unban_request_resolve>` /
            :meth:`EventSubWSClient.subscribe_channel_unban_request_resolve <twitchio.ext.eventsub.EventSubWSClient.subscribe_channel_unban_request_resolve>`
        - Added :meth:`EventSubClient.subscribe_automod_terms_update <twitchio.ext.eventsub.EventSubClient.subscribe_automod_terms_update>` /
            :meth:`EventSubWSClient.subscribe_automod_terms_update <twitchio.ext.eventsub.EventSubWSClient.subscribe_automod_terms_update>`
        - Added :meth:`EventSubClient.subscribe_automod_settings_update <twitchio.ext.eventsub.EventSubClient.subscribe_automod_settings_update>` /
            :meth:`EventSubWSClient.subscribe_automod_settings_update <twitchio.ext.eventsub.EventSubWSClient.subscribe_automod_settings_update>`
        - Added :meth:`EventSubClient.subscribe_automod_message_update <twitchio.ext.eventsub.EventSubClient.subscribe_automod_message_update>` /
            :meth:`EventSubWSClient.subscribe_automod_message_update <twitchio.ext.eventsub.EventSubWSClient.subscribe_automod_message_update>`
        - Added :meth:`EventSubClient.subscribe_automod_message_hold <twitchio.ext.eventsub.EventSubClient.subscribe_automod_message_hold>` /
            :meth:`EventSubWSClient.subscribe_automod_message_hold <twitchio.ext.eventsub.EventSubWSClient.subscribe_automod_message_hold>`
        - Added :meth:`EventSubClient.subscribe_channel_moderate <twitchio.ext.eventsub.EventSubClient.subscribe_channel_moderate>` /
            :meth:`EventSubWSClient.subscribe_channel_moderate <twitchio.ext.eventsub.EventSubWSClient.subscribe_channel_moderate>`
        - Added :meth:`EventSubClient.subscribe_suspicious_user_update <twitchio.ext.eventsub.EventSubClient.subscribe_suspicious_user_update>` /
            :meth:`EventSubWSClient.subscribe_suspicious_user_update <twitchio.ext.eventsub.EventSubWSClient.subscribe_suspicious_user_update>`
        - Added :meth:`EventSubClient.subscribe_channel_vip_add <twitchio.ext.eventsub.EventSubClient.subscribe_channel_vip_add>` /
            :meth:`EventSubWSClient.subscribe_channel_vip_add <twitchio.ext.eventsub.EventSubWSClient.subscribe_channel_vip_add>`
        - Added :meth:`EventSubClient.subscribe_channel_vip_remove <twitchio.ext.eventsub.EventSubClient.subscribe_channel_vip_remove>` /
            :meth:`EventSubWSClient.subscribe_channel_vip_remove <twitchio.ext.eventsub.EventSubWSClient.subscribe_channel_vip_remove>`
        - Added all accompanying models for those endpoints.
- ext.sounds
    - Additions
        - Added TinyTag as a dependency to support retrieving audio metadata.
        - added :meth:`twitchio.ext.sounds.Sound.rate` setter.
        - added :meth:`twitchio.ext.sounds.Sound.channels` setter.


2.9.2
=======
- TwitchIO
    - Changes:
        - :func:`~twitchio.PartialUser.fetch_moderated_channels` returns "broadcaster_login" api field instead of "broadcaster_name"

    - Bug fixes
        - fix: :func:`~twitchio.PartialUser.fetch_moderated_channels` used ``user_`` prefix from payload, now uses ``broadcaster_`` instead

- ext.commands
    - Bug fixes
        - Fixed return type of :func:`~twitchio.ext.commands.Context.get_user` to PartialChatter / Chatter from PartialUser / User.


2.9.1
=======
- ext.eventsub
    - Bug fixes
        - fix: Special-cased a restart when a specific known bad frame is received.


2.9.0
=======
- TwitchIO
    - Additions
        - Added :class:`~twitchio.AdSchedule` and :class:`~twitchio.Emote`
        - Added the new ad-related methods for :class:`~twitchio.PartialUser`:
            - :func:`~twitchio.PartialUser.fetch_ad_schedule`
            - :func:`~twitchio.PartialUser.snooze_ad`
        - Added new method :func:`~twitchio.PartialUser.fetch_user_emotes` to :class:`~twitchio.PartialUser`
        - Added :func:`~twitchio.PartialUser.fetch_moderated_channels` to :class:`~twitchio.PartialUser`

    - Bug fixes
        - Fixed ``event_token_expired`` not applying to the current request.

- ext.eventsub
    - Bug fixes
        - Fixed a crash where a Future could be None, causing unintentional errors.
        - Special-cased a restart when a specific known bad frame is received.


2.8.2
======
- ext.commands
    - Bug fixes
        - Fixed an issue where built-in converters would raise an internal ``TypeError``.

2.8.1
======
- ext.commands
    - Bug fixes
        - Fixed an issue where ``CommandNotFound`` couldn't be processed from ``get_context``.

2.8.0
======
- TwitchIO
    - Additions
        - Added the new follower / followed endpoints for :class:`~twitchio.PartialUser`:
            - :func:`~twitchio.PartialUser.fetch_channel_followers`
            - :func:`~twitchio.PartialUser.fetch_channel_following`
            - :func:`~twitchio.PartialUser.fetch_channel_follower_count`
            - :func:`~twitchio.PartialUser.fetch_channel_following_count`
        - The deprecated methods have had warnings added in the docs.
        - New models for the new methods have been added:
            - :class:`~twitchio.ChannelFollowerEvent`
            - :class:`~twitchio.ChannelFollowingEvent`
        - New optional ``is_featured`` query parameter for :func:`~twitchio.PartialUser.fetch_clips`
        - New optional ``is_featured`` query parameter for :func:`~twitchio.PartialUser.fetch_clips`
        - New attribute :attr:`~twitchio.Clip.is_featured` for :class:`~twitchio.Clip`

    - Bug fixes
        - Fix IndexError when getting prefix when empty message is sent in a reply.

- ext.eventsub
    - Bug fixes
        - Fix websocket reconnection event.
        - Fix another websocket reconnect issue where it tried to decode nonexistent headers.

- ext.commands
    - Additions
        - Added support for the following typing constructs in command signatures:
            - ``Union[A, B]`` / ``A | B``
            - ``Optional[T]`` / ``T | None``
            - ``Annotated[T, converter]`` (accessible through the ``typing_extensions`` module on older python versions)

- Docs
    - Added walkthrough for ext.commands

2.7.0
======
- TwitchIO
    - Additions
        - Added :func:`~twitchio.PartialUser.fetch_charity_campaigns` with :class:`~twitchio.CharityCampaign` and :class:`~twitchio.CharityValues`.
        - Added :func:`~twitchio.Client.fetch_global_chat_badges`
        - Added User method :func:`~twitchio.PartialUser.fetch_chat_badges`
        - Added repr for :class:`~twitchio.SearchUser`
        - Added two new events
            - Added :func:`~twitchio.Client.event_notice`
            - Added :func:`~twitchio.Client.event_raw_notice`

        - Added :class:`~twitchio.message.HypeChatData` for hype chat events
        - Added :attr:`~twitchio.message.Message.hype_chat_data` for hype chat events
        - Added :func:`~twitchio.Client.fetch_content_classification_labels` along with :class:`~twitchio.ContentClassificationLabel`
        - Added :attr:`~twitchio.ChannelInfo.content_classification_labels` and :attr:`~twitchio.ChannelInfo.is_branded_content` to :class:`~twitchio.ChannelInfo`
        - Added new parameters to :func:`~twitchio.PartialUser.modify_stream` for ``is_branded_content`` and ``content_classification_labels``


    - Bug fixes
        - Fix :func:`~twitchio.Client.search_categories` due to :attr:`~twitchio.Game.igdb_id` being added to :class:`~twitchio.Game`
        - Made Chatter :attr:`~twitchio.Chatter.id` property public
        - :func:`~twitchio.Client.event_token_expired` will now be called correctly when response is ``401 Invalid OAuth token``
        - Fix reconnect loop when Twitch sends a RECONNECT via IRC websocket
        - Fix :func:`~twitchio.CustomReward.edit` so it now can enable the reward


    - Other Changes
        - Updated the HTTPException to provide useful information when an error is raised.

- ext.eventsub
    - Added websocket support via :class:`~twitchio.ext.eventsub.EventSubWSClient`.
    - Added support for charity donation events.

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
    - Added sounds extension.

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
