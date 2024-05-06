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
from .models.raids import Raid


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
    from .models.chat import ChannelEmote, ChatBadge, ChatSettings, SentMessage, UserEmote
    from .models.clips import Clip, CreatedClip
    from .models.goals import Goal
    from .models.hype_train import HypeTrainEvent
    from .models.teams import ChannelTeam
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

            Only the broadcaster may start a commercial; the broadcaster's editors and moderators may not start commercials on behalf of the broadcaster.

        ??? note
            Requires user access token that includes the `channel:edit:commercial` scope.

        Parameters
        ----------
        length: int
            The length of the commercial to run, in seconds. Max length is 180.
            If you request a commercial that's longer than 180 seconds, the API uses 180 seconds.
        token_for: str
            User token to use that includes the `channel:edit:commercial` scope.

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

            The user id in the user access token must match the id of this PartialUser object.

        ??? note
            Requires user access token that includes the `channel:read:ads` scope.

        Parameters
        ----------
        token_for: str
            User token to use that includes the `channel:read:ads` scope.

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

        ??? note
            Requires user access token that includes the `channel:manage:ads` scope.

        Parameters
        ----------
        token_for: str
            User token to use that includes the `channel:manage:ads` scope.

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
            - Both `started_at` and `ended_at` must be provided when requesting a date range.
            If you omit both of these then the report includes all available data from January 31, 2018.

            - Because it can take up to two days for the data to be available, you must specify an end date that's earlier than today minus one to two days.
            If not, the API ignores your end date and uses an end date that is today minus one to two days.


        ??? note
            Requires user access token that includes the `analytics:read:extensions` scope.

        Parameters
        -----------
        token_for: str
            A user access token that includes the `analytics:read:extensions` scope.
        extension_id: str
            The extension's client ID. If specified, the response contains a report for the specified extension.
            If not specified, the response includes a report for each extension that the authenticated user owns.
        type: Literal["overview_v2"]
            The type of analytics report to get. This is set to `overview_v2` by default.
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
            - Both `started_at` and `ended_at` must be provided when requesting a date range.
            If you omit both of these then the report includes all available data from January 31, 2018.

            - Because it can take up to two days for the data to be available, you must specify an end date that's earlier than today minus one to two days.
            If not, the API ignores your end date and uses an end date that is today minus one to two days.


        ??? note
            Requires user access token that includes the `analytics:read:extensions` scope.

        Parameters
        -----------
        token_for: str
            A user access token that includes the `analytics:read:extensions` scope.
        game_id: str
            The game's client ID. If specified, the response contains a report for the specified game.
            If not specified, the response includes a report for each of the authenticated user's games.
        type: Literal["overview_v2"]
            The type of analytics report to get. This is set to `overview_v2` by default.
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
            - `started_at` is converted to PST before being used, so if you set the start time to 2022-01-01T00:00:00.0Z and period to month,
            the actual reporting period is December 2021, not January 2022.
            If you want the reporting period to be January 2022, you must set the start time to 2022-01-01T08:00:00.0Z or 2022-01-01T00:00:00.0-08:00.

            - When providing `started_at`, you must also change the `period` parameter to any value other than "all".
            Conversely, if `period` is set to anything other than "all", `started_at` must also be provided.


        ??? note
            Requires user access token that includes the `bits:read` scope.

        | Period  | Description |
        | ------- | -------------- |
        | day     | A day spans from 00:00:00 on the day specified in started_at and runs through 00:00:00 of the next day.            |
        | week    | A week spans from 00:00:00 on the Monday of the week specified in started_at and runs through 00:00:00 of the next Monday.           |
        | month   | A month spans from 00:00:00 on the first day of the month specified in started_at and runs through 00:00:00 of the first day of the next month.            |
        | year    | A year spans from 00:00:00 on the first day of the year specified in started_at and runs through 00:00:00 of the first day of the next year.            |
        | all     | Default. The lifetime of the broadcaster's channel.            |


        Parameters
        ----------
        count: int
            The number of results to return. The minimum count is 1 and the maximum is 100. The default is 10.
        period: Literal["all", "day", "week", "month", "year"]
            The time period over which data is aggregated (uses the PST time zone).
        started_at: datetime.datetime | None
            The start date, used for determining the aggregation period. Specify this parameter only if you specify the period query parameter.
            The start date is ignored if period is all.
        user_id: str | int | None
            An ID that identifies a user that cheered bits in the channel.
            If count is greater than 1, the response may include users ranked above and below the specified user.
            To get the leaderboard's top leaders, don't specify a user ID.
        token_for: str
            User token to use that includes the `bits:read` scope.

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
            An optional user token to use instead of the default app token.
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

        !!! info
            A channel may specify a maximum of 10 tags. Each tag is limited to a maximum of 25 characters and may not be an empty string or contain spaces or special characters.
            Tags are case insensitive.
            For readability, consider using camelCasing or PascalCasing.

        ??? note
            Requires user access token that includes the `channel:manage:broadcast` scope.


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
            User token to use that includes the `channel:manage:broadcast` scope.
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

    async def fetch_editors(self, token_for: str) -> list[ChannelEditor]:
        """
        Fetches a list of the user's editors for their channel.

        ??? note
            Requires user access token that includes the `channel:manage:broadcast` scope.

        Parameters
        -----------
        token_for: str
            User token to use that includes the `channel:manage:broadcast` scope.

        Returns
        -------
        list[twitchio.ChannelEditor]
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

        ??? note
            Requires user access token that includes the `user:read:follows` scope.

        Parameters
        -----------
        broadcaster_id: str | int | None
            Use this parameter to see whether the user follows this broadcaster.
        token_for: str
            User token to use that includes the `user:read:follows` scope.

        Returns
        -------
        twitchio.ChannelsFollowed
            ChannelsFollowed object.
        """

        return await self._http.get_followed_channels(
            user_id=self.id,
            token_for=token_for,
            broadcaster_id=broadcaster_id,
        )

    async def fetch_followers(self, token_for: str, user_id: str | int | None = None) -> ChannelFollowers:
        """
        Fetches information of who and when users followed this channel.

        !!! info
            The user ID in the token must match that of the broadcaster or a moderator.

        ??? note
            Requires user access token that includes the `moderator:read:followers` scope.

        Parameters
        -----------
        user_id: str | int | None
            Use this parameter to see whether the user follows this broadcaster.
        token_for: str
            User token to use that includes the `moderator:read:followers` scope.

        Returns
        -------
        twitchio.ChannelFollowers
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

        ??? note
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
            User token to use that includes the `channel:manage:redemptions` scope.

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

        ??? note
            Requires user access token that includes the `channel:read:redemptions` or `channel:manage:redemptions` scope.

        Parameters
        ----------
        token_for: str
            A user access token that includes the `channel:read:redemptions` or `channel:manage:redemptions` scope.
        ids: list[str] | None
            A list of IDs to filter the rewards by. You may request a maximum of 50.
        manageable: bool | None
            A Boolean value that determines whether the response contains only the custom rewards that the app (Client ID) may manage.
            Default is False.

        Returns
        -------
        list[twitchio.CustomReward]
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

        ??? note
            Requires user access token that includes the `channel:read:charity` scope.

        Parameters
        ----------
        token_for: str
            A user access token that includes the `channel:read:charity` scope.

        Returns
        -------
        twitchio.CharityCampaign
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

        ??? note
            Requires user access token that includes the `channel:read:charity` scope.

        Parameters
        -----------
        token_for: str
            A user access token that includes the `channel:read:charity` scope.
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

        ??? note
            Requires user access token that includes the `moderator:read:chatters` scope.

        Parameters
        ----------
        moderator_id: str | int
            The ID of the broadcaster or one of the broadcaster's moderators.
            This ID must match the user ID in the user access token.
        token_for: str
            A user access token that includes the `moderator:read:chatters` scope.
        first: int | None
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 1,000. The default is 100.

        Returns
        -------
        twitchio.Chatters
            A Chatters object containing the information of a broadcaster's connected chatters.
        """
        first = max(1, min(1000, first))

        return await self._http.get_chatters(
            token_for=token_for, first=first, broadcaster_id=self.id, moderator_id=moderator_id
        )

    async def fetch_channel_emotes(self, token_for: str | None = None) -> list[ChannelEmote]:
        """
        Fetches the broadcaster's list of custom emotes.
        Broadcasters create these custom emotes for users who subscribe to or follow the channel or cheer Bits in the channel's chat window.

        Parameters
        ----------
        token_for: str | None
            An optional user token to use instead of the default app token.

        Returns
        -------
        list[twitchio.ChannelEmote]
            A list of ChannelEmote objects
        """

        from twitchio.models.chat import ChannelEmote

        data = await self._http.get_channel_emotes(broadcaster_id=self.id, token_for=token_for)
        template = data["template"]
        return [ChannelEmote(d, template=template, http=self._http) for d in data["data"]]

    async def fetch_user_emotes(
        self, *, token_for: str, broadcaster_id: str | int | None = None
    ) -> HTTPAsyncIterator[UserEmote]:
        """
        Fetches the broadcaster's list of custom emotes.
        Broadcasters create these custom emotes for users who subscribe to or follow the channel or cheer Bits in the channel's chat window.

        ??? note
            Requires user access token that includes the `user:read:emotes` scope.

        Parameters
        ----------
        token_for: str
            Requires a user access token that includes the `user:read:emotes` scope.
        broadcaster_id: str | None
            The User ID of a broadcaster you wish to get follower emotes of. Using this query parameter will guarantee inclusion of the broadcaster's follower emotes in the response body.

        Returns
        -------
        HTTPAsyncIterator[twitchio.UserEmote]
        """

        return await self._http.get_user_emotes(user_id=self.id, token_for=token_for, broadcaster_id=broadcaster_id)

    async def fetch_chat_badges(self, token_for: str | None = None) -> list[ChatBadge]:
        """
        Fetches the broadcaster's list of custom chat badges.

        If you wish to fetch globally available chat badges use If you wish to fetch a specific broadcaster's chat badges use [`client.fetch_chat_badges`][twitchio.client.fetch_chat_badges]

        Parameters
        ----------
        token_for: str | None,
            An optional user token to use instead of the default app token.

        Returns
        --------
        list[twitchio.ChatBadge]
            A list of ChatBadge objects belonging to the user.
        """
        from .models.chat import ChatBadge

        data = await self._http.get_channel_chat_badges(broadcaster_id=self.id, token_for=token_for)
        return [ChatBadge(d, http=self._http) for d in data["data"]]

    async def fetch_chat_settings(
        self, *, moderator_id: str | int | None = None, token_for: str | None = None
    ) -> ChatSettings:
        """
        Fetches the broadcaster's chat settings.

        !!! note
            If you wish to view `non_moderator_chat_delay` and `non_moderator_chat_delay_duration` then you will need to provide a moderator_id, which can be
            either the broadcaster's or a moderators'. The token must include the `moderator:read:chat_settings` scope.
            the toke

        Parameters
        ----------
        moderator_id: str | int | None
            The ID of the broadcaster or one of the broadcaster's moderators.
            This field is required only if you want to include the `non_moderator_chat_delay` and `non_moderator_chat_delay_duration` settings in the response.
            If you specify this field, this ID must match the user ID in the user access token.

        token_for: str | None
            If you need the response to contain `non_moderator_chat_delay` and `non_moderator_chat_delay_duration` then you will provide a token for the user in `moderator_id`.
            The required scope is `moderator:read:chat_settings`.
            Otherwise it is an optional user token to use instead of the default app token.

        Returns
        -------
        twitchio.ChatSettings
            ChatSettings object of the broadcaster's chat settings.
        """
        from .models.chat import ChatSettings

        data = await self._http.get_channel_chat_settings(
            broadcaster_id=self.id, moderator_id=moderator_id, token_for=token_for
        )
        return ChatSettings(data["data"][0], http=self._http)

    async def update_chat_settings(
        self,
        moderator_id: str | int,
        token_for: str,
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
        """

        !!! info
            - To set the `slow_mode_wait_time` or `follower_mode_duration` field to its default value, set the corresponding `slow_mode` or `follower_mode` field to True (and don't include the `slow_mode_wait_time` or `follower_mode_duration` field).

            - To set the `slow_mode_wait_time`, `follower_mode_duration`, or `non_moderator_chat_delay_duration` field's value, you must set the corresponding `slow_mode`, `follower_mode`, or `non_moderator_chat_delay` field to True.

            - To remove the `slow_mode_wait_time`, `follower_mode_duration`, or `non_moderator_chat_delay_duration` field's value, set the corresponding `slow_mode`, `follower_mode`, or `non_moderator_chat_delay` field to False (and don't include the slow_mode_wait_time, follower_mode_duration, or non_moderator_chat_delay_duration field).

        ??? note
            Requires a user access token that includes the `moderator:manage:chat_settings` scope.

        Parameters
        ----------
        moderator_id: str | int
            The ID of a user that has permission to moderate the broadcaster's chat room, or the broadcaster's ID if they're making the update.
            This ID must match the user ID in the user access token.
        token_for: str
            User access token that includes the `moderator:manage:chat_settings` scope.
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
            moderator_id=moderator_id,
            token_for=token_for,
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

    async def send_announcement(
        self,
        *,
        moderator_id: str | int,
        token_for: str,
        message: str,
        color: Literal["blue", "green", "orange", "purple", "primary"] = "primary",
    ) -> None:
        """
        Sends an announcement to the broadcaster's chat room.

        ??? note
            Requires a user access token that includes the `moderator:manage:announcements` scope.

        Parameters
        ----------
        moderator_id: str | int
            The ID of a user who has permission to moderate the broadcaster's chat room, or the broadcaster''s ID if they're sending the announcement.
            This ID must match the user ID in the user access token.
        token_for: str
            User access token that includes the `moderator:manage:announcements` scope.
        message: str
            The announcement to make in the broadcaster's chat room. Announcements are limited to a maximum of 500 characters; announcements longer than 500 characters are truncated.
        color: Literal["blue", "green", "orange", "purple", "primary"]
            The color used to highlight the announcement. Possible case-sensitive values are: "blue", "green", "orange", "purple", "primary".
            Default is "primary".
        """
        return await self._http.post_chat_announcement(
            broadcaster_id=self.id, moderator_id=moderator_id, token_for=token_for, message=message, color=color
        )

    async def send_shoutout(
        self,
        *,
        to_broadcaster_id: str | int,
        moderator_id: str | int,
        token_for: str,
    ) -> None:
        """
        Sends a Shoutout to the specified broadcaster.

        !!! info
            `Rate Limits:` The broadcaster may send a Shoutout once every 2 minutes. They may send the same broadcaster a Shoutout once every 60 minutes.

        ??? note
            Requires a user access token that includes the `moderator:manage:shoutouts` scope.

        Parameters
        ----------
        to_broadcaster_id: str | int
            The ID of the broadcaster that's receiving the Shoutout.
        moderator_id: str | int
            The ID of the broadcaster or a user that is one of the broadcaster's moderators. This ID must match the user ID in the access token.
        token_for: str
            User access token that includes the `moderator:manage:shoutouts` scope.
        """
        return await self._http.post_chat_shoutout(
            broadcaster_id=self.id, moderator_id=moderator_id, token_for=token_for, to_broadcaster_id=to_broadcaster_id
        )

    # TODO App Token usage
    async def send_message(
        self, *, sender_id: str | int, message: str, token_for: str, reply_to_message_id: str | None = None
    ) -> SentMessage:
        """
        Send a message to the broadcaster's chat room.

        !!! note
            - Requires an app access token or user access token that includes the `user:write:chat` scope.
            User access token is generally recommended.

            - If app access token used, then additionally requires `user:bot scope` from chatting user, and either `channel:bot scope` from broadcaster or moderator status.

        ??? tip
            Chat messages can also include emoticons. To include emoticons, use the name of the emote.

            The names are case sensitive. Don't include colons around the name e.g., `:bleedPurple:`

            If Twitch recognizes the name, Twitch converts the name to the emote before writing the chat message to the chat room.

        Parameters
        ----------
        sender_id: str | int
            The ID of the user sending the message. This ID must match the user ID in the user access token.
        message: str
            The message to send. The message is limited to a maximum of 500 characters.
            Chat messages can also include emoticons. To include emoticons, use the name of the emote.
            The names are case sensitive. Don't include colons around the name e.g., `:bleedPurple:`.
            If Twitch recognizes the name, Twitch converts the name to the emote before writing the chat message to the chat room
        token_for: str
            User access token that includes the `user:write:chat` scope.
            You can use an app access token which additionally requires `user:bot scope` from chatting user, and either `channel:bot scope` from broadcaster or moderator status.
        reply_to_message_id: str | None
            The ID of the chat message being replied to.

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
            sender_id=sender_id,
            message=message,
            reply_to_message_id=reply_to_message_id,
            token_for=token_for,
        )

        return SentMessage(data["data"][0])

    async def update_chatter_color(self, *, color: str, token_for: str) -> None:
        """
        Updates the color used for the user's name in chat.

        ??? info
            Available colors:
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

        ??? note
            Requires a user access token that includes the `user:manage:chat_color` scope.

        Parameters
        ----------
        color: str
            The color to use, to see the list of colors available please refer to the docs.
            If the user is a Turbo or Prime member then you may specify a Hex color code e.g. `#9146FF`
        token_for: str
            User access token that includes the `user:manage:chat_color` scope.
        """
        return await self._http.put_user_chat_color(user_id=self.id, color=color, token_for=token_for)

    async def create_clip(self, *, token_for: str, has_delay: bool = False) -> CreatedClip:
        """
        Creates a clip from the broadcaster's stream.

        !!! info
            This API captures up to 90 seconds of the broadcaster's stream. The 90 seconds spans the point in the stream from when you called the API.
            For example, if you call the API at the 4:00 minute mark, the API captures from approximately the 3:35 mark to approximately the 4:05 minute mark.
            Twitch tries its best to capture 90 seconds of the stream, but the actual length may be less.
            This may occur if you begin capturing the clip near the beginning or end of the stream.

            By default, Twitch publishes up to the last 30 seconds of the 90 seconds window and provides a default title for the clip.
            To specify the title and the portion of the 90 seconds window that's used for the clip, use the URL in the CreatedClip's `edit_url` attribute.
            You can specify a clip that's from 5 seconds to 60 seconds in length. The URL is valid for up to 24 hours or until the clip is published, whichever comes first.

            Creating a clip is an asynchronous process that can take a short amount of time to complete.
            To determine whether the clip was successfully created, call [`fetch_clips`][twitchio.user.PartialUser.fetch_clips] using the clip ID that this request returned.
            If [`fetch_clips`][twitchio.user.PartialUser.fetch_clips] returns the clip, the clip was successfully created. If after 15 seconds [`fetch_clips`][twitchio.user.PartialUser.fetch_clips] hasn't returned the clip, assume it failed.

        ??? note
            Requires a user access token that includes the `clips:edit` scope.

        Parameters
        ----------
        has_delay: bool
            A Boolean value that determines whether the API captures the clip at the moment the viewer requests it or after a delay.
            If False (default), Twitch captures the clip at the moment the viewer requests it (this is the same clip experience as the Twitch UX).
            If True, Twitch adds a delay before capturing the clip (this basically shifts the capture window to the right slightly).
        token_for: str
            User access token that includes the `clips:edit` scope.

        Returns
        -------
        CreatedClip
            The CreatedClip object.
        """
        from .models.clips import CreatedClip

        data = await self._http.post_create_clip(broadcaster_id=self.id, token_for=token_for, has_delay=has_delay)
        return CreatedClip(data["data"][0])

    async def fetch_clips(
        self,
        *,
        started_at: datetime.datetime | None = None,
        ended_at: datetime.datetime | None = None,
        featured: bool | None = None,
        token_for: str | None = None,
        first: int = 20,
    ) -> HTTPAsyncIterator[Clip]:
        """
        Fetches clips from the broadcaster's streams.

        Parameters
        -----------
        started_at: datetime.datetime
            The start date used to filter clips.
        ended_at: datetime.datetime
            The end date used to filter clips. If not specified, the time window is the start date plus one week.
        featured: bool | None = None
            If True, returns only clips that are featured.
            If False, returns only clips that aren't featured.
            All clips are returned if this parameter is not provided.
        token_for: str | None
            An optional user token to use instead of the default app token.
        first: int
            Maximum number of items to return per page. Default is 20.
            Min is 1 and Max is 100.

        Returns
        --------
        twitchio.HTTPAsyncIterator[twitchio.Clip]
        """

        first = max(1, min(100, first))

        return await self._http.get_clips(
            broadcaster_id=self.id,
            first=first,
            started_at=started_at,
            ended_at=ended_at,
            is_featured=featured,
            token_for=token_for,
        )

    async def fetch_goals(self, *, token_for: str) -> list[Goal]:
        """
        Fetches a list of the creator's goals.

        ??? note
            Requires a user access token that includes the `channel:read:goals` scope.

        Parameters
        ----------
        token_for : str
            User access token that includes the `channel:read:goals` scope.

        Returns
        -------
        list[Goal]
            List of Goal objects.
        """
        from .models.goals import Goal

        data = await self._http.get_creator_goals(broadcaster_id=self.id, token_for=token_for)
        return [Goal(d, http=self._http) for d in data["data"]]

    async def fetch_hype_train_events(self, *, token_for: str, first: int = 1) -> HTTPAsyncIterator[HypeTrainEvent]:
        """
        Fetches information about the broadcaster's current or most recent Hype Train event.

        Parameters
        ----------
        token_for : str
            User access token that includes the channel:read:hype_train scope.
        first : int
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100 items per page. The default is 1.

        Returns
        -------
        HTTPAsyncIterator[HypeTrainEvent]
            HTTPAsyncIterator of HypeTrainEvent objects.
        """
        first = max(1, min(100, first))

        return await self._http.get_hype_train_events(broadcaster_id=self.id, first=first, token_for=token_for)

    async def start_raid(self, *, to_broadcaster_id: str | int, token_for: str) -> Raid:
        """
        Starts a raid to another channel.

        `Rate Limit:` The limit is 10 requests within a 10-minute window.

        ??? info
            When you call the API from a chat bot or extension, the Twitch UX pops up a window at the top of the chat room that identifies the number of viewers in the raid. The raid occurs when the broadcaster clicks Raid Now or after the 90-second countdown expires.

            To determine whether the raid successfully occurred, you must subscribe to the Channel Raid event.

            To cancel a pending raid, use the Cancel a raid endpoint.

        ??? note
            Requires a user access token that includes the `channel:manage:raids` scope.

        Parameters
        ----------
        to_broadcaster_id : str | int
            The ID of the broadcaster to raid.
        token_for : str
            User access token that includes the `channel:manage:raids` scope.

        Returns
        -------
        Raid
            Raid object.
        """
        data = await self._http.post_raid(
            from_broadcaster_id=self.id, to_broadcaster_id=to_broadcaster_id, token_for=token_for
        )

        return Raid(data["data"][0])

    async def cancel_raid(self, *, token_for: str) -> None:
        return await self._http.delete_raid(broadcaster_id=self.id, token_for=token_for)

    async def fetch_channel_teams(self, *, token_for: str | None = None) -> list[ChannelTeam]:
        """
        Fetches the list of Twitch teams that the broadcaster is a member of.

        Parameters
        ----------
        token_for : str | None, optional
            An optional user token to use instead of the default app token.
        Returns
        -------
        list[ChannelTeam]
            List of ChannelTeam objects.
        """
        from .models.teams import ChannelTeam

        data = await self._http.get_channel_teams(broadcaster_id=self.id, token_for=token_for)

        return [ChannelTeam(d, http=self._http) for d in data["data"]]
