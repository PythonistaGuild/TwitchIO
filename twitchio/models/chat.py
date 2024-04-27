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
    from twitchio.http import HTTPClient
    from twitchio.types_.responses import (
        ChannelChatBadgesResponseData,
        ChannelChatBadgesResponseVersions,
        GlobalChatBadgesResponseData,
        GlobalChatBadgesResponseVersions,
        GlobalEmotesResponseData,
        GlobalEmotesResponseImages,
        UserChatColorResponseData,
    )


__all__ = ("ChatterColor", "ChatBadge", "ChatBadgeVersions", "GlobalEmote")


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

    __slots__ = ("set_id", "versions")

    def __init__(self, data: GlobalChatBadgesResponseData | ChannelChatBadgesResponseData) -> None:
        self.set_id: str = data["set_id"]
        self.versions: list[ChatBadgeVersions] = [ChatBadgeVersions(version_data) for version_data in data["versions"]]

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
    )

    def __init__(self, data: ChannelChatBadgesResponseVersions | GlobalChatBadgesResponseVersions) -> None:
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
