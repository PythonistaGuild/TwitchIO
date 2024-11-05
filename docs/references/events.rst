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
     - AutomodMessageHoldSubscription
     - automod_message_hold
   * - Automod Message Update
     - AutomodMessageUpdateSubscription
     - automod_message_update
   * - Automod Settings Update
     - AutomodSettingsUpdateSubscription
     - automod_settings_update
   * - Automod Terms Update
     - AutomodTermsUpdateSubscription
     - automod_terms_update
   * - Channel Update
     - ChannelUpdateSubscription
     - channel_update
   * - Channel Follow
     - ChannelFollowSubscription
     - follow
   * - Channel Ad Break Begin
     - AdBreakBeginSubscription
     - ad_break
   * - Channel Chat Clear
     - ChatClearSubscription
     - chat_clear
   * - Channel Chat Clear User Messages
     - ChatClearUserMessagesSubscription
     - chat_clear_user
   * - Channel Chat Message
     - ChatMessageSubscription
     - message
   * - Channel Chat Message Delete
     - ChatNotificationSubscription
     - message_delete
   * - Channel Chat Notification
     - ChatMessageDeleteSubscription
     - chat_notification
   * - Channel Chat Settings Update
     - ChatSettingsUpdateSubscription
     - chat_settings_update
   * - Channel Chat User Message Hold
     - ChatUserMessageHoldSubscription
     - chat_user_message_hold
   * - Channel Chat User Message Update
     - ChatUserMessageUpdateSubscription
     - chat_user_message_update
   * - Channel Shared Chat Session Begin
     - SharedChatSessionBeginSubscription
     - shared_chat_begin
   * - Channel Shared Chat Session Update
     - SharedChatSessionUpdateSubscription
     - shared_chat_update
   * - Channel Shared Chat Session End
     - SharedChatSessionEndSubscription
     - shared_chat_end
   * - Channel Subscribe
     - ChannelSubscribeSubscription
     - subscription
   * - Channel Subscription End
     - ChannelSubscriptionEndSubscription
     - subscription_end
   * - Channel Subscription Gift
     - ChannelSubscriptionGiftSubscription
     - subscription_gift
   * - Channel Subscription Message
     - ChannelSubscribeMessageSubscription
     - subscription_message
   * - Channel Cheer
     - ChannelCheerSubscription
     - cheer
   * - Channel Raid
     - ChannelRaidSubscription
     - raid
   * - Channel Ban
     - ChannelBanSubscription
     - ban
   * - Channel Unban
     - ChannelUnbanSubscription
     - unban
   * - Channel Unban Request Create
     - ChannelUnbanRequestSubscription
     - unban_request
   * - Channel Unban Request Resolve
     - ChannelUnbanRequestResolveSubscription
     - unban_request_resolve
   * - Channel Moderate
     - ChannelModerateSubscription
     - mod_action
   * - Channel Moderate V2
     - ChannelModerateV2Subscription
     - mod_action
   * - Channel Moderator Add
     - ChannelModeratorAddSubscription
     - moderator_add
   * - Channel Moderator Remove
     - ChannelModeratorRemoveSubscription
     - moderator_remove
   * - Channel Points Automatic Reward Redemption
     - ChannelPointsAutoRedeemSubscription
     - automatic_redemption_add
   * - Channel Points Custom Reward Add
     - ChannelPointsRewardAddSubscription
     - custom_reward_add
   * - Channel Points Custom Reward Update
     - ChannelPointsRewardUpdateSubscription
     - custom_reward_update
   * - Channel Points Custom Reward Remove
     - ChannelPointsRewardRemoveSubscription
     - custom_reward_remove
   * - Channel Points Custom Reward Redemption Add
     - ChannelPointsRedeemAddSubscription
     - custom_redemption_add
   * - Channel Points Custom Reward Redemption Update
     - ChannelPointsRedeemUpdateSubscription
     - custom_redemption_update
   * - Channel Poll Begin
     - ChannelPollBeginSubscription
     - poll_begin
   * - Channel Poll Progress
     - ChannelPollProgressSubscription
     - poll_progress
   * - Channel Poll End
     - ChannelPollEndSubscription
     - poll_end
   * - Channel Prediction Begin
     - ChannelPredictionBeginSubscription
     - prediction_begin
   * - Channel Prediction Progress
     - ChannelPredictionProgressSubscription
     - prediction_progress
   * - Channel Prediction Lock
     - ChannelPredictionLockSubscription
     - prediction_lock
   * - Channel Prediction End
     - ChannelPredictionEndSubscription
     - prediction_end
   * - Channel Suspicious User Message
     - SuspiciousUserMessageSubscription
     - suspicious_user_message
   * - Channel Suspicious User Update
     - SuspiciousUserUpdateSubscription
     - suspicious_user_update
   * - Channel VIP Add
     - ChannelVIPAddSubscription
     - vip_add
   * - Channel VIP Remove
     - ChannelVIPRemoveSubscription
     - vip_remove
   * - Channel Warning Acknowledgement
     - ChannelWarningAcknowledgementSubscription
     - warning_acknowledge
   * - Channel Warning Send
     - ChannelWarningSendSubscription
     - warning_send
   * - Charity Donation
     - CharityDonationSubscription
     - charity_campaign_donate
   * - Charity Campaign Start
     - CharityCampaignStartSubscription
     - charity_campaign_start
   * - Charity Campaign Progress
     - CharityCampaignProgressSubscription
     - charity_campaign_progress
   * - Charity Campaign Stop
     - CharityCampaignStopSubscription
     - charity_campaign_stop
   * - Goal Begin
     - GoalBeginSubscription
     - goal_begin
   * - Goal Progress
     - GoalProgressSubscription
     - goal_progress
   * - Goal End
     - GoalEndSubscription
     - goal_end
   * - Hype Train Begin
     - HypeTrainBeginSubscription
     - hype_train
   * - Hype Train Progress
     - HypeTrainProgressSubscription
     - hype_train_progress
   * - Hype Train End
     - HypeTrainEndSubscription
     - hype_train_end
   * - Shield Mode Begin
     - ShieldModeBeginSubscription
     - shield_mode_begin
   * - Shield Mode End
     - ShieldModeEndSubscription
     - shield_mode_end
   * - Shoutout Create
     - ShoutoutCreateSubscription
     - shoutout_create
   * - Shoutout Received
     - ShoutoutReceiveSubscription
     - shoutout_receive
   * - Stream Online
     - StreamOnlineSubscription
     - stream_online
   * - Stream Offline
     - StreamOfflineSubscription
     - stream_offline
   * - User Authorization Grant
     - UserAuthorizationGrantSubscription
     - user_authorization_grant
   * - User Authorization Revoke
     - UserAuthorizationRevokeSubscription
     - user_authorization_revoke
   * - User Update
     - UserUpdateSubscription
     - user_update
   * - Whisper Received
     - WhisperReceivedSubscription
     - message_whisper
