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

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Literal, NotRequired, TypedDict, TypeVar


if TYPE_CHECKING:
    from ..eventsub.enums import SubscriptionType
    from .conduits import Condition


__all__ = (
    "AutomodBlockedTermData",
    "AutomodMessageHoldEvent",
    "AutomodMessageHoldV2Event",
    "AutomodMessageUpdateEvent",
    "AutomodSettingsUpdateEvent",
    "AutomodTermsUpdateEvent",
    "BaseChannelPointsRewardData",
    "BaseEmoteData",
    "BaseHypeTrainEvent",
    "ChannelAdBreakBeginEvent",
    "ChannelBanEvent",
    "ChannelBitsUseEvent",
    "ChannelChatClearEvent",
    "ChannelChatClearUserMessagesEvent",
    "ChannelChatMessageDeleteEvent",
    "ChannelChatMessageEvent",
    "ChannelChatNotificationEvent",
    "ChannelChatSettingsUpdateEvent",
    "ChannelCheerEvent",
    "ChannelFollowEvent",
    "ChannelModerateEvent",
    "ChannelModerateEventV2",
    "ChannelModeratorAddEvent",
    "ChannelModeratorRemoveEvent",
    "ChannelPointsAutoRewardRedemptionEvent",
    "ChannelPointsCustomRewardAddEvent",
    "ChannelPointsCustomRewardRemoveEvent",
    "ChannelPointsCustomRewardUpdateEvent",
    "ChannelPointsEmoteData",
    "ChannelPointsImageData",
    "ChannelPointsRewardRedemptionAddEvent",
    "ChannelPointsRewardRedemptionUpdateEvent",
    "ChannelPointsUnlockedEmoteData",
    "ChannelPollBeginEvent",
    "ChannelPollEndEvent",
    "ChannelPollProgressEvent",
    "ChannelPredictionBeginEvent",
    "ChannelPredictionBeginEvent",
    "ChannelPredictionEndEvent",
    "ChannelPredictionLockEvent",
    "ChannelPredictionProgressEvent",
    "ChannelRaidEvent",
    "ChannelSharedChatSessionBeginEvent",
    "ChannelSharedChatSessionEndEvent",
    "ChannelSharedChatSessionUpdateEvent",
    "ChannelSubscribeEvent",
    "ChannelSubscribeMessageEvent",
    "ChannelSubscriptionEndEvent",
    "ChannelSubscriptionGiftEvent",
    "ChannelSuspiciousUserMessageEvent",
    "ChannelSuspiciousUserUpdateEvent",
    "ChannelUnbanEvent",
    "ChannelUnbanRequestEvent",
    "ChannelUnbanRequestResolveEvent",
    "ChannelUpdateEvent",
    "ChannelVIPAddEvent",
    "ChannelVIPRemoveEvent",
    "ChannelWarningAcknowledgeEvent",
    "ChannelWarningSendEvent",
    "CharityCampaignDonationEvent",
    "CharityCampaignProgressEvent",
    "CharityCampaignStartEvent",
    "CharityCampaignStopEvent",
    "ChatAnnouncementData",
    "ChatBitsBadgeTierData",
    "ChatCharityAmountData",
    "ChatCharityDonationData",
    "ChatCommunitySubGiftData",
    "ChatGiftPaidUpgradeData",
    "ChatMessageBadgeData",
    "ChatMessageCheerData",
    "ChatMessageCheermoteData",
    "ChatMessageEmoteData",
    "ChatMessageFragmentsData",
    "ChatMessageReplyData",
    "ChatPayItForwardData",
    "ChatPrimePaidUpgradeData",
    "ChatRaidData",
    "ChatResubData",
    "ChatSubData",
    "ChatSubGiftData",
    "ChatUserMessageHoldEvent",
    "ChatUserMessageUpdateEvent",
    "EventSubHeaders",
    "GoalBeginEvent",
    "GoalEndEvent",
    "GoalProgressEvent",
    "HypeTrainBeginEvent",
    "HypeTrainContributionData",
    "HypeTrainEndEvent",
    "HypeTrainProgressEvent",
    "ModerateAutoModTermsData",
    "ModerateBanData",
    "ModerateDeleteData",
    "ModerateFollowersData",
    "ModerateRaidData",
    "ModerateSlowData",
    "ModerateTimeoutData",
    "ModerateUnbanRequestData",
    "ModerateWarnData",
    "PollChoiceData",
    "PowerUpData",
    "PowerUpEmoteDataData",
    "ReedemedRewardData",
    "ShardStatus",
    "ShieldModeBeginEvent",
    "ShieldModeEndEvent",
    "ShoutoutCreateEvent",
    "ShoutoutReceiveEvent",
    "StreamOfflineEvent",
    "StreamOnlineEvent",
    "SubscribeEmoteData",
    "SubscribeMessageData",
    "SuspiciousMessageData",
    "UserAuthorizationGrantEvent",
    "UserAuthorizationRevokeEvent",
    "UserUpdateEvent",
    "UserWhisperEvent",
)


T = TypeVar("T")

EventSubHeaders = TypedDict(
    "EventSubHeaders",
    {
        "Twitch-Eventsub-Message-Id": str,
        "Twitch-Eventsub-Message-Retry": str,
        "Twitch-Eventsub-Message-Type": Literal["notification", "webhook_callback_verification", "revocation"],
        "Twitch-Eventsub-Message-Signature": str,
        "Twitch-Eventsub-Message-Timestamp": str,
        "Twitch-Eventsub-Subscription-Type": str,
        "Twitch-Eventsub-Subscription-Version": str,
    },
    total=False,
)


class SubscriptionCreateTransport(TypedDict):
    method: Literal["websocket"] | Literal["webhook"] | Literal["conduit"]
    callback: NotRequired[str]
    secret: NotRequired[str]
    session_id: NotRequired[str]
    conduit_id: NotRequired[str]


class _SubscriptionData(TypedDict):  # type: ignore
    type: SubscriptionType
    version: str
    condition: Condition
    transport: SubscriptionCreateTransport
    token_for: str | None


class SubscriptionCreateRequest(TypedDict):
    type: str
    version: str
    condition: Condition
    transport: SubscriptionCreateTransport
    session_id: NotRequired[str]
    conduit_id: NotRequired[str]


class BaseBroadcasterEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class BaseUserEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str


class BaseModeratorEvent(TypedDict):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str


class BroadcasterModeratorEvent(BaseBroadcasterEvent, BaseModeratorEvent): ...


class BroadcasterUserEvent(BaseBroadcasterEvent, BaseUserEvent): ...


class BroadcasterModUserEvent(BaseBroadcasterEvent):
    moderator_user_id: str
    moderator_user_login: str
    moderator_user_name: str
    user_id: str
    user_login: str
    user_name: str


class WebhookTransport(TypedDict):
    method: Literal["webhook"]
    callback: str


class WebsocketTransport(TypedDict):
    method: Literal["websocket"]
    session_id: str


class ConduitTransport(TypedDict):
    method: Literal["conduit"]
    conduit_id: str


class WebsocketMetadata(TypedDict):
    message_id: str
    message_type: str
    message_timestamp: str
    subscription_type: str
    subscription_version: str


class BaseSubscription(TypedDict, Generic[T]):
    id: str
    type: str
    version: str
    status: Literal["enabled"] | Literal["webhook_callback_verification_pending"]
    cost: NotRequired[int]
    condition: T
    created_at: str


class AnySubscription(BaseSubscription[T]):
    transport: WebhookTransport | WebsocketTransport | ConduitTransport


class SubscriptionResponse(TypedDict):
    data: list[AnySubscription[Condition]]
    total: int
    total_cost: int
    max_total_cost: int


class AutomodMessageHoldEvent(BroadcasterUserEvent):
    message_id: str
    message: ChatMessageData
    level: int
    category: str
    held_at: str


class AutomodBoundaries(TypedDict):
    start_pos: int
    end_pos: int


class AutomodV2Data(TypedDict):
    category: str
    level: int
    boundaries: list[AutomodBoundaries]


class AutomodBlockedTermData(TypedDict):
    term_id: str
    boundary: AutomodBoundaries
    owner_broadcaster_user_id: str
    owner_broadcaster_user_login: str
    owner_broadcaster_user_name: str


class AutomodBlockedTerms(TypedDict):
    terms_found: list[AutomodBlockedTermData]


class AutomodMessageHoldV2Event(BroadcasterUserEvent):
    message_id: str
    message: ChatMessageData
    held_at: str
    reason: Literal["automod", "blocked_term"]
    blocked_term: AutomodBlockedTerms | None
    automod: AutomodV2Data | None


class AutomodMessageUpdateEvent(BroadcasterModUserEvent):
    message_id: str
    message: ChatMessageData
    level: int
    category: str
    held_at: str
    status: Literal["Approved", "Denied", "Expired"]


class AutomodSettingsUpdateEvent(BroadcasterModeratorEvent):
    overall_level: int | None
    disability: int
    aggression: int
    sexuality_sex_or_gender: int
    misogyny: int
    bullying: int
    swearing: int
    race_ethnicity_or_religion: int
    sex_based_terms: int


class AutomodTermsUpdateEvent(BroadcasterModeratorEvent):
    action: Literal["add_permitted", "remove_permitted", "add_blocked", "remove_blocked"]
    from_automod: bool
    terms: list[str]


class ChannelUpdateEvent(BaseBroadcasterEvent):
    title: str
    language: str
    category_id: str
    category_name: str
    content_classification_labels: list[str]


class ChannelFollowEvent(BroadcasterUserEvent):
    followed_at: str


class ChannelAdBreakBeginEvent(BaseBroadcasterEvent):
    requester_user_id: str
    requester_user_login: str
    requester_user_name: str
    duration_seconds: str
    duration_seconds: str
    duration_seconds: str
    started_at: str
    is_automatic: str


class PowerUpEmoteDataData(TypedDict):
    id: str
    name: str


class PowerUpData(TypedDict):
    type: Literal["message_effect", "celebration", "gigantify_an_emote"]
    emote: PowerUpEmoteDataData | None
    message_effect_id: str | None


class ChannelBitsUseEvent(BroadcasterUserEvent):
    bits: int
    type: Literal["cheer", "power_up"]
    message: ChatMessageData
    power_up: PowerUpData | None


class ChannelChatClearEvent(BaseBroadcasterEvent): ...


class ChannelChatClearUserMessagesEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_name: str


class ChatMessageEmoteData(TypedDict):
    id: str
    emote_set_id: str
    owner_id: NotRequired[str]
    format: NotRequired[list[Literal["static", "animated"]]]


class ChatMessageMention(BaseUserEvent): ...


class ChatMessageCheermoteData(TypedDict):
    prefix: str
    bits: int
    tier: int


class ChatMessageFragmentsData(TypedDict):
    text: str
    type: Literal["text", "cheermote", "emote", "mention"]
    cheermote: ChatMessageCheermoteData | None
    emote: ChatMessageEmoteData | None
    mention: NotRequired[ChatMessageMention | None]


class ChatMessageReplyData(TypedDict):
    parent_message_id: str
    parent_message_body: str
    parent_user_id: str
    parent_user_name: str
    parent_user_login: str
    thread_message_id: str
    thread_user_id: str
    thread_user_name: str
    thread_user_login: str


class ChatMessageBadgeData(TypedDict):
    set_id: str
    id: str
    info: str


class ChatMessageData(TypedDict):
    text: str
    fragments: list[ChatMessageFragmentsData]


class ChatMessageCheerData(TypedDict):
    bits: int


class ChannelChatMessageEvent(BaseBroadcasterEvent):
    chatter_user_id: str
    chatter_user_login: str
    chatter_user_name: str
    message_id: str
    message: ChatMessageData
    color: str
    message_type: Literal[
        "text",
        "channel_points_highlighted",
        "channel_points_sub_only",
        "user_intro",
        "power_ups_message_effect",
        "power_ups_gigantified_emote",
    ]
    badges: list[ChatMessageBadgeData]
    reply: ChatMessageReplyData | None
    cheer: ChatMessageCheerData | None
    channel_points_custom_reward_id: str | None
    channel_points_animation_id: str | None
    source_broadcaster_user_id: str | None
    source_broadcaster_user_login: str | None
    source_broadcaster_user_name: str | None
    source_message_id: str | None
    source_badges: list[ChatMessageBadgeData] | None


class ChatSubData(TypedDict):
    sub_tier: Literal["1000", "2000", "3000"]
    is_prime: bool
    duration_months: int


class ChatResubData(TypedDict):
    cumulative_months: int
    duration_months: int
    streak_months: int | None
    sub_tier: Literal["1000", "2000", "3000"]
    is_prime: bool
    is_gift: bool
    gifter_is_anonymous: bool | None
    gifter_user_id: str | None
    gifter_user_name: str | None
    gifter_user_login: str | None


class ChatSubGiftData(TypedDict):
    duration_months: int
    cumulative_total: int | None
    recipient_user_id: str
    recipient_user_name: str
    recipient_user_login: str
    sub_tier: Literal["1000", "2000", "3000"]
    community_gift_id: str | None


class ChatCommunitySubGiftData(TypedDict):
    id: str
    total: int
    sub_tier: Literal["1000", "2000", "3000"]
    cumulative_total: int | None


class ChatGiftPaidUpgradeData(TypedDict):
    gifter_is_anonymous: bool
    gifter_user_id: str | None
    gifter_user_name: str | None
    gifter_user_login: str | None


class ChatPrimePaidUpgradeData(TypedDict):
    sub_tier: Literal["1000", "2000", "3000"]


class ChatRaidData(TypedDict):
    user_id: str
    user_name: str
    user_login: str
    viewer_count: int
    profile_image_url: str


class ChatUnraidData(TypedDict, total=False): ...


class ChatPayItForwardData(TypedDict):
    gifter_is_anonymous: bool
    gifter_user_id: str | None
    gifter_user_name: str | None
    gifter_user_login: str | None


class ChatAnnouncementData(TypedDict):
    color: Literal["BLUE", "PURPLE", "ORANGE", "GREEN", "PRIMARY"]


class ChatCharityAmountData(TypedDict):
    value: int
    decimal_place: int
    currency: str


class ChatCharityDonationData(TypedDict):
    charity_name: str
    amount: ChatCharityAmountData


class ChatBitsBadgeTierData(TypedDict):
    tier: int


class ChannelChatNotificationEvent(BaseBroadcasterEvent):
    chatter_user_id: str
    chatter_user_login: str
    chatter_user_name: str
    chatter_is_anonymous: bool
    color: str
    badges: list[ChatMessageBadgeData]
    system_message: str
    message_id: str
    message: ChatMessageData
    notice_type: Literal[
        "sub",
        "resub",
        "sub_gift",
        "community_sub_gift",
        "gift_paid_upgrade",
        "prime_paid_upgrade",
        "raid",
        "unraid",
        "pay_it_forward",
        "announcement",
        "bits_badge_tier",
        "charity_donation",
        "shared_chat_sub",
        "shared_chat_resub",
        "shared_chat_sub_gift",
        "shared_chat_community_sub_gift",
        "shared_chat_gift_paid_upgrade",
        "shared_chat_prime_paid_upgrade",
        "shared_chat_raid",
        "shared_chat_pay_it_forward",
        "shared_chat_announcement",
    ]
    sub: ChatSubData | None
    resub: ChatResubData | None
    sub_gift: ChatSubGiftData | None
    community_sub_gift: ChatCommunitySubGiftData | None
    gift_paid_upgrade: ChatGiftPaidUpgradeData | None
    prime_paid_upgrade: ChatPrimePaidUpgradeData | None
    raid: ChatRaidData | None
    unraid: ChatUnraidData | None
    pay_it_forward: ChatPayItForwardData | None
    announcement: ChatAnnouncementData | None
    bits_badge_tier: ChatBitsBadgeTierData | None
    charity_donation: ChatCharityDonationData | None
    shared_chat_sub: ChatSubData | None
    shared_chat_resub: ChatResubData | None
    shared_chat_sub_gift: ChatSubGiftData | None
    shared_chat_community_sub_gift: ChatCommunitySubGiftData | None
    shared_chat_gift_paid_upgrade: ChatGiftPaidUpgradeData | None
    shared_chat_prime_paid_upgrade: ChatPrimePaidUpgradeData | None
    shared_chat_pay_it_forward: ChatPayItForwardData | None
    shared_chat_raid: ChatRaidData | None
    shared_chat_announcement: ChatAnnouncementData | None


class ChannelChatMessageDeleteEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_name: str
    message_id: str


class ChannelChatSettingsUpdateEvent(BaseBroadcasterEvent):
    emote_mode: bool
    follower_mode: bool
    follower_mode: bool
    follower_mode_duration_minutes: int | None
    slow_mode: bool
    slow_mode_wait_time_seconds: int | None
    subscriber_mode: bool
    unique_chat_mode: bool


class ChatUserMessageHoldEvent(BroadcasterUserEvent):
    message_id: str
    message: ChatMessageData


class ChatUserMessageUpdateEvent(ChatUserMessageHoldEvent):
    status: Literal["approved", "denied", "invalid"]


class BaseSharedChatSessionData(BaseBroadcasterEvent):
    session_id: str
    host_broadcaster_user_id: str
    host_broadcaster_user_login: str
    host_broadcaster_user_name: str


class ChannelSharedChatSessionBeginEvent(BaseSharedChatSessionData):
    participants: list[BaseBroadcasterEvent]


class ChannelSharedChatSessionUpdateEvent(BaseSharedChatSessionData):
    participants: list[BaseBroadcasterEvent]


class ChannelSharedChatSessionEndEvent(BaseSharedChatSessionData): ...


class ChannelSubscribeEvent(BroadcasterUserEvent):
    tier: Literal["1000", "2000", "3000"]
    is_gift: bool


class ChannelSubscriptionEndEvent(BroadcasterUserEvent):
    tier: Literal["1000", "2000", "3000"]
    is_gift: bool


class ChannelSubscriptionGiftEvent(BaseBroadcasterEvent):
    user_id: str | None
    user_login: str | None
    user_name: str | None
    total: int
    tier: Literal["1000", "2000", "3000"]
    cumulative_total: int | None
    is_anonymous: bool


class BaseEmoteData(TypedDict):
    begin: int
    end: int
    id: str


class BaseMessageData(TypedDict):
    text: str
    emotes: list[BaseEmoteData] | None


class SubscribeEmoteData(BaseEmoteData): ...


class SubscribeMessageData(BaseMessageData): ...


class ChannelSubscribeMessageEvent(BroadcasterUserEvent):
    total: int
    tier: Literal["1000", "2000", "3000"]
    cumulative_months: int
    streak_months: int | None
    duration_months: int
    message: SubscribeMessageData


class ChannelCheerEvent(BaseBroadcasterEvent):
    user_id: str | None
    user_login: str | None
    user_name: str | None
    is_anonymous: bool
    message: str
    bits: int


class ChannelRaidEvent(TypedDict):
    from_broadcaster_user_id: str
    from_broadcaster_user_login: str
    from_broadcaster_user_name: str
    to_broadcaster_user_id: str
    to_broadcaster_user_login: str
    to_broadcaster_user_name: str
    viewers: int


class ChannelBanEvent(BroadcasterModUserEvent):
    reason: str
    banned_at: str
    ends_at: str | None
    is_permanent: bool


class ChannelUnbanEvent(BroadcasterModUserEvent): ...


class ChannelUnbanRequestEvent(BroadcasterUserEvent):
    id: str
    text: str
    created_at: str


class ChannelUnbanRequestResolveEvent(BroadcasterUserEvent):
    moderator_user_id: str | None
    moderator_user_login: str | None
    moderator_user_name: str | None
    id: str
    resolution_text: str
    status: Literal["approved", "canceled", "denied"]


class ModerateFollowersData(TypedDict):
    follow_duration_minutes: int


class ModerateSlowData(TypedDict):
    wait_time_seconds: int


class ModerateVIPData(BaseUserEvent): ...


class ModerateUnVIPData(BaseUserEvent): ...


class ModerateModData(BaseUserEvent): ...


class ModerateUnmodData(BaseUserEvent): ...


class ModerateBanData(BaseUserEvent):
    reason: str | None


class ModerateUnbanData(BaseUserEvent): ...


class ModerateTimeoutData(BaseUserEvent):
    reason: str | None
    expires_at: str


class ModerateUntimeoutData(BaseUserEvent): ...


class ModerateRaidData(BaseUserEvent):
    viewer_count: int


class ModerateUnraidData(BaseUserEvent): ...


class ModerateDeleteData(BaseUserEvent):
    message_id: str
    message_body: str


class ModerateAutoModTermsData(TypedDict):
    action: Literal["add", "remove"]
    terms: list[str]
    list: Literal["blocked", "permitted"]
    from_automod: bool


class ModerateUnbanRequestData(BaseUserEvent):
    is_approved: bool
    moderator_message: str


class ModerateWarnData(BaseUserEvent):
    chat_rules_cited: list[str] | None
    reason: str | None


class BaseChannelModerate(TypedDict):
    followers: ModerateFollowersData | None
    slow: ModerateSlowData | None
    vip: ModerateVIPData | None
    unvip: ModerateUnVIPData | None
    mod: ModerateModData | None
    unmod: ModerateUnmodData | None
    ban: ModerateBanData | None
    unban: ModerateUnbanData | None
    timeout: ModerateTimeoutData | None
    untimeout: ModerateUntimeoutData | None
    raid: ModerateRaidData | None
    unraid: ModerateUnraidData | None
    delete: ModerateDeleteData | None
    automod_terms: ModerateAutoModTermsData | None
    unban_request: ModerateUnbanRequestData | None
    source_broadcaster_user_id: str
    source_broadcaster_user_login: str
    source_broadcaster_user_name: str
    shared_chat_ban: ModerateBanData | None
    shared_chat_unban: ModerateUnbanData | None
    shared_chat_timeout: ModerateTimeoutData | None
    shared_chat_untimeout: ModerateUntimeoutData | None
    shared_chat_delete: ModerateDeleteData | None


class ChannelModerateEvent(BaseChannelModerate, BroadcasterModeratorEvent):
    action: Literal[
        "ban",
        "timeout",
        "unban",
        "untimeout",
        "clear",
        "emoteonly",
        "emoteonlyoff",
        "followers",
        "followersoff",
        "uniquechat",
        "uniquechatoff",
        "slow",
        "slowoff",
        "subscribers",
        "subscribersoff",
        "unraid",
        "delete",
        "unvip",
        "vip",
        "raid",
        "add_blocked_term",
        "add_permitted_term",
        "remove_blocked_term",
        "remove_permitted_term",
        "mod",
        "unmod",
        "approve_unban_request",
        "deny_unban_request",
        "shared_chat_ban",
        "shared_chat_unban",
        "shared_chat_timeout",
        "shared_chat_untimeout",
        "shared_chat_delete",
    ]


class ChannelModerateEventV2(BaseChannelModerate, BroadcasterModeratorEvent):
    action: Literal[
        "ban",
        "timeout",
        "unban",
        "untimeout",
        "clear",
        "emoteonly",
        "emoteonlyoff",
        "followers",
        "followersoff",
        "uniquechat",
        "uniquechatoff",
        "slow",
        "slowoff",
        "subscribers",
        "subscribersoff",
        "unraid",
        "delete",
        "unvip",
        "vip",
        "raid",
        "add_blocked_term",
        "add_permitted_term",
        "remove_blocked_term",
        "remove_permitted_term",
        "mod",
        "unmod",
        "approve_unban_request",
        "deny_unban_request",
        "warn",
        "shared_chat_ban",
        "shared_chat_unban",
        "shared_chat_timeout",
        "shared_chat_untimeout",
        "shared_chat_delete",
    ]
    warn: ModerateWarnData | None


class ChannelModeratorAddEvent(BroadcasterUserEvent): ...


class ChannelModeratorRemoveEvent(BroadcasterUserEvent): ...


class ChannelPointsEmoteData(BaseEmoteData): ...


class ChannelPointsMessageData(BaseMessageData): ...


class ChannelPointsUnlockedEmoteData(TypedDict):
    id: str
    name: str


class BaseChannelPointsRewardData(TypedDict):
    type: Literal[
        "single_message_bypass_sub_mode",
        "send_highlighted_message",
        "random_sub_emote_unlock",
        "chosen_sub_emote_unlock",
        "chosen_modified_sub_emote_unlock",
        "message_effect",
        "gigantify_an_emote",
        "celebration",
    ]
    cost: NotRequired[int]
    unlocked_emote: NotRequired[ChannelPointsUnlockedEmoteData]
    channel_points: NotRequired[int]
    emote: NotRequired[ChannelPointsUnlockedEmoteData]


class ChannelPointsAutoRewardRedemptionEvent(BroadcasterUserEvent):
    id: str
    reward: BaseChannelPointsRewardData
    message: ChannelPointsMessageData
    user_input: str | None
    redeemed_at: str


class ChannelPointsMaxPerData(TypedDict):
    is_enabled: bool
    value: int


class ChannelPointsGlobalCooldownData(TypedDict):
    is_enabled: bool
    seconds: int


class ChannelPointsImageData(TypedDict):
    url_1x: str
    url_2x: str
    url_4x: str


class BaseChannelPointsCustomReward(BaseBroadcasterEvent):
    id: str
    is_enabled: bool
    is_paused: bool
    is_in_stock: bool
    title: str
    cost: int
    prompt: str
    is_user_input_required: bool
    should_redemptions_skip_request_queue: bool
    cooldown_expires_at: str | None
    redemptions_redeemed_current_stream: int | None
    max_per_stream: ChannelPointsMaxPerData
    max_per_user_per_stream: ChannelPointsMaxPerData
    global_cooldown: ChannelPointsGlobalCooldownData
    background_color: str
    image: ChannelPointsImageData
    default_image: ChannelPointsImageData


class ChannelPointsCustomRewardAddEvent(BaseChannelPointsCustomReward): ...


class ChannelPointsCustomRewardUpdateEvent(BaseChannelPointsCustomReward): ...


class ChannelPointsCustomRewardRemoveEvent(BaseChannelPointsCustomReward): ...


class ReedemedRewardData(TypedDict):
    id: str
    title: str
    cost: str
    prompt: str


class BaseChannelPointsCustomRewardRedeemData(BroadcasterUserEvent):
    id: str
    user_input: str
    status: Literal["unknown", "unfulfilled", "fulfilled", "canceled"]
    reward: ReedemedRewardData
    redeemed_at: str


class ChannelPointsRewardRedemptionAddEvent(BaseChannelPointsCustomRewardRedeemData): ...


class ChannelPointsRewardRedemptionUpdateEvent(BaseChannelPointsCustomRewardRedeemData): ...


class PollVotingData(TypedDict):
    is_enabled: bool
    amount_per_vote: int


class PollChoiceData(TypedDict):
    id: str
    title: str
    bits_votes: int
    channel_points_votes: int
    votes: int


class BaseChannelPoll(BaseBroadcasterEvent):
    id: str
    title: str
    choices: list[PollChoiceData]
    bits_voting: PollVotingData
    channel_points_voting: PollVotingData
    started_at: str


class ChannelPollBeginEvent(BaseChannelPoll):
    ends_at: str


class ChannelPollProgressEvent(BaseChannelPoll):
    ends_at: str


class ChannelPollEndEvent(BaseChannelPoll):
    status: Literal["completed", "archived", "terminated"]
    ended_at: str


class PredictorData(BaseUserEvent):
    channel_points_won: int | None
    channel_points_used: int


class PredictionOutcomeData(TypedDict):
    id: str
    title: str
    color: Literal["blue", "pink"]
    users: NotRequired[int]
    channel_points: NotRequired[int]
    top_predictors: NotRequired[list[PredictorData]]


class BaseChannelPredictionData(BaseBroadcasterEvent):
    id: str
    title: str
    outcomes: list[PredictionOutcomeData]
    started_at: str


class ChannelPredictionBeginEvent(BaseChannelPredictionData):
    locks_at: str


class ChannelPredictionProgressEvent(BaseChannelPredictionData):
    locks_at: str


class ChannelPredictionLockEvent(BaseChannelPredictionData):
    locked_at: str


class ChannelPredictionEndEvent(BaseChannelPredictionData):
    winning_outcome_id: str
    status: Literal["resolved", "canceled"]
    ended_at: str


class ChannelSuspiciousUserUpdateEvent(BroadcasterModUserEvent):
    low_trust_status: Literal["none", "active_monitoring", "restricted"]


class SuspiciousMessageData(ChatMessageData):
    message_id: str


class ChannelSuspiciousUserMessageEvent(BroadcasterUserEvent):
    low_trust_status: Literal["none", "active_monitoring", "restricted"]
    shared_ban_channel_ids: list[str]
    types: list[Literal["manually_added", "ban_evader", "banned_in_shared_channel"]]
    ban_evasion_evaluation: Literal["unknown", "possible", "likely"]
    message: SuspiciousMessageData


class ChannelVIPAddEvent(BroadcasterUserEvent): ...


class ChannelVIPRemoveEvent(BroadcasterUserEvent): ...


class ChannelWarningAcknowledgeEvent(BroadcasterUserEvent): ...


class ChannelWarningSendEvent(BroadcasterModUserEvent):
    reason: str
    chat_rules_cited: list[str] | None


class CharityDonationData(TypedDict):
    value: int
    decimal_places: int
    currency: str


class BaseCharityCampaignData(BaseBroadcasterEvent):
    id: str
    charity_name: str
    charity_description: str
    charity_logo: str
    charity_website: str


class CharityCampaignDonationEvent(BaseCharityCampaignData, BaseUserEvent):
    campaign_id: str
    amount: CharityDonationData


class CharityCampaignStartEvent(BaseCharityCampaignData):
    current_amount: CharityDonationData
    target_amount: CharityDonationData
    started_at: str


class CharityCampaignProgressEvent(BaseCharityCampaignData):
    current_amount: CharityDonationData
    target_amount: CharityDonationData


class CharityCampaignStopEvent(BaseCharityCampaignData):
    current_amount: CharityDonationData
    target_amount: CharityDonationData
    stopped_at: str


class GoalBeginEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: Literal[
        "follow",
        "subscription",
        "subscription_count",
        "new_subscription",
        "new_subscription_count",
        "new_bit",
        "new_cheerer",
    ]
    description: str
    current_amount: int
    target_amount: int
    started_at: str


class GoalProgressEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: Literal[
        "follow",
        "subscription",
        "subscription_count",
        "new_subscription",
        "new_subscription_count",
        "new_bit",
        "new_cheerer",
    ]
    description: str
    current_amount: int
    target_amount: int
    started_at: str


class GoalEndEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: Literal[
        "follow",
        "subscription",
        "subscription_count",
        "new_subscription",
        "new_subscription_count",
        "new_bit",
        "new_cheerer",
    ]
    description: str
    is_achieved: bool
    current_amount: int
    target_amount: int
    started_at: str
    ended_at: str


class HypeTrainContributionData(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    type: Literal["bits", "subscription", "other"]
    total: int


class HypeTrainSharedParticipants(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class BaseHypeTrainEvent(BaseBroadcasterEvent):
    id: str
    total: int
    level: int
    started_at: str
    top_contributions: list[HypeTrainContributionData]
    shared_train_participants: list[HypeTrainSharedParticipants]
    type: Literal["treasure", "golden_kappa", "regular"]
    is_shared_train: bool


class HypeTrainBeginEvent(BaseHypeTrainEvent):
    progress: int
    goal: int
    all_time_high_level: int
    all_time_high_total: int
    expires_at: str


class HypeTrainProgressEvent(BaseHypeTrainEvent):
    progress: int
    goal: int
    expires_at: str


class HypeTrainEndEvent(BaseHypeTrainEvent):
    ended_at: str
    cooldown_ends_at: str


class ShieldModeBeginEvent(BroadcasterModeratorEvent):
    started_at: str


class ShieldModeEndEvent(BroadcasterModeratorEvent):
    ended_at: str


class ShoutoutCreateEvent(BroadcasterModeratorEvent):
    to_broadcaster_user_id: str
    to_broadcaster_user_login: str
    to_broadcaster_user_name: str
    started_at: str
    viewer_count: int
    cooldown_ends_at: str
    target_cooldown_ends_at: str


class ShoutoutReceiveEvent(BaseBroadcasterEvent):
    from_broadcaster_user_id: str
    from_broadcaster_user_login: str
    from_broadcaster_user_name: str
    started_at: str
    viewer_count: int


class StreamOnlineEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: Literal["live", "playlist", "watch_party", "premiere", "rerun"]
    started_at: str


class StreamOfflineEvent(TypedDict):
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str


class UserAuthorizationGrantEvent(TypedDict):
    client_id: str
    user_id: str
    user_login: str
    user_name: str


class UserAuthorizationRevokeEvent(TypedDict):
    client_id: str
    user_id: str
    user_login: str | None
    user_name: str | None


class UserUpdateEvent(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    email: NotRequired[str]
    email_verified: bool
    description: str


class WhisperContent(TypedDict):
    text: str


class UserWhisperEvent(TypedDict):
    from_user_id: str
    from_user_login: str
    from_user_name: str
    to_user_id: str
    to_user_login: str
    to_user_name: str
    whisper_id: str
    whisper: WhisperContent


ShardStatus = Literal[
    "enabled",
    "webhook_callback_verification_pending",
    "webhook_callback_verification_failed",
    "notification_failures_exceeded",
    "websocket_disconnected",
    "websocket_failed_ping_pong",
    "websocket_received_inbound_traffic",
    "websocket_internal_error",
    "websocket_network_timeout",
    "websocket_network_error",
    "websocket_failed_to_reconnect",
]
