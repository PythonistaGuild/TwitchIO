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
from twitchio.utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPAsyncIterator, HTTPClient
    from twitchio.types_.responses import (
        ChannelChatBadgesResponseData,
        ChannelChatBadgesResponseVersions,
        ChannelEmotesResponseData,
        ChannelEmotesResponseImages,
        ChatSettingsResponseData,
        ChattersResponse,
        EmoteSetsResponseData,
        GlobalChatBadgesResponseData,
        GlobalChatBadgesResponseVersions,
        GlobalEmotesResponseData,
        GlobalEmotesResponseImages,
        SendChatMessageResponseData,
        SharedChatSessionResponseData,
        UserChatColorResponseData,
        UserEmotesResponseData,
    )


__all__ = (
    "ChannelEmote",
    "ChatBadge",
    "ChatBadgeVersions",
    "ChatSettings",
    "ChatterColor",
    "Chatters",
    "Emote",
    "EmoteSet",
    "GlobalEmote",
    "SentMessage",
    "SharedChatSession",
    "UserEmote",
)


class Chatters:
    """Represents a channel's chatters.

    Returns
    -------
    users: HTTPAsyncIterator[PartialUser]
        The PartialUser object of the chatter.
    total: int
        The the total number of users that are connected to the chat room. This may vary as you iterate through pages.
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
    user: PartialUser
        PartialUser of the chatter.
    colour: Colour | None
        The :class:`~twitchio.utils.Colour`. There is an alias to this named `color`.
        This is `None` if a colour is not set.
    """

    __slots__ = ("_colour", "user")

    def __init__(self, data: UserChatColorResponseData, *, http: HTTPClient) -> None:
        self.user = PartialUser(data["user_id"], data["user_login"], data["user_name"], http=http)
        self._colour: Colour | None = Colour.from_hex(data["color"]) if data.get("color") else None

    def __repr__(self) -> str:
        return f"<ChatterColor user={self.user} color={self.colour}>"

    @property
    def colour(self) -> Colour | None:
        return self._colour

    color = colour

    def __str__(self) -> str:
        return self._colour.hex if self._colour is not None else ""


class ChatBadge:
    """Represents chat badges.

    Attributes
    -----------
    set_id: str
        An ID that identifies this set of chat badges. For example, Bits or Subscriber.
    versions: list[ChatBadgeVersions]
        The list of chat badges in this set.
    """

    __slots__ = ("_http", "set_id", "versions")

    def __init__(self, data: GlobalChatBadgesResponseData | ChannelChatBadgesResponseData, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.set_id: str = data["set_id"]
        self.versions: list[ChatBadgeVersions] = [
            ChatBadgeVersions(version_data, self._http) for version_data in data["versions"]
        ]

    def __repr__(self) -> str:
        return f"<ChatBadge set_id={self.set_id} versions={self.versions}>"


class ChatBadgeVersions:
    """Represents the different versions of the chat badge.

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
        "_http",
        "click_action",
        "click_url",
        "description",
        "id",
        "image_url_1x",
        "image_url_2x",
        "image_url_4x",
        "title",
    )

    def __init__(self, data: ChannelChatBadgesResponseVersions | GlobalChatBadgesResponseVersions, http: HTTPClient) -> None:
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
        """Retrieves an Asset object for the chat badge image at the specified scale.

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
        .. code:: python3

            chat_badges: list[twitchio.ChatBadge] = await client.fetch_global_chat_badges()
            chat_badge: twitchio.ChatBadge = chat_badges[0]

            # Get and save the chat badge asset as an image
            asset: twitchio.Asset = await emote.get_image()
            await asset.save()

        Returns
        -------
        Asset
            The :class:`~twitchio.Asset` for the chat badge.
            You can use the asset to :meth:`~twitchio.Asset.read` or :meth:`~twitchio.Asset.save` the chat badge image or
            return the generated URL with :attr:`~twitchio.Asset.url`.
        """
        if scale == "1x":
            return Asset(self.image_url_1x, http=self._http, dimensions=(18, 18))
        elif scale == "2x":
            return Asset(self.image_url_2x, http=self._http, dimensions=(36, 36))
        elif scale == "4x":
            return Asset(self.image_url_4x, http=self._http, dimensions=(72, 72))
        else:
            raise ValueError(f"Invalid scale '{scale}'. Allowed values are '1x', '2x', '4x'.")


class Emote:
    """Represents the basics of an Emote.

    Attributes
    ----------
    id: str
        The ID of the emote.
    name: str
        The name of the emote.
    format: list[str]
        The formats that the emote is available in.
    scale: list[str]
        The sizes that the emote is available in.
    theme_mode: list[str]
        The background themes that the emote is available in.
    """

    __slots__ = ("_http", "format", "id", "name", "scale", "template", "theme_mode")

    def __init__(
        self,
        data: GlobalEmotesResponseData | EmoteSetsResponseData | UserEmotesResponseData,
        template: str,
        http: HTTPClient,
    ) -> None:
        self._http = http
        self.id = data["id"]
        self.name = data["name"]
        self.format = data["format"]
        self.scale = data["scale"]
        self.theme_mode = data["theme_mode"]
        self.template = template

    def get_image(
        self,
        *,
        theme: Literal["light", "dark"] = "light",
        scale: str = "2.0",
        format: Literal["default", "static", "animated"] = "default",
    ) -> Asset:
        """Creates an :class:`~twitchio.Asset` for the emote, which can be used to download/save the emote image.

        Parameters
        ----------
        theme: typing.Literal["light", "dark"]
            The background theme of the emote. Defaults to "light".
        scale: str
            The scale (size) of the emote. Usually this will be one of:
            - "1.0" (Small)
            - "2.0" (Medium)
            - "3.0" (Large)

            Defaults to "2.0".
        format: typing.Literal["default", "static", "animated"]
            The format of the image for the emote. E.g a static image (PNG) or animated (GIF).

            Use "default" to get the default format for the emote, which will be animated if available, otherwise static.
            Defaults to "default".

        Examples
        --------
        .. code:: python3

            emotes: list[twitchio.GlobalEmote] = await client.fetch_global_emotes()
            emote: twitchio.GlobalEmote = emotes[0]

            # Get and save the emote asset as an image
            asset: twitchio.Asset = await emote.get_image()
            await asset.save()

        Returns
        -------
        Asset
            The :class:`~twitchio.Asset` for the chat emote.
            You can use the asset to :meth:`~twitchio.Asset.read` or :meth:`~twitchio.Asset.save` the chat emote image or
            return the generated URL with :attr:`~twitchio.Asset.url`.
        """
        template: str = self.template.format()
        theme_: str = theme if theme in self.theme_mode else self.theme_mode[0]
        scale_: str = scale if scale in self.scale else self.scale[0]
        format_: str = format if format in self.format else "default"

        url: str = template.format(id=self.id, theme_mode=theme_, scale=scale_, format=format_)
        return Asset(url, name=self.name, http=self._http)


class GlobalEmote(Emote):
    """Represents a Global Emote

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

    __slots__ = "images"

    def __init__(self, data: GlobalEmotesResponseData, *, template: str, http: HTTPClient) -> None:
        super().__init__(data, template=template, http=http)
        self.images: GlobalEmotesResponseImages = data["images"]

    def __repr__(self) -> str:
        return f"<GlobalEmote id={self.id} name={self.name}"


class EmoteSet(Emote):
    """Represents an emote set.

    Attributes
    ----------
    id: str
        The ID of the emote.
    name: str
        The name of the emote.
    images: dict[str, str]
        Contains the image URLs for the emote. These image URLs will always provide a static (i.e., non-animated) emote image with a light background.
    set_id: str
        An ID that identifies the emote set that the emote belongs to.
    type: str
        The type of emote. The possible values are: ``bitstier``, ``follower``, ``subscriptions``.
    owner: str
        The :class:`~twitchio.PartialUser` who owns this emote set.
    format: list[str]
        The formats that the emote is available in.
    scale: list[str]
        The sizes that the emote is available in.
    theme_mode: list[str]
        The background themes that the emote is available in.
    """

    __slots__ = ("images", "owner", "set_id", "type")

    def __init__(self, data: EmoteSetsResponseData, *, template: str, http: HTTPClient) -> None:
        super().__init__(data, template=template, http=http)
        self.images: GlobalEmotesResponseImages = data["images"]
        self.set_id: str = data["emote_set_id"]
        self.type: str = data["emote_type"]
        self.owner: PartialUser = PartialUser(id=data["owner_id"], http=http)

    def __repr__(self) -> str:
        return f"<EmoteSet set_id={self.set_id} owner={self.owner}>"


class ChannelEmote(Emote):
    """Represents an emote set.

    Attributes
    ----------
    id: str
        The ID of the emote.
    name: str
        The name of the emote.
    images: dict[str, str]
        Contains the image URLs for the emote. These image URLs will always provide a static (i.e., non-animated) emote image with a light background.
    tier: typing.Literal["1000", "2000", "3000"] | None
        This field contains the tier information only if type is set to ``subscriptions``, otherwise it's `None`.
    set_id: str
        An ID that identifies the emote set that the emote belongs to.
    type: typing.Literal["bitstier", "follower", "subscriptions"]
        The type of emote. The possible values are:

        - bitstier — A custom Bits tier emote.
        - follower — A custom follower emote.
        - subscriptions — A custom subscriber emote.

    owner: PartialUser
        The :class:`~twitchio.PartialUser` who owns this emote.
    format: list[str]
        The formats that the emote is available in.
    scale: list[str]
        The sizes that the emote is available in.
    theme_mode: list[str]
        The background themes that the emote is available in.
    """

    __slots__ = ("images", "owner_id", "set_id", "tier", "type")

    def __init__(self, data: ChannelEmotesResponseData, *, template: str, http: HTTPClient) -> None:
        super().__init__(data, template=template, http=http)
        self.images: ChannelEmotesResponseImages = data["images"]
        self.tier: Literal["1000", "2000", "3000"] | None = data.get("tier")
        self.set_id: str = data["emote_set_id"]
        self.type: Literal["bitstier", "follower", "subscriptions"] = data["emote_type"]

    def __repr__(self) -> str:
        return f"<ChannelEmote id={self.id} name={self.name} set_id={self.set_id}>"


class UserEmote(Emote):
    """Represents an emote set.

    +------------------+-----------------------------------------------------------------------+
    | Type             | Description                                                           |
    +==================+=======================================================================+
    | none             | No emote type was assigned to this emote.                             |
    +------------------+-----------------------------------------------------------------------+
    | bitstier         | A Bits tier emote.                                                    |
    +------------------+-----------------------------------------------------------------------+
    | follower         | A follower emote.                                                     |
    +------------------+-----------------------------------------------------------------------+
    | subscriptions    | A subscriber emote.                                                   |
    +------------------+-----------------------------------------------------------------------+
    | channelpoints    | An emote granted by using channel points.                             |
    +------------------+-----------------------------------------------------------------------+
    | rewards          | An emote granted to the user through a special event.                 |
    +------------------+-----------------------------------------------------------------------+
    | hypetrain        | An emote granted for participation in a Hype Train.                   |
    +------------------+-----------------------------------------------------------------------+
    | prime            | An emote granted for linking an Amazon Prime account.                 |
    +------------------+-----------------------------------------------------------------------+
    | turbo            | An emote granted for having Twitch Turbo.                             |
    +------------------+-----------------------------------------------------------------------+
    | smilies          | Emoticons supported by Twitch.                                        |
    +------------------+-----------------------------------------------------------------------+
    | globals          | An emote accessible by everyone.                                      |
    +------------------+-----------------------------------------------------------------------+
    | owl2019          | Emotes related to Overwatch League 2019.                              |
    +------------------+-----------------------------------------------------------------------+
    | twofactor        | Emotes granted by enabling two-factor authentication on an account.   |
    +------------------+-----------------------------------------------------------------------+
    | limitedtime      | Emotes that were granted for only a limited time.                     |
    +------------------+-----------------------------------------------------------------------+


    Attributes
    ----------
    id: str
        The ID of the emote.
    name: str
        The name of the emote.
    type: str
        The type of emote. Please see docs for full list of possible values.
    set_id: str
        An ID that identifies the emote set that the emote belongs to.
    owner: PartialUser
        The ID of the broadcaster who owns the emote.
    format: list[str]
        The formats that the emote is available in.
    scale: list[str]
        The sizes that the emote is available in.
    theme_mode: list[str]
        The background themes that the emote is available in.
    """

    __slots__ = ("images", "owner_id", "set_id", "tier", "type")

    def __init__(self, data: UserEmotesResponseData, *, template: str, http: HTTPClient) -> None:
        super().__init__(data, template=template, http=http)
        self.set_id: str = data["emote_set_id"]
        self.type: str = data["emote_type"]

    def __repr__(self) -> str:
        return f"<UserEmote id={self.id} name={self.name} set_id={self.set_id}>"


class ChatSettings:
    """Represents the settings of a broadcaster's chat settings.

    Attributes
    ----------
    broadcaster: PartialUser
        The PartialUser object of the broadcaster, this will only contain the ID.
    moderator: PartialUser
        The PartialUser object of the moderator, this will only contain the ID.
    slow_mode: bool
        A Boolean value that determines whether the broadcaster limits how often users in the chat room are allowed to send messages.
    slow_mode_wait_time: int | None
        The amount of time, in seconds, that users must wait between sending messages.
        Is None if slow_mode is False.
    follower_mode: bool
        A Boolean value that determines whether the broadcaster restricts the chat room to followers only.
        Is True if the broadcaster restricts the chat room to followers only; otherwise, False.
    follower_mode_duration: int | None
        The length of time, in minutes, that users must follow the broadcaster before being able to participate in the chat room.
        Is None if follower_mode is False.
    subscriber_mode: bool
        A Boolean value that determines whether only users that subscribe to the broadcaster's channel may talk in the chat room.
    emote_mode: bool
        A Boolean value that determines whether chat messages must contain only emotes. Is True if chat messages may contain only emotes; otherwise, False.
    unique_chat_mode: bool
        A Boolean value that determines whether the broadcaster requires users to post only unique messages in the chat room.
        Is True if the broadcaster requires unique messages only; otherwise, False.
    non_moderator_chat_delay: bool
        A Boolean value that determines whether the broadcaster adds a short delay before chat messages appear in the chat room.
        This gives chat moderators and bots a chance to remove them before viewers can see the message.
        See the ``non_moderator_chat_delay_duration`` field for the length of the delay.

        Is True if the broadcaster applies a delay; otherwise, False.

        The response includes this field only if the request specifies a user access token that includes the ``moderator:read:chat_settings`` scope and the user in the moderator_id query parameter is one of the broadcaster's moderators.
    non_moderator_chat_delay_duration: int | None
        The amount of time, in seconds, that messages are delayed before appearing in chat. Is None if non_moderator_chat_delay is False.

        The response includes this field only if the request specifies a user access token that includes the ``moderator:read:chat_settings scope`` and the user in the moderator_id query parameter is one of the broadcaster's moderators.
    """

    __slots__ = (
        "broadcaster",
        "emote_mode",
        "follower_mode",
        "follower_mode_duration",
        "moderator",
        "non_moderator_chat_delay",
        "non_moderator_chat_delay_duration",
        "slow_mode",
        "slow_mode_wait_time",
        "subscriber_mode",
        "unique_chat_mode",
    )

    def __init__(self, data: ChatSettingsResponseData, *, http: HTTPClient) -> None:
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], None, http=http)
        self.slow_mode: int = data["slow_mode"]
        self.slow_mode_wait_time: int | None = data.get("slow_mode_wait_time")
        self.follower_mode: bool = data["follower_mode"]
        self.follower_mode_duration: int | None = data.get("follower_mode_duration")
        self.subscriber_mode: bool = data["subscriber_mode"]
        self.emote_mode: bool = data["emote_mode"]
        self.unique_chat_mode: bool = data["unique_chat_mode"]
        self.non_moderator_chat_delay: bool | None = data.get("non_moderator_chat_delay")
        self.non_moderator_chat_delay_duration: int | None = data.get("non_moderator_chat_delay_duration")

        try:
            self.moderator: PartialUser | None = PartialUser(data["moderator_id"], None, http=http)
        except KeyError:
            self.moderator = None

    def __repr__(self) -> str:
        return f"<ChatSettings broadcaster={self.broadcaster} slow_mode={self.slow_mode} follower_mode={self.follower_mode}>"


class SentMessage:
    """Represents the settings of a broadcaster's chat settings.

    Attributes
    ----------
    id: str
        The ID for the message that was sent.
    sent: bool
        Whether the message passed all checks and was sent.
    dropped_code: str | None
        Code for why the message was dropped.
    dropped_message: str | None
        Message for why the message was dropped.
    """

    __slots__ = ("dropped_code", "dropped_message", "id", "sent")

    def __init__(self, data: SendChatMessageResponseData) -> None:
        self.id: str = data["message_id"]
        self.sent: bool = data["is_sent"]
        drop_reason = data.get("drop_reason")
        self.dropped_code: str | None = drop_reason.get("code") if drop_reason is not None else None
        self.dropped_message: str | None = drop_reason.get("message") if drop_reason is not None else None

    def __repr__(self) -> str:
        return f"<SentMessage id={self.id} sent={self.sent}>"


class SharedChatSession:
    """Represents a shared chat session.

    Attributes
    ----------
    id: str
        The unique identifier for the shared chat session.
    host: PartialUser
        The User of the host channel.
    participants: list[PartialUser]
        The list of participants / users in the session.
    created_at: datetime.datetime
        When the session was created.
    updated_at: datetime.datetime
        When the session was last updated.
    """

    __slots__ = ("created_at", "host", "id", "participants", "updated_at")

    def __init__(self, data: SharedChatSessionResponseData, *, http: HTTPClient) -> None:
        self.id: str = data["session_id"]
        self.host: PartialUser = PartialUser(data["host_broadcaster_id"], None, http=http)
        self.participants: list[PartialUser] = [
            PartialUser(u["broadcaster_id"], None, http=http) for u in data["participants"]
        ]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"])

    def __repr__(self) -> str:
        return f"<SharedChatSession id={self.id} host={self.host} created_at={self.created_at}>"
