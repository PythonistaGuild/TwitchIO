.. currentmodule:: twitchio

.. _Event Ref:

Events Reference
################

All events are prefixed with **event_**

.. list-table::
   :header-rows: 1

   * - Type
     - Subscription
     - Event
     - Payload
   * - Automod Message Hold
     - :meth:`~eventsub.AutomodMessageHoldSubscription`
     - automod_message_hold
     - :class:`~models.eventsub_.AutomodMessageHold`
   * - Automod Message Update
     - :meth:`~eventsub.AutomodMessageUpdateSubscription`
     - automod_message_update
     - :class:`~models.eventsub_.AutomodMessageUpdate`
   * - Automod Settings Update
     - :meth:`~eventsub.AutomodSettingsUpdateSubscription`
     - automod_settings_update
     - :class:`~models.eventsub_.AutomodSettingsUpdate`
   * - Automod Terms Update
     - :meth:`~eventsub.AutomodTermsUpdateSubscription`
     - automod_terms_update
     - :class:`~models.eventsub_.AutomodTermsUpdate`
   * - Channel Update
     - :meth:`~eventsub.ChannelUpdateSubscription`
     - channel_update
     - :class:`~models.eventsub_.ChannelUpdate`
   * - Channel Follow
     - :meth:`~eventsub.ChannelFollowSubscription`
     - follow
     - :class:`~models.eventsub_.ChannelFollow`
   * - Channel Ad Break Begin
     - :meth:`~eventsub.AdBreakBeginSubscription`
     - ad_break
     - :class:`~models.eventsub_.ChannelAdBreakBegin`
   * - Channel Chat Clear
     - :meth:`~eventsub.ChatClearSubscription`
     - chat_clear
     - :class:`~models.eventsub_.ChannelChatClear`
   * - Channel Chat Clear User Messages
     - :meth:`~eventsub.ChatClearUserMessagesSubscription`
     - chat_clear_user
     - :class:`~models.eventsub_.ChannelChatClearUserMessages`
   * - Channel Chat Message
     - :meth:`~eventsub.ChatMessageSubscription`
     - message
     - :class:`~models.eventsub_.ChatMessage`
   * - Channel Chat Message Delete
     - :meth:`~eventsub.ChatMessageDeleteSubscription`
     - message_delete
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
     - :class:`~models.eventsub_.ChannelWarningSend`
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
     - shoutout_create
     - :class:`~models.eventsub_.ShoutoutCreate`
   * - Shoutout Received
     - :meth:`~eventsub.ShoutoutReceiveSubscription`
     - shoutout_receive
     - :class:`~models.eventsub_.ShoutoutReceive`
   * - Stream Online
     - :meth:`~eventsub.StreamOnlineSubscription`
     - stream_online
     - :class:`~models.eventsub_.StreamOnline`
   * - Stream Offline
     - :meth:`~eventsub.StreamOfflineSubscription`
     - stream_offline
     - :class:`~models.eventsub_.StreamOffline`
   * - User Authorization Grant
     - :meth:`~eventsub.UserAuthorizationGrantSubscription`
     - user_authorization_grant
     - :class:`~models.eventsub_.UserAuthorizationGrant`
   * - User Authorization Revoke
     - :meth:`~eventsub.UserAuthorizationRevokeSubscription`
     - user_authorization_revoke
     - :class:`~models.eventsub_.UserAuthorizationRevoke`
   * - User Update
     - :meth:`~eventsub.UserUpdateSubscription`
     - user_update
     - :class:`~models.eventsub_.UserUpdate`
   * - Whisper Received
     - :meth:`~eventsub.WhisperReceivedSubscription`
     - message_whisper
     - :class:`~models.eventsub_.Whisper`