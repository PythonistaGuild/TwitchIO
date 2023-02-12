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

import datetime
import time
from typing import TYPE_CHECKING, List, Optional, Union, Tuple

from .enums import BroadcasterTypeEnum, UserTypeEnum
from .errors import HTTPException, Unauthorized
from .rewards import CustomReward
from .utils import parse_timestamp


if TYPE_CHECKING:
    from .http import TwitchHTTP
    from .channel import Channel
    from .models import BitsLeaderboard, Clip, ExtensionBuilder, Tag, FollowEvent, Prediction
__all__ = (
    "PartialUser",
    "BitLeaderboardUser",
    "UserBan",
    "SearchUser",
    "User",
)


class PartialUser:
    """
    A class that contains minimal data about a user from the API.

    Attributes
    -----------
    id: :class:`int`
        The user's ID.
    name: Optional[:class:`str`]
        The user's name. In most cases, this is provided. There are however, rare cases where it is not.
    """

    __slots__ = "id", "name", "_http", "_cached_rewards"

    def __init__(self, http: "TwitchHTTP", id: Union[int, str], name: Optional[str]):
        self.id = int(id)
        self.name = name
        self._http = http

        self._cached_rewards = None

    def __repr__(self):
        return f"<PartialUser id={self.id}, name={self.name}>"

    @property
    def channel(self) -> Optional["Channel"]:
        """
        Returns the :class:`twitchio.Channel` associated with this user. Could be None if you are not part of the channel's chat

        Returns
        --------
        Optional[:class:`twitchio.Channel`]
        """
        from .channel import Channel

        if self.name in self._http.client._connection._cache:
            return Channel(self.name, self._http.client._connection)

    async def fetch(self, token: str = None, force=False) -> "User":
        """|coro|

        Fetches the full user from the api or cache

        Parameters
        -----------
        token : :class:`str`
            Optional OAuth token to be used instead of the bot-wide OAuth token
        force : :class:`bool`
            Whether to force a fetch from the api or try to get from the cache first. Defaults to False

        Returns
        --------
        :class:`twitchio.User` The full user associated with this PartialUser
        """
        data = await self._http.client.fetch_users(ids=[self.id], force=force, token=token)
        return data[0]

    async def edit(self, token: str, description: str) -> None:
        """|coro|

        Edits a channels description

        Parameters
        -----------
        token: :class:`str`
            An oauth token for the user with the user:edit scope
        description: :class:`str`
            The new description for the user
        """
        await self._http.put_update_user(token, description)

    async def fetch_tags(self):
        """|coro|

        Fetches tags the user currently has active.

        Returns
        --------
            List[:class:`twitchio.Tag`]
        """
        from .models import Tag

        data = await self._http.get_channel_tags(str(self.id))
        return [Tag(x) for x in data]

    async def replace_tags(self, token: str, tags: List[Union[str, "Tag"]]):
        """|coro|

        Replaces the channels active tags. Tags expire 72 hours after being applied,
        unless the stream is live during that time period.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the user:edit:broadcast scope
        tags: List[Union[:class:`twitchio.Tag`, :class:`str`]]
            A list of :class:`twitchio.Tag` or tag ids to put on the channel. Max 100
        """
        tags = [x if isinstance(x, str) else x.id for x in tags]
        await self._http.put_replace_channel_tags(token, str(self.id), tags)

    async def get_custom_rewards(
        self, token: str, *, only_manageable=False, ids: List[int] = None, force=False
    ) -> List["CustomReward"]:
        """|coro|

        Fetches the channels custom rewards (aka channel points) from the api.

        Parameters
        ----------
        token: :class:`str`
            The users oauth token.
        only_manageable: :class:`bool`
            Whether to fetch all rewards or only ones you can manage. Defaults to false.
        ids: List[:class:`int`]
            An optional list of reward ids
        force: :class:`bool`
            Whether to force a fetch or try to get from cache. Defaults to False

        Returns
        -------
        List[:class:`twitchio.CustomReward`]
        """
        if not force and self._cached_rewards and self._cached_rewards[0] + 300 > time.monotonic():
            return self._cached_rewards[1]
        try:
            data = await self._http.get_rewards(token, self.id, only_manageable, ids)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise
        else:
            values = [CustomReward(self._http, x, self) for x in data]
            self._cached_rewards = time.monotonic(), values
            return values

    async def create_custom_reward(
        self,
        token: str,
        title: str,
        cost: int,
        prompt: Optional[str] = None,
        enabled: Optional[bool] = True,
        background_color: Optional[str] = None,
        input_required: Optional[bool] = False,
        max_per_stream: Optional[int] = None,
        max_per_user_per_stream: Optional[int] = None,
        global_cooldown: Optional[int] = None,
        redemptions_skip_queue: Optional[bool] = False,
    ) -> "CustomReward":
        """|coro|

        Creates a custom reward for the user.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:redemptions`` scope
        title: :class:`str`
            The title of the reward
        cost: :class:`int`
            The cost of the reward
        prompt: Optional[:class:`str`]
            The prompt for the reward. Defaults to None
        enabled: Optional[:class:`bool`]
            Whether the reward is enabled. Defaults to True
        background_color: Optional[:class:`str`]
            The background color of the reward. Defaults to None
        input_required: Optional[:class:`bool`]
            Whether the reward requires input. Defaults to False
        max_per_stream: Optional[:class:`int`]
            The maximum number of times the reward can be redeemed per stream. Defaults to None
        max_per_user_per_stream: Optional[:class:`int`]
            The maximum number of times the reward can be redeemed per user per stream. Defaults to None
        global_cooldown: Optional[:class:`int`]
            The global cooldown of the reward. Defaults to None
        redemptions_skip_queue: Optional[:class:`bool`]
            Whether the reward skips the queue when redeemed. Defaults to False
        """
        try:
            data = await self._http.create_reward(
                token,
                self.id,
                title,
                cost,
                prompt,
                enabled,
                background_color,
                input_required,
                max_per_stream,
                max_per_user_per_stream,
                global_cooldown,
                redemptions_skip_queue,
            )
            return CustomReward(self._http, data[0], self)
        except Unauthorized as error:
            raise Unauthorized("The given token is invalid", "", 401) from error
        except HTTPException as error:
            status = error.args[2]
            if status == 403:
                raise HTTPException(
                    "The custom reward was created by a different application, or channel points are "
                    "not available for the broadcaster (403)",
                    error.args[1],
                    403,
                ) from error
            raise

    async def fetch_bits_leaderboard(
        self,
        token: str,
        period: str = "all",
        user_id: Optional[int] = None,
        started_at: Optional[datetime.datetime] = None,
    ) -> "BitsLeaderboard":
        """|coro|

        Fetches the bits leaderboard for the channel. This requires an OAuth token with the ``bits:read`` scope.

        Parameters
        -----------
        token: :class:`str`
            the OAuth token with the ``bits:read`` scope
        period: Optional[:class:`str`]
            one of `day`, `week`, `month`, `year`, or `all`, defaults to `all`
        started_at: Optional[:class:`datetime.datetime`]
            the timestamp to start the period at. This is ignored if the period is `all`
        user_id: Optional[:class:`int`]
            the id of the user to fetch for
        """
        from .models import BitsLeaderboard

        data = await self._http.get_bits_board(token, period, str(user_id), started_at)
        return BitsLeaderboard(self._http, data)

    async def start_commercial(self, token: str, length: int) -> dict:
        """|coro|

        Starts a commercial on the channel. Requires an OAuth token with the ``channel:edit:commercial`` scope.

        Parameters
        -----------
        token: :class:`str`
            the OAuth token
        length: :class:`int`
            the length of the commercial. Should be one of `30`, `60`, `90`, `120`, `150`, `180`

        Returns
        --------
        :class:`dict` a dictionary with `length`, `message`, and `retry_after`
        """
        data = await self._http.post_commercial(token, str(self.id), length)
        return data[0]

    async def create_clip(self, token: str, has_delay=False) -> dict:
        """|coro|

        Creates a clip on the channel. Note that clips are not created instantly, so you will have to query
        :meth:`~get_clips` to confirm the clip was created. Requires an OAuth token with the ``clips:edit`` scope

        Parameters
        -----------
        token: :class:`str`
            the OAuth token
        has_delay: :class:`bool`
            Whether the clip should have a delay to match that of a viewer. Defaults to False

        Returns
        --------
        :class:`dict` a dictionary with `id` and `edit_url`
        """
        data = await self._http.post_create_clip(token, self.id, has_delay)
        return data[0]

    async def fetch_clips(
        self, started_at: Optional[datetime.datetime] = None, ended_at: Optional[datetime.datetime] = None
    ) -> List["Clip"]:
        """|coro|

        Fetches clips from the api. This will only return clips from the specified user.
        Use :class:`Client.fetch_clips` to fetch clips by id

        Parameters
        -----------
        started_at: Optional[:class:`datetime.datetime`]
            Starting date/time for returned clips.
            If this is specified, ended_at also should be specified; otherwise, the ended_at date/time will be 1 week after the started_at value.
        ended_at: Optional[:class:`datetime.datetime`]
            Ending date/time for returned clips.
            If this is specified, started_at also must be specified; otherwise, the time period is ignored.

        Returns
        --------
        List[:class:`twitchio.Clip`]
        """
        from .models import Clip

        data = await self._http.get_clips(self.id, started_at=started_at, ended_at=ended_at)

        return [Clip(self._http, x) for x in data]

    async def fetch_hypetrain_events(self, id: str = None, token: str = None):
        """|coro|

        Fetches hypetrain event from the api. Needs a token with the ``channel:read:hype_train`` scope.

        Parameters
        -----------
        id: Optional[:class:`str`]
            The hypetrain id, if known, to fetch for
        token: Optional[:class:`str`]
            The oauth token to use. Will default to the one passed to the bot/client.

        Returns
        --------
        List[:class:`twitchio.HypeTrainEvent`]
        """
        from .models import HypeTrainEvent

        data = await self._http.get_hype_train(self.id, id=id, token=token)
        return [HypeTrainEvent(self._http, d) for d in data]

    async def fetch_bans(self, token: str, userids: List[Union[str, int]] = None) -> List["UserBan"]:
        """|coro|

        Fetches a list of people the User has banned from their channel.

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the ``moderation:read`` scope.
        userids: List[Union[:class:`str`, :class:`int`]]
            An optional list of userids to fetch. Will fetch all bans if this is not passed
        """
        data = await self._http.get_channel_bans(token, str(self.id), user_ids=userids)
        return [UserBan(self._http, d) for d in data]

    async def fetch_ban_events(self, token: str, userids: List[int] = None):
        """|coro|

        This has been deprecated and will be removed in a future release.

        Fetches ban/unban events from the User's channel.

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the ``moderation:read`` scope.
        userids: List[:class:`int`]
            An optional list of users to fetch ban/unban events for

        Returns
        --------
        List[:class:`twitchio.BanEvent`]
        """
        from .models import BanEvent

        data = await self._http.get_channel_ban_unban_events(token, str(self.id), userids)
        return [BanEvent(self._http, x, self) for x in data]

    async def fetch_moderators(self, token: str, userids: List[int] = None):
        """|coro|

        Fetches the moderators for this channel.

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the ``moderation:read`` scope.
        userids: List[:class:`int`]
            An optional list of users to check mod status of

        Returns
        --------
        List[:class:`twitchio.PartialUser`]
        """
        data = await self._http.get_channel_moderators(token, str(self.id), user_ids=userids)
        return [PartialUser(self._http, d["user_id"], d["user_name"]) for d in data]

    async def fetch_mod_events(self, token: str):
        """|coro|

        Fetches mod events (moderators being added and removed) for this channel.

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the ``moderation:read`` scope.

        Returns
        --------
        List[:class:`twitchio.ModEvent`]
        """
        from .models import ModEvent

        data = await self._http.get_channel_mod_events(token, str(self.id))
        return [ModEvent(self._http, d, self) for d in data]

    async def automod_check(self, token: str, query: list):
        """|coro|

        Checks if a string passes the automod filter

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the ``moderation:read`` scope.
        query: List[:class:`AutomodCheckMessage`]
            A list of :class:`twitchio.AutomodCheckMessage`

        Returns
        --------
        List[:class:`twitchio.AutomodCheckResponse`]
        """
        from .models import AutomodCheckResponse

        data = await self._http.post_automod_check(token, str(self.id), *[x._to_dict() for x in query])
        return [AutomodCheckResponse(d) for d in data]

    async def fetch_stream_key(self, token: str):
        """|coro|

        Fetches the users stream key

        Parameters
        -----------
        token: :class:`str`
            The oauth token with the ``channel:read:stream_key`` scope

        Returns
        --------
        :class:`str`
        """
        data = await self._http.get_stream_key(token, str(self.id))
        return data

    async def fetch_following(self, token: Optional[str] = None) -> List["FollowEvent"]:
        """|coro|

        Fetches a list of users that this user is following.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token to use instead of the bots token

        Returns
        --------
        List[:class:`twitchio.FollowEvent`]
        """
        from .models import FollowEvent

        data = await self._http.get_user_follows(token=token, from_id=str(self.id))
        return [FollowEvent(self._http, d, from_=self) for d in data]

    async def fetch_followers(self, token: Optional[str] = None):
        """|coro|

        Fetches a list of users that are following this user.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token to use instead of the bots token

        Returns
        --------
        List[:class:`twitchio.FollowEvent`]
        """
        from .models import FollowEvent

        data = await self._http.get_user_follows(token=token, to_id=str(self.id))
        return [FollowEvent(self._http, d, to=self) for d in data]

    async def fetch_follow(self, to_user: "PartialUser", token: Optional[str] = None):
        """|coro|

        Check if a user follows another user or when they followed a user.

        Parameters
        -----------
        to_user: :class:`PartialUser`
        token: Optional[:class:`str`]
            An oauth token to use instead of the bots token

        Returns
        --------
        :class:`twitchio.FollowEvent`
        """
        if not isinstance(to_user, PartialUser):
            raise TypeError(f"to_user must be a PartialUser not {type(to_user)}")
        from .models import FollowEvent

        data = await self._http.get_user_follows(token=token, from_id=str(self.id), to_id=str(to_user.id))
        return FollowEvent(self._http, data[0]) if data else None

    async def fetch_follower_count(self, token: Optional[str] = None) -> int:
        """|coro|

        Fetches a list of users that are following this user.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token to use instead of the bots token

        Returns
        --------
        :class:`int`
        """

        data = await self._http.get_follow_count(token=token, to_id=str(self.id))
        return data["total"]

    async def fetch_following_count(self, token: Optional[str] = None) -> int:
        """|coro|

        Fetches a list of users that this user is following.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token to use instead of the bots token

        Returns
        --------
        :class:`int`
        """
        data = await self._http.get_follow_count(token=token, from_id=str(self.id))
        return data["total"]

    async def fetch_channel_emotes(self):
        """|coro|

        Fetches channel emotes from the user

        Returns
        --------
        List[:class:`twitchio.ChannelEmote`]
        """
        from .models import ChannelEmote

        data = await self._http.get_channel_emotes(str(self.id))
        return [ChannelEmote(self._http, x) for x in data]

    async def follow(self, userid: int, token: str, *, notifications=False):
        """|coro|

        Follows the user

        Parameters
        -----------
        userid: :class:`int`
            The user id to follow this user with
        token: :class:`str`
            An oauth token with the ``user:edit:follows`` scope
        notifications: :class:`bool`
            Whether to allow push notifications when this user goes live. Defaults to False
        """
        await self._http.post_follow_channel(
            token, from_id=str(userid), to_id=str(self.id), notifications=notifications
        )

    async def unfollow(self, userid: int, token: str):
        """|coro|

        Unfollows the user

        Parameters
        -----------
        userid: :class:`int`
            The user id to unfollow this user with
        token: :class:`str`
            An oauth token with the ``user:edit:follows`` scope
        """
        await self._http.delete_unfollow_channel(token, from_id=str(userid), to_id=str(self.id))

    async def fetch_subscriptions(self, token: str, userids: Optional[List[int]] = None):
        """|coro|

        Fetches the subscriptions for this channel.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:read:subscriptions`` scope
        userids: Optional[List[:class:`int`]]
            An optional list of userids to look for

        Returns
        --------
        List[:class:`twitchio.SubscriptionEvent`]
        """
        from .models import SubscriptionEvent

        data = await self._http.get_channel_subscriptions(token, str(self.id), user_ids=userids)
        return [SubscriptionEvent(self._http, d, broadcaster=self) for d in data]

    async def create_marker(self, token: str, description: str = None):
        """|coro|

        Creates a marker on the stream. This only works if the channel is live (among other conditions)

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``user:edit:broadcast`` scope
        description: :class:`str`
            An optional description of the marker

        Returns
        --------
        :class:`twitchio.Marker`
        """
        from .models import Marker

        data = await self._http.post_stream_marker(token, user_id=str(self.id), description=description)
        return Marker(data[0])

    async def fetch_markers(self, token: str, video_id: str = None):
        """|coro|

        Fetches markers from the given video id, or the most recent video.
        The Twitch api will only return markers created by the user of the authorized token

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``user:edit:broadcast`` scope
        video_id: :class:`str`
            A specific video o fetch from. Defaults to the most recent stream if not passed

        Returns
        --------
        Optional[:class:`twitchio.VideoMarkers`]
        """
        from .models import VideoMarkers

        data = await self._http.get_stream_markers(token, user_id=str(self.id), video_id=video_id)
        if data:
            return VideoMarkers(data[0]["videos"])

    async def fetch_extensions(self, token: str):
        """|coro|

        Fetches extensions the user has (active and inactive)

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``user:read:broadcast`` scope

        Returns
        --------
        List[:class:`twitchio.Extension`]
        """
        from .models import Extension

        data = await self._http.get_channel_extensions(token)
        return [Extension(d) for d in data]

    async def fetch_active_extensions(self, token: str = None):
        """|coro|

        Fetches active extensions the user has.
        Returns a dictionary containing the following keys: `panel`, `overlay`, `component`.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token with the ``user:read:broadcast`` *or* ``user:edit:broadcast`` scope

        Returns
        --------
        Dict[:class:`str`, Dict[:class:`int`, :class:`twitchio.ActiveExtension`]]
        """
        from .models import ActiveExtension

        data = await self._http.get_user_active_extensions(token, str(self.id))
        return {typ: {int(n): ActiveExtension(d) for n, d in vals.items()} for typ, vals in data.items()}

    async def update_extensions(self, token: str, extensions: "ExtensionBuilder"):
        """|coro|

        Updates a users extensions. See the :class:`twitchio.ExtensionBuilder`

        Parameters
        -----------
        token: :class:`str`
            An oauth token with ``user:edit:broadcast`` scope
        extensions: :class:`twitchio.ExtensionBuilder`
            A :class:`twitchio.ExtensionBuilder` to be given to the twitch api

        Returns
        --------
        Dict[:class:`str`, Dict[:class:`int`, :class:`twitchio.ActiveExtension`]]
        """
        from .models import ActiveExtension

        data = await self._http.put_user_extensions(token, extensions._to_dict())
        return {typ: {int(n): ActiveExtension(d) for n, d in vals.items()} for typ, vals in data.items()}

    async def fetch_videos(self, period="all", sort="time", type="all", language=None):
        """|coro|

        Fetches videos that belong to the user. If you have specific video ids use :func:`Client.fetch_videos`

        Parameters
        -----------
        period: :class:`str`
            The period for which to fetch videos. Valid values are `all`, `day`, `week`, `month`. Defaults to `all`
        sort: :class:`str`
            Sort orders of the videos. Valid values are `time`, `trending`, `views`, Defaults to `time`
        type: Optional[:class:`str`]
            Type of the videos to fetch. Valid values are `upload`, `archive`, `highlight`. Defaults to `all`
        language: Optional[:class:`str`]
            Language of the videos to fetch. Must be an `ISO-639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ two letter code.

        Returns
        --------
        List[:class:`twitchio.Video`]
        """
        from .models import Video

        data = await self._http.get_videos(user_id=str(self.id), period=period, sort=sort, type=type, language=language)
        return [Video(self._http, x, self) for x in data]

    async def end_prediction(
        self, token: str, prediction_id: str, status: str, winning_outcome_id: Optional[str] = None
    ) -> "Prediction":
        """|coro|

        End a prediction with an outcome.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:predictions`` scope
        prediction_id: :class:`str`
            ID of the prediction to end.
        status: :class:`str`
            Status of the prediction. Valid values are:
            RESOLVED - Winning outcome has been choson and points distributed.
            CANCELED - Prediction canceled and points refunded
            LOCKED - Viewers can no longer make predictions.
        winning_outcome_id: Optional[:class:`str`]
            ID of the winning outcome. This is required if status is RESOLVED

        Returns
        --------
        :class:`twitchio.Prediction`
        """
        from .models import Prediction

        data = await self._http.patch_prediction(
            token,
            broadcaster_id=str(self.id),
            prediction_id=prediction_id,
            status=status,
            winning_outcome_id=winning_outcome_id,
        )
        return Prediction(self._http, data[0])

    async def get_predictions(self, token: str, prediction_id: str = None) -> List["Prediction"]:
        """|coro|

        Gets information on a prediction or the list of predictions
        if none is provided.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:predictions`` scope
        prediction_id: :class:`str`
            ID of the prediction to receive information about.

        Returns
        --------
        :class:`twitchio.Prediction`
        """
        from .models import Prediction

        data = await self._http.get_predictions(token, broadcaster_id=str(self.id), prediction_id=prediction_id)
        return [Prediction(self._http, d) for d in data]

    async def create_prediction(
        self, token: str, title: str, blue_outcome: str, pink_outcome: str, prediction_window: int
    ) -> "Prediction":
        """|coro|

        Creates a prediction for the channel.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:predictions`` scope
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
        from .models import Prediction

        data = await self._http.post_prediction(
            token,
            broadcaster_id=str(self.id),
            title=title,
            blue_outcome=blue_outcome,
            pink_outcome=pink_outcome,
            prediction_window=prediction_window,
        )
        return Prediction(self._http, data[0])

    async def modify_stream(self, token: str, game_id: int = None, language: str = None, title: str = None):
        """|coro|

        Modify stream information

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:broadcast`` scope
        game_id: :class:`int`
            Optional game ID being played on the channel. Use 0 to unset the game.
        language: :class:`str`
            Optional language of the channel. A language value must be either the ISO 639-1 two-letter code for a supported stream language or “other”.
        title: :class:`str`
            Optional title of the stream.
        """
        if game_id is not None:
            game_id = str(game_id)
        await self._http.patch_channel(
            token,
            broadcaster_id=str(self.id),
            game_id=game_id,
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
        from .models import Schedule

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
        from .models import ChannelTeams

        data = await self._http.get_channel_teams(
            broadcaster_id=str(self.id),
        )

        return [ChannelTeams(self._http, x) for x in data["data"]] if data["data"] else []

    async def fetch_polls(self, token: str, poll_ids: Optional[List[str]] = None, first: Optional[int] = 20):
        """|coro|

        Fetches a list of polls for the specified channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:read:polls`` scope
        poll_ids: Optional[List[:class:`str`]]
            List of poll IDs to return. Maximum: 100
        first: Optional[:class:`int`]
            Number of polls to return. Maximum: 20. Default: 20.

        Returns
        --------
        List[:class:`twitchio.Poll`]
        """
        from .models import Poll

        data = await self._http.get_polls(broadcaster_id=str(self.id), token=token, poll_ids=poll_ids, first=first)
        return [Poll(self._http, x) for x in data["data"]] if data["data"] else []

    async def create_poll(
        self,
        token: str,
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
        token: :class:`str`
            An oauth token with the ``channel:manage:polls`` scope.
            User ID in token must match the broadcaster's ID.
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
        from .models import Poll

        data = await self._http.post_poll(
            broadcaster_id=str(self.id),
            token=token,
            title=title,
            choices=choices,
            duration=duration,
            bits_voting_enabled=bits_voting_enabled,
            bits_per_vote=bits_per_vote,
            channel_points_voting_enabled=channel_points_voting_enabled,
            channel_points_per_vote=channel_points_per_vote,
        )
        return Poll(self._http, data[0])

    async def end_poll(self, token: str, poll_id: str, status: str):
        """|coro|

        Ends a poll for the specified channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:polls`` scope
        poll_id: :class:`str`
            ID of the poll.
        status: :class:`str`
            The poll status to be set. Valid values:
            TERMINATED: End the poll manually, but allow it to be viewed publicly.
            ARCHIVED: End the poll manually and do not allow it to be viewed publicly.

        Returns
        --------
        :class:`twitchio.Poll`
        """
        from .models import Poll

        data = await self._http.patch_poll(broadcaster_id=str(self.id), token=token, id=poll_id, status=status)
        return Poll(self._http, data[0])

    async def fetch_goals(self, token: str):
        """|coro|

        Fetches a list of goals for the specified channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:read:goals`` scope

        Returns
        --------
        List[:class:`twitchio.Goal`]
        """
        from .models import Goal

        data = await self._http.get_goals(broadcaster_id=str(self.id), token=token)
        return [Goal(self._http, x) for x in data]

    async def fetch_chat_settings(self, token: Optional[str] = None, moderator_id: Optional[int] = None):
        """|coro|

        Fetches the current chat settings for this channel/broadcaster.

        Parameters
        -----------
        token: Optional[:class:`str`]
            An oauth token with the ``moderator:read:chat_settings`` scope. Required if moderator_id is provided.
        moderator_id: Optional[:class:`int`]
            The ID of a user that has permission to moderate the broadcaster's chat room.
            Requires ``moderator:read:chat_settings`` scope.

        Returns
        --------
        :class:`twitchio.ChatSettings`
        """
        from .models import ChatSettings

        data = await self._http.get_chat_settings(
            broadcaster_id=str(self.id), moderator_id=str(moderator_id), token=token
        )
        return ChatSettings(self._http, data[0])

    async def update_chat_settings(
        self,
        token: str,
        moderator_id: int,
        emote_mode: Optional[bool] = None,
        follower_mode: Optional[bool] = None,
        follower_mode_duration: Optional[int] = None,
        slow_mode: Optional[bool] = None,
        slow_mode_wait_time: Optional[int] = None,
        subscriber_mode: Optional[bool] = None,
        unique_chat_mode: Optional[bool] = None,
        non_moderator_chat_delay: Optional[bool] = None,
        non_moderator_chat_delay_duration: Optional[int] = None,
    ):
        """|coro|

        Updates the current chat settings for this channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``moderator:manage:chat_settings`` scope.
        moderator_id: :class:`int`
            The ID of a user that has permission to moderate the broadcaster's chat room.
            Requires ``moderator:manage:chat_settings`` scope.
        emote_mode: Optional[:class:`bool`]
            A boolean to determine whether chat must contain only emotes or not.
        follower_mode: Optional[:class:`bool`]
            A boolean to determine whether chat must contain only emotes or not.
        follower_mode_duration: Optional[:class:`int`]
            The length of time, in minutes, that the followers must have followed the broadcaster to participate in chat.
            Values: 0 (no restriction) through 129600 (3 months). The default is 0.
        slow_mode: Optional[:class:`bool`]
            A boolean to determine whether the broadcaster limits how often users in the chat room are allowed to send messages.
        slow_mode_wait_time: Optional[:class:`int`]
            The amount of time, in seconds, that users need to wait between sending messages.
            Values: 3 through 120 (2 minute delay). The default is 30 seconds.
        subscriber_mode: Optional[:class:`bool`]
            A boolean to determine whether only users that subscribe to the broadcaster's channel can talk in chat.
        unique_chat_mode: Optional[:class:`bool`]
            A boolean to determine whether the broadcaster requires users to post only unique messages in chat.
        non_moderator_chat_delay: Optional[:class:`bool`]
            A boolean to determine whether the broadcaster adds a short delay before chat messages appear in chat.
        non_moderator_chat_delay_duration: Optional[:class:`int`]
            The amount of time, in seconds, that messages are delayed from appearing in chat.
            Valid values: 2, 4 and 6.

        Returns
        --------
        :class:`twitchio.ChatSettings`
        """
        from .models import ChatSettings

        data = await self._http.patch_chat_settings(
            broadcaster_id=str(self.id),
            moderator_id=str(moderator_id),
            token=token,
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
        return ChatSettings(self._http, data[0])

    async def chat_announcement(self, token: str, moderator_id: int, message: str, color: Optional[str] = "primary"):
        """|coro|

        Sends a chat announcement to the specified channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``moderator:manage:chat_settings`` scope.
        moderator_id: :class:`int`
            The ID of a user that has permission to moderate the broadcaster's chat room.
            Requires ``moderator:manage:announcements`` scope.
        message: :class:`str`
            The message to be sent.
        color: Optional[:class:`str`]
            The color of the message. Valid values:
            blue, green orange, pruple. The default is primary.
        Returns
        --------
        None
        """
        await self._http.post_chat_announcement(
            broadcaster_id=str(self.id),
            moderator_id=str(moderator_id),
            token=token,
            message=message,
            color=color,
        )

    async def delete_chat_messages(self, token: str, moderator_id: int, message_id: Optional[str] = None):
        """|coro|

        Deletes a chat message, or clears chat, in the specified channel/broadcaster's chat.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``moderator:manage:chat_settings`` scope.
        moderator_id: :class:`int`
            The ID of a user that has permission to moderate the broadcaster's chat room.
            Requires ``moderator:manage:chat_messages`` scope.
        message_id: Optional[:class:`str`]
            The ID of the message to be deleted.
            The message must have been created within the last 6 hours.
            The message must not belong to the broadcaster.
            If not specified, the request removes all messages in the broadcaster's chat room.

        Returns
        --------
        None
        """
        await self._http.delete_chat_messages(
            broadcaster_id=str(self.id), token=token, moderator_id=str(moderator_id), message_id=message_id
        )

    async def fetch_channel_vips(self, token: str, first: int = 20, user_ids: Optional[List[int]] = None):
        """|coro|

        Fetches the list of VIPs for the specified channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:read:vips`` or ``moderator:manage:chat_settings`` scope.
            Must be the broadcaster's token.
        first: Optional[:class:`int`]
            The maximum number of items to return per page in the response.
            The minimum page size is 1 item per page and the maximum is 100. The default is 20.
        user_ids: Optional[List[:class:`int`]]
            A list of user IDs to filter the results by.
            The maximum number of IDs that you may specify is 100. Ignores those users in the list that aren't VIPs.

        Returns
        --------
        List[:class:`twitchio.PartialUser`]
        """

        data = await self._http.get_channel_vips(
            broadcaster_id=str(self.id), token=token, first=first, user_ids=user_ids
        )
        return [PartialUser(self._http, x["user_id"], x["user_login"]) for x in data]

    async def add_channel_vip(self, token: str, user_id: int):
        """|coro|

        Adds a VIP to the specified channel/broadcaster.
        The channel may add a maximum of 10 VIPs within a 10 seconds period.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:vips scope``.
            Must be the broadcaster's token.
        user_id: :class:`int`
            The ID of the user to add as a VIP.

        Returns
        --------
        None
        """
        await self._http.post_channel_vip(broadcaster_id=str(self.id), token=token, user_id=str(user_id))

    async def remove_channel_vip(self, token: str, user_id: int):
        """|coro|

        Removes a VIP from the specified channel/broadcaster.
        The channel may remove a maximum of 10 vips within a 10 seconds period.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:vips`` scope.
            Must be the broadcaster's token.
        user_id: :class:`int`
            The ID of the user to remove as a VIP.

        Returns
        --------
        None
        """
        await self._http.delete_channel_vip(broadcaster_id=str(self.id), token=token, user_id=str(user_id))

    async def add_channel_moderator(self, token: str, user_id: int):
        """|coro|

        Adds a moderator to the specified channel/broadcaster.
        The channel may add a maximum of 10 moderators within a 10 seconds period.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:moderators`` scope.
            Must be the broadcaster's token.
        user_id: :class:`str`
            The ID of the user to add as a moderator.

        Returns
        --------
        None
        """
        await self._http.post_channel_moderator(broadcaster_id=str(self.id), token=token, user_id=str(user_id))

    async def remove_channel_moderator(self, token: str, user_id: int):
        """|coro|

        Removes a moderator from the specified channel/broadcaster.
        The channel may remove a maximum of 10 moderators within a 10 seconds period.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:moderators`` scope.
            Must be the broadcaster's token.
        user_id: :class:`str`
            The ID of the user to remove as a moderator.

        Returns
        --------
        None
        """
        await self._http.delete_channel_moderator(broadcaster_id=str(self.id), token=token, user_id=str(user_id))

    async def start_raid(self, token: str, to_broadcaster_id: int):
        """|coro|

        Starts a raid for the channel/broadcaster.
        The UTC date and time, in RFC3339 format, when the raid request was created.
        A Boolean value that indicates whether the channel being raided contains mature content.

        Rate Limit: The limit is 10 requests within a 10-minute window.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:raids`` scope
            Must be the broadcaster's token.
        to_broadcaster_id: :class:`int`
            The ID of the broadcaster to raid.

        Returns
        --------
        :class:`twitchio.Raid`
        """

        data = await self._http.post_raid(
            from_broadcaster_id=str(self.id), token=token, to_broadcaster_id=str(to_broadcaster_id)
        )

        from .models import Raid

        return Raid(data[0])

    async def cancel_raid(self, token: str):
        """|coro|

        Cancels a raid for the channel/broadcaster.
        The limit is 10 requests within a 10-minute window.

        Parameters
        -----------
        token: :class:`str`
            An oauth token with the ``channel:manage:raids`` scope
            Must be the broadcaster's token.

        Returns
        --------
        None
        """

        await self._http.delete_raid(broadcaster_id=str(self.id), token=token)

    async def ban_user(self, token: str, moderator_id: int, user_id, reason: str):
        """|coro|

        Bans a user from the channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth user access token with the ``moderator:manage:banned_users`` scope
        moderator_id: :class:`int`
            The ID of a user that has permission to moderate the broadcaster's chat room.
            If the broadcaster wants to ban the user set this parameter to the broadcaster's ID.
        user_id: :class:`int`
            The ID of the user to ban.
        reason: :class:`str`
            The reason for the ban.

        Returns
        --------
        :class:`twitchio.Ban`
        """
        from .models import Ban

        data = await self._http.post_ban_timeout_user(
            broadcaster_id=str(self.id),
            moderator_id=str(moderator_id),
            user_id=str(user_id),
            reason=reason,
            token=token,
        )
        return Ban(self._http, data[0])

    async def timeout_user(self, token: str, moderator_id: int, user_id: int, duration: int, reason: str):
        """|coro|

        Timeouts a user from the channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth user access token with the ``moderator:manage:banned_users`` scope
        moderator_id: :class:`int`
            The ID of a user that has permission to moderate the broadcaster's chat room.
            If the broadcaster wants to timeout the user set this parameter to the broadcaster's ID.
        user_id: :class:`int`
            The ID of the user that you wish to timeout.
        duration: :class:`int`
            The duration of the timeout in seconds.
            The minimum timeout is 1 second and the maximum is 1,209,600 seconds (2 weeks).
            To end a user's timeout early, set this field to 1, or send an Unban user request.
        reason: :class:`str`
            The reason for the timeout.

        Returns
        --------
        :class:`twitchio.Timeout`
        """
        from .models import Timeout

        data = await self._http.post_ban_timeout_user(
            broadcaster_id=str(self.id),
            moderator_id=str(moderator_id),
            user_id=str(user_id),
            duration=duration,
            reason=reason,
            token=token,
        )
        return Timeout(self._http, data[0])

    async def unban_user(self, token: str, moderator_id: int, user_id):
        """|coro|

        Unbans a user or removes a timeout from the channel/broadcaster.

        Parameters
        -----------
        token: :class:`str`
            An oauth user access token with the ``moderator:manage:banned_users`` scope
        moderator_id: :class:`int`
            The ID of a user that has permission to moderate the broadcaster's chat room.
            If the broadcaster wants to ban the user set this parameter to the broadcaster's ID.
        user_id: :class:`int`
            The ID of the user to unban.

        Returns
        --------
        None
        """

        await self._http.delete_ban_timeout_user(
            broadcaster_id=str(self.id),
            moderator_id=str(moderator_id),
            user_id=str(user_id),
            token=token,
        )

    async def send_whisper(self, token: str, user_id: int, message: str):
        """|coro|

        Sends a whisper to a user.
        Important Notes:
        - The user sending the whisper must have a verified phone number.
        - The API may silently drop whispers that it suspects of violating Twitch policies.
        - You may whisper to a maximum of 40 unique recipients per day. Within the per day limit.
        - You may whisper a maximum of 3 whispers per second and a maximum of 100 whispers per minute.

        Parameters
        -----------
        token: :class:`str`
            An oauth user token with the ``user:manage:whispers`` scope.
        user_id: :class:`int`
            The ID of the user to send the whisper to.
        message: :class:`str`
            The message to send.
            500 characters if the user you're sending the message to hasn't whispered you before.
            10,000 characters if the user you're sending the message to has whispered you before.

        Returns
        --------
        None
        """

        await self._http.post_whisper(token=token, from_user_id=str(self.id), to_user_id=str(user_id), message=message)

    async def fetch_shield_mode_status(self, token: str, moderator_id: int):
        """|coro|

        Fetches the user's Shield Mode activation status.

        Parameters
        -----------
        token: :class:`str`
            An oauth user token with the ``moderator:read:shield_mode`` or ``moderator:manage:shield_mode`` scope.
        moderator_id: :class:`int`
            The ID of the broadcaster or a user that is one of the broadcaster's moderators. This ID must match the user ID in the access token.

        Returns
        --------
        :class:`twitchio.ShieldStatus`
        """
        from .models import ShieldStatus

        data = await self._http.get_shield_mode_status(
            broadcaster_id=str(self.id), moderator_id=str(moderator_id), token=token
        )

        return ShieldStatus(self._http, data[0])

    async def update_shield_mode_status(self, token: str, moderator_id: int, is_active: bool):
        """|coro|

        Updates the user's Shield Mode activation status.

        Parameters
        -----------
        token: :class:`str`
            An oauth user token with the ``moderator:read:shield_mode`` or ``moderator:manage:shield_mode`` scope.
        moderator_id: :class:`int`
            The ID of the broadcaster or a user that is one of the broadcaster's moderators. This ID must match the user ID in the access token.
        is_active: :class:`bool`
            A Boolean value that determines whether to activate Shield Mode. Set to True to activate Shield Mode; otherwise, False to deactivate Shield Mode.

        Returns
        --------
        :class:`twitchio.ShieldStatus`
        """
        from .models import ShieldStatus

        data = await self._http.put_shield_mode_status(
            broadcaster_id=str(self.id), moderator_id=str(moderator_id), is_active=is_active, token=token
        )

        return ShieldStatus(self._http, data[0])

    async def fetch_followed_streams(self, token: str):
        """|coro|

        Fetches a list of broadcasters that the user follows and that are streaming live.

        Parameters
        -----------
        token: :class:`str`
            An oauth user token with the ``user:read:follows`` scope.

        Returns
        --------
        List[:class:`twitchio.Stream`]
        """

        data = await self._http.get_followed_streams(broadcaster_id=str(self.id), token=token)

        from .models import Stream

        return [Stream(self._http, x) for x in data]

    async def shoutout(self, token: str, to_broadcaster_id: int, moderator_id: int):
        """|coro|
        Sends a Shoutout to the specified broadcaster.
        ``Rate Limits``: The broadcaster may send a Shoutout once every 2 minutes. They may send the same broadcaster a Shoutout once every 60 minutes.
        Requires a user access token that includes the ``moderator:manage:shoutouts`` scope.

        Parameters
        -----------
        token: :class:`str`
            An oauth user token with the ``moderator:manage:shoutouts`` scope.
        to_broadcaster: :class:`int`
            The ID of the broadcaster that is recieving the shoutout.
        moderator_id: :class:`int`
            The ID of the broadcaster or a user that is one of the broadcaster's moderators. This ID must match the user ID in the access token.

        Returns
        --------
        None
        """

        await self._http.post_shoutout(
            token=token,
            broadcaster_id=str(self.id),
            to_broadcaster_id=str(to_broadcaster_id),
            moderator_id=str(moderator_id),
        )


class BitLeaderboardUser(PartialUser):
    __slots__ = "rank", "score"

    def __init__(self, http: "TwitchHTTP", data: dict):
        super(BitLeaderboardUser, self).__init__(http, id=data["user_id"], name=data["user_name"])
        self.rank: int = data["rank"]
        self.score: int = data["score"]


class UserBan(PartialUser):
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

    def __init__(self, http: "TwitchHTTP", data: dict):
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
    """
    Represents a User that has been searched for.

    Attributes
    ----------
    id: :class:`int`
        The ID of the user.
    name: :class:`str`
        The name of the user.
    display_name: :class:`str`
        The broadcaster's display name.
    game_id: :class:`str`
        The ID of the game that the broadcaster is playing or last played.
    title: :class:`str`
        The stream's title. Is an empty string if the broadcaster didn't set it.
    thumbnail_url :class:`str`
        A URL to a thumbnail of the broadcaster's profile image.
    language :class:`str`
        The ISO 639-1 two-letter language code of the language used by the broadcaster. For example, en for English.
    live: :class:`bool`
        A Boolean value that determines whether the broadcaster is streaming live. Is true if the broadcaster is streaming live; otherwise, false.
    started_at: :class:`datetime.datetime`
        The UTC date and time of when the broadcaster started streaming.
    tag_ids: List[:class:`str`]
        Tag IDs that apply to the stream.

        .. warning::

            This field will be deprecated by twitch in 2023.

    tags: List[:class:`str`]
        The tags applied to the channel.
    """

    __slots__ = (
        "game_id",
        "name",
        "display_name",
        "language",
        "title",
        "thumbnail_url",
        "live",
        "started_at",
        "tag_ids",
        "tags",
    )

    def __init__(self, http: "TwitchHTTP", data: dict):
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
        self.tags: List[str] = data["tags"]


class User(PartialUser):
    """
    A full user object, containing data from the users endpoint.

    Attributes
    -----------
    id: :class:`int`
        The user's ID
    name: :class:`str`
        The user's login name
    display_name: :class:`str`
        The name that is displayed in twitch chat. For the most part, this is simply a change of capitalization
    type: :class:`~twitchio.UserTypeEnum`
        The user's type. This will normally be :class:`~twitchio.UserTypeEnum.none`, unless they are twitch staff or admin
    broadcaster_type: :class:`~twitchio.BroadcasterTypeEnum`
        What type of broacaster the user is. none, affiliate, or partner
    description: :class:`str`
        The user's bio
    profile_image: :class:`str`
        The user's profile image URL
    offline_image: :class:`str`
        The user's offline image splash URL
    view_count: Tuple[int]
        The amount of views this channel has

        .. warning::

            This field has been deprecated by twitch, and is no longer updated.
            See `here <https://discuss.dev.twitch.tv/t/get-users-api-endpoint-view-count-deprecation/37777>`_ for more information.

        .. note::

            This field is a tuple due to a mistake when creating the models.
            Due to semver principals, this cannot be fixed until version 3.0 (at which time we will be removing the field entirely).
    created_at: :class:`datetime.datetime`
        When the user created their account
    email: Optional[class:`str`]
        The user's email. This is only returned if you have the ``user:read:email`` scope on the token used to make the request
    """

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

    def __init__(self, http: "TwitchHTTP", data: dict):
        self._http = http
        self.id = int(data["id"])
        self.name: str = data["login"]
        self.display_name: str = data["display_name"]
        self.type = UserTypeEnum(data["type"])
        self.broadcaster_type = BroadcasterTypeEnum(data["broadcaster_type"])
        self.description: str = data["description"]
        self.profile_image: str = data["profile_image_url"]
        self.offline_image: str = data["offline_image_url"]
        self.view_count: Tuple[int] = (
            data.get("view_count", 0),
        )  # this isn't supposed to be a tuple but too late to fix it!
        self.created_at = parse_timestamp(data["created_at"])
        self.email: Optional[str] = data.get("email")
        self._cached_rewards = None

    def __repr__(self):
        return f"<User id={self.id} name={self.name} display_name={self.display_name} type={self.type}>"
