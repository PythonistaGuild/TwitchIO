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

    from .http import HTTPAsyncIterator, HTTPClient
    from .models.analytics import ExtensionAnalytics, GameAnalytics
    from .models.channel_points import CustomReward
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

    async def start_commercial(self, length: int, token_for: str) -> CommercialStart:
        """
        Starts a commercial on the specified channel.

        !!! info
            Only partners and affiliates may run commercials and they must be streaming live at the time.

        !!! info
            Only the broadcaster may start a commercial; the broadcaster's editors and moderators may not start commercials on behalf of the broadcaster.

        !! note
            Requires a user access token that includes the ``channel:edit:commercial`` scope.

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
            Requires a user access token that includes the ``channel:read:ads`` scope.

        Parameters
        ----------
        token_for : str
            User OAuth token to use that includes the ``channel:edit:commercial`` scope.

        Returns
        -------
        twitchio.AdSchedule
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
            Requires a user access token that includes the ``channel:manage:ads`` scope.

        Parameters
        ----------
        token_for : str
            User OAuth token to use that includes the ``channel:manage:ads`` scope.

        Returns
        -------
        twitchio.SnoozeAd
        """
        data = await self._http.get_ad_schedule(broadcaster_id=self.id, token_for=token_for)
        return SnoozeAd(data["data"][0])

    async def fetch_custom_rewards(
        self, *, token_for: str, ids: list[str] | None = None, manageable: bool = False
    ) -> list[CustomReward]:
        from .models.channel_points import CustomReward

        data = await self._http.get_custom_reward(
            broadcaster_id=self.id, reward_ids=ids, manageable=manageable, token_for=token_for
        )
        return [CustomReward(d, http=self._http) for d in data["data"]]

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
            Requires a user access token that includes the channel:manage:redemptions scope.

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

    async def fetch_charity_campaign(self, *, token_for: str) -> CharityCampaign:
        """
        Fetch the active charity campaign of a broadcaster.

        !!! note
            Requires a user access token that includes the ``channel:read:charity`` scope.

        Parameters
        ----------
        token_for : str
            A user access token that includes the ``channel:read:charity`` scope.

        Returns
        -------
        CharityCampaign
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
            Requires a user access token that includes the ``channel:read:charity`` scope.

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
            Requires a user access token that includes the ``analytics:read:extensions`` scope.

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
            Requires a user access token that includes the ``analytics:read:extensions`` scope.

        Parameters
        -----------
        token_for: str
            A user access token that includes the ``analytics:read:extensions`` scope.
        extension_id: str
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
