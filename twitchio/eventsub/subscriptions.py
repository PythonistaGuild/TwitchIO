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

import abc
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypedDict, Unpack

from twitchio.utils import handle_user_ids


if TYPE_CHECKING:
    from twitchio.types_.conduits import Condition
    from twitchio.user import PartialUser


__all__ = (
    "AdBreakBeginSubscription",
    "AutomodMessageHoldSubscription",
    "AutomodMessageHoldV2Subscription",
    "AutomodMessageUpdateSubscription",
    "AutomodMessageUpdateV2Subscription",
    "AutomodSettingsUpdateSubscription",
    "AutomodTermsUpdateSubscription",
    "ChannelBanSubscription",
    "ChannelBitsUseSubscription",
    "ChannelCheerSubscription",
    "ChannelFollowSubscription",
    "ChannelModerateSubscription",
    "ChannelModerateV2Subscription",
    "ChannelModeratorAddSubscription",
    "ChannelModeratorRemoveSubscription",
    "ChannelPointsAutoRedeemSubscription",
    "ChannelPointsAutoRedeemV2Subscription",
    "ChannelPointsRedeemAddSubscription",
    "ChannelPointsRedeemUpdateSubscription",
    "ChannelPointsRewardAddSubscription",
    "ChannelPointsRewardRemoveSubscription",
    "ChannelPointsRewardUpdateSubscription",
    "ChannelPollBeginSubscription",
    "ChannelPollEndSubscription",
    "ChannelPollProgressSubscription",
    "ChannelPredictionBeginSubscription",
    "ChannelPredictionEndSubscription",
    "ChannelPredictionLockSubscription",
    "ChannelPredictionProgressSubscription",
    "ChannelRaidSubscription",
    "ChannelSubscribeMessageSubscription",
    "ChannelSubscribeSubscription",
    "ChannelSubscriptionEndSubscription",
    "ChannelSubscriptionGiftSubscription",
    "ChannelUnbanRequestResolveSubscription",
    "ChannelUnbanRequestSubscription",
    "ChannelUnbanSubscription",
    "ChannelUpdateSubscription",
    "ChannelVIPAddSubscription",
    "ChannelVIPRemoveSubscription",
    "ChannelWarningAcknowledgementSubscription",
    "ChannelWarningSendSubscription",
    "CharityCampaignProgressSubscription",
    "CharityCampaignStartSubscription",
    "CharityCampaignStopSubscription",
    "CharityDonationSubscription",
    "ChatClearSubscription",
    "ChatClearUserMessagesSubscription",
    "ChatMessageDeleteSubscription",
    "ChatMessageSubscription",
    "ChatNotificationSubscription",
    "ChatSettingsUpdateSubscription",
    "ChatUserMessageHoldSubscription",
    "ChatUserMessageUpdateSubscription",
    "GoalBeginSubscription",
    "GoalEndSubscription",
    "GoalProgressSubscription",
    "HypeTrainBeginSubscription",
    "HypeTrainEndSubscription",
    "HypeTrainProgressSubscription",
    "SharedChatSessionBeginSubscription",
    "SharedChatSessionEndSubscription",
    "SharedChatSessionUpdateSubscription",
    "ShieldModeBeginSubscription",
    "ShieldModeEndSubscription",
    "ShoutoutCreateSubscription",
    "ShoutoutReceiveSubscription",
    "StreamOfflineSubscription",
    "StreamOnlineSubscription",
    "SubscriptionPayload",
    "SuspiciousUserMessageSubscription",
    "SuspiciousUserUpdateSubscription",
    "UserAuthorizationGrantSubscription",
    "UserAuthorizationRevokeSubscription",
    "UserUpdateSubscription",
    "WhisperReceivedSubscription",
)


# Short names: Only map names that require shortening...
_SUB_MAPPING: dict[str, str] = {
    "channel.ad_break.begin": "ad_break",
    "channel.bits.use": "bits_use",
    "channel.chat.clear_user_messages": "chat_clear_user",
    "channel.chat.message": "message",  # Sub events?
    "channel.chat.message_delete": "message_delete",
    "channel.unban_request.create": "unban_request",
    "channel.channel_points_automatic_reward_redemption.add": "automatic_redemption_add",
    "channel.channel_points_custom_reward.add": "custom_reward_add",
    "channel.channel_points_custom_reward.update": "custom_reward_update",
    "channel.channel_points_custom_reward.remove": "custom_reward_remove",
    "channel.channel_points_custom_reward_redemption.add": "custom_redemption_add",
    "channel.channel_points_custom_reward_redemption.update": "custom_redemption_update",
    "user.whisper.message": "message_whisper",
    "channel.update": "channel_update",
    "channel.subscribe": "subscription",
    "channel.moderate": "mod_action",  # Sub events?
    "channel.hype_train.begin": "hype_train",
}


class DefaultAuthDict(TypedDict, total=False):
    as_bot: bool
    token_for: str | PartialUser | None


class SubscriptionPayload(abc.ABC):
    """Abstract Base Class which every EventSub subscription inherits from.

    See the individual subscriptions for more details on the specific subscription.
    """

    type: ClassVar[Any]
    version: ClassVar[Any]

    __slots__ = (
        "broadcaster_id",
        "broadcaster_user_id",
        "campaign_id",
        "category_id",
        "client_id",
        "conduit_id",
        "from_broadcaster_user_id",
        "moderator_user_id",
        "organization_id",
        "reward_id",
        "to_broadcaster_user_id",
        "user_id",
    )

    def __init__(self, **condition: Unpack[Condition]) -> None:
        raise NotImplementedError

    @property
    def condition(self) -> Condition:
        raise NotImplementedError

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {}


class AutomodMessageHoldSubscription(SubscriptionPayload):
    """The ``automod.message.hold`` subscription type notifies a user if a message was caught by automod for review.

    .. important::
        Requires a user access token that includes the ``moderator:manage:automod scope``. The ID in the ``moderator_user_id`` condition parameter must match the user ID in the access token.

        If app access token used, then additionally requires the ``moderator:manage:automod`` scope for the moderator.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["automod.message.hold"]] = "automod.message.hold"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodMessageHoldV2Subscription(SubscriptionPayload):
    """The ``automod.message.hold`` V2 subscription type notifies a user if a message was caught by automod for review.

    Version 2 of this endpoint provides additional information about the message, including the reason, the term used, and its position within the message.

    .. important::
        Requires a user access token that includes the ``moderator:manage:automod scope``. The ID in the ``moderator_user_id`` condition parameter must match the user ID in the access token.

        If app access token used, then additionally requires the ``moderator:manage:automod`` scope for the moderator.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["automod.message.hold"]] = "automod.message.hold"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodMessageUpdateSubscription(SubscriptionPayload):
    """The ``automod.message.update`` subscription type sends notification when a message in the automod queue has its status changed.

    .. important::
        Requires a user access token that includes the ``moderator:manage:automod scope``. The ID in the ``moderator_user_id`` condition parameter must match the user ID in the access token.

        If app access token used, then additionally requires the ``moderator:manage:automod`` scope for the moderator.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["automod.message.update"]] = "automod.message.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodMessageUpdateV2Subscription(SubscriptionPayload):
    """The ``automod.message.update`` subscription type sends notification when a message in the automod queue has its status changed.

    Version 2 of this endpoint provides additional information about the message, including the reason, the term used, and its position within the message.

    .. important::
        Requires a user access token that includes the ``moderator:manage:automod scope``. The ID in the ``moderator_user_id`` condition parameter must match the user ID in the access token.

        If app access token used, then additionally requires the ``moderator:manage:automod`` scope for the moderator.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["automod.message.update"]] = "automod.message.update"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodSettingsUpdateSubscription(SubscriptionPayload):
    """The ``automod.settings.update`` subscription type sends a notification when a broadcaster's automod settings are updated.

    .. important::
        Requires a user access token that includes the ``moderator:read:automod_settings`` scope. The ID in the ``moderator_user_id`` condition parameter must match the user ID in the access token.

        If app access token used, then additionally requires the ``moderator:read:automod_settings`` scope for the moderator.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["automod.settings.update"]] = "automod.settings.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AutomodTermsUpdateSubscription(SubscriptionPayload):
    """The ``automod.terms.update`` subscription type sends a notification when a broadcaster's terms settings are updated. Changes to private terms are not sent.

    .. important::
        Requires a user access token that includes the ``moderator:manage:automod`` scope. The ID in the ``moderator_user_id`` condition parameter must match the user ID in the access token.

        If app access token used, then additionally requires the ``moderator:manage:automod`` scope for the moderator.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["automod.terms.update"]] = "automod.terms.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelBitsUseSubscription(SubscriptionPayload):
    """The ``channel.bits.use`` subscription type sends a notification whenever Bits are used on a channel.

    This event is designed to be an all-purpose event for when Bits are used in a channel and might be updated in the future as more Twitch features use Bits.

    Currently, this event will be sent when a user:

    - Cheers in a channel
    - Uses a Power-up
        - Will not emit when a streamer uses a Power-up for free in their own channel.
    - Sends Combos

    .. important::
        Requires a user access token that includes the ``bits:read`` scope. This must be the broadcaster's token.

        Bits transactions via Twitch Extensions are not included in this subscription type.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.bits.use"]] = "channel.bits.use"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelUpdateSubscription(SubscriptionPayload):
    """The ``channel.update`` subscription type sends notifications when a broadcaster updates the category, title, content classification labels, or broadcast language for their channel.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.update"]] = "channel.update"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelFollowSubscription(SubscriptionPayload):
    """The ``channel.follow`` subscription type sends a notification when a specified channel receives a follow.

    .. important::
        Must have ``moderator:read:followers`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.follow"]] = "channel.follow"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class AdBreakBeginSubscription(SubscriptionPayload):
    """The ``channel.ad_break.begin`` subscription type sends a notification when a user runs a midroll commercial break, either manually or automatically via ads manager.

    .. important::
        Must have ``channel:read:ads`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.ad_break.begin"]] = "channel.ad_break.begin"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChatClearSubscription(SubscriptionPayload):
    """The ``channel.chat.clear`` subscription type sends a notification when a moderator or bot clears all messages from the chat room.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user, and either ``channel:bot`` scope from broadcaster or moderator status.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.clear"]] = "channel.chat.clear"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatClearUserMessagesSubscription(SubscriptionPayload):
    """The ``channel.chat.clear_user_messages`` subscription type sends a notification when a moderator or bot clears all messages for a specific user.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user, and either ``channel:bot`` scope from broadcaster or moderator status.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.clear_user_messages"]] = "channel.chat.clear_user_messages"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatMessageSubscription(SubscriptionPayload):
    """The ``channel.chat.message`` subscription type sends a notification when any user sends a message to a channel's chat room.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user, and either ``channel:bot`` scope from broadcaster or moderator status.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.message"]] = "channel.chat.message"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatNotificationSubscription(SubscriptionPayload):
    """The ``channel.chat.notification`` subscription type sends a notification when an event that appears in chat occurs, such as someone subscribing to the channel or a subscription is gifted.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user, and either ``channel:bot`` scope from broadcaster or moderator status.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.notification"]] = "channel.chat.notification"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatMessageDeleteSubscription(SubscriptionPayload):
    """The ``channel.chat.message_delete`` subscription type sends a notification when a moderator removes a specific message.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user, and either ``channel:bot`` scope from broadcaster or moderator status.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.message_delete"]] = "channel.chat.message_delete"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatSettingsUpdateSubscription(SubscriptionPayload):
    """The ``channel.chat_settings.update`` subscription type sends a notification when a broadcaster's chat settings are updated.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user, and either ``channel:bot`` scope from broadcaster or moderator status.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat_settings.update"]] = "channel.chat_settings.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatUserMessageHoldSubscription(SubscriptionPayload):
    """The ``channel.chat.user_message_hold`` subscription type notifies a user if their message is caught by automod.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.user_message_hold"]] = "channel.chat.user_message_hold"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class ChatUserMessageUpdateSubscription(SubscriptionPayload):
    """The ``channel.chat.user_message_update`` subscription type notifies a user if their message's automod status is updated.

    .. important::
        Requires ``user:read:chat`` scope from chatting user.

        If app access token used, then additionally requires ``user:bot`` scope from chatting user.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    user_id: str | PartialUser
        The ID, or PartialUser, of the chatter reading chat. e.g. Your bot ID.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "user_id" must be passed.
    """

    type: ClassVar[Literal["channel.chat.user_message_update"]] = "channel.chat.user_message_update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.user_id: str = condition.get("user_id", "")

        if not self.broadcaster_user_id or not self.user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "user_id": self.user_id}


class SharedChatSessionBeginSubscription(SubscriptionPayload):
    """The ``channel.shared_chat.begin`` subscription type sends a notification when a channel becomes active in an active shared chat session.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shared_chat.begin"]] = "channel.shared_chat.begin"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class SharedChatSessionUpdateSubscription(SubscriptionPayload):
    """The ``channel.shared_chat.update`` subscription type sends a notification when the active shared chat session the channel is in changes.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shared_chat.update"]] = "channel.shared_chat.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class SharedChatSessionEndSubscription(SubscriptionPayload):
    """The ``channel.shared_chat.end`` subscription type sends a notification when a channel leaves a shared chat session or the session ends.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shared_chat.end"]] = "channel.shared_chat.end"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class ChannelSubscribeSubscription(SubscriptionPayload):
    """The ``channel.subscribe`` subscription type sends a notification when a specified channel receives a subscriber. This does not include resubscribes.

    .. important::
        Must have ``channel:read:subscriptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.subscribe"]] = "channel.subscribe"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelSubscriptionEndSubscription(SubscriptionPayload):
    """The ``channel.subscription.end`` subscription type sends a notification when a subscription to the specified channel expires.

    .. important::
        Must have ``channel:read:subscriptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.subscription.end"]] = "channel.subscription.end"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelSubscriptionGiftSubscription(SubscriptionPayload):
    """The ``channel.subscription.gift`` subscription type sends a notification when a user gives one or more gifted subscriptions in a channel.

    .. important::
        Must have ``channel:read:subscriptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.subscription.gift"]] = "channel.subscription.gift"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelSubscribeMessageSubscription(SubscriptionPayload):
    """The ``channel.subscription.message`` subscription type sends a notification when a user sends a resubscription chat message in a specific channel.

    .. important::
        Must have ``channel:read:subscriptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.subscription.message"]] = "channel.subscription.message"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelCheerSubscription(SubscriptionPayload):
    """The ``channel.cheer`` subscription type sends a notification when a user cheers on the specified channel.

    .. important::
        Must have ``bits:read`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.cheer"]] = "channel.cheer"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelRaidSubscription(SubscriptionPayload):
    """The ``channel.raid`` subscription type sends a notification when a broadcaster raids another broadcaster's channel.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    to_broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to. This listens to the raid events to a specific broadcaster.
    from_broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to. This listens to the raid events from a specific broadcaster.

    Raises
    ------
    ValueError
        The parameter "to_broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.raid"]] = "channel.raid"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.to_broadcaster_user_id: str = condition.get("to_broadcaster_user_id", "")
        self.from_broadcaster_user_id: str = condition.get("from_broadcaster_user_id", "")

        if bool(self.to_broadcaster_user_id) == bool(self.from_broadcaster_user_id):
            raise ValueError(
                'Exactly one of the parameters "to_broadcaster_user_id" or "from_broadcaster_user_id" must be passed.'
            )

    @property
    def condition(self) -> Condition:
        return {
            "to_broadcaster_user_id": self.to_broadcaster_user_id,
            "from_broadcaster_user_id": self.from_broadcaster_user_id,
        }


class ChannelBanSubscription(SubscriptionPayload):
    """The ``channel.ban`` subscription type sends a notification when a viewer is timed out or banned from the specified channel.

    .. important::
        Must have ``channel:moderate`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.ban"]] = "channel.ban"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelUnbanSubscription(SubscriptionPayload):
    """The ``channel.unban`` subscription type sends a notification when a viewer is unbanned from the specified channel.

    .. important::
        Must have ``channel:moderate`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.unban"]] = "channel.unban"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelUnbanRequestSubscription(SubscriptionPayload):
    """The ``channel.unban_request.create`` subscription type sends a notification when a user creates an unban request.

    .. important::
        Must have ``moderator:read:unban_requests`` or ``moderator:manage:unban_requests`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.unban_request.create"]] = "channel.unban_request.create"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelUnbanRequestResolveSubscription(SubscriptionPayload):
    """The ``channel.unban_request.resolve`` subscription type sends a notification when an unban request has been resolved.

    .. important::
        Must have ``moderator:read:unban_requests`` or ``moderator:manage:unban_requests`` scope.

        If you use webhooks, the user in moderator_user_id must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        If you use WebSockets, the ID in moderator_user_id must match the user ID in the user access token.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.unban_request.resolve"]] = "channel.unban_request.resolve"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelModerateSubscription(SubscriptionPayload):
    """The ``channel.moderate`` subscription type sends a notification when a moderator performs a moderation action in a channel.
    Some of these actions affect chatters in other channels during Shared Chat.

        This is Version 1 of the subscription.

    .. important::
        Must have all of the following scopes:

        - ``moderator:read:blocked_terms`` OR ``moderator:manage:blocked_terms``
        - ``moderator:read:chat_settings`` OR ``moderator:manage:chat_settings``
        - ``moderator:read:unban_requests`` OR ``moderator:manage:unban_requests``
        - ``moderator:read:banned_users`` OR ``moderator:manage:banned_users``
        - ``moderator:read:chat_messages`` OR ``moderator:manage:chat_messages``
        - ``moderator:read:moderators``
        - ``moderator:read:vips``

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.moderate"]] = "channel.moderate"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelModerateV2Subscription(SubscriptionPayload):
    """The ``channel.moderate`` subscription type sends a notification when a moderator performs a moderation action in a channel.
    Some of these actions affect chatters in other channels during Shared Chat.

        This is Version 2 of the subscription that includes warnings.

    .. important::
        Must have all of the following scopes:

        - ``moderator:read:blocked_terms`` OR ``moderator:manage:blocked_terms``
        - ``moderator:read:chat_settings`` OR ``moderator:manage:chat_settings``
        - ``moderator:read:unban_requests`` OR ``moderator:manage:unban_requests``
        - ``moderator:read:banned_users`` OR ``moderator:manage:banned_users``
        - ``moderator:read:chat_messages`` OR ``moderator:manage:chat_messages``
        - ``moderator:read:warnings`` OR ``moderator:manage:warnings``
        - ``moderator:read:moderators``
        - ``moderator:read:vips``

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.moderate"]] = "channel.moderate"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelModeratorAddSubscription(SubscriptionPayload):
    """The ``channel.moderator.add`` subscription type sends a notification when a user is given moderator privileges on a specified channel.

    .. important::
        Must have ``moderation:read`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.moderator.add"]] = "channel.moderator.add"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelModeratorRemoveSubscription(SubscriptionPayload):
    """The ``channel.moderator.remove`` subscription type sends a notification when a user has moderator privileges removed on a specified channel.

    .. important::
        Must have ``moderation:read`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.moderator.remove"]] = "channel.moderator.remove"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsAutoRedeemSubscription(SubscriptionPayload):
    """The ``channel.channel_points_automatic_reward_redemption.add`` subscription type sends a notification when a viewer has redeemed an automatic channel points reward on the specified channel.

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_automatic_reward_redemption.add"]] = (
        "channel.channel_points_automatic_reward_redemption.add"
    )
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsAutoRedeemV2Subscription(SubscriptionPayload):
    """The ``channel.channel_points_automatic_reward_redemption.add`` subscription type sends a notification when a viewer has redeemed an automatic channel points reward on the specified channel.

    This is Version 2 of the subscription that includes message fragments and channel points.
    This does *not* notify for Power-up types currently, they are covered by V1 only. e.g.

        - message_effect
        - gigantify_an_emote
        - celebration

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_automatic_reward_redemption.add"]] = (
        "channel.channel_points_automatic_reward_redemption.add"
    )
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsRewardAddSubscription(SubscriptionPayload):
    """The ``channel.channel_points_custom_reward.add`` subscription type sends a notification when a custom channel points reward has been created for the specified channel.

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_custom_reward.add"]] = "channel.channel_points_custom_reward.add"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsRewardUpdateSubscription(SubscriptionPayload):
    """The ``channel.channel_points_custom_reward.update`` subscription type sends a notification when a custom channel points reward has been updated for the specified channel.

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    reward_id: str
        Optional to only get notifications for a specific reward.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_custom_reward.update"]] = "channel.channel_points_custom_reward.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.reward_id: str = condition.get("reward_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "reward_id": self.reward_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsRewardRemoveSubscription(SubscriptionPayload):
    """The ``channel.channel_points_custom_reward.remove`` subscription type sends a notification when a custom channel points reward has been removed from the specified channel.

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    reward_id: str
        Optional to only get notifications for a specific reward.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_custom_reward.remove"]] = "channel.channel_points_custom_reward.remove"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.reward_id: str = condition.get("reward_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "reward_id": self.reward_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsRedeemAddSubscription(SubscriptionPayload):
    """The ``channel.channel_points_custom_reward_redemption.add`` subscription type sends a notification when a viewer has redeemed a custom channel points reward on the specified channel.

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    reward_id: str
        Optional to only get notifications for a specific reward.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_custom_reward_redemption.add"]] = (
        "channel.channel_points_custom_reward_redemption.add"
    )
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.reward_id: str = condition.get("reward_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "reward_id": self.reward_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPointsRedeemUpdateSubscription(SubscriptionPayload):
    """The ``channel.channel_points_custom_reward_redemption.update`` subscription type sends a notification when a redemption of a channel points custom reward has been updated for the specified channel.

    .. important::
        Must have ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    reward_id: str
        Optional to only get notifications for a specific reward.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.channel_points_custom_reward_redemption.update"]] = (
        "channel.channel_points_custom_reward_redemption.update"
    )
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.reward_id: str = condition.get("reward_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "reward_id": self.reward_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPollBeginSubscription(SubscriptionPayload):
    """The ``channel.poll.begin`` subscription type sends a notification when a poll begins on the specified channel.

    .. important::
        Must have ``channel:read:polls`` or ``channel:manage:polls`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.poll.begin"]] = "channel.poll.begin"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPollProgressSubscription(SubscriptionPayload):
    """The ``channel.poll.progress`` subscription type sends a notification when users respond to a poll on the specified channel.

    .. important::
        Must have ``channel:read:polls`` or ``channel:manage:polls`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.poll.progress"]] = "channel.poll.progress"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPollEndSubscription(SubscriptionPayload):
    """The ``channel.poll.end`` subscription type sends a notification when a poll ends on the specified channel.

    .. important::
        Must have ``channel:read:polls`` or ``channel:manage:polls`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.poll.end"]] = "channel.poll.end"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPredictionBeginSubscription(SubscriptionPayload):
    """The ``channel.prediction.begin`` subscription type sends a notification when a Prediction begins on the specified channel.

    .. important::
        Must have ``channel:read:predictions`` or ``channel:manage:predictions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.prediction.begin"]] = "channel.prediction.begin"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPredictionLockSubscription(SubscriptionPayload):
    """The ``channel.prediction.lock`` subscription type sends a notification when a Prediction is locked on the specified channel.

    .. important::
        Must have ``channel:read:predictions`` or ``channel:manage:predictions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.prediction.lock"]] = "channel.prediction.lock"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPredictionProgressSubscription(SubscriptionPayload):
    """The ``channel.prediction.progress`` subscription type sends a notification when users participate in a Prediction on the specified channel.

    .. important::
        Must have ``channel:read:predictions`` or ``channel:manage:predictions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.prediction.progress"]] = "channel.prediction.progress"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelPredictionEndSubscription(SubscriptionPayload):
    """The ``channel.prediction.end`` subscription type sends a notification when a Prediction ends on the specified channel.

    .. important::
        Must have ``channel:read:predictions`` or ``channel:manage:predictions`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.prediction.end"]] = "channel.prediction.end"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class SuspiciousUserUpdateSubscription(SubscriptionPayload):
    """The ``channel.suspicious_user.update`` subscription type sends a notification when a suspicious user has been updated.

    .. important::
        Requires the ``moderator:read:suspicious_users scope``.

        If you use webhooks, the user in moderator_user_id must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        If you use WebSockets, the ID in moderator_user_id must match the user ID in the user access token.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.suspicious_user.update"]] = "channel.suspicious_user.update"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class SuspiciousUserMessageSubscription(SubscriptionPayload):
    """The ``channel.suspicious_user.message`` subscription type sends a notification when a chat message has been sent from a suspicious user.

    .. important::
        Requires the ``moderator:read:suspicious_users scope``.

        If you use webhooks, the user in moderator_user_id must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        If you use WebSockets, the ID in moderator_user_id must match the user ID in the user access token.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.suspicious_user.message"]] = "channel.suspicious_user.message"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelVIPAddSubscription(SubscriptionPayload):
    """The ``channel.vip.add`` subscription type sends a notification when a VIP is added to the channel.

    .. important::
        Must have ``channel:read:vips`` or ``channel:manage:vips`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.vip.add"]] = "channel.vip.add"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelVIPRemoveSubscription(SubscriptionPayload):
    """The ``channel.vip.remove`` subscription type sends a notification when a VIP is removed from the channel.

    .. important::
        Must have ``channel:read:vips`` or ``channel:manage:vips`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.vip.remove"]] = "channel.vip.remove"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ChannelWarningAcknowledgementSubscription(SubscriptionPayload):
    """The ``channel.warning.acknowledge`` subscription type sends a notification when a warning is acknowledged by a user.
    Broadcasters and moderators can see the warning's details.

    .. important::
        Must have the ``moderator:read:warnings`` or ``moderator:manage:warnings`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.warning.acknowledge"]] = "channel.warning.acknowledge"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ChannelWarningSendSubscription(SubscriptionPayload):
    """The ``channel.warning.send`` subscription type sends a notification when a warning is sent to a user.
    Broadcasters and moderators can see the warning's details.

    .. important::
        Must have the ``moderator:read:warnings`` or ``moderator:manage:warnings`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.warning.send"]] = "channel.warning.send"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class CharityDonationSubscription(SubscriptionPayload):
    """The ``channel.charity_campaign.donate`` subscription type sends a notification when a user donates to the broadcaster's charity campaign.

    .. important::
        Must have ``channel:read:charity`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.charity_campaign.donate"]] = "channel.charity_campaign.donate"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class CharityCampaignStartSubscription(SubscriptionPayload):
    """The ``channel.charity_campaign.start`` subscription type sends a notification when the broadcaster starts a charity campaign.

    .. note::
        It's possible to receive this event after the Progress event.

    .. important::
        Must have ``channel:read:charity`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.charity_campaign.start"]] = "channel.charity_campaign.start"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class CharityCampaignProgressSubscription(SubscriptionPayload):
    """The ``channel.charity_campaign.progress`` subscription type sends a notification when progress is made towards the campaign's goal or when the broadcaster changes the fundraising goal.

    .. note::
        It's possible to receive this event before the Start event.

        To get donation information, subscribe to :meth:`CharityDonationSubscription` event.

    .. important::
        Must have ``channel:read:charity`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.charity_campaign.progress"]] = "channel.charity_campaign.progress"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class CharityCampaignStopSubscription(SubscriptionPayload):
    """The ``channel.charity_campaign.stop`` subscription type sends a notification when the broadcaster stops a charity campaign.

    .. important::
        Must have ``channel:read:charity`` scope.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.charity_campaign.stop"]] = "channel.charity_campaign.stop"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class GoalBeginSubscription(SubscriptionPayload):
    """The ``channel.goal.begin`` subscription type sends a notification when the specified broadcaster begins a goal.

    .. note::
        It's possible to receive the Begin event after receiving Progress events.

    .. important::
        Requires a user OAuth access token with scope ``channel:read:goals``.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.goal.begin"]] = "channel.goal.begin"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class GoalProgressSubscription(SubscriptionPayload):
    """The ``channel.goal.progress`` subscription type sends a notification when progress is made towards the specified broadcaster's goal.
    Progress could be positive (added followers) or negative (lost followers).

    .. note::
        It's possible to receive the Progress events before receiving the Begin event.

    .. important::
        Requires a user OAuth access token with scope ``channel:read:goals``.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.goal.progress"]] = "channel.goal.progress"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class GoalEndSubscription(SubscriptionPayload):
    """The ``channel.goal.end`` subscription type sends a notification when the specified broadcaster ends a goal.

    .. important::
        Requires a user OAuth access token with scope ``channel:read:goals``.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.goal.end"]] = "channel.goal.end"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class HypeTrainBeginSubscription(SubscriptionPayload):
    """The ``channel.hype_train.begin`` subscription type sends a notification when a Hype Train begins on the specified channel.

    .. important::
        Requires a user OAuth access token with scope ``channel:read:hype_train``.

    .. note::
        EventSub does not make strong assurances about the order of message delivery, so it is possible to receive `channel.hype_train.progress` notifications before you receive the corresponding `channel.hype_train.begin` notification.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.hype_train.begin"]] = "channel.hype_train.begin"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class HypeTrainProgressSubscription(SubscriptionPayload):
    """The ``channel.hype_train.progress`` subscription type sends a notification when a Hype Train makes progress on the specified channel.

    .. important::
        Requires a user OAuth access token with scope ``channel:read:hype_train``.

    .. note::
        EventSub does not make strong assurances about the order of message delivery, so it is possible to receive `channel.hype_train.progress` notifications before you receive the corresponding `channel.hype_train.begin` notification.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.hype_train.progress"]] = "channel.hype_train.progress"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class HypeTrainEndSubscription(SubscriptionPayload):
    """The ``channel.hype_train.end`` subscription type sends a notification when a Hype Train ends on the specified channel.

    .. important::
        Requires a user OAuth access token with scope ``channel:read:hype_train``.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.hype_train.end"]] = "channel.hype_train.end"
    version: ClassVar[Literal["2"]] = "2"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}

    @property
    def default_auth(self) -> DefaultAuthDict:
        return {"as_bot": False, "token_for": self.broadcaster_user_id}


class ShieldModeBeginSubscription(SubscriptionPayload):
    """The ``channel.shield_mode.begin`` subscription type sends a notification when the broadcaster activates Shield Mode.

    This event informs the subscriber that the broadcaster's moderation settings were changed  based on the broadcaster's Shield Mode configuration settings.

    .. important::
        Requires the ``moderator:read:shield_mode`` or ``moderator:manage:shield_mode`` scope.

        - If you use webhooks, the moderator must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        - If you use WebSockets, the moderator's ID must match the user ID in the user access token.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shield_mode.begin"]] = "channel.shield_mode.begin"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ShieldModeEndSubscription(SubscriptionPayload):
    """The ``channel.shield_mode.end`` subscription type sends a notification when the broadcaster deactivates Shield Mode.

    This event informs the subscriber that the broadcaster's moderation settings were changed back to the broadcaster's previous moderation settings.

    .. important::
        Requires the ``moderator:read:shield_mode`` or ``moderator:manage:shield_mode`` scope.

        - If you use webhooks, the moderator must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        - If you use WebSockets, the moderator's ID must match the user ID in the user access token.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shield_mode.end"]] = "channel.shield_mode.end"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ShoutoutCreateSubscription(SubscriptionPayload):
    """The ``channel.shoutout.create`` subscription type sends a notification when the specified broadcaster sends a shoutout.

    .. important::
        Requires the ``moderator:read:shoutouts`` or ``moderator:manage:shoutouts`` scope.

        - If you use webhooks, the moderator must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        - If you use WebSockets, the moderator's ID must match the user ID in the user access token.

    .. note::
        This is only sent if Twitch posts the Shoutout to the broadcaster's activity feed.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shoutout.create"]] = "channel.shoutout.create"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster_user_id" and "moderator_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class ShoutoutReceiveSubscription(SubscriptionPayload):
    """The ``channel.shoutout.receive`` subscription type sends a notification when the specified broadcaster receives a shoutout.

    .. important::
        Requires the ``moderator:read:shoutouts`` or ``moderator:manage:shoutouts`` scope.

        - If you use webhooks, the moderator must have granted your app (client ID) one of the above permissions prior to your app subscribing to this subscription type.

        - If you use WebSockets, the moderator's ID must match the user ID in the user access token.

    .. note::
        This is only sent if Twitch posts the Shoutout to the broadcaster's activity feed.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.
    moderator_user_id: str | PartialUser
        The ID, or PartialUser, of a moderator for the the broadcaster you are subscribing to. This could also be the broadcaster.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["channel.shoutout.receive"]] = "channel.shoutout.receive"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")
        self.moderator_user_id: str = condition.get("moderator_user_id", "")

        if not self.broadcaster_user_id or not self.moderator_user_id:
            raise ValueError('The parameters "broadcaster" and "moderator" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id, "moderator_user_id": self.moderator_user_id}


class StreamOnlineSubscription(SubscriptionPayload):
    """The ``stream.online`` subscription type sends a notification when the specified broadcaster starts a stream.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["stream.online"]] = "stream.online"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class StreamOfflineSubscription(SubscriptionPayload):
    """The ``stream.offline`` subscription type sends a notification when the specified broadcaster stops a stream.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    broadcaster_user_id: str | PartialUser
        The ID, or PartialUser, of the broadcaster to subscribe to.

    Raises
    ------
    ValueError
        The parameter "broadcaster_user_id" must be passed.
    """

    type: ClassVar[Literal["stream.offline"]] = "stream.offline"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.broadcaster_user_id: str = condition.get("broadcaster_user_id", "")

        if not self.broadcaster_user_id:
            raise ValueError('The parameter "broadcaster_user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"broadcaster_user_id": self.broadcaster_user_id}


class UserAuthorizationGrantSubscription(SubscriptionPayload):
    """The ``user.authorization.grant`` subscription type sends a notification when a user's authorization has been granted to your client id.

    .. important::
        This subscription type is **only** supported by **webhooks**, and cannot be used with WebSockets.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    client_id: str
        Provided client_id must match the client id in the application access token.

    Raises
    ------
    ValueError
        The parameter "client_id" must be passed.
    """

    type: ClassVar[Literal["user.authorization.grant"]] = "user.authorization.grant"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.client_id: str = condition.get("client_id", "")

        if not self.client_id:
            raise ValueError('The parameter "client_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"client_id": self.client_id}


class UserAuthorizationRevokeSubscription(SubscriptionPayload):
    """The ``user.authorization.revoke`` subscription type sends a notification when a user's authorization has been revoked for your client id.
    Use this `webhook` to meet government requirements for handling user data, such as GDPR, LGPD, or CCPA.

    .. important::
        This subscription type is **only** supported by **webhooks**, and cannot be used with WebSockets.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    client_id: str
        Provided client_id must match the client id in the application access token.

    Raises
    ------
    ValueError
        The parameter "client_id" must be passed.
    """

    type: ClassVar[Literal["user.authorization.revoke"]] = "user.authorization.revoke"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.client_id: str = condition.get("client_id", "")

        if not self.client_id:
            raise ValueError('The parameter "client_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"client_id": self.client_id}


class UserUpdateSubscription(SubscriptionPayload):
    """The ``user.update`` subscription type sends a notification when user updates their account.

    .. note::
        No authorization required. If you have the ``user:read:email`` scope, the notification will include email field.

        If the user no longer exists then the login attribute will be None.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    user_id: str | PartialUser
        The ID, or PartialUser, of the user receiving the whispers you wish to subscribe to.

    Raises
    ------
    ValueError
        The parameter "user_id" must be passed.
    """

    type: ClassVar[Literal["user.update"]] = "user.update"
    version: ClassVar[Literal["1"]] = "1"

    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.user_id: str = condition.get("user_id", "")

        if not self.user_id:
            raise ValueError('The parameter "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"user_id": self.user_id}


class WhisperReceivedSubscription(SubscriptionPayload):
    """The ``user.whisper.message`` subscription type sends a notification when a user receives a whisper.

    .. important::
        Must have oauth scope ``user:read:whispers`` or ``user:manage:whispers``.

    One attribute ``.condition`` can be accessed from this class, which returns a mapping of the subscription
    parameters provided.

    Parameters
    ----------
    user_id: str | PartialUser
        The ID, or PartialUser, of the user receiving the whispers you wish to subscribe to.

    Raises
    ------
    ValueError
        The parameter "user_id" must be passed.
    """

    type: ClassVar[Literal["user.whisper.message"]] = "user.whisper.message"
    version: ClassVar[Literal["1"]] = "1"

    @handle_user_ids()
    def __init__(self, **condition: Unpack[Condition]) -> None:
        self.user_id: str = condition.get("user_id", "")

        if not self.user_id:
            raise ValueError('The parameter "user_id" must be passed.')

    @property
    def condition(self) -> Condition:
        return {"user_id": self.user_id}
