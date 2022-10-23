"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

import datetime
import time
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Tuple, TypedDict, Union

from .channel import Channel
from .enums import BroadcasterTypeEnum, ModEventEnum, UserTypeEnum
from .http import HTTPAwaitableAsyncIterator, HTTPAwaitableAsyncIteratorWithSource
from .rewards import CustomReward
from .utils import parse_timestamp

if TYPE_CHECKING:
    from .http import HTTPHandler
    from .models import BitsLeaderboard, Clip, ExtensionBuilder, FollowEvent, Prediction, Tag
    from .types.extensions import Extension as ExtensionType, ExtensionBuilder as ExtensionBuilderType


__all__ = (
    "PartialUser",
    "BitLeaderboardUser",
    "UserBan",
    "SearchUser",
    "User",
    "BitsLeaderboard",
    "Clip",
    "CheerEmote",
    "CheerEmoteTier",
    "HypeTrainContribution",
    "HypeTrainEvent",
    "BanEvent",
    "FollowEvent",
    "SubscriptionEvent",
    "Marker",
    "VideoMarkers",
    "Game",
    "ModEvent",
    "AutomodCheckMessage",
    "AutomodCheckResponse",
    "Extension",
    "MaybeActiveExtension",
    "ActiveExtension",
    "ExtensionBuilder",
    "Video",
    "Tag",
    "WebhookSubscription",
    "Prediction",
    "Predictor",
    "PredictionOutcome",
    "Schedule",
    "ScheduleSegment",
    "ScheduleCategory",
    "ScheduleVacation",
    "Stream",
    "Team",
    "ChannelTeams",
    "ChannelInfo",
    "Poll",
    "PollChoice",
    "Goal",
    "ChatSettings",
    "ChatterColor",
    "Raid",
)


class ActiveExtensionType(TypedDict):
    panels: Dict[int, ActiveExtension]
    overlay: Dict[int, ActiveExtension]
    component: Dict[int, ActiveExtension]


class PartialUser:
    """
    A minimal representation of a user on twitch.

    Attributes
    -----------
    id: :class:`int`
        The id of the user.
    name: Optional[:class:`str`]
        The name of the user (this corresponds to the ``login`` field of the API)
    """

    __slots__ = "id", "name", "_http", "_cached_rewards"

    def __init__(self, http: HTTPHandler, id: Union[int, str], name: Optional[str]):
        self.id: int = int(id)
        self.name: Optional[str] = name
        self._http: HTTPHandler = http

        self._cached_rewards: Optional[Tuple[float, List[CustomReward]]] = None

    def __repr__(self) -> str:
        return f"<PartialUser id={self.id}, name={self.name}>"

    @property
    def channel(self) -> Optional[Channel]:
        """
        Returns the :class:`~twitchio.Channel` associated with this user. Could be ``None`` if you are not part of the channel's chat

        Returns
        --------
        Optional[:class:`~twitchio.Channel`]
        """

        if self.name in self._http.client._connection._cache:
            return Channel(name=self.name, websocket=self._http.client._connection)

    async def fetch(self) -> User:
        """|coro|

        Fetches the full user from the api

        Returns
        --------
        :class:`User` The full user associated with this :class:`PartialUser`
        """
        if not self._http.client:
            raise RuntimeError("No client attached to underlying HTTP session")

        return await self._http.client.fetch_user(id=self.id, target=self)

    async def edit(self, description: str) -> None:
        """|coro|

        Edits a channels description

        Parameters
        -----------
        description: :class:`str`
            The new description for the user
        """
        await self._http.put_update_user(self, description)

    async def fetch_tags(self) -> List[Tag]:
        """|coro|

        Fetches tags the user currently has active.

        Returns
        --------
            List[:class:`Tag`]
        """
        data = await self._http.get_channel_tags(str(self.id))
        return [Tag(self._http, x) for x in data["data"]]

    async def replace_tags(self, tags: List[Union[str, Tag]]) -> None:
        """|coro|

        Replaces the channels active tags. Tags expire 72 hours after being applied,
        unless the stream is live during that time period.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the user:edit:broadcast scope
        tags: List[Union[:class:`Tag`, :class:`str`]]
            A list of :class:`Tag` or tag ids to put on the channel. Max 100
        """
        tags_ = [x if isinstance(x, str) else x.id for x in tags]
        await self._http.put_replace_channel_tags(self, str(self.id), tags_)

    async def get_custom_rewards(
        self, *, only_manageable=False, ids: Optional[List[int]] = None, force=False
    ) -> HTTPAwaitableAsyncIterator[CustomReward]:
        """|coro|

        Fetches the channels custom rewards (aka channel points) from the api.

        Parameters
        ----------
        only_manageable: :class:`bool`
            Whether to fetch all rewards or only ones you can manage. Defaults to false.
        ids: List[:class:`int`]
            An optional list of reward ids
        force: :class:`bool`
            Whether to force a fetch or try to get from cache. Defaults to False

        Returns
        -------
        List[:class:`~twitchio.CustomReward`]
        """
        if not force and self._cached_rewards and self._cached_rewards[0] + 300 > time.monotonic():
            return HTTPAwaitableAsyncIteratorWithSource(self._cached_rewards[1])

        self._cached_rewards = (time.monotonic(), [])

        def adapter(handler: HTTPHandler, data) -> CustomReward:
            resp = CustomReward(handler, data, self)
            self._cached_rewards[1].append(resp)  # type: ignore
            return resp

        data: HTTPAwaitableAsyncIterator[CustomReward] = self._http.get_rewards(self, self.id, only_manageable, ids)
        data.set_adapter(adapter)
        return data

    async def fetch_bits_leaderboard(
        self,
        period: Literal["all", "day", "week", "month", "year"] = "all",
        user_id: Optional[int] = None,
        started_at: Optional[datetime.datetime] = None,
    ) -> BitsLeaderboard:
        """|coro|

        Fetches the bits leaderboard for the channel. This requires an OAuth token with the bits:read scope.

        Parameters
        -----------
        period: Optional[:class:`str`]
            one of `day`, `week`, `month`, `year`, or `all`, defaults to `all`
        started_at: Optional[:class:`datetime.datetime`]
            the timestamp to start the period at. This is ignored if the period is `all`
        user_id: Optional[:class:`int`]
            the id of the user to fetch for
        """

        data = await self._http.get_bits_board(self, period, user_id, started_at)
        return BitsLeaderboard(self._http, data)

    async def start_commercial(self, length: Literal[30, 60, 90, 120, 150, 180]) -> dict:
        """|coro|

        Starts a commercial on the channel. Requires an OAuth token with the `channel:edit:commercial` scope.

        Parameters
        -----------
        length: :class:`int`
            the length of the commercial. Should be one of `30`, `60`, `90`, `120`, `150`, `180`

        Returns
        --------
        :class:`dict` a dictionary with `length`, `message`, and `retry_after`
        """
        data = await self._http.post_commercial(self, str(self.id), length)
        return data

    async def create_clip(self, has_delay=False) -> dict:
        """|coro|

        Creates a clip on the channel. Note that clips are not created instantly, so you will have to query
        :meth:`~get_clips` to confirm the clip was created. Requires an OAuth token with the `clips:edit` scope

        Parameters
        -----------
        has_delay: :class:`bool`
            Whether the clip should have a delay to match that of a viewer. Defaults to False

        Returns
        --------
        :class:`dict` a dictionary with `id` and `edit_url`
        """
        data = await self._http.post_create_clip(self, self.id, has_delay)
        return data["data"][0]

    def fetch_clips(self) -> HTTPAwaitableAsyncIterator[Clip]:
        """|coro|

        Fetches clips from the api. This will only return clips from the specified user.
        Use :class:`Client.fetch_clips` to fetch clips by id

        Returns
        --------
        List[:class:`twitchio.Clip`]
        """

        iterator: HTTPAwaitableAsyncIterator[Clip] = self._http.get_clips(self.id)
        iterator.set_adapter(lambda handler, data: Clip(handler, data))

        return iterator

    def fetch_hypetrain_events(self, id: Optional[str] = None) -> HTTPAwaitableAsyncIterator[HypeTrainEvent]:
        """|coro|

        Fetches hypetrain event from the api. Needs a token with the channel:read:hype_train scope.

        Parameters
        -----------
        id: Optional[:class:`str`]
            The hypetrain id, if known, to fetch for

        Returns
        --------
            List[:class:`twitchio.HypeTrainEvent`]
            A list of hypetrain events
        """
        iterator: HTTPAwaitableAsyncIterator[HypeTrainEvent] = self._http.get_hype_train(str(self.id), id=id)
        iterator.set_adapter(lambda handler, data: HypeTrainEvent(handler, data))
        return iterator

    def fetch_bans(self, userids: Optional[List[Union[str, int]]] = None) -> HTTPAwaitableAsyncIterator[UserBan]:
        """|coro|

        Fetches a list of people the User has banned from their channel. Requires an OAuth token with the ``moderation:read`` scope.

        Parameters
        -----------
        userids: List[Union[:class:`str`, :class:`int`]]
            An optional list of userids to fetch. Will fetch all bans if this is not passed

        Returns
        --------
        List[:class:`UserBan`]
        """
        iterator: HTTPAwaitableAsyncIterator[UserBan] = self._http.get_channel_bans(
            self, str(self.id), user_ids=userids
        )
        iterator.set_adapter(lambda handler, data: UserBan(handler, data))
        return iterator

    def fetch_ban_events(self, userids: Optional[List[int]] = None) -> HTTPAwaitableAsyncIterator[BanEvent]:
        """|coro|

        Fetches ban/unban events from the User's channel. Requires an OAuth token with the ``moderation:read`` scope.

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the moderation:read scope.
        userids: List[:class:`int`]
            An optional list of users to fetch ban/unban events for

        Returns
        --------
            List[:class:`BanEvent`]
        """

        iterator: HTTPAwaitableAsyncIterator[BanEvent] = self._http.get_channel_ban_unban_events(
            self, str(self.id), userids
        )
        iterator.set_adapter(lambda handler, data: BanEvent(handler, data, self))
        return iterator

    def fetch_moderators(self, userids: Optional[List[int]] = None) -> HTTPAwaitableAsyncIterator[PartialUser]:
        """|coro|

        Fetches the moderators for this channel. Requires an OAuth token with the ``moderation:read`` scope.

        Parameters
        -----------
        userids: List[:class:`int`]
            An optional list of users to check mod status of

        Returns
        --------
            List[:class:`twitchio.PartialUser`]
        """
        iterator: HTTPAwaitableAsyncIterator[PartialUser] = self._http.get_channel_moderators(
            self, str(self.id), user_ids=userids
        )
        iterator.set_adapter(lambda handler, data: PartialUser(handler, data["user_id"], data["user_name"]))
        return iterator

    def fetch_mod_events(self) -> HTTPAwaitableAsyncIterator[ModEvent]:
        """|coro|

        Fetches mod events (moderators being added and removed) for this channel. Requires an OAuth token with the ``moderation:read`` scope.

        Returns
        --------
            List[:class:`twitchio.ModEvent`]
        """
        iterator: HTTPAwaitableAsyncIterator[ModEvent] = self._http.get_channel_mod_events(self, str(self.id))
        iterator.set_adapter(lambda handler, data: ModEvent(handler, data, self))
        return iterator

    async def automod_check(self, query: List[AutomodCheckMessage]) -> List[AutomodCheckResponse]:
        """|coro|

        Checks if a string passes the automod filter. Requires an OAuth token with the ``moderation:read`` scope.

        Parameters
        -----------
        query: List[:class:`AutomodCheckMessage`]
            A list of :class:`AutomodCheckMessage`

        Returns
        --------
            List[:class:`AutomodCheckResponse`]
        """
        data = await self._http.post_automod_check(self, str(self.id), [x._to_dict() for x in query])
        return [AutomodCheckResponse(d) for d in data["data"]]

    async def fetch_stream_key(self) -> str:
        """|coro|

        Fetches the users stream key. Requires an OAuth token with the ``channel:read:stream_key`` scope.

        Returns
        --------
            :class:`str`
        """
        data = await self._http.get_stream_key(self, str(self.id))
        return data  # FIXME what does this payload look like

    def fetch_following(self) -> HTTPAwaitableAsyncIterator[FollowEvent]:
        """|coro|

        Fetches a list of users that this user is following.

        Returns
        --------
            List[:class:`FollowEvent`]
        """
        iterator = self._http.get_user_follows(target=self, from_id=str(self.id))
        iterator.set_adapter(lambda handler, data: FollowEvent(handler, data, self))
        return iterator

    def fetch_followers(self) -> HTTPAwaitableAsyncIterator[FollowEvent]:
        """|coro|

        Fetches a list of users that are following this user.

        Returns
        --------
            List[:class:`FollowEvent`]
        """
        iterator = self._http.get_user_follows(to_id=str(self.id))
        iterator.set_adapter(lambda handler, data: FollowEvent(handler, data, self))
        return iterator

    async def fetch_follow(self, to_user: PartialUser) -> Optional[FollowEvent]:
        """|coro|

        Check if a user follows another user or when they followed a user.

        Parameters
        -----------
        to_user: :class:`PartialUser`
            The user to check for a follow to. (self -> to_user)

        Returns
        --------
            :class:`FollowEvent`
        """
        if not isinstance(to_user, PartialUser):
            raise TypeError(f"to_user must be a PartialUser not {type(to_user)}")

        iterator: HTTPAwaitableAsyncIterator[FollowEvent] = self._http.get_user_follows(
            from_id=str(self.id), to_id=str(to_user.id)
        )
        iterator.set_adapter(lambda handler, data: FollowEvent(handler, data, self))
        data = await iterator
        return data[0] if data else None

    async def follow(self, target: Union[User, PartialUser], *, notifications=False) -> None:
        """|coro|

        Follows the target user. Requires an OAuth token with the ``user:edit:follows`` scope.

        Parameters
        -----------
        target: Union[:class:`User`, :class:`PartialUser`]
            The user to follow
        notifications: :class:`bool`
            Whether to allow push notifications when the target user goes live. Defaults to False

        Returns
            ``None``
        """
        await self._http.post_follow_channel(
            self, from_id=str(self.id), to_id=str(target.id), notifications=notifications
        )

    async def unfollow(self, target: Union[User, PartialUser]) -> None:
        """|coro|

        Unfollows the target user. Requires an OAuth token with the ``user:edit:follows`` scope.

        Parameters
        -----------
        target: Union[:class:`User`, :class:`PartialUser`]
            The user to unfollow

        Returns
            ``None``
        """
        await self._http.delete_unfollow_channel(self, to_id=str(target.id), from_id=str(self.id))

    async def fetch_subscriptions(
        self, userids: Optional[List[int]] = None
    ) -> HTTPAwaitableAsyncIterator[SubscriptionEvent]:
        """|coro|

        Fetches the subscriptions for this channel.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the channel:read:subscriptions scope
        userids: Optional[List[:class:`int`]]
            An optional list of userids to look for

        Returns
        --------
            List[:class:`twitchio.SubscriptionEvent`]
        """
        iterator: HTTPAwaitableAsyncIterator[SubscriptionEvent] = self._http.get_channel_subscriptions(
            self, str(self.id), user_ids=[str(x) for x in (userids or ())]
        )
        iterator.set_adapter(lambda handler, data: SubscriptionEvent(handler, data, self))
        return iterator

    async def create_marker(self, description: Optional[str] = None) -> Marker:
        """|coro|

        Creates a marker on the stream. This only works if the channel is live (among other conditions).
        Requires an OAuth token with the ``user:edit:broadcast`` scope.

        Parameters
        -----------
        description: :class:`str`
            An optional description of the marker

        Returns
        --------
            :class:`Marker`
        """
        data = await self._http.post_stream_marker(self, user_id=str(self.id), description=description)
        return Marker(data["data"][0])

    async def fetch_markers(self, video_id: Optional[str] = None) -> Optional[VideoMarkers]:
        """|coro|

        Fetches markers from the given video id, or the most recent video.
        The Twitch api will only return markers created by the user of the authorized token.
        Requires an OAuth token with the ``user:edit:broadcast`` scope.

        Parameters
        -----------
        video_id: :class:`str`
            A specific video o fetch from. Defaults to the most recent stream if not passed

        Returns
        --------
            Optional[:class:`twitchio.VideoMarkers`]
        """
        data = await self._http.get_stream_markers(self, user_id=str(self.id), video_id=video_id)
        if data:
            return VideoMarkers(data[0]["videos"])

    async def fetch_extensions(self) -> List[Extension]:
        """|coro|

        Fetches extensions the user has (active and inactive). Requires an OAuth token with the ``user:read:broadcast`` scope.

        Returns
        --------
            List[:class:`Extension`]
        """
        data = await self._http.get_channel_extensions(self)
        return [Extension(d) for d in data["data"]]

    async def fetch_active_extensions(self) -> ActiveExtensionType:
        """|coro|

        Fetches active extensions the user has.
        Returns a dictionary containing the following keys: `panel`, `overlay`, `component`.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token with the user:read:broadcast *or* user:edit:broadcast scope

        Returns
        --------
            Dict[Literal["panel", "overlay", "component"], Dict[:class:`int`, :class:`ActiveExtension`]]
        """
        data = await self._http.get_user_active_extensions(self, str(self.id))
        return {typ: {int(n): ActiveExtension(d) for n, d in vals.items()} for typ, vals in data.items()}  # type: ignore

    async def update_extensions(self, extensions: ExtensionBuilder) -> ActiveExtensionType:
        """|coro|

        Updates a users extensions. See the :class:`ExtensionBuilder` for information on how to use it

        Parameters
        -----------
        token: :class:`str`
            An oauth token with user:edit:broadcast scope
        extensions: :class:`twitchio.ExtensionBuilder`
            A :class:`twitchio.ExtensionBuilder` to be given to the twitch api

        Returns
        --------
            Dict[:class:`str`, Dict[:class:`int`, :class:`twitchio.ActiveExtension`]]
        """
        data = await self._http.put_user_extensions(self, extensions._to_dict())
        return {typ: {int(n): ActiveExtension(d) for n, d in vals.items()} for typ, vals in data.items()}  # type: ignore

    def fetch_videos(
        self,
        period: Literal["all", "day", "week", "month"] = "all",
        sort: Literal["time", "trending", "views"] = "time",
        type: Literal["upload", "archive", "highlight", "all"] = "all",
        language=None,
    ) -> HTTPAwaitableAsyncIterator[Video]:
        """|coro|

        Fetches videos that belong to the user. If you have specific video ids use :func:`~twitchio.Client.fetch_videos`

        Parameters
        -----------
        period: :class:`str`
            The period for which to fetch videos. Valid values are `all`, `day`, `week`, `month`. Defaults to `all`
        sort: :class:`str`
            Sort orders of the videos. Valid values are `time`, `trending`, `views`, Defaults to `time`
        type: Optional[:class:`str`]
            Type of the videos to fetch. Valid values are `upload`, `archive`, `highlight`, `all`. Defaults to `all`
        language: Optional[:class:`str`]
            Language of the videos to fetch. Must be an `ISO-639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ two letter code.

        Returns
        --------
            List[:class:`twitchio.Video`]
        """
        iterator: HTTPAwaitableAsyncIterator[Video] = self._http.get_videos(
            user_id=str(self.id), period=period, sort=sort, type=type, language=language
        )
        iterator.set_adapter(lambda handler, data: Video(handler, data, self))
        return iterator

    async def end_prediction(
        self, prediction_id: str, status: str, winning_outcome_id: Optional[str] = None
    ) -> Prediction:
        """|coro|

        End a prediction with an outcome. Requires an OAuth token with the ``channel:manage:prediction`` scope.

        Parameters
        -----------
        prediction_id: :class:`str`
            ID of the prediction to end.
        status: :class:`str`
            TODO what this
        winning_outcome_id: Optional[:class:`str`]
            The outcome id. # TODO wth is this

        Returns
        --------
            :class:`Prediction`
        """
        data = await self._http.patch_prediction(
            self,
            broadcaster_id=str(self.id),
            prediction_id=prediction_id,
            status=status,
            winning_outcome_id=winning_outcome_id,
        )
        return Prediction(self._http, data[0])

    async def get_predictions(self, prediction_id: Optional[str] = None) -> List[Prediction]:
        """|coro|

        Gets information on a prediction or the list of predictions if none is provided.

        Parameters
        -----------
        prediction_id: :class:`str`
            ID of the prediction to receive information about.

        Returns
        --------
            List[:class:`Prediction`]
        """

        data = await self._http.get_predictions(self, broadcaster_id=self.id, prediction_id=prediction_id)
        return [Prediction(self._http, d) for d in data]

    async def create_prediction(
        self, title: str, blue_outcome: str, pink_outcome: str, prediction_window: int
    ) -> Prediction:
        """|coro|

        Creates a prediction for the channel.

        Parameters
        -----------
        title: :class:`str`
            Title for the prediction (max of 45 characters)
        blue_outcome: :class:`str`
            Text for the first outcome people can vote for. (max 25 characters)
        pink_outcome: :class:`str`
            Text for the second outcome people can vote for. (max 25 characters)
        prediction_window: :class:`int`
            Total duration for the prediction (in seconds)

        Returns
        --------
            :class:`twitchio.Prediction`
        """

        data = await self._http.post_prediction(
            self,
            broadcaster_id=self.id,
            title=title,
            blue_outcome=blue_outcome,
            pink_outcome=pink_outcome,
            prediction_window=prediction_window,
        )
        return Prediction(self._http, data[0])

    async def modify_stream(
        self, token: str, game_id: Optional[int] = None, language: Optional[str] = None, title: Optional[str] = None
    ):
        """|coro|

        Modify stream information

        Parameters
        -----------
        game_id: :class:`int`
            Optional game ID being played on the channel. Use 0 to unset the game.
        language: :class:`str`
            Optional language of the channel. A language value must be either the ISO 639-1 two-letter code for a supported stream language or “other”.
        title: :class:`str`
            Optional title of the stream.
        """
        gid = None
        if game_id is not None:
            gid = str(game_id)

        await self._http.patch_channel(
            self,
            broadcaster_id=str(self.id),
            game_id=gid,
            language=language,
            title=title,
        )

    async def fetch_schedule(
        self,
        segment_ids: Optional[List[str]] = None,
        start_time: Optional[datetime.datetime] = None,
        utc_offset: Optional[int] = None,
        first: int = 20,
    ):
        """|coro|

        Fetches the schedule of a streamer
        Parameters
        -----------
        segment_ids: Optional[List[:class:`str`]]
            List of segment IDs of the stream schedule to return. Maximum: 100
        start_time: Optional[:class:`datetime.datetime`]
            A datetime object to start returning stream segments from. If not specified, the current date and time is used.
        utc_offset: Optional[:class:`int`]
            A timezone offset for the requester specified in minutes. +4 hours from GMT would be `240`
        first: Optional[:class:`int`]
            Maximum number of stream segments to return. Maximum: 25. Default: 20.

        Returns
        --------
            :class:`twitchio.Schedule`
        """

        data = await self._http.get_channel_schedule(
            broadcaster_id=str(self.id),
            segment_ids=segment_ids,
            start_time=start_time,
            utc_offset=utc_offset,
            first=first,
        )
        return Schedule(self._http, data)

    async def fetch_channel_teams(self):
        """|coro|

        Fetches a list of Twitch Teams of which the specified channel/broadcaster is a member.

        Returns
        --------
        List[:class:`twitchio.ChannelTeams`]
        """

        data = await self._http.get_channel_teams(
            broadcaster_id=str(self.id),
        )

        return [ChannelTeams(self._http, x) for x in data]

    def fetch_polls(self, poll_ids: Optional[List[str]] = None, first: Optional[int] = 20) -> HTTPAwaitableAsyncIterator[Poll]:
        """|coro|

        Fetches a list of polls for the specified channel/broadcaster.

        Parameters
        -----------
        poll_ids: Optional[List[:class:`str`]]
            List of poll IDs to return. Maximum: 100
        first: Optional[:class:`int`]
            Number of polls to return. Maximum: 20. Default: 20.

        Returns
        --------
        List[:class:`twitchio.Poll`]
        """

        data: HTTPAwaitableAsyncIterator[Poll] = self._http.get_polls(broadcaster_id=str(self.id), target=self, poll_ids=poll_ids, first=first)
        data.set_adapter(lambda handler, data: Poll(handler, data))
        return data

    async def create_poll(
        self,
        title: str,
        choices: List[str],
        duration: int,
        bits_voting_enabled: Optional[bool] = False,
        bits_per_vote: Optional[int] = None,
        channel_points_voting_enabled: Optional[bool] = False,
        channel_points_per_vote: Optional[int] = None,
    ):
        """|coro|

        Creates a poll for the specified channel/broadcaster.

        Parameters
        -----------
        title: :class:`str`
            Question displayed for the poll.
        choices: List[:class:`str`]
            List of choices for the poll. Must be between 2 and 5 choices.
        duration: :class:`int`
            Total duration for the poll in seconds. Must be between 15 and 1800.
        bits_voting_enabled: Optional[:class:`bool`]
            Indicates if Bits can be used for voting. Default is False.
        bits_per_vote: Optional[:class:`int`]
            Number of Bits required to vote once with Bits. Max 10000.
        channel_points_voting_enabled: Optional[:class:`bool`]
            Indicates if Channel Points can be used for voting. Default is False.
        channel_points_per_vote: Optional[:class:`int`]
            Number of Channel Points required to vote once with Channel Points. Max 1000000.

        Returns
        --------
        List[:class:`twitchio.Poll`]
        """

        data = await self._http.post_poll(
            broadcaster_id=str(self.id),
            target=self,
            title=title,
            choices=choices,
            duration=duration,
            bits_voting_enabled=bits_voting_enabled,
            bits_per_vote=bits_per_vote,
            channel_points_voting_enabled=channel_points_voting_enabled,
            channel_points_per_vote=channel_points_per_vote,
        )
        return Poll(self._http, data[0])

    async def end_poll(self, poll_id: str, status: Literal["TERMINATED", "ARCHIVED"]):
        """|coro|

        Ends a poll for the specified channel/broadcaster.

        Parameters
        -----------
        poll_id: :class:`str`
            ID of the poll.
        status: Literal["TERMINATED", "ARCHIVED"]
            The poll status to be set. Valid values:
            TERMINATED: End the poll manually, but allow it to be viewed publicly.
            ARCHIVED: End the poll manually and do not allow it to be viewed publicly.

        Returns
        --------
        :class:`twitchio.Poll`
        """

        data = await self._http.patch_poll(broadcaster_id=str(self.id), target=self, id=poll_id, status=status)
        return Poll(self._http, data[0])


class BitLeaderboardUser(PartialUser):

    __slots__ = "rank", "score"

    def __init__(self, http: HTTPHandler, data: dict):
        super(BitLeaderboardUser, self).__init__(http, id=data["user_id"], name=data["user_name"])
        self.rank: int = data["rank"]
        self.score: int = data["score"]


class UserBan(PartialUser):  # TODO will probably rework this
    """
    Represents a banned user or one in timeout.

    Attributes
    ----------
    id: :class:`int`
        The ID of the banned user.
    name: :class:`str`
        The name of the banned user.
    created_at: :class:`datetime.datetime`
        The date and time the ban was created.
    expires_at: Optional[:class:`datetime.datetime`]
        The date and time the timeout will expire.
        Is None if it's a ban.
    reason: :class:`str`
        The reason for the ban/timeout.
    moderator: :class:`~twitchio.PartialUser`
        The moderator that banned the user.
    """

    __slots__ = ("created_at", "expires_at", "reason", "moderator")

    def __init__(self, http: HTTPHandler, data: dict):
        super(UserBan, self).__init__(http, id=data["user_id"], name=data["user_login"])
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.expires_at: Optional[datetime.datetime] = (
            parse_timestamp(data["expires_at"]) if data["expires_at"] else None
        )
        self.reason: str = data["reason"]
        self.moderator = PartialUser(http, id=data["moderator_id"], name=data["moderator_login"])

    def __repr__(self):
        return f"<UserBan {super().__repr__()} created_at={self.created_at} expires_at={self.expires_at} reason={self.reason}>"


class SearchUser(PartialUser):

    __slots__ = "game_id", "name", "display_name", "language", "title", "thumbnail_url", "live", "started_at", "tag_ids"

    def __init__(self, http: HTTPHandler, data: dict):
        self._http = http
        self.display_name: str = data["display_name"]
        self.name: str = data["broadcaster_login"]
        self.id: int = int(data["id"])
        self.game_id: str = data["game_id"]
        self.title: str = data["title"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.language: str = data["broadcaster_language"]
        self.live: bool = data["is_live"]
        self.started_at = datetime.datetime.strptime(data["started_at"], "%Y-%m-%dT%H:%M:%SZ") if self.live else None
        self.tag_ids: List[str] = data["tag_ids"]


class User(PartialUser):

    __slots__ = (
        "_http",
        "id",
        "name",
        "display_name",
        "type",
        "broadcaster_type",
        "description",
        "profile_image",
        "offline_image",
        "view_count",
        "created_at",
        "email",
        "_cached_rewards",
    )

    def __init__(self, http: HTTPHandler, data: dict):
        self._http = http
        self.id = int(data["id"])
        self.name: str = data["login"]
        self.display_name: str = data["display_name"]
        self.type = UserTypeEnum(data["type"])
        self.broadcaster_type = BroadcasterTypeEnum(data["broadcaster_type"])
        self.description: str = data["description"]
        self.profile_image: str = data["profile_image_url"]
        self.offline_image: str = data["offline_image_url"]
        self.view_count: int = data["view_count"]
        self.created_at = parse_timestamp(data["created_at"])
        self.email: Optional[str] = data.get("email")
        self._cached_rewards = None

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name} display_name={self.display_name} type={self.type}>"


class BitsLeaderboard:
    """
    Represents a Bits leaderboard from the twitch API.

    Attributes
    ------------
    started_at: :class:`datetime.datetime`
        The time the leaderboard started.
    ended_at: :class`datetime.datetime`
        The time the leaderboard ended.
    leaders: List[:class:`BitLeaderboardUser`]
        The current leaders of the Leaderboard.
    """

    __slots__ = "_http", "leaders", "started_at", "ended_at"

    def __init__(self, http: HTTPHandler, data: dict):
        self._http = http
        self.started_at = datetime.datetime.fromisoformat(data["date_range"]["started_at"])
        self.ended_at = datetime.datetime.fromisoformat(data["date_range"]["ended_at"])
        self.leaders = [BitLeaderboardUser(http, x) for x in data["data"]]

    def __repr__(self) -> str:
        return f"<BitsLeaderboard started_at={self.started_at} ended_at={self.ended_at}>"


class CheerEmoteTier:
    """
    Represents a Cheer Emote tier.

    Attributes
    -----------
    min_bits: :class:`int`
        The minimum bits for the tier
    id: :class:`str`
        The ID of the tier
    color: :class:`str`
        The color of the tier
    images: :class:`dict`
        contains two dicts, ``light`` and ``dark``. Each item will have an ``animated`` and ``static`` item,
        which will contain yet another dict, with sizes ``1``, ``1.5``, ``2``, ``3``, and ``4``.
        Ex. ``cheeremotetier.images["light"]["animated"]["1"]``
    can_cheer: :class:`bool`
        Indicates whether emote information is accessible to users.
    show_in_bits_card: :class`bool`
        Indicates whether twitch hides the emote from the bits card.
    """

    __slots__ = "min_bits", "id", "color", "images", "can_cheer", "show_in_bits_card"

    def __init__(self, data: dict):
        self.min_bits: int = data["min_bits"]
        self.id: str = data["id"]
        self.color: str = data["color"]
        self.images = data["images"]  # TODO types
        self.can_cheer: bool = data["can_cheer"]
        self.show_in_bits_card: bool = data["show_in_bits_card"]

    def __repr__(self) -> str:
        return f"<CheerEmoteTier id={self.id} min_bits={self.min_bits}>"


class CheerEmote:
    """
    Represents a Cheer Emote

    Attributes
    -----------
    prefix: :class:`str`
        The string used to Cheer that precedes the Bits amount.
    tiers: :class:`~CheerEmoteTier`
        The tiers this Cheer Emote has
    type: :class:`str`
        Shows whether the emote is ``global_first_party``, ``global_third_party``, ``channel_custom``, ``display_only``, or ``sponsored``.
    order: :class:`str`
        Order of the emotes as shown in the bits card, in ascending order.
    last_updated :class:`datetime.datetime`
        The date this cheermote was last updated.
    charitable: :class:`bool`
        Indicates whether this emote provides a charity contribution match during charity campaigns.
    """

    __slots__ = "_http", "prefix", "tiers", "type", "order", "last_updated", "charitable"

    def __init__(self, http: HTTPHandler, data: dict):
        self._http = http
        self.prefix: str = data["prefix"]
        self.tiers: List[CheerEmoteTier] = [CheerEmoteTier(x) for x in data["tiers"]]
        self.type: str = data["type"]
        self.order: str = data["order"]
        self.last_updated: datetime.datetime = parse_timestamp(data["last_updated"])
        self.charitable: bool = data["is_charitable"]

    def __repr__(self) -> str:
        return f"<CheerEmote prefix={self.prefix} type={self.type} order={self.order}>"


class Clip:
    """
    Represents a Twitch Clip

    Attributes
    -----------
    id: :class:`str`
        The ID of the clip.
    url: :class:`str`
        The URL of the clip.
    embed_url: :class:`str`
        The URL to embed the clip with.
    broadcaster: :class:`~twitchio.PartialUser`
        The user whose channel the clip was created on.
    creator: :class:`~twitchio.PartialUser`
        The user who created the clip.
    video_id: :class:`str`
        The ID of the video the clip is sourced from.
    game_id: :class:`str`
        The ID of the game that was being played when the clip was created.
    language: :class:`str`
        The language, in an `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ format, of the stream when the clip was created.
    title: :class:`str`
        The title of the clip.
    views: :class:`int`
        The amount of views this clip has.
    created_at: :class:`datetime.datetime`
        When the clip was created.
    thumbnail_url: :class:`str`
        The url of the clip thumbnail.
    """

    __slots__ = (
        "id",
        "url",
        "embed_url",
        "broadcaster",
        "creator",
        "video_id",
        "game_id",
        "language",
        "title",
        "views",
        "created_at",
        "thumbnail_url",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.id: str = data["id"]
        self.url: str = data["url"]
        self.embed_url: str = data["embed_url"]
        self.broadcaster: PartialUser = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.creator: PartialUser = PartialUser(http, data["creator_id"], data["creator_name"])
        self.video_id: str = data["video_id"]
        self.game_id: str = data["game_id"]
        self.language: str = data["language"]
        self.title: str = data["title"]
        self.views: int = data["view_count"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.thumbnail_url: str = data["thumbnail_url"]

    def __repr__(self) -> str:
        return f"<Clip id={self.id} broadcaster={self.broadcaster} creator={self.creator}>"


class HypeTrainContribution:
    """
    A Contribution to a Hype Train

    Attributes
    -----------
    total: :class:`int`
        Total aggregated amount of all contributions by the top contributor. If type is ``BITS``, total represents aggregate amount of bits used.
        If type is ``SUBS``, aggregate total where 500, 1000, or 2500 represent tier 1, 2, or 3 subscriptions respectively.
        For example, if top contributor has gifted a tier 1, 2, and 3 subscription, total would be 4000.
    type: :class:`str`
        Identifies the contribution method, either BITS or SUBS.
    user: :class:`~twitchio.PartialUser`
        The user making the contribution.
    """

    __slots__ = "total", "type", "user"

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.total: int = data["total"]
        self.type: str = data["type"]
        self.user: PartialUser = PartialUser(http, id=data["user"], name=None)

    def __repr__(self) -> str:
        return f"<HypeTrainContribution total={self.total} type={self.type} user={self.user}>"


class HypeTrainEvent:
    """
    Represents a Hype Train Event (progression)

    Attributes
    -----------
    id: :class:`str`
        The ID of the event.
    event_id: :class:`str`
        The ID of the Hype Train.
    type: :class:`str`
        The type of the event. Currently only ``hypetrain.progression``.
    version: :class:`str`
        The version of the endpoint.
    broadcaster: :class:`~twitchio.PartialUser`
        The user whose channel the Hype Train is occurring on.
    timestamp: :class:`datetime.datetime`
        The time the event happened at.
    cooldown_end_time: :class:`datetime.datetime`
        The time that another Hype Train can happen at.
    expiry: :class:`datetime.datetime`
        The time that this Hype Train expires at.
    started_at: :class:`datetime.datetime`
        The time that this Hype Train started at.
    last_contribution: :class:`HypeTrainContribution`
        The last contribution to this Hype Train.
    level: :class:`int`
        The level reached on this Hype Train (1-5).
    top_contributions: List[:class:`HypeTrainContribution`]
        The top contributors to the Hype Train.
    contributions_total: :class:`int`
        The total score towards completing the goal.
    goal: :class:`int`
        The goal for the next Hype Train level
    """

    __slots__ = (
        "id",
        "type",
        "timestamp",
        "version",
        "broadcaster",
        "expiry",
        "event_id",
        "goal",
        "level",
        "started_at",
        "top_contributions",
        "contributions_total",
        "cooldown_end_time",
        "last_contribution",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.id: str = data["id"]
        self.event_id: str = data["event_data"]["id"]
        self.type: str = data["event_type"]
        self.version: str = data["version"]
        self.broadcaster: PartialUser = PartialUser(http, id=data["event_data"]["broadcaster_id"], name=None)
        self.timestamp: datetime.datetime = parse_timestamp(data["event_timestamp"])
        self.cooldown_end_time: datetime.datetime = parse_timestamp(data["event_data"]["cooldown_end_time"])
        self.expiry: datetime.datetime = parse_timestamp(data["expires_at"])
        self.started_at: datetime.datetime = parse_timestamp(data["event_data"]["started_at"])
        self.last_contribution: HypeTrainContribution = HypeTrainContribution(
            http, data["event_data"]["last_contribution"]
        )
        self.level: int = data["event_data"]["level"]
        self.top_contributions: List[HypeTrainContribution] = [
            HypeTrainContribution(http, x) for x in data["event_data"]["top_contributions"]
        ]
        self.contributions_total: int = data["event_data"]["total"]
        self.goal: int = data["event_data"]["goal"]

    def __repr__(self) -> str:
        return f"<HypeTrainEvent id={self.id} type={self.type} level={self.level} broadcaster={self.broadcaster}>"


class BanEvent:
    """
    Represents a user being banned from a channel.

    Attributes
    -----------
    id: :class:`str`
        The event ID.
    type: :class:`str`
        Type of ban event. Either ``moderation.user.ban`` or ``moderation.user.unban``.
    timestamp: :class:`datetime.datetime`
        The time the action occurred at.
    version: :class:`float`
        The version of the endpoint.
    broadcaster: :class:`~twitchio.PartialUser`
        The user whose channel the ban/unban occurred on.
    user: :class:`~twichio.PartialUser`
        The user who was banned/unbanned.
    moderator: :class:`~twitchio.PartialUser`
        The user who performed the action.
    expires_at: Optional[:class:`datetime.datetime`]
        When the ban expires.
    reason: :class:`str`
        The reason the moderator banned/unbanned the user.
    """

    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user", "expires_at", "moderator", "reason"

    def __init__(self, http: HTTPHandler, data: dict, broadcaster: Optional[Union[PartialUser, User]]) -> None:
        self.id: str = data["id"]
        self.type: str = data["event_type"]
        self.timestamp: datetime.datetime = parse_timestamp(data["event_timestamp"])
        self.version: float = float(data["version"])
        self.reason: str = data["event_data"]["reason"]
        self.broadcaster: Union[User, PartialUser] = broadcaster or PartialUser(
            http, data["event_data"]["broadcaster_id"], data["event_data"]["broadcaster_name"]
        )
        self.user: PartialUser = PartialUser(http, data["event_data"]["user_id"], data["event_data"]["user_name"])
        self.moderator: PartialUser = PartialUser(
            http, data["event_data"]["moderator_id"], data["event_data"]["moderator_name"]
        )
        self.expires_at: Optional[datetime.datetime] = (
            parse_timestamp(data["event_data"]["expires_at"]) if data["event_data"]["expires_at"] else None
        )

    def __repr__(self) -> str:
        return f"<BanEvent id={self.id} type={self.type} broadcaster={self.broadcaster} user={self.user}>"


class FollowEvent:
    """
    Represents a Follow Event.

    Attributes
    -----------
    from_user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user that followed another user.
    to_user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user that was followed.
    followed_at: :class:`datetime.datetime`
        When the follow happened.
    """

    __slots__ = "from_user", "to_user", "followed_at"

    def __init__(
        self,
        http: HTTPHandler,
        data: dict,
        from_: Optional[Union[User, PartialUser]] = None,
        to: Optional[Union[User, PartialUser]] = None,
    ) -> None:
        self.from_user: Union[User, PartialUser] = from_ or PartialUser(http, data["from_id"], data["from_name"])
        self.to_user: Union[User, PartialUser] = to or PartialUser(http, data["to_id"], data["to_name"])
        self.followed_at: datetime.datetime = parse_timestamp(data["followed_at"])

    def __repr__(self) -> str:
        return f"<FollowEvent from_user={self.from_user} to_user={self.to_user} followed_at={self.followed_at}>"


class SubscriptionEvent:
    """
    Represents a Subscription Event

    Attributes
    -----------
    broadcaster: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user that was subscribed to.
    user: Union[:class:`~twitchio.User`, :class:`~twitchio.PartialUser`]
        The user who subscribed.
    tier: :class:`int`
        The tier at which the user subscribed. Could be ``1``, ``2``, or ``3``.
    plan_name: :class:`str`
        Name of the description. (twitch docs aren't helpful, if you know what this is specifically please PR :) ).
    gift: :class:`bool`
        Whether the subscription is a gift.
    """

    __slots__ = "broadcaster", "gift", "tier", "plan_name", "user"

    def __init__(
        self,
        http: HTTPHandler,
        data: dict,
        broadcaster: Optional[Union[User, PartialUser]] = None,
        user: Optional[Union[User, PartialUser]] = None,
    ):
        self.broadcaster: Union[User, PartialUser] = broadcaster or PartialUser(
            http, data["broadcaster_id"], data["broadcaster_name"]
        )
        self.user: Union[User, PartialUser] = user or PartialUser(http, data["user_id"], data["user_name"])
        self.tier: int = round(int(data["tier"]) / 1000)
        self.plan_name: str = data["plan_name"]
        self.gift: bool = data["is_gift"]

    def __repr__(self) -> str:
        return (
            f"<SubscriptionEvent broadcaster={self.broadcaster} user={self.user} tier={self.tier} "
            f"plan_name={self.plan_name} gift={self.gift}>"
        )


class Marker:
    """
    Represents a stream Marker

    Attributes
    -----------
    id: :class:`str`
        The ID of the marker.
    created_at: :class:`datetime.datetime`
        When the marker was created.
    description: :class:`str`
        The description of the marker.
    position: :class:`int`
        The position of the marker, in seconds.
    url: Optional[:class:`str`]
        The url that leads to the marker.
    """

    __slots__ = "id", "created_at", "description", "position", "url"

    def __init__(self, data: dict) -> None:
        self.id: str = data["id"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.description: str = data["description"]
        self.position: int = data["position_seconds"]
        self.url: Optional[str] = data.get("URL")

    def __repr__(self) -> str:
        return f"<Marker id={self.id} created_at={self.created_at} position={self.position} url={self.url}>"


class VideoMarkers:
    """
    Represents markers contained in a video

    Attributes
    -----------
    id: :class:`str`
        The video id.
    markers: List[:class:`Marker`]
        The markers contained in the video.
    """

    __slots__ = "id", "markers"

    def __init__(self, data: dict) -> None:
        self.id: str = data["video_id"]
        self.markers: List[Marker] = [Marker(d) for d in data["markers"]]

    def __repr__(self) -> str:
        return f"<VideoMarkers id={self.id}>"


class Game:
    """
    Represents a Game on twitch

    Attributes
    -----------
    id: :class:`int`
        Game ID.
    name: :class:`str`
        Game name.
    box_art_url: :class:`str`
        Template URL for the game’s box art.
    """

    __slots__ = "id", "name", "box_art_url"

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.id: int = int(data["id"])
        self.name: str = data["name"]
        self.box_art_url: str = data["box_art_url"]

    def __repr__(self) -> str:
        return f"<Game id={self.id} name={self.name}>"

    def art_url(self, width: int, height: int) -> str:
        """
        Adds width and height into the box art url

        Parameters
        -----------
        width: :class:`int`
            The width of the image
        height: :class:`int`
            The height of the image

        Returns
        --------
            :class:`str`
        """
        return self.box_art_url.format(width=width, height=height)


class ModEvent:
    """
    Represents a mod add/remove action

    Attributes
    -----------
    id: :class:`str`
        The ID of the event.
    type: :class:`~twitchio.ModEventEnum`
        The type of the event.
    timestamp: :class:`datetime.datetime`
        The timestamp of the event.
    version: :class:`str`
        The version of the endpoint.
    broadcaster: Union[:class:`~twitchio.PartialUser`, :class:`~twitchio.User`]
        The user whose channel the event happened on.
    user: :class:`~twitchio.PartialUser`
        The user being removed or added as a moderator.
    """

    __slots__ = "id", "type", "timestamp", "version", "broadcaster", "user"

    def __init__(self, http: HTTPHandler, data: dict, broadcaster: Union[PartialUser, User]):
        self.id: str = data["id"]
        self.type = ModEventEnum(value=data["event_type"])
        self.timestamp = parse_timestamp(data["event_timestamp"])
        self.version: str = data["version"]
        self.broadcaster: Union[PartialUser, User] = broadcaster
        self.user: PartialUser = PartialUser(http, data["event_data"]["user_id"], data["event_data"]["user_name"])

    def __repr__(self) -> str:
        return f"<ModEvent id={self.id} type={self.type} broadcaster={self.broadcaster} user={self.user}>"


class AutomodCheckMessage:
    """
    Represents the message to check with automod

    Attributes
    -----------
    id: :class:`str`
        Developer-generated identifier for mapping messages to results.
    text: :class:`str`
        Message text.
    user_id: :class:`int`
        User ID of the sender.
    """

    __slots__ = "id", "text", "user_id"

    def __init__(self, id: str, text: str, user: Union[PartialUser, int]):
        self.id: str = id
        self.text: str = text
        self.user_id: int = user.id if isinstance(user, PartialUser) else user

    def _to_dict(self) -> Dict[str, Union[str, int]]:
        return {"msg_id": self.id, "msg_text": self.text, "user_id": str(self.user_id)}

    def __repr__(self) -> str:
        return f"<AutomodCheckMessage id={self.id} user_id={self.user_id}>"


class AutomodCheckResponse:
    """
    Represents the response to a message check with automod

    Attributes
    -----------
    id: :class:`str`
        The message ID passed in the body of the check
    permitted: :class:`bool`
        Indicates if this message meets AutoMod requirements.
    """

    __slots__ = "id", "permitted"

    def __init__(self, data: dict) -> None:
        self.id: str = data["msg_id"]
        self.permitted: bool = data["is_permitted"]

    def __repr__(self) -> str:
        return f"<AutomodCheckResponse id={self.id} permitted={self.permitted}>"


class Extension:
    """
    Represents an extension for a specified user

    Attributes
    -----------
    id: :class:`str`
        ID of the extension.
    version: :class:`str`
        Version of the extension.
    active: :class:`bool`
        Activation state of the extension, for each extension type (component, overlay, mobile, panel).
    """

    __slots__ = "id", "active", "version", "_x", "_y"

    def __init__(self, data) -> None:
        self.id: str = data["id"]
        self.version: str = data["version"]
        self.active: bool = data["active"]
        self._x = None
        self._y = None

    def __repr__(self) -> str:
        return f"<Extension id={self.id} version={self.version} active={self.active}>"

    @classmethod
    def new(cls, active: bool, version: str, id: str, x: Optional[int] = None, y: Optional[int] = None) -> Extension:
        self = cls.__new__(cls)
        self.active = active
        self.version = version
        self.id = id
        self._x = x
        self._y = y
        return self

    def _to_dict(self) -> ExtensionType:
        v: ExtensionType = {"active": self.active, "id": self.id, "version": self.version}
        if self._x is not None:
            v["x"] = self._x
        if self._y is not None:
            v["y"] = self._y

        return v


class MaybeActiveExtension(Extension):
    """
    Represents an extension for a specified user that could be may be activated

    Attributes
    -----------
    id: :class:`str`
        ID of the extension.
    version: :class:`str`
        Version of the extension.
    name: :class:`str`
        Name of the extension.
    can_activate: :class:`bool`
        Indicates whether the extension is configured such that it can be activated.
    types: List[:class:`str`]
        Types for which the extension can be activated.
    """

    __slots__ = "id", "version", "name", "can_activate", "types"

    def __init__(self, data) -> None:
        self.id: str = data["id"]
        self.version: str = data["version"]
        self.name: str = data["name"]
        self.can_activate: bool = data["can_activate"]
        self.types: List[str] = data["type"]

    def __repr__(self) -> str:
        return f"<MaybeActiveExtension id={self.id} version={self.version} name={self.name}>"


class ActiveExtension(Extension):
    """
    Represents an active extension for a specified user

    Attributes
    -----------
    id: :class:`str`
        ID of the extension.
    version: :class:`str`
        Version of the extension.
    active: :class:`bool`
        Activation state of the extension.
    name: :class:`str`
        Name of the extension.
    x: :class:`int`
        (Video-component Extensions only) X-coordinate of the placement of the extension. Could be None.
    y: :class:`int`
        (Video-component Extensions only) Y-coordinate of the placement of the extension. Could be None.
    """

    __slots__ = "id", "active", "name", "version", "x", "y"

    def __init__(self, data) -> None:
        self.active: bool = data["active"]
        self.id: Optional[str] = data.get("id", None)
        self.version: Optional[str] = data.get("version", None)
        self.name: Optional[str] = data.get("name", None)
        self.x: Optional[int] = data.get("x", None)  # x and y only show for component extensions.
        self.y: Optional[int] = data.get("y", None)

    def __repr__(self) -> str:
        return f"<ActiveExtension id={self.id} version={self.version} name={self.name}>"


class ExtensionBuilder:
    """
    Represents an extension to be updated for a specific user

    Attributes
    -----------
    panels: List[:class:`~twitchio.Extension`]
        List of panels to update for an extension.
    overlays: List[:class:`~twitchio.Extension`]
        List of overlays to update for an extension.
    components: List[:class:`~twitchio.Extension`]
        List of components to update for an extension.
    """

    __slots__ = "panels", "overlays", "components"

    def __init__(
        self,
        panels: Optional[List[Extension]] = None,
        overlays: Optional[List[Extension]] = None,
        components: Optional[List[Extension]] = None,
    ) -> None:
        self.panels: List[Extension] = panels or []
        self.overlays: List[Extension] = overlays or []
        self.components: List[Extension] = components or []

    def _to_dict(self) -> ExtensionBuilderType:
        d: ExtensionBuilderType = {
            "panel": {str(x): y._to_dict() for x, y in enumerate(self.panels)},
            "overlay": {str(x): y._to_dict() for x, y in enumerate(self.overlays)},
            "component": {str(x): y._to_dict() for x, y in enumerate(self.components)},
        }
        return d


class Video:
    """
    Represents video information

    Attributes
    -----------
    id: :class:`int`
        The ID of the video.
    user: :class:`~twitchio.PartialUser`
        User who owns the video.
    title: :class:`str`
        Title of the video
    description: :class:`str`
        Description of the video.
    created_at: :class:`datetime.datetime`
        Date when the video was created.
    published_at: :class:`datetime.datetime`
       Date when the video was published.
    url: :class:`str`
        URL of the video.
    thumbnail_url: :class:`str`
        Template URL for the thumbnail of the video.
    viewable: :class:`str`
        Indicates whether the video is public or private.
    view_count: :class:`int`
        Number of times the video has been viewed.
    language: :class:`str`
        Language of the video.
    type: :class:`str`
        The type of video.
    duration: :class:`str`
        Length of the video.
    """

    __slots__ = (
        "_http",
        "id",
        "user",
        "title",
        "description",
        "created_at",
        "published_at",
        "url",
        "thumbnail_url",
        "viewable",
        "view_count",
        "language",
        "type",
        "duration",
    )

    def __init__(self, http: HTTPHandler, data: dict, user: Optional[Union[PartialUser, User]] = None) -> None:
        self._http = http
        self.id: int = int(data["id"])
        self.user = user or PartialUser(http, data["user_id"], data["user_name"])
        self.title: str = data["title"]
        self.description: str = data["description"]
        self.created_at = parse_timestamp(data["created_at"])
        self.published_at = parse_timestamp(data["published_at"])
        self.url: str = data["url"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.viewable: str = data["viewable"]
        self.view_count: int = data["view_count"]
        self.language: str = data["language"]
        self.type: str = data["type"]
        self.duration: str = data["duration"]

    def __repr__(self) -> str:
        return f"<Video id={self.id} title={self.title} url={self.url}>"

    async def delete(self) -> None:
        """|coro|

        Deletes the video. For bulk deletion see :func:`Client.delete_videos`

        Parameters
        -----------
        token: :class:`str`
            The users oauth token with the channel:manage:videos
        """
        await self._http.delete_videos(ids=[self.id], target=self.user)


class Tag:
    """
    Represents a stream tag

    Attributes
    -----------
    id: :class:`str`
        An ID that identifies the tag.
    auto: :class:`bool`
        Indicates whether the tag is an automatic tag.
    localization_names: Dict[:class:`str`, :class:`str`]
        A dictionary that contains the localized names of the tag.
    localization_descriptions: :class:`str`
        A dictionary that contains the localized descriptions of the tag.
    """

    __slots__ = "id", "auto", "localization_names", "localization_descriptions"

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.id: str = data["tag_id"]
        self.auto: bool = data["is_auto"]
        self.localization_names: Dict[str, str] = data["localization_names"]
        self.localization_descriptions: Dict[str, str] = data["localization_descriptions"]

    def __repr__(self) -> str:
        return f"<Tag id={self.id}>"


class WebhookSubscription:
    """
    Represents a Webhook Subscription

    Attributes
    -----------
    callback: :class:`str`
        Where the webhook will be directed when triggered.
    expires_at: :class:`datetime.datetime`
        When the webhook expires.
    topic: :class:`str`
        The topic of the subscription.
    """

    __slots__ = "callback", "expires_at", "topic"

    def __init__(self, data: dict) -> None:
        self.callback: str = data["callback"]
        self.expires_at: datetime.datetime = parse_timestamp(data["expired_at"])
        self.topic: str = data["topic"]

    def __repr__(self) -> str:
        return f"<WebhookSubscription callback={self.callback} topic={self.topic} expires_at={self.expires_at}>"


class Stream:
    """
    Represents a Stream

    Attributes
    -----------
    id: :class:`int`
        The current stream ID.
    user: :class:`~twitchio.PartialUser`
        The user who is streaming.
    game_id: :class:`int`
        Current game ID being played on the channel.
    game_name: :class:`str`
        Name of the game being played on the channel.
    type: :class:`str`
        Whether the stream is "live" or not.
    title: :class:`str`
        Title of the stream.
    viewer_count: :class:`int`
        Current viewer count of the stream
    started_at: :class:`datetime.datetime`
        UTC timestamp of when the stream started.
    language: :class:`str`
        Language of the channel.
    thumbnail_url: :class:`str`
        Thumbnail URL of the stream.
    tag_ids: List[:class:`str`]
        Tag IDs that apply to the stream.
    is_mature: :class:`bool`
        Indicates whether the stream is intended for mature audience.
    """

    __slots__ = (
        "id",
        "user",
        "game_id",
        "game_name",
        "type",
        "title",
        "viewer_count",
        "started_at",
        "language",
        "thumbnail_url",
        "tag_ids",
        "is_mature",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.id: int = data["id"]
        self.user: PartialUser = PartialUser(http, data["user_id"], data["user_name"])
        self.game_id: int = data["game_id"]
        self.game_name: str = data["game_name"]
        self.type: str = data["type"]
        self.title: str = data["title"]
        self.viewer_count: int = data["viewer_count"]
        self.started_at = parse_timestamp(data["started_at"])
        self.language: str = data["language"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.tag_ids: List[str] = data["tag_ids"]
        self.is_mature: bool = data["is_mature"]

    def __repr__(self) -> str:
        return f"<Stream id={self.id} user={self.user} title={self.title} started_at={self.started_at}>"


class ChannelInfo:
    """
    Represents a channel's current information

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        The user whose channel information was requested.
    game_id: :class:`int`
        Current game ID being played on the channel.
    game_name: :class:`str`
        Name of the game being played on the channel.
    title: :class:`str`
        Title of the stream.
    language: :class:`str`
        Language of the channel.
    delay: :class:`int`
        Stream delay in seconds.
    """

    __slots__ = ("user", "game_id", "game_name", "title", "language", "delay")

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.user: PartialUser = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.game_id: int = data["game_id"]
        self.game_name: str = data["game_name"]
        self.title: str = data["title"]
        self.language: str = data["broadcaster_language"]
        self.delay: int = data["delay"]

    def __repr__(self) -> str:
        return f"<ChannelInfo user={self.user} game_id={self.game_id} game_name={self.game_name} title={self.title} language={self.language} delay={self.delay}>"


class Prediction:
    """
    Represents channel point predictions

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        The user who is streaming.
    prediction_id: :class:`str`
        ID of the Prediction.
    title: :class:`str`
        Title for the Prediction.
    winning_outcome_id: :class:`str`
        ID of the winning outcome
    outcomes: List[:class:`~twitchio.PredictionOutcome`]
        List of possible outcomes for the Prediction.
    prediction_window: :class:`int`
        Total duration for the Prediction (in seconds).
    prediction_status: :class:`str`
        Status of the Prediction.
    created_at: :class:`datetime.datetime`
        Time for when the Prediction was created.
    ended_at: Optional[:class:`datetime.datetime`]
        Time for when the Prediction ended.
    locked_at: Optional[:class:`datetime.datetime`]
        Time for when the Prediction was locked.
    """

    __slots__ = (
        "user",
        "prediction_id",
        "title",
        "winning_outcome_id",
        "outcomes",
        "prediction_window",
        "prediction_status",
        "created_at",
        "ended_at",
        "locked_at",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.user: PartialUser = PartialUser(http, data["broadcaster_id"], data["broadcaster_name"])
        self.prediction_id: str = data["id"]
        self.title: str = data["title"]
        self.winning_outcome_id: str = data["winning_outcome_id"]
        self.outcomes: List[PredictionOutcome] = [PredictionOutcome(http, x) for x in data["outcomes"]]
        self.prediction_window: int = data["prediction_window"]
        self.prediction_status: str = data["status"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.ended_at: Optional[datetime.datetime] = data.get("ended_at") and parse_timestamp(data["ended_at"])
        self.locked_at: Optional[datetime.datetime] = data.get("locked_at") and parse_timestamp(data["locked_at"])

    def __repr__(self) -> str:
        return f"<Prediction user={self.user} prediction_id={self.prediction_id} winning_outcome_id={self.winning_outcome_id} title={self.title}>"


class Predictor:
    """
    Represents a predictor

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        The user who is streaming.
    channel_points_used: :class:`int`
        Number of Channel Points used by the user.
    channel_points_won: :class:`int`
        Number of Channel Points won by the user.
    """

    __slots__ = ("points_used", "points_won", "user")

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.points_used: int = data["channel_points_used"]
        self.points_won: int = data["channel_points_won"]
        self.user: PartialUser = PartialUser(http, data["user"]["id"], data["user"]["name"])

    def __repr__(self) -> str:
        return f"<Predictor points_used={self.points_used} points_won={self.points_won} user={self.user}>"


class PredictionOutcome:
    """
    Represents a prediction outcome

    Attributes
    -----------
    outcome_id: :class:`str`
        ID for the outcome.
    title: :class:`str`
        Text displayed for outcome.
    channel_points: :class:`int`
        Number of Channel Points used for the outcome.
    color: :class:`str`
        Color for the outcome.
    users: :class:`int`
        Number of unique uesrs that chose the outcome.
    top_predictors: List[:class:`~twitchio.Predictor`]
        List of the top predictors. Could be None.
    """

    __slots__ = ("outcome_id", "title", "channel_points", "color", "users", "top_predictors")

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.outcome_id: str = data["id"]
        self.title: str = data["title"]
        self.channel_points: int = data["channel_points"]
        self.color: str = data["color"]
        self.users: int = data["users"]
        self.top_predictors: Optional[List[Predictor]]

        if data["top_predictors"]:
            self.top_predictors = [Predictor(http, x) for x in data["top_predictors"]]
        else:
            self.top_predictors = None

    @property
    def colour(self) -> str:
        """The colour of the prediction. Alias to color."""
        return self.color

    def __repr__(self) -> str:
        return f"<PredictionOutcome outcome_id={self.outcome_id} title={self.title} channel_points={self.channel_points} color={self.color}>"


class Schedule:
    """
    Represents a channel's stream schedule

    Attributes
    -----------
    segments: List[:class:`~twitchio.ScheduleSegment`]
        List of segments of a channel's stream schedule.
    user: :class:`~twitchio.PartialUser`
        The user of the channel associated to the schedule.
    vacation: :class:`~twitchio.ScheduleVacation`
        Vacation details of stream schedule.
    """

    __slots__ = ("segments", "user", "vacation")

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.segments: List[ScheduleSegment] = (
            [ScheduleSegment(d) for d in data["data"]["segments"]] if data["data"]["segments"] else []
        )
        self.user: PartialUser = PartialUser(http, data["data"]["broadcaster_id"], data["data"]["broadcaster_login"])
        self.vacation: Optional[ScheduleVacation] = (
            ScheduleVacation(data["data"]["vacation"]) if data["data"]["vacation"] else None
        )

    def __repr__(self) -> str:
        return f"<Schedule segments={self.segments} user={self.user} vacation={self.vacation}>"


class ScheduleSegment:
    """
    Represents a list segments of a channel's stream schedule

    Attributes
    -----------
    id: :class:`str`
        The ID for the scheduled broadcast.
    start_time: :class:`datetime.datetime`
        Scheduled start time for the scheduled broadcast
    end_time: :class:`datetime.datetime`
        Scheduled end time for the scheduled broadcast
    title: :class:`str`
        Title for the scheduled broadcast.
    canceled_until: :class:`datetime.datetime`
        Used with recurring scheduled broadcasts. Specifies the date of the next recurring broadcast.
    category: :class:`~twitchio.ScheduleCategory`
        The game or category details for the scheduled broadcast.
    is_recurring: :class:`bool`
        Indicates if the scheduled broadcast is recurring weekly.
    """

    __slots__ = ("id", "start_time", "end_time", "title", "canceled_until", "category", "is_recurring")

    def __init__(self, data: dict) -> None:
        self.id: str = data["id"]
        self.start_time: datetime.datetime = parse_timestamp(data["start_time"])
        self.end_time: datetime.datetime = parse_timestamp(data["end_time"])
        self.title: str = data["title"]
        self.canceled_until: Optional[datetime.datetime] = (
            parse_timestamp(data["canceled_until"]) if data["canceled_until"] else None
        )
        self.category: Optional[ScheduleCategory] = ScheduleCategory(data["category"]) if data["category"] else None
        self.is_recurring: bool = data["is_recurring"]

    def __repr__(self) -> str:
        return f"<ScheduleSegment id={self.id} start_time={self.start_time} end_time={self.end_time} title={self.title} canceled_until={self.canceled_until} category={self.category} is_recurring={self.is_recurring}>"


class ScheduleCategory:
    """
    Game or category details of a stream's schedule

    Attributes
    -----------
    id: :class:`str`
        The game or category ID.
    name: :class:`str`
        The game or category name.
    """

    __slots__ = ("id", "name")

    def __init__(self, data: dict) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]

    def __repr__(self) -> str:
        return f"<ScheduleCategory id={self.id} name={self.name}>"


class ScheduleVacation:
    """
    A schedule's vacation details

    Attributes
    -----------
    start_time: :class:`datetime.datetime`
        Start date of stream schedule vaction.
    end_time: :class:`datetime.datetime`
        End date of stream schedule vaction.
    """

    __slots__ = ("start_time", "end_time")

    def __init__(self, data: dict) -> None:
        self.start_time: datetime.datetime = parse_timestamp(data["start_time"])
        self.end_time: datetime.datetime = parse_timestamp(data["end_time"])

    def __repr__(self) -> str:
        return f"<ScheduleVacation start_time={self.start_time} end_time={self.end_time}>"


class Team:
    """
    Represents information for a specific Twitch Team

    Attributes
    -----------
    users: List[:class:`~twitchio.PartialUser`]
        List of users in the specified Team.
    background_image_url: :class:`str`
        URL for the Team background image.
    banner: :class:`str`
        URL for the Team banner.
    created_at: :class:`datetime.datetime`
        Date and time the Team was created.
    updated_at: :class:`datetime.datetime`
        Date and time the Team was last updated.
    info: :class:`str`
        Team description.
    thumbnail_url: :class:`str`
        Image URL for the Team logo.
    team_name: :class:`str`
        Team name.
    team_display_name: :class:`str`
        Team display name.
    id: :class:`str`
        Team ID.
    """

    __slots__ = (
        "users",
        "background_image_url",
        "banner",
        "created_at",
        "updated_at",
        "info",
        "thumbnail_url",
        "team_name",
        "team_display_name",
        "id",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.users: List[PartialUser] = [PartialUser(http, x["user_id"], x["user_login"]) for x in data["users"]]
        self.background_image_url: str = data["background_image_url"]
        self.banner: str = data["banner"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"].split(" ")[0])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"].split(" ")[0])
        self.info: str = data["info"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.team_name: str = data["team_name"]
        self.team_display_name: str = data["team_display_name"]
        self.id: int = data["id"]

    def __repr__(self) -> str:
        return f"<Team users={self.users} team_name={self.team_name} team_display_name={self.team_display_name} id={self.id} created_at={self.created_at}>"


class ChannelTeams:
    """
    Represents the Twitch Teams of which the specified channel/broadcaster is a member

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster.
    background_image_url: :class:`str`
        URL for the Team background image.
    banner: :class:`str`
        URL for the Team banner.
    created_at: :class:`datetime.datetime`
        Date and time the Team was created.
    updated_at: :class:`datetime.datetime`
        Date and time the Team was last updated.
    info: :class:`str`
        Team description.
    thumbnail_url: :class:`str`
        Image URL for the Team logo.
    team_name: :class:`str`
        Team name.
    team_display_name: :class:`str`
        Team display name.
    id: :class:`str`
        Team ID.
    """

    __slots__ = (
        "broadcaster",
        "background_image_url",
        "banner",
        "created_at",
        "updated_at",
        "info",
        "thumbnail_url",
        "team_name",
        "team_display_name",
        "id",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.broadcaster: PartialUser = PartialUser(http, data["broadcaster_id"], data["broadcaster_login"])
        self.background_image_url: str = data["background_image_url"]
        self.banner: str = data["banner"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"].split(" ")[0])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"].split(" ")[0])
        self.info: str = data["info"]
        self.thumbnail_url: str = data["thumbnail_url"]
        self.team_name: str = data["team_name"]
        self.team_display_name: str = data["team_display_name"]
        self.id: int = data["id"]

    def __repr__(self) -> str:
        return f"<ChannelTeams user={self.broadcaster} team_name={self.team_name} team_display_name={self.team_display_name} id={self.id} created_at={self.created_at}>"


class Poll:
    """
    Represents a list of Polls for a broadcaster / channel

    Attributes
    -----------
    id: :class:`str`
        ID of a poll.
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster.
    title: :class:`str`
        Question displayed for the poll.
    choices: List[:class:`~twitchio.PollChoice`]
        The poll choices.
    bits_voting_enabled: :class:`bool`
        Indicates if Bits can be used for voting.
    bits_per_vote: :class:`int`
        Number of Bits required to vote once with Bits.
    channel_points_voting_enabled: :class:`bool`
        Indicates if Channel Points can be used for voting.
    channel_points_per_vote: :class:`int`
        Number of Channel Points required to vote once with Channel Points.
    status: :class:`str`
        Poll status. Valid values: ACTIVE, COMPLETED, TERMINATED, ARCHIVED, MODERATED, INVALID
    duration: :class:`int`
        Total duration for the poll (in seconds).
    started_at: :class:`datetime.datetime`
        Date and time the the poll was started.
    ended_at: :class:`datetime.datetime`
        Date and time the the poll was ended.
    """

    __slots__ = (
        "id",
        "broadcaster",
        "title",
        "choices",
        "channel_points_voting_enabled",
        "channel_points_per_vote",
        "status",
        "duration",
        "started_at",
        "ended_at",
    )

    def __init__(self, http: HTTPHandler, data: dict) -> None:
        self.id: str = data["id"]
        self.broadcaster: PartialUser = PartialUser(http, data["broadcaster_id"], data["broadcaster_login"])
        self.title: str = data["title"]
        self.choices: List[PollChoice] = [PollChoice(d) for d in data["choices"]] if data["choices"] else []
        self.channel_points_voting_enabled: bool = data["channel_points_voting_enabled"]
        self.channel_points_per_vote: int = data["channel_points_per_vote"]
        self.status: str = data["status"]
        self.duration: int = data["duration"]
        self.started_at: datetime.datetime = parse_timestamp(data["started_at"])
        self.ended_at: Optional[datetime.datetime]
        try:
            self.ended_at = parse_timestamp(data["ended_at"])
        except KeyError:
            self.ended_at = None

    def __repr__(self) -> str:
        return f"<Polls id={self.id} broadcaster={self.broadcaster} title={self.title} status={self.status} duration={self.duration} started_at={self.started_at} ended_at={self.ended_at}>"


class PollChoice:
    """
    Represents a polls choices

    Attributes
    -----------
    id: :class:`str`
        ID for the choice
    title: :class:`str`
        Text displayed for the choice
    votes: :class:`int`
        Total number of votes received for the choice across all methods of voting
    channel_points_votes: :class:`int`
        Number of votes received via Channel Points
    bits_votes: :class:`int`
        Number of votes received via Bits
    """

    __slots__ = ("id", "title", "votes", "channel_points_votes", "bits_votes")

    def __init__(self, data: dict) -> None:
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.votes: int = data["votes"]
        self.channel_points_votes: int = data["channel_points_votes"]
        self.bits_votes: int = data["bits_votes"]

    def __repr__(self) -> str:
        return f"<PollChoice id={self.id} title={self.title} votes={self.votes} channel_points_votes={self.channel_points_votes} bits_votes={self.bits_votes}>"


class Goal:
    """
    Represents a list of Goals for a broadcaster / channel

    Attributes
    -----------
    id: :class:`str`
        An ID that uniquely identifies this goal
    broadcaster: :class:`~twitchio.PartialUser`
        The broadcaster
    type: Literal["follower", "subscription", "new_subscription"]
        The type of goal
    description: :class:`str`
        A description of the goal, if specified
    current_amount: :class:`int`
        The current value
    target_amount: :class:`int`
        Number of Bits required to vote once with Bits
    created_at: :class:`datetime.datetime`
        Date and time of when the broadcaster created the goal
    """

    __slots__ = (
        "id",
        "broadcaster",
        "type",
        "description",
        "current_amount",
        "target_amount",
        "created_at",
    )

    def __init__(self, http: HTTPHandler, data: dict):
        self.id: str = data["id"]
        self.broadcaster = PartialUser(http, data["broadcaster_id"], data["broadcaster_login"])
        self.type: Literal["follower", "subscription", "new_subscription"] = data["type"]
        self.description: str = data["description"]
        self.current_amount: int = data["current_amount"]
        self.target_amount: int = data["target_amount"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])

    def __repr__(self):
        return f"<Goal id={self.id} broadcaster={self.broadcaster} description={self.description} current_amount={self.current_amount} target_amount={self.target_amount} created_at={self.created_at}>"


class ChatSettings:
    """
    Represents current chat settings of a broadcaster / channel

    Attributes
    -----------
    broadcaster: :class:`~twitchio.PartialUser`
        User of the broadcaster. Only returns the ID
    emote_mode: :class:`bool`
        Indicates whether emote only mode is enabled
    follower_mode: :class:`bool`
        Indicates whether follower only chat is enabled
    follower_mode_duration: Optional[:class:`int`]
        The length of time, in minutes, that the followers must have followed the broadcaster to participate in chat
    slow_mode: :class:`bool`
        Indicates whether the chat is in slow mode
    slow_mode_wait_time: Optional[:class:`int`]
        The amount of time, in seconds, that users need to wait between sending messages
    subscriber_mode: :class:`bool`
        Indicates whether only users that subscribe to the broadcaster's channel can talk in chat
    unique_chat_mode: :class:`bool`
        Indicates whether the broadcaster requires users to post only unique messages in the chat room
    moderator: Optional[:class:`~twitchio.PartialUser`]
        The User of the moderator, if provided. Only returns the ID
    non_moderator_chat_delay: Optional[:class:`bool`]
        Indicates whether the broadcaster adds a short delay before chat messages appear in the chat room
    non_moderator_chat_delay_duration: Optional[:class:`int`]
        The amount of time, in seconds, that messages are delayed from appearing in chat
    """

    __slots__ = (
        "broadcaster",
        "emote_mode",
        "follower_mode",
        "follower_mode_duration",
        "slow_mode",
        "slow_mode_wait_time",
        "subscriber_mode",
        "unique_chat_mode",
        "moderator",
        "non_moderator_chat_delay",
        "non_moderator_chat_delay_duration",
    )

    def __init__(self, http: HTTPHandler, data: dict):
        self.broadcaster = PartialUser(http, data["broadcaster_id"], None)
        self.emote_mode: bool = data["emote_mode"]
        self.follower_mode: bool = data["follower_mode"]
        self.follower_mode_duration: Optional[int] = data.get("follower_mode_duration")
        self.slow_mode: bool = data["slow_mode"]
        self.slow_mode_wait_time: Optional[int] = data.get("slow_mode_wait_time")
        self.subscriber_mode: bool = data["subscriber_mode"]
        self.unique_chat_mode: bool = data["unique_chat_mode"]
        self.non_moderator_chat_delay: Optional[bool] = data.get("non_moderator_chat_delay")
        self.non_moderator_chat_delay_duration: Optional[int] = data.get("non_moderator_chat_delay_duration")
        self.moderator: Optional[PartialUser]
        try:
            self.moderator = PartialUser(http, data["moderator_id"], None)
        except KeyError:
            self.moderator = None

    def __repr__(self):
        return f"<ChatSettings broadcaster={self.broadcaster} emote_mode={self.emote_mode} follower_mode={self.follower_mode} slow_mode={self.slow_mode} subscriber_mode={self.subscriber_mode} unique_chat_mode={self.unique_chat_mode}>"


class ChatterColor:
    """
    Represents chatters current name color.

    Attributes
    -----------
    user: :class:`~twitchio.PartialUser`
        PartialUser of the chatter.
    color: :class:`str`
        The color of the chatter's name.
    """

    __slots__ = ("user", "color")

    def __init__(self, http: HTTPHandler, data: dict):
        self.user = PartialUser(http, data["user_id"], data["user_login"])
        self.color: str = data["color"]

    def __repr__(self):
        return f"<ChatterColor user={self.user} color={self.color}>"


class Raid:
    """
    Represents a raid for a broadcaster / channel

    Attributes
    -----------
    created_at: :class:`datetime.datetime`
        Date and time of when the raid started.
    is_mature: :class:`bool`
        Indicates whether the stream being raided is marked as mature.
    """

    __slots__ = ("created_at", "is_mature")

    def __init__(self, data: dict):
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.is_mature: bool = data["is_mature"]

    def __repr__(self):
        return f"<Raid created_at={self.created_at} is_mature={self.is_mature}>"
