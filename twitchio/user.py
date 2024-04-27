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

from typing import TYPE_CHECKING

from .models_test.channel_points import CustomReward


if TYPE_CHECKING:
    from .http import HTTPClient
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

    async def fetch_custom_rewards(
        self, *, token_for: str, ids: list[str] | None = None, manageable: bool = False
    ) -> list[CustomReward]:
        data = await self._http.get_custom_reward(
            broadcaster_id=self.id, reward_ids=ids, manageable=manageable, token_for=token_for
        )
        return [CustomReward(d, broadcaster=self, http=self._http) for d in data["data"]]

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
        return CustomReward(data["data"][0], broadcaster=self, http=self._http)
