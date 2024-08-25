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

from typing import TYPE_CHECKING, Any, ClassVar, Literal, NamedTuple

from twitchio.assets import Asset
from twitchio.eventsub import RevocationReason, TransportMethod
from twitchio.models.charity import CharityValues
from twitchio.models.chat import EmoteSet
from twitchio.user import PartialUser
from twitchio.utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.conduits import RevocationSubscription, RevocationTransport
    from twitchio.types_.eventsub import *


class BaseEvent:
    _registry: ClassVar[dict[str, type]] = {}
    subscription_type: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.subscription_type is not None:
            BaseEvent._registry[cls.subscription_type] = cls


def create_event_instance(event_type: str, payload: dict[str, Any], http: HTTPClient | None = None) -> Any:
    event_cls = BaseEvent._registry.get(event_type)
    if event_cls is None:
        raise ValueError(f"No class registered for event type {event_type}")
    return event_cls(payload) if http is None else event_cls(payload, http=http)


class AutomodEmote:
    __slots__ = ("set_id", "id", "text", "_http")

    def __init__(self, data: AutomodEmoteData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.set_id: str = data["set-id"]
        self.id: str = data["id"]
        self.text: str = data["text"]

    def __repr__(self) -> str:
        return f"<AutomodEmote set_id={self.set_id} id={self.id} text={self.text}>"

    async def fetch_emote_set(self, *, token_for: str | None = None) -> EmoteSet:
        data = await self._http.get_emote_sets(emote_set_ids=[self.set_id], token_for=token_for)
        return EmoteSet(data["data"][0], template=data["template"], http=self._http)


class AutomodCheermote:
    __slots__ = ("prefix", "amount", "text", "tier")

    def __init__(self, data: AutomodCheermoteData) -> None:
        self.text: str = data["text"]
        self.prefix: str = data["prefix"]
        self.amount: int = int(data["amount"])
        self.tier: int = int(data["tier"])

    def __repr__(self) -> str:
        return f"<AutomodCheermote prefix={self.prefix} amount={self.amount} text={self.text} tier={self.tier}>"


class AutomodMessageHold(BaseEvent):
    subscription_type = "automod.message.hold"

    __slots__ = ("broadcaster", "user", "message_id", "message", "level", "category", "held_at", "emotes", "cheermotes")

    def __init__(self, payload: AutomodMessageHoldEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http)
        self.user = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.message_id: str = payload["message_id"]
        self.message: str = payload["message"]
        self.level: int = int(payload["level"])
        self.category: str = payload["category"]
        self.held_at: datetime.datetime = parse_timestamp(payload["held_at"])
        self.emotes: list[AutomodEmote] = [AutomodEmote(e, http=http) for e in payload["fragments"]["emotes"]]
        self.cheermotes: list[AutomodCheermote] = [AutomodCheermote(e) for e in payload["fragments"]["cheermotes"]]

    def __repr__(self) -> str:
        return f"<AutomodMessageHold broadcaster={self.broadcaster} user={self.user} message_id={self.message_id} level={self.level}>"


class AutomodMessageUpdate(AutomodMessageHold):
    subscription_type = "automod.message.update"

    __slots__ = ("moderator", "status")

    def __init__(self, payload: AutomodMessageUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload=payload, http=http)
        self.moderator = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.status: Literal["Approved", "Denied", "Expired"] = payload["status"]

    def __repr__(self) -> str:
        return f"<AutomodMessageUpdate broadcaster={self.broadcaster} user={self.user} message_id={self.message_id} level={self.level}>"


class AutomodSettingsUpdate(BaseEvent):
    subscription_type = "automod.settings.update"

    __slots__ = (
        "broadcaster",
        "moderator",
        "overall_level",
        "disability",
        "aggression",
        "misogyny",
        "bullying",
        "swearing",
        "race_ethnicity_or_religion",
        "sex_based_terms",
    )

    def __init__(self, payload: AutomodSettingsUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http)
        self.moderator = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.overall_level: int | None = int(payload["overall_level"]) if payload["overall_level"] is not None else None
        self.disability: int = int(payload["disability"])
        self.aggression: int = int(payload["aggression"])
        self.misogyny: int = int(payload["misogyny"])
        self.bullying: int = int(payload["bullying"])
        self.swearing: int = int(payload["swearing"])
        self.race_ethnicity_or_religion: int = int(payload["race_ethnicity_or_religion"])
        self.sex_based_terms: int = int(payload["sex_based_terms"])

    def __repr__(self) -> str:
        return f"<AutomodSettingsUpdate broadcaster={self.broadcaster} moderator={self.moderator} overall_level={self.overall_level}>"


class AutomodTermsUpdate(BaseEvent):
    subscription_type = "automod.terms.update"

    __slots__ = ("broadcaster", "moderator", "action", "automod", "terms")

    def __init__(self, payload: AutomodTermsUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http)
        self.moderator = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.action: Literal["add_permitted", "remove_permitted", "add_blocked", "remove_blocked"] = payload["action"]
        self.automod: bool = bool(payload["from_automod"])
        self.terms: list[str] = payload["terms"]

    def __repr__(self) -> str:
        return f"<AutomodTermsUpdate broadcaster={self.broadcaster} moderator={self.moderator} action={self.action} automod={self.automod}>"


class ChannelUpdate(BaseEvent):
    subscription_type = "channel.update"

    __slots__ = ("broadcaster", "title", "category_id", "category_name", "content_classification_labels")

    def __init__(self, payload: ChannelUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http)
        self.title = payload["title"]
        self.language = payload["language"]
        self.category_id = payload["category_id"]
        self.category_name = payload["category_name"]
        self.content_classification_labels = payload["content_classification_labels"]

    def __repr__(self) -> str:
        return f"<ChannelUpdate title={self.title} language={self.language} category_id={self.category_id} category_name={self.category_name}>"


class ChannelFollow(BaseEvent):
    subscription_type = "channel.follow"

    __slots__ = ("broadcaster", "user", "followed_at")

    def __init__(self, payload: ChannelFollowEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.followed_at: datetime.datetime = parse_timestamp(payload["followed_at"])

    def __repr__(self) -> str:
        return f"<ChannelFollow broadcaster={self.broadcaster} user={self.user} followed_at={self.followed_at}>"


class ChannelAdBreakBegin(BaseEvent):
    subscription_type = "channel.ad_break.begin"

    __slots__ = ("broadcaster", "requester", "duration", "automatic", "started_at")

    def __init__(self, payload: ChannelAdBreakBeginEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.requester: PartialUser = PartialUser(payload["requester_user_id"], payload["requester_user_login"], http=http)
        self.duration: int = int(payload["duration_seconds"])
        self.automatic: bool = bool(payload["is_automatic"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return (
            f"<ChannelAdBreakBegin broadcaster={self.broadcaster} requester={self.requester} started_at={self.started_at}>"
        )


class ChannelChatClear(BaseEvent):
    subscription_type = "channel.chat.clear"

    __slots__ = ("broadcaster",)

    def __init__(self, payload: ChannelChatClearEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChannelChatClear broadcaster={self.broadcaster}>"


class ChannelChatClearUserMessages(BaseEvent):
    subscription_type = "channel.chat.clear_user_messages"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelChatClearUserMessagesEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["target_user_id"], payload["target_user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelChatClearUserMessages broadcaster={self.broadcaster} user={self.user}>"


class ChatMessageReply:
    __slots__ = (
        "parent_message_id",
        "parent_message_body",
        "parent_user_id",
        "parent_user_name",
        "parent_user_login",
        "thread_message_id",
        "thread_user_id",
        "thread_user_name",
        "thread_user_login",
    )

    def __init__(self, data: ChatMessageReplyData) -> None:
        self.parent_message_id: str = data["parent_message_id"]
        self.parent_message_body: str = data["parent_message_body"]
        self.parent_user_id: str = data["parent_user_id"]
        self.parent_user_name: str = data["parent_user_name"]
        self.parent_user_login: str = data["parent_user_login"]
        self.thread_message_id: str = data["thread_message_id"]
        self.thread_user_id: str = data["thread_user_id"]
        self.thread_user_name: str = data["thread_user_name"]
        self.thread_user_login: str = data["thread_user_login"]

    def __repr__(self) -> str:
        return f"<ChatMessageReply parent_message_id={self.parent_message_id} parent_user_id={self.parent_user_id}>"


class ChatMessageCheer:
    __slots__ = ("bits",)

    def __init__(self, data: ChatMessageCheerData) -> None:
        self.bits: int = int(data["bits"])

    def __repr__(self) -> str:
        return f"<ChatMessageCheer bits={self.bits}>"


class ChatMessageBadge:
    __slots__ = ("set_id", "id", "info")

    def __init__(self, data: ChatMessageBadgeData) -> None:
        self.set_id: str = data["set_id"]
        self.id: str = data["id"]
        self.info: str = data["info"]

    def __repr__(self) -> str:
        return f"<ChatMessageBadge set_id={self.set_id} id={self.id} info={self.info}>"


class ChatMessageEmote:
    __slots__ = ("set_id", "id", "owner_id", "format", "_http")

    def __init__(self, data: ChatMessageEmoteData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.set_id: str = data["emote_set_id"]
        self.id: str = data["id"]
        self.owner_id: str | None = data.get("owner_id")
        self.format: list[Literal["static", "animated"]] = data.get("format", [])

    def __repr__(self) -> str:
        return f"<ChatMessageEmote set_id={self.set_id} id={self.id} owner_id={self.owner_id} format={self.format}>"

    async def fetch_emote_set(self, *, token_for: str | None = None) -> EmoteSet:
        data = await self._http.get_emote_sets(emote_set_ids=[self.set_id], token_for=token_for)
        return EmoteSet(data["data"][0], template=data["template"], http=self._http)


class ChatMessageCheermote:
    __slots__ = ("prefix", "bits", "tier")

    def __init__(self, data: ChatMessageCheermoteData) -> None:
        self.prefix: str = data["prefix"]
        self.bits: int = int(data["bits"])
        self.tier: int = int(data["tier"])

    def __repr__(self) -> str:
        return f"<ChatMessageCheermote prefix={self.prefix} bits={self.bits} tier={self.tier}>"


class ChatMessageFragment:
    __slots__ = ("text", "type", "cheermote", "emote", "mention")

    def __init__(self, data: ChatMessageFragmentsData, *, http: HTTPClient) -> None:
        self.text = data["text"]
        self.type: Literal["text", "cheermote", "emote", "mention"] = data["type"]
        user = data.get("mention")
        self.mention: PartialUser | None = (
            PartialUser(user["user_id"], user["user_login"], http=http) if user is not None else None
        )
        self.cheermote: ChatMessageCheermote | None = (
            ChatMessageCheermote(data["cheermote"]) if data["cheermote"] is not None else None
        )
        self.emote: ChatMessageEmote | None = ChatMessageEmote(data["emote"], http=http) if data["emote"] else None

    def __repr__(self) -> str:
        return f"<ChatMessageFragment type={self.type} text={self.text}>"


class BaseChatMessage(BaseEvent):
    __slots__ = (
        "broadcaster",
        "text",
        "fragments",
        "id",
    )

    def __init__(
        self, payload: ChannelChatMessageEvent | ChatUserMessageHoldEvent | ChatUserMessageUpdateEvent, *, http: HTTPClient
    ) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.text: str = payload["message"]["text"]
        self.id: str = payload["message_id"]
        self.fragments: list[ChatMessageFragment] = [
            ChatMessageFragment(fragment, http=http) for fragment in payload["message"]["fragments"]
        ]

    @property
    def emotes(self) -> list[ChatMessageEmote]:
        return [f.emote for f in self.fragments if f.emote is not None]

    @property
    def cheermotes(self) -> list[ChatMessageCheermote]:
        return [f.cheermote for f in self.fragments if f.cheermote is not None]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} broadcaster={self.broadcaster} id={self.id} text={self.text}>"


class ChatMessage(BaseChatMessage):
    subscription_type = "channel.chat.message"

    __slots__ = (
        "chatter",
        "colour",
        "badges",
        "message_type",
        "cheer",
        "reply",
        "channel_points_id",
        "channel_points_animation_id",
    )

    def __init__(self, payload: ChannelChatMessageEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.chatter: PartialUser = PartialUser(payload["chatter_user_id"], payload["chatter_user_login"], http=http)
        self.colour: Colour | None = Colour.from_hex(payload["color"]) if payload["color"] else None
        self.channel_points_id: str | None = payload["channel_points_custom_reward_id"]
        self.channel_points_animation_id: str | None = payload["channel_points_animation_id"]
        self.reply: ChatMessageReply | None = ChatMessageReply(payload["reply"]) if payload["reply"] is not None else None
        self.message_type: Literal[
            "text",
            "channel_points_highlighted",
            "channel_points_sub_only",
            "user_intro",
            "power_ups_message_effect",
            "power_ups_gigantified_emote",
        ] = payload["message_type"]

        self.cheer: ChatMessageCheer | None = ChatMessageCheer(payload["cheer"]) if payload["cheer"] is not None else None
        self.badges: list[ChatMessageBadge] = [ChatMessageBadge(badge) for badge in payload["badges"]]

    @property
    def mentions(self) -> list[PartialUser]:
        return [f.mention for f in self.fragments if f.mention is not None]

    @property
    def color(self) -> Colour | None:
        return self.colour

    def __repr__(self) -> str:
        return f"<ChatMessage broadcaster={self.broadcaster} chatter={self.chatter} id={self.id} text={self.text}>"


class ChatSub:
    __slots__ = ("tier", "prime", "duration_months")

    def __init__(self, data: ChatSubData) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.prime: bool = bool(data["is_prime"])
        self.duration_months: int = int(data["duration_months"])

    def __repr__(self) -> str:
        return f"<ChatSub tier={self.tier} prime={self.prime} duration_months={self.duration_months}>"


class ChatResub:
    __slots__ = (
        "tier",
        "prime",
        "duration",
        "cumulative_months",
        "streak_months",
        "gift",
        "anonymous",
        "gifter",
    )

    def __init__(self, data: ChatResubData, *, http: HTTPClient) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.prime: bool = bool(data["is_prime"])
        self.gift: bool = bool(data["is_gift"])
        self.duration: int = int(data["duration_months"])
        self.cumulative_months: int = int(data["cumulative_months"])
        self.streak_months: int = int(data["streak_months"])
        self.anonymous: bool | None = (
            bool(data["gifter_is_anonymous"]) if data.get("gifter_is_anonymous") is not None else None
        )
        gifter = data.get("gifter_user_id")
        self.gifter: PartialUser | None = (
            PartialUser(str(data["gifter_user_id"]), data["gifter_user_login"], http=http) if gifter is not None else None
        )

    def __repr__(self) -> str:
        return f"<ChatResub tier={self.tier} prime={self.prime} duration={self.duration}>"


class ChatSubGift:
    __slots__ = ("duration", "tier", "cumulative_total", "recipient", "community_gift_id")

    def __init__(self, data: ChatSubGiftData, *, http: HTTPClient) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.duration: int = int(data["duration_months"])
        self.cumulative_total: int | None = int(data["cumulative_total"]) if data["cumulative_total"] is not None else None
        self.community_gift_id: str | None = data.get("community_gift_id")
        self.recipient: PartialUser = PartialUser(data["recipient_user_id"], data["recipient_user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChatSubGift tier={self.tier} duration={self.duration} recipient={self.recipient}>"


class ChatCommunitySubGift:
    __slots__ = ("total", "tier", "cumulative_total", "id")

    def __init__(self, data: ChatCommunitySubGiftData) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.total: int = int(data["total"])
        self.cumulative_total: int | None = int(data["cumulative_total"]) if data["cumulative_total"] is not None else None
        self.id: str | None = data.get("community_gift_id")

    def __repr__(self) -> str:
        return f"<ChatCommunitySubGift id={self.id} tier={self.tier} total={self.total}>"


class ChatGiftPaidUpgrade:
    __slots__ = ("anonymous", "gifter")

    def __init__(self, data: ChatGiftPaidUpgradeData, *, http: HTTPClient) -> None:
        self.anonymous: bool = bool(data["gifter_is_anonymous"])
        gifter = data.get("gifter_user_id")
        self.gifter: PartialUser | None = (
            PartialUser(str(data["gifter_user_id"]), data["gifter_user_login"], http=http) if gifter is not None else None
        )

    def __repr__(self) -> str:
        return f"<ChatGiftPaidUpgrade anonymous={self.anonymous} gifter={self.gifter}>"


class ChatPrimePaidUpgrade:
    __slots__ = ("tier",)

    def __init__(self, data: ChatPrimePaidUpgradeData) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]

    def __repr__(self) -> str:
        return f"<ChatPrimePaidUpgrade tier={self.tier}>"


class ChatRaid:
    __slots__ = ("user", "viewer_count", "profile_image")

    def __init__(self, data: ChatRaidData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.viewer_count = int(data["viewer_count"])
        self.profile_image: Asset = Asset(data["profile_image_url"], http=http)

    def __repr__(self) -> str:
        return f"<ChatRaid user={self.user} viewer_count={self.viewer_count}>"


class ChatPayItForward:
    __slots__ = ("anonymous", "gifter")

    def __init__(self, data: ChatPayItForwardData, *, http: HTTPClient) -> None:
        self.anonymous: bool = bool(data["gifter_is_anonymous"])
        gifter = data.get("gifter_user_id")
        self.gifter: PartialUser | None = (
            PartialUser(str(data["gifter_user_id"]), data["gifter_user_login"], http=http) if gifter is not None else None
        )

    def __repr__(self) -> str:
        return f"<ChatPayItForward anonymous={self.anonymous} gifter={self.gifter}>"


class ChatAnnouncement:
    __slots__ = ("colour",)

    def __init__(self, data: ChatAnnouncementData) -> None:
        self.colour: Literal["BLUE", "PURPLE", "ORANGE", "GREEN", "PRIMARY"] = data["color"]

    @property
    def color(self) -> Literal["BLUE", "PURPLE", "ORANGE", "GREEN", "PRIMARY"]:
        return self.colour

    def __repr__(self) -> str:
        return f"<ChatAnnouncement colour={self.colour}>"


class ChatBitsBadgeTier:
    __slots__ = ("tier",)

    def __init__(self, data: ChatBitsBadgeTierData) -> None:
        self.tier: int = int(data["tier"])

    def __repr__(self) -> str:
        return f"<ChatBitsBadgeTier tier={self.tier}>"


class ChatCharityValues:
    __slots__ = ("value", "decimal_place", "currency")

    def __init__(self, data: ChatCharityAmountData) -> None:
        self.value: int = int(data["value"])
        self.decimal_place: int = int(data["decimal_place"])
        self.currency: str = data["currency"]

    def __repr__(self) -> str:
        return f"<ChatCharityValues value={self.value} decimal_place={self.decimal_place} currency={self.currency}>"


class ChatCharityDonation:
    __slots__ = ("name", "amount")

    def __init__(self, data: ChatCharityDonationData) -> None:
        self.name: str = data["charity_name"]
        self.amount: ChatCharityValues = ChatCharityValues(data["amount"])

    def __repr__(self) -> str:
        return f"<ChatCharityDonation name={self.name}>"


class ChatNotification(BaseEvent):
    subscription_type = "channel.chat.notification"

    __slots__ = (
        "broadcaster",
        "chatter",
        "anonymous",
        "colour",
        "badges",
        "system_message",
        "id",
        "text",
        "fragments",
        "notice_type",
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
    )

    def __init__(self, payload: ChannelChatNotificationEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.chatter: PartialUser = PartialUser(payload["chatter_user_id"], payload["chatter_user_login"], http=http)
        self.anonymous: bool = bool(payload["chatter_is_anonymous"])
        self.colour: Colour | None = Colour.from_hex(payload["color"]) if payload["color"] else None
        self.badges: list[ChatMessageBadge] = [ChatMessageBadge(badge) for badge in payload["badges"]]
        self.system_message: str = payload["system_message"]
        self.id: str = payload["message_id"]
        self.text: str = payload["message"]["text"]
        self.fragments: list[ChatMessageFragment] = [
            ChatMessageFragment(fragment, http=http) for fragment in payload["message"]["fragments"]
        ]
        self.sub: ChatSub | None = ChatSub(payload["sub"]) if payload["sub"] is not None else None
        self.resub: ChatResub | None = ChatResub(payload["resub"], http=http) if payload["resub"] is not None else None
        self.sub_gift: ChatSubGift | None = (
            ChatSubGift(payload["sub_gift"], http=http) if payload["sub_gift"] is not None else None
        )
        self.community_sub_gift: ChatCommunitySubGift | None = (
            ChatCommunitySubGift(payload["community_sub_gift"]) if payload["community_sub_gift"] is not None else None
        )
        self.gift_paid_upgrade: ChatGiftPaidUpgrade | None = (
            ChatGiftPaidUpgrade(payload["gift_paid_upgrade"], http=http)
            if payload["gift_paid_upgrade"] is not None
            else None
        )
        self.prime_paid_upgrade: ChatPrimePaidUpgrade | None = (
            ChatPrimePaidUpgrade(payload["prime_paid_upgrade"]) if payload["prime_paid_upgrade"] is not None else None
        )
        self.raid: ChatRaid | None = ChatRaid(payload["raid"], http=http) if payload["raid"] is not None else None
        self.unraid: None  # TODO This returns an empty payload otherwise None so just make it None?
        self.pay_it_forward: ChatPayItForward | None = (
            ChatPayItForward(payload["pay_it_forward"], http=http) if payload["pay_it_forward"] is not None else None
        )
        self.announcement: ChatAnnouncement | None = (
            ChatAnnouncement(payload["announcement"]) if payload["announcement"] is not None else None
        )
        self.bits_badge_tier: ChatBitsBadgeTier | None = (
            ChatBitsBadgeTier(payload["bits_badge_tier"]) if payload["bits_badge_tier"] is not None else None
        )
        self.charity_donation: ChatCharityDonation | None = (
            ChatCharityDonation(payload["charity_donation"]) if payload["charity_donation"] is not None else None
        )
        self.notice_type: Literal[
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
        ] = payload["notice_type"]

    @property
    def color(self) -> Colour | None:
        return self.colour

    def __repr__(self) -> str:
        return f"<ChatNotification broadcaster={self.broadcaster} chatter={self.chatter} id={self.id} text={self.text}>"


class ChatMessageDelete(BaseEvent):
    subscription_type = "channel.chat.message_delete"

    __slots__ = ("broadcaster", "user", "message_id")

    def __init__(self, payload: ChannelChatMessageDeleteEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["target_user_id"], payload["target_user_login"], http=http)
        self.message_id: str = payload["message_id"]

    def __repr__(self) -> str:
        return f"<ChatMessageDelete broadcaster={self.broadcaster} user={self.user} message_id={self.message_id}>"


class ChatSettingsUpdate(BaseEvent):
    subscription_type = "channel.chat_settings.update"

    __slots__ = (
        "broadcaster",
        "emote_mode",
        "follower_mode",
        "follower_mode_duration",
        "slow_mode",
        "slow_mode_wait_time",
        "subscriber_mode",
        "unique_chat_mode",
    )

    def __init__(self, payload: ChannelChatSettingsUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.emote_mode: bool = bool(payload["emote_mode"])
        self.follower_mode: bool = bool(payload["follower_mode"])
        self.slow_mode: bool = bool(payload["slow_mode"])
        self.subscriber_mode: bool = bool(payload["subscriber_mode"])
        self.unique_chat_mode: bool = bool(payload["unique_chat_mode"])
        self.slow_mode_wait_time: int | None = payload.get("slow_mode_wait_time_seconds")
        self.follower_mode_duration: int | None = payload.get("follower_mode_duration_minutes")

    def __repr__(self) -> str:
        return f"<ChatSettingsUpdate broadcaster={self.broadcaster} slow_mode={self.slow_mode} follower_mode={self.follower_mode} subscriber_mode={self.subscriber_mode} unique_chat_mode={self.unique_chat_mode}>"


class ChatUserMessageHold(BaseChatMessage):
    subscription_type = "channel.chat.user_message_hold"

    # TODO text is the caught text. Maybe we shouldn't inherit here after all.

    __slots__ = ("user",)

    def __init__(self, payload: ChatUserMessageHoldEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChatUserMessageHold broadcaster={self.broadcaster} user={self.user} id={self.id} text={self.text}>"

    @property
    def full_message(self) -> str:
        return " ".join(fragment.text for fragment in self.fragments if fragment.type == "text")


class ChatUserMessageUpdate(BaseChatMessage):
    subscription_type = "channel.chat.user_message_update"

    # TODO text is the caught text. Maybe we shouldn't inherit here after all.

    __slots__ = ("user", "status")

    def __init__(self, payload: ChatUserMessageUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.status: Literal["approved", "denied", "invalid"] = payload["status"]

    def __repr__(self) -> str:
        return f"<ChatUserMessageUpdate broadcaster={self.broadcaster} user={self.user} id={self.id} text={self.text}>"

    @property
    def full_message(self) -> str:
        return " ".join(fragment.text for fragment in self.fragments if fragment.type == "text")


class ChannelSubscribe(BaseEvent):
    subscription_type = "channel.subscribe"

    __slots__ = (
        "broadcaster",
        "user",
        "tier",
        "gift",
    )

    def __init__(self, payload: ChannelSubscribeEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.gift: bool = bool(payload["is_gift"])

    def __repr__(self) -> str:
        return f"<ChannelSubscribe broadcaster={self.broadcaster} user={self.user} tier={self.tier} gift={self.gift}>"


class ChannelSubscriptionEnd(BaseEvent):
    subscription_type = "channel.subscribe.end"

    __slots__ = (
        "broadcaster",
        "user",
        "tier",
        "gift",
    )

    def __init__(self, payload: ChannelSubscriptionEndEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.gift: bool = bool(payload["is_gift"])

    def __repr__(self) -> str:
        return f"<ChannelSubscriptionEnd broadcaster={self.broadcaster} user={self.user} tier={self.tier} gift={self.gift}>"


class ChannelSubscriptionGift(BaseEvent):
    subscription_type = "channel.subscribe.gift"

    __slots__ = ("broadcaster", "user", "tier", "total", "cumulative_total", "anonymous")

    def __init__(self, payload: ChannelSubscriptionGiftEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.total: int = int(payload["total"])
        self.anonymous: bool = bool(payload["is_anonymous"])
        cumulative_total = payload.get("cumulative_total")
        self.cumulative_total: int | None = int(cumulative_total) if cumulative_total is not None else None

    def __repr__(self) -> str:
        return (
            f"<ChannelSubscriptionGift broadcaster={self.broadcaster} user={self.user} tier={self.tier} total={self.total}>"
        )


class BaseEmote:
    def __init__(self, data: BaseEmoteData) -> None:
        self.begin: int = int(data["begin"])
        self.end: int = int(data["end"])
        self.id: str = data["id"]

    def __repr__(self) -> str:
        return f"<BaseEmote id={self.id} begin={self.id} end={self.end}>"


class SubscribeEmote(BaseEmote):
    def __init__(self, data: SubscribeEmoteData) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<SubscribeEmote id={self.id} begin={self.id} end={self.end}>"


class ChannelSubscriptionMessage(BaseEvent):
    subscription_type = "channel.subscribe.message"

    __slots__ = ("broadcaster", "user", "tier", "message", "cumulative_months", "streak_months", "duration")

    def __init__(self, payload: ChannelSubscribeMessageEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.tier: str = payload["tier"]
        self.duration_months: int = int(payload["duration_months"])
        self.cumulative_months: int = int(payload["cumulative_months"])
        self.streak_months: int | None = int(payload["streak_months"]) if payload["streak_months"] is not None else None
        self.text: str = payload["message"]["text"]
        self.emotes: list[SubscribeEmote] = [SubscribeEmote(emote) for emote in payload["message"]["emotes"]]

    def __repr__(self) -> str:
        return f"<ChannelSubscriptionMessage broadcaster={self.broadcaster} user={self.user} text={self.text}>"


class ChannelCheer(BaseEvent):
    subscription_type = "channel.cheer"

    __slots__ = ("broadcaster", "user", "anonymous", "message", "bits")

    def __init__(self, payload: ChannelCheerEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.anonymous: bool = bool(payload["is_anonymous"])
        self.bits: int = int(payload["bits"])
        self.message: str = payload["message"]
        self.user: PartialUser | None = (
            PartialUser(payload["user_id"], payload["user_login"], http=http) if payload["user_id"] is not None else None
        )

    def __repr__(self) -> str:
        return f"<ChannelCheer broadcaster={self.broadcaster} user={self.user} bits={self.bits} message={self.message}>"


class ChannelRaid(BaseEvent):
    subscription_type = "channel.raid"

    __slots__ = ("from_broadcaster", "to_boradcaster", "viewer_count")

    def __init__(self, payload: ChannelRaidEvent, *, http: HTTPClient) -> None:
        self.from_broadcaster: PartialUser = PartialUser(
            payload["from_broadcaster_user_id"], payload["from_broadcaster_user_login"], http=http
        )
        self.to_broadcaster: PartialUser = PartialUser(
            payload["to_broadcaster_user_id"], payload["to_broadcaster_user_login"], http=http
        )
        self.viewer_count: int = int(payload["viewers"])

    def __repr__(self) -> str:
        return f"<ChannelRaid from_broadcaster={self.from_broadcaster} to_broadcaster={self.to_broadcaster} viewer_count={self.viewer_count}>"


class ChannelBan(BaseEvent):
    subscription_type = "channel.ban"

    __slots__ = ("broadcaster", "user", "moderator", "reason", "banned_at", "ends_at", "permanent")

    def __init__(self, payload: ChannelBanEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.reason: str = payload["reason"]
        self.banned_at: datetime.datetime = parse_timestamp(payload["banned_at"])
        self.ends_at: datetime.datetime | None = (
            parse_timestamp(payload["ends_at"]) if payload["ends_at"] is not None else None
        )
        self.permanent: bool = bool(payload["is_permanent"])

    def __repr__(self) -> str:
        return f"<ChannelBan broadcaster={self.broadcaster} user={self.user} moderator={self.moderator} banned_at={self.banned_at}>"


class ChannelUnban(BaseEvent):
    subscription_type = "channel.unban"

    __slots__ = ("broadcaster", "user", "moderator")

    def __init__(self, payload: ChannelUnbanEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelUnban broadcaster={self.broadcaster} user={self.user} moderator={self.moderator}>"


class ChannelUnbanRequest(BaseEvent):
    subscription_type = "channel.unban_request.create"

    __slots__ = ("broadcaster", "user", "id", "text", "created_at")

    def __init__(self, payload: ChannelUnbanRequestEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.id: str = payload["id"]
        self.text: str = payload["text"]
        self.created_at: datetime.datetime = parse_timestamp(payload["created_at"])

    def __repr__(self) -> str:
        return f"<ChannelUnbanRequest broadcaster={self.broadcaster} user={self.user} id={self.id}>"


class ChannelUnbanRequestResolve(BaseEvent):
    subscription_type = "channel.unban_request.resolve"

    __slots__ = ("broadcaster", "user", "id", "resolution_text", "status")

    def __init__(self, payload: ChannelUnbanRequestResolveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.id: str = payload["id"]
        self.resolution_text: str = payload["resolution_text"]
        self.status: Literal["approved", "canceled", "denied"] = payload["status"]

    def __repr__(self) -> str:
        return (
            f"<ChannelUnbanRequestResolve broadcaster={self.broadcaster} user={self.user} id={self.id} status={self.status}>"
        )


class ModerateFollowers:
    __slots__ = ("follow_duration",)

    def __init__(self, data: ModerateFollowersData) -> None:
        self.follow_duration: int = int(data["follow_duration_minutes"])

    def __repr__(self) -> str:
        return f"<ModerateFollowers follow_duration={self.follow_duration}>"


class ModerateBan:
    __slots__ = ("user", "reason")

    def __init__(self, data: ModerateBanData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.reason: str | None = data.get("reason")

    def __repr__(self) -> str:
        return f"<ModerateBan user={self.user} reason={self.reason}>"


class ModerateTimeout:
    __slots__ = ("user", "reason", "expires_at")

    def __init__(self, data: ModerateTimeoutData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.reason: str | None = data.get("reason")
        self.expires_at: datetime.datetime = parse_timestamp(data["expires_at"])

    def __repr__(self) -> str:
        return f"<ModerateTimeout user={self.user} expires_at={self.expires_at}>"


class ModerateSlow:
    __slots__ = ("wait_time",)

    def __init__(self, data: ModerateSlowData) -> None:
        self.wait_time: int = int(data["wait_time_seconds"])

    def __repr__(self) -> str:
        return f"<ModerateSlow wait_time={self.wait_time}>"


class ModerateRaid:
    __slots__ = ("user", "viewer_count")

    def __init__(self, data: ModerateRaidData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.viewer_count: int = int(data["viewer_count"])

    def __repr__(self) -> str:
        return f"<ModerateRaid user={self.user} viewer_count={self.viewer_count}>"


class ModerateDelete:
    __slots__ = ("user", "message_id", "message")

    def __init__(self, data: ModerateDeleteData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.message_id: str = data["message_id"]
        self.message: str = data["message_body"]

    def __repr__(self) -> str:
        return f"<ModerateDelete user={self.user} message_id={self.message_id} message={self.message}>"


class ModerateAutomodTerms:
    __slots__ = ("action", "list", "terms", "from_automod")

    def __init__(self, data: ModerateAutoModTermsData) -> None:
        self.action: Literal["add", "remove"] = data["action"]
        self.list: Literal["blocked", "permitted"] = data["list"]
        self.terms: list[str] = data["terms"]
        self.from_automod: bool = bool(data["from_automod"])

    def __repr__(self) -> str:
        return f"<ModerateAutomodTerms action={self.action} list={self.list} terms={self.terms} from_automod={self.from_automod}>"


class ModerateUnbanRequest:
    __slots__ = ("approved", "user", "message")

    def __init__(self, data: ModerateUnbanRequestData, *, http: HTTPClient) -> None:
        self.approved: bool = bool(data["is_approved"])
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.message: str = data["moderator_message"]

    def __repr__(self) -> str:
        return f"<ModerateUnbanRequest approved={self.approved} user={self.user} message={self.message}>"


class ModerateWarn:
    __slots__ = ("user", "reason", "chat_rules")

    def __init__(self, data: ModerateWarnData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.reason: str | None = data.get("reason")
        self.chat_rules: list[str] | None = data.get("chat_rules_cited")

    def __repr__(self) -> str:
        return f"<ModerateWarn user={self.user} reason={self.reason} chat_rules={self.chat_rules}>"


class ChannelModerate(BaseEvent):
    subscription_type = "channel.moderate"

    __slots__ = (
        "broadcaster",
        "moderator",
        "action",
        "followers",
        "slow",
        "vip",
        "unvip",
        "mod",
        "unmod",
        "ban",
        "unban",
        "timeout",
        "untimeout",
        "raid",
        "unraid",
        "delete",
        "automod_terms",
        "unban_request",
    )

    def __init__(self, payload: ChannelModerateEvent | ChannelModerateEventV2, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.followers: ModerateFollowers | None = (
            ModerateFollowers(payload["followers"]) if payload["followers"] is not None else None
        )
        self.slow: ModerateSlow | None = ModerateSlow(payload["slow"]) if payload["slow"] is not None else None
        self.vip: PartialUser | None = (
            PartialUser(payload["vip"]["user_id"], payload["vip"]["user_login"], http=http)
            if payload["vip"] is not None
            else None
        )
        self.unvip: PartialUser | None = (
            PartialUser(payload["unvip"]["user_id"], payload["unvip"]["user_login"], http=http)
            if payload["unvip"] is not None
            else None
        )
        self.mod: PartialUser | None = (
            PartialUser(payload["mod"]["user_id"], payload["mod"]["user_login"], http=http)
            if payload["mod"] is not None
            else None
        )
        self.unmod: PartialUser | None = (
            PartialUser(payload["unmod"]["user_id"], payload["unmod"]["user_login"], http=http)
            if payload["unmod"] is not None
            else None
        )
        self.ban: ModerateBan | None = ModerateBan(payload["ban"], http=http) if payload["ban"] is not None else None
        self.unban: PartialUser | None = (
            PartialUser(payload["unban"]["user_id"], payload["unban"]["user_login"], http=http)
            if payload["unban"] is not None
            else None
        )
        self.timeout: ModerateTimeout | None = (
            ModerateTimeout(payload["timeout"], http=http) if payload["timeout"] is not None else None
        )
        self.untimeout: PartialUser | None = (
            PartialUser(payload["untimeout"]["user_id"], payload["untimeout"]["user_login"], http=http)
            if payload["untimeout"] is not None
            else None
        )
        self.raid: ModerateRaid | None = ModerateRaid(payload["raid"], http=http) if payload["raid"] is not None else None
        self.unraid: PartialUser | None = (
            PartialUser(payload["unraid"]["user_id"], payload["unraid"]["user_login"], http=http)
            if payload["unraid"] is not None
            else None
        )
        self.delete: ModerateDelete | None = ModerateDelete(payload["delete"], http=http) if payload["delete"] else None
        self.automod_terms: ModerateAutomodTerms | None = (
            ModerateAutomodTerms(payload["automod_terms"]) if payload["automod_terms"] is not None else None
        )
        self.unban_request: ModerateUnbanRequest | None = (
            ModerateUnbanRequest(payload["unban_request"], http=http) if payload["unban_request"] is not None else None
        )
        self.action: Literal[
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
        ] = payload["action"]
        warn = payload.get("warn")
        self.warn: ModerateWarn | None = ModerateWarn(warn, http=http) if warn is not None else None


class ChannelModeratorAdd(BaseEvent):
    subscription_type = "channel.moderator.add"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelModeratorAddEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelModeratorAdd broadcaster={self.broadcaster} user={self.user}>"


class ChannelModeratorRemove(BaseEvent):
    subscription_type = "channel.moderator.remove"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelModeratorRemoveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelModeratorRemove broadcaster={self.broadcaster} user={self.user}>"


class ChannelPointsEmote(BaseEmote):
    def __init__(self, data: ChannelPointsEmoteData) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<ChannelPointsEmote id={self.id} begin={self.id} end={self.end}>"


class ChannelPointsAutoRedeemAdd(BaseEvent):
    subscription_type = "channel.channel_points_automatic_reward_redemption.add"

    __slots__ = ("broadcaster", "user", "id", "reward", "text", "emotes", "user_input", "redeemed_at")

    def __init__(self, payload: ChannelPointsAutoRewardRedemptionEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.id: str = payload["id"]
        self.text: str = payload["message"]["text"]
        self.emotes: list[ChannelPointsEmote] = [ChannelPointsEmote(emote) for emote in payload["message"]["emotes"]]
        self.user_input: str | None = payload.get("user_input")
        self.redeemed_attributes: datetime.datetime = parse_timestamp(payload["redeemed_at"])

    def __repr__(self) -> str:
        return f"<ChannelPointsAutoRedeemAdd broadcaster={self.broadcaster} user={self.user} id={self.id}>"


class RewardLimitSettings(NamedTuple):
    """
    NamedTuple that represents a custom reward's stream limit settings.

    Attributes
    -----------
    enabled: bool
        Whether the stream setting is enabled or not.
    value: int
        The value of the limit setting.
    """

    enabled: bool
    value: int


class CooldownSettings(NamedTuple):
    """
    NamedTuple that represents a custom reward's cooldown settings.

    Attributes
    -----------
    enabled: bool
        Whether the stream setting is enabled or not.
    seconds: int
        The cooldown in seconds.
    """

    enabled: bool
    seconds: int


class ChannelPointsRewardAdd(BaseEvent):
    subscription_type = "channel.channel_points_custom_reward.add"

    __slots__ = (
        "_http",
        "broadcaster",
        "id",
        "enabled",
        "paused",
        "in_stock",
        "title",
        "cost",
        "prompt",
        "input_required",
        "skip_queue",
        "cooldown_until",
        "colour",
        "max_per_stream",
        "max_per_user_per_stream",
        "_image",
        "default_image",
        "current_stream_redeems",
    )

    def __init__(self, payload: ChannelPointsCustomRewardAddEvent, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=self._http
        )
        self.id: str = payload["id"]
        self.title: str = payload["title"]
        self.cost: int = int(payload["cost"])
        self.prompt: str = payload["prompt"]
        self.enabled: bool = bool(payload["is_enabled"])
        self.paused: bool = bool(payload["is_paused"])
        self.in_stock: bool = bool(payload["is_in_stock"])
        self.input_required: bool = bool(payload["is_user_input_required"])
        self.skip_queue: bool = bool(payload["should_redemptions_skip_request_queue"])
        self.colour: Colour | None = Colour.from_hex(payload["background_color"])
        self.cooldown_until: datetime.datetime | None = (
            parse_timestamp(payload["cooldown_expires_at"]) if payload["cooldown_expires_at"] is not None else None
        )
        self.max_per_stream: RewardLimitSettings = RewardLimitSettings(
            enabled=payload["max_per_stream"]["is_enabled"], value=payload["max_per_stream"]["value"]
        )
        self.max_per_user_per_stream: RewardLimitSettings = RewardLimitSettings(
            enabled=payload["max_per_user_per_stream"]["is_enabled"], value=int(payload["max_per_user_per_stream"]["value"])
        )
        self.global_cooldown: CooldownSettings = CooldownSettings(
            enabled=payload["global_cooldown"]["is_enabled"], seconds=int(payload["global_cooldown"]["seconds"])
        )
        self.default_image: dict[str, str] = {k: str(v) for k, v in payload["default_image"].items()}
        self.current_stream_redeems: int | None = (
            int(payload["redemptions_redeemed_current_stream"])
            if payload["redemptions_redeemed_current_stream"] is not None
            else None
        )
        self._image: ChannelPointsImageData | None = payload.get("image")

    def __repr__(self) -> str:
        return f"<ChannelPointsRewardAdd broadcaster={self.broadcaster} id={self.id} title={self.title} cost={self.cost} enabled={self.enabled}>"

    @property
    def color(self) -> Colour | None:
        return self.colour

    @property
    def image(self) -> dict[str, str] | None:
        if self._image is not None:
            return {k: str(v) for k, v in self._image.items()}
        else:
            return None

    def get_image(self, size: Literal["1x", "2x", "4x"] = "2x", use_default: bool = False) -> Asset:
        """
        Get an image Asset for the reward at a specified size.
        Falls back to default images if no custom images have been uploaded.

        Parameters
        ----------
        size : str
            The size key of the image. Options are "1x", "2x", "4x". Defaults to "2x".
        use_default : bool
            Use default images instead of user uploaded images.

        Returns
        -------
        Asset
            The Asset for the image. Falls back to default images if no custom images have been uploaded.
        """
        if use_default or self.image is None or f"url_{size}" not in self.image:
            url = self.default_image[f"url_{size}"]
        else:
            url = self.image[f"url_{size}"]

        return Asset(url, http=self._http)


class ChannelVIPAdd(BaseEvent):
    subscription_type = "channel.vip.add"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelVIPAddEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelVIPAdd broadcaster={self.broadcaster} user={self.user}>"


class ChannelVIPRemove(BaseEvent):
    subscription_type = "channel.vip.remove"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelVIPRemoveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelVIPRemove broadcaster={self.broadcaster} user={self.user}>"


class ChannelWarningAcknowledge(BaseEvent):
    subscription_type = "channel.warning.acknowledge"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelWarningAcknowledgeEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelWarningAcknowledge broadcaster={self.broadcaster} user={self.user}>"


class ChannelWarningSend(BaseEvent):
    subscription_type = "channel.warning.send"

    __slots__ = ("broadcaster", "user", "moderator", "reason", "chat_rules")

    def __init__(self, payload: ChannelWarningSendEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.reason: str | None = payload.get("reason")
        self.chat_rules: list[str] | None = payload.get("chat_rules_cited")

    def __repr__(self) -> str:
        return f"<ChannelWarningSend broadcaster={self.broadcaster} user={self.user} moderator={self.moderator}>"


class CharityDonation(BaseEvent):
    subscription_type = "channel.charity_campaign.donate"

    __slots__ = ("broadcaster", "user", "id", "campaign_id", "name", "description", "logo", "website", "amount")

    def __init__(self, payload: CharityCampaignDonationEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.id: str = payload["id"]
        self.campaign_id: str = payload["campaign_id"]
        self.name: str = payload["charity_name"]
        self.description: str = payload["charity_description"]
        self.logo: Asset = Asset(payload["charity_logo"], http=http, dimensions=(100, 100))
        self.website: str = payload["charity_website"]
        self.amount: CharityValues = CharityValues(payload["amount"])

    def __repr__(self) -> str:
        return f"<CharityDonation broadcaster={self.broadcaster} user={self.user} id={self.id} name={self.name}>"


class CharityCampaignStart(BaseEvent):
    subscription_type = "channel.charity_campaign.start"

    __slots__ = ("broadcaster", "id", "name", "description", "logo", "website", "current", "target", "started_at")

    def __init__(self, payload: CharityCampaignStartEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.name: str = payload["charity_name"]
        self.description: str = payload["charity_description"]
        self.logo: Asset = Asset(payload["charity_logo"], http=http, dimensions=(100, 100))
        self.website: str = payload["charity_website"]
        self.current: CharityValues = CharityValues(payload["current_amount"])
        self.target: CharityValues = CharityValues(payload["target_amount"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<CharityCampaignStart broadcaster={self.broadcaster} id={self.id} name={self.name} started_at={self.started_at}>"


class CharityCampaignProgress(BaseEvent):
    subscription_type = "channel.charity_campaign.progress"

    __slots__ = ("broadcaster", "id", "name", "description", "logo", "website", "current", "target")

    def __init__(self, payload: CharityCampaignProgressEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.name: str = payload["charity_name"]
        self.description: str = payload["charity_description"]
        self.logo: Asset = Asset(payload["charity_logo"], http=http, dimensions=(100, 100))
        self.website: str = payload["charity_website"]
        self.current: CharityValues = CharityValues(payload["current_amount"])
        self.target: CharityValues = CharityValues(payload["target_amount"])

    def __repr__(self) -> str:
        return f"<CharityCampaignProgress broadcaster={self.broadcaster} id={self.id} name={self.name} current={self.current} target={self.target}>"


class CharityCampaignStop(BaseEvent):
    subscription_type = "channel.charity_campaign.stop"

    __slots__ = ("broadcaster", "id", "name", "description", "logo", "website", "current", "target", "stopped_at")

    def __init__(self, payload: CharityCampaignStopEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.name: str = payload["charity_name"]
        self.description: str = payload["charity_description"]
        self.logo: Asset = Asset(payload["charity_logo"], http=http, dimensions=(100, 100))
        self.website: str = payload["charity_website"]
        self.current: CharityValues = CharityValues(payload["current_amount"])
        self.target: CharityValues = CharityValues(payload["target_amount"])
        self.stopped_at: datetime.datetime = parse_timestamp(payload["stopped_at"])

    def __repr__(self) -> str:
        return f"<CharityCampaignStop broadcaster={self.broadcaster} id={self.id} name={self.name} stopped_at={self.stopped_at}>"


class ShieldModeBegin(BaseEvent):
    subscription_type = "channel.shield_mode.begin"

    __slots__ = (
        "broadcaster",
        "moderator",
        "started_at",
    )

    def __init__(self, payload: ShieldModeBeginEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<ShieldModeBegin broadcaster={self.broadcaster} moderator={self.moderator} started_at={self.started_at}>"


class HypeTrainContribution:
    __slots__ = ("user", "type", "total")

    def __init__(self, data: HypeTrainContributionData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], http=http)
        self.type: Literal["bits", "subscription", "other"] = data["type"]
        self.total: int = int(data["total"])

    def __repr__(self) -> str:
        return f"<HypeTrainContribution user={self.user} type={self.type} total={self.total}>"


class GoalBegin(BaseEvent):
    subscription_type = "channel.goal.begin"

    __slots__ = ("id", "broadcaster", "type", "description", "current_amount", "target_amount", "started_at")

    def __init__(self, payload: GoalBeginEvent, *, http: HTTPClient) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.type: Literal[
            "follow",
            "subscription",
            "subscription_count",
            "new_subscription",
            "new_subscription_count",
            "new_bit",
            "new_cheerer",
        ] = payload["type"]
        self.description: str = payload["description"]
        self.current_amount: int = int(payload["current_amount"])
        self.target_amount: int = int(payload["target_amount"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<GoalBegin id={self.id} broadcaster={self.broadcaster} type={self.type} target_amount={self.target_amount} started_at={self.started_at}>"


class GoalProgress(BaseEvent):
    subscription_type = "channel.goal.progress"

    __slots__ = ("id", "broadcaster", "type", "description", "current_amount", "target_amount", "started_at")

    def __init__(self, payload: GoalProgressEvent, *, http: HTTPClient) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.type: Literal[
            "follow",
            "subscription",
            "subscription_count",
            "new_subscription",
            "new_subscription_count",
            "new_bit",
            "new_cheerer",
        ] = payload["type"]
        self.description: str = payload["description"]
        self.current_amount: int = int(payload["current_amount"])
        self.target_amount: int = int(payload["target_amount"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<GoalProgress id={self.id} broadcaster={self.broadcaster} type={self.type} current_amount={self.current_amount} target_amount={self.target_amount} started_at={self.started_at}>"


class GoalEnd(BaseEvent):
    subscription_type = "channel.goal.end"

    __slots__ = (
        "id",
        "broadcaster",
        "type",
        "description",
        "current_amount",
        "target_amount",
        "started_at",
        "ended_at",
        "achieved",
    )

    def __init__(self, payload: GoalEndEvent, *, http: HTTPClient) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.type: Literal[
            "follow",
            "subscription",
            "subscription_count",
            "new_subscription",
            "new_subscription_count",
            "new_bit",
            "new_cheerer",
        ] = payload["type"]
        self.description: str = payload["description"]
        self.current_amount: int = int(payload["current_amount"])
        self.target_amount: int = int(payload["target_amount"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])
        self.achieved: bool = bool(payload["is_achieved"])

    def __repr__(self) -> str:
        return f"<GoalEnd id={self.id} broadcaster={self.broadcaster} type={self.type} started_at={self.started_at} ended_at={self.ended_at} achieved={self.achieved}>"


class HypeTrainBegin(BaseEvent):
    subscription_type = "channel.hype_train.begin"

    __slots__ = (
        "broadcaster",
        "id",
        "level",
        "total",
        "progress",
        "goal",
        "top_contributions",
        "last_contribution",
        "started_at",
        "expires_at",
    )

    def __init__(self, payload: HypeTrainBeginEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.level: int = int(payload["level"])
        self.total: int = int(payload["total"])
        self.progress: int = int(payload["progress"])
        self.goal: int = int(payload["goal"])
        self.top_contributions: list[HypeTrainContribution] = [
            HypeTrainContribution(c, http=http) for c in payload["top_contributions"]
        ]
        self.last_contribution: HypeTrainContribution = HypeTrainContribution(payload["last_contribution"], http=http)
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.expires_at: datetime.datetime = parse_timestamp(payload["expires_at"])

    def __repr__(self) -> str:
        return f"<HypeTrainBegin id={self.id} broadcaster={self.broadcaster} goal={self.goal} started_at={self.started_at}>"


class HypeTrainProgress(BaseEvent):
    subscription_type = "channel.hype_train.progress"

    __slots__ = (
        "broadcaster",
        "id",
        "level",
        "total",
        "progress",
        "goal",
        "top_contributions",
        "last_contribution",
        "started_at",
        "expires_at",
    )

    def __init__(self, payload: HypeTrainProgressEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.level: int = int(payload["level"])
        self.total: int = int(payload["total"])
        self.progress: int = int(payload["progress"])
        self.goal: int = int(payload["goal"])
        self.top_contributions: list[HypeTrainContribution] = [
            HypeTrainContribution(c, http=http) for c in payload["top_contributions"]
        ]
        self.last_contribution: HypeTrainContribution = HypeTrainContribution(payload["last_contribution"], http=http)
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.expires_at: datetime.datetime = parse_timestamp(payload["expires_at"])

    def __repr__(self) -> str:
        return f"<HypeTrainProgress id={self.id} broadcaster={self.broadcaster} goal={self.goal} progress={self.progress}>"


class HypeTrainEnd(BaseEvent):
    subscription_type = "channel.hype_train.end"

    __slots__ = (
        "broadcaster",
        "id",
        "level",
        "total",
        "top_contributions",
        "cooldown_ends_at",
        "started_at",
        "ended_at",
    )

    def __init__(self, payload: HypeTrainEndEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.level: int = int(payload["level"])
        self.total: int = int(payload["total"])

        self.top_contributions: list[HypeTrainContribution] = [
            HypeTrainContribution(c, http=http) for c in payload["top_contributions"]
        ]
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])
        self.cooldown_ends_at: datetime.datetime = parse_timestamp(payload["cooldown_ends_at"])

    def __repr__(self) -> str:
        return f"<HypeTrainEnd id={self.id} broadcaster={self.broadcaster} total={self.total} ended_at={self.ended_at}>"


class ShieldModeEnd(BaseEvent):
    subscription_type = "channel.shield_mode.end"

    __slots__ = (
        "broadcaster",
        "moderator",
        "ended_at",
    )

    def __init__(self, payload: ShieldModeEndEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])

    def __repr__(self) -> str:
        return f"<ShieldModeEnd broadcaster={self.broadcaster} moderator={self.moderator} ended_at={self.ended_at}>"


class ShoutoutCreate(BaseEvent):
    subscription_type = "channel.shoutout.create"

    __slots__ = (
        "broadcaster",
        "to_broadcaster",
        "moderator",
        "viewer_count",
        "started_at",
        "cooldown_ends_at",
        "target_cooldown_ends_at",
    )

    def __init__(self, payload: ShoutoutCreateEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.moderator: PartialUser = PartialUser(payload["moderator_user_id"], payload["moderator_user_login"], http=http)
        self.to_broadcaster: PartialUser = PartialUser(
            payload["to_broadcaster_user_id"], payload["to_broadcaster_user_login"], http=http
        )
        self.viewer_count: int = int(payload["viewer_count"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.cooldown_ends_at: datetime.datetime = parse_timestamp(payload["cooldown_ends_at"])
        self.target_cooldown_ends_at: datetime.datetime = parse_timestamp(payload["target_cooldown_ends_at"])

    def __repr__(self) -> str:
        return f"<ShoutoutCreate broadcaster={self.broadcaster} to_broadcaster={self.to_broadcaster} started_at={self.started_at}>"


class ShoutoutReceive(BaseEvent):
    subscription_type = "channel.shoutout.receive"

    __slots__ = ("broadcaster", "from_broadcaster", "viewer_count", "started_at")

    def __init__(self, payload: ShoutoutReceiveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.from_broadcaster: PartialUser = PartialUser(
            payload["from_broadcaster_user_id"], payload["from_broadcaster_user_login"], http=http
        )
        self.viewer_count: int = int(payload["viewer_count"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<ShoutoutReceive broadcaster={self.broadcaster} from_broadcaster={self.from_broadcaster} started_at={self.started_at}>"


class StreamOnline(BaseEvent):
    subscription_type = "stream.online"

    __slots__ = ("broadcaster", "id", "type", "started_at")

    def __init__(self, payload: StreamOnlineEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )
        self.id: str = payload["id"]
        self.type: Literal["live", "playlist", "watch_party", "premiere", "rerun"] = payload["type"]
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<StreamOnline id={self.id} broadcaster={self.broadcaster} started_at={self.started_at}>"


class StreamOffline(BaseEvent):
    subscription_type = "stream.offline"

    __slots__ = "broadcaster"

    def __init__(self, payload: StreamOfflineEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], http=http
        )

    def __repr__(self) -> str:
        return f"<StreamOffline broadcaster={self.broadcaster}>"


class UserAuthorizationGrant(BaseEvent):
    subscription_type = "user.authorization.grant"

    __slots__ = ("client_id", "user")

    def __init__(self, payload: UserAuthorizationGrantEvent, *, http: HTTPClient) -> None:
        self.client_id: str = payload["client_id"]
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<UserAuthorizationGrant client_id={self.client_id} user={self.user}>"


class UserAuthorizationRevoke(BaseEvent):
    subscription_type = "user.authorization.revoke"

    __slots__ = ("client_id", "user")

    def __init__(self, payload: UserAuthorizationRevokeEvent, *, http: HTTPClient) -> None:
        self.client_id: str = payload["client_id"]
        self.user: PartialUser | None = (
            PartialUser(payload["user_id"], payload["user_login"], http=http) if payload.get("user_id") else None
        )

    def __repr__(self) -> str:
        return f"<UserAuthorizationRevoke client_id={self.client_id} user={self.user}>"


class UserUpdate(BaseEvent):
    subscription_type = "user.update"

    __slots__ = ("user", "email", "verified", "description")

    def __init__(self, payload: UserUpdateEvent, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.verified: bool = bool(payload["email_verified"])
        self.description: str = payload["description"]
        self.email: str | None = payload.get("email", None)

    def __repr__(self) -> str:
        return f"<UserUpdate user={self.user} verified={self.verified} description={self.description}>"


class Whisper(BaseEvent):
    subscription_type = "user.whisper.message"

    __slots__ = ("sender", "recipient", "id", "message")

    def __init__(self, payload: UserWhisperEvent, *, http: HTTPClient) -> None:
        self.sender: PartialUser = PartialUser(payload["from_user_id"], payload["from_user_login"], http=http)
        self.recipient: PartialUser = PartialUser(payload["to_user_id"], payload["to_user_login"], http=http)
        self.id: str = payload["whisper_id"]
        self.message: str = payload["whisper"]["text"]

    def __repr__(self) -> str:
        return f"<Whisper sender={self.sender} recipient={self.recipient} id={self.id} message={self.message}>"


class SubscriptionRevoked:
    __slots__ = (
        "raw",
        "status",
        "reason",
        "transport_method",
        "transport_data",
    )

    def __init__(self, data: RevocationSubscription) -> None:
        self.raw: RevocationSubscription = data
        self.status: RevocationReason = RevocationReason(data["status"])
        self.reason: RevocationReason = self.status
        self.transport_method: TransportMethod = TransportMethod(data["transport"]["method"])
        self.transport_data: RevocationTransport = data["transport"]
