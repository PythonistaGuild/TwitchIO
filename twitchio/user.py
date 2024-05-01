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

from .models.ads import AdSchedule, CommercialStart, SnoozeAd


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPAsyncIterator
    from twitchio.models.chat import Chatters

    from .http import HTTPClient
    from .models.analytics import ExtensionAnalytics, GameAnalytics
    from .models.bits import BitsLeaderboard
    from .models.channel_points import CustomReward
    from .models.channels import ChannelEditor, ChannelFollowers, ChannelInfo, FollowedChannels
    from .models.charity import CharityCampaign, CharityDonation
    from .utils import Colour

__all__ = ("PartialUser",)


class PartialUser:
    """
    A class that contains minimal data about a user from the API.

    Attributes
    -----------
    id: str
        The user's ID.
    name: str | None
        The user's name. In most cases, this is provided. There are however, rare cases where it is not.
    """

    __slots__ = "id", "name", "_http", "_cached_rewards"

    def __init__(self, id: int | str, name: str | None = None, *, http: HTTPClient) -> None:
        self._http = http
        self.id = str(id)
        self.name = name

    def __repr__(self) -> str:
        return f"<PartialUser id={self.id}, name={self.name}>"

    async def start_commercial(self, *, length: int, token_for: str) -> CommercialStart:
        """
        Starts a commercial on the specified channel.

        !!! info
            Only partners and affiliates may run commercials and they must be streaming live at the time.

        !!! info
            Only the broadcaster may start a commercial; the broadcaster's editors and moderators may not start commercials on behalf of the broadcaster.

        !! note
            Requires user access token that includes the ``channel:edit:commercial`` scope.

        Parameters
        ----------
        length : int
            The length of the commercial to run, in seconds. Max length is 180.
            If you request a commercial that's longer than 180 seconds, the API uses 180 seconds.
        token_for : str
            User OAuth token to use that includes the ``channel:edit:commercial`` scope.

        Returns
        -------
        twitchio.CommercialStart
            A CommercialStart object.
        """
        data = await self._http.start_commercial(broadcaster_id=self.id, length=length, token_for=token_for)
        return CommercialStart(data["data"][0])

    async def fetch_ad_schedule(self, token_for: str) -> AdSchedule:
        """
        Fetch ad schedule related information, including snooze, when the last ad was run, when the next ad is scheduled, and if the channel is currently in pre-roll free time.

        !!! info
            A new ad cannot be run until 8 minutes after running a previous ad.

        !!! info
            The user id in the user access token must match the id of this PartialUser object.

        !! note
            Requires user access token that includes the ``channel:read:ads`` scope.

        Parameters
        ----------
        token_for : str
            User OAuth token to use that includes the ``channel:edit:commercial`` scope.

        Returns
        -------
        twitchio.AdSchedule
            An AdSchedule object.
        """
        data = await self._http.get_ad_schedule(broadcaster_id=self.id, token_for=token_for)
        return AdSchedule(data["data"][0])

    async def snooze_next_ad(self, token_for: str) -> SnoozeAd:
        """
        If available, pushes back the timestamp of the upcoming automatic mid-roll ad by 5 minutes.
        This endpoint duplicates the snooze functionality in the creator dashboard's Ads Manager.

        !!! info
            The user id in the user access token must match the id of this PartialUser object.

        !! note
            Requires user access token that includes the ``channel:manage:ads`` scope.

        Parameters
        ----------
        token_for : str
            User OAuth token to use that includes the ``channel:manage:ads`` scope.

        Returns
        -------
        twitchio.SnoozeAd
            A SnoozeAd object.
        """
        data = await self._http.get_ad_schedule(broadcaster_id=self.id, token_for=token_for)
        return SnoozeAd(data["data"][0])

    async def fetch_extension_analytics(
        self,
        *,
        token_for: str,
        first: int = 20,
        extension_id: str | None = None,
        type: Literal["overview_v2"] = "overview_v2",
        started_at: datetime.date | None = None,
        ended_at: datetime.date | None = None,
    ) -> HTTPAsyncIterator[ExtensionAnalytics]:
        """
        Fetches an analytics report for one or more extensions. The response contains the URLs used to download the reports (CSV files)

        !!! info
            Both ``started_at`` and ``ended_at`` must be provided when requesting a date range.
            If you omit both of these then the report includes all available data from January 31, 2018.

            Because it can take up to two days for the data to be available, you must specify an end date that's earlier than today minus one to two days.
            If not, the API ignores your end date and uses an end date that is today minus one to two days.


        !!! note
            Requires user access token that includes the ``analytics:read:extensions`` scope.

        Parameters
        -----------
        token_for: str
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

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.ExtensionAnalytics]

        Raises
        ------
        ValueError
            Both started_at and ended_at must be provided together.
        """

        first = max(1, min(100, first))

        if bool(started_at) != bool(ended_at):
            raise ValueError("Both started_at and ended_at must be provided together.")

        return await self._http.get_extension_analytics(
            first=first,
            token_for=token_for,
            extension_id=extension_id,
            type=type,
            started_at=started_at,
            ended_at=ended_at,
        )

    async def fetch_game_analytics(
        self,
        *,
        token_for: str,
        first: int = 20,
        game_id: str | None = None,
        type: Literal["overview_v2"] = "overview_v2",
        started_at: datetime.date | None = None,
        ended_at: datetime.date | None = None,
    ) -> HTTPAsyncIterator[GameAnalytics]:
        """
        Fetches a game report for one or more games. The response contains the URLs used to download the reports (CSV files)

        !!! info
            Both ``started_at`` and ``ended_at`` must be provided when requesting a date range.
            If you omit both of these then the report includes all available data from January 31, 2018.

            Because it can take up to two days for the data to be available, you must specify an end date that's earlier than today minus one to two days.
            If not, the API ignores your end date and uses an end date that is today minus one to two days.


        !!! note
            Requires user access token that includes the ``analytics:read:extensions`` scope.

        Parameters
        -----------
        token_for: str
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

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.GameAnalytics]

        Raises
        ------
        ValueError
            Both started_at and ended_at must be provided together.
        """

        first = max(1, min(100, first))

        if bool(started_at) != bool(ended_at):
            raise ValueError("Both started_at and ended_at must be provided together")

        return await self._http.get_game_analytics(
            first=first,
            token_for=token_for,
            game_id=game_id,
            type=type,
            started_at=started_at,
            ended_at=ended_at,
        )

    async def fetch_bits_leaderboard(
        self,
        token_for: str,
        count: int = 10,
        period: Literal["all", "day", "week", "month", "year"] = "all",
        started_at: datetime.datetime | None = None,
        user_id: str | int | None = None,
    ) -> BitsLeaderboard:
        """
        Fetches the Bits leaderboard for this user.

        !!! info
            ``started_at`` is converted to PST before being used, so if you set the start time to 2022-01-01T00:00:00.0Z and period to month,
            the actual reporting period is December 2021, not January 2022.
            If you want the reporting period to be January 2022, you must set the start time to 2022-01-01T08:00:00.0Z or 2022-01-01T00:00:00.0-08:00.

        !!! info
            When providing ``started_at``, you must also change the ``period`` parameter to any value other than "all".
            Conversely, if ``period`` is set to anything other than "all", ``started_at`` must also be provided.


        !!! note
            Requires user access token that includes the ``bits:read`` scope.

        | Period          | Description |
        | -----------      | -------------- |
        | day   | A day spans from 00:00:00 on the day specified in started_at and runs through 00:00:00 of the next day.            |
        | week   | A week spans from 00:00:00 on the Monday of the week specified in started_at and runs through 00:00:00 of the next Monday.           |
        | month    | A month spans from 00:00:00 on the first day of the month specified in started_at and runs through 00:00:00 of the first day of the next month.            |
        | year    | A year spans from 00:00:00 on the first day of the year specified in started_at and runs through 00:00:00 of the first day of the next year.            |
        | all   | Default. The lifetime of the broadcaster's channel.            |


        Parameters
        ----------
        count : int
            The number of results to return. The minimum count is 1 and the maximum is 100. The default is 10.
        period : Literal["all", "day", "week", "month", "year"]
            The time period over which data is aggregated (uses the PST time zone).
        started_at : datetime.datetime | None
            The start date, used for determining the aggregation period. Specify this parameter only if you specify the period query parameter.
            The start date is ignored if period is all.
        user_id : str | int | None
            An ID that identifies a user that cheered bits in the channel.
            If count is greater than 1, the response may include users ranked above and below the specified user.
            To get the leaderboard's top leaders, don't specify a user ID.
        token_for : str
            User OAuth token to use that includes the ``bits:read`` scope.

        Returns
        -------
        twitchio.BitsLeaderboard
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
            broadcaster_id=self.id,
            token_for=token_for,
            count=count,
            period=period,
            started_at=started_at,
            user_id=user_id,
        )
        return BitsLeaderboard(data, http=self._http)

    async def fetch_channel_info(self, *, token_for: str | None = None) -> ChannelInfo:
        """
        Retrieve channel information for this user.

        Parameters
        -----------
        token_for: str | None
            An optional User OAuth token to use instead of the default app token.
        Returns
        --------
        twitchio.ChannelInfo
            ChannelInfo object representing the channel information.
        """
        from .models.channels import ChannelInfo

        data = await self._http.get_channel_info(broadcaster_ids=[self.id], token_for=token_for)
        return ChannelInfo(data["data"][0], http=self._http)

    async def modify_channel(
        self,
        *,
        token_for: str,
        game_id: str | None = None,
        language: str | None = None,
        title: str | None = None,
        delay: int | None = None,
        tags: list[str] | None = None,
        classification_labels: list[
            dict[Literal["DrugsIntoxication", "SexualThemes", "ViolentGraphic", "Gambling", "ProfanityVulgarity"], bool]
        ]
        | None = None,
        branded: bool | None = None,
    ) -> None:
        """
        Updates this user's channel properties.

        !! info
            A channel may specify a maximum of 10 tags. Each tag is limited to a maximum of 25 characters and may not be an empty string or contain spaces or special characters.
            Tags are case insensitive.
            For readability, consider using camelCasing or PascalCasing.

        !!! note
            Requires user access token that includes the ``channel:manage:broadcast`` scope.


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
            You may set a maximum of 10 tags, each limited to 25 characters. They can not be empty strings, contain spaces or special characters
            See here for more [information](https://help.twitch.tv/s/article/guide-to-tags)
        classification_labels: list[dict[Literal["DrugsIntoxication", "SexualThemes", "ViolentGraphic", "Gambling", "ProfanityVulgarity"], bool]] | None
            List of labels that should be set as the Channel's CCLs.
        branded: bool | None
            Boolean flag indicating if the channel has branded content.
        token_for: str
            User OAuth token to use that includes the ``channel:manage:broadcast`` scope.
        """

        return await self._http.patch_channel_info(
            broadcaster_id=self.id,
            token_for=token_for,
            game_id=game_id,
            language=language,
            title=title,
            delay=delay,
            tags=tags,
            classification_labels=classification_labels,
            branded_content=branded,
        )

    async def fetch_channel_editors(self, token_for: str) -> list[ChannelEditor]:
        """
        Fetches a list of the user's editors for their channel.

        !!! note
            Requires user access token that includes the ``channel:manage:broadcast`` scope.

        Parameters
        -----------
        token_for: str
            User OAuth token to use that includes the ``channel:manage:broadcast`` scope.

        Returns
        -------
        list[ChannelEditor]
            A list of ChannelEditor objects.
        """
        from .models.channels import ChannelEditor

        data = await self._http.get_channel_editors(broadcaster_id=self.id, token_for=token_for)
        return [ChannelEditor(d, http=self._http) for d in data["data"]]

    async def fetch_followed_channels(
        self, token_for: str, broadcaster_id: str | int | None = None
    ) -> FollowedChannels | None:
        """
        Fetches information of who and when this user followed other channels.

        !!! note
            Requires user access token that includes the ``user:read:follows`` scope.

        Parameters
        -----------
        broadcaster_id: str | int | None
            Use this parameter to see whether the user follows this broadcaster.
        token_for: str
            User OAuth token to use that includes the ``user:read:follows`` scope.

        Returns
        -------
        ChannelsFollowed
            ChannelsFollowed object.
        """

        return await self._http.get_followed_channels(
            user_id=self.id,
            token_for=token_for,
            broadcaster_id=broadcaster_id,
        )

    async def fetch_channels_followers(self, token_for: str, user_id: str | int | None = None) -> ChannelFollowers:
        """
        Fetches information of who and when users followed this channel.

        !!! info
            The User ID in the token must match that of the broadcaster or a moderator.

        !!! note
            Requires user access token that includes the ``moderator:read:followers`` scope.

        Parameters
        -----------
        user_id: str | int | None
            Use this parameter to see whether the user follows this broadcaster.
        token_for: str
            User OAuth token to use that includes the ``moderator:read:followers`` scope.

        Returns
        -------
        ChannelFollowers
            A ChannelFollowers object.
        """

        return await self._http.get_channel_followers(
            broadcaster_id=self.id,
            token_for=token_for,
            user_id=user_id,
        )

    async def create_custom_reward(
        self,
        *,
        token_for: str,
        title: str,
        cost: int,
        prompt: str | None = None,
        enabled: bool = True,
        background_color: str | Colour | None = None,
        max_per_stream: int | None = None,
        max_per_user: int | None = None,
        global_cooldown: int | None = None,
        redemptions_skip_queue: bool = False,
    ) -> CustomReward:
        """
        Creates a Custom Reward in the broadcaster's channel.

        !!! info
            The maximum number of custom rewards per channel is 50, which includes both enabled and disabled rewards.

        !!! note
            Requires user access token that includes the channel:manage:redemptions scope.

        Parameters
        -----------
        title: str
            The custom reward's title. The title may contain a maximum of 45 characters and it must be unique amongst all of the broadcaster's custom rewards.
        cost: int
            The cost of the reward, in Channel Points. The minimum is 1 point.
        prompt: str | None
            The prompt shown to the viewer when they redeem the reward. The prompt is limited to a maximum of 200 characters.
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
        token_for: str
            User OAuth token to use that includes the ``channel:manage:redemptions`` scope.

        Returns
        --------
        twitchio.CustomReward
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
            token_for=token_for,
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

    async def fetch_custom_rewards(
        self, *, token_for: str, ids: list[str] | None = None, manageable: bool = False
    ) -> list[CustomReward]:
        """
        Fetches list of custom rewards that the specified broadcaster created.

        !!! note
            Requires user access token that includes the ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.

        Parameters
        ----------
        token_for : str
            A user access token that includes the ``channel:read:redemptions`` or ``channel:manage:redemptions`` scope.
        ids : list[str] | None
            A list of IDs to filter the rewards by. You may request a maximum of 50.
        manageable : bool, optional
            A Boolean value that determines whether the response contains only the custom rewards that the app (Client ID) may manage.
            Default is False.

        Returns
        -------
        list[CustomReward]
            _description_
        """
        from .models.channel_points import CustomReward

        data = await self._http.get_custom_reward(
            broadcaster_id=self.id, reward_ids=ids, manageable=manageable, token_for=token_for
        )
        return [CustomReward(d, http=self._http) for d in data["data"]]

    async def fetch_charity_campaign(self, *, token_for: str) -> CharityCampaign:
        """
        Fetch the active charity campaign of a broadcaster.

        !!! note
            Requires user access token that includes the ``channel:read:charity`` scope.

        Parameters
        ----------
        token_for : str
            A user access token that includes the ``channel:read:charity`` scope.

        Returns
        -------
        CharityCampaign
            A CharityCampaign object.
        """
        from .models.charity import CharityCampaign

        data = await self._http.get_charity_campaign(broadcaster_id=self.id, token_for=token_for)
        return CharityCampaign(data["data"][0], http=self._http)

    async def fetch_charity_donations(
        self,
        *,
        token_for: str,
        first: int = 20,
    ) -> HTTPAsyncIterator[CharityDonation]:
        """
        Fetches information about all broadcasts on Twitch.

        !!! note
            Requires user access token that includes the ``channel:read:charity`` scope.

        Parameters
        -----------
        token_for: str
            A user access token that includes the ``channel:read:charity`` scope.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.CharityDonation]
        """

        first = max(1, min(100, first))

        return await self._http.get_charity_donations(
            broadcaster_id=self.id,
            first=first,
            token_for=token_for,
        )

    async def fetch_chatters(self, *, moderator_id: str | int, token_for: str, first: int = 100) -> Chatters:
        """
        Fetches users that are connected to the broadcaster's chat session.

        !!! note
            Requires user access token that includes the ``moderator:read:chatters`` scope.

        Parameters
        ----------
        moderator_id : str | int
            The ID of the broadcaster or one of the broadcaster's moderators.
            This ID must match the user ID in the user access token.
        token_for : str
            A user access token that includes the ``moderator:read:chatters`` scope.
        first : int | None
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 1,000. The default is 100.

        Returns
        -------
        Chatters
            A Chatters object containing the information of a broadcaster's connected chatters.
        """
        first = max(1, min(1000, first))

        return await self._http.get_chatters(
            token_for=token_for, first=first, broadcaster_id=self.id, moderator_id=moderator_id
        )


    async def fetch_channel_emotes(self):
        ... #TODO