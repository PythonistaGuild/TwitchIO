"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import enum


__all__ = (
    "CloseCode",
    "MessageType",
    "RevocationReason",
    "ShardStatus",
    "SubscriptionType",
    "TransportMethod",
)


class TransportMethod(enum.Enum):
    """An enum of EventSub transports.

    Attributes
    ----------
    WEBHOOK: Literal["webhook"]
    WEBSOCKET: Literal["websocket]
    CONDUIT: Literal["conduit"]
    """

    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    CONDUIT = "conduit"


class ShardStatus(enum.Enum):
    ENABLED = "enabled"
    WEBHOOK_VERIFICATION_PENDING = "webhook_callback_verification_pending"
    WEBHOOK_VERIFICATION_FAILED = "webhook_callback_verification_failed"
    NOTIFICATION_FAILURES_EXCEEDED = "notification_failures_exceeded"
    WEBSOCKET_DISCONNECTED = "websocket_disconnected"
    WEBSOCKET_FAILIED_PING = "websocket_failed_ping_pong"
    WEBSOCKET_RECEIVED_INBOUD = "websocket_received_inbound_traffic"
    WEBSOCKET_INTERNAL_ERROR = "websocket_internal_error"
    WEBSOCKET_NETWORK_TIMEOUT = "websocket_network_timeout"
    WEBSOCKET_NETWORK_ERROR = "websocket_network_error"
    WEBSOCKET_FAILED_RECONNECT = "websocket_failed_to_reconnect"


class CloseCode(enum.Enum):
    INTERNAL_SERVER_ERROR = 4000
    SENT_INBOUND_TRAFFIC = 4001
    FAILED_PING = 4002
    CONNECTION_UNUSED = 4003
    RECONNECT_GRACE_TIMEOUT = 4004
    NETWORK_TIMEOUT = 4005
    NETWORK_ERROR = 4006
    INVALID_RECONNECT = 4007


class MessageType(enum.Enum):
    SESSION_WELCOME = "session_welcome"
    SESSION_KEEPALIVE = "session_keepalive"
    NOTIFICATION = "notification"
    SESSION_RECONNECT = "session_reconnect"
    REVOCATION = "revocation"


class SubscriptionType(enum.Enum):
    """An enum of available EventSub subscription types.

    The value of each enum attribute will be the formal name sent and received to/from Twitch.

    E.g. ``AutomodMessageHold`` -> ``"automod.message.hold"``.

    Attributes
    ----------
    AutomodMessageHold: Literal["automod.message.hold"]
    AutomodMessageUpdate: Literal["automod.message.update"]
    AutomodSettingsUpdate: Literal["automod.settings.update"]
    AutomodTermsUpdate: Literal["automod.terms.update"]
    ChannelUpdate: Literal["channel.update"]
    ChannelFollow: Literal["channel.follow"]
    ChannelAdBreakBegin: Literal["channel.ad_break.begin"]
    ChannelBitsUseSubscription: Literal["channel.bits.use"]
    ChannelChatClear: Literal["channel.chat.clear"]
    ChannelChatClearUserMessages: Literal["channel.chat.clear_user_messages"]
    ChannelChatMessage: Literal["channel.chat.message"]
    ChannelChatMessageDelete: Literal["channel.chat.message_delete"]
    ChannelChatNotification: Literal["channel.chat.notification"]
    ChannelChatSettingsUpdate: Literal["channel.chat_settings.update"]
    ChannelChatUserMessageHold: Literal["channel.chat.user_message_hold"]
    ChannelChatUserMessageUpdate: Literal["channel.chat.user_message_update"]
    ChannelSharedChatBegin: Literal["channel.shared_chat.begin"]
    ChannelSharedChatUpdate: Literal["channel.shared_chat.update"]
    ChannelSharedChatEnd: Literal["channel.shared_chat.end"]
    ChannelSubscribe: Literal["channel.subscribe"]
    ChannelSubscriptionEnd: Literal["channel.subscription.end"]
    ChannelSubscriptionGift: Literal["channel.subscription.gift"]
    ChannelSubscriptionMessage: Literal["channel.subscription.message"]
    ChannelCheer: Literal["channel.cheer"]
    ChannelRaid: Literal["channel.raid"]
    ChannelBan: Literal["channel.ban"]
    ChannelUnban: Literal["channel.unban"]
    ChannelUnbanRequestCreate: Literal["channel.unban_request.create"]
    ChannelUnbanRequestResolve: Literal["channel.unban_request.resolve"]
    ChannelModerate: Literal["channel.moderate"]
    ChannelModeratorAdd: Literal["channel.moderator.add"]
    ChannelModeratorRemove: Literal["channel.moderator.remove"]
    ChannelGuestStarSessionBegin: Literal["channel.guest_star_session.begin"]
    ChannelGuestStarSessionEnd: Literal["channel.guest_star_session.end"]
    ChannelGuestStarGuestUpdate: Literal["channel.guest_star_guest.update"]
    ChannelGuestStarSettingsUpdate: Literal["channel.guest_star_settings.update"]
    ChannelChannelPointsAutomaticRewardRedemptionAdd: Literal["channel.channel_points_automatic_reward_redemption.add"]
    ChannelChannelPointsCustomRewardAdd: Literal["channel.channel_points_custom_reward.add"]
    ChannelChannelPointsCustomRewardUpdate: Literal["channel.channel_points_custom_reward.update"]
    ChannelChannelPointsCustomRewardRemove: Literal["channel.channel_points_custom_reward.remove"]
    ChannelChannelPointsCustomRewardRedemptionAdd: Literal["channel.channel_points_custom_reward_redemption.add"]
    ChannelChannelPointsCustomRewardRedemptionUpdate: Literal["channel.channel_points_custom_reward_redemption.update"]
    ChannelPollBegin: Literal["channel.poll.begin"]
    ChannelPollProgres: Literal["channel.poll.progress"]
    ChannelPollEnd: Literal["channel.poll.end"]
    ChannelPredictionBegin: Literal["channel.prediction.begin"]
    ChannelPredictionProgres: Literal["channel.prediction.progress"]
    ChannelPredictionLock: Literal["channel.prediction.lock"]
    ChannelPredictionEnd: Literal["channel.prediction.end"]
    ChannelSuspiciousUserMessage: Literal["channel.suspicious_user.message"]
    ChannelSuspiciousUserUpdate: Literal["channel.suspicious_user.update"]
    ChannelVipAdd: Literal["channel.vip.add"]
    ChannelVipRemove: Literal["channel.vip.remove"]
    ChannelCharityCampaignDonate: Literal["channel.charity_campaign.donate"]
    ChannelCharityCampaignStart: Literal["channel.charity_campaign.start"]
    ChannelCharityCampaignProgress: Literal["channel.charity_campaign.progress"]
    ChannelCharityCampaignStop: Literal["channel.charity_campaign.stop"]
    ConduitShardDisabled: Literal["conduit.shard.disabled"]
    DropEntitlementGrant: Literal["drop.entitlement.grant"]
    ExtensionBitsTransactionCreate: Literal["extension.bits_transaction.create"]
    ChannelGoalBegin: Literal["channel.goal.begin"]
    ChannelGoalProgress: Literal["channel.goal.progress"]
    ChannelGoalEnd: Literal["channel.goal.end"]
    ChannelHypeTrainBegin: Literal["channel.hype_train.begin"]
    ChannelHypeTrainProgress: Literal["channel.hype_train.progress"]
    ChannelHypeTrainEnd: Literal["channel.hype_train.end"]
    ChannelShieldModeBegin: Literal["channel.shield_mode.begin"]
    ChannelShieldModeEnd: Literal["channel.shield_mode.end"]
    ChannelShoutoutCreate: Literal["channel.shoutout.create"]
    ChannelShoutoutReceive: Literal["channel.shoutout.receive"]
    ChannelWarningAcknowledgement: Literal["channel.warning.acknowledge"]
    ChannelWarningSend: Literal["channel.warning.send"]
    StreamOnline: Literal["stream.online"]
    StreamOffline: Literal["stream.offline"]
    UserAuthorizationGrant: Literal["user.authorization.grant"]
    UserAuthorizationRevoke: Literal["user.authorization.revoke"]
    UserUpdate: Literal["user.update"]
    UserWhisperMessage: Literal["user.whisper.message"]
    """

    AutomodMessageHold = "automod.message.hold"
    AutomodMessageUpdate = "automod.message.update"
    AutomodSettingsUpdate = "automod.settings.update"
    AutomodTermsUpdate = "automod.terms.update"
    ChannelBitsUse = "channel.bits.use"
    ChannelUpdate = "channel.update"
    ChannelFollow = "channel.follow"
    ChannelAdBreakBegin = "channel.ad_break.begin"
    ChannelChatClear = "channel.chat.clear"
    ChannelChatClearUserMessages = "channel.chat.clear_user_messages"
    ChannelChatMessage = "channel.chat.message"
    ChannelChatMessageDelete = "channel.chat.message_delete"
    ChannelChatNotification = "channel.chat.notification"
    ChannelChatSettingsUpdate = "channel.chat_settings.update"
    ChannelChatUserMessageHold = "channel.chat.user_message_hold"
    ChannelChatUserMessageUpdate = "channel.chat.user_message_update"
    ChannelSharedChatBegin = "channel.shared_chat.begin"
    ChannelSharedChatUpdate = "channel.shared_chat.update"
    ChannelSharedChatEnd = "channel.shared_chat.end"
    ChannelSubscribe = "channel.subscribe"
    ChannelSubscriptionEnd = "channel.subscription.end"
    ChannelSubscriptionGift = "channel.subscription.gift"
    ChannelSubscriptionMessage = "channel.subscription.message"
    ChannelCheer = "channel.cheer"
    ChannelRaid = "channel.raid"
    ChannelBan = "channel.ban"
    ChannelUnban = "channel.unban"
    ChannelUnbanRequestCreate = "channel.unban_request.create"
    ChannelUnbanRequestResolve = "channel.unban_request.resolve"
    ChannelModerate = "channel.moderate"
    ChannelModeratorAdd = "channel.moderator.add"
    ChannelModeratorRemove = "channel.moderator.remove"
    ChannelGuestStarSessionBegin = "channel.guest_star_session.begin"
    ChannelGuestStarSessionEnd = "channel.guest_star_session.end"
    ChannelGuestStarGuestUpdate = "channel.guest_star_guest.update"
    ChannelGuestStarSettingsUpdate = "channel.guest_star_settings.update"
    ChannelChannelPointsAutomaticRewardRedemptionAdd = "channel.channel_points_automatic_reward_redemption.add"
    ChannelChannelPointsCustomRewardAdd = "channel.channel_points_custom_reward.add"
    ChannelChannelPointsCustomRewardUpdate = "channel.channel_points_custom_reward.update"
    ChannelChannelPointsCustomRewardRemove = "channel.channel_points_custom_reward.remove"
    ChannelChannelPointsCustomRewardRedemptionAdd = "channel.channel_points_custom_reward_redemption.add"
    ChannelChannelPointsCustomRewardRedemptionUpdate = "channel.channel_points_custom_reward_redemption.update"
    ChannelPollBegin = "channel.poll.begin"
    ChannelPollProgress = "channel.poll.progress"
    ChannelPollEnd = "channel.poll.end"
    ChannelPredictionBegin = "channel.prediction.begin"
    ChannelPredictionProgress = "channel.prediction.progress"
    ChannelPredictionLock = "channel.prediction.lock"
    ChannelPredictionEnd = "channel.prediction.end"
    ChannelSuspiciousUserMessage = "channel.suspicious_user.message"
    ChannelSuspiciousUserUpdate = "channel.suspicious_user.update"
    ChannelVipAdd = "channel.vip.add"
    ChannelVipRemove = "channel.vip.remove"
    ChannelCharityCampaignDonate = "channel.charity_campaign.donate"
    ChannelCharityCampaignStart = "channel.charity_campaign.start"
    ChannelCharityCampaignProgress = "channel.charity_campaign.progress"
    ChannelCharityCampaignStop = "channel.charity_campaign.stop"
    ConduitShardDisabled = "conduit.shard.disabled"
    DropEntitlementGrant = "drop.entitlement.grant"
    ExtensionBitsTransactionCreate = "extension.bits_transaction.create"
    ChannelGoalBegin = "channel.goal.begin"
    ChannelGoalProgress = "channel.goal.progress"
    ChannelGoalEnd = "channel.goal.end"
    ChannelHypeTrainBegin = "channel.hype_train.begin"
    ChannelHypeTrainProgress = "channel.hype_train.progress"
    ChannelHypeTrainEnd = "channel.hype_train.end"
    ChannelShieldModeBegin = "channel.shield_mode.begin"
    ChannelShieldModeEnd = "channel.shield_mode.end"
    ChannelShoutoutCreate = "channel.shoutout.create"
    ChannelShoutoutReceive = "channel.shoutout.receive"
    ChannelWarningAcknowledgement = "channel.warning.acknowledge"
    ChannelWarningSend = "channel.warning.send"
    StreamOnline = "stream.online"
    StreamOffline = "stream.offline"
    UserAuthorizationGrant = "user.authorization.grant"
    UserAuthorizationRevoke = "user.authorization.revoke"
    UserUpdate = "user.update"
    UserWhisperMessage = "user.whisper.message"


class RevocationReason(enum.Enum):
    USER_REMOVED = "user_removed"
    AUTHORIZATION_REVOKED = "authorization_revoked"
    NOTIFICATION_FAILURES_EXCEEDED = "notification_failures_exceeded"
    VERSION_REMOVED = "version_removed"
    CHAT_USER_BANNED = "chat_user_banned"
