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

from twitchio.assets import Asset
from twitchio.user import PartialUser
from twitchio.utils import Colour


if TYPE_CHECKING:
    from twitchio.http import HTTPAsyncIterator, HTTPClient
    from twitchio.types_.responses import (
        ChannelChatBadgesResponseData,
        ChannelChatBadgesResponseVersions,
        ChattersResponse,
        EmoteSetsResponseData,
        GlobalChatBadgesResponseData,
        GlobalChatBadgesResponseVersions,
        GlobalEmotesResponseData,
        GlobalEmotesResponseImages,
        UserChatColorResponseData,
        UserEmotesResponseData,
    )


__all__ = ("Chatters", "ChatterColor", "ChatBadge", "ChatBadgeVersions", "EmoteSet", "GlobalEmote")


class Chatters:
    """
    Represents a channel's chatters.

    Returns
    -------
    users: HTTPAsyncIterator[PartialUser]
        The PartialUser object of the chatter.
    total: int
        The the total number of users that are connected to the chat room. This may vary as your iterate through pages.
    """

    def __init__(self, iterator: HTTPAsyncIterator[PartialUser], data: ChattersResponse) -> None:
        self.users: HTTPAsyncIterator[PartialUser] = iterator
        self.total: int = data["total"]

    def __repr__(self) -> str:
        return f"<Chatters total={self.total}>"


class ChatterColor:
    """
    Represents chatters current name color.

    Attributes
    -----------
    user: twitchio.PartialUser
        PartialUser of the chatter.
    color: str
        The hex color code of the chatter's name.
    """

    __slots__ = ("user", "_colour")

    def __init__(self, data: UserChatColorResponseData, *, http: HTTPClient) -> None:
        self.user = PartialUser(data["user_id"], data["user_login"], http=http)
        self._colour: Colour = Colour.from_hex(data["color"])

    def __repr__(self) -> str:
        return f"<ChatterColor user={self.user} color={self.colour}>"

    @property
    def colour(self) -> Colour:
        return self._colour

    color = colour

    def __str__(self) -> str:
        return self._colour.hex


class ChatBadge:
    """
    Represents chat badges.

    Attributes
    -----------
    set_id: str
        An ID that identifies this set of chat badges. For example, Bits or Subscriber.
    versions: list[ChatBadgeVersions]
        The list of chat badges in this set.
    """

    __slots__ = ("set_id", "versions", "_http")

    def __init__(self, data: GlobalChatBadgesResponseData | ChannelChatBadgesResponseData, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.set_id: str = data["set_id"]
        self.versions: list[ChatBadgeVersions] = [
            ChatBadgeVersions(version_data, self._http) for version_data in data["versions"]
        ]

    def __repr__(self) -> str:
        return f"<ChatBadge set_id={self.set_id} versions={self.versions}>"


class ChatBadgeVersions:
    """
    Represents the different versions of the chat badge.

    Attributes
    -----------
    id: str
        An ID that identifies this version of the badge. The ID can be any value.
    image_url_1x: str
        URL to the small version (18px x 18px) of the badge.
    image_url_2x: str
        URL to the medium version (36px x 36px) of the badge.
    image_url_4x: str
        URL to the large version (72px x 72px) of the badge.
    title: str
        The title of the badge.
    description: str
        The description of the badge.
    click_action: str | None
        The action to take when clicking on the badge. This can be None if no action is specified
    click_url: str | None
        The URL to navigate to when clicking on the badge. This can be None if no URL is specified.
    """

    __slots__ = (
        "id",
        "image_url_1x",
        "image_url_2x",
        "image_url_4x",
        "title",
        "description",
        "click_url",
        "click_action",
        "_http",
    )

    def __init__(
        self, data: ChannelChatBadgesResponseVersions | GlobalChatBadgesResponseVersions, http: HTTPClient
    ) -> None:
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.image_url_1x: str = data["image_url_1x"]
        self.image_url_2x: str = data["image_url_2x"]
        self.image_url_4x: str = data["image_url_4x"]
        self.title: str = data["title"]
        self.description: str = data["description"]
        self.click_action: str | None = data.get("click_action")
        self.click_url: str | None = data.get("click_url")

    def __repr__(self) -> str:
        return f"<ChatBadgeVersions id={self.id} title={self.title}>"

    def get_image(self, scale: Literal["1x", "2x", "4x"] = "2x") -> Asset:
        """
        Retrieves an Asset object for the chat badge image at the specified scale.

        Parameters
        ----------
        scale: str
            The scale (size) of the emote. Usually this will be one of:
            - "1x" (Small)
            - "2x" (Medium)
            - "4x" (Large)

            Defaults is "2x".

        Example
        --------
        ```py
            chat_badges: list[twitchio.ChatBadge] = await client.fetch_global_chat_badges()
            chat_badge: twitchio.ChatBadge = chat_badges[0]

            # Get and save the chat badge asset as an image
            asset: twitchio.Asset = await emote.get_image()
            await asset.save()
        ```

        Returns
        -------
        twitchio.Asset
            The [`Asset`][twitchio.Asset] for the chat badge.
            You can use the asset to [`.read`][twitchio.Asset.read] or [`.save`][twitchio.Asset.save] the chat badge image or
            return the generated URL with [`.url`][twitchio.Asset.url].
        """
        if scale == "1x":
            return Asset(self.image_url_1x, http=self._http, dimensions=(18, 18))
        elif scale == "2x":
            return Asset(self.image_url_2x, http=self._http, dimensions=(36, 36))
        elif scale == "4x":
            return Asset(self.image_url_4x, http=self._http, dimensions=(72, 72))
        else:
            raise ValueError(f"Invalid scale '{scale}'. Allowed values are '1x', '2x', '4x'.")


class GlobalEmote:
    """
    Represents a Global Emote

    Attributes
    -----------
    id: str
        The ID of the emote.
    name: str
        The name of the emote.
    images: dict[str, str]
        Contains the image URLs for the emote. These image URLs will always provide a static (i.e., non-animated) emote image with a light background.
    format: list[str]
        The formats that the emote is available in.
    scale: list[str]
        The sizes that the emote is available in.
    theme_mode: list[str]
        The background themes that the emote is available in.
    """

    __slots__ = ("_http", "id", "name", "images", "format", "scale", "theme_mode", "template", "_data")

    def __init__(self, data: GlobalEmotesResponseData, *, template: str, http: HTTPClient) -> None:
        self._data = data
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.images: GlobalEmotesResponseImages = data["images"]
        self.format: list[str] = data["format"]
        self.scale: list[str] = data["scale"]
        self.theme_mode: list[str] = data["theme_mode"]
        self.template: str = template

    def __repr__(self) -> str:
        return f"<GlobalEmote id={self.id} name={self.name}"

    def get_image(
        self,
        *,
        theme: Literal["light", "dark"] = "light",
        scale: str = "2.0",
        format: Literal["default", "static", "animated"] = "default",
    ) -> Asset:
        """
        Creates an [`Asset`][twitchio.Asset] for the emote, which can be used to download/save the emote image.

        Parameters
        ----------
        theme: Literal["light", "dark"]
            The background theme of the emote. Defaults to "light".
        scale: str
            The scale (size) of the emote. Usually this will be one of:
            - "1.0" (Small)
            - "2.0" (Medium)
            - "3.0" (Large)

            Defaults to "2.0".
        format: Literal["default", "static", "animated"]
            The format of the image for the emote. E.g a static image (PNG) or animated (GIF).

            Use "default" to get the default format for the emote, which will be animated if available, otherwise static.
            Defaults to "default".

        Examples
        --------
        ```py
            emotes: list[twitchio.GlobalEmote] = await client.fetch_global_emotes()
            emote: twitchio.GlobalEmote = emotes[0]

            # Get and save the emote asset as an image
            asset: twitchio.Asset = await emote.get_image()
            await asset.save()
        ```

        Returns
        -------
        twitchio.Asset
            The [`Asset`][twitchio.Asset] for the emote.
            You can use the asset to [`.read`][twitchio.Asset.read] or [`.save`][twitchio.Asset.save] the emote image or
            return the generated URL with [`.url`][twitchio.Asset.url].
        """
        template: str = self.template.format()
        theme_: str = theme if theme in self.theme_mode else self.theme_mode[0]
        scale_: str = scale if scale in self.scale else self.scale[0]
        format_: str = format if format in self.format else "default"

        url: str = template.format(id=self.id, theme_mode=theme_, scale=scale_, format=format_)
        return Asset(url, name=self.name, http=self._http)


class EmoteSet(GlobalEmote):
    """
    Represents an emote set.

    Parameters
    ----------
    set_id: str
        An ID that identifies the emote set that the emote belongs to.
    type: str
        The type of emote. The possible values are: ``bitstier``, ``follower``, ``subscriptions``.
    owner_id: str
        The ID of the broadcaster who owns the emote.
    id: str
        The ID of the emote.
    name: str
        The name of the emote.
    images: dict[str, str]
        Contains the image URLs for the emote. These image URLs will always provide a static (i.e., non-animated) emote image with a light background.
    format: list[str]
        The formats that the emote is available in.
    scale: list[str]
        The sizes that the emote is available in.
    theme_mode: list[str]
        The background themes that the emote is available in.
    """

    __slots__ = ("type", "set_id", "owner_id")

    def __init__(self, data: EmoteSetsResponseData, *, template: str, http: HTTPClient) -> None:
        super().__init__(data, template=template, http=http)
        self.set_id: str = data["emote_set_id"]
        self.type: str = data["emote_type"]
        self.owner_id: str = data["owner_id"]

    def __repr__(self) -> str:
        return f"<EmoteSet set_id={self.set_id} owner_id={self.owner_id}>"
