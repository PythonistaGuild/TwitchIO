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

from typing import TYPE_CHECKING, Literal

from .assets import Asset
from .exceptions import HTTPException, MessageRejectedError
from .models.ads import AdSchedule, CommercialStart, SnoozeAd
from .models.raids import Raid
from .utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.types_.responses import (
        UserActiveExtensionsResponseData,
        UserExtensionsResponseData,
        UserPanelComponentItem,
        UserPanelItem,
        UserPanelOverlayItem,
        UsersResponseData,
    )

    from .http import HTTPAsyncIterator, HTTPClient
    from .models.analytics import ExtensionAnalytics, GameAnalytics
    from .models.bits import BitsLeaderboard
    from .models.channel_points import CustomReward
    from .models.channels import ChannelEditor, ChannelFollowerEvent, ChannelFollowers, ChannelInfo, FollowedChannels
    from .models.charity import CharityCampaign, CharityDonation
    from .models.chat import ChannelEmote, ChatBadge, ChatSettings, Chatters, SentMessage, SharedChatSession, UserEmote
    from .models.clips import Clip, CreatedClip
    from .models.eventsub_ import ChannelChatMessageEvent, ChatMessageBadge
    from .models.goals import Goal
    from .models.hype_train import HypeTrainEvent
    from .models.moderation import (
        AutomodCheckMessage,
        AutomodSettings,
        AutoModStatus,
        Ban,
        BannedUser,
        BlockedTerm,
        ShieldModeStatus,
        Timeout,
        UnbanRequest,
        Warning,
    )
    from .models.polls import Poll
    from .models.predictions import Prediction
    from .models.schedule import Schedule
    from .models.streams import Stream, StreamMarker, VideoMarkers
    from .models.subscriptions import BroadcasterSubscriptions, UserSubscription
    from .models.teams import ChannelTeam

__all__ = ("ActiveExtensions", "Extension", "PartialUser", "User")


class PartialUser:
    """A class that contains minimal data about a user from the API.

    Any API calls pertaining to a user / broadcaster / channel will be on this object.

    Attributes
    -----------
    id: str | int
        The user's ID.
    name: str | None
        The user's name. Also known as *username* or *login name*. In most cases, this is provided. There are however, rare cases where it is not.
    display_name: str | None
        The user's display name in chat. In most cases, this is provided otherwise fallsback to `name`. There are however, rare cases where it is not.
    """

    __slots__ = "_cached_rewards", "_http", "display_name", "id", "name"

    def __init__(self, id: str | int, name: str | None = None, display_name: str | None = None, *, http: HTTPClient) -> None:
        self._http = http
        self.id = str(id)
        self.name = name
        self.display_name = display_name or name

    def __repr__(self) -> str:
        return f"<PartialUser id={self.id} name={self.name}>"

    def __str__(self) -> str:
        return self.name or "..."

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (PartialUser, User, Chatter)):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def mention(self) -> str:
        """Property returning the users display_name formatted to mention them in chat.

        E.g. "@kappa"
        """
        return f"@{self.display_name or '...'}"

    async def start_commercial(self, *, length: int) -> CommercialStart:
        """|coro|

        Starts a commercial on the specified channel.

        .. important::
            Only partners and affiliates may run commercials and they must be streaming live at the time.

            Only the broadcaster may start a commercial; the broadcaster's editors and moderators may not start commercials on behalf of the broadcaster.

        .. note::
            Requires user access token that includes the ``channel:edit:commercial`` scope.

        Parameters
        ----------
        length: int
            The length of the commercial to run, in seconds. Max length is 180.
            If you request a commercial that's longer than 180 seconds, the API uses 180 seconds.

        Returns
        -------
        CommercialStart
            A CommercialStart object.
        """
        data = await self._http.start_commercial(broadcaster_id=self.id, length=length, token_for=self.id)
        return CommercialStart(data["data"][0])

    async def fetch_ad_schedule(self) -> AdSchedule:
        """|coro|

        Fetch ad schedule related information, including snooze, when the last ad was run, when the next ad is scheduled, and if the channel is currently in pre-roll free time.

        .. important::
            A new ad cannot be run until 8 minutes after running a previous ad.

            The user id in the user access token must match the id of this PartialUser object.

        .. note::
            Requires user access token that includes the ``channel:read:ads`` scope.

        Returns
        -------
        AdSchedule
            An AdSchedule object.
        """
        data = await self._http.get_ad_schedule(broadcaster_id=self.id, token_for=self.id)
        return AdSchedule(data["data"][0])

    async def snooze_next_ad(self) -> SnoozeAd:
        """|coro|

        If available, pushes back the timestamp of the upcoming automatic mid-roll ad by 5 minutes.
        This endpoint duplicates the snooze functionality in the creator dashboard's Ads Manager.

        .. important::
            The user id in the user access token must match the id of this PartialUser object.

        .. note::
            Requires user access token that includes the ``channel:manage:ads`` scope.

        Returns
        -------
        SnoozeAd
            A SnoozeAd object.
        """
        data = await self._http.post_snooze_ad(broadcaster_id=self.id, token_for=self.id)
        return SnoozeAd(data["data"][0])

    def fetch_extension_analytics(
        self,
        *,
        token_for: str | PartialUser,
        first: int = 20,
        extension_id: str | None = None,
        type: Literal["overview_v2"] = "overview_v2",
        started_at: datetime.date | None = None,
        ended_at: datetime.date | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[ExtensionAnalytics]:
        """|aiter|

        Fetches an analytics report for one or more extensions. The response contains the URLs used to download the reports (CSV files)

        .. important::
            Both ``started_at`` and ``ended_at`` must be provided when requesting a date range. They are UTC timezone by default.
            If you omit both of these then the report includes all available data from January 31, 2018.

            Because it can take up to two days for the data to be available, you must specify an end date that's earlier than today minus one to two days.
            If not, the API ignores your end date and uses an end date that is today minus one to two days.

        .. note::
            Requires user access token that includes the ``analytics:read:extensions`` scope.

        Parameters
        -----------
        token_for: str | PartialUser
            A user access token that includes the ``analytics:read:extensions`` scope.
        extension_id: str
            The extension's client ID. If specified, the response contains a report for the specified extension.
            If not specified, the response includes a report for each extension that the authenticated user owns.
        type: Literal["overview_v2"]
            The type of analytics report to get. This is set to ``overview_v2`` by default.
        started_at: datetime.date
            The date to start the report from. If you specify a start date, you must specify an end date.
        ended_at: datetime.date
            The end date for the report, this is inclusive. Specify an end date only if you provide a start date.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        HTTPAsyncIterator[ExtensionAnalytics]

        Raises
        ------
        ValueError
            Both started_at and ended_at must be provided together.
        """

        first = max(1, min(100, first))

        if bool(started_at) != bool(ended_at):
            raise ValueError("Both started_at and ended_at must be provided together.")

        return self._http.get_extension_analytics(
            first=first,
            token_for=token_for,
            extension_id=extension_id,
            type=type,
            started_at=started_at,
            ended_at=ended_at,
            max_results=max_results,
        )

    def fetch_game_analytics(
        self,
        *,
        token_for: str | PartialUser,
        first: int = 20,
        game_id: str | None = None,
        type: Literal["overview_v2"] = "overview_v2",
        started_at: datetime.date | None = None,
        ended_at: datetime.date | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[GameAnalytics]:
        """|aiter|

        Fetches a game report for one or more games. The response contains the URLs used to download the reports (CSV files)

        .. important::
            Both ``started_at`` and ``ended_at`` must be provided when requesting a date range.
            If you omit both of these then the report includes all available data from January 31, 2018.

            Because it can take up to two days for the data to be available, you must specify an end date that's earlier than today minus one to two days.
            If not, the API ignores your end date and uses an end date that is today minus one to two days.

        .. note::
            Requires user access token that includes the ``analytics:read:extensions`` scope.

        Parameters
        -----------
        token_for: str | PartialUser
            A user access token that includes the ``analytics:read:extensions`` scope.
        game_id: str
            The game's client ID. If specified, the response contains a report for the specified game.
            If not specified, the response includes a report for each of the authenticated user's games.
        type: Literal["overview_v2"]
            The type of analytics report to get. This is set to ``overview_v2`` by default.
        started_at: datetime.date
            The date to start the report from. If you specify a start date, you must specify an end date.
        ended_at: datetime.date
            The end date for the report, this is inclusive. Specify an end date only if you provide a start date.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        twitchio.HTTPAsyncIterator[GameAnalytics]

        Raises
        ------
        ValueError
            Both started_at and ended_at must be provided together.
        """

        first = max(1, min(100, first))

        if bool(started_at) != bool(ended_at):
            raise ValueError("Both started_at and ended_at must be provided together")

        return self._http.get_game_analytics(
            first=first,
            token_for=token_for,
            game_id=game_id,
            type=type,
            started_at=started_at,
            ended_at=ended_at,
            max_results=max_results,
        )

    async def fetch_bits_leaderboard(
        self,
        count: int = 10,
        period: Literal["all", "day", "week", "month", "year"] = "all",
        started_at: datetime.datetime | None = None,
        user: str | int | PartialUser | None = None,
    ) -> BitsLeaderboard:
        """|coro|

        Fetches the Bits leaderboard for this user.

        .. important::
            ``started_at`` is converted to PST before being used, so if you set the start time to 2022-01-01T00:00:00.0Z and period to month, the actual reporting period is December 2021, not January 2022.

            If you want the reporting period to be January 2022, you must set the start time to 2022-01-01T08:00:00.0Z or 2022-01-01T00:00:00.0-08:00.

            When providing ``started_at``, you must also change the ``period`` parameter to any value other than "all".

            Conversely, if `period` is set to anything other than "all", ``started_at`` must also be provided.

        .. note::
            Requires user access token that includes the ``bits:read`` scope.

        +---------+-----------------------------------------------------------------------------------------------------+
        | Period  | Description                                                                                         |
        +=========+=====================================================================================================+
        | day     | A day spans from 00:00:00 on the day specified in started_at and runs through 00:00:00 of the next  |
        |         | day.                                                                                                |
        +---------+-----------------------------------------------------------------------------------------------------+
        | week    | A week spans from 00:00:00 on the Monday of the week specified in started_at and runs through       |
        |         | 00:00:00 of the next Monday.                                                                        |
        +---------+-----------------------------------------------------------------------------------------------------+
        | month   | A month spans from 00:00:00 on the first day of the month specified in started_at and runs through  |
        |         | 00:00:00 of the first day of the next month.                                                        |
        +---------+-----------------------------------------------------------------------------------------------------+
        | year    | A year spans from 00:00:00 on the first day of the year specified in started_at and runs through    |
        |         | 00:00:00 of the first day of the next year.                                                         |
        +---------+-----------------------------------------------------------------------------------------------------+
        | all     | Default. The lifetime of the broadcaster's channel.                                                 |
        +---------+-----------------------------------------------------------------------------------------------------+


        Parameters
        ----------
        count: int
            The number of results to return. The minimum count is 1 and the maximum is 100. The default is 10.
        period: Literal["all", "day", "week", "month", "year"]
            The time period over which data is aggregated (uses the PST time zone).
        started_at: datetime.datetime | None
            The start date, used for determining the aggregation period. Specify this parameter only if you specify the period query parameter.
            The start date is ignored if period is all. This can be timezone aware.
        user: str | int | PartialUser | None
            A User ID that identifies a user that cheered bits in the channel.
            If count is greater than 1, the response may include users ranked above and below the specified user.
            To get the leaderboard's top leaders, don't specify a user ID.

        Returns
        -------
        BitsLeaderboard
            BitsLeaderboard object for a user's channel.

        Raises
        ------
        ValueError
            Count must be between 10 and 100.
        ValueError
            The 'period' parameter must be set to anything other than 'all' if 'started_at' is provided, and vice versa.
        """
        if count > 100 or count < 1:
            raise ValueError("Count must be between 10 and 100.")

        if (period != "all" and started_at is None) or (period == "all" and started_at is not None):
            raise ValueError(
                "The 'period' parameter must be set to anything other than 'all' if 'started_at' is provided, and vice versa."
            )
        from .models.bits import BitsLeaderboard

        data = await self._http.get_bits_leaderboard(
            token_for=self.id,
            count=count,
            period=period,
            started_at=started_at,
            user_id=user,
        )
        return BitsLeaderboard(data, http=self._http)

    async def fetch_channel_info(self, *, token_for: str | PartialUser | None = None) -> ChannelInfo:
        """|coro|

        Retrieve channel information for this user.

        Parameters
        -----------
        token_for: str | PartialUser | None
            An optional user token to use instead of the default app token.

        Returns
        --------
        ChannelInfo
            ChannelInfo object representing the channel information.
        """
        from .models.channels import ChannelInfo

        data = await self._http.get_channel_info(broadcaster_ids=[self.id], token_for=token_for)
        return ChannelInfo(data["data"][0], http=self._http)

    async def modify_channel(
        self,
        *,
        game_id: str | None = None,
        language: str | None = None,
        title: str | None = None,
        delay: int | None = None,
        tags: list[str] | None = None,
        classification_labels: list[
            dict[
                Literal[
                    "DebatedSocialIssuesAndPolitics",
                    "MatureGame",
                    "DrugsIntoxication",
                    "SexualThemes",
                    "ViolentGraphic",
                    "Gambling",
                    "ProfanityVulgarity",
                ],
                bool,
            ]
        ]
        | None = None,
        branded: bool | None = None,
    ) -> None:
        """|coro|

        Updates this user's channel properties.

        .. important::
            A channel may specify a maximum of 10 tags. Each tag is limited to a maximum of 25 characters and may not be an empty string or contain spaces or special characters.
            Tags are case insensitive.
            For readability, consider using camelCasing or PascalCasing.

        .. note::
            Requires user access token that includes the ``channel:manage:broadcast`` scope.

        Examples
        --------
        .. code:: python3

            import twitchio

            users: list[ChannelInfo] = await client.fetch_channels([21734222])

            msg_checks: list[AutomodCheckMessage]  = [AutomodCheckMessage(id="1234", text="Some Text"), AutomodCheckMessage(id="12345", text="Some More Text")]

            checks: list[AutoModStatus] = await users[0].check_automod_status(messages=msg_checks, token_for="21734222")


        Parameters
        -----------
        game_id: str | None
            The ID of the game that the user plays. The game is not updated if the ID isn't a game ID that Twitch recognizes. To unset this field, use '0' or '' (an empty string).
        language: str | None
            The user's preferred language. Set the value to an ISO 639-1 two-letter language code (for example, en for English).
            Set to “other” if the user's preferred language is not a Twitch supported language.
            The language isn't updated if the language code isn't a Twitch supported language.
        title: str | None
            The title of the user's stream. You may not set this field to an empty string.
        delay: int | None
            The number of seconds you want your broadcast buffered before streaming it live.
            The delay helps ensure fairness during competitive play.
            Only users with Partner status may set this field. The maximum delay is 900 seconds (15 minutes).
        tags: list[str] | None
            A list of channel-defined tags to apply to the channel. To remove all tags from the channel, set tags to an empty array. Tags help identify the content that the channel streams.
            You may set a maximum of 10 tags, each limited to 25 characters. They can not be empty strings, contain spaces or special characters.

            See `here for more information <https://help.twitch.tv/s/article/guide-to-tags>`_
        classification_labels: list[dict[Literal["DebatedSocialIssuesAndPolitics", "MatureGame", "DrugsIntoxication", "SexualThemes", "ViolentGraphic", "Gambling", "ProfanityVulgarity"], bool]] | None
            List of labels that should be set as the Channel's CCLs.
        branded: bool | None
            Boolean flag indicating if the channel has branded content.
        """

        return await self._http.patch_channel_info(
            broadcaster_id=self.id,
            token_for=self.id,
            game_id=game_id,
            language=language,
            title=title,
            delay=delay,
            tags=tags,
            classification_labels=classification_labels,
            branded_content=branded,
        )

    async def fetch_editors(self) -> list[ChannelEditor]:
        """|coro|

        Fetches a list of the user's editors for their channel.

        .. note::
            Requires user access token that includes the ``channel:manage:broadcast`` scope.

        Returns
        -------
        list[ChannelEditor]
            A list of ChannelEditor objects.
        """
        from .models.channels import ChannelEditor

        data = await self._http.get_channel_editors(broadcaster_id=self.id, token_for=self.id)
        return [ChannelEditor(d, http=self._http) for d in data["data"]]

    async def fetch_followed_channels(
        self,
        broadcaster: str | int | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> FollowedChannels | None:
        """|coro|

        Fetches information of who and when this user followed other channels.

        .. note::
            Requires user access token that includes the ``user:read:follows`` scope.

        Parameters
        -----------
        broadcaster: str | int | PartialUser | None
            Provide a User ID, or PartialUser, to check whether the user follows this broadcaster.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        FollowedChannels
            FollowedChannels object.
        """

        return await self._http.get_followed_channels(
            user_id=self.id,
            token_for=self.id,
            broadcaster_id=broadcaster,
            first=first,
            max_results=max_results,
        )

    async def fetch_followers(
        self,
        user: str | int | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
        token_for: str | PartialUser | None = None,
    ) -> ChannelFollowers:
        """|coro|

        Fetches information of who and when users followed this channel.

        .. important::
            The user ID in the token must match that of the broadcaster or a moderator.

        .. note::
            Requires user access token that includes the ``moderator:read:followers`` scope.

        Parameters
        -----------
        user: str | int | PartialUser | None
            Provide a User ID, or PartialUser, to check whether the user follows this broadcaster.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.
        token_for: str | PartialUser | None
            An optional user token, for a moderator, to use instead of the User's token that this method is called on.


        Returns
        -------
        ChannelFollowers
            A ChannelFollowers object.
        """

        return await self._http.get_channel_followers(
            broadcaster_id=self.id,
            token_for=token_for or self.id,
            user_id=user,
            first=first,
            max_results=max_results,
        )

    async def create_custom_reward(
        self,
        title: str,
        cost: int,
        *,
        prompt: str | None = None,
        enabled: bool = True,
        background_color: str | Colour | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        redemptions_skip_queue: bool = False,
    ) -> CustomReward:
        """|coro|

        Creates a Custom Reward in the broadcaster's channel.

        .. note::
            The maximum number of custom rewards per channel is 50, which includes both enabled and disabled rewards.

        .. note::
            Requires user access token that includes the channel:manage:redemptions scope.

        Parameters
        -----------
        title: str
            The custom reward's title. The title may contain a maximum of 45 characters and it must be unique amongst all of the broadcaster's custom rewards.
        cost: int
            The cost of the reward, in Channel Points. The minimum is 1 point.
        prompt: str | None
            The prompt shown to the viewer when they redeem the reward. The prompt is limited to a maximum of 200 characters.
            If provided, the user must input a message when redeeming the reward.
        enabled: bool
            A Boolean value that determines whether the reward is enabled. Viewers see only enabled rewards. The default is True.
        background_color: str | Colour | None
            The background color to use for the reward. Specify the color using Hex format (for example, #9147FF).
            This can also be a [`.Colour`][twitchio.utils.Colour] object.
        max_per_stream: int | None
            The maximum number of redemptions allowed per live stream. Minimum value is 1.
        max_per_user: int | None
            The maximum number of redemptions allowed per user per stream. Minimum value is 1.
        global_cooldown: int | None
            The cooldown period, in seconds. The minimum value is 1; however, the minimum value is 60 for it to be shown in the Twitch UX.
        redemptions_skip_queue: bool
            A Boolean value that determines whether redemptions should be set to FULFILLED status immediately when a reward is redeemed. If False, status is set to UNFULFILLED and follows the normal request queue process. The default is False.

        Returns
        --------
        CustomReward
            Information regarding the custom reward.

        Raises
        ------
        ValueError
            title must be a maximum of 45 characters.
        ValueError
            prompt must be a maximum of 200 characters.
        ValueError
            Minimum value must be at least 1.
        """

        if len(title) > 45:
            raise ValueError("title must be a maximum of 45 characters.")
        if cost < 1:
            raise ValueError("cost must be at least 1.")
        if prompt is not None and len(prompt) > 200:
            raise ValueError("prompt must be a maximum of 200 characters.")
        if max_per_stream is not None and max_per_stream < 1:
            raise ValueError("max_per_stream must be at least 1.")
        if max_per_user is not None and max_per_user < 1:
            raise ValueError("max_per_user must be at least 1.")
        if global_cooldown is not None and global_cooldown < 1:
            raise ValueError("global_cooldown must be at least 1.")

        from .models.channel_points import CustomReward

        data = await self._http.post_custom_reward(
            broadcaster_id=self.id,
            token_for=self.id,
            title=title,
            cost=cost,
            prompt=prompt,
            enabled=enabled,
            background_color=background_color,
            max_per_stream=max_per_stream,
            max_per_user=max_per_user,
            global_cooldown=global_cooldown,
            skip_queue=redemptions_skip_queue,
        )
        return CustomReward(data["data"][0], http=self._http)

    async def fetch_custom_rewards(self, *, ids: list[str] | None = None, manageable: bool = False) -> list[CustomReward]:
        """|coro|

        Fetches list of custom rewards that the specified broadcaster created.

        .. note::
            Requires user access token that includes the ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

        Parameters
        ----------
        ids: list[str] | None
            A list of IDs to filter the rewards by. You may request a maximum of 50.
        manageable: bool | None
            A Boolean value that determines whether the response contains only the custom rewards that the app (Client ID) may manage.
            Default is False.

        Returns
        -------
        list[CustomReward]
            _description_
        """
        from .models.channel_points import CustomReward

        data = await self._http.get_custom_reward(
            broadcaster_id=self.id, reward_ids=ids, manageable=manageable, token_for=self.id
        )
        return [CustomReward(d, http=self._http) for d in data["data"]]

    async def fetch_charity_campaign(self) -> CharityCampaign:
        """|coro|

        Fetch the active charity campaign of a broadcaster.

        .. note::
            Requires user access token that includes the ``channel:read:charity`` scope.

        Returns
        -------
        CharityCampaign
            A CharityCampaign object.
        """
        from .models.charity import CharityCampaign

        data = await self._http.get_charity_campaign(broadcaster_id=self.id, token_for=self.id)
        return CharityCampaign(data["data"][0], http=self._http)

    def fetch_charity_donations(
        self,
        *,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[CharityDonation]:
        """|aiter|

        Fetches information about all broadcasts on Twitch.

        .. note::
            Requires user access token that includes the ``channel:read:charity`` scope.

        Parameters
        -----------
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        HTTPAsyncIterator[CharityDonation]
        """

        first = max(1, min(100, first))

        return self._http.get_charity_donations(
            broadcaster_id=self.id,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    async def fetch_chatters(
        self,
        *,
        moderator: str | int | PartialUser,  # TODO Default to bot_id, same for token_for.
        first: int = 100,
        max_results: int | None = None,
    ) -> Chatters:
        """|coro|

        Fetches users that are connected to the broadcaster's chat session.

        .. note::
            Requires user access token that includes the ``moderator:read:chatters`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or one of the broadcaster's moderators.
            This ID must match the user ID in the user access token.
        first: int | None
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 1,000. The default is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        Chatters
            A Chatters object containing the information of a broadcaster's connected chatters.
        """
        first = max(1, min(1000, first))

        return await self._http.get_chatters(
            token_for=moderator, first=first, broadcaster_id=self.id, moderator_id=moderator, max_results=max_results
        )

    async def fetch_channel_emotes(self, token_for: str | PartialUser | None = None) -> list[ChannelEmote]:
        """|coro|

        Fetches the broadcaster's list of custom emotes.

        Broadcasters create these custom emotes for users who subscribe to or follow the channel or cheer Bits in the channel's chat window.

        Parameters
        ----------
        token_for: str | PartialUser | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        list[ChannelEmote]
            A list of ChannelEmote objects
        """

        from twitchio.models.chat import ChannelEmote

        data = await self._http.get_channel_emotes(broadcaster_id=self.id, token_for=token_for)
        template = data["template"]
        return [ChannelEmote(d, template=template, http=self._http) for d in data["data"]]

    def fetch_user_emotes(
        self,
        *,
        broadcaster: str | int | PartialUser | None = None,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[UserEmote]:
        """|aiter|

        Fetches the broadcaster's list of custom emotes.

        Broadcasters create these custom emotes for users who subscribe to or follow the channel or cheer Bits in the channel's chat window.

        .. note::
            Requires user access token that includes the ``user:read:emotes`` scope.

        Parameters
        ----------
        broadcaster: str | int | PartialUser | None
            The User ID, or PartialUser, of a broadcaster you wish to get follower emotes of. Using this query parameter will guarantee inclusion of the broadcaster's follower emotes in the response body.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[UserEmote]
        """

        return self._http.get_user_emotes(
            user_id=self.id,
            token_for=self.id,
            broadcaster_id=broadcaster,
            max_results=max_results,
        )

    async def fetch_badges(self, token_for: str | PartialUser | None = None) -> list[ChatBadge]:
        """|coro|

        Fetches the broadcaster's list of custom chat badges.

        If you wish to fetch globally available chat badges use If you wish to fetch a specific broadcaster's chat badges use [`client.fetch_badges`][twitchio.client.fetch_badges]

        Parameters
        ----------
        token_for: str | PartialUser | None
            An optional user token to use instead of the default app token.

        Returns
        --------
        list[ChatBadge]
            A list of ChatBadge objects belonging to the user.
        """
        from .models.chat import ChatBadge

        data = await self._http.get_channel_chat_badges(broadcaster_id=self.id, token_for=token_for)
        return [ChatBadge(d, http=self._http) for d in data["data"]]

    async def fetch_chat_settings(
        self, *, moderator: str | int | PartialUser | None = None, token_for: str | PartialUser | None = None
    ) -> ChatSettings:
        """|coro|

        Fetches the broadcaster's chat settings.

        .. note::
            If you wish to view ``non_moderator_chat_delay`` and ``non_moderator_chat_delay_duration`` then you will need to provide a moderator, which can be
            either the broadcaster's or a moderators'. The token must include the ``moderator:read:chat_settings`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser | None
            The ID, or PartialUser, of the broadcaster or one of the broadcaster's moderators.
            This field is only required if you want to include the ``non_moderator_chat_delay`` and ``non_moderator_chat_delay_duration`` settings in the response.
            If you specify this field, this ID must match the user ID in the user access token.

        token_for: str | PartialUser | None
            If you need the response to contain ``non_moderator_chat_delay`` and ``non_moderator_chat_delay_duration`` then you will provide a token for the user in ``moderator``.
            The required scope is ``moderator:read:chat_settings``.
            Otherwise it is an optional user token to use instead of the default app token.

        Returns
        -------
        ChatSettings
            ChatSettings object of the broadcaster's chat settings.
        """
        from .models.chat import ChatSettings

        data = await self._http.get_channel_chat_settings(
            broadcaster_id=self.id, moderator_id=moderator, token_for=token_for
        )
        return ChatSettings(data["data"][0], http=self._http)

    async def update_chat_settings(
        self,
        moderator: str | int | PartialUser,
        emote_mode: bool | None = None,
        follower_mode: bool | None = None,
        follower_mode_duration: int | None = None,
        slow_mode: bool | None = None,
        slow_mode_wait_time: int | None = None,
        subscriber_mode: bool | None = None,
        unique_chat_mode: bool | None = None,
        non_moderator_chat_delay: bool | None = None,
        non_moderator_chat_delay_duration: Literal[2, 4, 6] | None = None,
    ) -> ChatSettings:
        """|coro|

        Update the user's chat settings.

        .. note::
            - To set the ``slow_mode_wait_time`` or ``follower_mode_duration`` field to its default value, set the corresponding ``slow_mode`` or ``follower_mode`` field to True (and don't include the ``slow_mode_wait_time`` or ``follower_mode_duration`` field).

            - To set the ``slow_mode_wait_time``, ``follower_mode_duration``, or ``non_moderator_chat_delay_duration`` field's value, you must set the corresponding ``slow_mode``, ``follower_mode``, or ``non_moderator_chat_delay`` field to True.

            - To remove the ``slow_mode_wait_time``, ``follower_mode_duration``, or ``non_moderator_chat_delay_duration`` field's value, set the corresponding ``slow_mode``, ``follower_mode``, or ``non_moderator_chat_delay`` field to False (and don't include the slow_mode_wait_time, follower_mode_duration, or non_moderator_chat_delay_duration field).

        .. note::
            Requires a user access token that includes the ``moderator:manage:chat_settings`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of a user that has permission to moderate the broadcaster's chat room, or the broadcaster's ID if they're making the update.
            This ID must match the user ID in the user access token.
        emote_mode: bool | None
            A Boolean value that determines whether chat messages must contain only emotes.
        follower_mode: bool | None
            A Boolean value that determines whether the broadcaster restricts the chat room to followers only.
        follower_mode_duration: int | None
            The length of time, in minutes, that users must follow the broadcaster before being able to participate in the chat room.
            Set only if follower_mode is True. Possible values are: 0 (no restriction) through 129600 (3 months).
        slow_mode: bool | None
            A Boolean value that determines whether the broadcaster limits how often users in the chat room are allowed to send messages.
            Set to True if the broadcaster applies a wait period between messages; otherwise, False.
        slow_mode_wait_time: int | None
            The amount of time, in seconds, that users must wait between sending messages. Set only if slow_mode is True.
            Possible values are: 3 (3 second delay) through 120 (2 minute delay). The default is 30 seconds.
        subscriber_mode: bool | None
            A Boolean value that determines whether only users that subscribe to the broadcaster's channel may talk in the chat room.
            Set to True if the broadcaster restricts the chat room to subscribers only; otherwise, False.
        unique_chat_mode: bool | None
            A Boolean value that determines whether the broadcaster requires users to post only unique messages in the chat room.
            Set to True if the broadcaster allows only unique messages; otherwise, False.
        non_moderator_chat_delay: bool | None
            A Boolean value that determines whether the broadcaster adds a short delay before chat messages appear in the chat room.
            This gives chat moderators and bots a chance to remove them before viewers can see the message.
            Set to True if the broadcaster applies a delay; otherwise, False.
        non_moderator_chat_delay_duration: Literal[2, 4, 6] | None
            The amount of time, in seconds, that messages are delayed before appearing in chat.
            Set only if non_moderator_chat_delay is True.
            Possible values in seconds: 2 (recommended), 4 and 6.

        Returns
        -------
        ChatSettings
            The newly applied chat settings.

        Raises
        ------
        ValueError
            follower_mode_duration must be below 129600
        ValueError
            slow_mode_wait_time must be between 3 and 120

        """
        if follower_mode_duration is not None and follower_mode_duration > 129600:
            raise ValueError("follower_mode_duration must be below 129600")
        if slow_mode_wait_time is not None and (slow_mode_wait_time < 3 or slow_mode_wait_time > 120):
            raise ValueError("slow_mode_wait_time must be between 3 and 120")

        from .models.chat import ChatSettings

        data = await self._http.patch_chat_settings(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            emote_mode=emote_mode,
            follower_mode=follower_mode,
            follower_mode_duration=follower_mode_duration,
            slow_mode=slow_mode,
            slow_mode_wait_time=slow_mode_wait_time,
            subscriber_mode=subscriber_mode,
            unique_chat_mode=unique_chat_mode,
            non_moderator_chat_delay=non_moderator_chat_delay,
            non_moderator_chat_delay_duration=non_moderator_chat_delay_duration,
        )

        return ChatSettings(data["data"][0], http=self._http)

    async def fetch_shared_chat_session(self, token_for: str | PartialUser | None = None) -> SharedChatSession:
        """|coro|

        Fetches the active shared chat session for a channel.

        Parameters
        ----------
        token_for: str | PartialUser | None
            An optional user token to use instead of the default app token.

        Returns
        --------
        SharedChatSession
            Object representing the user's shared chat session.
        """
        from .models.chat import SharedChatSession

        data = await self._http.get_shared_chat_session(broadcaster_id=self.id, token_for=token_for)
        return SharedChatSession(data["data"][0], http=self._http)

    async def send_announcement(
        self,
        *,
        moderator: str | int | PartialUser,
        message: str,
        color: Literal["blue", "green", "orange", "purple", "primary"] | None = None,
    ) -> None:
        """|coro|

        Sends an announcement to the broadcaster's chat room.

        .. note::
            Requires a user access token that includes the ``moderator:manage:announcements`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of a user who has permission to moderate the broadcaster's chat room,
            or the broadcaster''s ID if they're sending the announcement.

            This ID must match the user ID in the user access token.
        message: str
            The announcement to make in the broadcaster's chat room. Announcements are limited to a maximum of 500 characters;
            announcements longer than 500 characters are truncated.
        color: Literal["blue", "green", "orange", "purple", "primary"] | None
            An optional colour to use for the announcement. If set to ``"primary``" or `None`
            the channels accent colour will be used instead. Defaults to `None`.
        """
        return await self._http.post_chat_announcement(
            broadcaster_id=self.id, moderator_id=moderator, token_for=moderator, message=message, color=color
        )

    async def send_shoutout(
        self,
        *,
        to_broadcaster: str | int | PartialUser,
        moderator: str | int | PartialUser,
    ) -> None:
        """|coro|

        Sends a Shoutout to the specified broadcaster.

        .. note::
            The broadcaster may send a Shoutout once every 2 minutes. They may send the same broadcaster a Shoutout once every 60 minutes.

        .. note::
            Requires a user access token that includes the ``moderator:manage:shoutouts`` scope.

        Parameters
        ----------
        to_broadcaster: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster that's receiving the Shoutout.
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that is one of the broadcaster's moderators. This ID must match the user ID in the access token.
        """
        return await self._http.post_chat_shoutout(
            broadcaster_id=self.id, moderator_id=moderator, token_for=moderator, to_broadcaster_id=to_broadcaster
        )

    async def send_message(
        self,
        message: str,
        sender: str | int | PartialUser,
        *,
        token_for: str | PartialUser | None = None,
        reply_to_message_id: str | None = None,
        source_only: bool | None = None,
    ) -> SentMessage:
        """|coro|

        Send a message to the broadcaster's chat room.

        The PartialUser/User object this method is called on is the broadcaster / channel the message will be sent to.

        .. important::
            Requires an App Access Token or user access token that includes the ``user:write:chat`` scope.
            User access token is generally recommended.

            If an App Access Token is used, then additionally requires ``user:bot scope`` from chatting user, and either ``channel:bot scope`` from broadcaster or moderator status.
            This means creating a user token for the "bot" account with the above scopes associated to the correct Client ID. This token does not need to be used.

        .. tip::
            Chat messages can also include emoticons. To include emoticons, use the name of the emote.

            The names are case sensitive. Don't include colons around the name e.g., ``:bleedPurple:``

            If Twitch recognizes the name, Twitch converts the name to the emote before writing the chat message to the chat room.

        Parameters
        ----------
        message: str
            The message to send. The message is limited to a maximum of 500 characters.
            Chat messages can also include emoticons. To include emoticons, use the name of the emote.
            The names are case sensitive. Don't include colons around the name e.g., `:bleedPurple:`.
            If Twitch recognizes the name, Twitch converts the name to the emote before writing the chat message to the chat room
        sender: str | int | PartialUser
            The ID, or PartialUser, of the user sending the message. This ID must match the user ID in the user access token.
        token_for: str | PartialUser | None
            User access token that includes the ``user:write:chat`` scope.
            You can use an App Access Token which additionally requires ``user:bot scope`` from chatting user, and either ``channel:bot scope`` from broadcaster or moderator status.
        reply_to_message_id: str | None
            The ID of the chat message being replied to.
        source_only: bool | None
            Determines if the chat message is sent only to the source channel (defined by the PartialUser this is called on) during a shared chat session.
            This has no effect if the message is sent during a shared chat session.
            This parameter can only be set when utilizing an `App Access Token`. It cannot be specified when a User Access Token is used, and will instead result in an HTTP 400 error.
            If this parameter is not set, when using an App Access Token, then it will use the default that Twitch has set, which will be `True` after 2025-05-19.
        Returns
        -------
        SentMessage
            An object containing the response from Twitch regarding the sent message.

        Raises
        ------
        ValueError
            The message is limited to a maximum of 500 characters.
        """
        _message = " ".join(message.split())
        if len(_message) > 500:
            raise ValueError("The message is limited to a maximum of 500 characters.")

        from twitchio.models import SentMessage

        data = await self._http.post_chat_message(
            broadcaster_id=self.id,
            sender_id=sender,
            message=message,
            reply_to_message_id=reply_to_message_id,
            token_for=token_for,
            source_only=source_only,
        )

        sent: SentMessage = SentMessage(data["data"][0])
        if sent.dropped_code:
            msg = f"Twitch rejected your message to '{self}': '{sent.dropped_message}' ({sent.dropped_code})"
            raise MessageRejectedError(msg, message=sent, channel=self, content=_message)

        return SentMessage(data["data"][0])

    async def update_chatter_color(self, color: str) -> None:
        """|coro|

        Updates the color used for the user's name in chat.

        **Available Colors**
            - blue
            - blue_violet
            - cadet_blue
            - chocolate
            - coral
            - dodger_blue
            - firebrick
            - golden_rod
            - green
            - hot_pink
            - orange_red
            - red
            - sea_green
            - spring_green
            - yellow_green

        .. note::
            Requires a user access token that includes the ``user:manage:chat_color`` scope.

        Parameters
        ----------
        color: str
            The color to use, to see the list of colors available please refer to the docs.
            If the user is a Turbo or Prime member then you may specify a Hex color code e.g. ``#9146FF``
        """
        return await self._http.put_user_chat_color(user_id=self.id, color=color, token_for=self.id)

    async def create_clip(
        self, *, token_for: str | PartialUser, has_delay: bool = False
    ) -> CreatedClip:  # TODO Test this with non broadcaster token
        """|coro|

        Creates a clip from the broadcaster's stream.

        This API captures up to 90 seconds of the broadcaster's stream. The 90 seconds spans the point in the stream from when you called the API.
        For example, if you call the API at the 4:00 minute mark, the API captures from approximately the 3:35 mark to approximately the 4:05 minute mark.
        Twitch tries its best to capture 90 seconds of the stream, but the actual length may be less.
        This may occur if you begin capturing the clip near the beginning or end of the stream.

        By default, Twitch publishes up to the last 30 seconds of the 90 seconds window and provides a default title for the clip.
        To specify the title and the portion of the 90 seconds window that's used for the clip, use the URL in the CreatedClip's ``edit_url`` attribute.
        You can specify a clip that's from 5 seconds to 60 seconds in length. The URL is valid for up to 24 hours or until the clip is published, whichever comes first.

        Creating a clip is an asynchronous process that can take a short amount of time to complete.
        To determine whether the clip was successfully created, call [`fetch_clips`][twitchio.user.PartialUser.fetch_clips] using the clip ID that this request returned.
        If [`fetch_clips`][twitchio.user.PartialUser.fetch_clips] returns the clip, the clip was successfully created. If after 15 seconds [`fetch_clips`][twitchio.user.PartialUser.fetch_clips] hasn't returned the clip, assume it failed.

        .. note::
            Requires a user access token that includes the ``clips:edit`` scope.

        Parameters
        ----------
        has_delay: bool
            A Boolean value that determines whether the API captures the clip at the moment the viewer requests it or after a delay.
            If False (default), Twitch captures the clip at the moment the viewer requests it (this is the same clip experience as the Twitch UX).
            If True, Twitch adds a delay before capturing the clip (this basically shifts the capture window to the right slightly).
        token_for: str | PartialUser
            User access token that includes the ``clips:edit`` scope.

        Returns
        -------
        CreatedClip
            The CreatedClip object.
        """
        from .models.clips import CreatedClip

        data = await self._http.post_create_clip(broadcaster_id=self.id, token_for=token_for, has_delay=has_delay)
        return CreatedClip(data["data"][0])

    def fetch_clips(
        self,
        *,
        started_at: datetime.datetime | None = None,
        ended_at: datetime.datetime | None = None,
        featured: bool | None = None,
        token_for: str | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Clip]:
        """|aiter|

        Fetches clips from the broadcaster's streams.

        Parameters
        -----------
        started_at: datetime.datetime
            The start date used to filter clips.
            This can be timezone aware.
        ended_at: datetime.datetime
            The end date used to filter clips. If not specified, the time window is the start date plus one week.
            This can be timezone aware.
        featured: bool | None = None
            If True, returns only clips that are featured.
            If False, returns only clips that aren't featured.
            All clips are returned if this parameter is not provided.
        token_for: str | PartialUser | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        --------
        HTTPAsyncIterator[Clip]
        """

        first = max(1, min(100, first))

        return self._http.get_clips(
            broadcaster_id=self.id,
            first=first,
            started_at=started_at,
            ended_at=ended_at,
            is_featured=featured,
            token_for=token_for,
            max_results=max_results,
        )

    async def fetch_goals(self) -> list[Goal]:
        """|coro|

        Fetches a list of the creator's goals.

        .. note::
            Requires a user access token that includes the ``channel:read:goals`` scope.

        Returns
        -------
        list[Goal]
            List of Goal objects.
        """
        from .models.goals import Goal

        data = await self._http.get_creator_goals(broadcaster_id=self.id, token_for=self.id)
        return [Goal(d, http=self._http) for d in data["data"]]

    def fetch_hype_train_events(
        self,
        *,
        first: int = 1,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[HypeTrainEvent]:
        """|aiter|

        Fetches information about the broadcaster's current or most recent Hype Train event.

        Parameters
        ----------
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 1.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[HypeTrainEvent]
            HTTPAsyncIterator of HypeTrainEvent objects.
        """
        first = max(1, min(100, first))

        return self._http.get_hype_train_events(
            broadcaster_id=self.id,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    async def start_raid(self, to_broadcaster: str | int | PartialUser) -> Raid:
        """|coro|

        Starts a raid to another channel.

        .. note::
            The limit is 10 requests within a 10-minute window.

            When you call the API from a chat bot or extension, the Twitch UX pops up a window at the top of the chat room that identifies the number of viewers in the raid.
            The raid occurs when the broadcaster clicks Raid Now or after the 90-second countdown expires.

            To determine whether the raid successfully occurred, you must subscribe to the Channel Raid event.

            To cancel a pending raid, use the Cancel a raid endpoint.

        .. note::
            Requires a user access token that includes the ``channel:manage:raids`` scope.

        Parameters
        ----------
        to_broadcaster: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster to raid.

        Returns
        -------
        Raid
            Raid object.
        """
        data = await self._http.post_raid(from_broadcaster_id=self.id, to_broadcaster_id=to_broadcaster, token_for=self.id)

        return Raid(data["data"][0])

    async def cancel_raid(self) -> None:
        """|coro|

        Cancel a pending raid.

        You can cancel a raid at any point up until the broadcaster clicks `Raid Now` in the Twitch UX or the 90-second countdown expires.

        .. note::
            The limit is 10 requests within a 10-minute window.

        .. note::
            Requires a user access token that includes the ``channel:manage:raids`` scope.

        Returns
        -------
        Raid
            Raid object.
        """

        return await self._http.delete_raid(broadcaster_id=self.id, token_for=self.id)

    def fetch_stream_schedule(
        self,
        *,
        ids: list[str] | None = None,
        token_for: str | PartialUser | None = None,
        start_time: datetime.datetime | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Schedule]:
        """|aiter|

        Fetches stream schedule information for a broadcaster.

        Parameters
        ----------
        ids: list[str] | None
            List of scheduled segments ids to return.
        start_time: datetime.datetime | None
            The datetime of when to start returning segments from the schedule. This can be timezone aware.
        token_for: str | PartialUser | None
            An optional token to use instead of the default app token.
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 25 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[Schedule]
            HTTPAsyncIterator of Schedule objects.

        Raises
        ------
        ValueError
            You may specify a maximum of 100 ids.
        """
        first = max(1, min(25, first))

        if ids is not None and len(ids) > 100:
            raise ValueError("You may specify a maximum of 100 ids.")

        return self._http.get_channel_stream_schedule(
            broadcaster_id=self.id,
            ids=ids,
            token_for=token_for,
            start_time=start_time,
            first=first,
            max_results=max_results,
        )

    async def update_stream_schedule(
        self,
        *,
        vacation: bool,
        vacation_start_time: datetime.datetime | None = None,
        vacation_end_time: datetime.datetime | None = None,
        timezone: str | None = None,
    ) -> None:
        """|coro|

        Updates the broadcaster's schedule settings, such as scheduling a vacation.

        .. note::
            Requires a user access token that includes the ``channel:manage:schedule`` scope.

        Parameters
        ----------
        vacation: bool
            A Boolean value that indicates whether the broadcaster has scheduled a vacation. Set to True to enable Vacation Mode and add vacation dates, or False to cancel a previously scheduled vacation.
        vacation_start_time: datetime.datetime | None
            Datetime of when the broadcaster's vacation starts. Required if `vacation` is True. This can be timezone aware.
        vacation_end_time: datetime.datetime | None
            Datetime of when the broadcaster's vacation ends. Required if `vacation` is True. This can be timezone aware.
        timezone: str | None
            The time zone that the broadcaster broadcasts from. Specify the time zone using `IANA time zone database <https://www.iana.org/time-zones>`_ format (for example, `America/New_York`). Required if vaction is True.

        Raises
        ------
        ValueError
            When vacation is True, all of vacation_start_time, vacation_end_time, and timezone must be provided.
        """

        if vacation and any(v is None for v in (vacation_start_time, vacation_end_time, timezone)):
            raise ValueError(
                "When vacation is True, all of vacation_start_time, vacation_end_time, and timezone must be provided."
            )

        return await self._http.patch_channel_stream_schedule(
            broadcaster_id=self.id,
            vacation=vacation,
            token_for=self.id,
            vacation_start_time=vacation_start_time,
            vacation_end_time=vacation_end_time,
            timezone=timezone,
        )

    async def create_schedule_segment(
        self,
        *,
        start_time: datetime.datetime,
        timezone: str,
        duration: int,
        recurring: bool = True,
        category_id: str | None = None,
        title: str | None = None,
    ) -> Schedule:
        """|coro|

        Adds a single or recurring broadcast to the broadcaster's streaming schedule.

        For information about scheduling broadcasts, see `Stream Schedule <https://help.twitch.tv/s/article/channel-page-setup#Schedule>`_.

        .. note::
            Requires a user access token that includes the ``channel:manage:schedule`` scope.

        Parameters
        ----------
        start_time: datetime.datetime
            Datetime that the broadcast segment starts. This can be timezone aware.
        timezone: str | None
            The time zone that the broadcaster broadcasts from. Specify the time zone using `IANA time zone database <https://www.iana.org/time-zones>`_ format (for example, `America/New_York`).
        duration: int
            The length of time, in minutes, that the broadcast is scheduled to run. The duration must be in the range 30 through 1380 (23 hours)
        recurring: bool
            A Boolean value that determines whether the broadcast recurs weekly. Is True if the broadcast recurs weekly. Only partners and affiliates may add non-recurring broadcasts.
            Default is True.
        category_id: str | None
            The ID of the category that best represents the broadcast's content. To get the category ID, use the [Search Categories][twitchio.client.search_categories].
        title: str | None
            The broadcast's title. The title may contain a maximum of 140 characters.

        Raises
        ------
        ValueError
            Duration must be between 30 and 1380.
        ValueError
            Title must not be greater than 140 characters.
        """

        if duration < 30 or duration > 1380:
            raise ValueError("Duration must be between 30 and 1380.")
        if title is not None and len(title) > 140:
            raise ValueError("Title must not be greater than 140 characters.")

        from .models.schedule import Schedule

        data = await self._http.post_channel_stream_schedule_segment(
            broadcaster_id=self.id,
            start_time=start_time,
            token_for=self.id,
            duration=duration,
            recurring=recurring,
            timezone=timezone,
            category_id=category_id,
            title=title,
        )
        return Schedule(data["data"], http=self._http)

    async def update_schedule_segment(
        self,
        *,
        id: str,
        start_time: datetime.datetime | None = None,
        duration: int | None = None,
        category_id: str | None = None,
        title: str | None = None,
        canceled: bool | None = None,
        timezone: str | None = None,
    ) -> Schedule:
        """|coro|

        Updates a scheduled broadcast segment.

        Parameters
        ----------
        id: str
            The ID of the broadcast segment to update.
        start_time: datetime.datetime | None
            The datetime that the broadcast segment starts. This can be timezone aware.
        duration: int | None
            he length of time, in minutes, that the broadcast is scheduled to run. The duration must be in the range 30 through 1380 (23 hours)
        category_id: str | None
            The ID of the category that best represents the broadcast's content. To get the category ID, use :meth:`~Client.search_categories`.
        title: str | None
            The broadcast's title. The title may contain a maximum of 140 characters.
        canceled: bool | None
            A Boolean value that indicates whether the broadcast is canceled. Set to True to cancel the segment.
        timezone: str | None
            The time zone where the broadcast takes place. Specify the time zone using `IANA time zone database <https://www.iana.org/time-zones>`_  format (for example, America/New_York).

        Returns
        -------
        Schedule
            Schedule object.

        Raises
        ------
        ValueError
            Duration must be between 30 and 1380.
        ValueError
            Title must not be greater than 140 characters.
        """
        if duration is not None and (duration < 30 or duration > 1380):
            raise ValueError("Duration must be between 30 and 1380.")
        if title is not None and len(title) > 140:
            raise ValueError("Title must not be greater than 140 characters.")

        from .models.schedule import Schedule

        data = await self._http.patch_channel_stream_schedule_segment(
            broadcaster_id=self.id,
            id=id,
            start_time=start_time,
            duration=duration,
            category_id=category_id,
            title=title,
            canceled=canceled,
            timezone=timezone,
            token_for=self.id,
        )

        return Schedule(data["data"], http=self._http)

    async def delete_schedule_segment(self, id: str) -> None:
        """|coro|

        Removes a broadcast segment from the broadcaster's streaming schedule.

        .. note::
            For recurring segments, removing a segment removes all segments in the recurring schedule.

        .. note::
            Requires a user access token that includes the ``channel:manage:schedule`` scope.

        Parameters
        ----------
        id: str
            The ID of the segment to remove.
        """
        return await self._http.delete_channel_stream_schedule_segment(broadcaster_id=self.id, id=id, token_for=self.id)

    async def fetch_channel_teams(self, *, token_for: str | PartialUser | None = None) -> list[ChannelTeam]:
        """|coro|

        Fetches the list of Twitch teams that the broadcaster is a member of.

        Parameters
        ----------
        token_for: str | PartialUser | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        list[ChannelTeam]
            List of ChannelTeam objects.
        """
        from .models.teams import ChannelTeam

        data = await self._http.get_channel_teams(broadcaster_id=self.id, token_for=token_for)

        return [ChannelTeam(d, http=self._http) for d in data["data"]]

    async def check_automod_status(self, *messages: list[AutomodCheckMessage]) -> list[AutoModStatus]:
        r"""|coro|

        Checks whether AutoMod would flag the specified message for review.

        Rates are limited per channel based on the account type rather than per access token.

        +---------------+-----------------+---------------+
        | Account type  | Limit per minute| Limit per hour|
        +===============+=================+===============+
        | Normal        | 5               | 50            |
        +---------------+-----------------+---------------+
        | Affiliate     | 10              | 100           |
        +---------------+-----------------+---------------+
        | Partner       | 30              | 300           |
        +---------------+-----------------+---------------+

        .. note::
            AutoMod is a moderation tool that holds inappropriate or harassing chat messages for moderators to review.
            Moderators approve or deny the messages that AutoMod flags; only approved messages are released to chat.
            AutoMod detects misspellings and evasive language automatically.

            For information about AutoMod, see `How to Use AutoMod <https://help.twitch.tv/s/article/how-to-use-automod?language=en_US>`_.

        .. note::
            Requires a user access token that includes the ``moderation:read`` scope.

        Parameters
        ----------
        \*messages: :class:`twitchio.AutomodCheckMessage`
            An argument list of AutomodCheckMessage objects.

        Returns
        -------
        list[AutoModStatus]
            List of AutoModStatus objects.
        """
        from .models.moderation import AutoModStatus

        data = await self._http.post_check_automod_status(broadcaster_id=self.id, messages=messages, token_for=self.id)
        return [AutoModStatus(d) for d in data["data"]]

    async def approve_automod_messages(self, msg_id: str) -> None:
        """|coro|

        Allow the message that AutoMod flagged for review.

        The PartialUser / User object to perform this task is the moderator.

        .. note::
            Requires a user access token that includes the ``moderator:manage:automod`` scope.

        Parameters
        ----------
        msg_id: str
            The ID of the message to allow.
        """
        return await self._http.post_manage_automod_messages(
            user_id=self.id, msg_id=msg_id, action="ALLOW", token_for=self.id
        )

    async def deny_automod_messages(self, msg_id: str) -> None:
        """|coro|

        Deny the message that AutoMod flagged for review.

        The PartialUser / User object to perform this task is the moderator.

        .. note::
            Requires a user access token that includes the ``moderator:manage:automod`` scope.

        Parameters
        ----------
        msg_id: str
            The ID of the message to deny.
        """
        return await self._http.post_manage_automod_messages(
            user_id=self.id, msg_id=msg_id, action="DENY", token_for=self.id
        )

    async def fetch_automod_settings(
        self,
        *,
        moderator: str | int | PartialUser,
    ) -> AutomodSettings:
        """|coro|

        Fetches the broadcaster's AutoMod settings.

        The settings are used to automatically block inappropriate or harassing messages from appearing in the broadcaster's chat room.

        .. note::
            Requires a user access token that includes the ``moderator:read:automod_settings`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's chat room.
            This ID must match the user ID in the user access token.

        Returns
        -------
        AutomodSettings
            AutomodSettings object.
        """
        from .models import AutomodSettings

        data = await self._http.get_automod_settings(broadcaster_id=self.id, moderator_id=moderator, token_for=moderator)
        return AutomodSettings(data["data"][0], http=self._http)

    async def update_automod_settings(
        self,
        *,
        moderator: str | int | PartialUser,
        settings: AutomodSettings,
    ) -> AutomodSettings:
        """|coro|

        Updates the broadcaster's AutoMod settings.

        The settings are used to automatically block inappropriate or harassing messages from appearing in the broadcaster's chat room.

        Perform a fetch with :meth:`~fetch_automod_settings` to obtain the :class:`~twitchio.models.moderation.AutomodSettings` object to modify and pass to this method.

        You may set either overall_level or the individual settings like aggression, but not both.

        Setting overall_level applies default values to the individual settings. However, setting overall_level to 4 does not necessarily mean that it applies 4 to all the individual settings.
        Instead, it applies a set of recommended defaults to the rest of the settings. For example, if you set overall_level to 2, Twitch provides some filtering on discrimination and sexual content, but more filtering on hostility (see the first example response).

        If overall_level is currently set and you update swearing to 3, overall_level will be set to null and all settings other than swearing will be set to 0.
        The same is true if individual settings are set and you update overall_level to 3 — all the individual settings are updated to reflect the default level.

        Note that if you set all the individual settings to values that match what overall_level would have set them to, Twitch changes AutoMod to use the default AutoMod level instead of using the individual settings.

        Valid values for all levels are from 0 (no filtering) through 4 (most aggressive filtering).
        These levels affect how aggressively AutoMod holds back messages for moderators to review before they appear in chat or are denied (not shown).

        .. note::
            Requires a user access token that includes the ``moderator:manage:automod_settings`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's chat room.
            This ID must match the user ID in the user access token.
        settings: AutomodSettings
            AutomodSettings object containing the new settings for the broadcaster's channel.
            You can fetch this using :meth:`~fetch_automod_settings`

        Returns
        -------
        AutomodSettings
            AutomodSettings object.
        """
        from .models import AutomodSettings

        data = await self._http.put_automod_settings(
            broadcaster_id=self.id, moderator_id=moderator, settings=settings, token_for=moderator
        )
        return AutomodSettings(data["data"][0], http=self._http)

    def fetch_banned_user(
        self,
        *,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[BannedUser]:
        """|aiter|

        Fetch all users that the broadcaster has banned or put in a timeout.

        .. note::
            Requires a user access token that includes the ``moderation:read`` or ``moderator:manage:banned_users`` scope.

        Parameters
        ----------
        user_ids: list[str | int] | None
            A list of user IDs used to filter the results. To specify more than one ID, include this parameter for each user you want to get.
            You may specify a maximum of 100 IDs.

            The returned list includes only those users that were banned or put in a timeout.
            The list is returned in the same order that you specified the IDs.
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[BannedUser]
            HTTPAsyncIterator of BannedUser objects.

        Raises
        ------
        ValueError
            You may only specify a maximum of 100 users.
        """
        first = max(1, min(100, first))
        if user_ids is not None and len(user_ids) > 100:
            raise ValueError("You may only specify a maximum of 100 users.")

        return self._http.get_banned_users(
            broadcaster_id=self.id,
            user_ids=user_ids,
            token_for=self.id,
            max_results=max_results,
        )

    async def ban_user(
        self,
        *,
        moderator: str | PartialUser | None = None,
        user: str | PartialUser,
        reason: str | None = None,
    ) -> Ban:
        """|coro|

        Ban the provided user from the channel tied with this :class:`~twitchio.PartialUser`.

        .. note::

            Requires a user access token that includes the ``moderator:manage:banned_users`` scope.

        Parameters
        ----------
        moderator: str | PartialUser | None
            An optional ID of or the :class:`~twitchio.PartialUser` object of the moderator issuing this action.
            You must have a token stored with the ``moderator:manage:banned_users`` scope for this moderator.

            If `None`, the ID of this :class:`~twitchio.PartialUser` will be used.
        user: str | PartialUser
            The ID of, or the :class:`~twitchio.PartialUser` of the user to ban.
        reason: str | None
            An optional reason this chatter is being banned. If provided the length of the reason must not be more than
            ``500`` characters long. Defaults to `None`.

        Raises
        ------
        ValueError
            The length of the reason parameter exceeds 500 characters.
        HTTPException
            The request to ban the chatter failed.

        Returns
        -------
        Ban
            The :class:`~twitchio.Ban` object for this ban.
        """
        from .models import Ban  # fixes: circular import

        if reason and len(reason) > 500:
            raise ValueError("The provided reason exceeds the allowed length of 500 characters.")

        data = await self._http.post_ban_user(
            broadcaster_id=self.id,
            moderator_id=moderator or self.id,
            user_id=user,
            token_for=moderator,
            reason=reason,
        )

        return Ban(data["data"][0], http=self._http)

    async def timeout_user(
        self,
        *,
        moderator: str | int | PartialUser | None,  # TODO Default to bot_id, same for token_for.
        user: str | PartialUser | None,
        duration: int,
        reason: str | None = None,
    ) -> Timeout:
        """|coro|

        Timeout the provided user from the channel tied with this :class:`~twitchio.PartialUser`.

        .. note::

            Requires a user access token that includes the ``moderator:manage:banned_users`` scope.

        Parameters
        ----------
        moderator: str | PartialUser | None
            An optional ID of or the :class:`~twitchio.PartialUser` object of the moderator issuing this action.
            You must have a token stored with the ``moderator:manage:banned_users`` scope for this moderator.

            If `None`, the ID of this :class:`~twitchio.PartialUser` will be used.
        user: str | PartialUser
            The ID of, or the :class:`~twitchio.PartialUser` of the user to ban.
        reason: str | None
            An optional reason this chatter is being banned. If provided the length of the reason must not be more than
            ``500`` characters long. Defaults to `None`.
        duration: int
            The duration of the timeout in seconds. The minimum duration is ``1`` second and the
            maximum is ``1_209_600`` seconds (2 weeks).

            To end the chatters timeout early, set this field to ``1``,
            or use the :meth:`~twitchio.user.PartialUser.unban_user` endpoint.

            The default is ``600`` which is ten minutes.

        Returns
        -------
        Timeout
            The :class:`~twitchio.Timeout` object.
        """
        from .models import Timeout

        data = await self._http.post_ban_user(
            broadcaster_id=self.id,
            moderator_id=moderator or self.id,
            user_id=user,
            token_for=moderator,
            duration=duration,
            reason=reason,
        )
        return Timeout(data["data"][0], http=self._http)

    async def unban_user(
        self,
        *,
        moderator: str | int | PartialUser,
        user_id: str | int | PartialUser,
    ) -> None:
        """|coro|

        Unban a user from the broadcaster's channel.

        .. note::

            Requires a user access token that includes the ``moderator:manage:banned_users`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID of the broadcaster or a user that has permission to moderate the broadcaster's chat room.
            This ID must match the user ID in the user access token.
        user_id: str | int | PartialUser
            The ID, or PartialUser, of the user to ban or put in a timeout.
        """

        return await self._http.delete_unban_user(
            broadcaster_id=self.id,
            moderator_id=moderator,
            user_id=user_id,
            token_for=moderator,
        )

    def fetch_unban_requests(
        self,
        *,
        moderator: str | int | PartialUser,
        status: Literal["pending", "approved", "denied", "acknowledged", "canceled"],
        user: str | int | PartialUser | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[UnbanRequest]:
        """|aiter|

        Fetches the unban requests of a broadcaster's channel.

        .. note::
            Requires a user access token that includes the ``moderator:read:unban_requests`` or ``moderator:manage:unban_requests`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's unban requests. This ID must match the user ID in the user access token.
        status: Literal["pending", "approved", "denied", "acknowledged", "canceled"]
            Filter by a status. Possible values are:

            - pending
            - approved
            - denied
            - acknowledged
            - canceled

        user: str | int | PartialUser | None
            An ID, or PartialUser, used to filter what unban requests are returned.
        first: int
            The maximum number of items to return per page in response. Default 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[UnbanRequest]
            HTTPAsyncIterator of UnbanRequest objects.
        """
        first = max(1, min(100, first))

        return self._http.get_unban_requests(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            status=status,
            user_id=user,
            first=first,
            max_results=max_results,
        )

    async def resolve_unban_request(
        self,
        *,
        moderator: str | int | PartialUser,  # TODO Default to bot_id, same for token_for.
        status: Literal["approved", "denied"],
        unban_request_id: str,
        resolution_text: str | None = None,
    ) -> UnbanRequest:
        """|coro|

        Resolves an unban request by approving or denying it.

        .. note::
            Requires a user access token that includes the ``moderator:manage:unban_requests`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's unban requests. This ID must match the user ID in the user access token.
        status: Literal["approved", "denied"]
            Resolution status. This is either ``approved`` or ``denied``.
        unban_request_id: str
            The ID of the unban request.
        resolution_text: str | None
            Message supplied by the unban request resolver. The message is limited to a maximum of 500 characters.

        Returns
        -------
        UnbanRequest
            UnbanRequest object.

        Raises
        ------
        ValueError
            Resolution text must be less than 500 characters.
        """

        if resolution_text is not None and len(resolution_text) > 500:
            raise ValueError("Resolution text must be less than 500 characters.")

        from .models.moderation import UnbanRequest

        data = await self._http.patch_unban_requests(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            unban_request_id=unban_request_id,
            status=status,
            resolution_text=resolution_text,
        )
        return UnbanRequest(data["data"][0], http=self._http)

    def fetch_blocked_terms(
        self,
        moderator: str | int | PartialUser,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[BlockedTerm]:
        """|aiter|

        Fetches the broadcaster's list of non-private, blocked words or phrases.
        These are the terms that the broadcaster or moderator added manually or that were denied by AutoMod.

        .. note::
            Requires a user access token that includes the ``moderator:read:blocked_terms` or ``moderator:manage:blocked_terms`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's chat room.
            This ID must match the user ID in the user access token.
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[BlockedTerm]
            HTTPAsyncIterator of BlockedTerm objects.
        """
        first = max(1, min(100, first))

        return self._http.get_blocked_terms(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            first=first,
            max_results=max_results,
        )

    async def add_blocked_term(
        self,
        *,
        moderator: str | int | PartialUser,
        text: str,
    ) -> BlockedTerm:
        """|coro|

        Adds a word or phrase to the broadcaster's list of blocked terms.

        These are the terms that the broadcaster doesn't want used in their chat room.

        .. note::
            Terms may include a wildcard character ``(*)``. The wildcard character must appear at the beginning or end of a word or set of characters. For example, ``*foo`` or ``foo*``.

            If the blocked term already exists, the response contains the existing blocked term.

        .. note::
           Requires a user access token that includes the ``moderator:manage:blocked_terms`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's unban requests. This ID must match the user ID in the user access token.
        text: str
            The word or phrase to block from being used in the broadcaster's chat room. The term must contain a minimum of 2 characters and may contain up to a maximum of 500 characters.

            Terms may include a wildcard character ``(*)``. The wildcard character must appear at the beginning or end of a word or set of characters. For example, ``*foo`` or ``foo*``.

            If the blocked term already exists, the response contains the existing blocked term.

        Returns
        -------
        BlockedTerm
            BlockedTerm object.

        Raises
        ------
        ValueError
            Text must be more than 2 characters but less than 500 characters.
        """

        if len(text) > 500 or len(text) < 2:
            raise ValueError("Text must be more than 2 characters but less than 500 characters.")

        from .models.moderation import BlockedTerm

        data = await self._http.post_blocked_term(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            text=text,
        )
        return BlockedTerm(data["data"][0], http=self._http)

    async def remove_blocked_term(
        self,
        *,
        moderator: str | int | PartialUser,
        id: str,
    ) -> None:
        """|coro|

        Removes the word or phrase from the broadcaster's list of blocked terms.

        .. note::
           Requires a user access token that includes the ``oderator:manage:blocked_terms`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's unban requests.
            This ID must match the user ID in the user access token.
        id: str
            The ID of the blocked term to remove from the broadcaste's list of blocked terms.
        """

        return await self._http.delete_blocked_term(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            id=id,
        )

    async def delete_chat_messages(
        self,
        *,
        moderator: str | int | PartialUser,
        message_id: str | None = None,
    ) -> None:
        """|coro|

        Removes a single chat message or all chat messages from the broadcaster's chat room.

        .. important::
            Restrictions:

            - The message must have been created within the last 6 hours.
            - The message must not belong to the broadcaster.
            - The message must not belong to another moderator.

            If not specified, the request removes all messages in the broadcaster's chat room.

        .. note::
           Requires a user access token that includes the ``moderator:manage:chat_messages`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that has permission to moderate the broadcaster's chat room.
            This ID must match the user ID in the user access token.
        token_for: str | PartialUser
            User access token that includes the ``moderator:manage:chat_messages`` scope.
        message_id: str
            The ID of the message to remove.
        """

        return await self._http.delete_chat_message(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            message_id=message_id,
        )

    def fetch_moderated_channels(self, *, first: int = 20, max_results: int | None = None) -> HTTPAsyncIterator[PartialUser]:
        """|aiter|

        Fetches channels that the specified user has moderator privileges in.

        .. note::
           Requires a user access token that includes the ``user:read:moderated_channels`` scope.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[PartialUser]
            HTTPAsyncIterator of PartialUser objects.
        """
        first = max(1, min(100, first))
        return self._http.get_moderated_channels(
            user_id=self.id,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    def fetch_moderators(
        self,
        *,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[PartialUser]:
        """|aiter|

        Fetches users allowed to moderate the broadcaster's chat room.

        .. note::
           Requires a user access token that includes the ``moderation:read`` scope.
           If your app also adds and removes moderators, you can use the ``channel:manage:moderators`` scope instead.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        user_ids: list[str | int] | None
            A list of user IDs used to filter the results. To specify more than one ID, include this parameter for each moderator you want to get.
            The returned list includes only the users from the list who are moderators in the broadcaster's channel. You may specify a maximum of 100 IDs.
        token_for: str | PartialUser
            User access token that includes the ``moderation:read`` scope.
            If your app also adds and removes moderators, you can use the ``channel:manage:moderators`` scope instead.
            The user ID in the access token must match the broadcaster's ID.
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[PartialUser]
            HTTPAsyncIterator of PartialUser objects.

        Raises
        ------
        ValueError
            You may only specify a maximum of 100 user IDs.

        """
        first = max(1, min(100, first))

        if user_ids is not None and len(user_ids) > 100:
            raise ValueError("You may only specify a maximum of 100 user IDs.")

        return self._http.get_moderators(
            broadcaster_id=self.id,
            user_ids=user_ids,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    async def add_moderator(self, user: str | int | PartialUser) -> None:
        """|coro|

        Adds a moderator to the broadcaster's chat room.

        The broadcaster may add a maximum of 10 moderators within a 10-second window.

        .. note::
           Requires a user access token that includes the ``channel:manage:moderators`` scope.

        Parameters
        ----------
        user: str | int | PartialUser
            The ID of the user to add as a moderator in the broadcaster's chat room.
        """

        return await self._http.post_channel_moderator(broadcaster_id=self.id, user_id=user, token_for=self.id)

    async def remove_moderator(self, user: str | int | PartialUser) -> None:
        """|coro|

        Removes a moderator to the broadcaster's chat room.

        The broadcaster may remove a maximum of 10 moderators within a 10-second window.

        .. note::
           Requires a user access token that includes the ``channel:manage:moderators`` scope.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        user: str | int | PartialUser
            The ID of the user to remove as a moderator in the broadcaster's chat room.
        """

        return await self._http.delete_channel_moderator(broadcaster_id=self.id, user_id=user, token_for=self.id)

    def fetch_vips(
        self,
        *,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[PartialUser]:
        """|aiter|

        Fetches the broadcaster's VIPs.

        .. note::
           Requires a user access token that includes the ``channel:read:vips`` scope.
           If your app also adds and removes moderators, you can use the ``channel:manage:vips`` scope instead.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        user_ids: list[str | int] | None
            Filters the list for specific VIPs. You may specify a maximum of 100 IDs.
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[PartialUser]
            HTTPAsyncIterator of PartialUser objects.

        Raises
        ------
        ValueError
            You may only specify a maximum of 100 user IDs.

        """
        first = max(1, min(100, first))

        if user_ids is not None and len(user_ids) > 100:
            raise ValueError("You may only specify a maximum of 100 user IDs.")

        return self._http.get_vips(
            broadcaster_id=self.id,
            user_ids=user_ids,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    async def add_vip(self, user: str | int | PartialUser) -> None:
        """|coro|

        Adds a VIP to the broadcaster's chat room.

        The broadcaster may add a maximum of 10 VIPs within a 10-second window.

        .. note::
           Requires a user access token that includes the ``channel:manage:vips`` scope.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        user: str | int
            The ID, or PartialUser, of the user to add as a VIP in the broadcaster's chat room.
        """

        return await self._http.add_vip(broadcaster_id=self.id, user_id=user, token_for=self.id)

    async def remove_vip(self, user: str | int | PartialUser) -> None:
        """|coro|

        Removes a VIP to the broadcaster's chat room.

        The broadcaster may remove a maximum of 10 VIPs within a 10-second window.

        .. note::
           Requires a user access token that includes the ``channel:manage:vips`` scope.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        user: str | int | PartialUser
            The ID, or PartialUser, of the user to remove as a VIP in the broadcaster's chat room.
        """

        return await self._http.delete_vip(broadcaster_id=self.id, user_id=user, token_for=self.id)

    async def update_shield_mode_status(
        self,
        *,
        moderator: str | int | PartialUser,
        active: bool,
    ) -> ShieldModeStatus:
        """|coro|

        Activates or deactivates  the broadcaster's Shield Mode.

        .. note::
           Requires a user access token that includes the ``moderator:manage:shield_mode`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that is one of the broadcaster's moderators.
            This ID must match the user ID in the access token.
        active: bool
            A Boolean value that determines whether to activate Shield Mode.
            Set to True to activate Shield Mode; otherwise, False to deactivate Shield Mode.
        """

        from .models.moderation import ShieldModeStatus

        data = await self._http.put_shield_mode_status(
            broadcaster_id=self.id,
            moderator_id=moderator,
            token_for=moderator,
            active=active,
        )
        return ShieldModeStatus(data["data"][0], http=self._http)

    async def fetch_shield_mode_status(
        self,
        *,
        moderator: str | int | PartialUser,
    ) -> ShieldModeStatus:
        """|coro|

        Fetches the broadcaster's Shield Mode activation status.

        .. note::
           Requires a user access token that includes the ``moderator:read:shield_mode`` or ``moderator:manage:shield_mode`` scope.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the broadcaster or a user that is one of the broadcaster's moderators.
            This ID must match the user ID in the access token.
        """

        from .models.moderation import ShieldModeStatus

        data = await self._http.get_shield_mode_status(broadcaster_id=self.id, moderator_id=moderator, token_for=moderator)
        return ShieldModeStatus(data["data"][0], http=self._http)

    def fetch_polls(
        self,
        *,
        ids: list[str] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Poll]:
        """|aiter|

        Fetches polls that the broadcaster created.

        Polls are available for 90 days after they're created.

        .. note::
           Requires a user access token that includes the ``channel:read:polls`` or ``channel:manage:polls`` scope.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        ids: list[str] | None
            A list of IDs that identify the polls to return. You may specify a maximum of 20 IDs.
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 20 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[Poll]
            HTTPAsyncIterator of Poll objects.

        Raises
        ------
        ValueError
            You may only specify a maximum of 20 IDs.

        """
        first = max(1, min(20, first))

        if ids is not None and len(ids) > 20:
            raise ValueError("You may only specify a maximum of 20 IDs.")

        return self._http.get_polls(
            broadcaster_id=self.id,
            ids=ids,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    async def create_poll(
        self,
        *,
        title: str,
        choices: list[str],
        duration: int,
        channel_points_voting_enabled: bool = False,
        channel_points_per_vote: int | None = None,
    ) -> Poll:
        """|coro|

        Creates a poll that viewers in the broadcaster's channel can vote on.

        The poll begins as soon as it's created. You may run only one poll at a time.

        .. note::
            Requires a user access token that includes the ``channel:manage:polls`` scope.

        Parameters
        ----------
        title: str
            The question that viewers will vote on.
            The question may contain a maximum of 60 characters.
        choices: list[str]
            A list of choice titles that viewers may choose from.
            The list must contain a minimum of 2 choices and up to a maximum of 5 choices.
            The title itself can only have a maximum of 25 characters.
        duration: int
            The length of time (in seconds) that the poll will run for.
            The minimum is 15 seconds and the maximum is 1800 seconds (30 minutes).
        channel_points_voting_enabled: bool
            A Boolean value that indicates whether viewers may cast additional votes using Channel Points.
            If True, the viewer may cast more than one vote but each additional vote costs the number of Channel Points specified in ``channel_points_per_vote``. The default is False
        channel_points_per_vote: int | None
            The number of points that the viewer must spend to cast one additional vote. The minimum is 1 and the maximum is 1000000.
            Only use this if ``channel_points_voting_enabled`` is True; otherwise it is ignored.

        Returns
        -------
        Poll
            A Poll object.

        Raises
        ------
        ValueError
            The question may contain a maximum of 60 characters.
        ValueError
            You must provide a minimum of 2 choices or a maximum of 5.
        ValueError
            Choice title may contain a maximum of 25 characters.
        ValueError
            Duration must be between 15 and 1800.
        ValueError
            Channel points per vote must be between 1 and 1000000.
        """
        data = await self._http.post_poll(
            broadcaster_id=self.id,
            title=title,
            choices=choices,
            duration=duration,
            token_for=self.id,
            channel_points_voting_enabled=channel_points_voting_enabled,
            channel_points_per_vote=channel_points_per_vote,
        )

        if len(title) > 60:
            raise ValueError("The question may contain a maximum of 60 characters.")
        if len(choices) < 2 or len(choices) > 5:
            raise ValueError("You must provide a minimum of 2 choices or a maximum of 5.")
        if any(len(title) > 25 for title in choices):
            raise ValueError("Choice title may contain a maximum of 25 characters.")
        if duration < 15 or duration > 1800:
            raise ValueError("Duration must be between 15 and 1800.")
        if channel_points_per_vote is not None and (channel_points_per_vote < 1 or channel_points_per_vote > 1000000):
            raise ValueError("Channel points per vote must be between 1 and 1000000.")

        from .models.polls import Poll

        return Poll(data["data"][0], http=self._http)

    async def end_poll(self, *, id: str, status: Literal["ARCHIVED", "TERMINATED"]) -> Poll:
        """|coro|

        End an active poll. You have the option to end it or end it and archive it.

        Status must be set to one of the below.

        - TERMINATED — Ends the poll before the poll is scheduled to end. The poll remains publicly visible.
        - ARCHIVED — Ends the poll before the poll is scheduled to end, and then archives it so it's no longer publicly visible.

        .. tip::
            You can also call this method directly on a Poll object with [`end_poll`][twitchio.models.polls.Poll.end_poll]

        Parameters
        ----------
        id: str
            The ID of the poll to end.
        status:  Literal["ARCHIVED", "TERMINATED"]
            The status to set the poll to. Possible case-sensitive values are: ``ARCHIVED`` and ``TERMINATED``.

        Returns
        -------
        Poll
            A Poll object.
        """
        from .models.polls import Poll

        data = await self._http.patch_poll(broadcaster_id=self.id, id=id, status=status, token_for=self.id)
        return Poll(data["data"][0], http=self._http)

    def fetch_predictions(
        self,
        *,
        ids: list[str] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Prediction]:
        """|aiter|

        Fetches predictions that the broadcaster created.

        If the number of outcomes is two, the color is BLUE for the first outcome and PINK for the second outcome.
        If there are more than two outcomes, the color is BLUE for all outcomes.

        .. note::
           Requires a user access token that includes the ``channel:read:predictions`` or ``channel:manage:predictions`` scope.
           The user ID in the access token must match the broadcaster's ID.

        Parameters
        ----------
        ids: list[str] | None
            A list of IDs that identify the predictions to return. You may specify a maximum of 20 IDs.
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 25 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[Prediction]
            HTTPAsyncIterator of Prediction objects.

        Raises
        ------
        ValueError
            You may only specify a maximum of 25 IDs.

        """
        first = max(1, min(25, first))

        if ids is not None and len(ids) > 20:
            raise ValueError("You may only specify a maximum of 25 IDs.")

        return self._http.get_predictions(
            broadcaster_id=self.id,
            ids=ids,
            first=first,
            token_for=self.id,
            max_results=max_results,
        )

    async def create_prediction(
        self,
        *,
        title: str,
        outcomes: list[str],
        prediction_window: int,
    ) -> Prediction:
        """|coro|

        Creates a prediction that viewers in the broadcaster's channel can vote on.

        The prediction begins as soon as it's created. You may run only one prediction at a time.

        .. note::
            Requires a user access token that includes the ``channel:manage:predictions`` scope.

        Parameters
        ----------
        title: str
            The question that viewers will vote on.
            The question may contain a maximum of 45 characters.
        outcomes: list[str]
            A list of outcomes titles that viewers may choose from.
            The list must contain a minimum of 2 outcomes and up to a maximum of 10 outcomes.
            The title itself can only have a maximum of 25 characters.
        prediction_window: int
            The length of time (in seconds) that the prediction will run for.
            The minimum is 30 seconds and the maximum is 1800 seconds (30 minutes).

        Returns
        -------
        Prediction
            A Prediction object.

        Raises
        ------
        ValueError
            The question may contain a maximum of 45 characters.
        ValueError
            You must provide a minimum of 2 choices or a maximum of 5.
        ValueError
            Choice title may contain a maximum of 25 characters.
        ValueError
            Duration must be between 15 and 1800.
        """
        data = await self._http.post_prediction(
            broadcaster_id=self.id,
            title=title,
            outcomes=outcomes,
            prediction_window=prediction_window,
            token_for=self.id,
        )

        if len(outcomes) < 2 or len(outcomes) > 10:
            raise ValueError("You must provide a minimum of 2 choices or a maximum of 10.")
        if any(len(title) > 25 for title in outcomes):
            raise ValueError("Choice title may contain a maximum of 25 characters.")
        if prediction_window < 15 or prediction_window > 1800:
            raise ValueError("Duration must be between 15 and 1800.")

        from .models.predictions import Prediction

        return Prediction(data["data"][0], http=self._http)

    async def end_prediction(
        self,
        *,
        id: str,
        status: Literal["RESOLVED", "CANCELED", "LOCKED"],
        winning_outcome_id: str | None = None,
    ) -> Prediction:
        """|coro|

        End an active prediction.

        The status to set the prediction to. Possible case-sensitive values are:

        - RESOLVED — The winning outcome is determined and the Channel Points are distributed to the viewers who predicted the correct outcome.
        - CANCELED — The broadcaster is canceling the prediction and sending refunds to the participants.
        - LOCKED — The broadcaster is locking the prediction, which means viewers may no longer make predictions.

        The broadcaster can update an active prediction to LOCKED, RESOLVED, or CANCELED; and update a locked prediction to RESOLVED or CANCELED.

        The broadcaster has up to 24 hours after the prediction window closes to resolve the prediction. If not, Twitch sets the status to CANCELED and returns the points.

        A winning_outcome_id must be provided when setting to RESOLVED>

        .. tip::
            You can also call this method directly on a Prediction object with [`end_poll`][twitchio.models.predictions.Prediction.end_prediction]

        Parameters
        ----------
        id: str
            The ID of the prediction to end.
        status  Literal["RESOLVED", "CANCELED", "LOCKED"]
            The status to set the prediction to. Possible case-sensitive values are: ``RESOLVED`` , ``CANCELED`` and ``LOCKED``.
        winning_outcome_id: str
            The ID of the winning outcome. You must set this parameter if you set status to ``RESOLVED``.

        Returns
        -------
        Prediction
            A Prediction object.
        """
        from .models.predictions import Prediction

        data = await self._http.patch_prediction(
            broadcaster_id=self.id, id=id, status=status, token_for=self.id, winning_outcome_id=winning_outcome_id
        )
        return Prediction(data["data"][0], http=self._http)

    async def fetch_stream_key(self) -> str:
        """|coro|

        Fetches the channel's stream key.

        .. note::
            Requires a user access token that includes the ``channel:read:stream_key`` scope

        Returns
        -------
        str
            The channel's stream key.
        """
        data = await self._http.get_stream_key(broadcaster_id=self.id, token_for=self.id)
        return data["data"][0]["stream_key"]

    def fetch_followed_streams(
        self,
        *,
        first: int = 100,
        max_results: int | None = None,
    ) -> HTTPAsyncIterator[Stream]:
        """|aiter|

        Fetches the broadcasters that the user follows and that are streaming live.

        .. note::
            Requires a user access token that includes the ``user:read:follows`` scope

        Parameters
        ----------
        first: int
            The maximum number of items to return per page in the response. The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[Stream]
            HTTPAsyncIterator of Stream objects.
        """
        first = max(1, min(100, first))
        return self._http.get_followed_streams(
            user_id=self.id,
            token_for=self.id,
            first=first,
            max_results=max_results,
        )

    async def create_stream_marker(self, *, token_for: str | PartialUser, description: str | None = None) -> StreamMarker:
        """|coro|

        Adds a marker to a live stream.

        A marker is an arbitrary point in a live stream that the broadcaster or editor wants to mark, so they can return to that spot later to create video highlights.

        .. important::
            You may not add markers:

            - If the stream is not live
            - If the stream has not enabled video on demand (VOD)
            - If the stream is a premiere (a live, first-viewing event that combines uploaded videos with live chat)
            - If the stream is a rerun of a past broadcast, including past premieres.

        .. note::
            Requires a user access token that includes the ``channel:manage:broadcast`` scope.

        Parameters
        ----------
        token_for: str | PartialUser
            This must be the user ID, or PartialUser, of the broadcaster or one of the broadcaster's editors.
        description: str | None
            A short description of the marker to help the user remember why they marked the location.
            The maximum length of the description is 140 characters.

        Returns
        -------
        StreamMarker
            Represents a StreamMarker

        Raises
        ------
        ValueError
            The maximum length of the description is 140 characters.
        """
        if description is not None and len(description) > 140:
            raise ValueError("The maximum length of the description is 140 characters.")

        from .models.streams import StreamMarker

        data = await self._http.post_stream_marker(user_id=self.id, token_for=token_for, description=description)
        return StreamMarker(data["data"][0])

    def fetch_stream_markers(
        self, *, token_for: str | PartialUser, first: int = 20, max_results: int | None = None
    ) -> HTTPAsyncIterator[VideoMarkers]:
        """|aiter|

        Fetches markers from the user's most recent stream or from the specified VOD/video.

        A marker is an arbitrary point in a live stream that the broadcaster or editor marked, so they can return to that spot later to create video highlights

        .. tip::
            To fetch by video ID please use [`fetch_stream_markers`][twitchio.client.fetch_stream_markers]

        .. note::
            Requires a user access token that includes the ``user:read:broadcast`` or ``channel:manage:broadcast scope``.

        Parameters
        ----------
        token_for: str | PartialUser
            This must be the user ID, or PartialUser, of the broadcaster or one of the broadcaster's editors.
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[VideoMarkers]
            HTTPAsyncIterator of VideoMarkers objects.
        """
        first = max(1, min(100, first))
        return self._http.get_stream_markers(
            user_id=self.id,
            token_for=token_for,
            first=first,
            max_results=max_results,
        )

    async def fetch_subscription(self, broadcaster: str | int | PartialUser) -> UserSubscription | None:
        """|coro|

        Checks whether the user subscribes to the broadcaster's channel.

        .. note::
            Requires a user access token that includes the ``user:read:subscriptions`` scope.

        Parameters
        ----------
        broadcaster: str | int | PartialUser
            The ID, or PartialUser, of a partner or affiliate broadcaster.

        Returns
        -------
        UserSubscription | None
            Returns UserSubscription if subscription exists; otherwise None.

        Raises
        ------
        HTTPException
        """
        from .models.subscriptions import UserSubscription

        try:
            data = await self._http.get_user_subscription(user_id=self.id, broadcaster_id=broadcaster, token_for=self.id)
        except HTTPException as e:
            if e.status == 404:
                return None
            else:
                raise e

        return UserSubscription(data["data"][0], http=self._http)

    async def fetch_broadcaster_subscriptions(
        self,
        *,
        user_ids: list[str | int] | None = None,
        first: int = 20,
        max_results: int | None = None,
    ) -> BroadcasterSubscriptions:
        """|coro|

        Fetches all subscriptions for the broadcaster.

        .. note::
            Requires a user access token that includes the ``channel:read:subscriptions`` scope

        Parameters
        ----------
        user_ids: list[str | int] | None
            Filters the list to include only the specified subscribers. You may specify a maximum of 100 subscribers.
        first: int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 20.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        BroadcasterSubscriptions

        Raises
        ------
        ValueError
            You may only provide a maximum of 100 user IDs.
        """
        first = max(1, min(100, first))

        if user_ids is not None and len(user_ids) > 100:
            raise ValueError("You may only provide a maximum of 100 user IDs.")

        return await self._http.get_broadcaster_subscriptions(
            token_for=self.id, broadcaster_id=self.id, user_ids=user_ids, first=first, max_results=max_results
        )

    async def send_whisper(self, *, to_user: str | int | PartialUser, message: str) -> None:
        """|coro|

        Send a whisper to a user.

        You may whisper to a maximum of 40 unique recipients per day. Within the per day limit, you may whisper a maximum of 3 whispers per second and a maximum of 100 whispers per minute.

        .. important::
            The user sending the whisper must have a verified phone number (see the `Phone Number setting in your Security and Privacy <https://www.twitch.tv/settings/security>`_ settings).

            The API may silently drop whispers that it suspects of violating Twitch policies. (The API does not indicate that it dropped the whisper).

            The message must not be empty.

            The maximum message lengths are:

            - 500 characters if the user you're sending the message to hasn't whispered you before.
            - 10,000 characters if the user you're sending the message to has whispered you before.

            Messages that exceed the maximum length are truncated.

        .. note::
            Requires a user access token that includes the ``user:manage:whispers`` scope.

        Parameters
        ----------
        to_user: str | int | PartialUser
            The ID or the PartialUser of the user to receive the whisper.
        message: str
            The whisper message to send. The message must not be empty.

            The maximum message lengths are:

            - 500 characters if the user you're sending the message to hasn't whispered you before.
            - 10,000 characters if the user you're sending the message to has whispered you before.

            Messages that exceed the maximum length are truncated.
        """

        return await self._http.post_whisper(from_user_id=self.id, to_user_id=to_user, token_for=self.id, message=message)

    async def user(self) -> User:
        """|coro|

        Fetch the full User information for the PartialUser.

        Returns
        -------
        User
            User object.
        """
        data = await self._http.get_users(ids=[self.id])
        return User(data["data"][0], http=self._http)

    async def update(self, description: str | None = None) -> User:
        """|coro|

        Update the user's information.

        .. note::
            Requires a user access token that includes the ``user:edit`` scope.

        Parameters
        ----------
        description: str | None
            The string to update the channel's description to. The description is limited to a maximum of 300 characters.
            To remove the description then do not pass this kwarg.

        Returns
        -------
        User
            User object.

        Raises
        ------
        ValueError
            The description must be a maximum of 300 characters.
        """

        if description is not None and len(description) > 300:
            raise ValueError("The description must be a maximum of 300 characters.")

        data = await self._http.put_user(token_for=self.id, description=description)
        return User(data["data"][0], http=self._http)

    def fetch_block_list(self, *, first: int = 20, max_results: int | None = None) -> HTTPAsyncIterator[PartialUser]:
        """|aiter|

        Fetches a list of users that the broadcaster has blocked.

        .. note::
            Requires a user access token that includes the ``user:read:blocked_users`` scope.

        Parameters
        ----------
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.
        max_results: int | None
            Maximum number of total results to return. When this is set to None (default), then everything found is returned.

        Returns
        -------
        HTTPAsyncIterator[PartialUser]
            HTTPAsyncIterator of PartialUser objects.
        """
        return self._http.get_user_block_list(
            broadcaster_id=self.id, token_for=self.id, first=first, max_results=max_results
        )

    async def block_user(
        self,
        *,
        user: str | int | PartialUser,
        source: Literal["chat", "whisper"] | None = None,
        reason: Literal["harassment", "spam", "other"] | None = None,
    ) -> None:
        """|coro|

        Blocks the specified user from interacting with or having contact with the broadcaster.

        The user ID in the OAuth token identifies the broadcaster who is blocking the user.

        Parameters
        ----------
        user: str | int | PartialUser
            The ID, or PartialUser, of the user to block.
        source: Literal["chat", "whisper"] | None
            The location where the harassment took place that is causing the brodcaster to block the user. Possible values are:

            - chat
            - whisper

        reason: Literal["harassment", "spam", "other"] | None
            The reason that the broadcaster is blocking the user. Possible values are:

            - harassment
            - spam
            - other

        Returns
        -------
        None
        """
        return await self._http.put_block_user(user_id=user, source=source, reason=reason, token_for=self.id)

    async def unblock_user(
        self,
        *,
        user: str | int | PartialUser,
    ) -> None:
        """|coro|

        Removes the user from the broadcaster's list of blocked users.

        Parameters
        ----------
        user: str | int | PartialUser
            The ID, or PartialUser, of the user to unblock.

        Returns
        -------
        None
        """
        return await self._http.delete_block_user(user_id=user, token_for=self.id)

    async def fetch_active_extensions(self, token_for: str | PartialUser | None = None) -> ActiveExtensions:
        """|coro|

        Fetches a user's active extensions.

        .. tip::
            To include extensions that you have under development, you must specify a user access token that includes the ``user:read:broadcast`` or ``user:edit:broadcast`` scope.

        Parameters
        ----------
        token_for: str | PartialUser | None
            Optional user access token. To include extensions that you have under development, you must specify a user access token that includes the ``user:read:broadcast`` or ``user:edit:broadcast`` scope.

        Returns
        -------
        ActiveExtensions
            ActiveExtensions object.
        """
        data = await self._http.get_active_user_extensions(user_id=self.id, token_for=token_for)
        return ActiveExtensions(data["data"])

    async def warn_user(
        self,
        *,
        moderator: str | int | PartialUser,
        user_id: str | int | PartialUser,
        reason: str,
    ) -> Warning:
        """|coro|

        Warns a user in the specified broadcaster's chat room, preventing them from chat interaction until the warning is acknowledged.
        New warnings can be issued to a user when they already have a warning in the channel (new warning will replace old warning).

        .. note::
            Requires a user access token that includes the ``moderator:manage:warnings`` scope.
            moderator id must match the user id in the user access token.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the user who requested the warning.
        user_id: str | int | PartialUser
            The ID, or PartialUser, of the user being warned.
        reason: str
            The reason provided for warning.

        Returns
        -------
        Warning
            Warning object.
        """
        from .models.moderation import Warning

        data = await self._http.post_warn_chat_user(
            broadcaster_id=self.id, moderator_id=moderator, user_id=user_id, reason=reason, token_for=moderator
        )
        return Warning(data["data"][0], http=self._http)

    async def update_custom_reward(
        self,
        id: str,
        *,
        title: str | None = None,
        cost: int | None = None,
        prompt: str | None = None,
        enabled: bool | None = None,
        colour: str | Colour | None = None,
        input_required: bool | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        paused: bool | None = None,
        skip_queue: bool | None = None,
    ) -> CustomReward:
        """|coro|

        Update a specific custom reward for this broadcaster / streamer.

        .. important::
            The app / client ID used to create the reward is the only app that may update the reward.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.

        Parameters
        -----------
        id: str
            The ID of the custom reward.
        title: str | None
            The reward's title.
            The title may contain a maximum of 45 characters and it must be unique amongst all of the broadcaster's custom rewards.
        cost: int | None
            The cost of the reward, in channel points. The minimum is 1 point.
        prompt: str | None
            The prompt shown to the viewer when they redeem the reward.
            ``input_required`` needs to be set to ``True`` for this to work,
        enabled: bool | None
             Boolean value that indicates whether the reward is enabled. Set to ``True`` to enable the reward. Viewers see only enabled rewards.
        colour: str | Colour | None
            The background colour to use for the reward. Specify the color using Hex format (for example, #00E5CB).
            You can also pass a twitchio.Colour object.
        input_required: bool | None
            A Boolean value that determines whether users must enter information to redeem the reward.
        max_per_stream: int | None
            The maximum number of redemptions allowed per live stream.
            Setting this to 0 disables the maximum number of redemptions per stream.
        max_per_user: int | None
            The maximum number of redemptions allowed per user per live stream.
            Setting this to 0 disables the maximum number of redemptions per user per stream.
        global_cooldown: int | None
            The cooldown period, in seconds. The minimum value is 1; however, for it to be shown in the Twitch UX, the minimum value is 60.
            Setting this to 0 disables the global cooldown period.
        paused: bool | None
            A Boolean value that determines whether to pause the reward. Set to ``True`` to pause the reward. Viewers can't redeem paused rewards.
        skip_queue: bool | None
            A Boolean value that determines whether redemptions should be set to FULFILLED status immediately when a reward is redeemed.
            If False, status is set to UNFULFILLED and follows the normal request queue process.

        Returns
        --------
        CustomReward

        Raises
        ------
        ValueError
            title must be a maximum of 45 characters.
        ValueError
            prompt must be a maximum of 200 characters.
        ValueError
            Minimum value must be at least 1.
        """

        if title is not None and len(title) > 45:
            raise ValueError("title must be a maximum of 45 characters.")
        if cost is not None and cost < 1:
            raise ValueError("cost must be at least 1.")
        if prompt is not None and len(prompt) > 200:
            raise ValueError("prompt must be a maximum of 200 characters.")

        from .models.channel_points import CustomReward

        data = await self._http.patch_custom_reward(
            broadcaster_id=self.id,
            token_for=self.id,
            reward_id=id,
            title=title,
            cost=cost,
            prompt=prompt,
            enabled=enabled,
            background_color=colour,
            user_input_required=input_required,
            max_per_stream=max_per_stream,
            max_per_user=max_per_user,
            global_cooldown=global_cooldown,
            paused=paused,
            skip_queue=skip_queue,
        )

        return CustomReward(data=data["data"][0], http=self._http)

    async def delete_custom_reward(
        self,
        id: str,
    ) -> None:
        """|coro|

        Delete a specific custom reward for this broadcaster / user.

        The app used to create the reward is the only app that may delete it.
        If the reward's redemption status is UNFULFILLED at the time the reward is deleted, its redemption status is marked as FULFILLED.

        .. note::
            Requires a user access token that includes the ``channel:manage:redemptions`` scope.

        Parameters
        ----------
        id: str
            The ID of the custom reward to delete.

        Returns
        -------
        None
        """
        await self._http.delete_custom_reward(broadcaster_id=self.id, reward_id=id, token_for=self.id)


class User(PartialUser):
    """Represents a User.

    This class inherits from PartialUser and contains additional information about the user.

    Attributes
    ----------
    id: str
        The user's ID.
    name: str | None
        The user's name. Also known as *username* or *login name*. In most cases, this is provided. There are however, rare cases where it is not.
    display_name: str
        The display name of the user.
    type: Literal["admin", "global_mod", "staff", ""]
        The type of the user. Possible values are:

        - admin - Twitch administrator
        - global_mod
        - staff - Twitch staff
        - empty string - Normal user

    broadcaster_type: Literal["affiliate", "partner", ""]
        The broadcaster type of the user. Possible values are:

        - affiliate
        - partner
        - empty string - Normal user

    description: str
        Description of the user.
    profile_image: Asset
        Profile image as an asset.
    offline_image: Asset | None
        Offline image as an asset, otherwise None if broadcaster as not set one.
    email: str | None
        The user's verified email address. The object includes this field only if the user access token includes the ``user:read:email`` scope.
    created_at: datetime.datetime
        When the user was created.
    """

    __slots__ = (
        "broadcaster_type",
        "created_at",
        "description",
        "display_name",
        "email",
        "offline_image",
        "profile_image",
        "type",
    )

    def __init__(self, data: UsersResponseData, *, http: HTTPClient) -> None:
        super().__init__(data["id"], data["login"], data["display_name"], http=http)
        self.type: Literal["admin", "global_mod", "staff", ""] = data["type"]
        self.broadcaster_type: Literal["affiliate", "partner", ""] = data["broadcaster_type"]
        self.description: str = data["description"]
        self.profile_image: Asset = Asset(data["profile_image_url"], http=http)
        self.offline_image: Asset | None = Asset(data["offline_image_url"], http=http) if data["offline_image_url"] else None
        self.email: str | None = data.get("email")
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self) -> str:
        return f"<User id={self.id}, name={self.name} display_name={self.display_name}>"


class Extension:
    """Represents a user extension.

    Attributes
    ----------
    id: str
       An ID that identifies the extension.
    version: str
        The extension's version.
    name: str
        The extension's name.
    can_activate: bool
        A Boolean value that determines whether the extension is configured and can be activated. Is True if the extension is configured and can be activated.
    type: list[Literal["component", "mobile", "overlay", "panel"]]
        The extension types that you can activate for this extension. Possible values are:

        - component
        - mobile
        - overlay
        - panel

    """

    __slots__ = ("can_activate", "id", "name", "type", "version")

    def __init__(self, data: UserExtensionsResponseData) -> None:
        self.id: str = data["id"]
        self.version: str = data["version"]
        self.name: str = data["name"]
        self.can_activate: bool = bool(data["can_activate"])
        self.type: list[Literal["component", "mobile", "overlay", "panel"]] = data["type"]

    def __repr__(self) -> str:
        return f"<Extension id={self.id} name={self.name}>"


class ExtensionItem:
    """Base class of extension items.

    Attributes
    ----------
    id: str | None
       An ID that identifies the extension. This is None if not active.
    version: str | None
        The extension's version. This is None if not active.
    name: str | None
        The extension's name. This is None if not active.
    active: bool
        A Boolean value that determines the extension';'s activation state. If False, the user has not configured this panel extension.
    """

    __slots__ = ("active", "id", "name", "version")

    def __init__(self, data: UserPanelItem | UserPanelOverlayItem | UserPanelComponentItem) -> None:
        self.id: str | None = data.get("id")
        self.name: str | None = data.get("name")
        self.version: str | None = data.get("version")
        self.active: bool = bool(data["active"])

    def __repr__(self) -> str:
        return f"<ExtensionItem id={self.id} name={self.name} active={self.active}>"

    def _to_dict(self) -> dict[str, bool | str | int | None]:
        return {"active": self.active, "id": self.id, "version": self.version}


class ExtensionPanel(ExtensionItem):
    """Represents an extension panel item.

    Attributes
    ----------
    id: str | None
       An ID that identifies the extension. This is None if not active.
    version: str | None
        The extension's version. This is None if not active.
    name: str | None
        The extension's name. This is None if not active.
    active: bool
        A Boolean value that determines the extension';'s activation state. If False, the user has not configured this panel extension.
    """

    def __init__(self, data: UserPanelItem) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<ExtensionPanel id={self.id} name={self.name} active={self.active}>"


class ExtensionOverlay(ExtensionItem):
    """Represents an extension overlay item.

    Attributes
    ----------
    id: str | None
       An ID that identifies the extension. This is None if not active.
    version: str | None
        The extension's version. This is None if not active.
    name: str | None
        The extension's name. This is None if not active.
    active: bool
        A Boolean value that determines the extension's activation state. If False, the user has not configured this panel extension.
    """

    def __init__(self, data: UserPanelOverlayItem) -> None:
        super().__init__(data)

    def __repr__(self) -> str:
        return f"<ExtensionOverlay id={self.id} name={self.name} active={self.active}>"


class ExtensionComponent(ExtensionItem):
    """Represents an extension component item.

    Attributes
    ----------
    id: str | None
       An ID that identifies the extension. This is None if not active.
    version: str | None
        The extension's version. This is None if not active.
    name: str | None
        The extension's name. This is None if not active.
    active: bool
        A Boolean value that determines the extension';'s activation state. If False, the user has not configured this panel extension.
    x: int | None
        The x-coordinate where the extension is placed.
    y: int | None
        The y-coordinate where the extension is placed.
    """

    def __init__(self, data: UserPanelComponentItem) -> None:
        super().__init__(data)
        self.x = int(data["x"]) if "x" in data else None
        self.y = int(data["y"]) if "y" in data else None

    def _to_dict(self) -> dict[str, bool | str | int | None]:
        data = super()._to_dict()
        data.update({"x": self.x, "y": self.y})
        return data

    def __repr__(self) -> str:
        return f"<ExtensionComponent id={self.id} name={self.name} active={self.active}>"


class ActiveExtensions:
    __slots__ = ("components", "overlays", "panels")

    def __init__(self, data: UserActiveExtensionsResponseData) -> None:
        self.panels: list[ExtensionPanel] = [ExtensionPanel(d) for d in data["panel"].values()]
        self.overlays: list[ExtensionOverlay] = [ExtensionOverlay(d) for d in data["overlay"].values()]
        self.components: list[ExtensionComponent] = [ExtensionComponent(d) for d in data["component"].values()]

    def __repr__(self) -> str:
        return f"<ActiveExtensions panels={self.panels} overlays={self.overlays} components={self.components}>"

    def _to_dict(self) -> dict[str, dict[str, dict[str, bool | str | int | None]]]:
        """
        Serialise all contained extensions to a dictionary that can be easily converted to JSON.
        This method aggregates the serialised data of all extensions in the format required by Helix.
        """
        return {
            "panel": {str(i + 1): panel._to_dict() for i, panel in enumerate(self.panels)},
            "overlay": {str(i + 1): overlay._to_dict() for i, overlay in enumerate(self.overlays)},
            "component": {str(i + 1): component._to_dict() for i, component in enumerate(self.components)},
        }


class Chatter(PartialUser):
    """Class which represents a User in a chat room and has sent a message.

    This class inherits from :class:`~twitchio.PartialUser` and contains additional information about the chatting user.
    Most of the additional information is received in the form of the badges sent by Twitch.

    .. note::

        You usually wouldn't construct this class yourself. You will receive it in :class:`~.commands.Command` callbacks,
        via :class:`~.commands.Context` and in the ``event_message`` event.
    """

    __slots__ = (
        "__dict__",
        "_badges",
        "_channel",
        "_colour",
        "_is_admin",
        "_is_artist_badge",
        "_is_broadcaster",
        "_is_founder",
        "_is_moderator",
        "_is_no_audio",
        "_is_no_video",
        "_is_premium",
        "_is_staff",
        "_is_subscriber",
        "_is_turbo",
        "_is_verified",
        "_is_vip",
    )

    def __init__(
        self,
        payload: ChannelChatMessageEvent,
        *,
        http: HTTPClient,
        broadcaster: PartialUser,
        badges: list[ChatMessageBadge],
    ) -> None:
        super().__init__(
            id=payload["chatter_user_id"],
            name=payload["chatter_user_login"],
            display_name=payload["chatter_user_name"],
            http=http,
        )

        slots = [s for s in self.__slots__ if not s.startswith("__")]
        for badge in badges:
            name = f"_is_{badge.set_id}".replace("-", "_")

            if name in slots:
                setattr(self, name, True)

        self._channel: PartialUser = broadcaster
        self._colour: Colour | None = Colour.from_hex(payload["color"]) if payload["color"] else None
        self._badges: list[ChatMessageBadge] = badges

    def __repr__(self) -> str:
        return f"<Chatter id={self.id} name={self.name}, channel={self.channel}>"

    @property
    def channel(self) -> PartialUser:
        """Property returning the channel in the form of a :class:`~twitchio.PartialUser` this chatter belongs to."""
        return self._channel

    @property
    def staff(self) -> bool:
        """A property returning a bool indicating whether the chatter is Twitch Staff.

        This bool should always be ``True`` when the chatter is a Twitch Staff.
        """
        return getattr(self, "_is_staff", False)

    @property
    def admin(self) -> bool:
        """A property returning a bool indicating whether the chatter is Twitch Admin.

        This bool should always be ``True`` when the chatter is a Twitch Admin.
        """
        return getattr(self, "_is_admin", False)

    @property
    def broadcaster(self) -> bool:
        """A property returning a bool indicating whether the chatter is the broadcaster.

        This bool should always be ``True`` when the chatter is the broadcaster.
        """
        return getattr(self, "_is_broadcaster", False)

    @property
    def moderator(self) -> bool:
        """A property returning a bool indicating whether the chatter is a moderator.

        This bool should always be ``True`` when the chatter is a moderator.
        """
        return getattr(self, "_is_moderator", False) or self.broadcaster

    @property
    def vip(self) -> bool:
        """A property returning a bool indicating whether the chatter is a VIP."""
        return getattr(self, "_is_vip", False)

    @property
    def artist(self) -> bool:
        """A property returning a bool indicating whether the chatter is an artist for the channel."""
        return getattr(self, "_is_artist_badge", False)

    @property
    def founder(self) -> bool:
        """A property returning a bool indicating whether the chatter is a founder of the channel."""
        return getattr(self, "_is_founder", False)

    @property
    def subscriber(self) -> bool:
        """A property returning a bool indicating whether the chatter is a subscriber of the channel."""
        return getattr(self, "_is_subscriber", False)

    @property
    def no_audio(self) -> bool:
        """A property returning a bool indicating whether the chatter is watching without audio."""
        return getattr(self, "_is_no_audio", False)

    @property
    def no_video(self) -> bool:
        """A property returning a bool indicating whether the chatter is watching without video."""
        return getattr(self, "_is_no_video", False)

    @property
    def partner(self) -> bool:
        """A property returning a bool indicating whether the chatter is a Twitch partner."""
        return getattr(self, "_is_partner", False)

    @property
    def turbo(self) -> bool:
        """A property returning a bool indicating whether the chatter has Twitch Turbo."""
        return getattr(self, "_is_turbo", False)

    @property
    def prime(self) -> bool:
        """A property returning a bool indicating whether the chatter has Twitch Prime."""
        return getattr(self, "_is_premium", False)

    @property
    def colour(self) -> Colour | None:
        """Property returning the colour of the chatter as a :class:`~twitchio.Colour`.

        There is an alias for this property named :attr:`.color`.

        Could be `None` if the chatter has not set a colour.
        """
        return self._colour

    @property
    def color(self) -> Colour | None:
        """Property returning the color of the chatter as a :class:`~twitchio.Colour`.

        There is an alias for this property named :attr:`.colour`.

        Could be `None` if the chatter has not set a color.
        """
        return self._colour

    @property
    def badges(self) -> list[ChatMessageBadge]:
        """Property returning a list of :class:`~twitchio.ChatMessageBadge` associated with the chatter in this channel."""
        return self._badges

    async def ban(self, moderator: str | PartialUser, reason: str | None = None) -> Ban:
        """|coro|

        Ban the chatter from the associated channel/broadcaster.

        .. important::
            This is different to the :meth:`~twitchio.user.PartialUser.ban_user` as it will ban this chatter directly in the associated channel in the object.

        .. note::

            You must have a user access token that includes the ``moderator:manage:banned_users`` scope to do this.

        Parameters
        ----------
        moderator: str | PartialUser
            The ID of or the :class:`~twitchio.PartialUser` object of the moderator issuing this action. You must have a
            token stored with the ``moderator:manage:banned_users`` scope for this moderator.
        reason: str | None
            An optional reason this chatter is being banned. If provided the length of the reason must not be more than
            ``500`` characters long. Defaults to `None`.

        Raises
        ------
        ValueError
            The length of the reason parameter exceeds 500 characters.
        TypeError
            You can not ban the broadcaster.
        HTTPException
            The request to ban the chatter failed.

        Returns
        -------
        Ban
            The :class:`~twitchio.Ban` object for this ban.
        """
        if reason and len(reason) > 500:
            raise ValueError("The provided reason exceeds the allowed length of 500 characters.")

        if self.broadcaster:
            raise TypeError("Banning the broadcaster of a channel is not a possible action.")

        return await self._channel.ban_user(moderator=moderator, user=self, reason=reason)

    async def timeout(
        self, moderator: str | PartialUser | None = None, duration: int = 600, reason: str | None = None
    ) -> Timeout:
        """|coro|

        Timeout the chatter from the associated channel/broadcaster.

        .. important::
            This is different to the :meth:`~twitchio.user.PartialUser.timeout_user` as it will timeout this chatter directly in the associated channel in the object.

        .. note::

            You must have a user access token that includes the ``moderator:manage:banned_users`` scope to do this.

        Parameters
        ----------
        moderator: str | PartialUser | None
            The ID of or the :class:`~twitchio.PartialUser` object of the moderator issuing this action. You must have a
            token stored with the ``moderator:manage:banned_users`` scope for this moderator.
        duration: int
            The duration of the timeout in seconds. The minimum duration is ``1`` second and the
            maximum is ``1_209_600`` seconds (2 weeks).

            To end the chatters timeout early, set this field to ``1``,
            or use the :meth:`~twitchio.user.PartialUser.unban_user` endpoint.

            The default is ``600`` which is ten minutes.
        reason: str | None
            An optional reason this chatter is being banned. If provided the length of the reason must not be more than
            ``500`` characters long. Defaults to `None`.
        """
        if reason and len(reason) > 500:
            raise ValueError("The provided reason exceeds the allowed length of 500 characters.")

        if self.broadcaster:
            raise TypeError("Banning the broadcaster of a channel is not a possible action.")

        return await self._channel.timeout_user(moderator=moderator, user=self, duration=duration, reason=reason)

    async def warn(self, moderator: str | PartialUser, reason: str) -> Warning:
        """|coro|

        Send this chatter a warning, preventing them from chat interaction until the warning is acknowledged.
        New warnings can be issued to a chatter / user when they already have a warning in the channel (new warning will replace old warning).

        .. important::
            This is different to the :meth:`~twitchio.user.PartialUser.warn_user` as it will warn this chatter directly for the associated channel in the object.

        .. note::
            Requires a user access token that includes the ``moderator:manage:warnings`` scope.
            moderator id must match the user id in the user access token.

        Parameters
        ----------
        moderator: str | int | PartialUser
            The ID, or PartialUser, of the user who requested the warning.
        reason: str
            The reason provided for warning.

        Returns
        -------
        Warning
            Warning object.
        """
        from .models.moderation import Warning

        data = await self._http.post_warn_chat_user(
            broadcaster_id=self.channel, moderator_id=moderator, user_id=self, reason=reason, token_for=moderator
        )
        return Warning(data["data"][0], http=self._http)

    async def block(
        self,
        source: Literal["chat", "whisper"] | None = None,
        reason: Literal["harassment", "spam", "other"] | None = None,
    ) -> None:
        """|coro|

        Blocks this chatter from interacting with or having contact with the broadcaster.

        The user ID in the OAuth token identifies the broadcaster who is blocking the user.

        .. important::
            This is different to the :meth:`~twitchio.user.PartialUser.block_user` as it will block this chatter directly from the associated channel in the object.

        .. note::
            Requires a user access token that includes the ``user:manage:blocked_users`` scope.

        Parameters
        ----------
        source: Literal["chat", "whisper"] | None
            The location where the harassment took place that is causing the brodcaster to block the user. Possible values are:

            - chat
            - whisper

        reason: Literal["harassment", "spam", "other"] | None
            The reason that the broadcaster is blocking the user. Possible values are:

            - harassment
            - spam
            - other

        Returns
        -------
        None
        """

        return await self._http.put_block_user(user_id=self, source=source, reason=reason, token_for=self.channel)

    async def follow_info(self) -> ChannelFollowerEvent | None:
        """|coro|

        Check whether this Chatter is following the broadcaster. If the user is not following then this will return `None`.

        .. important::
            You must have a user token for the broadcaster / channel that this chatter is being checked in.

        .. note::
            Requires user access token that includes the ``moderator:read:followers`` scope.

        Returns
        -------
        ChannelFollowerEvent | None
        """

        data = await self._http.get_channel_followers(
            user_id=self, broadcaster_id=self.channel, token_for=self.channel, max_results=1
        )
        return await anext(data.followers, None)
