.. currentmodule:: twitchio

.. _Event Ref:

Events Reference
################

.. warning::

   This document is a work in progress.

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
     - :func:`~twitchio.event_chat_notification()`
     - :class:`~models.eventsub_.ChatNotification`
   * - Channel Chat Settings Update
     - :meth:`~eventsub.ChatSettingsUpdateSubscription`
     - :func:`~twitchio.event_chat_settings_update()`
     - :class:`~models.eventsub_.ChatSettingsUpdate`
   * - Channel Chat User Message Hold
     - :meth:`~eventsub.ChatUserMessageHoldSubscription`
     - :func:`~twitchio.event_chat_user_message_hold()`
     - :class:`~models.eventsub_.ChatUserMessageHold`
   * - Channel Chat User Message Update
     - :meth:`~eventsub.ChatUserMessageUpdateSubscription`
     - :func:`~twitchio.event_chat_user_message_update()`
     - :class:`~models.eventsub_.ChatUserMessageUpdate`
   * - Channel Shared Chat Session Begin
     - :meth:`~eventsub.SharedChatSessionBeginSubscription`
     - :func:`~twitchio.event_shared_chat_begin()`
     - :class:`~models.eventsub_.SharedChatSessionBegin`
   * - Channel Shared Chat Session Update
     - :meth:`~eventsub.SharedChatSessionUpdateSubscription`
     - :func:`~twitchio.event_shared_chat_update()`
     - :class:`~models.eventsub_.SharedChatSessionUpdate`
   * - Channel Shared Chat Session End
     - :meth:`~eventsub.SharedChatSessionEndSubscription`
     - :func:`~twitchio.event_shared_chat_end()`
     - :class:`~models.eventsub_.SharedChatSessionEnd`
   * - Channel Subscribe
     - :meth:`~eventsub.ChannelSubscribeSubscription`
     - :func:`~twitchio.event_subscription()`
     - :class:`~models.eventsub_.ChannelSubscribe`
   * - Channel Subscription End
     - :meth:`~eventsub.ChannelSubscriptionEndSubscription`
     - :func:`~twitchio.event_subscription_end()`
     - :class:`~models.eventsub_.ChannelSubscriptionEnd`
   * - Channel Subscription Gift
     - :meth:`~eventsub.ChannelSubscriptionGiftSubscription`
     - :func:`~twitchio.event_subscription_gift()`
     - :class:`~models.eventsub_.ChannelSubscriptionGift`
   * - Channel Subscription Message
     - :meth:`~eventsub.ChannelSubscribeMessageSubscription`
     - :func:`~twitchio.event_subscription_message()`
     - :class:`~models.eventsub_.ChannelSubscriptionMessage`
   * - Channel Cheer
     - :meth:`~eventsub.ChannelCheerSubscription`
     - :func:`~twitchio.event_cheer()`
     - :class:`~models.eventsub_.ChannelCheer`
   * - Channel Raid
     - :meth:`~eventsub.ChannelRaidSubscription`
     - :func:`~twitchio.event_raid()`
     - :class:`~models.eventsub_.ChannelRaid`
   * - Channel Ban
     - :meth:`~eventsub.ChannelBanSubscription`
     - :func:`~twitchio.event_ban()`
     - :class:`~models.eventsub_.ChannelBan`
   * - Channel Unban
     - :meth:`~eventsub.ChannelUnbanSubscription`
     - :func:`~twitchio.event_unban()`
     - :class:`~models.eventsub_.ChannelUnban`
   * - Channel Unban Request Create
     - :meth:`~eventsub.ChannelUnbanRequestSubscription`
     - :func:`~twitchio.event_unban_request()`
     - :class:`~models.eventsub_.ChannelUnbanRequest`
   * - Channel Unban Request Resolve
     - :meth:`~eventsub.ChannelUnbanRequestResolveSubscription`
     - :func:`~twitchio.event_unban_request_resolve()`
     - :class:`~models.eventsub_.ChannelUnbanRequestResolve`
   * - Channel Moderate
     - :meth:`~eventsub.ChannelModerateSubscription`
     - :func:`~twitchio.event_mod_action()`
     - :class:`~models.eventsub_.ChannelModerate`
   * - Channel Moderate V2
     - :meth:`~eventsub.ChannelModerateV2Subscription`
     - :func:`~twitchio.event_mod_action()`
     - :class:`~models.eventsub_.ChannelModerate`
   * - Channel Moderator Add
     - :meth:`~eventsub.ChannelModeratorAddSubscription`
     - :func:`~twitchio.event_moderator_add()`
     - :class:`~models.eventsub_.ChannelModeratorAdd`
   * - Channel Moderator Remove
     - :meth:`~eventsub.ChannelModeratorRemoveSubscription`
     - :func:`~twitchio.event_moderator_remove()`
     - :class:`~models.eventsub_.ChannelModeratorRemove`
   * - Channel Points Automatic Reward Redemption
     - :meth:`~eventsub.ChannelPointsAutoRedeemSubscription`
     - :func:`~twitchio.event_automatic_redemption_add()`
     - :class:`~models.eventsub_.ChannelPointsAutoRedeemAdd`
   * - Channel Points Custom Reward Add
     - :meth:`~eventsub.ChannelPointsRewardAddSubscription`
     - :func:`~twitchio.event_custom_reward_add()`
     - :class:`~models.eventsub_.ChannelPointsRewardAdd`
   * - Channel Points Custom Reward Update
     - :meth:`~eventsub.ChannelPointsRewardUpdateSubscription`
     - :func:`~twitchio.event_custom_reward_update()`
     - :class:`~models.eventsub_.ChannelPointsRewardUpdate`
   * - Channel Points Custom Reward Remove
     - :meth:`~eventsub.ChannelPointsRewardRemoveSubscription`
     - :func:`~twitchio.event_custom_reward_remove()`
     - :class:`~models.eventsub_.ChannelPointsRewardRemove`
   * - Channel Points Custom Reward Redemption Add
     - :meth:`~eventsub.ChannelPointsRedeemAddSubscription`
     - :func:`~twitchio.event_custom_redemption_add()`
     - :class:`~models.eventsub_.ChannelPointsRedemptionAdd`
   * - Channel Points Custom Reward Redemption Update
     - :meth:`~eventsub.ChannelPointsRedeemUpdateSubscription`
     - :func:`~twitchio.event_custom_redemption_update()`
     - :class:`~models.eventsub_.ChannelPointsRedemptionUpdate`
   * - Channel Poll Begin
     - :meth:`~eventsub.ChannelPollBeginSubscription`
     - :func:`~twitchio.event_poll_begin()`
     - :class:`~models.eventsub_.ChannelPollBegin`
   * - Channel Poll Progress
     - :meth:`~eventsub.ChannelPollProgressSubscription`
     - :func:`~twitchio.event_poll_progress()`
     - :class:`~models.eventsub_.ChannelPollProgress`
   * - Channel Poll End
     - :meth:`~eventsub.ChannelPollEndSubscription`
     - :func:`~twitchio.event_poll_end()`
     - :class:`~models.eventsub_.ChannelPollEnd`
   * - Channel Prediction Begin
     - :meth:`~eventsub.ChannelPredictionBeginSubscription`
     - :func:`~twitchio.event_prediction_begin()`
     - :class:`~models.eventsub_.ChannelPredictionBegin`
   * - Channel Prediction Progress
     - :meth:`~eventsub.ChannelPredictionProgressSubscription`
     - :func:`~twitchio.event_prediction_progress()`
     - :class:`~models.eventsub_.ChannelPredictionProgress`
   * - Channel Prediction Lock
     - :meth:`~eventsub.ChannelPredictionLockSubscription`
     - :func:`~twitchio.event_prediction_lock()`
     - :class:`~models.eventsub_.ChannelPredictionLock`
   * - Channel Prediction End
     - :meth:`~eventsub.ChannelPredictionEndSubscription`
     - :func:`~twitchio.event_prediction_end()`
     - :class:`~models.eventsub_.ChannelPredictionEnd`
   * - Channel Suspicious User Message
     - :meth:`~eventsub.SuspiciousUserMessageSubscription`
     - :func:`~twitchio.event_suspicious_user_message()`
     - :class:`~models.eventsub_.SuspiciousUserMessage`
   * - Channel Suspicious User Update
     - :meth:`~eventsub.SuspiciousUserUpdateSubscription`
     - :func:`~twitchio.event_suspicious_user_update()`
     - :class:`~models.eventsub_.SuspiciousUserUpdate`
   * - Channel VIP Add
     - :meth:`~eventsub.ChannelVIPAddSubscription`
     - :func:`~twitchio.event_vip_add()`
     - :class:`~models.eventsub_.ChannelVIPAdd`
   * - Channel VIP Remove
     - :meth:`~eventsub.ChannelVIPRemoveSubscription`
     - :func:`~twitchio.event_vip_remove()`
     - :class:`~models.eventsub_.ChannelVIPRemove`
   * - Channel Warning Acknowledgement
     - :meth:`~eventsub.ChannelWarningAcknowledgementSubscription`
     - :func:`~twitchio.event_warning_acknowledge()`
     - :class:`~models.eventsub_.ChannelWarningAcknowledge`
   * - Channel Warning Send
     - :meth:`~eventsub.ChannelWarningSendSubscription`
     - :func:`~twitchio.event_warning_send()`
     - :class:`~models.eventsub_.ChannelWarningSend`
   * - Charity Donation
     - :meth:`~eventsub.CharityDonationSubscription`
     - :func:`~twitchio.event_charity_campaign_donate()`
     - :class:`~models.eventsub_.CharityCampaignDonation`
   * - Charity Campaign Start
     - :meth:`~eventsub.CharityCampaignStartSubscription`
     - :func:`~twitchio.event_charity_campaign_start()`
     - :class:`~models.eventsub_.CharityCampaignStart`
   * - Charity Campaign Progress
     - :meth:`~eventsub.CharityCampaignProgressSubscription`
     - :func:`~twitchio.event_charity_campaign_progress()`
     - :class:`~models.eventsub_.CharityCampaignProgress`
   * - Charity Campaign Stop
     - :meth:`~eventsub.CharityCampaignStopSubscription`
     - :func:`~twitchio.event_charity_campaign_stop()`
     - :class:`~models.eventsub_.CharityCampaignStop`
   * - Goal Begin
     - :meth:`~eventsub.GoalBeginSubscription`
     - :func:`~twitchio.event_goal_begin()`
     - :class:`~models.eventsub_.GoalBegin`
   * - Goal Progress
     - :meth:`~eventsub.GoalProgressSubscription`
     - :func:`~twitchio.event_goal_progress()`
     - :class:`~models.eventsub_.GoalProgress`
   * - Goal End
     - :meth:`~eventsub.GoalEndSubscription`
     - :func:`~twitchio.event_goal_end()`
     - :class:`~models.eventsub_.GoalEnd`
   * - Hype Train Begin
     - :meth:`~eventsub.HypeTrainBeginSubscription`
     - :func:`~twitchio.event_hype_train()`
     - :class:`~models.eventsub_.HypeTrainBegin`
   * - Hype Train Progress
     - :meth:`~eventsub.HypeTrainProgressSubscription`
     - :func:`~twitchio.event_hype_train_progress()`
     - :class:`~models.eventsub_.HypeTrainProgress`
   * - Hype Train End
     - :meth:`~eventsub.HypeTrainEndSubscription`
     - :func:`~twitchio.event_hype_train_end()`
     - :class:`~models.eventsub_.HypeTrainEnd`
   * - Shield Mode Begin
     - :meth:`~eventsub.ShieldModeBeginSubscription`
     - :func:`~twitchio.event_shield_mode_begin()`
     - :class:`~models.eventsub_.ShieldModeBegin`
   * - Shield Mode End
     - :meth:`~eventsub.ShieldModeEndSubscription`
     - :func:`~twitchio.event_shield_mode_end()`
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
  
.. py:function:: event_subscription_revoked(payload: twitchio.models.eventsub_.SubscriptionRevoked) -> None
  :async:

  Event dispatched when Twitch revokes a subscription. This can occur on websockets and webhooks.
  You'll receive this message once and then no longer receive messages for the specified user and subscription type.

  Webhook:
      - The user mentioned in the subscription no longer exists. The notification's status is set to `user_removed`.
      - The user revoked the authorization token or simply changed their password. The notification's status is set to `authorization_revoked`.
      - The callback failed to respond in a timely manner too many times. The notification's status is set to `notification_failures_exceeded`.
      - The subscribed to subscription type and version is no longer supported. The notification's status is set to `version_removed`.

  Websocket:
      - The user mentioned in the subscription no longer exists. The notification's status field is set to `user_removed`.
      - The user revoked the authorization token that the subscription relied on. The notification's status field is set to `authorization_revoked`.
      - The subscribed to subscription type and version is no longer supported. The notification's status field is set to `version_removed`.


  :param SubscriptionRevoked payload: The payload containing token information.


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


Bans
----

.. py:function:: event_ban(payload: twitchio.ChannelBan) -> None
    :async:

    Event dispatched when a viewer is banned from the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Ban <channelban>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelBanSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelBan payload: The EventSub payload received for this event.

.. py:function:: event_unban(payload: twitchio.ChannelUnban) -> None
    :async:

    Event dispatched when a viewer is unbanned from the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Unban <channelunban>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelUnbanSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelUnban payload: The EventSub payload received for this event.

.. py:function:: event_unban_request(payload: twitchio.ChannelUnbanRequest) -> None
    :async:

    Event dispatched when user creates an unban request.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Unban Request Create <channelunban_requestcreate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelUnbanRequestSubscription`
    for each required broadcaster, with moderator, to receive this event.

    :param twitchio.ChannelUnbanRequest payload: The EventSub payload received for this event.

.. py:function:: event_unban_request_resolve(payload: twitchio.ChannelUnbanRequest) -> None
    :async:

    Event dispatched when an unban request is resolved.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Unban Request Resolve <channelunban_requestresolve>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelUnbanRequestResolveSubscription`
    for each required broadcaster, with moderator, to receive this event.

    :param twitchio.ChannelUnbanRequest payload: The EventSub payload received for this event.


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

.. py:function:: event_cheer(payload: twitchio.ChannelCheer) -> None
    :async:

    Event dispatched when a user cheers on the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Cheer <channelcheer>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelCheerSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelCheer payload: The EventSub payload received for this event.

.. py:function:: event_raid(payload: twitchio.ChannelRaid) -> None
    :async:

    Event dispatched when a user broadcaster raids another broadcaster's channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Raid <channelraid>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelRaidSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelRaid payload: The EventSub payload received for this event.


Channel Points
--------------

.. py:function:: event_automatic_redemption_add(payload: twitchio.ChannelPointsAutoRedeemAdd) -> None
    :async:

    Event dispatched when a viewer has redeemed an automatic channel points reward on the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Points Automatic Reward Redemption <channelchannel_points_automatic_reward_redemptionadd>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPointsAutoRedeemSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelPointsAutoRedeemAdd payload: The EventSub payload received for this event.

.. py:function:: event_custom_reward_add(payload: twitchio.ChannelPointsRewardAdd) -> None
    :async:

    Event dispatched when a custom channel points reward has been created for the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Points Custom Reward Add <channelchannel_points_custom_rewardadd>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPointsRewardAddSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelPointsRewardAdd payload: The EventSub payload received for this event.

.. py:function:: event_custom_reward_update(payload: twitchio.ChannelPointsRewardUpdate) -> None
    :async:

    Event dispatched when a custom channel points reward has been updated for the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Points Custom Reward Update <channelchannel_points_custom_rewardupdate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPointsRewardUpdateSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelPointsRewardUpdate payload: The EventSub payload received for this event.

.. py:function:: event_custom_reward_remove(payload: twitchio.ChannelPointsRewardRemove) -> None
    :async:

    Event dispatched when a custom channel points reward has been removed from the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Points Custom Reward Remove <channelchannel_points_custom_rewardremove>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPointsRewardRemoveSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelPointsRewardRemove payload: The EventSub payload received for this event.

.. py:function:: event_custom_redemption_add(payload: twitchio.ChannelPointsRedemptionAdd) -> None
    :async:

    Event dispatched when a viewer has redeemed a custom channel points reward on the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Points Custom Reward Redemption Add <channelchannel_points_custom_reward_redemptionadd>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPointsRedemptionAddSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelPointsRedemptionAdd payload: The EventSub payload received for this event.

.. py:function:: event_custom_redemption_update(payload: twitchio.ChannelPointsRedemptionUpdate) -> None
    :async:

    Event dispatched when a redemption of a channel points custom reward has been updated for the specified channel.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Points Custom Reward Redemption Update <channelchannel_points_custom_reward_redemptionupdate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPointsRedemptionUpdateSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChannelPointsRedemptionUpdate payload: The EventSub payload received for this event.

Charity Campaigns
-----------------

.. py:function:: event_charity_campaign_donate(payload: twitchio.CharityCampaignDonation) -> None
  :async:

  Event dispatched when a user donates to the broadcaster's charity campaign.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Charity Donation <channelcharity_campaigndonate>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.CharityDonationSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.CharityCampaignDonation payload: The EventSub payload for this event.

.. py:function:: event_charity_campaign_start(payload: twitchio.CharityCampaignStart) -> None
  :async:

  Event dispatched when the broadcaster starts a charity campaign.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Charity Campaign Start <channelcharity_campaignstart>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.CharityCampaignStartSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.CharityCampaignStart payload: The EventSub payload for this event.

.. py:function:: event_charity_campaign_progress(payload: twitchio.CharityCampaignProgress) -> None
  :async:

  Event dispatched when progress is made towards the campaign’s goal or when the broadcaster changes the fundraising goal.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Charity Campaign Progress <channelcharity_campaignprogress>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.CharityCampaignProgressSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.CharityCampaignProgress payload: The EventSub payload for this event.

.. py:function:: event_charity_campaign_stop(payload: twitchio.CharityCampaignStop) -> None
  :async:

  Event dispatched when the broadcaster stops a charity campaign.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Charity Campaign Stop <channelcharity_campaignend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.CharityCampaignStopSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.CharityCampaignStop payload: The EventSub payload for this event.

Chat / Messages
---------------

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


.. py:function:: event_chat_notification(payload: twitchio.ChatNotification) -> None
    :async:

    Event dispatched when an event that appears in chat has occurred. 
    This event can be used to replace multiple other events, depending on the data required.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat Notification <channelchatnotification>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatNotificationSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChatNotification payload: The EventSub payload received for this event.

.. py:function:: event_chat_settings_update(payload: twitchio.ChatSettingsUpdate) -> None
    :async:

    Event dispatched when a broadcaster's chat settings are updated.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat Settings Update <channelchat_settingsupdate>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatSettingsUpdateSubscription`
    for each required broadcaster to receive this event.

    :param twitchio.ChatSettingsUpdate payload: The EventSub payload received for this event.

.. py:function:: event_chat_user_message_hold(payload: twitchio.ChatUserMessageHold) -> None
    :async:

    Event dispatched when a user is notified if their message is caught by automod.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat User Message Hold <channelchatuser_message_hold>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatUserMessageHoldSubscription`
    for each required broadcaster and user to receive this event.

    :param twitchio.ChatUserMessageHold payload: The EventSub payload received for this event.

.. py:function:: event_chat_user_message_update(payload: twitchio.ChatUserMessageUpdate) -> None
    :async:

    Event dispatched when a user is notified if their message's automod status is updated.
    
    Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Chat User Message Hold <channelchatuser_message_hold>`
    
    You must subscribe to EventSub with :class:`~twitchio.eventsub.ChatUserMessageUpdateSubscription`
    for each required broadcaster and user to receive this event.

    :param twitchio.ChatUserMessageUpdate payload: The EventSub payload received for this event.

.. py:function:: event_message_whisper(payload: twitchio.Whisper) -> None
  :async:

  Event dispatched when a user receives this a whisper.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`User Whisper <userwhispermessage>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.WhisperReceivedSubscription` for each required user
  to receive this event.

  :param twitchio.Whisper payload: The EventSub payload for this event.

Goals
-----

.. py:function:: event_goal_begin(payload: twitchio.GoalBegin) -> None
  :async:

  Event dispatched when a broadcaster begins a goal.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Goal Begin <channelgoalbegin>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.GoalBeginSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.GoalBegin payload: The EventSub payload for this event.

.. py:function:: event_goal_progress(payload: twitchio.GoalProgress) -> None
  :async:

  Event dispatched when progress (either positive or negative) is made towards a broadcaster's goal.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Goal Progress <channelgoalprogress>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.GoalProgressSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.GoalProgress payload: The EventSub payload for this event.

.. py:function:: event_goal_end(payload: twitchio.GoalEnd) -> None
  :async:

  Event dispatched when a broadcaster ends a goal.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Goal End <channelgoalend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.GoalEndSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.GoalEnd payload: The EventSub payload for this event.

Hype Train
----------

.. py:function:: event_hype_train(payload: twitchio.HypeTrainBegin) -> None
  :async:

  Event dispatched when a Hype Train begins on the specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Hype Train Begin <channelhype_trainbegin>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.HypeTrainBeginSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.HypeTrainBegin payload: The EventSub payload for this event.

.. py:function:: event_hype_train_progress(payload: twitchio.HypeHypeTrainProgress) -> None
  :async:

  Event dispatched when a Hype Train makes progress on the specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Hype Train Progress <channelhype_trainprogress>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.HypeTrainProgressSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.HypeTrainProgress payload: The EventSub payload for this event.

.. py:function:: event_hype_train_end(payload: twitchio.HypeTrainEnd) -> None
  :async:

  Event dispatched when a Hype Train ends on the specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Hype Train End <channelhype_trainend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.HypeTrainEndSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.HypeTrainEnd payload: The EventSub payload for this event.


Moderation
----------

.. py:function:: event_mod_action(payload: twitchio.ChannelModerate) -> None
  :async:

  Event dispatched when a moderator performs a moderation action in a channel.
  If you subscribe to V2 then warnings are included.
    
  Corresponds to the Twitch EventSub subscriptions :es-docs:`Channel Moderate <channelmoderate>` and 
  :es-docs:`Channel Moderate V2 <channelmoderate-v2>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelModerateSubscription` or 
  :class:`~twitchio.eventsub.ChannelModerateV2Subscription` for each required broadcaster to receive this event.


  :param twitchio.ChannelModerate payload: The EventSub payload for this event.

.. py:function:: event_moderator_add(payload: twitchio.ChannelModeratorAdd) -> None
  :async:

  Event dispatched when moderator privileges were added to a user on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Moderator Add <channelmoderatoradd>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelModeratorAddSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelModeratorAdd payload: The EventSub payload for this event.

.. py:function:: event_moderator_remove(payload: twitchio.ChannelModeratorRemove) -> None
  :async:

  Event dispatched when moderator privileges were rmoved from a user on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Moderator Removed <channelmoderatorremove>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelModeratorRemoveSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelModeratorRemove payload: The EventSub payload for this event.

.. py:function:: event_vip_add(payload: twitchio.ChannelVIPAdd) -> None
  :async:

  Event dispatched when a vip is added to the channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel VIP Add <channelvipadd>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelVIPAddSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelVIPAdd payload: The EventSub payload for this event.

.. py:function:: event_vip_remove(payload: twitchio.ChannelVIPRemove) -> None
  :async:

  Event dispatched when a vip is removed from the channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel VIP Remove <channelvipremove>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelVIPRemoveSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelVIPRemove payload: The EventSub payload for this event.


Polls
-----

.. py:function:: event_poll_begin(payload: twitchio.ChannelPollBegin) -> None
  :async:

  Event dispatched when a poll started on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Poll Begin <channelpollbegin>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPollBeginSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPollBegin payload: The EventSub payload for this event.

.. py:function:: event_poll_progress(payload: twitchio.ChannelPollProgress) -> None
  :async:

  Event dispatched when users respond to a poll on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Poll Progress <channelpollprogress>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPollProgressSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPollProgress payload: The EventSub payload for this event.

.. py:function:: event_poll_end(payload: twitchio.ChannelPollEnd) -> None
  :async:

  Event dispatched when a poll ends on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Poll End <channelpollend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPollEndSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPollEnd payload: The EventSub payload for this event.

Predictions
-----------

.. py:function:: event_prediction_begin(payload: twitchio.ChannelPredictionBegin) -> None
  :async:

  Event dispatched when a prediction begins on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Prediction Begin <channelpredictionbegin>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPredictionBeginSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPredictionBegin payload: The EventSub payload for this event.

.. py:function:: event_prediction_progress(payload: twitchio.ChannelPredictionProgress) -> None
  :async:

  Event dispatched when users participated in a Prediction on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Prediction Progress <channelpredictionprogress>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPredictionProgressSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPredictionProgress payload: The EventSub payload for this event.

.. py:function:: event_prediction_lock(payload: twitchio.ChannelPredictionLock) -> None
  :async:

  Event dispatched when a prediction was locked on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Prediction Lock <channelpredictionlock>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPredictionLockSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPredictionLock payload: The EventSub payload for this event.

.. py:function:: event_prediction_end(payload: twitchio.ChannelPredictionEnd) -> None
  :async:

  Event dispatched when a prediction ended on a specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Prediction End <channelpredictionend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelPredictionEndSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ChannelPredictionEnd payload: The EventSub payload for this event.


Shared Chat
-----------

.. py:function:: event_shared_chat_begin(payload: twitchio.SharedChatSessionBegin) -> None
  :async:

  Event dispatched when a channel becomes active in an active shared chat session.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Shared Chat Session Begin <channelshared_chatbegin>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.SharedChatSessionBeginSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.SharedChatSessionBegin payload: The EventSub payload for this event.

.. py:function:: event_shared_chat_update(payload: twitchio.SharedChatSessionUpdate) -> None
  :async:

  Event dispatched when the active shared chat session the channel is in changes.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Shared Chat Session Update <channelshared_chatupdate>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.SharedChatSessionUpdateSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.SharedChatSessionUpdate payload: The EventSub payload for this event.

.. py:function:: event_shared_chat_end(payload: twitchio.SharedChatSessionEnd) -> None
  :async:

  Event dispatched when a channel leaves a shared chat session or the session ends.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Shared Chat Session End <channelshared_chatend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.SharedChatSessionEndSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.SharedChatSessionEnd payload: The EventSub payload for this event.


Shield Mode
-----------

.. py:function:: event_shield_mode_begin(payload: twitchio.ShieldModeBegin) -> None
  :async:

  Event dispatched when the broadcaster activates Shield Mode.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Shield Mode Begin <channelshield_modebegin>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ShieldModeBeginSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ShieldModeBegin payload: The EventSub payload for this event.

.. py:function:: event_shield_mode_end(payload: twitchio.ShieldModeEnd) -> None
  :async:

  Event dispatched when the broadcaster deactivates Shield Mode.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Shield Mode End <channelshield_modeend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ShieldModeEndSubscription`
  for each required broadcaster to receive this event to receive this event.

  :param twitchio.ShieldModeEnd payload: The EventSub payload for this event.


Shoutouts
---------

.. py:function:: event_shoutout_create(payload: twitchio.ShoutoutCreate) -> None
  :async:

  Event dispatched when the specified broadcaster sends a shoutout.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Shoutout Create <shoutoutcreate>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ShoutoutCreateSubscription` for each required broadcaster 
  to receive this event to receive this event.

  :param twitchio.ShoutoutCreate payload: The EventSub payload for this event.

.. py:function:: event_shoutout_receive(payload: twitchio.ShoutoutReceive) -> None
  :async:

  Event dispatched when the specified broadcaster receives a shoutout.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Shoutout Create <shoutoutreceive>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ShoutoutReceiveSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.ShoutoutReceive payload: The EventSub payload for this event.

Subscriptions
-------------

.. py:function:: event_subscription(payload: twitchio.ChannelSubscribe) -> None
  :async:

  Event dispatched when a specified channel receives a subscriber. This does not include resubscribes.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Subscribe <Channelsubscribe>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelSubscribeSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.ChannelSubscribe payload: The EventSub payload for this event.

.. py:function:: event_subscription_end(payload: twitchio.ChannelSubscriptionEnd) -> None
  :async:

  Event dispatched when a subscription to the specified channel ends.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Subscription End <channelsubscriptionend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelSubscriptionEndSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.ChannelSubscriptionEnd payload: The EventSub payload for this event.

.. py:function:: event_subscription_gift(payload: twitchio.ChannelSubscriptionGift) -> None
  :async:

  Event dispatched when a viewer gives a gift subscription to one or more users in the specified channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Subscription Gift <channelsubscriptiongift>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelSubscriptionGiftSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.ChannelSubscriptionGift payload: The EventSub payload for this event.

.. py:function:: event_subscription_message(payload: twitchio.ChannelSubscriptionMessage) -> None
  :async:

  Event dispatched when a user sends a resubscription chat message in a specific channel.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Subscription Message <channelsubscriptionmessage>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelSubscriptionMessageSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.ChannelSubscriptionMessage payload: The EventSub payload for this event.

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

Suspicious Users
----------------

.. py:function:: event_suspicious_user_message(payload: twitchio.SuspiciousUserMessage) -> None
  :async:

  Event dispatched when chat message has been sent by a suspicious user.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Suspicious User Message <channelsuspicious_usermessage>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.SuspiciousUserMessageSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.SuspiciousUserMessage payload: The EventSub payload for this event.

.. py:function:: event_suspicious_user_update(payload: twitchio.SuspiciousUserUpdate) -> None
  :async:

  Event dispatched when a suspicious user has been updated.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Suspicious User Update <channelsuspicious_userupdate>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.SuspiciousUserUpdateSubscription` for each required broadcaster
  to receive this event.

  :param twitchio.SuspiciousUserUpdate payload: The EventSub payload for this event.

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

Warnings
--------

.. py:function:: event_warning_acknowledge(payload: twitchio.ChannelWarningAcknowledge) -> None
  :async:

  Event dispatched when a user awknowledges a warning. Broadcasters and moderators can see the warning's details.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Warning Acknowledgement <channelwarningacknowledge>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelWarningAcknowledgementSubscription` 
  for each required broadcaster, with a moderator, to receive this event.

  :param twitchio.ChannelWarningAcknowledge payload: The EventSub payload for this event.

.. py:function:: event_warning_send(payload: twitchio.ChannelWarningSend) -> None
  :async:

  Event dispatched when a user is sent a warning. Broadcasters and moderators can see the warning's details.
    
  Corresponds to the Twitch EventSub subscription :es-docs:`Channel Warning Send <channelwarningsend>`.
    
  You must subscribe to EventSub with :class:`~twitchio.eventsub.ChannelWarningSendSubscription` 
  for each required broadcaster, with a moderator, to receive this event.

  :param twitchio.ChannelWarningSend payload: The EventSub payload for this event.


Payloads
~~~~~~~~

.. attributetable:: twitchio.EventErrorPayload

.. autoclass:: twitchio.EventErrorPayload()
  :members: