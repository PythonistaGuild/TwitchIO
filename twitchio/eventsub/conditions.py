"""MIT License

Copyright (c) 2025 - Present Evie. P., Chillymosh and TwitchIO

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

from typing import NotRequired, Required, TypedDict

# TODO: __all__
# TODO: Accept Partial/User etc objects??


class _BroadcasterCT(TypedDict):
    """
    broadcaster_user_id: str
        The ID of the broadcaster/channel for this event.
    """

    broadcaster_user_id: Required[str]


class _BroadcasterIdCT(TypedDict):
    """
    broadcaster_id: str
        The ID of the broadcaster/channel for this event.
    """

    broadcaster_id: Required[str]


class _ModeratorCT(TypedDict):
    """
    moderator_user_id: str
        The ID of the moderator to subscribe with for this event.
    """

    moderator_user_id: Required[str]


class _UserCT(TypedDict):
    """
    user_id: str
        The ID of the user associated with this event.
    """

    user_id: Required[str]


class _RewardCT(TypedDict):
    reward_id: NotRequired[str]


class _ClientCT(TypedDict):
    client_id: Required[str]


class _BroadcasterModeratorCT(_BroadcasterCT, _ModeratorCT):
    __doc__ = f"""{_BroadcasterCT.__doc__.strip()}{_ModeratorCT.__doc__}"""  # type: ignore


class _BroadcasterUserCT(_BroadcasterCT, _UserCT):
    __doc__ = f"""{_BroadcasterCT.__doc__.strip()}{_UserCT.__doc__}"""  # type: ignore


class _BroadcasterRewardCT(_BroadcasterCT, _RewardCT):
    __doc__ = f"""{_BroadcasterCT.__doc__.strip()}{_RewardCT.__doc__}"""  # type: ignore


# -----------------------------------------------------------
# Condition Payloads:


type AnyCondition = (
    AutomodMessageHoldCT
    | AutomodMessageUpdateCT
    | AutomodSettingsUpdateCT
    | AutomodTermsUpdateCT
    | ChannelAdBreakBeginCT
    | ChannelBanCT
    | ChannelBitUseCT
    | ChannelChatClearCT
    | ChannelChatClearUserMessagesCT
    | ChannelChatMessageCT
    | ChannelChatMessageDeleteCT
    | ChannelChatNotificationCT
    | ChannelChatSettingsUpdateCT
    | ChannelChatUserMessageHoldCT
    | ChannelChatUserMessageUpdate
    | ChannelSubscribeCT
    | ChannelSubscriptionEndCT
    | ChannelSubscriptionGiftCT
    | ChannelSubscriptionMessageCT
    | ChannelCheerCT
    | ChannelUpdateCT
    | ChannelFollowCT
    | ChannelUnbanCT
    | ChannelUnbanRequestCreateCT
    | ChannelUnbanRequestResolveCT
    | ChannelRaidCT
    | ChannelModerateCT
    | ChannelModeratorAddCT
    | ChannelModeratorRemoveCT
    | ChannelGuestStarSessionBeginCT
    | ChannelGuestStarSessionEndCT
    | ChannelGuestStarGuestUpdate
    | ChannelGuestStarSettingsUpdate
    | ChannelPointsAutomaticRewardRedemptionAddCT
    | ChannelPointsCustomRewardAddCT
    | ChannelPointsCustomRewardUpdateCT
    | ChannelPointsCustomRewardRemoveCT
    | ChannelPointsCustomRewardRedemptionAddCT
    | ChannelPointsCustomRewardRedemptionUpdateCT
    | ChannelPollBeginCT
    | ChannelPollProgressCT
    | ChannelPollEndCT
    | ChannelPredictionBeginCT
    | ChannelPredictionProgressCT
    | ChannelPredictionLockCT
    | ChannelPredictionEndCT
    | ChannelSharedChatSessionBeginCT
    | ChannelSharedChatSessionUpdateCT
    | ChannelSharedChatSessionEndCT
    | ChannelSuspiciousUserMessageCT
    | ChannelSuspiciousUserUpdateCT
    | ChannelVIPAddCT
    | ChannelVIPRemoveCT
    | ChannelWarningAcknowledgeCT
    | ChannelWarningSendCT
    | ConduitShardDisabledCT
    | DropEntitlementGrantCT
    | ExtensionBitsTransactionCreateCT
    | GoalsCT
    | HypeTrainBeginCT
    | HypeTrainProgressCT
    | HypeTrainEndCT
    | StreamOnlineCT
    | StreamOfflineCT
    | UserAuthorizationGrantCT
    | UserAuthorizationRevokeCT
    | UserUpdateCT
    | WhisperReceivedCT
)


class AutomodMessageHoldCT(_BroadcasterModeratorCT): ...


class AutomodMessageUpdateCT(_BroadcasterModeratorCT): ...


class AutomodSettingsUpdateCT(_BroadcasterModeratorCT): ...


class AutomodTermsUpdateCT(_BroadcasterModeratorCT): ...


class ChannelAdBreakBeginCT(_BroadcasterIdCT): ...


class ChannelBanCT(_BroadcasterCT): ...


class ChannelBitUseCT(_BroadcasterCT): ...


class ChannelChatClearCT(_BroadcasterUserCT): ...


class ChannelChatClearUserMessagesCT(_BroadcasterUserCT): ...


class ChannelChatMessageCT(_BroadcasterUserCT): ...


class ChannelChatMessageDeleteCT(_BroadcasterUserCT): ...


class ChannelChatNotificationCT(_BroadcasterUserCT): ...


class ChannelChatSettingsUpdateCT(_BroadcasterUserCT): ...


class ChannelChatUserMessageHoldCT(_BroadcasterUserCT): ...


class ChannelChatUserMessageUpdate(_BroadcasterUserCT): ...


class ChannelSubscribeCT(_BroadcasterCT): ...


class ChannelSubscriptionEndCT(_BroadcasterCT): ...


class ChannelSubscriptionGiftCT(_BroadcasterCT): ...


class ChannelSubscriptionMessageCT(_BroadcasterCT): ...


class ChannelCheerCT(_BroadcasterCT): ...


class ChannelUpdateCT(_BroadcasterCT): ...


class ChannelFollowCT(_BroadcasterModeratorCT): ...


class ChannelUnbanCT(_BroadcasterCT): ...


class ChannelUnbanRequestCreateCT(_BroadcasterModeratorCT): ...


class ChannelUnbanRequestResolveCT(_BroadcasterModeratorCT): ...


class ChannelRaidCT(TypedDict, total=False):
    from_broadcaster_user_id: str
    to_broadcaster_user_id: str


# NOTE: Includes V2
class ChannelModerateCT(_BroadcasterModeratorCT): ...


class ChannelModeratorAddCT(_BroadcasterCT): ...


class ChannelModeratorRemoveCT(_BroadcasterCT): ...


class ChannelGuestStarSessionBeginCT(_BroadcasterModeratorCT): ...


class ChannelGuestStarSessionEndCT(_BroadcasterModeratorCT): ...


class ChannelGuestStarGuestUpdate(_BroadcasterModeratorCT): ...


class ChannelGuestStarSettingsUpdate(_BroadcasterModeratorCT): ...


# NOTE: Includes V2
class ChannelPointsAutomaticRewardRedemptionAddCT(_BroadcasterCT): ...


class ChannelPointsCustomRewardAddCT(_BroadcasterCT): ...


class ChannelPointsCustomRewardUpdateCT(_BroadcasterRewardCT): ...


class ChannelPointsCustomRewardRemoveCT(_BroadcasterRewardCT): ...


class ChannelPointsCustomRewardRedemptionAddCT(_BroadcasterRewardCT): ...


class ChannelPointsCustomRewardRedemptionUpdateCT(_BroadcasterRewardCT): ...


class ChannelPollBeginCT(_BroadcasterCT): ...


class ChannelPollProgressCT(_BroadcasterCT): ...


class ChannelPollEndCT(_BroadcasterCT): ...


class ChannelPredictionBeginCT(_BroadcasterCT): ...


class ChannelPredictionProgressCT(_BroadcasterCT): ...


class ChannelPredictionLockCT(_BroadcasterCT): ...


class ChannelPredictionEndCT(_BroadcasterCT): ...


class ChannelSharedChatSessionBeginCT(_BroadcasterCT): ...


class ChannelSharedChatSessionUpdateCT(_BroadcasterCT): ...


class ChannelSharedChatSessionEndCT(_BroadcasterCT): ...


class ChannelSuspiciousUserMessageCT(_BroadcasterModeratorCT): ...


class ChannelSuspiciousUserUpdateCT(_BroadcasterModeratorCT): ...


class ChannelVIPAddCT(_BroadcasterCT): ...


class ChannelVIPRemoveCT(_BroadcasterCT): ...


class ChannelWarningAcknowledgeCT(_BroadcasterModeratorCT): ...


class ChannelWarningSendCT(_BroadcasterModeratorCT): ...


class ConduitShardDisabledCT(_ClientCT):
    conduit_id: NotRequired[str]


class DropEntitlementGrantCT(TypedDict):
    organization_id: Required[str]
    category_id: NotRequired[str]
    campaign_id: NotRequired[str]


class ExtensionBitsTransactionCreateCT(TypedDict):
    extension_client_id: Required[str]


class GoalsCT(_BroadcasterCT): ...


class HypeTrainBeginCT(_BroadcasterCT): ...


class HypeTrainProgressCT(_BroadcasterCT): ...


class HypeTrainEndCT(_BroadcasterCT): ...


class StreamOnlineCT(_BroadcasterCT): ...


class StreamOfflineCT(_BroadcasterCT): ...


class UserAuthorizationGrantCT(_ClientCT): ...


class UserAuthorizationRevokeCT(_ClientCT): ...


class UserUpdateCT(_UserCT): ...


class WhisperReceivedCT(_UserCT): ...
