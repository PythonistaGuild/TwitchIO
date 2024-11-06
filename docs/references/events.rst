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
   * - Automod Message Hold
     - :meth:`~eventsub.AutomodMessageHoldSubscription`
     - automod_message_hold
   * - Automod Message Update
     - :meth:`~eventsub.AutomodMessageUpdateSubscription`
     - automod_message_update
   * - Automod Settings Update
     - :meth:`~eventsub.AutomodSettingsUpdateSubscription`
     - automod_settings_update
   * - Automod Terms Update
     - :meth:`~eventsub.AutomodTermsUpdateSubscription`
     - automod_terms_update
   * - Channel Update
     - :meth:`~eventsub.ChannelUpdateSubscription`
     - channel_update
   * - Channel Follow
     - :meth:`~eventsub.ChannelFollowSubscription`
     - follow
   * - Channel Ad Break Begin
     - :meth:`~eventsub.AdBreakBeginSubscription`
     - ad_break
   * - Channel Chat Clear
     - :meth:`~eventsub.ChatClearSubscription`
     - chat_clear
   * - Channel Chat Clear User Messages
     - :meth:`~eventsub.ChatClearUserMessagesSubscription`
     - chat_clear_user
   * - Channel Chat Message
     - :meth:`~eventsub.ChatMessageSubscription`
     - message
   * - Channel Chat Message Delete
     - :meth:`~eventsub.ChatNotificationSubscription`
     - message_delete
   * - Channel Chat Notification
     - :meth:`~eventsub.ChatMessageDeleteSubscription`
     - chat_notification
   * - Channel Chat Settings Update
     - :meth:`~eventsub.ChatSettingsUpdateSubscription`
     - chat_settings_update
   * - Channel Chat User Message Hold
     - :meth:`~eventsub.ChatUserMessageHoldSubscription`
     - chat_user_message_hold
   * - Channel Chat User Message Update
     - :meth:`~eventsub.ChatUserMessageUpdateSubscription`
     - chat_user_message_update
   * - Channel Shared Chat Session Begin
     - :meth:`~eventsub.SharedChatSessionBeginSubscription`
     - shared_chat_begin
   * - Channel Shared Chat Session Update
     - :meth:`~eventsub.SharedChatSessionUpdateSubscription`
     - shared_chat_update
   * - Channel Shared Chat Session End
     - :meth:`~eventsub.SharedChatSessionEndSubscription`
     - shared_chat_end
   * - Channel Subscribe
     - :meth:`~eventsub.ChannelSubscribeSubscription`
     - subscription
   * - Channel Subscription End
     - :meth:`~eventsub.ChannelSubscriptionEndSubscription`
     - subscription_end
   * - Channel Subscription Gift
     - :meth:`~eventsub.ChannelSubscriptionGiftSubscription`
     - subscription_gift
   * - Channel Subscription Message
     - :meth:`~eventsub.ChannelSubscribeMessageSubscription`
     - subscription_message
   * - Channel Cheer
     - :meth:`~eventsub.ChannelCheerSubscription`
     - cheer
   * - Channel Raid
     - :meth:`~eventsub.ChannelRaidSubscription`
     - raid
   * - Channel Ban
     - :meth:`~eventsub.ChannelBanSubscription`
     - ban
   * - Channel Unban
     - :meth:`~eventsub.ChannelUnbanSubscription`
     - unban
   * - Channel Unban Request Create
     - :meth:`~eventsub.ChannelUnbanRequestSubscription`
     - unban_request
   * - Channel Unban Request Resolve
     - :meth:`~eventsub.ChannelUnbanRequestResolveSubscription`
     - unban_request_resolve
   * - Channel Moderate
     - :meth:`~eventsub.ChannelModerateSubscription`
     - mod_action
   * - Channel Moderate V2
     - :meth:`~eventsub.ChannelModerateV2Subscription`
     - mod_action
   * - Channel Moderator Add
     - :meth:`~eventsub.ChannelModeratorAddSubscription`
     - moderator_add
   * - Channel Moderator Remove
     - :meth:`~eventsub.ChannelModeratorRemoveSubscription`
     - moderator_remove
   * - Channel Points Automatic Reward Redemption
     - :meth:`~eventsub.ChannelPointsAutoRedeemSubscription`
     - automatic_redemption_add
   * - Channel Points Custom Reward Add
     - :meth:`~eventsub.ChannelPointsRewardAddSubscription`
     - custom_reward_add
   * - Channel Points Custom Reward Update
     - :meth:`~eventsub.ChannelPointsRewardUpdateSubscription`
     - custom_reward_update
   * - Channel Points Custom Reward Remove
     - :meth:`~eventsub.ChannelPointsRewardRemoveSubscription`
     - custom_reward_remove
   * - Channel Points Custom Reward Redemption Add
     - :meth:`~eventsub.ChannelPointsRedeemAddSubscription`
     - custom_redemption_add
   * - Channel Points Custom Reward Redemption Update
     - :meth:`~eventsub.ChannelPointsRedeemUpdateSubscription`
     - custom_redemption_update
   * - Channel Poll Begin
     - :meth:`~eventsub.ChannelPollBeginSubscription`
     - poll_begin
   * - Channel Poll Progress
     - :meth:`~eventsub.ChannelPollProgressSubscription`
     - poll_progress
   * - Channel Poll End
     - :meth:`~eventsub.ChannelPollEndSubscription`
     - poll_end
   * - Channel Prediction Begin
     - :meth:`~eventsub.ChannelPredictionBeginSubscription`
     - prediction_begin
   * - Channel Prediction Progress
     - :meth:`~eventsub.ChannelPredictionProgressSubscription`
     - prediction_progress
   * - Channel Prediction Lock
     - :meth:`~eventsub.ChannelPredictionLockSubscription`
     - prediction_lock
   * - Channel Prediction End
     - :meth:`~eventsub.ChannelPredictionEndSubscription`
     - prediction_end
   * - Channel Suspicious User Message
     - :meth:`~eventsub.SuspiciousUserMessageSubscription`
     - suspicious_user_message
   * - Channel Suspicious User Update
     - :meth:`~eventsub.SuspiciousUserUpdateSubscription`
     - suspicious_user_update
   * - Channel VIP Add
     - :meth:`~eventsub.ChannelVIPAddSubscription`
     - vip_add
   * - Channel VIP Remove
     - :meth:`~eventsub.ChannelVIPRemoveSubscription`
     - vip_remove
   * - Channel Warning Acknowledgement
     - :meth:`~eventsub.ChannelWarningAcknowledgementSubscription`
     - warning_acknowledge
   * - Channel Warning Send
     - :meth:`~eventsub.ChannelWarningSendSubscription`
     - warning_send
   * - Charity Donation
     - :meth:`~eventsub.CharityDonationSubscription`
     - charity_campaign_donate
   * - Charity Campaign Start
     - :meth:`~eventsub.CharityCampaignStartSubscription`
     - charity_campaign_start
   * - Charity Campaign Progress
     - :meth:`~eventsub.CharityCampaignProgressSubscription`
     - charity_campaign_progress
   * - Charity Campaign Stop
     - :meth:`~eventsub.CharityCampaignStopSubscription`
     - charity_campaign_stop
   * - Goal Begin
     - :meth:`~eventsub.GoalBeginSubscription`
     - goal_begin
   * - Goal Progress
     - :meth:`~eventsub.GoalProgressSubscription`
     - goal_progress
   * - Goal End
     - :meth:`~eventsub.GoalEndSubscription`
     - goal_end
   * - Hype Train Begin
     - :meth:`~eventsub.HypeTrainBeginSubscription`
     - hype_train
   * - Hype Train Progress
     - :meth:`~eventsub.HypeTrainProgressSubscription`
     - hype_train_progress
   * - Hype Train End
     - :meth:`~eventsub.HypeTrainEndSubscription`
     - hype_train_end
   * - Shield Mode Begin
     - :meth:`~eventsub.ShieldModeBeginSubscription`
     - shield_mode_begin
   * - Shield Mode End
     - :meth:`~eventsub.ShieldModeEndSubscription`
     - shield_mode_end
   * - Shoutout Create
     - :meth:`~eventsub.ShoutoutCreateSubscription`
     - shoutout_create
   * - Shoutout Received
     - :meth:`~eventsub.ShoutoutReceiveSubscription`
     - shoutout_receive
   * - Stream Online
     - :meth:`~eventsub.StreamOnlineSubscription`
     - stream_online
   * - Stream Offline
     - :meth:`~eventsub.StreamOfflineSubscription`
     - stream_offline
   * - User Authorization Grant
     - :meth:`~eventsub.UserAuthorizationGrantSubscription`
     - user_authorization_grant
   * - User Authorization Revoke
     - :meth:`~eventsub.UserAuthorizationRevokeSubscription`
     - user_authorization_revoke
   * - User Update
     - :meth:`~eventsub.UserUpdateSubscription`
     - user_update
   * - Whisper Received
     - :meth:`~eventsub.WhisperReceivedSubscription`
     - message_whisper
