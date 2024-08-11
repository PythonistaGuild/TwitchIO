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

from typing import Generic, Literal, NotRequired, TypedDict, TypeVar

from ..eventsub.enums import SubscriptionType
from .conduits import Condition


__all__ = (
    "AutomodEmoteData",
    "AutomodCheermoteData",
    "AutomodMessageHoldEvent",
    "AutomodMessageUpdateEvent",
    "AutomodSettingsUpdateEvent",
    "AutomodTermsUpdateEvent",
    "ChannelAdBreakBeginEvent",
    "ChannelBanEvent",
    "ChannelChatClearEvent",
    "ChannelChatClearUserMessagesEvent",
    "ChannelChatMessageDeleteEvent",
    "ChannelChatMessageEvent",
    "ChannelChatNotificationEvent",
    "ChannelChatSettingsUpdateEvent",
    "ChatUserMessageHoldEvent",
    "ChannelCheerEvent",
    "ChannelFollowEvent",
    "ChannelRaidEvent",
    "ChannelSubscribeEvent",
    "ChannelSubscribeMessageEvent",
    "ChannelSubscriptionEndEvent",
    "ChannelSubscriptionGiftEvent",
    "ChannelUnbanEvent",
    "ChannelUnbanRequestEvent",
    "ChannelUnbanRequestResolveEvent",
    "ChannelUpdateEvent",
    "ChannelVIPAddEvent",
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
    "ShoutoutCreateEvent",
    "ShoutoutReceiveEvent",
    "StreamOfflineEvent",
    "StreamOnlineEvent",
    "SubscribeEmoteData",
    "SubscribeMessageData",
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


class _SubscriptionData(TypedDict):  # type: ignore
    type: SubscriptionType
    version: str
    condition: Condition
    transport: SubscriptionCreateTransport
    token_for: str


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


AutomodEmoteData = TypedDict("AutomodEmoteData", {"text": str, "id": str, "set-id": str})


class AutomodCheermoteData(TypedDict):
    text: str
    amount: int
    prefix: str
    tier: int


class AutomodFragments(TypedDict):
    emotes: list[AutomodEmoteData]
    cheermotes: list[AutomodCheermoteData]


class AutomodMessageHoldEvent(BroadcasterUserEvent):
    message_id: str
    message: str
    level: int
    category: str
    held_at: str
    fragments: AutomodFragments


class AutomodMessageUpdateEvent(BroadcasterModUserEvent):
    message_id: str
    message: str
    level: int
    category: str
    held_at: str
    status: Literal["Approved", "Denied", "Expired"]
    fragments: AutomodFragments


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


class ChannelChatClearEvent(BaseBroadcasterEvent): ...


class ChannelChatClearUserMessagesEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_user_name: str


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


class ChatMessage(TypedDict):
    text: str
    fragments: list[ChatMessageFragmentsData]


class ChatMessageCheerData(TypedDict):
    bits: int


class ChannelChatMessageEvent(BaseBroadcasterEvent):
    chatter_user_id: str
    chatter_user_login: str
    chatter_user_name: str
    message_id: str
    message: ChatMessage
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


class ChatSubData(TypedDict):
    sub_tier: Literal["1000", "2000", "3000"]
    is_prime: bool
    duration_months: int


class ChatResubData(TypedDict):
    cumulative_months: int
    duration_months: int
    streak_months: int
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
    color: str


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
    message: ChatMessage
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


class ChannelChatMessageDeleteEvent(BaseBroadcasterEvent):
    target_user_id: str
    target_user_login: str
    target_user_user_name: str
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
    message: ChatMessage


class ChannelSubscribeEvent(BroadcasterUserEvent):
    tier: str
    is_gift: bool


class ChannelSubscriptionEndEvent(BroadcasterUserEvent):
    tier: str
    is_gift: bool


class ChannelSubscriptionGiftEvent(BroadcasterUserEvent):
    total: int
    tier: str
    cumulative_total: int | None
    is_anonymous: bool


class SubscribeEmoteData(TypedDict):
    begin: int
    end: int
    id: str


class SubscribeMessageData(TypedDict):
    text: str
    emotes: list[SubscribeEmoteData]


class ChannelSubscribeMessageEvent(BroadcasterUserEvent):
    total: int
    tier: str
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


class ChannelUnbanRequestResolveEvent(BroadcasterModUserEvent):
    id: str
    resolution_text: str
    status: Literal["approved", "canceled", "denied"]


class ChannelVIPAddEvent(BroadcasterUserEvent): ...


class GoalBeginProgressEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    description: str
    current_amount: int
    target_amount: int
    started_at: str


class GoalEndEvent(TypedDict):
    id: str
    broadcaster_user_id: str
    broadcaster_user_login: str
    broadcaster_user_name: str
    type: str
    description: str
    is_achieved: bool
    current_amount: int
    target_amount: int
    started_at: str
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
