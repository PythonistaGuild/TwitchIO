.. currentmodule:: twitchio

.. _Event Ref:

Events Reference
################

.. warning::

   This document is a work in progress.


All events are prefixed with **event_**

.. list-table::
   :header-rows: 1

   * - Type
     - Subscription
     - Event
     - Payload
   * - Automod Message Hold
     - :meth:`~eventsub.AutomodMessageHoldSubscription`
     - :func:`~twitchio.event_automod_message_hold()`
     - :class:`~models.eventsub_.AutomodMessageHold`
   * - Automod Message Update
     - :meth:`~eventsub.AutomodMessageUpdateSubscription`
     - :func:`~twitchio.event_automod_message_update()`
     - :class:`~models.eventsub_.AutomodMessageUpdate`
   * - Automod Settings Update
     - :meth:`~eventsub.AutomodSettingsUpdateSubscription`
     - :func:`~twitchio.event_automod_settings_update()`
     - :class:`~models.eventsub_.AutomodSettingsUpdate`
   * - Automod Terms Update
     - :meth:`~eventsub.AutomodTermsUpdateSubscription`
     - :func:`~twitchio.event_automod_terms_update()`
     - :class:`~models.eventsub_.AutomodTermsUpdate`
   * - Channel Update
     - :meth:`~eventsub.ChannelUpdateSubscription`
     - :func:`~twitchio.event_channel_update()`
     - :class:`~models.eventsub_.ChannelUpdate`
   * - Channel Follow
     - :meth:`~eventsub.ChannelFollowSubscription`
     - :func:`~twitchio.event_follow()`
     - :class:`~models.eventsub_.ChannelFollow`
   * - Channel Ad Break Begin
     - :meth:`~eventsub.AdBreakBeginSubscription`
     - :func:`~twitchio.event_ad_break()`
     - :class:`~models.eventsub_.ChannelAdBreakBegin`
   * - Channel Chat Clear
     - :meth:`~eventsub.ChatClearSubscription`
     - :func:`~twitchio.event_chat_clear()`
     - :class:`~models.eventsub_.ChannelChatClear`
   * - Channel Chat Clear User Messages
     - :meth:`~eventsub.ChatClearUserMessagesSubscription`
     - :func:`~twitchio.event_chat_clear_user()`
     - :class:`~models.eventsub_.ChannelChatClearUserMessages`
   * - Channel Chat Message
     - :meth:`~eventsub.ChatMessageSubscription`
     - :func:`~twitchio.event_message()`
     - :class:`~models.eventsub_.ChatMessage`
   * - Channel Chat Message Delete
     - :meth:`~eventsub.ChatMessageDeleteSubscription`
     - :func:`~twitchio.event_message_delete()`
     - :class:`~models.eventsub_.ChatMessageDelete`
   * - Channel Chat Notification 
     - :meth:`~eventsub.ChatNotificationSubscription`
     - chat_notification
     - :class:`~models.eventsub_.ChatNotification`
   * - Channel Chat Settings Update
     - :meth:`~eventsub.ChatSettingsUpdateSubscription`
     - chat_settings_update
     - :class:`~models.eventsub_.ChatSettingsUpdate`
   * - Channel Chat User Message Hold
     - :meth:`~eventsub.ChatUserMessageHoldSubscription`
     - chat_user_message_hold
     - :class:`~models.eventsub_.ChatUserMessageHold`
   * - Channel Chat User Message Update
     - :meth:`~eventsub.ChatUserMessageUpdateSubscription`
     - chat_user_message_update
     - :class:`~models.eventsub_.ChatUserMessageUpdate`
   * - Channel Shared Chat Session Begin
     - :meth:`~eventsub.SharedChatSessionBeginSubscription`
     - shared_chat_begin
     - :class:`~models.eventsub_.SharedChatSessionBegin`
   * - Channel Shared Chat Session Update
     - :meth:`~eventsub.SharedChatSessionUpdateSubscription`
     - shared_chat_update
     - :class:`~models.eventsub_.SharedChatSessionUpdate`
   * - Channel Shared Chat Session End
     - :meth:`~eventsub.SharedChatSessionEndSubscription`
     - shared_chat_end
     - :class:`~models.eventsub_.SharedChatSessionEnd`
   * - Channel Subscribe
     - :meth:`~eventsub.ChannelSubscribeSubscription`
     - subscription
     - :class:`~models.eventsub_.ChannelSubscribe`
   * - Channel Subscription End
     - :meth:`~eventsub.ChannelSubscriptionEndSubscription`
     - subscription_end
     - :class:`~models.eventsub_.ChannelSubscriptionEnd`
   * - Channel Subscription Gift
     - :meth:`~eventsub.ChannelSubscriptionGiftSubscription`
     - subscription_gift
     - :class:`~models.eventsub_.ChannelSubscriptionGift`
   * - Channel Subscription Message
     - :meth:`~eventsub.ChannelSubscribeMessageSubscription`
     - subscription_message
     - :class:`~models.eventsub_.ChannelSubscriptionMessage`
   * - Channel Cheer
     - :meth:`~eventsub.ChannelCheerSubscription`
     - cheer
     - :class:`~models.eventsub_.ChannelCheer`
   * - Channel Raid
     - :meth:`~eventsub.ChannelRaidSubscription`
     - raid
     - :class:`~models.eventsub_.ChannelRaid`
   * - Channel Ban
     - :meth:`~eventsub.ChannelBanSubscription`
     - ban
     - :class:`~models.eventsub_.ChannelBan`
   * - Channel Unban
     - :meth:`~eventsub.ChannelUnbanSubscription`
     - unban
     - :class:`~models.eventsub_.ChannelUnban`
   * - Channel Unban Request Create
     - :meth:`~eventsub.ChannelUnbanRequestSubscription`
     - unban_request
     - :class:`~models.eventsub_.ChannelUnbanRequest`
   * - Channel Unban Request Resolve
     - :meth:`~eventsub.ChannelUnbanRequestResolveSubscription`
     - unban_request_resolve
     - :class:`~models.eventsub_.ChannelUnbanRequestResolve`
   * - Channel Moderate
     - :meth:`~eventsub.ChannelModerateSubscription`
     - mod_action
     - :class:`~models.eventsub_.ChannelModerate`
   * - Channel Moderate V2
     - :meth:`~eventsub.ChannelModerateV2Subscription`
     - mod_action
     - :class:`~models.eventsub_.ChannelModerate`
   * - Channel Moderator Add
     - :meth:`~eventsub.ChannelModeratorAddSubscription`
     - moderator_add
     - :class:`~models.eventsub_.ChannelModeratorAdd`
   * - Channel Moderator Remove
     - :meth:`~eventsub.ChannelModeratorRemoveSubscription`
     - moderator_remove
     - :class:`~models.eventsub_.ChannelModeratorRemove`
   * - Channel Points Automatic Reward Redemption
     - :meth:`~eventsub.ChannelPointsAutoRedeemSubscription`
     - automatic_redemption_add
     - :class:`~models.eventsub_.ChannelPointsAutoRedeemAdd`
   * - Channel Points Custom Reward Add
     - :meth:`~eventsub.ChannelPointsRewardAddSubscription`
     - custom_reward_add
     - :class:`~models.eventsub_.ChannelPointsRewardAdd`
   * - Channel Points Custom Reward Update
     - :meth:`~eventsub.ChannelPointsRewardUpdateSubscription`
     - custom_reward_update
     - :class:`~models.eventsub_.ChannelPointsRewardUpdate`
   * - Channel Points Custom Reward Remove
     - :meth:`~eventsub.ChannelPointsRewardRemoveSubscription`
     - custom_reward_remove
     - :class:`~models.eventsub_.ChannelPointsRewardRemove`
   * - Channel Points Custom Reward Redemption Add
     - :meth:`~eventsub.ChannelPointsRedeemAddSubscription`
     - custom_redemption_add
     - :class:`~models.eventsub_.ChannelPointsRedemptionAdd`
   * - Channel Points Custom Reward Redemption Update
     - :meth:`~eventsub.ChannelPointsRedeemUpdateSubscription`
     - custom_redemption_update
     - :class:`~models.eventsub_.ChannelPointsRedemptionUpdate`
   * - Channel Poll Begin
     - :meth:`~eventsub.ChannelPollBeginSubscription`
     - poll_begin
     - :class:`~models.eventsub_.ChannelPollBegin`
   * - Channel Poll Progress
     - :meth:`~eventsub.ChannelPollProgressSubscription`
     - poll_progress
     - :class:`~models.eventsub_.ChannelPollProgress`
   * - Channel Poll End
     - :meth:`~eventsub.ChannelPollEndSubscription`
     - poll_end
     - :class:`~models.eventsub_.ChannelPollEnd`
   * - Channel Prediction Begin
     - :meth:`~eventsub.ChannelPredictionBeginSubscription`
     - prediction_begin
     - :class:`~models.eventsub_.ChannelPredictionBegin`
   * - Channel Prediction Progress
     - :meth:`~eventsub.ChannelPredictionProgressSubscription`
     - prediction_progress
     - :class:`~models.eventsub_.ChannelPredictionProgress`
   * - Channel Prediction Lock
     - :meth:`~eventsub.ChannelPredictionLockSubscription`
     - prediction_lock
     - :class:`~models.eventsub_.ChannelPredictionLock`
   * - Channel Prediction End
     - :meth:`~eventsub.ChannelPredictionEndSubscription`
     - prediction_end
     - :class:`~models.eventsub_.ChannelPredictionEnd`
   * - Channel Suspicious User Message
     - :meth:`~eventsub.SuspiciousUserMessageSubscription`
     - suspicious_user_message
     - :class:`~models.eventsub_.SuspiciousUserMessage`
   * - Channel Suspicious User Update
     - :meth:`~eventsub.SuspiciousUserUpdateSubscription`
     - suspicious_user_update
     - :class:`~models.eventsub_.SuspiciousUserUpdate`
   * - Channel VIP Add
     - :meth:`~eventsub.ChannelVIPAddSubscription`
     - vip_add
     - :class:`~models.eventsub_.ChannelVIPAdd`
   * - Channel VIP Remove
     - :meth:`~eventsub.ChannelVIPRemoveSubscription`
     - vip_remove
     - :class:`~models.eventsub_.ChannelVIPRemove`
   * - Channel Warning Acknowledgement
     - :meth:`~eventsub.ChannelWarningAcknowledgementSubscription`
     - warning_acknowledge
     - :class:`~models.eventsub_.ChannelWarningAcknowledge`
   * - Channel Warning Send
     - :meth:`~eventsub.ChannelWarningSendSubscription`
     - warning_send
     - :class:`~models.eventsub_.ChannelWarningSend`
   * - Charity Donation
     - :meth:`~eventsub.CharityDonationSubscription`
     - charity_campaign_donate
     - :class:`~models.eventsub_.CharityCampaignDonation`
   * - Charity Campaign Start
     - :meth:`~eventsub.CharityCampaignStartSubscription`
     - charity_campaign_start
     - :class:`~models.eventsub_.CharityCampaignStart`
   * - Charity Campaign Progress
     - :meth:`~eventsub.CharityCampaignProgressSubscription`
     - charity_campaign_progress
     - :class:`~models.eventsub_.CharityCampaignProgress`
   * - Charity Campaign Stop
     - :meth:`~eventsub.CharityCampaignStopSubscription`
     - charity_campaign_stop
     - :class:`~models.eventsub_.CharityCampaignStop`
   * - Goal Begin
     - :meth:`~eventsub.GoalBeginSubscription`
     - goal_begin
     - :class:`~models.eventsub_.GoalBegin`
   * - Goal Progress
     - :meth:`~eventsub.GoalProgressSubscription`
     - goal_progress
     - :class:`~models.eventsub_.GoalProgress`
   * - Goal End
     - :meth:`~eventsub.GoalEndSubscription`
     - goal_end
     - :class:`~models.eventsub_.GoalEnd`
   * - Hype Train Begin
     - :meth:`~eventsub.HypeTrainBeginSubscription`
     - hype_train
     - :class:`~models.eventsub_.HypeTrainBegin`
   * - Hype Train Progress
     - :meth:`~eventsub.HypeTrainProgressSubscription`
     - hype_train_progress
     - :class:`~models.eventsub_.HypeTrainProgress`
   * - Hype Train End
     - :meth:`~eventsub.HypeTrainEndSubscription`
     - hype_train_end
     - :class:`~models.eventsub_.HypeTrainEnd`
   * - Shield Mode Begin
     - :meth:`~eventsub.ShieldModeBeginSubscription`
     - shield_mode_begin
     - :class:`~models.eventsub_.ShieldModeBegin`
   * - Shield Mode End
     - :meth:`~eventsub.ShieldModeEndSubscription`
     - shield_mode_end
     - :class:`~models.eventsub_.ShieldModeEnd`
   * - Shoutout Create
     - :meth:`~eventsub.ShoutoutCreateSubscription`
     - :func:`~twitchio.event_shoutout_create()`
     - :class:`~models.eventsub_.ShoutoutCreate`
   * - Shoutout Received
     - :meth:`~eventsub.ShoutoutReceiveSubscription`
     - :func:`~twitchio.event_shoutout_receive()`
     - :class:`~models.eventsub_.ShoutoutReceive`
   * - Stream Online
     - :meth:`~eventsub.StreamOnlineSubscription`
     - :func:`~twitchio.event_stream_online()`
     - :class:`~models.eventsub_.StreamOnline`
   * - Stream Offline
     - :meth:`~eventsub.StreamOfflineSubscription`
     - :func:`~twitchio.event_stream_offline()`
     - :class:`~models.eventsub_.StreamOffline`
   * - User Authorization Grant
     - :meth:`~eventsub.UserAuthorizationGrantSubscription`
     - :func:`~twitchio.event_user_authorization_grant()`
     - :class:`~models.eventsub_.UserAuthorizationGrant`
   * - User Authorization Revoke
     - :meth:`~eventsub.UserAuthorizationRevokeSubscription`
     - :func:`~twitchio.event_user_authorization_revoke()`
     - :class:`~models.eventsub_.UserAuthorizationRevoke`
   * - User Update
     - :meth:`~eventsub.UserUpdateSubscription`
     - :func:`~twitchio.event_user_update()`
     - :class:`~models.eventsub_.UserUpdate`
   * - Whisper Received
     - :meth:`~eventsub.WhisperReceivedSubscription`
     - :func:`~twitchio.event_message_whisper()`
     - :class:`~models.eventsub_.Whisper`


Client Events
~~~~~~~~~~~~~

.. py:function:: event_ready() -> None
  :async:
   
  Event dispatched when the :class:`~.Client` is ready and has completed login.

.. py:function:: event_error(payload: twitchio.EventErrorPayload) -> None
  :async:
   
  Event dispatched when an exception is raised inside of a dispatched event.

  :param twitchio.EventErrorPayload payload: The payload containing information about the event and exception raised.
  
.. py:function:: event_oauth_authorized(payload: twitchio.authentication.UserTokenPayload) -> None
  :async:

  Event dispatched when a user authorizes your Client-ID via Twitch OAuth on a built-in web adapter.

  The default behaviour of this event is to add the authorized token to the client.
  See: :class:`~twitchio.Client.add_token` for more details.

  :param UserTokenPayload payload: The payload containing token information.


Commands Events
~~~~~~~~~~~~~~~

.. py:function:: event_command_invoked(ctx: twitchio.ext.commands.Context) -> None
  :async:
   
  Event dispatched when a :class:`~twitchio.ext.commands.Command` is invoked.

  :param twitchio.ext.commands.Context ctx: The context object that invoked the command.

.. py:function:: event_command_completed(ctx: twitchio.ext.commands.Context) -> None
  :async:
   
  Event dispatched when a :class:`~twitchio.ext.commands.Command` has completed invocation.

  :param twitchio.ext.commands.Context ctx: The context object that invoked the command.

.. py:function:: event_command_error(payload: twitchio.ext.commands.CommandErrorPayload) -> None
  :async:
   
  Event dispatched when a :class:`~twitchio.ext.commands.Command` encounters an error during invocation.

  :param twitchio.ext.commands.CommandErrorPayload payload: The error payload containing context and the exception raised.


EventSub Events
~~~~~~~~~~~~~~~

Automod
-------

.. py:function:: event_automod_message_hold(payload: twitchio.AutomodMessageHold) -> None
    :async:

    Event dispatched when a message is held by Automod and needs review.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Automod Message Hold <automodmessagehold>` and 
    :es-docs:`Automod Message Hold V2 <automodmessagehold-v2>`.
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.AutomodMessageHoldSubscription` or 
    :class:`~twitchio.eventsub.AutomodMessageHoldV2Subscription` for each required broadcaster to receive this event.

    :param twitchio.AutomodMessageHold payload: The EventSub payload received for this event.

.. py:function:: event_automod_message_update(payload: twitchio.AutomodMessageUpdate) -> None
    :async:

    Event dispatched when a message held by Automod status changes.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Automod Message Update <automodmessageupdate>` and 
    :es-docs:`Automod Message Update V2 <automodmessageupdate-v2>`.
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.AutomodMessageUpdateSubscription` or 
    :class:`~twitchio.eventsub.AutomodMessageUpdateV2Subscription` for each required broadcaster to receive this event.

    :param twitchio.AutomodMessageUpdate payload: The EventSub payload received for this event.

.. py:function:: event_automod_settings_update(payload: twitchio.AutomodSettingsUpdate) -> None
    :async:

    Event dispatched when a broadcaster's automod settings are updated.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Automod Settings Update <automodsettingsupdate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.AutomodSettingsUpdateSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.AutomodSettingsUpdate payload: The EventSub payload received for this event.

.. py:function:: event_automod_terms_update(payload: twitchio.AutomodTermsUpdate) -> None
    :async:

    Event dispatched when a broadcaster's automod terms are updated. Changes to private terms are not sent.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Automod Terms Update <automodtermsupdate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.AutomodTermsUpdateSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.AutomodTermsUpdate payload: The EventSub payload received for this event.


Channel / Broadcaster
---------------------

.. py:function:: event_channel_update(payload: twitchio.ChannelUpdate) -> None
    :async:

    Event dispatched when a broadcaster updates their channel properties e.g. category, title, content classification labels, broadcast, or language.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Update <channelupdate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelUpdateSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelUpdate payload: The EventSub payload received for this event.

.. py:function:: event_follow(payload: twitchio.ChannelFollow) -> None
    :async:

    Event dispatched when someone follows a channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Follow <channelfollow>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelFollowSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelFollow payload: The EventSub payload received for this event.

.. py:function:: event_ad_break(payload: twitchio.ChannelAdBreakBegin) -> None
    :async:

    Event dispatched when a midroll commercial break has started running.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Ad Break Begin <channelad_breakbegin>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.AdBreakBeginSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelAdBreakBegin payload: The EventSub payload received for this event.

.. py:function:: event_chat_clear(payload: twitchio.ChannelChatClear) -> None
    :async:

    Event dispatched when a moderator or bot has cleared all messages from the chat room.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat Clear <channelchatclear>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatClearSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelChatClear payload: The EventSub payload received for this event.

.. py:function:: event_chat_clear_user(payload: twitchio.ChannelChatClearUserMessages) -> None
    :async:

    Event dispatched when a moderator or bot has cleared all messages from a specific user.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat Clear User Messages <channelchatclear_user_messages>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatClearUserMessagesSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelChatClearUserMessages payload: The EventSub payload received for this event.

.. py:function:: event_message(payload: twitchio.ChatMessage) -> None
    :async:

    Event dispatched when a user sends a message to a chat room.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat Message <channelchatmessage>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatMessageSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChatMessage payload: The EventSub payload received for this event.

.. py:function:: event_message_delete(payload: twitchio.ChatMessageDelete) -> None
    :async:

    Event dispatched when a moderator has removed a specific message.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat Message Delete <channelchatmessage_delete>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatMessageDeleteSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChatMessageDelete payload: The EventSub payload received for this event.

Streams
-------

.. py:function:: event_stream_online(payload: twitchio.StreamOnline) -> None
  :async:

  Event dispatched when a stream comes online.

  Corresponds to the Twitch EventSub subscription :es-docs:`Stream Online <streamonline>`.

  You must subscribe to EventSub with :class:`~twitchio.eventsub.StreamOnlineSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.StreamOnline payload: The EventSub payload for this event.

.. py:function:: event_stream_offline(payload: twitchio.StreamOffline) -> None
  :async:

  Event dispatched when a stream goes offline.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Stream Offline <streamoffline>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.StreamOfflineSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.StreamOffline payload: The EventSub payload for this event.


Shoutouts
---------

.. py:function:: event_shoutout_create(payload: twitchio.ShoutoutCreate) -> None
  :async:

  Event dispatched when when the specified broadcaster sends a shoutout.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Shoutout Create <shoutoutcreate>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ShoutoutCreateSubscription` for each required broadcaster 
  to receive this event to receive this event.

  :param twitchio.ShoutoutCreate payload: The EventSub payload for this event.

.. py:function:: event_shoutout_receive(payload: twitchio.ShoutoutReceive) -> None
  :async:

  Event dispatched when when the specified broadcaster receives a shoutout.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Shoutout Create <shoutoutreceive>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ShoutoutReceiveSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.ShoutoutReceive payload: The EventSub payload for this event.


OAuth
-----

.. py:function:: event_user_authorization_grant(payload: twitchio.UserAuthorizationGrant) -> None
  :async:

  Event dispatched when a user's authorization has been granted for your client id.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`User Authorization Grant <userauthorizationgrant>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.UserAuthorizationRevokeSubscription` to receive this event.

  :param twitchio.UserAuthorizationGrant payload: The EventSub payload for this event.

.. py:function:: event_user_authorization_revoke(payload: twitchio.UserAuthorizationRevoke) -> None
  :async:

  Event dispatched when a user's authorization has been revoked for your client id.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`User Authorization Revoke <userauthorizationrevoke>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.UserAuthorizationRevokeSubscription` to receive this event.

  :param twitchio.UserAuthorizationRevoke payload: The EventSub payload for this event.


User
-----

.. py:function:: event_user_update(payload: twitchio.UserUpdate) -> None
  :async:

  Event dispatched when a user has updated their account.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`User Update <userupdate>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.UserUpdateSubscription` for each required user
  to receive this event.

  :param twitchio.UserUpdate payload: The EventSub payload for this event.

.. py:function:: event_message_whisper(payload: twitchio.Whisper) -> None
  :async:

  Event dispatched when a user receives this a whisper.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`User Whisper <userwhispermessage>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.WhisperReceivedSubscription` for each required user
  to receive this event.

  :param twitchio.Whisper payload: The EventSub payload for this event.


Payloads
~~~~~~~~

.. attributetable:: twitchio.EventErrorPayload

.. autoclass:: twitchio.EventErrorPayload()
  :members: