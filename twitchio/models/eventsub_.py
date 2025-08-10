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

import datetime
from itertools import accumulate
from typing import TYPE_CHECKING, Any, ClassVar, Literal, NamedTuple, cast

from twitchio.assets import Asset
from twitchio.eventsub import RevocationReason, TransportMethod
from twitchio.models.channel_points import CustomReward, RewardLimitSettings
from twitchio.models.charity import CharityValues
from twitchio.models.chat import EmoteSet
from twitchio.models.polls import PollChoice
from twitchio.models.predictions import PredictionOutcome
from twitchio.user import Chatter, PartialUser
from twitchio.utils import Colour, parse_timestamp


if TYPE_CHECKING:
    from twitchio.http import HTTPAsyncIterator, HTTPClient
    from twitchio.models.channel_points import CustomRewardRedemption
    from twitchio.models.chat import SentMessage
    from twitchio.types_.conduits import (
        Condition,
        ConduitData,
        NotificationMessage,
        NotificationMetaData,
        NotificationSubscription as _NotificationSubscription,
        NotificationTransport,
        RevocationSubscription,
        RevocationTransport,
        ShardData,
        ShardUpdateRequest,
        WelcomeSession,
    )
    from twitchio.types_.eventsub import *
    from twitchio.types_.responses import (
        EventsubSubscriptionResponse,
        EventsubSubscriptionResponseData,
        EventsubTransportData,
    )

__all__ = (
    "AutoRedeemReward",
    "AutomodBlockedTerm",
    "AutomodMessageHold",
    "AutomodMessageUpdate",
    "AutomodSettingsUpdate",
    "AutomodTermsUpdate",
    "BaseChannelPointsRedemption",
    "BaseChannelPoll",
    "BaseChannelPrediction",
    "BaseCharityCampaign",
    "BaseChatMessage",
    "BaseEmote",
    "BaseHypeTrain",
    "BaseSharedChatSession",
    "Boundary",
    "ChannelAdBreakBegin",
    "ChannelBan",
    "ChannelBitsUse",
    "ChannelChatClear",
    "ChannelChatClearUserMessages",
    "ChannelCheer",
    "ChannelFollow",
    "ChannelModerate",
    "ChannelModeratorAdd",
    "ChannelModeratorRemove",
    "ChannelPointsAutoRedeemAdd",
    "ChannelPointsEmote",
    "ChannelPointsRedemptionAdd",
    "ChannelPointsRedemptionUpdate",
    "ChannelPointsReward",
    "ChannelPointsRewardAdd",
    "ChannelPointsRewardRemove",
    "ChannelPointsRewardUpdate",
    "ChannelPollBegin",
    "ChannelPollEnd",
    "ChannelPollProgress",
    "ChannelPredictionBegin",
    "ChannelPredictionEnd",
    "ChannelPredictionLock",
    "ChannelPredictionProgress",
    "ChannelRaid",
    "ChannelSubscribe",
    "ChannelSubscriptionEnd",
    "ChannelSubscriptionGift",
    "ChannelSubscriptionMessage",
    "ChannelUnban",
    "ChannelUnbanRequest",
    "ChannelUnbanRequestResolve",
    "ChannelUpdate",
    "ChannelVIPAdd",
    "ChannelVIPRemove",
    "ChannelWarningAcknowledge",
    "ChannelWarningSend",
    "CharityCampaignDonation",
    "CharityCampaignProgress",
    "CharityCampaignStart",
    "CharityCampaignStop",
    "ChatAnnouncement",
    "ChatBitsBadgeTier",
    "ChatCharityDonation",
    "ChatCommunitySubGift",
    "ChatGiftPaidUpgrade",
    "ChatMessage",
    "ChatMessageBadge",
    "ChatMessageCheer",
    "ChatMessageCheermote",
    "ChatMessageDelete",
    "ChatMessageEmote",
    "ChatMessageFragment",
    "ChatMessageReply",
    "ChatNotification",
    "ChatPayItForward",
    "ChatPrimePaidUpgrade",
    "ChatRaid",
    "ChatResub",
    "ChatSettingsUpdate",
    "ChatSub",
    "ChatSubGift",
    "ChatUserMessageHold",
    "ChatUserMessageUpdate",
    "Chatter",
    "Conduit",
    "ConduitShard",
    "CooldownSettings",
    "EventsubSubscription",
    "EventsubSubscriptions",
    "GoalBegin",
    "GoalEnd",
    "GoalProgress",
    "HypeTrainBegin",
    "HypeTrainEnd",
    "HypeTrainProgress",
    "ModerateAutomodTerms",
    "ModerateBan",
    "ModerateDelete",
    "ModerateFollowers",
    "ModerateRaid",
    "ModerateSlow",
    "ModerateTimeout",
    "ModerateUnbanRequest",
    "ModerateWarn",
    "PollVoting",
    "PowerUp",
    "PowerUpEmote",
    "SharedChatSessionBegin",
    "SharedChatSessionEnd",
    "SharedChatSessionUpdate",
    "ShieldModeBegin",
    "ShieldModeEnd",
    "ShoutoutCreate",
    "ShoutoutReceive",
    "StreamOffline",
    "StreamOnline",
    "SubscribeEmote",
    "SubscriptionRevoked",
    "SuspiciousUserMessage",
    "SuspiciousUserUpdate",
    "UnlockedEmote",
    "UserAuthorizationGrant",
    "UserAuthorizationRevoke",
    "UserUpdate",
    "WebsocketWelcome",
    "Whisper",
)


class BaseEvent:
    _registry: ClassVar[dict[str, type]] = {}
    subscription_type: ClassVar[str | None] = None

    def __init__(
        self,
        *,
        subscription_data: Any,
        metadata: NotificationMetaData | None = None,
        headers: EventSubHeaders | None = None,
    ) -> None:
        self._metadata = metadata
        self._headers = headers
        self._sub_data = subscription_data

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.subscription_type is not None:
            BaseEvent._registry[cls.subscription_type] = cls

    @property
    def timestamp(self) -> datetime.datetime | None:
        """The timestamp of the eventsub notification from Twitch in UTC.

        If the notification Twitch sends is missing this data, then it will return `None`.

        Returns
        -------
        datetime.datetime
            The datetime in UTC of the eventsub notification from Twitch.
        """
        if self._metadata and (timestamp := self._metadata.get("message_timestamp")):
            return parse_timestamp(timestamp)

        if self._headers and (timestamp := self._headers.get("Twitch-Eventsub-Message-Timestamp")):
            return parse_timestamp(timestamp)

        return None

    @property
    def metadata(self) -> Metadata | None:
        """Returns the metadata of a websocket event notification.

        Returns
        -------
        Metadata | None
        """
        return Metadata(self._metadata) if self._metadata is not None else None

    @property
    def headers(self) -> Headers | None:
        """Returns eventsub webhook headers as a structured Headers object.

        Returns
        -------
        Headers | None
        """
        return Headers(self._headers) if self._headers is not None else None

    @property
    def subscription_data(self) -> NotificationSubscription:
        """Returns the subscription data of the eventsub notification.

        Returns
        -------
        NotificationSubscription
        """
        return NotificationSubscription(self._sub_data)


class _ResponderEvent(BaseEvent):
    broadcaster: PartialUser
    _http: HTTPClient

    async def respond(self, content: str, *, me: bool = False) -> SentMessage:
        """|coro|

        Helper method to respond by sending a message to the broadcasters channel this event originates from, as the bot.

        .. warning::

            You must set the ``bot_id`` parameter on your :class:`~twitchio.Client`, :class:`~twitchio.ext.commands.Bot` or
            :class:`~twitchio.ext.commands.AutoBot` for this method to work.

        .. important::

            You must have the ``user:write:chat`` scope. If an app access token is used,
            then additionally requires the ``user:bot`` scope on the bot,
            and either ``channel:bot`` scope from the broadcaster or moderator status.

        .. versionadded:: 3.1

        Parameters
        ----------
        content: str
            The content of the message you would like to send. This cannot exceed ``500`` characters. Additionally the content
            parameter will be stripped of all leading and trailing whitespace.
        me: bool
            An optional bool indicating whether you would like to send this message with the ``/me`` chat command.

        Returns
        -------
        SentMessage
            The payload received by Twitch after sending this message.

        Raises
        ------
        HTTPException
            Twitch failed to process the message, could be ``400``, ``401``, ``403``, ``422`` or any ``5xx`` status code.
        MessageRejectedError
            Twitch rejected the message from various checks.
        RuntimeError
            You must provide the ``bot_id`` parameter to :class:`~twitchio.Client`, :class:`~twitchio.ext.commands.Bot` or
            :class:`~twitchio.ext.commands.AutoBot` for this method to work.
        """
        client = getattr(self._http, "_client", None)
        if not client:
            raise NotImplementedError("This method is only available with Client/Bot dispatched events.")

        bot_id = client.bot_id
        if not bot_id:
            raise RuntimeError(f"You must provide 'bot_id' to {client!r} to use this method.")

        new = (f"/me {content}" if me else content).strip()
        return await self.broadcaster.send_message(sender=bot_id, message=new)


def create_event_instance(
    event_type: str,
    raw_data: NotificationMessage | Any,
    *,
    http: HTTPClient | None = None,
    headers: EventSubHeaders | None = None,
) -> Any:
    event_cls = BaseEvent._registry.get(event_type)
    if not event_cls:
        raise ValueError(f"No class registered for event type {event_type}")

    payload = raw_data["payload"]["event"] if "payload" in raw_data else raw_data["event"]
    metadata = raw_data.get("metadata")
    sub_data = raw_data["payload"]["subscription"] if "payload" in raw_data else raw_data["subscription"]
    instance = event_cls(payload, http=http)

    if isinstance(instance, BaseEvent):
        instance._sub_data = sub_data
        instance._metadata = metadata
        instance._headers = headers

    if isinstance(instance, _ResponderEvent):
        instance._http = http  # type: ignore

    return instance


class Metadata:
    """
    Represents the metadata returned from a websocket eventsub notification.

    Attributes
    -----------
    message_id: str
        An ID that uniquely identifies the message.
    message_type: typing.Literal["notification"]
        The type of message, which is set to `notification`.
    message_timestamp: datetime.datetime
        The UTC date and time that the message was sent.
    subscription_type: str
        The type of subscription. See `Subscription Types <https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/#subscription-types>`_.
    subscription_version: typing.Literal["1", "2"]
        The version number of the subscription type's definition. This is the same value specified in the subscription request.
    """

    __slots__ = ("message_id", "message_timestamp", "message_type", "subscription_type", "subscription_version")

    def __init__(self, data: NotificationMetaData) -> None:
        self.message_id: str = data["message_id"]
        self.message_type: Literal["notification"] = data["message_type"]
        self.message_timestamp: datetime.datetime = parse_timestamp(data["message_timestamp"])
        self.subscription_type: str = data["subscription_type"]
        self.subscription_version: Literal["1", "2"] = data["subscription_version"]

    def __repr__(self) -> str:
        return f"<Metadata message_id={self.message_id}, message_type={self.message_type} subscription_type={self.subscription_type}>"


class Headers:
    """
    Represents the headers received from a webhook notification.

    Attributes
    -----------
    message_id: str
        An ID that uniquely identifies this message. This is an opaque ID, and is not required to be in any particular format.
    message_retry: str
        Twitch sends you a notification at least once. If Twitch is unsure of whether you received a notification, it'll resend the event, which means you may receive a notification twice.
    message_type: typing.Literal["notification", "webhook_callback_verification", "revocation"]
        The type of notification. Possible values are:

        - notification — Contains the event's data.
        - webhook_callback_verification — Contains the challenge used to verify that you own the event handler.
        - revocation — Contains the reason why Twitch revoked your subscription.

    message_signature: str
        The HMAC signature that you use to verify that Twitch sent the message.
    message_timestamp: datetime.datetime: str
        The UTC date and time that Twitch sent the notification.
    subscription_type: str
        The subscription type you subscribed to. For example, `channel.follow`.
    subscription_version: str
        The version number that identifies the definition of the subscription request. This version matches the version number that you specified in your subscription request.
    raw_data: dict[str, str]
        The headers as a raw dictionary, as there are additional fields that are not Twitch specific. You can utilise the `.get()` method to retrieve specific headers.

    """

    __slots__ = (
        "message_id",
        "message_retry",
        "message_signature",
        "message_timestamp",
        "message_type",
        "raw_data",
        "subscription_type",
        "subscription_version",
    )

    def __init__(self, data: EventSubHeaders) -> None:
        self.message_id: str = data.get("Twitch-Eventsub-Message-Id", "")
        self.message_retry: str = data.get("Twitch-Eventsub-Message-Retry", "")
        self.message_type: Literal["notification", "webhook_callback_verification", "revocation"] = data.get(
            "Twitch-Eventsub-Message-Type", "notification"
        )
        self.message_signature: str = data.get("Twitch-Eventsub-Message-Signature", "")
        timestamp = data.get("Twitch-Eventsub-Message-Timestamp", datetime.datetime.now(tz=datetime.UTC).isoformat())
        self.message_timestamp: datetime.datetime = parse_timestamp(timestamp)
        self.subscription_type: str = data.get("Twitch-Eventsub-Subscription-Type", "")
        self.subscription_version: str = data.get("Twitch-Eventsub-Subscription-Version", "")

        self.raw_data: EventSubHeaders = data

    def get(self, key: str) -> str | None:
        """Retrieve a header value by key."""
        return self.raw_data.get(key)

    def __repr__(self) -> str:
        return f"<Headers message_id={self.message_id}, message_type={self.message_type} subscription_type={self.subscription_type}>"


class NotificationSubscription:
    """
    Represents the metadata returned from a websocket eventsub notification.

    Attributes
    -----------
    id: str
        An ID that uniquely identifies this subscription.
    status: str
        The subscription's status.
    type: str
        The notification's subscription type.
    version: typing.Literal["1", "2"]
        The version number of the subscription type's definition.
    cost: int
        How much the subscription counts against your limit. See `Subscription Limits <https://dev.twitch.tv/docs/eventsub/manage-subscriptions#subscription-limits>`_.
    condition: Condition
        This is a TypedDict that contains the conditions under which the event fires.
    transport: NotificationTransport
        This is a TypedDict that contains information about the transport used for notifications.
    created_at: datetime.datetime
        The UTC date and time that the subscription was created.
    """

    __slots__ = ("condition", "cost", "created_at", "id", "status", "transport", "type", "version")

    def __init__(self, data: _NotificationSubscription) -> None:
        self.id: str = data["id"]
        self.status: str = data["status"]
        self.type: str = data["type"]
        self.version: Literal["1", "2"] = data["version"]
        self.cost: int = data["cost"]
        self.condition: Condition = data["condition"]
        self.transport: NotificationTransport = data["transport"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self) -> str:
        return (
            f"<NotificationSubscription id={self.id}, type={self.type}, status={self.status} created_at={self.created_at}>"
        )


class Boundary(NamedTuple):
    """
    NamedTuple that represents the boundaries of caught automod words.

    Attributes
    -----------
    start: int
        Index in the message for the start of the problem (0 indexed, inclusive).
    end: int
        Index in the message for the end of the problem (0 indexed, inclusive).
    """

    start: int
    end: int


class AutomodBlockedTerm:
    """
    Represents a blocked term from AutoMod.

    Attributes
    ----------
    id: str
        The id of the blocked term found.
    owner: PartialUser
        The broadcaster who has blocked the term.
    boundary: Boundary
        The start and end indexes of the blocked term in the message.
    """

    __slots__ = ("boundary", "id", "owner")

    def __init__(self, payload: AutomodBlockedTermData, *, http: HTTPClient) -> None:
        self.id: str = payload["term_id"]
        self.owner: PartialUser = PartialUser(
            payload["owner_broadcaster_user_id"],
            payload["owner_broadcaster_user_login"],
            payload["owner_broadcaster_user_name"],
            http=http,
        )
        self.boundary: Boundary = Boundary(payload["boundary"]["start_pos"], payload["boundary"]["end_pos"])

    def __repr__(self) -> str:
        return f"<BlockedTerm id={self.id} owner={self.owner} boundary={self.boundary}>"


class AutomodMessageHold(_ResponderEvent):
    """
    Represents an automod message hold event. Both V1 and V2.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster specified in the request.
    user: PartialUser
        The user who sent the message.
    message_id: str
        The ID of the message that was flagged by automod.
    text: str
        The text content of the message.
    level: int | None
        The level of severity. Measured between 1 to 4. This is `None` if the V2 endpoint is used and the reason is `blocked_term`.
    category: str | None
        The category of the message. This is `None` if the V2 endpoint is used and the reason is `blocked_term`.
    held_at: datetime.datetime
        The datetime of when automod saved the message.
    fragments: list[ChatMessageFragment]
        List of chat message fragments.
    reason: typing.Literal["automod", "blocked_term"] | None
        The reason for the message being held. This is only populated for the V2 endpoint.
    boundaries: list[Boundary]
        The start and end index of the words caught by automod. This is only populated for the V2 endpoint and when the reason is `automod`.

    """

    subscription_type = "automod.message.hold"

    __slots__ = (
        "blocked_terms",
        "boundaries",
        "broadcaster",
        "category",
        "held_at",
        "level",
        "message_id",
        "reason",
        "text",
        "user",
    )

    def __init__(self, payload: AutomodMessageHoldEvent | AutomodMessageHoldV2Event, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.message_id: str = payload["message_id"]
        self.text: str = payload["message"]["text"]
        self.held_at: datetime.datetime = parse_timestamp(payload["held_at"])

        message_fragments = payload["message"]["fragments"]
        self.fragments: list[ChatMessageFragment] = [
            ChatMessageFragment(fragment, http=http) for fragment in message_fragments
        ]

        automod_data = payload.get("automod") or {}
        blocked_term_data = payload.get("blocked_term") or {}

        self.reason: Literal["automod", "blocked_term"] | None = payload.get("reason")
        self.level: int | None = automod_data.get("level") or payload.get("level")
        self.category: str | None = automod_data.get("category") or payload.get("category")

        boundaries = automod_data.get("boundaries", [])
        self.boundaries: list[Boundary] = [Boundary(boundary["start_pos"], boundary["end_pos"]) for boundary in boundaries]

        blocked_terms = blocked_term_data.get("terms_found", [])
        self.blocked_terms: list[AutomodBlockedTerm] = [AutomodBlockedTerm(term, http=http) for term in blocked_terms]

    def __repr__(self) -> str:
        return f"<AutomodMessageHold broadcaster={self.broadcaster} user={self.user} message_id={self.message_id} level={self.level}>"

    @property
    def emotes(self) -> list[ChatMessageEmote]:
        """
        A property that lists all of the emotes of a message.
        If no emotes are in the message this will return an empty list.

        Returns
        -------
        list[ChatMessageEmote]
            A list of ChatMessageEmote objects.
        """
        return [f.emote for f in self.fragments if f.emote is not None]

    @property
    def cheermotes(self) -> list[ChatMessageCheermote]:
        """
        A property that lists all of the cheermotes of a message.
        If no cheermotes are in the message this will return an empty list.

        Returns
        -------
        list[ChatMessageCheermote]
            A list of ChatMessageCheermote objects.
        """
        return [f.cheermote for f in self.fragments if f.cheermote is not None]


class AutomodMessageUpdate(AutomodMessageHold):
    """
    Represents an automod message update event. Both V1 and V2.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster specified in the request.
    moderator: PartialUser
        The moderator who approved or denied the message.
    user: PartialUser
        The user who sent the message.
    message_id: str
        The ID of the message that was flagged by automod.
    text: str
        The text content of the message.
    level: int | None
        The level of severity. Measured between 1 to 4. This is `None` if the V2 endpoint is used and the reason is `blocked_term`.
    category: str | None
        The category of the message. This is `None` if the V2 endpoint is used and the reason is `blocked_term`.
    held_at: datetime.datetime
        The datetime of when automod saved the message.
    emotes: list[ChatMessageEmote]
        List of emotes in the message.
    cheermotes: list[ChatMessageCheermote]
        List of cheermotes in the message.
    fragments: list[ChatMessageFragment]
        List of chat message fragments.
    status: typing.Literal["Approved", "Denied", "Expired"]
        The message's status. Possible values are:

        - Approved
        - Denied
        - Expired

    reason: typing.Literal["automod", "blocked_term"] | None
        The reason for the message being held. This is only populated for the V2 endpoint.
    boundaries: list[Boundary]
        The start and end index of the words caught by automod. This is only populated for the V2 endpoint and when the reason is `automod`.
    """

    subscription_type = "automod.message.update"

    __slots__ = ("moderator", "status")

    def __init__(self, payload: AutomodMessageUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload=payload, http=http)
        self.moderator = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.status: Literal["Approved", "Denied", "Expired"] = payload["status"]

    def __repr__(self) -> str:
        return f"<AutomodMessageUpdate broadcaster={self.broadcaster} user={self.user} message_id={self.message_id} level={self.level}>"


class AutomodSettingsUpdate(_ResponderEvent):
    """
    Represents an automod settings update event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster who had their automod settings updated.
    moderator: PartialUser
        The moderator who changed the channel settings.
    overall_level: int | None
        The default AutoMod level for the broadcaster. This is `None` if the broadcaster has set one or more of the individual settings.
    disability: int
        The Automod level for discrimination against disability.
    aggression: int
        The Automod level for hostility involving aggression.
    misogyny: int
        The Automod level for discrimination against women.
    bullying: int
        The Automod level for hostility involving name calling or insults.
    swearing: int
        The Automod level for profanity.
    race_ethnicity_or_religion: int
        The Automod level for racial discrimination.
    sex_based_terms: int
        The Automod level for sexual content.
    sexuality_sex_or_gender: int
        The AutoMod level for discrimination based on sexuality, sex, or gender.
    """

    subscription_type = "automod.settings.update"

    __slots__ = (
        "aggression",
        "broadcaster",
        "bullying",
        "disability",
        "misogyny",
        "moderator",
        "overall_level",
        "race_ethnicity_or_religion",
        "sex_based_terms",
        "sexuality_sex_or_gender",
        "swearing",
    )

    def __init__(self, payload: AutomodSettingsUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.moderator = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.overall_level: int | None = int(payload["overall_level"]) if payload["overall_level"] is not None else None
        self.disability: int = int(payload["disability"])
        self.aggression: int = int(payload["aggression"])
        self.misogyny: int = int(payload["misogyny"])
        self.bullying: int = int(payload["bullying"])
        self.swearing: int = int(payload["swearing"])
        self.race_ethnicity_or_religion: int = int(payload["race_ethnicity_or_religion"])
        self.sex_based_terms: int = int(payload["sex_based_terms"])
        self.sexuality_sex_or_gender: int = int(payload["sexuality_sex_or_gender"])

    def __repr__(self) -> str:
        return f"<AutomodSettingsUpdate broadcaster={self.broadcaster} moderator={self.moderator} overall_level={self.overall_level}>"


class AutomodTermsUpdate(_ResponderEvent):
    """
    Represents an automod terms update event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster specified in the request.
    moderator: PartialUser
        The moderator who changed the channel settings.
    action: typing.Literal["add_permitted", "remove_permitted", "add_blocked", "remove_blocked"]
        The status change applied to the terms. Possible options are:

        - add_permitted
        - remove_permitted
        - add_blocked
        - remove_blocked

    automod: bool
        Whether this term was added due to an Automod message approve/deny action
    terms: list[str]
        The list of terms that had a status change.
    """

    subscription_type = "automod.terms.update"

    __slots__ = ("action", "automod", "broadcaster", "moderator", "terms")

    def __init__(self, payload: AutomodTermsUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.moderator = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.action: Literal["add_permitted", "remove_permitted", "add_blocked", "remove_blocked"] = payload["action"]
        self.automod: bool = bool(payload["from_automod"])
        self.terms: list[str] = payload["terms"]

    def __repr__(self) -> str:
        return f"<AutomodTermsUpdate broadcaster={self.broadcaster} moderator={self.moderator} action={self.action} automod={self.automod}>"


class RewardEmote:
    """
    Represents a minimal Reward Emote.

    Attributes
    ----------
    id: str
        The ID that uniquely identifies this emote.
    name: str
        The human readable emote token.
    """

    __slots__ = ("id", "name")

    def __init__(self, data: ChannelPointsUnlockedEmoteData | PowerUpEmoteDataData) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]

    def __repr__(self) -> str:
        return f"<RewardEmote id={self.id} name={self.name}>"


class PowerUpEmote(RewardEmote):
    """
    Represents a PowerUp Emote on a channel bits use event.

    Attributes
    ----------
    id: str
        The ID that uniquely identifies this emote.
    name: str
        The human readable emote token.
    """

    def __init__(self, data: PowerUpEmoteDataData) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<PowerUpEmote id={self.id} name={self.name}>"


class PowerUp:
    """
    Represents a PowerUp on a channel bits use event.

    Attributes
    ----------
    emote: PowerUpEmote | None
        Emote associated with the reward. Is `None` if no emote was used.
    type: typing.Literal["message_effect", "celebration", "gigantify_an_emote"]
        The type of Power-up redeemed.

            - message_effect
            - celebration
            - gigantify_an_emote

    message_effect_id: str | None
        The ID of the message effect. Is `None` if no message effect was used.
    """

    __slots__ = ("emote", "message_effect_id", "type")

    def __init__(self, data: PowerUpData) -> None:
        emote = data.get("emote")
        self.emote: PowerUpEmote | None = PowerUpEmote(emote) if emote is not None else None
        self.type: Literal["message_effect", "celebration", "gigantify_an_emote"] = data["type"]
        self.message_effect_id: str | None = data.get("message_effect_id")


class ChannelBitsUse(_ResponderEvent):
    """
    Represents a channel bits use event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcastter / channel where the Bits were redeemed.
    user: PartialUser
        The redeeming user.
    bits: int
        The number of Bits used.
    type: typing.Literal["cheer", "power_up"]
        What the Bits were used for.
    text: str | None
        The chat message in plain text. Is `None` if no chat message was used.
    fragments: list[ChatMessageFragment]
        The ordered list of chat message fragments. Is `None` if no chat message was used.
    power_up: PowerUp | None
        Data about Power-up. Is `None` if a Power-up is not used.
    """

    subscription_type = "channel.bits.use"

    __slots__ = ("bits", "broadcaster", "fragments", "power_up", "text", "type", "user")

    def __init__(self, payload: ChannelBitsUseEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.bits: int = int(payload["bits"])
        self.type: Literal["cheer", "power_up"] = payload["type"]
        self.text: str | None = payload.get("message").get("text")
        power_up = payload.get("power_up")
        self.power_up: PowerUp | None = PowerUp(power_up) if power_up is not None else None
        self.fragments: list[ChatMessageFragment] = [
            ChatMessageFragment(fragment, http=http) for fragment in payload["message"]["fragments"]
        ]

    def __repr__(self) -> str:
        return f"<ChannelBitsUse broadcaster={self.broadcaster} user={self.user} bits={self.bits} type={self.type}>"


class ChannelUpdate(_ResponderEvent):
    """
    Represents a channel update event.

    Attributes
    ----------
    broadcaster: PartialUser
        An ID that identifies the emote set that the emote belongs to.
    title: str
        The channel's stream title.
    language: str
        The channel's broadcast language.
    category_id: str
        The channel's category ID.
    category_name: str
        The category name.
    content_classification_labels: list[str]
        List of content classification label IDs currently applied on the Channel.
    """

    subscription_type = "channel.update"

    __slots__ = ("broadcaster", "category_id", "category_name", "content_classification_labels", "title")

    def __init__(self, payload: ChannelUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.title: str = payload["title"]
        self.language: str = payload["language"]
        self.category_id: str = payload["category_id"]
        self.category_name: str = payload["category_name"]
        self.content_classification_labels: list[str] = payload["content_classification_labels"]

    def __repr__(self) -> str:
        return f"<ChannelUpdate title={self.title} language={self.language} category_id={self.category_id} category_name={self.category_name}>"


class ChannelFollow(_ResponderEvent):
    """
    Represents a channel follow event.

    Attributes
    ----------
    broadcaster: PartialUser
        The requested broadcaster to listen to follows for.
    user: PartialUser
        The user that is now following the specified channel.
    followed_at: datetime.datetime
        Datetime when the follow occurred.
    """

    subscription_type = "channel.follow"

    __slots__ = ("broadcaster", "followed_at", "user")

    def __init__(self, payload: ChannelFollowEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.followed_at: datetime.datetime = parse_timestamp(payload["followed_at"])

    def __repr__(self) -> str:
        return f"<ChannelFollow broadcaster={self.broadcaster} user={self.user} followed_at={self.followed_at}>"


class ChannelAdBreakBegin(_ResponderEvent):
    """
    Represents a channel ad break event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster the ad was run on.
    requester: PartialUser
        The user that requested the ad.
    duration: int
        Length in seconds of the mid-roll ad break requested.
    automatic: bool
        Indicates if the ad was automatically scheduled via Ads Manager.
    started_at: datetime.datetime
        Datetime when the follow occurred.
    """

    subscription_type = "channel.ad_break.begin"

    __slots__ = ("automatic", "broadcaster", "duration", "requester", "started_at")

    def __init__(self, payload: ChannelAdBreakBeginEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.requester: PartialUser = PartialUser(
            payload["requester_user_id"], payload["requester_user_login"], payload["requester_user_name"], http=http
        )
        self.duration: int = int(payload["duration_seconds"])
        self.automatic: bool = bool(payload["is_automatic"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return (
            f"<ChannelAdBreakBegin broadcaster={self.broadcaster} requester={self.requester} started_at={self.started_at}>"
        )


class ChannelChatClear(_ResponderEvent):
    """
    Represents a channel chat clear event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster's chat that was cleared.
    """

    subscription_type = "channel.chat.clear"

    __slots__ = ("broadcaster",)

    def __init__(self, payload: ChannelChatClearEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChannelChatClear broadcaster={self.broadcaster}>"


class ChannelChatClearUserMessages(_ResponderEvent):
    """
    Represents a user's channel chat clear event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster's chat that had the user's messages cleared.
    user: PartialUser
        The user that was banned or put in a timeout and had all their messaged deleted.
    """

    subscription_type = "channel.chat.clear_user_messages"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelChatClearUserMessagesEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(
            payload["target_user_id"], payload["target_user_login"], payload["target_user_name"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChannelChatClearUserMessages broadcaster={self.broadcaster} user={self.user}>"


class ChatMessageReply:
    """
    Represents a chat message reply.

    Attributes
    ----------
    parent_message_id: str
        An ID that uniquely identifies the parent message that this message is replying to.
    parent_message_body: str
        The message body of the parent message.
    parent_user: PartialUser
        The sender of the parent message.
    thread_message_id: str
        An ID that identifies the parent message of the reply thread.
    thread_user: PartialUser
        The sender of the thread's parent message.
    """

    __slots__ = (
        "parent_message_body",
        "parent_message_id",
        "parent_user",
        "thread_message_id",
        "thread_user",
    )

    def __init__(self, data: ChatMessageReplyData, *, http: HTTPClient) -> None:
        self.parent_message_id: str = data["parent_message_id"]
        self.parent_message_body: str = data["parent_message_body"]
        self.parent_user: PartialUser = PartialUser(
            data["parent_user_id"], data["parent_user_login"], data["parent_user_name"], http=http
        )
        self.thread_message_id: str = data["thread_message_id"]
        self.thread_user: PartialUser = PartialUser(
            data["thread_user_id"], data["thread_user_login"], data["thread_user_name"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChatMessageReply parent_message_id={self.parent_message_id} parent_user={self.parent_user}>"


class ChatMessageCheer:
    """
    Represents a chat message cheer.

    Attributes
    ----------
    bits: int
        The amount of Bits the user cheered.
    """

    __slots__ = ("bits",)

    def __init__(self, data: ChatMessageCheerData) -> None:
        self.bits: int = int(data["bits"])

    def __repr__(self) -> str:
        return f"<ChatMessageCheer bits={self.bits}>"


class ChatMessageBadge:
    """
    Represents a chat message badge.

    Attributes
    ----------
    set_id: str
        An ID that identifies this set of chat badges. For example, Bits or Subscriber.
    id: str
        An ID that identifies this version of the badge. The ID can be any value.
        For example, for Bits, the ID is the Bits tier level, but for World of Warcraft, it could be Alliance or Horde.
    info: str
        Contains metadata related to the chat badges in the badges tag.
        Currently, this tag contains metadata only for subscriber badges, to indicate the number of months the user has been a subscriber.
    """

    __slots__ = ("id", "info", "set_id")

    def __init__(self, data: ChatMessageBadgeData) -> None:
        self.set_id: str = data["set_id"]
        self.id: str = data["id"]
        self.info: str = data["info"]

    def __repr__(self) -> str:
        return f"<ChatMessageBadge set_id={self.set_id} id={self.id} info={self.info}>"


class ChatMessageEmote:
    """
    Represents a chat message emote.

    Attributes
    ----------
    set_id: str | None
        An ID that identifies the emote set that the emote belongs to.
    id: str
        An ID that uniquely identifies this emote.
    owner: PartialUser | None
        The broadcaster who owns the emote.
    format: list[typing.Literal["static", "animated"]]
        The formats that the emote is available in. For example, if the emote is available only as a static PNG, the array contains only static.
        But if the emote is available as a static PNG and an animated GIF, the array contains static and animated. The possible formats are:

        - animated - An animated GIF is available for this emote.
        - static - A static PNG file is available for this emote.

    """

    __slots__ = ("_http", "format", "id", "owner", "set_id")

    def __init__(self, data: ChatMessageEmoteData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.set_id: str | None = data.get("emote_set_id")
        self.id: str = data["id"]
        owner_id: str | None = data.get("owner_id")
        self.owner: PartialUser | None = PartialUser(owner_id, None, http=http) if owner_id is not None else None
        self.format: list[Literal["static", "animated"]] = data.get("format", [])

    def __repr__(self) -> str:
        return f"<ChatMessageEmote set_id={self.set_id} id={self.id} owner={self.owner} format={self.format}>"

    async def fetch_emote_set(self, *, token_for: str | PartialUser | None = None) -> EmoteSet:
        """|coro|

        Fetches emotes for this emote set.

        Parameters
        ----------
        token_for : str | PartialUser | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        EmoteSet
            A list of EmoteSet objects.
        """
        data = await self._http.get_emote_sets(emote_set_ids=[self.set_id], token_for=token_for)
        return EmoteSet(data["data"][0], template=data["template"], http=self._http)


class ChatMessageCheermote:
    """
    Represents a chat message cheermote.

    Attributes
    ----------
    prefix: str
        The name portion of the Cheermote string that you use in chat to cheer Bits. The full Cheermote string is the concatenation of {prefix} + {number of Bits}.
        For example, if the prefix is “Cheer” and you want to cheer 100 Bits, the full Cheermote string is Cheer100.
        When the Cheermote string is entered in chat, Twitch converts it to the image associated with the Bits tier that was cheered.
    bits: int
        The amount of bits cheered.
    tier: int
        The tier level of the cheermote.
    """

    __slots__ = ("bits", "prefix", "tier")

    def __init__(self, data: ChatMessageCheermoteData) -> None:
        self.prefix: str = data["prefix"]
        self.bits: int = int(data["bits"])
        self.tier: int = int(data["tier"])

    def __repr__(self) -> str:
        return f"<ChatMessageCheermote prefix={self.prefix} bits={self.bits} tier={self.tier}>"


class ChatMessageFragment:
    """
    Represents a chat message's fragments.

    Attributes
    ----------
    text: str
        The chat message in plain text.
    type: typing.Literal["text", "cheermote", "emote", "mention"]
        The type of message fragment. Possible values:

        - text
        - cheermote
        - emote
        - mention

    mention: PartialUser | None
        The user that is mentioned, if one is mentioned.
    cheermote: ChatMessageCheermote | None
        Cheermote data if a cheermote is sent.
    emote: ChatMessageEmote | None
        Emote data if a cheermote is sent.
    """

    __slots__ = ("cheermote", "emote", "mention", "text", "type")

    def __init__(self, data: ChatMessageFragmentsData, *, http: HTTPClient) -> None:
        self.text = data["text"]
        self.type: Literal["text", "cheermote", "emote", "mention"] = data["type"]
        user = data.get("mention")
        self.mention: PartialUser | None = (
            PartialUser(user["user_id"], user["user_login"], user["user_name"], http=http) if user is not None else None
        )
        cheermote = data.get("cheermote")
        self.cheermote: ChatMessageCheermote | None = ChatMessageCheermote(cheermote) if cheermote is not None else None
        emote = data.get("emote")
        self.emote: ChatMessageEmote | None = ChatMessageEmote(emote, http=http) if emote else None

    def __repr__(self) -> str:
        return f"<ChatMessageFragment type={self.type} text={self.text}>"


class BaseChatMessage(_ResponderEvent):
    __slots__ = (
        "broadcaster",
        "fragments",
        "id",
        "text",
    )

    def __init__(
        self,
        payload: ChannelChatMessageEvent
        | ChatUserMessageHoldEvent
        | ChatUserMessageUpdateEvent
        | ChannelSuspiciousUserMessageEvent,
        *,
        http: HTTPClient,
    ) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.text: str = payload["message"]["text"]
        self.id = payload.get("message_id") or payload["message"].get("message_id")
        self.fragments: list[ChatMessageFragment] = [
            ChatMessageFragment(fragment, http=http) for fragment in payload["message"]["fragments"]
        ]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} broadcaster={self.broadcaster} id={self.id} text={self.text}>"

    @property
    def emotes(self) -> list[ChatMessageEmote]:
        """
        A property that lists all of the emotes of a message.
        If no emotes are in the message this will return an empty list.

        Returns
        -------
        list[ChatMessageEmote]
            A list of ChatMessageEmote objects.
        """
        return [f.emote for f in self.fragments if f.emote is not None]

    @property
    def cheermotes(self) -> list[ChatMessageCheermote]:
        """
        A property that lists all of the cheermotes of a message.
        If no cheermotes are in the message this will return an empty list.

        Returns
        -------
        list[ChatMessageCheermote]
            A list of ChatMessageCheermote objects.
        """
        return [f.cheermote for f in self.fragments if f.cheermote is not None]


class ChatMessage(BaseChatMessage):
    """
    Represents a chat message.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose room recieved the message.
    chatter: PartialUser
        The user / chatter who sent the message.
    id: str
        A UUID that identifies the message.
    text: str
        The chat message in plain text.
    reply: ChatMessageReply | None
        Data regarding parent message and thread, if this message is a reply.
    type: typing.Literal["text", "channel_points_highlighted", "channel_points_sub_only", "user_intro", "power_ups_message_effect", "power_ups_gigantified_emote"]
        The type of message. Possible values:

        - text
        - channel_points_highlighted
        - channel_points_sub_only
        - user_intro
        - power_ups_message_effect
        - power_ups_gigantified_emote

    fragments: ChatMessageFragment
        The chat message fragments.
    colour: Colour | None
        The colour of the user's name in the chat room.
    channel_points_id: str | None
        The ID of a channel points custom reward that was redeemed.
    channel_points_animation_id: str | None
        An ID for the type of animation selected as part of an “animate my message” redemption.
    cheer: ChatMessageCheer | None
        Data for a cheer, if received.
    badges: list[ChatMessageBadge]
        List of ChatMessageBadge for chat badges.
    source_broadcaster: PartialUser | None
        The broadcaster of the channel the message was sent from.
        Is `None` when the message happens in the same channel as the broadcaster.
        Is not `None` when in a shared chat session, and the action happens in the channel of a participant other than the broadcaster.
    source_id: str | None
        The source message ID from the channel the message was sent from.
        Is `None` when the message happens in the same channel as the broadcaster.
        Is not `None` when in a shared chat session, and the action happens in the channel of a participant other than the broadcaster.
    source_badges: list[ChatMessageBadge]
        The list of chat badges for the chatter in the channel the message was sent from.
        Is `None` when the message happens in the same channel as the broadcaster.
        Is not `None` when in a shared chat session, and the action happens in the channel of a participant other than the broadcaster.
    source_only: bool | None
        Whether a message delivered during a shared chat session is only sent to the source channel. This is `None` when not in a shared chat.
    """

    subscription_type = "channel.chat.message"

    __slots__ = (
        "badges",
        "channel_points_animation_id",
        "channel_points_id",
        "chatter",
        "cheer",
        "colour",
        "reply",
        "source_badges",
        "source_broadcaster",
        "source_id",
        "type",
    )

    def __init__(self, payload: ChannelChatMessageEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

        self.colour: Colour | None = Colour.from_hex(payload["color"]) if payload["color"] else None
        self.channel_points_id: str | None = payload["channel_points_custom_reward_id"]
        self.channel_points_animation_id: str | None = payload["channel_points_animation_id"]
        self.reply: ChatMessageReply | None = (
            ChatMessageReply(payload["reply"], http=http) if payload["reply"] is not None else None
        )
        self.type: Literal[
            "text",
            "channel_points_highlighted",
            "channel_points_sub_only",
            "user_intro",
            "power_ups_message_effect",
            "power_ups_gigantified_emote",
        ] = payload["message_type"]

        self.cheer: ChatMessageCheer | None = ChatMessageCheer(payload["cheer"]) if payload["cheer"] is not None else None
        self.badges: list[ChatMessageBadge] = [ChatMessageBadge(badge) for badge in payload["badges"]]
        self.source_broadcaster: PartialUser | None = (
            PartialUser(
                payload["source_broadcaster_user_id"],
                payload["source_broadcaster_user_login"],
                payload["source_broadcaster_user_name"],
                http=http,
            )
            if payload["source_broadcaster_user_id"] is not None
            else None
        )
        self.source_id: str | None = payload.get("source_message_id")
        self.source_badges: list[ChatMessageBadge] = [
            ChatMessageBadge(badge) for badge in (payload.get("source_badges") or [])
        ]
        self.source_only: bool | None = payload.get("is_source_only")
        self.chatter: Chatter = Chatter(payload, broadcaster=self.broadcaster, badges=self.badges, http=http)

    def __repr__(self) -> str:
        return f"<ChatMessage broadcaster={self.broadcaster} chatter={self.chatter} id={self.id} text={self.text}>"

    @property
    def mentions(self) -> list[PartialUser]:
        """List of PartialUsers of chatters who were mentioned in the message."""
        return [f.mention for f in self.fragments if f.mention is not None]

    @property
    def color(self) -> Colour | None:
        """An alias for colour"""
        return self.colour


class ChatSub:
    """
    Represents a chat subscription.

    Attributes
    ----------
    tier: typing.Literal["1000", "2000", "3000"]
        The type of subscription plan being used.

        +------+-----------------------------------------------+
        | Type | Description                                   |
        +======+===============================================+
        | 1000 | First level of paid or Prime subscription.    |
        +------+-----------------------------------------------+
        | 2000 | Second level of paid subscription.            |
        +------+-----------------------------------------------+
        | 3000 | Third level of paid subscription.             |
        +------+-----------------------------------------------+

    prime: bool
        Indicates if the subscription was obtained through Amazon Prime.
    months: int
        The number of months the subscription is for.
    """

    __slots__ = ("months", "prime", "tier")

    def __init__(self, data: ChatSubData) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.prime: bool = bool(data["is_prime"])
        self.months: int = int(data["duration_months"])

    def __repr__(self) -> str:
        return f"<ChatSub tier={self.tier} prime={self.prime} months={self.months}>"


class ChatResub:
    """
    Represents a chat resubscription.

    Attributes
    ----------
    tier: typing.Literal["1000", "2000", "3000"]
        The type of subscription plan being used.

        +------+-----------------------------------------------+
        | Type | Description                                   |
        +======+===============================================+
        | 1000 | First level of paid or Prime subscription.    |
        +------+-----------------------------------------------+
        | 2000 | Second level of paid subscription.            |
        +------+-----------------------------------------------+
        | 3000 | Third level of paid subscription.             |
        +------+-----------------------------------------------+

    prime: bool
        Indicates if the subscription was obtained through Amazon Prime.
    months: int
        The number of months the subscription is for.
    cumulative_months: int
        The total number of months the user has subscribed.
    streak_months: int
        The number of consecutive months the user's current subscription has been active.
        This is None if the user has opted out of sharing this information.
    gift: bool
        Whether or not the resub was a result of a gift.
    anonymous: bool | None
        Whether or not the gift was anonymous.
    gifter: PartialUser | None
        The user who gifted the subscription.
    """

    __slots__ = (
        "anonymous",
        "cumulative_months",
        "gift",
        "gifter",
        "months",
        "prime",
        "streak_months",
        "tier",
    )

    def __init__(self, data: ChatResubData, *, http: HTTPClient) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.prime: bool = bool(data["is_prime"])
        self.gift: bool = bool(data["is_gift"])
        self.months: int = int(data["duration_months"])
        self.cumulative_months: int = int(data["cumulative_months"])
        self.streak_months: int | None = int(data["streak_months"]) if data["streak_months"] is not None else None
        self.anonymous: bool | None = (
            bool(data["gifter_is_anonymous"]) if data.get("gifter_is_anonymous") is not None else None
        )
        gifter = data.get("gifter_user_id")
        self.gifter: PartialUser | None = (
            PartialUser(str(data["gifter_user_id"]), data["gifter_user_login"], data["gifter_user_name"], http=http)
            if gifter is not None
            else None
        )

    def __repr__(self) -> str:
        return f"<ChatResub tier={self.tier} prime={self.prime} months={self.months}>"


class ChatSubGift:
    """
    Represents a chat subscription gift.

    Attributes
    ----------
    tier: typing.Literal["1000", "2000", "3000"]
        The type of subscription plan being used.

        +------+-------------------------------------------+
        | Type | Description                               |
        +======+===========================================+
        | 1000 | First level of paid or Prime subscription.|
        +------+-------------------------------------------+
        | 2000 | Second level of paid subscription.        |
        +------+-------------------------------------------+
        | 3000 | Third level of paid subscription.         |
        +------+-------------------------------------------+

    months: int
        The number of months the subscription is for.
    cumulative_total: int | None
        The amount of gifts the gifter has given in this channel. `None` if anonymous.
    community_gift_id: int | None
        The ID of the associated community gift. `Mone` if not associated with a community gift.
    recipient: PartialUser
        The user who received the gift subscription.
    """

    __slots__ = ("community_gift_id", "cumulative_total", "months", "recipient", "tier")

    def __init__(self, data: ChatSubGiftData, *, http: HTTPClient) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.months: int = int(data["duration_months"])
        self.cumulative_total: int | None = int(data["cumulative_total"]) if data["cumulative_total"] is not None else None
        self.community_gift_id: str | None = data.get("community_gift_id")
        self.recipient: PartialUser = PartialUser(
            data["recipient_user_id"], data["recipient_user_login"], data["recipient_user_name"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChatSubGift tier={self.tier} months={self.months} recipient={self.recipient}>"


class ChatCommunitySubGift:
    """
    Represents a chat community subscription gift.

    Attributes
    ----------
    tier: typing.Literal["1000", "2000", "3000"]
        The type of subscription plan being used.

        +------+-------------------------------------------+
        | Type | Description                               |
        +======+===========================================+
        | 1000 | First level of paid or Prime subscription.|
        +------+-------------------------------------------+
        | 2000 | Second level of paid subscription.        |
        +------+-------------------------------------------+
        | 3000 | Third level of paid subscription.         |
        +------+-------------------------------------------+

    total: int
        Number of subscriptions being gifted.
    cumulative_total: int | None
        The amount of gifts the gifter has given in this channel. `None`` if anonymous.
    id: str
        The ID of the associated community gift. `Mone` if not associated with a community gift.
    """

    __slots__ = ("cumulative_total", "id", "tier", "total")

    def __init__(self, data: ChatCommunitySubGiftData) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]
        self.total: int = int(data["total"])
        self.cumulative_total: int | None = int(data["cumulative_total"]) if data["cumulative_total"] is not None else None
        self.id: str = data["id"]

    def __repr__(self) -> str:
        return f"<ChatCommunitySubGift id={self.id} tier={self.tier} total={self.total}>"


class ChatGiftPaidUpgrade:
    """
    Represents a paid chat subscription upgrade gift.

    Attributes
    ----------
    anonymous: bool
        Whether the gift was given anonymously.
    gifter: PartialUser | None
        The user who gifted the subscription. `None` if anonymous.
    """

    __slots__ = ("anonymous", "gifter")

    def __init__(self, data: ChatGiftPaidUpgradeData, *, http: HTTPClient) -> None:
        self.anonymous: bool = bool(data["gifter_is_anonymous"])
        gifter = data.get("gifter_user_id")
        self.gifter: PartialUser | None = (
            PartialUser(str(data["gifter_user_id"]), data["gifter_user_login"], data["gifter_user_name"], http=http)
            if gifter is not None
            else None
        )

    def __repr__(self) -> str:
        return f"<ChatGiftPaidUpgrade anonymous={self.anonymous} gifter={self.gifter}>"


class ChatPrimePaidUpgrade:
    """
    Represents a prime chat subscription upgrade.

    Attributes
    ----------
    tier: typing.Literal["1000", "2000", "3000"]
        The type of subscription plan being used.

        +------+-----------------------------------------------+
        | Type | Description                                   |
        +======+===============================================+
        | 1000 | First level of paid or Prime subscription.    |
        +------+-----------------------------------------------+
        | 2000 | Second level of paid subscription.            |
        +------+-----------------------------------------------+
        | 3000 | Third level of paid subscription.             |
        +------+-----------------------------------------------+
    """

    __slots__ = ("tier",)

    def __init__(self, data: ChatPrimePaidUpgradeData) -> None:
        self.tier: Literal["1000", "2000", "3000"] = data["sub_tier"]

    def __repr__(self) -> str:
        return f"<ChatPrimePaidUpgrade tier={self.tier}>"


class ChatRaid:
    """
    Represents a chat raid event.

    Attributes
    ----------
    user: PartialUser
        The user raiding this channel.
    viewer_count: int
        The number of viewers raiding this channel from the user's channel.
    profile_image: Asset
        Profile image, as an Asset, of the user raiding this channel.
    """

    __slots__ = ("profile_image", "user", "viewer_count")

    def __init__(self, data: ChatRaidData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.viewer_count = int(data["viewer_count"])
        self.profile_image: Asset = Asset(data["profile_image_url"], http=http)

    def __repr__(self) -> str:
        return f"<ChatRaid user={self.user} viewer_count={self.viewer_count}>"


class ChatPayItForward:
    """
    Represents a pay it forward gift subscription.

    Attributes
    ----------
    anonymous: bool
        Whether the gift was given anonymously.
    gifter: PartialUser | None
        The user who gifted the subscription. `None` if anonymous.
    """

    __slots__ = ("anonymous", "gifter")

    def __init__(self, data: ChatPayItForwardData, *, http: HTTPClient) -> None:
        self.anonymous: bool = bool(data["gifter_is_anonymous"])
        gifter = data.get("gifter_user_id")
        self.gifter: PartialUser | None = (
            PartialUser(str(data["gifter_user_id"]), data["gifter_user_login"], data["gifter_user_name"], http=http)
            if gifter is not None
            else None
        )

    def __repr__(self) -> str:
        return f"<ChatPayItForward anonymous={self.anonymous} gifter={self.gifter}>"


class ChatAnnouncement:
    """
    Represents a pay it forward gift subscription.

    Attributes
    ----------
    colour: typing.Literal["BLUE", "PURPLE", "ORANGE", "GREEN", "PRIMARY"]
        Colour of the announcement.
    """

    __slots__ = ("colour",)

    def __init__(self, data: ChatAnnouncementData) -> None:
        self.colour: Literal["BLUE", "PURPLE", "ORANGE", "GREEN", "PRIMARY"] = data["color"]

    @property
    def color(self) -> Literal["BLUE", "PURPLE", "ORANGE", "GREEN", "PRIMARY"]:
        """An alias for Colour"""
        return self.colour

    def __repr__(self) -> str:
        return f"<ChatAnnouncement colour={self.colour}>"


class ChatBitsBadgeTier:
    """
    Represents a bits badge tier.

    Attributes
    ----------
    tier: int
        The tier of the Bits badge the user just earned. For example, 100, 1000, or 10000.
    """

    __slots__ = ("tier",)

    def __init__(self, data: ChatBitsBadgeTierData) -> None:
        self.tier: int = int(data["tier"])

    def __repr__(self) -> str:
        return f"<ChatBitsBadgeTier tier={self.tier}>"


class ChatCharityDonation:
    """
    Represents a charity donation.

    Attributes
    ----------
    name: str
        Name of the charity.
    amount: CharityValues
        The amount of money donation. This includes currency and decimal places.
    """

    __slots__ = ("amount", "name")

    def __init__(self, data: ChatCharityDonationData) -> None:
        self.name: str = data["charity_name"]
        self.amount: CharityValues = CharityValues(data["amount"])

    def __repr__(self) -> str:
        return f"<ChatCharityDonation name={self.name}>"


class ChatNotification(_ResponderEvent):
    """
    Represents a chat notification.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster / channel that received the notification.
    chatter: PartialUser
        The chatter / user that sent the message.
    anonymous: bool
        Whether or not the chatter is anonymous.
    colour: Colour
        The colour of the chatter / user's name in the chat room.
    badges: list[ChatMessageBadge]
        A list of badges the chatter / user has.
    system_message: str
        The message Twitch shows in the chat room for this notice.
    id: str
        The message ID (This is a UUID).
    text: str
        The chat message in plain text.
    fragments: list[ChatMessageFragment]
        A list of chat fragments, each containing structured data related to the messages, such as:

            - text
            - cheermote
            - emote
            - mention

    notice_type: typing.Literal["sub", "resub", "sub_gift", "community_sub_gift", "gift_paid_upgrade", "prime_paid_upgrade", "raid", "unraid", "pay_it_forward", "announcement", "bits_badge_tier", "charity_donation", "shared_chat_sub", "shared_chat_resub", "shared_chat_community_sub_gift", "shared_chat_gift_paid_upgrade", "shared_chat_prime_paid_upgrade", "shared_chat_raid", "shared_chat_pay_it_forward", "shared_chat_announcement"]
        The type of notice. Possible values are:

            - sub
            - resub
            - sub_gift
            - community_sub_gift
            - gift_paid_upgrade
            - prime_paid_upgrade
            - raid
            - unraid
            - pay_it_forward
            - announcement
            - bits_badge_tier
            - charity_donation
            - shared_chat_sub
            - shared_chat_resub
            - shared_chat_community_sub_gift
            - shared_chat_gift_paid_upgrade
            - shared_chat_prime_paid_upgrade
            - shared_chat_raid
            - shared_chat_pay_it_forward
            - shared_chat_announcement

    sub: ChatSub | None
        Information about the sub event. `None` if `notice_type` is not `sub`.
    resub: ChatResub | None
        Information about the resub event. `None` if `notice_type` is not `resub`.
    sub_gift: ChatSubGift | None
                Information about the gift sub event. `None` if `notice_type` is not `sub_gift`.
    community_sub_gift: ChatCommunitySubGift | None
        Information about the community gift sub event. `None` if `notice_type` is not `community_sub_gift`.
    gift_paid_upgrade: ChatGiftPaidUpgrade | None
        nformation about the community gift paid upgrade event. `None` if `notice_type` is not `gift_paid_upgrade`.
    prime_paid_upgrade: ChatPrimePaidUpgrade | None
        Information about the Prime gift paid upgrade event. `None` if `notice_type` is not `prime_paid_upgrade`.
    raid: ChatRaid | None
        Information about the raid event. `None` if `notice_type` is not `raid`.
    unraid: None
        Returns None as this is an empty payload. You will need to check the `notice_type`.
    pay_it_forward: ChatPayItForward | None
        Information about the pay it forward event. `None` if `notice_type` is not `pay_it_forward`
    announcement: ChatAnnouncement | None
        Information about the announcement event. `None` if `notice_type` is not `announcement`
    bits_badge_tier: ChatBitsBadgeTier | None
        Information about the bits badge tier event. `None` if `notice_type` is not `bits_badge_tier`
    charity_donation: ChatCharityDonation
        Information about the announcement event. `None` if `notice_type` is not `charity_donation`
    shared_sub: ChatSub | None
        Information about the shared_chat_sub event. Is `None` if `notice_type` is not `shared_chat_sub`.
        This field has the same information as the sub field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_resub: ChatResub | None
        Information about the shared_chat_resub event. Is `None` if `notice_type` is not `shared_chat_resub`.
        This field has the same information as the resub field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_sub_gift: ChatSubGift | None
        Information about the shared_chat_sub_gift event. Is `None` if `notice_type` is not `shared_chat_sub_gift`.
        This field has the same information as the chat_sub_gift field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_community_sub_gift: ChatCommunitySubGift | None
        Information about the shared_chat_community_sub_gift event. Is `None` if `notice_type` is not `shared_chat_community_sub_gift`.
        This field has the same information as the community_sub_gift field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_gift_paid_upgrade: ChatGiftPaidUpgrade | None
        Information about the shared_chat_gift_paid_upgrade event. Is `None` if `notice_type` is not `shared_chat_gift_paid_upgrade`.
        This field has the same information as the gift_paid_upgrade field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_prime_paid_upgrade: ChatPrimePaidUpgrade | None
        Information about the shared_chat_chat_prime_paid_upgrade event. Is `None` if `notice_type` is not `shared_chat_prime_paid_upgrade`.
        This field has the same information as the prime_paid_upgrade field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_raid: ChatRaid | None
        Information about the shared_chat_raid event. Is `None` if `notice_type` is not `shared_chat_raid`.
        This field has the same information as the raid field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_pay_it_forward: ChatPayItForward | None
        Information about the shared_chat_pay_it_forward event. Is `None` if `notice_type` is not `shared_chat_pay_it_forward`.
        This field has the same information as the pay_it_forward field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_announcement: ChatAnnouncement | None
        Information about the shared_chat_announcement event. Is `None` if `notice_type` is not `shared_chat_announcement`.
        This field has the same information as the announcement field but for a notice that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    """

    subscription_type = "channel.chat.notification"

    __slots__ = (
        "announcement",
        "anonymous",
        "badges",
        "bits_badge_tier",
        "broadcaster",
        "charity_donation",
        "chatter",
        "colour",
        "community_sub_gift",
        "fragments",
        "gift_paid_upgrade",
        "id",
        "notice_type",
        "pay_it_forward",
        "prime_paid_upgrade",
        "raid",
        "resub",
        "shared_chat_announcement",
        "shared_chat_community_sub_gift",
        "shared_chat_gift_paid_upgrade",
        "shared_chat_pay_it_forward",
        "shared_chat_prime_paid_upgrade",
        "shared_chat_raid",
        "shared_chat_resub",
        "shared_chat_sub",
        "shared_chat_sub_gift",
        "sub",
        "sub_gift",
        "system_message",
        "text",
        "unraid",
    )

    def __init__(self, payload: ChannelChatNotificationEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.chatter: PartialUser = PartialUser(
            payload["chatter_user_id"], payload["chatter_user_login"], payload["chatter_user_name"], http=http
        )
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
        self.unraid: None = None
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
        self.shared_sub: ChatSub | None = (
            ChatSub(payload["shared_chat_sub"]) if payload["shared_chat_sub"] is not None else None
        )
        self.shared_resub: ChatResub | None = (
            ChatResub(payload["shared_chat_resub"], http=http) if payload["shared_chat_resub"] is not None else None
        )
        self.shared_sub_gift: ChatSubGift | None = (
            ChatSubGift(payload["shared_chat_sub_gift"], http=http) if payload["shared_chat_sub_gift"] is not None else None
        )
        self.shared_community_sub_gift: ChatCommunitySubGift | None = (
            ChatCommunitySubGift(payload["shared_chat_community_sub_gift"])
            if payload["shared_chat_community_sub_gift"] is not None
            else None
        )
        self.shared_gift_paid_upgrade: ChatGiftPaidUpgrade | None = (
            ChatGiftPaidUpgrade(payload["shared_chat_gift_paid_upgrade"], http=http)
            if payload["shared_chat_gift_paid_upgrade"] is not None
            else None
        )
        self.shared_prime_paid_upgrade: ChatPrimePaidUpgrade | None = (
            ChatPrimePaidUpgrade(payload["shared_chat_prime_paid_upgrade"])
            if payload["shared_chat_prime_paid_upgrade"] is not None
            else None
        )
        self.shared_raid: ChatRaid | None = (
            ChatRaid(payload["shared_chat_raid"], http=http) if payload["shared_chat_raid"] is not None else None
        )
        self.shared_pay_it_forward: ChatPayItForward | None = (
            ChatPayItForward(payload["shared_chat_pay_it_forward"], http=http)
            if payload["shared_chat_pay_it_forward"] is not None
            else None
        )
        self.shared_announcement: ChatAnnouncement | None = (
            ChatAnnouncement(payload["shared_chat_announcement"])
            if payload["shared_chat_announcement"] is not None
            else None
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
            "shared_chat_sub",
            "shared_chat_resub",
            "shared_chat_sub_gift",
            "shared_chat_community_sub_gift",
            "shared_chat_gift_paid_upgrade",
            "shared_chat_prime_paid_upgrade",
            "shared_chat_raid",
            "shared_chat_pay_it_forward",
            "shared_chat_announcement",
        ] = payload["notice_type"]

    @property
    def color(self) -> Colour | None:
        return self.colour

    def __repr__(self) -> str:
        return f"<ChatNotification broadcaster={self.broadcaster} chatter={self.chatter} id={self.id} text={self.text}>"


class ChatMessageDelete(_ResponderEvent):
    """
    Represents a chat message delete event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel deleted the message.
    user: PartialUser
        The user whose message was deleted.
    message_id: str
        The message ID of the deleted message.
    """

    subscription_type = "channel.chat.message_delete"

    __slots__ = ("broadcaster", "message_id", "user")

    def __init__(self, payload: ChannelChatMessageDeleteEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(
            payload["target_user_id"], payload["target_user_login"], payload["target_user_name"], http=http
        )
        self.message_id: str = payload["message_id"]

    def __repr__(self) -> str:
        return f"<ChatMessageDelete broadcaster={self.broadcaster} user={self.user} message_id={self.message_id}>"


class ChatSettingsUpdate(_ResponderEvent):
    """
    Represents a chat settings update event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel updated their chat settings.
    emote_mode: bool
        Whether chat messages must contain only emotes.
    slow_mode: bool
        Whether the broadcaster limits how often users in the chat room are allowed to send messages.
    slow_mode_wait_time: int | None
        The amount of time, in seconds, that users need to wait between sending messages. `None` if `slow_mode` is False.
    follower_mode: bool
        Whether the broadcaster restricts the chat room to followers only, based on how long they've followed.
    follower_mode_duration: int | None
        The length of time, in minutes, that the followers must have followed the broadcaster to participate in the chat room.
        `None` if `follower_mode` is False.
    subscriber_mode: bool
        Whether only users that subscribe to the broadcaster's channel can talk in the chat room.
    unique_chat_mode: bool
        Whether the broadcaster requires users to post only unique messages in the chat room.
    """

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
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
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

    __slots__ = ("user",)

    def __init__(self, payload: ChatUserMessageHoldEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<ChatUserMessageHold broadcaster={self.broadcaster} user={self.user} id={self.id} text={self.text}>"

    @property
    def full_message(self) -> str:
        return " ".join(fragment.text for fragment in self.fragments if fragment.type == "text")


class ChatUserMessageUpdate(BaseChatMessage):
    subscription_type = "channel.chat.user_message_update"

    __slots__ = ("status", "user")

    def __init__(self, payload: ChatUserMessageUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.status: Literal["approved", "denied", "invalid"] = payload["status"]

    def __repr__(self) -> str:
        return f"<ChatUserMessageUpdate broadcaster={self.broadcaster} user={self.user} id={self.id} text={self.text}>"

    @property
    def full_message(self) -> str:
        return " ".join(fragment.text for fragment in self.fragments if fragment.type == "text")


class BaseSharedChatSession(_ResponderEvent):
    __slots__ = (
        "broadcaster",
        "host",
        "session_id",
    )

    def __init__(
        self,
        payload: ChannelSharedChatSessionBeginEvent | ChannelSharedChatSessionUpdateEvent | ChannelSharedChatSessionEndEvent,
        *,
        http: HTTPClient,
    ) -> None:
        self.session_id: str = payload["session_id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.host: PartialUser = PartialUser(
            payload["host_broadcaster_user_id"],
            payload["host_broadcaster_user_login"],
            payload["host_broadcaster_user_name"],
            http=http,
        )

    def __repr__(self) -> str:
        return f"<BaseSharedChatSession session_id={self.session_id} broadcaster={self.broadcaster} host={self.host}>"


class SharedChatSessionBegin(BaseSharedChatSession):
    """
    Represents a shared chat session begin event.

    Attributes
    ----------
    session_id: PartialUser
        The unique identifier for the shared chat session.
    broadcaster: PartialUser
        The user of the channel in the subscription condition which is now active in the shared chat session.
    host: PartialUser
        The user of the host channel.
    participants: str
        List of participants in the session.
    """

    subscription_type = "channel.shared_chat.begin"

    __slots__ = ("participants",)

    def __init__(self, payload: ChannelSharedChatSessionBeginEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.participants: list[PartialUser] = [
            PartialUser(p["broadcaster_user_id"], p["broadcaster_user_login"], payload["broadcaster_user_name"], http=http)
            for p in payload["participants"]
        ]

    def __repr__(self) -> str:
        return f"<BaseSharedChatSession session_id={self.session_id} broadcaster={self.broadcaster} host={self.host}>"


class SharedChatSessionUpdate(BaseSharedChatSession):
    """
    Represents a shared chat session begin event.

    Attributes
    ----------
    session_id: PartialUser
        The unique identifier for the shared chat session.
    broadcaster: PartialUser
        The user of the channel in the subscription condition which is now active in the shared chat session.
    host: PartialUser
        The user of the host channel.
    participants: str
        List of participants in the session.
    """

    subscription_type = "channel.shared_chat.update"

    __slots__ = ("participants",)

    def __init__(self, payload: ChannelSharedChatSessionUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.participants: list[PartialUser] = [
            PartialUser(p["broadcaster_user_id"], p["broadcaster_user_login"], payload["broadcaster_user_name"], http=http)
            for p in payload["participants"]
        ]

    def __repr__(self) -> str:
        return f"<SharedChatSessionUpdate session_id={self.session_id} broadcaster={self.broadcaster} host={self.host}>"


class SharedChatSessionEnd(BaseSharedChatSession):
    """
    Represents a shared chat session end event.

    Attributes
    ----------
    session_id: PartialUser
        The unique identifier for the shared chat session.
    broadcaster: PartialUser
        The user of the channel in the subscription condition which is no longer active in the shared chat session.
    host: PartialUser
        The user of the host channel.
    """

    subscription_type = "channel.shared_chat.end"

    def __init__(self, payload: ChannelSharedChatSessionUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<SharedChatSessionEnd session_id={self.session_id} broadcaster={self.broadcaster} host={self.host}>"


class ChannelSubscribe(_ResponderEvent):
    """
    Represents a channel subscribe event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel received a subscription.
    user: PartialUser
        The user who subscribed to the channel.
    tier: typing.Literal["1000", "2000", "3000"]
        The tier of the subscription. Valid values are 1000, 2000, and 3000.
    gift: bool
        Whether the subscription is a gift.
    """

    subscription_type = "channel.subscribe"

    __slots__ = (
        "broadcaster",
        "gift",
        "tier",
        "user",
    )

    def __init__(self, payload: ChannelSubscribeEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.tier: Literal["1000", "2000", "3000"] = payload["tier"]
        self.gift: bool = bool(payload["is_gift"])

    def __repr__(self) -> str:
        return f"<ChannelSubscribe broadcaster={self.broadcaster} user={self.user} tier={self.tier} gift={self.gift}>"


class ChannelSubscriptionEnd(_ResponderEvent):
    """
    Represents a channel subscription end event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had the subscription end.
    user: PartialUser
        The user whose subscription ended.
    tier: typing.Literal["1000", "2000", "3000"]
        The tier of the subscription that ended. Valid values are 1000, 2000, and 3000.
    gift: bool
        Whether the subscription was a gift.
    """

    subscription_type = "channel.subscription.end"

    __slots__ = (
        "broadcaster",
        "gift",
        "tier",
        "user",
    )

    def __init__(self, payload: ChannelSubscriptionEndEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.tier: Literal["1000", "2000", "3000"] = payload["tier"]
        self.gift: bool = bool(payload["is_gift"])

    def __repr__(self) -> str:
        return f"<ChannelSubscriptionEnd broadcaster={self.broadcaster} user={self.user} tier={self.tier} gift={self.gift}>"


class ChannelSubscriptionGift(_ResponderEvent):
    """
    Represents a channel subscription gift event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel received the gift subscriptions.
    user: PartialUser | None
        The user who sent the gift. `None` if it was an anonymous subscription gift.
    tier: typing.Literal["1000", "2000", "3000"]
        The tier of the subscription that ended. Valid values are 1000, 2000, and 3000.
    total: int
        The number of subscriptions in the subscription gift.
    anonymous: bool
        Whether the subscription gift was anonymous.
    cumulative_total: int | None
        The number of subscriptions gifted by this user in the channel.
        This is `None` for anonymous gifts or if the gifter has opted out of sharing this information
    """

    subscription_type = "channel.subscription.gift"

    __slots__ = ("anonymous", "broadcaster", "cumulative_total", "tier", "total", "user")

    def __init__(self, payload: ChannelSubscriptionGiftEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser | None = (
            PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
            if payload["user_id"] is not None
            else None
        )
        self.tier: Literal["1000", "2000", "3000"] = payload["tier"]
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
        return f"<BaseEmote id={self.id} begin={self.begin} end={self.end}>"


class SubscribeEmote(BaseEmote):
    """
    Represents a subscription emote.

    Attributes
    ----------
    begin: int
        The index of where the emote starts in the text.
    end: int
        The index of where the emote ends in the text.
    id: str
        The emote ID.
    """

    def __init__(self, data: SubscribeEmoteData) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<SubscribeEmote id={self.id} begin={self.id} end={self.end}>"


class ChannelSubscriptionMessage(_ResponderEvent):
    """
    Represents a subscription message event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel received a subscription message.
    user: PartialUser
        The user who sent a resubscription chat message.
    tier: typing.Literal["1000", "2000", "3000"]
        The tier of the user's subscription. Valid values are 1000, 2000, and 3000.
    months: str
        The month duration of the subscription.
    cumulative_months: int
        The total number of months the user has been subscribed to the channel.
    streak_months: int | None
        The number of consecutive months the user's current subscription has been active.
        `None` if the user has opted out of sharing this information
    text: str
        The text of the resubscription chat message.
    emotes: list[SubscribeEmote]
        List of emote information for the subscription message. This includes start and end positions for where the emote appears in the text.
    """

    subscription_type = "channel.subscription.message"

    __slots__ = ("broadcaster", "cumulative_months", "message", "months", "streak_months", "tier", "user")

    def __init__(self, payload: ChannelSubscribeMessageEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.tier: Literal["1000", "2000", "3000"] = payload["tier"]
        self.months: int = int(payload["duration_months"])
        self.cumulative_months: int = int(payload["cumulative_months"])
        self.streak_months: int | None = int(payload["streak_months"]) if payload["streak_months"] is not None else None
        self.text: str = payload["message"]["text"]
        emotes = payload.get("message", {}).get("emotes", [])
        self.emotes: list[SubscribeEmote] = [SubscribeEmote(emote) for emote in emotes] if emotes is not None else []

    def __repr__(self) -> str:
        return f"<ChannelSubscriptionMessage broadcaster={self.broadcaster} user={self.user} text={self.text}>"


class ChannelCheer(_ResponderEvent):
    """
    Represents a channel cheer event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel received a cheer.
    user: PartialUser | None
        The user who cheered on the specified channel. `None` if anonymous is true.
    anonymous: bool
        Whether the user cheered anonymously or not.
    bits: int
        The number of bits cheered.
    message: str
        The message sent with the cheer.
    """

    subscription_type = "channel.cheer"

    __slots__ = ("anonymous", "bits", "broadcaster", "message", "user")

    def __init__(self, payload: ChannelCheerEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.anonymous: bool = bool(payload["is_anonymous"])
        self.bits: int = int(payload["bits"])
        self.message: str = payload["message"]
        self.user: PartialUser | None = (
            PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
            if payload["user_id"] is not None
            else None
        )

    def __repr__(self) -> str:
        return f"<ChannelCheer broadcaster={self.broadcaster} user={self.user} bits={self.bits} message={self.message}>"


class ChannelRaid(BaseEvent):
    """
    Represents a channel raid event.

    Attributes
    ----------
    from_broadcaster: PartialUser
        The broadcaster whose channel started a raid.
    to_broadcaster: PartialUser
        The broadcaster whose channel is being raided.
    viewer_count: int
        The number of viewers in the raid.
    """

    subscription_type = "channel.raid"

    __slots__ = ("from_broadcaster", "to_broadcaster", "viewer_count")

    def __init__(self, payload: ChannelRaidEvent, *, http: HTTPClient) -> None:
        self.from_broadcaster: PartialUser = PartialUser(
            payload["from_broadcaster_user_id"],
            payload["from_broadcaster_user_login"],
            payload["from_broadcaster_user_name"],
            http=http,
        )
        self.to_broadcaster: PartialUser = PartialUser(
            payload["to_broadcaster_user_id"],
            payload["to_broadcaster_user_login"],
            payload["to_broadcaster_user_name"],
            http=http,
        )
        self.viewer_count: int = int(payload["viewers"])

    def __repr__(self) -> str:
        return f"<ChannelRaid from_broadcaster={self.from_broadcaster} to_broadcaster={self.to_broadcaster} viewer_count={self.viewer_count}>"


class ChannelBan(_ResponderEvent):
    """
    Represents a channel ban event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel banned a user.
    user: PartialUser
        The user who was banned on the specified channel.
    moderator: PartialUser
        The moderator who banned the user.
    reason: str
        The reason behind the ban.
    banned_at: datetime.datetime
        The datetime of when the user was banned or put in a timeout.
    ends_at: datetime.datetime | None
        The datetime of when the timeout ends. `None` if the user was banned instead of put in a timeout
    permanent: bool
        Indicates whether the ban is permanent (True) or a timeout (False). If True, `ends_at` will be `None`.
    """

    subscription_type = "channel.ban"

    __slots__ = ("banned_at", "broadcaster", "ends_at", "moderator", "permanent", "reason", "user")

    def __init__(self, payload: ChannelBanEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], http=http)
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.reason: str = payload["reason"]
        self.banned_at: datetime.datetime = parse_timestamp(payload["banned_at"])
        self.ends_at: datetime.datetime | None = (
            parse_timestamp(payload["ends_at"]) if payload["ends_at"] is not None else None
        )
        self.permanent: bool = bool(payload["is_permanent"])

    def __repr__(self) -> str:
        return f"<ChannelBan broadcaster={self.broadcaster} user={self.user} moderator={self.moderator} banned_at={self.banned_at}>"


class ChannelUnban(_ResponderEvent):
    """
    Represents a channel unban event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel unbanned a user.
    user: PartialUser
        The user who was unbanned on the specified channel.
    moderator: PartialUser
        The moderator who unbanned the user.
    """

    subscription_type = "channel.unban"

    __slots__ = ("broadcaster", "moderator", "user")

    def __init__(self, payload: ChannelUnbanEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )

    def __repr__(self) -> str:
        return f"<ChannelUnban broadcaster={self.broadcaster} user={self.user} moderator={self.moderator}>"


class ChannelUnbanRequest(_ResponderEvent):
    """
    Represents a channel unban request event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel received an unban request.
    user: PartialUser
        The user that is requesting to be unbanned.
    id: str
        The ID of the unban request.
    text: str
        The message sent in the unban request.
    created_at: datetime.datetime
        The datetime of when the unban request was created.
    """

    subscription_type = "channel.unban_request.create"

    __slots__ = ("broadcaster", "created_at", "id", "text", "user")

    def __init__(self, payload: ChannelUnbanRequestEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.id: str = payload["id"]
        self.text: str = payload["text"]
        self.created_at: datetime.datetime = parse_timestamp(payload["created_at"])

    def __repr__(self) -> str:
        return f"<ChannelUnbanRequest broadcaster={self.broadcaster} user={self.user} id={self.id}>"


class ChannelUnbanRequestResolve(_ResponderEvent):
    """
    Represents a channel unban request resolve event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel resolved an unban request.
    user: PartialUser
        The user that is requesting to be unbanned.
    moderator: PartialUser | None
        The moderator who approved/denied the request. This is None is the user is unbanned (/unban) via chat.
    id: str
        The ID of the unban request.
    text: str
        The message sent in the unban request.
    status: typing.Literal["approved", "canceled", "denied"]
        Whether the unban request was approved or denied. Can be the following:

        - approved
        - canceled
        - denied
    """

    subscription_type = "channel.unban_request.resolve"

    __slots__ = ("broadcaster", "id", "status", "text", "user")

    def __init__(self, payload: ChannelUnbanRequestResolveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.moderator: PartialUser | None = (
            PartialUser(
                payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
            )
            if payload["moderator_user_id"] is not None
            else None
        )
        self.id: str = payload["id"]
        self.text: str = payload["resolution_text"]
        self.status: Literal["approved", "canceled", "denied"] = payload["status"]

    def __repr__(self) -> str:
        return (
            f"<ChannelUnbanRequestResolve broadcaster={self.broadcaster} user={self.user} id={self.id} status={self.status}>"
        )


class ModerateFollowers:
    """
    Represents data associated with the followers command.

    Attributes
    ----------
    follow_duration: int
        The length of time, in minutes, that the followers must have followed the broadcaster to participate in the chat room.
    """

    __slots__ = ("follow_duration",)

    def __init__(self, data: ModerateFollowersData) -> None:
        self.follow_duration: int = int(data["follow_duration_minutes"])

    def __repr__(self) -> str:
        return f"<ModerateFollowers follow_duration={self.follow_duration}>"


class ModerateBan:
    """
    Represents data associated with the ban command.

    Attributes
    ----------
    user: PartialUser
        The user being banned.
    reason: str | None
        Reason given for the ban.
    """

    __slots__ = ("reason", "user")

    def __init__(self, data: ModerateBanData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.reason: str | None = data.get("reason")

    def __repr__(self) -> str:
        return f"<ModerateBan user={self.user} reason={self.reason}>"


class ModerateTimeout:
    """
    Represents data associated with the timeout command.

    Attributes
    ----------
    user: PartialUser
        The user being timed out.
    reason: str | None
        Reason given for the timeout.
    expires_at: datetime.datetime
        The time at which the timeout ends.
    """

    __slots__ = ("expires_at", "reason", "user")

    def __init__(self, data: ModerateTimeoutData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.reason: str | None = data.get("reason")
        self.expires_at: datetime.datetime = parse_timestamp(data["expires_at"])

    def __repr__(self) -> str:
        return f"<ModerateTimeout user={self.user} expires_at={self.expires_at}>"


class ModerateSlow:
    """
    Represents data associated with the slow command.

    Attributes
    ----------
    wait_time: int
        The amount of time, in seconds, that users need to wait between sending messages.
    """

    __slots__ = ("wait_time",)

    def __init__(self, data: ModerateSlowData) -> None:
        self.wait_time: int = int(data["wait_time_seconds"])

    def __repr__(self) -> str:
        return f"<ModerateSlow wait_time={self.wait_time}>"


class ModerateRaid:
    """
    Represents data associated with the raid command.

    Attributes
    ----------
    user: PartialUser
        The user being raided.
    viewer_count: int
        The viewer count.
    """

    __slots__ = ("user", "viewer_count")

    def __init__(self, data: ModerateRaidData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.viewer_count: int = int(data["viewer_count"])

    def __repr__(self) -> str:
        return f"<ModerateRaid user={self.user} viewer_count={self.viewer_count}>"


class ModerateDelete:
    """
    Represents data associated with the delete command.

    Attributes
    ----------
    user: PartialUser
        The user whose message is being deleted.
    message_id: str
        The ID of the message being deleted.
    text: str
        The text of the message being deleted.
    """

    __slots__ = ("message_id", "text", "user")

    def __init__(self, data: ModerateDeleteData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.message_id: str = data["message_id"]
        self.text: str = data["message_body"]

    def __repr__(self) -> str:
        return f"<ModerateDelete user={self.user} message_id={self.message_id} text={self.text}>"


class ModerateAutomodTerms:
    """
    Represents data associated with the automod terms changes.

    Attributes
    ----------
    action: typing.Literal["add", "remove"]
        Either “add” or “remove”.
    list: typing.Literal["blocked", "permitted"]
        Either “blocked” or “permitted”.
    terms: list[str]
        Terms being added or removed.
    from_automod: bool
        Whether the terms were added due to an Automod message approve/deny action.
    """

    __slots__ = ("action", "from_automod", "list", "terms")

    def __init__(self, data: ModerateAutoModTermsData) -> None:
        self.action: Literal["add", "remove"] = data["action"]
        self.list: Literal["blocked", "permitted"] = data["list"]
        self.terms: list[str] = data["terms"]
        self.from_automod: bool = bool(data["from_automod"])

    def __repr__(self) -> str:
        return f"<ModerateAutomodTerms action={self.action} list={self.list} terms={self.terms} from_automod={self.from_automod}>"


class ModerateUnbanRequest:
    """
    Represents data associated with an unban request.

    Attributes
    ----------
    approved: bool
        Whether or not the unban request was approved or denied.
    user: PartialUser
        The banned user.
    text: str
        The message included by the moderator explaining their approval or denial.
    """

    __slots__ = ("approved", "text", "user")

    def __init__(self, data: ModerateUnbanRequestData, *, http: HTTPClient) -> None:
        self.approved: bool = bool(data["is_approved"])
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.text: str = data["moderator_message"]

    def __repr__(self) -> str:
        return f"<ModerateUnbanRequest approved={self.approved} user={self.user} text={self.text}>"


class ModerateWarn:
    """
    Represents data associated with the warn command.

    Attributes
    ----------
    user: PartialUser
        The user being warned.
    reason: str | None
        Reason given for the warning.
    chat_rules: list[str]
        Chat rules cited for the warning.
    """

    __slots__ = ("chat_rules", "reason", "user")

    def __init__(self, data: ModerateWarnData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.reason: str | None = data.get("reason")
        self.chat_rules: list[str] | None = data.get("chat_rules_cited")

    def __repr__(self) -> str:
        return f"<ModerateWarn user={self.user} reason={self.reason} chat_rules={self.chat_rules}>"


class ChannelModerate(_ResponderEvent):
    """
    Represents a channel moderate event, both V1 and V2.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster who had a moderate event occur.
    source_broadcaster: PartialUser
        The channel in which the action originally occurred. Is the same as `broadcaster` if not in shared chat.
    moderator: PartialUser
        The moderator who performed the action.
    followers: ModerateFollowers | None
        Information associated with the followers command.
    slow: ModerateSlow | None
        Information associated with the slow command.
    vip: PartialUser | None
        Information associated with the vip command.
    unvip: PartialUser | None
        Information associated with the unvip command.
    mod: PartialUser | None
        Information associated with the mod command.
    unmod: PartialUser | None
        Information associated with the unmod command.
    ban: ModerateBan | None
        Information associated with the ban command.
    unban: PartialUser | None
        Information associated with the unban command.
    timeout: ModerateTimeout | None
        Information associated with the timeout command.
    untimeout: PartialUser | None
        Information associated with the untimeout command.
    raid: ModerateRaid | None
        Information associated with the raid command.
    unraid: PartialUser | None
        Information associated with the unraid command.
    delete: ModerateDelete | None
        Information associated with the delete command.
    automod_terms: ModerateAutomodTerms | None
        Information associated with the automod terms changes.
    unban_request: ModerateUnbanRequest | None
        Information associated with an unban request.
    shared_ban: ModerateBan | None
        Information about the shared_chat_ban event.
        Is `None` if action is not shared_chat_ban.
        This field has the same information as the ban field but for a action that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_unban: PartialUser | None
        Information about the shared_chat_unban event.
        Is `None` if action is not shared_chat_unban.
        This field has the same information as the unban field but for a action that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_timeout: ModerateTimeout | None
        Information about the shared_chat_timeout event.
        Is `None` if action is not shared_chat_timeout.
        This field has the same information as the timeout field but for a action that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_untimeout: PartialUser | None
        Information about the shared_chat_untimeout event.
        Is `None` if action is not shared_chat_untimeout.
        This field has the same information as the untimeout field but for a action that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    shared_delete: ModerateDelete | None
        Information about the shared_chat_delete event.
        Is `None` if action is not shared_chat_delete.
        This field has the same information as the delete field but for a action that happened for a channel in a shared chat session other than the broadcaster in the subscription condition.
    action: typing.Literal["ban","timeout", "unban", "untimeout", "clear", "emoteonly", "emoteonlyoff", "followers", "followersoff", "uniquechat", "uniquechatoff", "slow", "slowoff", "subscribers", "subscribersoff", "unraid", "delete", "unvip", "vip", "raid", "add_blocked_term", "add_permitted_term", "remove_blocked_term", "remove_permitted_term", "mod", "unmod", "approve_unban_request", "deny_unban_request", "warn", "shared_chat_ban", "shared_chat_unban", "shared_chat_timeout", "shared_chat_untimeout", "shared_chat_delete"]
        The type of action. `warn` is only available with V2.

        - ban
        - timeout
        - unban
        - untimeout
        - clear
        - emoteonly
        - emoteonlyoff
        - followers
        - followersoff
        - uniquechat
        - uniquechatoff
        - slow
        - slowoff
        - subscribers
        - subscribersoff
        - unraid
        - delete
        - unvip
        - vip
        - raid
        - add_blocked_term
        - add_permitted_term
        - remove_blocked_term
        - remove_permitted_term
        - mod
        - unmod
        - approve_unban_request
        - deny_unban_request
        - warn
        - shared_chat_ban
        - shared_chat_unban
        - shared_chat_timeout
        - shared_chat_untimeout
        - shared_chat_delete
    """

    subscription_type = "channel.moderate"

    __slots__ = (
        "action",
        "automod_terms",
        "ban",
        "broadcaster",
        "delete",
        "followers",
        "mod",
        "moderator",
        "raid",
        "shared_ban",
        "shared_delete",
        "shared_timeout",
        "shared_unban",
        "shared_untimeout",
        "slow",
        "source_broadcaster",
        "timeout",
        "unban",
        "unban_request",
        "unmod",
        "unraid",
        "untimeout",
        "unvip",
        "vip",
    )

    def __init__(self, payload: ChannelModerateEvent | ChannelModerateEventV2, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.source_broadcaster: PartialUser = PartialUser(
            payload["source_broadcaster_user_id"],
            payload["source_broadcaster_user_login"],
            payload["source_broadcaster_user_name"],
            http=http,
        )
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.followers: ModerateFollowers | None = (
            ModerateFollowers(payload["followers"]) if payload["followers"] is not None else None
        )
        self.slow: ModerateSlow | None = ModerateSlow(payload["slow"]) if payload["slow"] is not None else None
        self.vip: PartialUser | None = (
            PartialUser(payload["vip"]["user_id"], payload["vip"]["user_login"], payload["vip"]["user_name"], http=http)
            if payload["vip"] is not None
            else None
        )
        self.unvip: PartialUser | None = (
            PartialUser(
                payload["unvip"]["user_id"], payload["unvip"]["user_login"], payload["unvip"]["user_name"], http=http
            )
            if payload["unvip"] is not None
            else None
        )
        self.mod: PartialUser | None = (
            PartialUser(payload["mod"]["user_id"], payload["mod"]["user_login"], payload["mod"]["user_name"], http=http)
            if payload["mod"] is not None
            else None
        )
        self.unmod: PartialUser | None = (
            PartialUser(
                payload["unmod"]["user_id"], payload["unmod"]["user_login"], payload["unmod"]["user_name"], http=http
            )
            if payload["unmod"] is not None
            else None
        )
        self.ban: ModerateBan | None = ModerateBan(payload["ban"], http=http) if payload["ban"] is not None else None
        self.unban: PartialUser | None = (
            PartialUser(
                payload["unban"]["user_id"], payload["unban"]["user_login"], payload["unban"]["user_name"], http=http
            )
            if payload["unban"] is not None
            else None
        )
        self.timeout: ModerateTimeout | None = (
            ModerateTimeout(payload["timeout"], http=http) if payload["timeout"] is not None else None
        )
        self.untimeout: PartialUser | None = (
            PartialUser(
                payload["untimeout"]["user_id"],
                payload["untimeout"]["user_login"],
                payload["untimeout"]["user_name"],
                http=http,
            )
            if payload["untimeout"] is not None
            else None
        )
        self.raid: ModerateRaid | None = ModerateRaid(payload["raid"], http=http) if payload["raid"] is not None else None
        self.unraid: PartialUser | None = (
            PartialUser(
                payload["unraid"]["user_id"], payload["unraid"]["user_login"], payload["unraid"]["user_name"], http=http
            )
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
        self.shared_ban: ModerateBan | None = (
            ModerateBan(payload["shared_chat_ban"], http=http) if payload["shared_chat_ban"] is not None else None
        )
        self.shared_unban: PartialUser | None = (
            PartialUser(
                payload["shared_chat_unban"]["user_id"],
                payload["shared_chat_unban"]["user_login"],
                payload["shared_chat_unban"]["user_name"],
                http=http,
            )
            if payload["shared_chat_unban"] is not None
            else None
        )
        self.shared_timeout: ModerateTimeout | None = (
            ModerateTimeout(payload["shared_chat_timeout"], http=http)
            if payload["shared_chat_timeout"] is not None
            else None
        )
        self.shared_untimeout: PartialUser | None = (
            PartialUser(
                payload["shared_chat_untimeout"]["user_id"],
                payload["shared_chat_untimeout"]["user_login"],
                payload["shared_chat_untimeout"]["user_name"],
                http=http,
            )
            if payload["shared_chat_untimeout"] is not None
            else None
        )
        self.shared_delete: ModerateDelete | None = (
            ModerateDelete(payload["shared_chat_delete"], http=http) if payload["shared_chat_delete"] else None
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
            "shared_chat_ban",
            "shared_chat_unban",
            "shared_chat_timeout",
            "shared_chat_untimeout",
            "shared_chat_delete",
        ] = payload["action"]
        warn = payload.get("warn")
        self.warn: ModerateWarn | None = ModerateWarn(warn, http=http) if warn is not None else None


class ChannelModeratorAdd(_ResponderEvent):
    """
    Represents a moderator add event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster who had a new moderator added.
    user: PartialUser
        The new moderator.
    """

    subscription_type = "channel.moderator.add"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelModeratorAddEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelModeratorAdd broadcaster={self.broadcaster} user={self.user}>"


class ChannelModeratorRemove(_ResponderEvent):
    """
    Represents a moderator remove event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster who had a moderator removed.
    user: PartialUser
        The removed moderator.
    """

    subscription_type = "channel.moderator.remove"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelModeratorRemoveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelModeratorRemove broadcaster={self.broadcaster} user={self.user}>"


class ChannelPointsEmote(BaseEmote):
    """
    Represents a channel points emote.

    Attributes
    ----------
    begin: int
        The index of where the emote starts in the text.
    end: int
        The index of where the emote ends in the text.
    id: str
        The emote ID.
    """

    def __init__(self, data: ChannelPointsEmoteData) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<ChannelPointsEmote id={self.id} begin={self.begin} end={self.end}>"


class UnlockedEmote(RewardEmote):
    """
    Represents an Unlocked Emote on an automatic redeem.

    Attributes
    ----------
    id: str
        The ID that uniquely identifies this emote.
    name: str
        The human readable emote token.
    """

    def __init__(self, data: ChannelPointsUnlockedEmoteData) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<UnlockedEmote id={self.id} name={self.name}>"


class AutoRedeemReward:
    """
    Represents a reward on an automatic redeem.

    Attributes
    ----------
    type: typing.Literal["single_message_bypass_sub_mode", "send_highlighted_message", "random_sub_emote_unlock", "chosen_sub_emote_unlock", "chosen_modified_sub_emote_unlock", "message_effect", "gigantify_an_emote", "celebration"]
        The type of the reward. V2 does not cover Power-ups e.g. `gigantify_an_emote`, `celebration`, and `message_effect`.
    channel_points: int
        Number of channel points used. This is also covers `cost` when using V1.
    emote: UnlockedEmote | None
        The human readable emote token.
    """

    __slots__ = ("channel_points", "emote", "type")

    def __init__(self, data: BaseChannelPointsRewardData) -> None:
        self.type: Literal[
            "single_message_bypass_sub_mode",
            "send_highlighted_message",
            "random_sub_emote_unlock",
            "chosen_sub_emote_unlock",
            "chosen_modified_sub_emote_unlock",
            "message_effect",
            "gigantify_an_emote",
            "celebration",
        ] = data["type"]
        self.channel_points: int | None = data.get("cost") or data.get("channel_points")
        emote = data.get("unlocked_emote") or data.get("emote")
        self.emote: UnlockedEmote | None = UnlockedEmote(emote) if emote else None

    def __repr__(self) -> str:
        return f"<AutoRedeemReward type={self.type} channel_points={self.channel_points}>"


class ChannelPointsAutoRedeemAdd(_ResponderEvent):
    """
    Represents an automatic redemption of a channel points reward.

    .. note::
        This is a combination of V1 and V2.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster / channel who had the reward redeemed.
    user: PartialUser
        The user who redeemed the reward.
    id: str
        The ID of the redemption.
    text: str
        The text of the chat message.
    redeemed_at: datetime.datetime
        The datetime object of when the reward was redeemed.
    reward: AutoRedeemReward
        The details of the reward auto redeemed.

        V2 does not cover Power-ups e.g. `gigantify_an_emote`, `celebration`, and `message_effect`.
        Please see ChannelBitsUseSubscription for those specific types if using V2.
    emotes: list[ChannelPointsEmote]
        A list of ChannelPointsEmote objects that appear in the text.

        - If using V1, this is populated by Twitch.
        - If using V2, the emotes can be found in the fragments, but we calculate the index ourselves for this property.

    user_input: str | None
        The text input by the user if the reward requires input. This is `None` when using V2. `text` is the preferred attribute to use.
    fragments: list[ChatMessageFragment]
        The ordered list of chat message fragments. This is only populated when using V2.
    """

    subscription_type = "channel.channel_points_automatic_reward_redemption.add"

    __slots__ = ("_raw_emotes", "broadcaster", "fragments", "id", "redeemed_at", "reward", "text", "user", "user_input")

    def __init__(self, payload: ChannelPointsAutoRewardRedemptionEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.id: str = payload["id"]
        self.text: str = payload["message"]["text"]
        self.user_input: str | None = payload.get("user_input")
        self.redeemed_at: datetime.datetime = parse_timestamp(payload["redeemed_at"])
        self.reward: AutoRedeemReward = AutoRedeemReward(payload["reward"])
        fragments = payload["message"].get("fragments", [])
        self.fragments: list[ChatMessageFragment] = [ChatMessageFragment(f, http=http) for f in fragments]
        self._raw_emotes = payload.get("message", {}).get("emotes", [])

    def __repr__(self) -> str:
        return f"<ChannelPointsAutoRedeemAdd broadcaster={self.broadcaster} user={self.user} id={self.id}>"

    @property
    def emotes(self) -> list[ChannelPointsEmote]:
        if self._raw_emotes:
            return [ChannelPointsEmote(emote) for emote in self._raw_emotes]
        lengths = [len(frag.text) for frag in self.fragments]
        offsets = [0, *list(accumulate(lengths))]

        return [
            ChannelPointsEmote({"id": frag.emote.id, "begin": offsets[i], "end": offsets[i + 1] - 1})
            for i, frag in enumerate(self.fragments)
            if frag.type == "emote" and frag.emote is not None
        ]


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


class ChannelPointsReward(_ResponderEvent):
    """
    Represents an Eventsub Custom Reward.

    Attributes
    -----------
    broadcaster: Partialuser
        The broadcaster / channel associated with the custom reward.
    id: str
        The reward identifier.
    title: str
        The reward title.
    cost: int
        The reward cost.
    prompt: str
        The reward description.
    enabled: bool | None
        Whether the reward currently enabled. If False, the reward won't show up to viewers.
    paused: bool | None
        Whether the reward currently paused. If True, viewers can't redeem.
    in_stock: bool | None
        Whether the reward currently in stock. If False, viewers can't redeem.
    input_requred: bool | None
        Whether the viewer needs to enter information when redeeming the reward.
    skip_queue: bool | None
        Should redemptions be set to fulfilled status immediately when redeemed and skip the request queue instead of the normal unfulfilled status.
    colour: Colour
        Custom background colour for the reward.
    cooldown_until: datetime.datetime | None
        The cooldown expiration datetime. Is `None` if the reward is not on cooldown.
    max_per_stream: RewardLimitSettings | None
        Whether a maximum per stream is enabled and what the maximum is.
    max_per_user_per_stream: RewardLimitSettings | None
        Whether a maximum per user per stream is enabled and what the maximum is.
    global_cooldown: CooldownSettings | None
        Whether a cooldown is enabled and what the cooldown is in seconds.
    default_image: dict[str, str] | None
        Dictionary of default images of varying sizes for the reward.
    current_stream_redeems: int | None
        The number of redemptions redeemed during the current live stream. Counts against the `max_per_stream` limit.
        Is `None` if the broadcasters stream isn't live or max_per_stream isn't enabled.
    """

    __slots__ = (
        "_http",
        "_image",
        "broadcaster",
        "colour",
        "cooldown_until",
        "cost",
        "current_stream_redeems",
        "default_image",
        "enabled",
        "id",
        "in_stock",
        "input_required",
        "max_per_stream",
        "max_per_user_per_stream",
        "paused",
        "prompt",
        "skip_queue",
        "title",
    )

    def __init__(
        self,
        payload: ChannelPointsCustomRewardAddEvent | ChannelPointsCustomRewardUpdateEvent | ReedemedRewardData,
        *,
        http: HTTPClient,
        broadcaster: PartialUser | None = None,
    ) -> None:
        self._http: HTTPClient = http
        self.id: str = payload["id"]
        self.title: str = payload["title"]
        self.cost: int = int(payload["cost"])
        self.prompt: str = payload["prompt"]
        self.broadcaster: PartialUser = broadcaster or (
            PartialUser(
                payload.get("broadcaster_user_id", ""),
                payload.get("broadcaster_user_login"),
                payload.get("broadcaster_user_name"),
                http=self._http,
            )
        )
        self.enabled: bool | None = payload.get("is_enabled")
        self.paused: bool | None = payload.get("is_paused")
        self.in_stock: bool | None = payload.get("is_in_stock")
        self.input_required: bool | None = payload.get("is_user_input_required")
        self.skip_queue: bool | None = payload.get("should_redemptions_skip_request_queue")
        self.colour: Colour | None = Colour.from_hex(payload["background_color"]) if "background_color" in payload else None
        self.cooldown_until: datetime.datetime | None = (
            parse_timestamp(payload["cooldown_expires_at"])
            if "cooldown_expires_at" in payload and payload["cooldown_expires_at"] is not None
            else None
        )
        self.max_per_stream: RewardLimitSettings | None = (
            RewardLimitSettings(enabled=payload["max_per_stream"]["is_enabled"], value=payload["max_per_stream"]["value"])
            if "max_per_stream" in payload
            else None
        )
        self.max_per_user_per_stream: RewardLimitSettings | None = (
            RewardLimitSettings(
                enabled=payload["max_per_user_per_stream"]["is_enabled"],
                value=int(payload["max_per_user_per_stream"]["value"]),
            )
            if "max_per_user_per_stream" in payload
            else None
        )

        self.global_cooldown: CooldownSettings | None = (
            CooldownSettings(
                enabled=payload["global_cooldown"]["is_enabled"], seconds=int(payload["global_cooldown"]["seconds"])
            )
            if "global_cooldown" in payload
            else None
        )
        self.default_image: dict[str, str] | None = (
            {k: str(v) for k, v in payload["default_image"].items()} if "default_image" in payload else None
        )
        self.current_stream_redeems: int | None = payload.get("redemptions_redeemed_current_stream")
        self._image: ChannelPointsImageData | None = payload.get("image")

    def __repr__(self) -> str:
        return f"<ChannelPointsReward broadcaster={self.broadcaster} id={self.id} title={self.title} cost={self.cost}>"

    @property
    def color(self) -> Colour | None:
        """Alias for Colour."""
        return self.colour

    @property
    def image(self) -> dict[str, str] | None:
        """Dictionary of custom images for the reward. Is `None` if no images have been uploaded."""
        if self._image is not None:
            return {k: str(v) for k, v in self._image.items()}
        else:
            return None

    def get_image(self, size: Literal["1x", "2x", "4x"] = "2x", use_default: bool = False) -> Asset | None:
        """
        Get an image Asset for the reward at a specified size.
        Falls back to default images if no custom images have been uploaded or if specified.

        Parameters
        ----------
        size: str
            The size key of the image. Options are "1x", "2x", "4x". Defaults to "2x".
        use_default: bool
            Use default images instead of user uploaded images.

        Returns
        -------
        Asset | None
            The Asset for the image. Falls back to default images if no custom images have been uploaded.
        """
        if use_default or self.image is None or f"url_{size}" not in self.image:
            if self.default_image and f"url_{size}" in self.default_image:
                url = self.default_image[f"url_{size}"]
            else:
                return None
        else:
            url = self.image[f"url_{size}"]

        return Asset(url, http=self._http)

    async def fetch_reward(self) -> CustomReward:
        """|coro|

        Method to fetch and return the :class:`twitchio.CustomReward` associated with this event from the Twitch API.

        Returns
        -------
        CustomReward
            The reward object associated with this event, received from the Twitch API.

        Raises
        ------
        HTTPException
            An error occurred making the request to Twitch to fetch the reward.
        """
        reward = await self.broadcaster.fetch_custom_rewards(ids=[self.id])
        return reward[0]


class ChannelPointsRewardAdd(ChannelPointsReward):
    """
    Represents an Eventsub Custom Reward that has been created for a channel.

    Attributes
    -----------
    broadcaster: Partialuser
        The broadcaster / channel associated with the custom reward.
    id: str
        The reward identifier.
    title: str
        The reward title.
    cost: int
        The reward cost.
    prompt: str
        The reward description.
    enabled: bool
        Whether the reward currently enabled. If False, the reward won't show up to viewers.
    paused: bool
        Whether the reward currently paused. If True, viewers can't redeem.
    in_stock: bool
        Whether the reward currently in stock. If False, viewers can't redeem.
    input_requred: bool
        Whether the viewer needs to enter information when redeeming the reward.
    skip_queue: bool
        Should redemptions be set to fulfilled status immediately when redeemed and skip the request queue instead of the normal unfulfilled status.
    colour: Colour
        Custom background colour for the reward.
    cooldown_until: datetime.datetime | None
        The cooldown expiration datetime. Is `None` if the reward is not on cooldown.
    max_per_stream: RewardLimitSettings
        Whether a maximum per stream is enabled and what the maximum is.
    max_per_user_per_stream: RewardLimitSettings
        Whether a maximum per user per stream is enabled and what the maximum is.
    global_cooldown: CooldownSettings
        Whether a cooldown is enabled and what the cooldown is in seconds.
    default_image: dict[str, str]
        Dictionary of default images of varying sizes for the reward.
    current_stream_redeems: int
        The number of redemptions redeemed during the current live stream. Counts against the `max_per_stream` limit.
        Is `None` if the broadcasters stream isn't live or max_per_stream isn't enabled.
    """

    subscription_type = "channel.channel_points_custom_reward.add"

    def __init__(self, payload: ChannelPointsCustomRewardAddEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<ChannelPointsRewardAdd broadcaster={self.broadcaster} id={self.id} title={self.title} cost={self.cost} enabled={self.enabled}>"


class ChannelPointsRewardUpdate(ChannelPointsReward):
    """
    Represents an Eventsub Custom Reward that has been updated for a channel.

    Attributes
    -----------
    broadcaster: Partialuser
        The broadcaster / channel associated with the custom reward.
    id: str
        The reward identifier.
    title: str
        The reward title.
    cost: int
        The reward cost.
    prompt: str
        The reward description.
    enabled: bool
        Whether the reward currently enabled. If False, the reward won't show up to viewers.
    paused: bool
        Whether the reward currently paused. If True, viewers can't redeem.
    in_stock: bool
        Whether the reward currently in stock. If False, viewers can't redeem.
    input_requred: bool
        Whether the viewer needs to enter information when redeeming the reward.
    skip_queue: bool
        Should redemptions be set to fulfilled status immediately when redeemed and skip the request queue instead of the normal unfulfilled status.
    colour: Colour
        Custom background colour for the reward.
    cooldown_until: datetime.datetime | None
        The cooldown expiration datetime. Is `None` if the reward is not on cooldown.
    max_per_stream: RewardLimitSettings
        Whether a maximum per stream is enabled and what the maximum is.
    max_per_user_per_stream: RewardLimitSettings
        Whether a maximum per user per stream is enabled and what the maximum is.
    global_cooldown: CooldownSettings
        Whether a cooldown is enabled and what the cooldown is in seconds.
    default_image: dict[str, str]
        Dictionary of default images of varying sizes for the reward.
    current_stream_redeems: int
        The number of redemptions redeemed during the current live stream. Counts against the `max_per_stream` limit.
        Is `None` if the broadcasters stream isn't live or max_per_stream isn't enabled.
    """

    subscription_type = "channel.channel_points_custom_reward.update"

    def __init__(self, payload: ChannelPointsCustomRewardAddEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<ChannelPointsRewardUpdate broadcaster={self.broadcaster} id={self.id} title={self.title} cost={self.cost} enabled={self.enabled}>"


class ChannelPointsRewardRemove(ChannelPointsReward):
    """
    Represents an Eventsub Custom Reward that has been removed from a channel.

    Attributes
    -----------
    broadcaster: Partialuser
        The broadcaster / channel associated with the custom reward.
    id: str
        The reward identifier.
    title: str
        The reward title.
    cost: int
        The reward cost.
    prompt: str
        The reward description.
    enabled: bool
        Whether the reward currently enabled. If False, the reward won't show up to viewers.
    paused: bool
        Whether the reward currently paused. If True, viewers can't redeem.
    in_stock: bool
        Whether the reward currently in stock. If False, viewers can't redeem.
    input_requred: bool
        Whether the viewer needs to enter information when redeeming the reward.
    skip_queue: bool
        Should redemptions be set to fulfilled status immediately when redeemed and skip the request queue instead of the normal unfulfilled status.
    colour: Colour
        Custom background colour for the reward.
    cooldown_until: datetime.datetime | None
        The cooldown expiration datetime. Is `None` if the reward is not on cooldown.
    max_per_stream: RewardLimitSettings
        Whether a maximum per stream is enabled and what the maximum is.
    max_per_user_per_stream: RewardLimitSettings
        Whether a maximum per user per stream is enabled and what the maximum is.
    global_cooldown: CooldownSettings
        Whether a cooldown is enabled and what the cooldown is in seconds.
    default_image: dict[str, str]
        Dictionary of default images of varying sizes for the reward.
    current_stream_redeems: int
        The number of redemptions redeemed during the current live stream. Counts against the `max_per_stream` limit.
        Is `None` if the broadcasters stream isn't live or max_per_stream isn't enabled.
    """

    subscription_type = "channel.channel_points_custom_reward.remove"

    def __init__(self, payload: ChannelPointsCustomRewardAddEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<ChannelPointsRewardRemove broadcaster={self.broadcaster} id={self.id} title={self.title} cost={self.cost} enabled={self.enabled}>"


class BaseChannelPointsRedemption(_ResponderEvent):
    __slots__ = ("broadcaster", "id", "redeemed_at", "reward", "status", "user", "user_input")

    def __init__(
        self, payload: ChannelPointsRewardRedemptionAddEvent | ChannelPointsRewardRedemptionUpdateEvent, *, http: HTTPClient
    ) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.status: Literal["unknown", "unfulfilled", "fulfilled", "canceled"] = payload["status"]
        self.redeemed_at: datetime.datetime = parse_timestamp(payload["redeemed_at"])
        self.reward: ChannelPointsReward = ChannelPointsReward(payload["reward"], http=http, broadcaster=self.broadcaster)
        self.user_input: str = payload["user_input"]

    def __repr__(self) -> str:
        return f"<BaseChannelPointsRedemption broadcaster={self.broadcaster} user={self.user} status={self.status} redeemed_at={self.redeemed_at}>"


class ChannelPointsRedemptionAdd(BaseChannelPointsRedemption):
    """
    Represents a channel points redemption add event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel where the reward was redeemed.
    user: PartialUser
        The user that redeemed the reward.
    user_input: str
        The user input provided. Empty string if not provided.
    id: str
        The ID of the redemption.
    status: typing.Literal["unknown", "unfulfilled", "fulfilled", "canceled"]
        The status of the redemption. Defaults to unfulfilled.

        - unknown
        - unfulfilled
        - fulfilled
        - canceled

    redeemed_at: datetime.datetime
        Datetime when the reward was redeemed.
    reward: ChannelPointsReward
        Information about the reward that was redeemed, at the time it was redeemed.
    """

    subscription_type = "channel.channel_points_custom_reward_redemption.add"

    def __init__(self, payload: ChannelPointsRewardRedemptionAddEvent, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<ChannelPointsRedemptionAdd broadcaster={self.broadcaster} user={self.user} status={self.status} redeemed_at={self.redeemed_at}>"

    async def fulfill(self, *, token_for: str | PartialUser) -> CustomRewardRedemption:
        """|coro|

        Updates the redemption's status to FULFILLED.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.

        Parameters
        -----------
        token_for: str | PartialUser
            The user's token that has permission manage the broadcaster's reward redemptions.

        Returns
        --------
        CustomRewardRedemption
        """
        from twitchio.models.channel_points import CustomRewardRedemption

        data = await self._http.patch_custom_reward_redemption(
            broadcaster_id=self.reward.broadcaster.id,
            id=self.id,
            token_for=token_for,
            reward_id=self.reward.id,
            status="FULFILLED",
        )
        reward = cast("CustomReward", self.reward)
        return CustomRewardRedemption(data["data"][0], parent_reward=reward, http=self._http)

    async def refund(self, *, token_for: str | PartialUser) -> CustomRewardRedemption:
        """|coro|

        Updates the redemption's status to CANCELED.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.

        Parameters
        -----------
        token_for: str | PartialUser
            The user's token that has permission manage the broadcaster's reward redemptions.

        Returns
        --------
        CustomRewardRedemption
        """
        from twitchio.models.channel_points import CustomRewardRedemption

        data = await self._http.patch_custom_reward_redemption(
            broadcaster_id=self.reward.broadcaster.id,
            id=self.id,
            token_for=token_for,
            reward_id=self.reward.id,
            status="CANCELED",
        )
        reward = cast("CustomReward", self.reward)
        return CustomRewardRedemption(data["data"][0], parent_reward=reward, http=self._http)


class ChannelPointsRedemptionUpdate(BaseChannelPointsRedemption):
    """
    Represents a channel points redemption update event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel where the reward was redeemed.
    user: PartialUser
        The user that redeemed the reward.
    user_input: str
        The user input provided. Empty string if not provided.
    id: str
        The ID of the redemption.
    status: typing.Literal["unknown", "unfulfilled", "fulfilled", "canceled"]
        The status of the redemption. Will be fulfilled or canceled.

        - unknown
        - unfulfilled
        - fulfilled
        - canceled

    redeemed_at: datetime.datetime
        Datetime when the reward was redeemed.
    reward: ChannelPointsReward
        Information about the reward that was redeemed, at the time it was redeemed.
    """

    subscription_type = "channel.channel_points_custom_reward_redemption.update"

    def __init__(self, payload: ChannelPointsRewardRedemptionUpdateEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<ChannelPointsRedemptionUpdate broadcaster={self.broadcaster} user={self.user} status={self.status} redeemed_at={self.redeemed_at}>"


class PollVoting(NamedTuple):
    """
    NamedTuple that represents a channel poll's voting settings.

    Attributes
    -----------
    enabled: bool
        Indicates if Channel Points can be used for voting.
    amount: int
        Number of Channel Points required to vote once with Channel Points.
    """

    enabled: bool
    amount: int


class BaseChannelPoll(_ResponderEvent):
    __slots__ = ("broadcaster", "channel_points_voting", "choices", "id", "started_at", "status", "title")

    def __init__(
        self, payload: ChannelPollBeginEvent | ChannelPollProgressEvent | ChannelPollEndEvent, *, http: HTTPClient
    ) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.title: str = payload["title"]
        self.choices: list[PollChoice] = [PollChoice(choice) for choice in payload["choices"]]
        self.channel_points_voting = PollVoting(
            enabled=payload["channel_points_voting"]["is_enabled"],
            amount=payload["channel_points_voting"]["amount_per_vote"],
        )
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<BaseChannelPoll broadcaster={self.broadcaster} id={self.id} title={self.title}>"


class ChannelPollBegin(BaseChannelPoll):
    """
    Represents a channel poll begin event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel started a poll.
    id: str
        ID of the poll.
    title: str
        Question displayed for the poll.
    choices: list[PollChoice]
        A list of choices for the poll.
    channel_points_voting: PollVoting
        The channel points voting settings.
    started_at: datetime.datetime
        The time the poll started.
    ends_at: datetime.datetime
       The time the poll will end.
    """

    subscription_type = "channel.poll.begin"

    __slots__ = ("ends_at",)

    def __init__(self, payload: ChannelPollBeginEvent, *, http: HTTPClient) -> None:
        super().__init__(payload=payload, http=http)
        self.ends_at: datetime.datetime = parse_timestamp(payload["ends_at"])

    def __repr__(self) -> str:
        return (
            f"<ChannelPollBegin broadcaster={self.broadcaster} id={self.id} title={self.title} started_at={self.started_at}>"
        )


class ChannelPollProgress(BaseChannelPoll):
    """
    Represents a channel poll progress event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had received a poll update.
    id: str
        ID of the poll.
    title: str
        Question displayed for the poll.
    choices: list[PollChoice]
        A list of choices for the poll.
    channel_points_voting: PollVoting
        The channel points voting settings.
    started_at: datetime.datetime
        The time the poll started.
    ends_at: datetime.datetime
       The time the poll will end.
    """

    subscription_type = "channel.poll.progress"

    __slots__ = ("ends_at",)

    def __init__(self, payload: ChannelPollProgressEvent, *, http: HTTPClient) -> None:
        super().__init__(payload=payload, http=http)
        self.ends_at: datetime.datetime = parse_timestamp(payload["ends_at"])

    def __repr__(self) -> str:
        return f"<ChannelPollProgress broadcaster={self.broadcaster} id={self.id} title={self.title} started_at={self.started_at}>"


class ChannelPollEnd(BaseChannelPoll):
    """
    Represents a channel poll begin event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had received a poll update.
    id: str
        ID of the poll.
    title: str
        Question displayed for the poll.
    choices: list[PollChoice]
        A list of choices for the poll.
    channel_points_voting: PollVoting
        The channel points voting settings.
    status: typing.Literal["completed", "terminated", "archived"]
        The status of the poll. Valid values are:

        - completed
        - archived
        - terminated

    started_at: datetime.datetime
        The time the poll started.
    ended_at: datetime.datetime
       The time the poll ended.
    """

    subscription_type = "channel.poll.end"

    __slots__ = ("ended_at", "status")

    def __init__(self, payload: ChannelPollEndEvent, *, http: HTTPClient) -> None:
        super().__init__(payload=payload, http=http)
        self.status: Literal["completed", "terminated", "archived"] = payload["status"]
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])

    def __repr__(self) -> str:
        return f"<ChannelPollEnd broadcaster={self.broadcaster} id={self.id} title={self.title} started_at={self.started_at} ended_at={self.ended_at}>"


class BaseChannelPrediction(_ResponderEvent):
    def __init__(
        self,
        payload: ChannelPredictionBeginEvent
        | ChannelPredictionProgressEvent
        | ChannelPredictionLockEvent
        | ChannelPredictionEndEvent,
        *,
        http: HTTPClient,
    ) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.title: str = payload["title"]
        self.outcomes: list[PredictionOutcome] = [PredictionOutcome(c, http=http) for c in payload["outcomes"]]
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<BaseChannelPrediction id={self.id} title={self.title} started_at={self.started_at}>"


class ChannelPredictionBegin(BaseChannelPrediction):
    """
    Represents a channel points prediction begin event.

    Attributes
    ----------
    id: str
        ID of the prediction.
    broadcaster: PartialUser
        The broadcaster whose channel started a prediction.
    title: str
        Title for the channel points Prediction.
    outcomes: list[PredictionOutcome]
        A list of outcomes for the predictions. Only `id`, `title` and `colour` will be populated.
    started_at: datetime.datetime
        The time the prediction started.
    locks_at: datetime.datetime
        The time the prediction will automatically lock.
    """

    subscription_type = "channel.prediction.begin"

    __slots__ = ("locks_at",)

    def __init__(self, data: ChannelPredictionBeginEvent, *, http: HTTPClient) -> None:
        super().__init__(data, http=http)
        self.locks_at: datetime.datetime = parse_timestamp(data["locks_at"])

    def __repr__(self) -> str:
        return (
            f"<ChannelPredictionBegin id={self.id} title={self.title} started_at={self.started_at} locks_at={self.locks_at}>"
        )


class ChannelPredictionProgress(BaseChannelPrediction):
    """
    Represents a channel points prediction progress event.

    Attributes
    ----------
    id: str
        ID of the prediction.
    broadcaster: PartialUser
        The broadcaster whose channel started a prediction.
    title: str
        Title for the channel points Prediction.
    outcomes: list[PredictionOutcome]
        A list of outcomes for the predictions.
    started_at: datetime.datetime
        The time the prediction started.
    locks_at: datetime.datetime
        The time the prediction will automatically lock.
    """

    subscription_type = "channel.prediction.progress"

    __slots__ = ("locks_at",)

    def __init__(self, data: ChannelPredictionProgressEvent, *, http: HTTPClient) -> None:
        super().__init__(data, http=http)
        self.locks_at: datetime.datetime = parse_timestamp(data["locks_at"])

    def __repr__(self) -> str:
        return f"<ChannelPredictionProgress id={self.id} title={self.title} started_at={self.started_at} locks_at={self.locks_at}>"


class ChannelPredictionLock(BaseChannelPrediction):
    """
    Represents a channel points prediction progress event.

    Attributes
    ----------
    id: str
        ID of the prediction.
    broadcaster: PartialUser
        The broadcaster whose channel started a prediction.
    title: str
        Title for the channel points Prediction.
    outcomes: list[PredictionOutcome]
        A list of outcomes for the predictions.
    started_at: datetime.datetime
        The time the prediction started.
    locked_at: datetime.datetime
        The time the prediction was locked.
    """

    subscription_type = "channel.prediction.lock"

    __slots__ = ("locked_at",)

    def __init__(self, data: ChannelPredictionLockEvent, *, http: HTTPClient) -> None:
        super().__init__(data, http=http)
        self.locked_at: datetime.datetime = parse_timestamp(data["locked_at"])

    def __repr__(self) -> str:
        return f"<ChannelPredictionLock id={self.id} title={self.title} started_at={self.started_at} locked_at={self.locked_at}>"


class ChannelPredictionEnd(BaseChannelPrediction):
    """
    Represents a channel points prediction progress event.

    Attributes
    ----------
    id: str
        ID of the prediction.
    broadcaster: PartialUser
        The broadcaster whose channel started a prediction.
    title: str
        Title for the channel points Prediction.
    outcomes: list[PredictionOutcome]
        A list of outcomes for the predictions.
    winning_outcome: PredictionOutcome | None
        The winning outcome. This can be None if the prediction is deleted.
    started_at: datetime.datetime
        The time the prediction started.
    ended_at: datetime.datetime
        The time the prediction ended.
    status: typing.Literal["resolved", "canceled"]
        The status of the Channel Points Prediction. Valid values are ``resolved`` and ``canceled``.
    """

    subscription_type = "channel.prediction.end"

    __slots__ = ("ended_at", "status", "winning_outcome_id")

    def __init__(self, data: ChannelPredictionEndEvent, *, http: HTTPClient) -> None:
        super().__init__(data, http=http)
        self.ended_at: datetime.datetime = parse_timestamp(data["ended_at"])
        self.status: Literal["resolved", "canceled"] = data["status"]
        winning_outcome_id = data.get("winning_outcome_id")
        self.winning_outcome = next((outcome for outcome in self.outcomes if outcome.id == winning_outcome_id), None)

    def __repr__(self) -> str:
        return f"<ChannelPredictionEnd id={self.id} title={self.title} started_at={self.started_at} ended_at={self.ended_at} status={self.status} winning_outcome={self.winning_outcome}>"


class SuspiciousUserUpdate(_ResponderEvent):
    """
    Represents a suspicious user update event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had the treatment for a suspicious user was updated.
    user: PartialUser
        The suspicious user whose treatment was updated.
    moderator: PartialUser
        The moderator that updated the treatment for a suspicious user.
    low_trust_status: typing.Literal["none", "active_monitoring", "restricted"]
        The status set for the suspicious user. Can be the following:

        - none
        - active_monitoring
        - restricted
    """

    subscription_type = "channel.suspicious_user.update"

    __slots__ = ("broadcaster", "low_trust_status", "moderator", "user")

    def __init__(self, payload: ChannelSuspiciousUserUpdateEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.low_trust_status: Literal["none", "active_monitoring", "restricted"] = payload["low_trust_status"]

    def __repr__(self) -> str:
        return f"<SuspiciousUserUpdate broadcaster={self.broadcaster} user={self.user} moderator={self.moderator} low_trust_status={self.low_trust_status}>"


class SuspiciousUserMessage(_ResponderEvent):
    """
    Represents a suspicious user message event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had the treatment for a suspicious user was updated.
    user: PartialUser
        The user that sent the message.
    low_trust_status: typing.Literal["none", "active_monitoring", "restricted"]
        The status set for the suspicious user. Can be the following:

        - none
        - active_monitoring
        - restricted

    banned_channels: list[str]
        A list of channel IDs where the suspicious user is also banned.
    types: list[typing.Literal["manually_added", "ban_evader", "banned_in_shared_channel"]]
        User types (if any) that apply to the suspicious user. Can be the following:

        - manually_added
        - ban_evader
        - banned_in_shared_channel

    evaluation: typing.Literal["unknown", "possible", "likely"]
        A ban evasion likelihood value (if any) that as been applied to the user automatically by Twitch. Can be:

        - unknown
        - possible
        - likely

    message: BaseChatMessage
        The chat message.
    """

    subscription_type = "channel.suspicious_user.message"

    __slots__ = ("banned_channels", "broadcaster", "evaluation", "low_trust_status", "types", "user")

    def __init__(self, payload: ChannelSuspiciousUserMessageEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.low_trust_status: Literal["none", "active_monitoring", "restricted"] = payload["low_trust_status"]
        self.banned_channels: list[str] = payload["shared_ban_channel_ids"]
        self.types: list[Literal["manually_added", "ban_evader", "banned_in_shared_channel"]] = payload["types"]
        self.evaluation: Literal["unknown", "possible", "likely"] = payload["ban_evasion_evaluation"]
        self.message: BaseChatMessage = BaseChatMessage(payload, http=http)

    def __repr__(self) -> str:
        return f"<SuspiciousUserMessage broadcaster={self.broadcaster} user={self.user} low_trust_status={self.low_trust_status}>"


class ChannelVIPAdd(_ResponderEvent):
    """
    Represents a channel VIP remove event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had a VIP added.
    user: PartialUser
        The user who was added as a VIP.
    """

    subscription_type = "channel.vip.add"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelVIPAddEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelVIPAdd broadcaster={self.broadcaster} user={self.user}>"


class ChannelVIPRemove(_ResponderEvent):
    """
    Represents a channel VIP remove event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel had a VIP removed.
    user: PartialUser
        The user who was removed as a VIP.
    """

    subscription_type = "channel.vip.remove"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelVIPRemoveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelVIPRemove broadcaster={self.broadcaster} user={self.user}>"


class ChannelWarningAcknowledge(_ResponderEvent):
    """
    Represents a channel warning acknowledge event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel sent a warning.
    user: PartialUser
        The user that has acknowledged their warning.
    """

    subscription_type = "channel.warning.acknowledge"

    __slots__ = ("broadcaster", "user")

    def __init__(self, payload: ChannelWarningAcknowledgeEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<ChannelWarningAcknowledge broadcaster={self.broadcaster} user={self.user}>"


class ChannelWarningSend(_ResponderEvent):
    """
    Represents a channel warning send event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose channel sent a warning.
    user: PartialUser
        The user being warned.
    moderator: PartialUser
        The moderator who sent the warning.
    reason: str | None
        The reason given for the warning.
    chat_rules: list[str] | None
        The chat rules cited for the warning.
    """

    subscription_type = "channel.warning.send"

    __slots__ = ("broadcaster", "chat_rules", "moderator", "reason", "user")

    def __init__(self, payload: ChannelWarningSendEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.reason: str | None = payload.get("reason")
        self.chat_rules: list[str] | None = payload.get("chat_rules_cited")

    def __repr__(self) -> str:
        return f"<ChannelWarningSend broadcaster={self.broadcaster} user={self.user} moderator={self.moderator}>"


class BaseCharityCampaign(_ResponderEvent):
    __slots__ = ("broadcaster", "current", "description", "id", "logo", "name", "target", "website")

    def __init__(
        self,
        payload: CharityCampaignStartEvent
        | CharityCampaignProgressEvent
        | CharityCampaignStopEvent
        | CharityCampaignDonationEvent,
        *,
        http: HTTPClient,
    ) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.id: str = payload.get("campaign_id") or payload["id"]
        self.name: str = payload["charity_name"]
        self.description: str = payload["charity_description"]
        self.logo: Asset = Asset(payload["charity_logo"], http=http, dimensions=(100, 100))
        self.website: str = payload["charity_website"]

    def __repr__(self) -> str:
        return f"<BaseCharityCampaign broadcaster={self.broadcaster} id={self.id} name={self.name}>"


class CharityCampaignDonation(_ResponderEvent):
    """
    Represents a charity campaign donation event.

    Attributes
    ----------
    id: str
        An ID that identifies the donation. The ID is unique across campaigns.
    broadcaster: PartialUser
        The broadcaster that's running the campaign.
    user: PartialUser
        The user that donated to the campaign.
    charity: BaseCharityCampaign
        The charity associated with the campaign.
    amount: CharityValues
        The amount of money donated.
    """

    subscription_type = "channel.charity_campaign.donate"

    __slots__ = ("amount", "broadcaster", "charity", "id", "user")

    def __init__(self, payload: CharityCampaignDonationEvent, *, http: HTTPClient) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.charity: BaseCharityCampaign = BaseCharityCampaign(payload, http=http)
        self.amount: CharityValues = CharityValues(payload["amount"])

    def __repr__(self) -> str:
        return f"<CharityCampaignDonation id={self.id} broadcaster={self.broadcaster} user={self.user} amount={self.amount}>"


class CharityCampaignStart(BaseCharityCampaign):
    """
    Represents a charity campaign start event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster that's running the campaign.
    id: str
        ID that identifies the charity campaign.
    name: str
        The name of the charity.
    description: str
        A description of the charity.
    logo: Asset
        The charity logo as an asset.
    website: str
        A URL to the charity's website.
    current: CharityValues
        The current amount of donations that the campaign has received.
    target: CharityValues
        The target amount of donations that the campaign has received.
    started_at: datetime.datetime
        Datetime of when the broadcaster started the campaign.
    """

    subscription_type = "channel.charity_campaign.start"

    __slots__ = ("current", "started_at", "target")

    def __init__(self, payload: CharityCampaignStartEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.current: CharityValues = CharityValues(payload["current_amount"])
        self.target: CharityValues = CharityValues(payload["target_amount"])

    def __repr__(self) -> str:
        return f"<CharityCampaignStart broadcaster={self.broadcaster} id={self.id} name={self.name} started_at={self.started_at}>"


class CharityCampaignProgress(BaseCharityCampaign):
    """
    Represents a charity campaign progress event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster that's running the campaign.
    id: str
        ID that identifies the charity campaign.
    name: str
        The name of the charity.
    description: str
        A description of the charity.
    logo: Asset
        The charity logo as an asset.
    website: str
        A URL to the charity's website.
    current: CharityValues
        The current amount of donations that the campaign has received.
    target: CharityValues
        The target amount of donations that the campaign has received.
    """

    subscription_type = "channel.charity_campaign.progress"

    __slots__ = ("current", "target")

    def __init__(self, payload: CharityCampaignProgressEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.current: CharityValues = CharityValues(payload["current_amount"])
        self.target: CharityValues = CharityValues(payload["target_amount"])

    def __repr__(self) -> str:
        return f"<CharityCampaignProgress broadcaster={self.broadcaster} id={self.id} name={self.name} current={self.current} target={self.target}>"


class CharityCampaignStop(BaseCharityCampaign):
    """
    Represents a charity campaign stop event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster that's running the campaign.
    id: str
        ID that identifies the charity campaign.
    name: str
        The name of the charity.
    description: str
        A description of the charity.
    logo: Asset
        The charity logo as an asset.
    website: str
        A URL to the charity's website.
    current: CharityValues
        The current amount of donations that the campaign has received.
    target: CharityValues
        The target amount of donations that the campaign has received.
    stopped_at: datetime.datetime
        Datetime of when the broadcaster stopped the campaign.
    """

    subscription_type = "channel.charity_campaign.stop"

    __slots__ = ("current", "stopped_at", "target")

    def __init__(self, payload: CharityCampaignStopEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.stopped_at: datetime.datetime = parse_timestamp(payload["stopped_at"])
        self.current: CharityValues = CharityValues(payload["current_amount"])
        self.target: CharityValues = CharityValues(payload["target_amount"])

    def __repr__(self) -> str:
        return f"<CharityCampaignStop broadcaster={self.broadcaster} id={self.id} name={self.name} stopped_at={self.stopped_at}>"


class BaseGoal(_ResponderEvent):
    __slots__ = ("broadcaster", "current_amount", "description", "id", "started_at", "target_amount", "type")

    def __init__(self, payload: GoalBeginEvent | GoalProgressEvent | GoalEndEvent, *, http: HTTPClient) -> None:
        self.id: str = payload["id"]
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
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
        return f"<BaseGoal id={self.id} broadcaster={self.broadcaster} type={self.type} target_amount={self.target_amount} started_at={self.started_at}>"


class GoalBegin(BaseGoal):
    """
    Represents a goal begin event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster who started a goal.
    id: str
        An ID that identifies this event.
    type: typing.Literal["follow", "subscription", "subscription_count", "new_subscription", "new_subscription_count", "new_bit", "new_cheerer"]
        The type of goal.

        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | type                    | Description                                                                                                                                                                                              |
        +=========================+==========================================================================================================================================================================================================+
        | follow                  | The goal is to increase followers.                                                                                                                                                                       |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription            | The goal is to increase subscriptions. This type shows the net increase or decrease in tier points associated with the subscriptions.                                                                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription_count      | The goal is to increase subscriptions. This type shows the net increase or decrease in the number of subscriptions.                                                                                      |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription        | The goal is to increase subscriptions. This type shows only the net increase in tier points associated with the subscriptions (it does not account for users that unsubscribed since the goal started).  |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription_count  | The goal is to increase subscriptions. This type shows only the net increase in the number of subscriptions (it does not account for users that unsubscribed since the goal started).                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_bit                 | The goal is to increase the amount of Bits used on the channel.                                                                                                                                          |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_cheerer             | The goal is to increase the number of unique Cheerers to Cheer on the channel.                                                                                                                           |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

    description: str
        A description of the goal, if specified. The description may contain a maximum of 40 characters.
    current_amount: int
        The goal's current value. The goal's type determines how this value is increased or decreased.

        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | type                    | Description                                                                                                                                                                                                    |
        +=========================+================================================================================================================================================================================================================+
        | follow                  | This number increases with new followers and decreases when users unfollow the broadcaster.                                                                                                                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription            | This number is increased and decreased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased or decreased by 2, not 1. |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription_count      | This field is increased by 1 for each new subscription and decreased by 1 for each user that unsubscribes.                                                                                                     |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription        | This field is increased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased by 2, not 1.                             |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription_count  | This field is increased by 1 for each new subscription.                                                                                                                                                        |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

    target_amount: int
        The goal's target value. For example, if the broadcaster has 200 followers before creating the goal, and their goal is to double that number, this field is set to 400.
    started_at: datetime.datetime
        The datetime when the broadcaster started the goal.
    """

    subscription_type = "channel.goal.begin"

    def __init__(self, payload: GoalBeginEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<GoalBegin id={self.id} broadcaster={self.broadcaster} type={self.type} target_amount={self.target_amount} started_at={self.started_at}>"


class GoalProgress(BaseGoal):
    """
    Represents a goal progress event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose goal progressed.
    id: str
        An ID that identifies this event.
    type: typing.Literal["follow", "subscription", "subscription_count", "new_subscription", "new_subscription_count", "new_bit", "new_cheerer"]
        The type of goal.

        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | type                    | Description                                                                                                                                                                                              |
        +=========================+==========================================================================================================================================================================================================+
        | follow                  | The goal is to increase followers.                                                                                                                                                                       |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription            | The goal is to increase subscriptions. This type shows the net increase or decrease in tier points associated with the subscriptions.                                                                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription_count      | The goal is to increase subscriptions. This type shows the net increase or decrease in the number of subscriptions.                                                                                      |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription        | The goal is to increase subscriptions. This type shows only the net increase in tier points associated with the subscriptions (it does not account for users that unsubscribed since the goal started).  |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription_count  | The goal is to increase subscriptions. This type shows only the net increase in the number of subscriptions (it does not account for users that unsubscribed since the goal started).                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_bit                 | The goal is to increase the amount of Bits used on the channel.                                                                                                                                          |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_cheerer             | The goal is to increase the number of unique Cheerers to Cheer on the channel.                                                                                                                           |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

    description: str
        A description of the goal, if specified. The description may contain a maximum of 40 characters.
    current_amount: int
        The goal's current value. The goal's type determines how this value is increased or decreased.

        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | type                    | Description                                                                                                                                                                                                    |
        +=========================+================================================================================================================================================================================================================+
        | follow                  | This number increases with new followers and decreases when users unfollow the broadcaster.                                                                                                                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription            | This number is increased and decreased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased or decreased by 2, not 1. |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription_count      | This field is increased by 1 for each new subscription and decreased by 1 for each user that unsubscribes.                                                                                                     |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription        | This field is increased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased by 2, not 1.                             |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription_count  | This field is increased by 1 for each new subscription.                                                                                                                                                        |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

    target_amount: int
        The goal's target value. For example, if the broadcaster has 200 followers before creating the goal, and their goal is to double that number, this field is set to 400.
    started_at: datetime.datetime
        The datetime when the broadcaster started the goal.
    """

    subscription_type = "channel.goal.progress"

    def __init__(self, payload: GoalProgressEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)

    def __repr__(self) -> str:
        return f"<GoalProgress id={self.id} broadcaster={self.broadcaster} type={self.type} current_amount={self.current_amount} target_amount={self.target_amount} started_at={self.started_at}>"


class GoalEnd(BaseGoal):
    """
    Represents a goal end event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose goal ended.
    id: str
        An ID that identifies this event.
    type: typing.Literal["follow", "subscription", "subscription_count", "new_subscription", "new_subscription_count", "new_bit", "new_cheerer"]
        The type of goal.

        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | type                    | Description                                                                                                                                                                                              |
        +=========================+==========================================================================================================================================================================================================+
        | follow                  | The goal is to increase followers.                                                                                                                                                                       |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription            | The goal is to increase subscriptions. This type shows the net increase or decrease in tier points associated with the subscriptions.                                                                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription_count      | The goal is to increase subscriptions. This type shows the net increase or decrease in the number of subscriptions.                                                                                      |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription        | The goal is to increase subscriptions. This type shows only the net increase in tier points associated with the subscriptions (it does not account for users that unsubscribed since the goal started).  |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription_count  | The goal is to increase subscriptions. This type shows only the net increase in the number of subscriptions (it does not account for users that unsubscribed since the goal started).                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_bit                 | The goal is to increase the amount of Bits used on the channel.                                                                                                                                          |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_cheerer             | The goal is to increase the number of unique Cheerers to Cheer on the channel.                                                                                                                           |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

    description: str
        A description of the goal, if specified. The description may contain a maximum of 40 characters.
    current_amount: int
        The goal's current value. The goal's type determines how this value is increased or decreased.

        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | type                    | Description                                                                                                                                                                                                    |
        +=========================+================================================================================================================================================================================================================+
        | follow                  | This number increases with new followers and decreases when users unfollow the broadcaster.                                                                                                                    |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription            | This number is increased and decreased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased or decreased by 2, not 1. |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | subscription_count      | This field is increased by 1 for each new subscription and decreased by 1 for each user that unsubscribes.                                                                                                     |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription        | This field is increased by the points value associated with the subscription tier. For example, if a tier-two subscription is worth 2 points, this field is increased by 2, not 1.                             |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
        | new_subscription_count  | This field is increased by 1 for each new subscription.                                                                                                                                                        |
        +-------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

    target_amount: int
        The goal's target value. For example, if the broadcaster has 200 followers before creating the goal, and their goal is to double that number, this field is set to 400.
    started_at: datetime.datetime
        The datetime when the broadcaster started the goal.
    ended_at: datetime.datetime
        The datetime when the broadcaster ended the goal.
    achieved: bool
        Whether the broadcaster achieved their goal. Is True if the goal was achieved; otherwise, False.
    """

    subscription_type = "channel.goal.end"

    __slots__ = ("achieved", "ended_at")

    def __init__(self, payload: GoalEndEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])
        self.achieved: bool = bool(payload["is_achieved"])

    def __repr__(self) -> str:
        return f"<GoalEnd id={self.id} broadcaster={self.broadcaster} type={self.type} started_at={self.started_at} ended_at={self.ended_at} achieved={self.achieved}>"


class HypeTrainContribution:
    """
    Represents a hype train contribution.

    Attributes
    ----------
    user: PartialUser
        The user that made the contribution.
    type: typing.Literal["bits", "subscription", "other"]
        The contribution method used. Possible values are:

        +---------------+-------------------------------------------------------------------+
        | type          | Description                                                       |
        +===============+===================================================================+
        | bits          | Cheering with Bits.                                               |
        +---------------+-------------------------------------------------------------------+
        | subscription  | Subscription activity like subscribing or gifting subscriptions.  |
        +---------------+-------------------------------------------------------------------+
        | other         | Covers other contribution methods not listed.                     |
        +---------------+-------------------------------------------------------------------+

    total: int
        The total amount contributed. If type is bits, total represents the amount of Bits used.
        If type is subscription, total is 500, 1000, or 2500 to represent tier 1, 2, or 3 subscriptions, respectively.
    """

    __slots__ = ("total", "type", "user")

    def __init__(self, data: HypeTrainContributionData, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self.type: Literal["bits", "subscription", "other"] = data["type"]
        self.total: int = int(data["total"])

    def __repr__(self) -> str:
        return f"<HypeTrainContribution user={self.user} type={self.type} total={self.total}>"


class BaseHypeTrain(_ResponderEvent):
    __slots__ = (
        "broadcaster",
        "id",
        "level",
        "shared_train",
        "shared_train_participants",
        "started_at",
        "top_contributions",
        "total",
        "type",
    )

    def __init__(self, payload: BaseHypeTrainEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.id: str = payload["id"]
        self.level: int = int(payload["level"])
        self.total: int = int(payload["total"])
        self.top_contributions: list[HypeTrainContribution] = [
            HypeTrainContribution(c, http=http) for c in payload["top_contributions"]
        ]
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.shared_train_participants: list[PartialUser] = [
            PartialUser(u["broadcaster_user_id"], u["broadcaster_user_login"], u["broadcaster_user_name"], http=http)
            for u in payload["shared_train_participants"]
        ]
        self.shared_train: bool = bool(payload["is_shared_train"])
        self.type: Literal["treasure", "golden_kappa", "regular"] = payload["type"]

    def __repr__(self) -> str:
        return f"<BaseHypeTrain id={self.id} broadcaster={self.broadcaster} started_at={self.started_at}>"


class HypeTrainBegin(BaseHypeTrain):
    """
    Represents a hype train begin event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster who has a hype train begin.
    id: str
        The hype train ID.
    level: int
        The starting level of the hype train.
    total: int
        Total points contributed to the hype train.
    progress: int
        The number of points contributed to the hype train at the current level.
    goal: int
        The number of points required to reach the next level.
    top_contributions: list[HypeTrainContribution]
        The contributors with the most points contributed.
    all_time_high_level: int
        The all-time high level this type of Hype Train has reached for this broadcaster.
    all_time_high_total: int
        The all-time high total this type of Hype Train has reached for this broadcaster.
    shared_train: bool
        Indicates if the Hype Train is shared.
        When True, `shared_train_participants` will contain the list of broadcasters the train is shared with.
    shared_train_participants: list[PartialUser]
        List of broadcasters in the shared Hype Train.
    type: typing.Literal["treasure", "golden_kappa", "regular"]
        The type of the Hype Train. Possible values are:

        - treasure
        - golden_kappa
        - regular

    started_at: datetime.datetime
        The datetime of when the hype train started.
    expires_at: datetime.datetime
        The datetime when the hype train expires. The expiration is extended when the hype train reaches a new level.

    """

    subscription_type = "channel.hype_train.begin"

    __slots__ = (
        "all_time_high_level",
        "all_time_high_total",
        "expires_at",
        "goal",
        "progress",
    )

    def __init__(self, payload: HypeTrainBeginEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.progress: int = int(payload["progress"])
        self.goal: int = int(payload["goal"])
        self.expires_at: datetime.datetime = parse_timestamp(payload["expires_at"])
        self.all_time_high_level: int = int(payload["all_time_high_level"])
        self.all_time_high_total: int = int(payload["all_time_high_total"])

    def __repr__(self) -> str:
        return f"<HypeTrainBegin id={self.id} broadcaster={self.broadcaster} goal={self.goal} started_at={self.started_at} type={self.type}>"


class HypeTrainProgress(BaseHypeTrain):
    """
    Represents a hype train progress event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose hype train progressed.
    id: str
        The hype train ID.
    level: int
        The current level of the hype train.
    total: int
        Total points contributed to the hype train.
    progress: int
        The number of points contributed to the hype train at the current level.
    goal: int
        The number of points required to reach the next level.
    top_contributions: list[HypeTrainContribution]
        The contributors with the most points contributed.
    started_at: datetime.datetime
        The datetime of when the hype train started.
    expires_at: datetime.datetime
        The datetime when the hype train expires. The expiration is extended when the hype train reaches a new level.
    shared_train: bool
        Indicates if the Hype Train is shared.
        When True, `shared_train_participants` will contain the list of broadcasters the train is shared with.
    shared_train_participants: list[PartialUser]
        List of broadcasters in the shared Hype Train.
    type: typing.Literal["treasure", "golden_kappa", "regular"]
        The type of the Hype Train. Possible values are:

        - treasure
        - golden_kappa
        - regular

    """

    subscription_type = "channel.hype_train.progress"

    __slots__ = (
        "expires_at",
        "goal",
        "progress",
    )

    def __init__(self, payload: HypeTrainProgressEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.progress: int = int(payload["progress"])
        self.goal: int = int(payload["goal"])
        self.expires_at: datetime.datetime = parse_timestamp(payload["expires_at"])

    def __repr__(self) -> str:
        return f"<HypeTrainProgress id={self.id} broadcaster={self.broadcaster} goal={self.goal} progress={self.progress} type={self.type}>"


class HypeTrainEnd(BaseHypeTrain):
    """
    Represents a hype train end event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose hype train has ended.
    id: str
        The hype train ID.
    level: int
        The final level of the hype train.
    total: int
        Total points contributed to the hype train.
    top_contributions: list[HypeTrainContribution]
        The contributors with the most points contributed.
    started_at: datetime.datetime
        The datetime of when the hype train started.
    ended_at: datetime.datetime
        The datetime of when the hype train ended.
    cooldown_until: datetime.datetime
        The datetime when the hype train cooldown ends so that the next hype train can start.
    shared_train: bool
        Indicates if the Hype Train is shared.
        When True, `shared_train_participants` will contain the list of broadcasters the train is shared with.
    shared_train_participants: list[PartialUser]
        List of broadcasters in the shared Hype Train.
    type: typing.Literal["treasure", "golden_kappa", "regular"]
        The type of the Hype Train. Possible values are:

        - treasure
        - golden_kappa
        - regular

    """

    subscription_type = "channel.hype_train.end"

    __slots__ = (
        "cooldown_until",
        "ended_at",
    )

    def __init__(self, payload: HypeTrainEndEvent, *, http: HTTPClient) -> None:
        super().__init__(payload, http=http)
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])
        self.cooldown_until: datetime.datetime = parse_timestamp(payload["cooldown_ends_at"])

    def __repr__(self) -> str:
        return f"<HypeTrainEnd id={self.id} broadcaster={self.broadcaster} total={self.total} ended_at={self.ended_at} type={self.type}>"


class ShieldModeBegin(_ResponderEvent):
    """
    Represents a shield mode begin event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose shield mode status was updated.
    moderator: PartialUser
        The moderator that updated the shield mode status. This will be the same as the `broadcaster` if the broadcaster updated the status.
    started_at: datetime.datetime
        The UTC datetime of when the moderator activated shield mode.
    """

    subscription_type = "channel.shield_mode.begin"

    __slots__ = (
        "broadcaster",
        "moderator",
        "started_at",
    )

    def __init__(self, payload: ShieldModeBeginEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<ShieldModeBegin broadcaster={self.broadcaster} moderator={self.moderator} started_at={self.started_at}>"


class ShieldModeEnd(_ResponderEvent):
    """
    Represents a shield mode end event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster whose shield mode status was updated.
    moderator: PartialUser
        The moderator that updated the shield mode status. This will be the same as the `broadcaster` if the broadcaster updated the status.
    ended_at: datetime.datetime
        The UTC datetime of when the moderator deactivated shield mode.
    """

    subscription_type = "channel.shield_mode.end"

    __slots__ = (
        "broadcaster",
        "ended_at",
        "moderator",
    )

    def __init__(self, payload: ShieldModeEndEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.ended_at: datetime.datetime = parse_timestamp(payload["ended_at"])

    def __repr__(self) -> str:
        return f"<ShieldModeEnd broadcaster={self.broadcaster} moderator={self.moderator} ended_at={self.ended_at}>"


class ShoutoutCreate(_ResponderEvent):
    """
    Represents a shoutout create event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster that sent the shoutout.
    moderator: PartialUser
        The moderator that sent the shoutout. This may be the same as the broadcaster.
    to_broadcaster: PartialUser
        The broadcaster that received the shoutout.
    viewer_count: int
        The number of users that were watching the broadcaster's stream at the time of the shoutout.
    started_at: datetime.datetime
        The UTC datetime of when the moderator sent the shoutout.
    cooldown_until: datetime.datetime
        The UTC datetime of when the broadcaster may send a shoutout to a different broadcaster.
    target_cooldown_until: datetime.datetime
        The UTC datetime of when the broadcaster may send another shoutout to the `to_broadcaster` again.
    """

    subscription_type = "channel.shoutout.create"

    __slots__ = (
        "broadcaster",
        "cooldown_until",
        "moderator",
        "started_at",
        "target_cooldown_until",
        "to_broadcaster",
        "viewer_count",
    )

    def __init__(self, payload: ShoutoutCreateEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.moderator: PartialUser = PartialUser(
            payload["moderator_user_id"], payload["moderator_user_login"], payload["moderator_user_name"], http=http
        )
        self.to_broadcaster: PartialUser = PartialUser(
            payload["to_broadcaster_user_id"],
            payload["to_broadcaster_user_login"],
            payload["to_broadcaster_user_name"],
            http=http,
        )
        self.viewer_count: int = int(payload["viewer_count"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])
        self.cooldown_until: datetime.datetime = parse_timestamp(payload["cooldown_ends_at"])
        self.target_cooldown_until: datetime.datetime = parse_timestamp(payload["target_cooldown_ends_at"])

    def __repr__(self) -> str:
        return f"<ShoutoutCreate broadcaster={self.broadcaster} to_broadcaster={self.to_broadcaster} started_at={self.started_at}>"


class ShoutoutReceive(_ResponderEvent):
    """
    Represents a shoutout received event.

    Attributes
    ----------
    broadcaster: PartialUser
        The broadcaster that received the shoutout.
    from_broadcaster: PartialUser
        The broadcaster that sent the shoutout.
    viewer_count: int
        The number of users that were watching the from_broadcaster's stream at the time of the shoutout.
    started_at: datetime.datetime
        The UTC datetime of when the moderator sent the shoutout.
    """

    subscription_type = "channel.shoutout.receive"

    __slots__ = ("broadcaster", "from_broadcaster", "started_at", "viewer_count")

    def __init__(self, payload: ShoutoutReceiveEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.from_broadcaster: PartialUser = PartialUser(
            payload["from_broadcaster_user_id"],
            payload["from_broadcaster_user_login"],
            payload["from_broadcaster_user_name"],
            http=http,
        )
        self.viewer_count: int = int(payload["viewer_count"])
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<ShoutoutReceive broadcaster={self.broadcaster} from_broadcaster={self.from_broadcaster} started_at={self.started_at}>"


class StreamOnline(_ResponderEvent):
    """
    Represents a stream online event.

    Attributes
    ----------
    broadcaster: PartialUser
        The user whose stream is now online.
    id: str
        The ID of the stream.
    type: typing.Literal["live", "playlist", "watch_party", "premiere", "rerun"]
        The stream type. Valid values are:

        - live
        - playlist
        - watch_party
        - premiere
        - rerun

    started_at: datetime.datetime
        The datetime of when the stream started.
    """

    subscription_type = "stream.online"

    __slots__ = ("broadcaster", "id", "started_at", "type")

    def __init__(self, payload: StreamOnlineEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )
        self.id: str = payload["id"]
        self.type: Literal["live", "playlist", "watch_party", "premiere", "rerun"] = payload["type"]
        self.started_at: datetime.datetime = parse_timestamp(payload["started_at"])

    def __repr__(self) -> str:
        return f"<StreamOnline id={self.id} broadcaster={self.broadcaster} started_at={self.started_at}>"


class StreamOffline(_ResponderEvent):
    """
    Represents a stream offline event.

    Attributes
    ----------
    broadcaster: PartialUser
        The user whose stream is now offline.
    """

    subscription_type = "stream.offline"

    __slots__ = "broadcaster"

    def __init__(self, payload: StreamOfflineEvent, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(
            payload["broadcaster_user_id"], payload["broadcaster_user_login"], payload["broadcaster_user_name"], http=http
        )

    def __repr__(self) -> str:
        return f"<StreamOffline broadcaster={self.broadcaster}>"


class UserAuthorizationGrant(BaseEvent):
    """
    Represents a user authorisation grant event.

    .. note::
        This subscription type is only supported by webhooks, and cannot be used with WebSockets.

    Attributes
    ----------
    client_id: str
        The client_id  of the application that was granted user access.
    user: PartialUser
        The user who has granted authorization for your client id.
    """

    subscription_type = "user.authorization.grant"

    __slots__ = ("client_id", "user")

    def __init__(self, payload: UserAuthorizationGrantEvent, *, http: HTTPClient) -> None:
        self.client_id: str = payload["client_id"]
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)

    def __repr__(self) -> str:
        return f"<UserAuthorizationGrant client_id={self.client_id} user={self.user}>"


class UserAuthorizationRevoke(BaseEvent):
    """
    Represents a user authorisation reoke event.

    .. note::
        This subscription type is only supported by webhooks, and cannot be used with WebSockets.

        The `user.id` will always be populated but `user.name` can be `None` if the user no longer exists.

    Attributes
    ----------
    client_id: str
        The client_id of the application with revoked user access.
    user: PartialUser
        The user who has revoked authorization for your client id.
    """

    subscription_type = "user.authorization.revoke"

    __slots__ = ("client_id", "user")

    def __init__(self, payload: UserAuthorizationRevokeEvent, *, http: HTTPClient) -> None:
        self.client_id: str = payload["client_id"]
        self.user: PartialUser | None = (
            PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
            if payload.get("user_id")
            else None
        )

    def __repr__(self) -> str:
        return f"<UserAuthorizationRevoke client_id={self.client_id} user={self.user}>"


class UserUpdate(BaseEvent):
    """
    Represents a user update event.

    .. note::
        The email attribute requires the `user:read:email` scope otherwise it is None.

    Attributes
    ----------
    user: PartialUser
        The user who has updated their account.
    verified: bool
        Whether Twitch has verified the user's email address.
    description: str
        The user's description.
    email: str | None
        The user's email address. Requires the `user:read:email` scope for the user.
    """

    subscription_type = "user.update"

    __slots__ = ("description", "email", "user", "verified")

    def __init__(self, payload: UserUpdateEvent, *, http: HTTPClient) -> None:
        self.user: PartialUser = PartialUser(payload["user_id"], payload["user_login"], payload["user_name"], http=http)
        self.verified: bool = bool(payload["email_verified"])
        self.description: str = payload["description"]
        self.email: str | None = payload.get("email", None)

    def __repr__(self) -> str:
        return f"<UserUpdate user={self.user} verified={self.verified} description={self.description}>"


class Whisper(BaseEvent):
    """Represents a whisper event.

    Attributes
    ----------
    sender: PartialUser
        The user sending the whisper.
    recipient: PartialUser
        The user receiving the whisper.
    id: str
        The whisper ID.
    text: str
        The message text.
    """

    subscription_type = "user.whisper.message"

    __slots__ = ("id", "recipient", "sender", "text")

    def __init__(self, payload: UserWhisperEvent, *, http: HTTPClient) -> None:
        self.sender: PartialUser = PartialUser(
            payload["from_user_id"], payload["from_user_login"], payload["from_user_name"], http=http
        )
        self.recipient: PartialUser = PartialUser(
            payload["to_user_id"], payload["to_user_login"], payload["to_user_name"], http=http
        )
        self.id: str = payload["whisper_id"]
        self.text: str = payload["whisper"]["text"]

    def __repr__(self) -> str:
        return f"<Whisper sender={self.sender} recipient={self.recipient} id={self.id} text={self.text}>"


class SubscriptionRevoked:
    """Represents a revoked eventsub subscription by Twitch.

    Attributes
    ----------
    id: str
        The ID of the subscription that has been revoked.
    raw: RevocationSubscription
        The raw payload of the revoked subscription as a TypedDict.
    status: RevocationReason
        The status provides the reason as to why the subscription was revoked by Twitch.
    type: str
        The type of subscription that was revoked e.g. `channel.follow`.
    version: str
        The version of the subscription e.g. `1` or `2`.
    cost: int
        The cost of the subscription.
    transport_method: TransportMethod
        The transport method of the subscription.
    transport_data: RevocationTransport
        The data pertaining to the transport of the subscription.
        This will contain `session_id` or `callback` url depending on the transport method.
    created_at: datetime.datetime
        The datetime that the subscription was created.
    """

    __slots__ = (
        "cost",
        "created_at",
        "id",
        "raw",
        "reason",
        "status",
        "transport_data",
        "transport_method",
        "type",
        "version",
    )

    def __init__(self, data: RevocationSubscription) -> None:
        self.id: str = data["id"]
        self.raw: RevocationSubscription = data
        self.status: RevocationReason = RevocationReason(data["status"])
        self.reason: RevocationReason = self.status
        self.type: str = data["type"]
        self.version: str = data["version"]
        self.cost: int = data["cost"]
        self.transport_method: TransportMethod = TransportMethod(data["transport"]["method"])
        self.transport_data: RevocationTransport = data["transport"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])


class EventsubTransport:
    """Represents an eventsub subscription.

    Attributes
    ----------
    method: typing.Literal["websocket", "webhook"]
        The transport method. This can be either ``websocket`` or ``webhook``.
    callback: str | None
        The callback URL where the notifications are sent. This will only be populated if the method is set to ``webhook``.
    session_id: str | None
        An ID that identifies the WebSocket that notifications are sent to. This will only be populated if the method is set to ``websocket``.
    connected_at: str | None
        The UTC datetime that the WebSocket connection was established. This will only be populated if the method is set to ``websocket``.
    disconnected_at: str | None
        The UTC datetime that the WebSocket connection was lost. This will only be populated if the method is set to ``websocket``.
    """

    __slots__ = ("callback", "connected_at", "disconnected_at", "method", "session_id")

    def __init__(self, data: EventsubTransportData) -> None:
        self.method: Literal["websocket", "webhook"] = data["method"]
        self.callback: str | None = data.get("callback")
        self.session_id: str | None = data.get("session_id")
        self.connected_at: str | None = data.get("connected_at")
        self.disconnected_at: str | None = data.get("disconnected_at")

    def __repr__(self) -> str:
        return f"<EventsubTransport method={self.method} callback={self.callback} session_id={self.session_id}>"


class EventsubSubscription:
    """Represents an eventsub subscription.

    Attributes
    ----------
    id: str
        An ID that identifies the subscription.
    status: typing.Literal[
            "enabled",
            "webhook_callback_verification_pending",
            "webhook_callback_verification_failed",
            "notification_failures_exceeded",
            "authorization_revoked",
            "moderator_removed",
            "user_removed",
            "version_removed",
            "beta_maintenance",
            "websocket_disconnected",
            "websocket_failed_ping_pong",
            "websocket_received_inbound_traffic",
            "websocket_connection_unused",
            "websocket_internal_error",
            "websocket_network_timeout",
            "websocket_network_error",
        ]
        The subscription's status. The subscriber receives events only for enabled subscriptions.

        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | Status                                 | Description                                                                                                       |
        +========================================+===================================================================================================================+
        | enabled                                | The subscription is enabled.                                                                                      |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | webhook_callback_verification_pending  | The subscription is pending verification of the specified callback URL.                                           |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | webhook_callback_verification_failed   | The specified callback URL failed verification.                                                                   |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | notification_failures_exceeded         | The notification delivery failure rate was too high.                                                              |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | authorization_revoked                  | The authorization was revoked for one or more users specified in the Condition object.                            |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | moderator_removed                      | The moderator that authorized the subscription is no longer one of the broadcaster's moderators.                  |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | user_removed                           | One of the users specified in the Condition object was removed.                                                   |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | chat_user_banned                       | The user specified in the Condition object was banned from the broadcaster's chat.                                |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | version_removed                        | The subscription to subscription type and version is no longer supported.                                         |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | beta_maintenance                       | The subscription to the beta subscription type was removed due to maintenance.                                    |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_disconnected                 | The client closed the connection.                                                                                 |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_failed_ping_pong             | The client failed to respond to a ping message.                                                                   |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_received_inbound_traffic     | The client sent a non-pong message. Clients may only send pong messages (and only in response to a ping message). |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_connection_unused            | The client failed to subscribe to events within the required time.                                                |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_internal_error               | The Twitch WebSocket server experienced an unexpected error.                                                      |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_network_timeout              | The Twitch WebSocket server timed out writing the message to the client.                                          |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_network_error                | The Twitch WebSocket server experienced a network error writing the message to the client.                        |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | websocket_failed_to_reconnect          | The client failed to reconnect to the Twitch WebSocket server within the required time after a Reconnect Message. |
        +----------------------------------------+-------------------------------------------------------------------------------------------------------------------+

    type: str
        The subscription's type. e.g. ``channel.follow`` For a list of subscription types, see `Subscription Types <https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/#subscription-types>`_.
    version: str
        The version number that identifies this definition of the subscription's data.
    condition: Condition
        The subscription's parameter values. This is a dictionary mapping of parameters used to subscribe.
        e.g. {"broadcaster_user_id": "123456789"}
    created_at: datetime.datetime
        The datetime of when the subscription was created.
    cost: int
        The amount that the subscription counts against your limit. Learn More
    transport: EventsubTransport
        The transport details used to send the notifications.
    """

    def __init__(self, data: EventsubSubscriptionResponseData, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.status: Literal[
            "enabled",
            "webhook_callback_verification_pending",
            "webhook_callback_verification_failed",
            "notification_failures_exceeded",
            "authorization_revoked",
            "moderator_removed",
            "user_removed",
            "version_removed",
            "beta_maintenance",
            "websocket_disconnected",
            "websocket_failed_ping_pong",
            "websocket_received_inbound_traffic",
            "websocket_connection_unused",
            "websocket_internal_error",
            "websocket_network_timeout",
            "websocket_network_error",
        ] = data["status"]
        self.type: str = data["type"]
        self.version: str = data["version"]
        self.condition: Condition = data["condition"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.cost: int = int(data["cost"])
        self.transport: EventsubTransport = EventsubTransport(data["transport"])

    def __repr__(self) -> str:
        return f"<EventsubSubscription id={self.id} status={self.status} transport={self.transport} type={self.type} version={self.version} condition={self.condition} created_at={self.created_at} cost={self.cost}>"

    async def delete(self, *, token_for: str | None = None) -> None:
        """|coro|

        Delete the eventsub subscription.

        Parameters
        ----------
        token_for: str | None
            For websocket subscriptions, provide the user ID associated with the subscription.
        """
        await self._http.delete_eventsub_subscription(self.id, token_for=token_for)


class EventsubSubscriptions:
    """Represents eventsub subscriptions.

    Attributes
    ----------
    subscriptions: HTTPAsyncIterator[EventsubSubscription]
        Async iterable of the actual subscriptions.
    total: int
        The total number of subscriptions that you've created.
    total_cost: int
        The sum of all of your subscription costs. `Learn more <https://dev.twitch.tv/docs/eventsub/manage-subscriptions/#subscription-limits>_`
    max_total_cost: int
        The maximum total cost that you're allowed to incur for all subscriptions that you create.
    """

    def __init__(self, data: EventsubSubscriptionResponse, iterator: HTTPAsyncIterator[EventsubSubscription]) -> None:
        self.subscriptions: HTTPAsyncIterator[EventsubSubscription] = iterator
        self.total: int = int(data["total"])
        self.total_cost: int = int(data["total_cost"])
        self.max_total_cost: int = int(data["max_total_cost"])

    def __repr__(self) -> str:
        return (
            f"<EventsubSubscriptions total={self.total} total_cost={self.total_cost} max_total_cost={self.max_total_cost}>"
        )


class WebsocketWelcome:
    """The model received in the :func:`~twitchio.event_websocket_welcome` event.

    Attributes
    ----------
    id: str
        The ID associated with the Websocket, received from Twitch in "session_welcome".
    keepalive_timeout_seconds: int
        The keepalive timeout as an :class:`int` sent and confirmed by Twitch.
    connected_at: :class:`datetime.datetime`
        A :class:`datetime.datetime` representing when this websocket officially connected.
    """

    def __init__(self, data: WelcomeSession) -> None:
        self.id: str = data["id"]
        self.keepalive_timeout_seconds: int = data["keepalive_timeout_seconds"]
        self.connected_at: datetime.datetime = parse_timestamp(data["connected_at"])


class ConduitShard:
    """ConduitShard model containing various information about a Shard on a :class:`~twitchio.Conduit`.

    Attributes
    ----------
    raw: dict[str, Any]
        The raw data retrieved from Twitch.
    id: str
        The ID of the shard. Will be a nummeric :class:`str` between ``0`` and ``19_999``.
    method: str
        A str literal of either ``websocket`` or ``webhook``, indicating what transport this shard uses.
    session_id: str | None
        If ``method == websocket``, this will be the ``session_id`` of the websocket. Could be ``None`` if the shard is not
        connected or ``method == webhook``.
    connected_at: :class:`datetime.datetime` | None
        A :class:`datetime.datetime` of when the shard was connected in UTC. Only availabe when ``method == websocket``.
    disconnected_at: :class:`datetime.datetime` | None
        A :class:`datetime.datetime` of when the shard was lost connection in UTC. Only availabe when ``method == websocket``.
    callback: str | None
        The URL that notifications for the shard are sent via Webhooks. Only availabe when ``method == webhook``.
    """

    def __init__(self, data: ShardData) -> None:
        self.raw: ShardData = data
        self.id = data["id"]
        self._status: ShardStatus = data["status"]

        transport = data["transport"]
        self.method: str = transport["method"]
        self.session_id: str | None = transport.get("session_id")

        self.connected_at: datetime.datetime | None = None
        if cat := transport.get("connected_at"):
            self.connected_at = parse_timestamp(cat)

        self.disconnected_at: datetime.datetime | None = None
        if dat := transport.get("disconnected_at"):
            self.disconnected_at = parse_timestamp(dat)

        self.callback: str | None = transport.get("callback")

    @property
    def status(self) -> ShardStatus:
        """Property returning the status of the shard.

        The possible statuses are provided below.

        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | Status                                    | Description                                                                                                       |
        +===========================================+===================================================================================================================+
        | ``enabled``                               | The shard is enabled.                                                                                             |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``webhook_callback_verification_pending`` | The shard is pending verification of the specified callback URL.                                                  |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``webhook_callback_verification_failed``  | The specified callback URL failed verification.                                                                   |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``notification_failures_exceeded``        | The notification delivery failure rate was too high.                                                              |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_disconnected``                | The client closed the connection.                                                                                 |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_failed_ping_pong``            | The client failed to respond to a ping message.                                                                   |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_received_inbound_traffic``    | The client sent a non-pong message. Clients may only send pong messages (and only in response to a ping message). |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_internal_error``              | The Twitch WebSocket server experienced an unexpected error.                                                      |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_network_timeout``             | The Twitch WebSocket server timed out writing the message to the client.                                          |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_network_error``               | The Twitch WebSocket server experienced a network error writing the message to the client.                        |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_failed_to_reconnect``         | The client failed to reconnect to the Twitch WebSocket server within the required time after a Reconnect Message. |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        """
        return self._status

    def __repr__(self) -> str:
        return f'ConduitShard(id={self.id}, method="{self.method}", status="{self._status}")'


class Conduit:
    """The :class:`~twitchio.Conduit` model which is returned from various API endpoints relating to Conduits on Twitch.

    This class can be used to manage the underlying Conduit, however for a more intuitive approach see:
    :class:`~twitchio.AutoClient` or :class:`~twitchio.ext.commands.AutoBot` which wraps this class and provides a
    :class:`~twitchio.ConduitInfo` class instead.

    Supported Operations
    --------------------

    +-------------+-------------------------------------------+-----------------------------------------------+
    | Operation   | Usage(s)                                  | Description                                   |
    +=============+===========================================+===============================================+
    | __str__     | ``str(conduit)``, ``f"{conduit}"``        | Return the official str represntation.        |
    +-------------+-------------------------------------------+-----------------------------------------------+
    | __repr__    | ``repr(conduit)``, ``f"{conduit!r}"``     | Return the official represntation.            |
    +-------------+-------------------------------------------+-----------------------------------------------+
    | __eq__      | ``conduit == other``, ``conduit != other``| Compare equality of two conduits.             |
    +-------------+-------------------------------------------+-----------------------------------------------+

    Attributes
    ----------
    raw: dict[Any, Any]
        The raw response from Twitch which was used to create this class.
    shard_count: int
        The amount of shards assigned to this conduit.
    """

    def __init__(self, data: ConduitData, *, http: HTTPClient) -> None:
        self.raw: ConduitData = data
        self.shard_count: int = data["shard_count"]
        self._id: str = data["id"]
        self._http = http

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Conduit):
            return NotImplemented

        return self._id == other._id

    def __repr__(self) -> str:
        return f'Conduit(id="{self._id}", shard_count="{self.shard_count}")'

    def __str__(self) -> str:
        return self._id

    @property
    def id(self) -> str:
        """Property returning the Conduit ID as a :class:`str`."""
        return self._id

    async def delete(self) -> None:
        """|coro|

        Method to delete the associated :class:`~twitchio.Conduit` from the API.

        Returns
        -------
        None
            Successfully removed the :class:`~twitchio.Conduit`

        Raises
        ------
        :class:`~twitchio.HTTPException`
            ``404`` - Conduit was not found or you do not own this Conduit.
        """
        await self._http.delete_conduit(self.id)

    async def update(self, shard_count: int, /) -> Conduit:
        """|coro|

        Method which updates the underlying Conduit on the Twitch API with the provided ``shard_count``.

        .. important::

            If you are using :class:`~twitchio.AutoClient` or :class:`~twitchio.ext.commands.AutoBot` this will not
            update the underlying websocket connections. See: :meth:`~twitchio.ConduitInfo.update_shard_count` instead.

        Parameters
        ----------
        shard_count: int
            The new amount of shards the Conduit should be assigned. Should be between ``1`` and ``20_000``.

        Raises
        ------
        ValueError
            ``shard_count`` must be between ``1`` and ``20_000``.

        Returns
        -------
        :class:`~twitchio.Conduit`
            The updated :class:`~twitchio.Conduit`.
        """
        if shard_count <= 0:
            raise ValueError('The provided "shard_count" must not be lower than 1.')

        elif shard_count > 20_000:
            raise ValueError('The provided "shard_count" cannot be greater than 20_000.')

        payload = await self._http.update_conduits(self.id, shard_count=shard_count)
        return Conduit(payload["data"][0], http=self._http)

    def fetch_shards(self, *, status: ShardStatus | None = None) -> HTTPAsyncIterator[ConduitShard]:
        """|aiter|

        Method which returns the shards for the Conduit retrieved from the Twitch API.

        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | Status                                    | Description                                                                                                       |
        +===========================================+===================================================================================================================+
        | ``enabled``                               | The shard is enabled.                                                                                             |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``webhook_callback_verification_pending`` | The shard is pending verification of the specified callback URL.                                                  |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``webhook_callback_verification_failed``  | The specified callback URL failed verification.                                                                   |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``notification_failures_exceeded``        | The notification delivery failure rate was too high.                                                              |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_disconnected``                | The client closed the connection.                                                                                 |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_failed_ping_pong``            | The client failed to respond to a ping message.                                                                   |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_received_inbound_traffic``    | The client sent a non-pong message. Clients may only send pong messages (and only in response to a ping message). |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_internal_error``              | The Twitch WebSocket server experienced an unexpected error.                                                      |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_network_timeout``             | The Twitch WebSocket server timed out writing the message to the client.                                          |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_network_error``               | The Twitch WebSocket server experienced a network error writing the message to the client.                        |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+
        | ``websocket_failed_to_reconnect``         | The client failed to reconnect to the Twitch WebSocket server within the required time after a Reconnect Message. |
        +-------------------------------------------+-------------------------------------------------------------------------------------------------------------------+

        Parameters
        ----------
        status: str
            An optional :class:`str` which when provided, filters the shards by their status on the API. Possible statuses
            are listed above. Defaults to ``None`` which fetches all shards.

        Returns
        -------
        HTTPAsyncIterator[:class:`~twitchio.ConduitShard`]
            An :class:`~twitchio.HTTPAsyncIterator` which can be awaited or used with ``async for`` to retrieve the
            :class:`~twitchio.ConduitShard`'s.

        Raises
        ------
        HTTPException
            An error occurred making the request to Twitch.
        """
        return self._http.get_conduit_shards(self._id, status=status)

    async def update_shards(self, shards: list[ShardUpdateRequest]) -> ...:
        # TODO: Docs
        # TODO; Shard Model...
        await self._http.update_conduit_shards(self.id, shards=shards)
