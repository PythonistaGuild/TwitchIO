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
from .user import PartialUser
from .utils import Colour, parse_timestamp


if TYPE_CHECKING:
    import datetime

    from .http import HTTPClient
    from .types_.responses import (
        AdScheduleResponse,
        BitsLeaderboardPayload,
        BitsLeaderboardResponse,
        CCLResponse,
        ChannelInfoResponse,
        ChatBadgeSetResponse,
        ChatBadgeVersionResponse,
        ChatterColorResponse,
        CheerEmoteResponse,
        CheerEmoteTierResponse,
        CostResponse,
        ExtensionTransactionResponse,
        GamePayload,
        GameResponse,
        GlobalEmoteResponse,
        ProductDataResponse,
        RawResponse,
        SearchChannelResponse,
        SnoozeAdResponse,
        StartCommercialResponse,
        StreamResponse,
        TeamResponse,
        VideoResponse,
    )


__all__ = (
    "AdSchedule",
    "ChatterColor",
    "ChannelInfo",
    "ChatBadge",
    "ChatBadgeVersions",
    "CheerEmoteTier",
    "CheerEmote",
    "Clip",
    "CommercialStart",
    "ContentClassificationLabel",
    "Game",
    "GlobalEmote",
    "SearchChannel",
    "Stream",
    "SnoozeAd",
    "Team",
    "Video",
)


class AdSchedule:
    """
    Represents ad schedule information.

    Attributes
    -----------
    snooze_count: int
        The number of snoozes available for the broadcaster.
    snooze_refresh_at: datetime.datetime
        The UTC datetime when the broadcaster will gain an additional snooze.
    duration: int
        The length in seconds of the scheduled upcoming ad break.
    next_ad_at: datetime.datetime | None
        The UTC datetime of the broadcaster's next scheduled ad format. None if channel has no ad scheduled.
    last_ad_at: datetime.datetime | None
        The UTC datetime of the broadcaster's last ad-break. None if channel has not run an ad or is not live.
    preroll_free_time: int
        The amount of pre-roll free time remaining for the channel in seconds. Returns 0 if they are currently not pre-roll free.
    """

    __slots__ = ("snooze_count", "snooze_refresh_at", "duration", "next_ad_at", "last_ad_at", "preroll_free_time")

    def __init__(self, data: AdScheduleResponse) -> None:
        self.snooze_count: int = int(data["snooze_count"])
        self.snooze_refresh_at: datetime.datetime = parse_timestamp(data["snooze_refresh_at"])
        self.duration: int = int(data["duration"])
        self.next_ad_at: datetime.datetime | None = parse_timestamp(data["next_ad_at"]) if data["next_ad_at"] else None
        self.last_ad_at: datetime.datetime | None = parse_timestamp(data["last_ad_at"]) if data["last_ad_at"] else None
        self.preroll_free_time: int = int(data["preroll_free_time"])


class BitsLeaderboard:
    """
    Represents a Bits leaderboard.

    Attributes
    ------------
    started_at: datetime.datetime | None
        The time the leaderboard started.
    ended_at: datetime.datetime | None
        The time the leaderboard ended.
    leaders: list[BitLeaderboardUser]
        The current leaders of the Leaderboard.
    """

    __slots__ = ("leaders", "started_at", "ended_at")

    def __init__(self, data: BitsLeaderboardPayload) -> None:
        self.started_at = (
            parse_timestamp(data["date_range"]["started_at"]) if data["date_range"]["started_at"] else None
        )
        self.ended_at = parse_timestamp(data["date_range"]["ended_at"]) if data["date_range"]["ended_at"] else None
        self.leaders = [BitLeaderboardUser(d) for d in data["data"]]

    def __repr__(self) -> str:
        return f"<BitsLeaderboard started_at={self.started_at} ended_at={self.ended_at}>"


class BitLeaderboardUser:
    __slots__ = ("user", "rank", "score")

    def __init__(self, data: BitsLeaderboardResponse) -> None:
        self.user = PartialUser(data["user_id"], data["user_login"])
        self.rank: int = int(data["rank"])
        self.score: int = int(data["score"])


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

    def __init__(self, data: ChatterColorResponse) -> None:
        self.user = PartialUser(data["user_id"], data["user_login"])
        self._colour: Colour = Colour.from_hex(data["color"])

    def __repr__(self) -> str:
        return f"<ChatterColor user={self.user} color={self.colour}>"

    @property
    def colour(self) -> Colour:
        return self._colour

    color = colour

    def __str__(self) -> str:
        return self._colour.hex


class ChannelInfo:
    """
    Represents a channel's current information

    Attributes
    -----------
    user: twitchio.PartialUser
        The user whose channel information was requested.
    game_id: int
        Current game ID being played on the channel.
    game_name: str
        Name of the game being played on the channel.
    title: str
        Title of the stream.
    language: str
        Language of the channel.
    delay: int
        Stream delay in seconds.
        This defaults to 0 if the broadcaster_id does not match the user access token.
    tags: list[str]
        The tags applied to the channel.
    classification_labels: list[str]
        The CCLs applied to the channel.
    is_branded_content: bool
        Boolean flag indicating if the channel has branded content.
    """

    __slots__ = (
        "user",
        "game_id",
        "game_name",
        "title",
        "language",
        "delay",
        "tags",
        "classification_labels",
        "is_branded_content",
    )

    def __init__(self, data: ChannelInfoResponse) -> None:
        self.user = PartialUser(data["broadcaster_id"], data["broadcaster_name"])
        self.game_id: str = data["game_id"]
        self.game_name: str = data["game_name"]
        self.title: str = data["title"]
        self.language: str = data["broadcaster_language"]
        self.delay: int = int(data["delay"])
        self.tags: list[str] = data["tags"]
        self.classification_labels: list[str] = data["content_classification_labels"]
        self.is_branded_content: bool = data["is_branded_content"]

    def __repr__(self) -> str:
        return f"<ChannelInfo user={self.user} game_id={self.game_id} game_name={self.game_name} title={self.title} language={self.language} delay={self.delay}>"


class Clip:
    """
    Represents a Twitch Clip

    Attributes
    -----------
    id: str
        The ID of the clip.
    url: str
        The URL of the clip.
    embed_url: str
        The URL to embed the clip with.
    broadcaster: twitchio.PartialUser
        The user whose channel the clip was created on.
    creator: twitchio.PartialUser
        The user who created the clip.
    video_id: str
        The ID of the video the clip is sourced from.
    game_id: str
        The ID of the game that was being played when the clip was created.
    language: str
        The language, in an `ISO 639-1 <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ format, of the stream when the clip was created.
    title: str
        The title of the clip.
    views: int
        The amount of views this clip has.
    created_at: datetime.datetime
        When the clip was created.
    thumbnail_url: str
        The url of the clip thumbnail.
    is_featured: bool
        Indicates if the clip is featured or not.
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
        "is_featured",
    )

    def __init__(self, data: RawResponse) -> None:
        self.id: str = data["id"]
        self.url: str = data["url"]
        self.embed_url: str = data["embed_url"]
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], data["broadcaster_name"])
        self.creator: PartialUser = PartialUser(data["creator_id"], data["creator_name"])
        self.video_id: str = data["video_id"]
        self.game_id: str = data["game_id"]
        self.language: str = data["language"]
        self.title: str = data["title"]
        self.views: int = data["view_count"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.thumbnail_url: str = data["thumbnail_url"]
        self.is_featured: bool = data["is_featured"]

    def __repr__(self) -> str:
        return f"<Clip id={self.id} broadcaster={self.broadcaster} creator={self.creator}>"


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

    def __init__(self, data: ChatBadgeSetResponse) -> None:
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

    def __init__(self, data: ChatBadgeVersionResponse) -> None:
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


class CheerEmoteTier:
    """
    Represents a Cheer Emote tier.

    Attributes
    -----------
    min_bits: int
        The minimum bits for the tier
    id: str
        The ID of the tier
    colour: str
        The colour of the tier
    images: dict[str, dict[str, dict[str, str]]]
        contains two dicts, ``light`` and ``dark``. Each item will have an ``animated`` and ``static`` item,
        which will contain yet another dict, with sizes ``1``, ``1.5``, ``2``, ``3``, and ``4``.
        Ex. ``cheeremotetier.images["light"]["animated"]["1"]``
    can_cheer: bool
        Indicates whether emote information is accessible to users.
    show_in_bits_card: bool
        Indicates whether twitch hides the emote from the bits card.
    """

    __slots__ = "min_bits", "id", "color", "images", "can_cheer", "show_in_bits_card"

    def __init__(self, data: CheerEmoteTierResponse) -> None:
        self.min_bits: int = data["min_bits"]
        self.id: str = data["id"]
        self.color: str = data["color"]
        self.images = data["images"]
        self.can_cheer: bool = data["can_cheer"]
        self.show_in_bits_card: bool = data["show_in_bits_card"]

    def __repr__(self) -> str:
        return f"<CheerEmoteTier id={self.id} min_bits={self.min_bits}>"


class CheerEmote:
    """
    Represents a Cheer Emote

    Attributes
    -----------
    prefix: str
        The string used to Cheer that precedes the Bits amount.
    tiers: CheerEmoteTier
        The tiers this Cheer Emote has
    type: str
        Shows whether the emote is ``global_first_party``, ``global_third_party``, ``channel_custom``, ``display_only``, or ``sponsored``.
    order: int
        Order of the emotes as shown in the bits card, in ascending order.
    last_updated datetime.datetime
        The date this cheermote was last updated.
    charitable: bool
        Indicates whether this emote provides a charity contribution match during charity campaigns.
    """

    __slots__ = (
        "_http",
        "prefix",
        "tiers",
        "type",
        "order",
        "last_updated",
        "charitable",
    )

    def __init__(self, data: CheerEmoteResponse) -> None:
        self.prefix: str = data["prefix"]
        self.tiers = [CheerEmoteTier(d) for d in data["tiers"]]
        self.type: str = data["type"]
        self.order: int = int(data["order"])
        self.last_updated = parse_timestamp(data["last_updated"])
        self.charitable: bool = data["is_charitable"]

    def __repr__(self) -> str:
        return f"<CheerEmote prefix={self.prefix} type={self.type} order={self.order}>"


class CommercialStart:
    """Represents a Commercial starting.

    Attributes
    ----------
    length: int
        The length of the commercial you requested. If you request a commercial that's longer than 180 seconds, the API uses 180 seconds.
    message: str
        A message that indicates whether Twitch was able to serve an ad.
    retry_after: int
        The number of seconds you must wait before running another commercial.
    """

    __slots__ = ("length", "message", "retry_after")

    def __init__(self, data: StartCommercialResponse) -> None:
        self.length: int = int(data["length"])
        self.message: str = data["message"]
        self.retry_after: int = int(data["retry_after"])

    def __repr__(self) -> str:
        return f"<CommercialStart length={self.length} message={self.message}>"


class ContentClassificationLabel:
    """
    Represents a Content Classification Label.

    Attributes
    -----------
    id: str
        Unique identifier for the CCL.
    description: str
        Localized description of the CCL.
    name: str
        Localized name of the CCL.
    """

    __slots__ = ("id", "description", "name")

    def __init__(self, data: CCLResponse) -> None:
        self.id: str = data["id"]
        self.description: str = data["description"]
        self.name: str = data["name"]

    def __repr__(self) -> str:
        return f"<ContentClassificationLabel id={self.id}>"


class ExtensionTransaction:
    """
    Represents an Extension Transaction.

    Attributes
    -----------
    id: str
        An ID that identifies the transaction.
    timestamp: datetime.datetime
        The UTC date and time of the transaction.
    broadcaster: twitchio.PartialUser
        The broadcaster that owns the channel where the transaction occurred.
    user: twitchio.PartialUser
        The user that purchased the digital product.
    product_type: str
        The type of transaction. Currently only ``BITS_IN_EXTENSION``
    product_data: twitchio.ExtensionProductData
        Details about the digital product.
    """

    __slots__ = ("id", "timestamp", "broadcaster", "user", "product_type", "product_data")

    def __init__(self, data: ExtensionTransactionResponse) -> None:
        self.id: str = data["id"]
        self.timestamp: datetime.datetime = parse_timestamp(data["timestamp"])
        self.broadcaster = PartialUser(data["broadcaster_id"], data["broadcaster_login"])
        self.user = PartialUser(data["user_id"], data["user_login"])
        self.product_type: str = data["product_type"]
        self.product_data: ExtensionProductData = ExtensionProductData(data["product_data"])


class ExtensionProductData:
    """
    Represents Product Data of an Extension Transaction.

    Attributes
    -----------
    domain: str
        Set to twitch.ext. + <the extension's ID>.
    sku: str
        An ID that identifies the digital product.
    cost: twitchio.ExtensionCost
        Contains details about the digital product's cost.
    in_development: bool
        Whether the product is in development.
    display_name: str
        The name of the digital product.
    expiration: str
        This field is always empty since you may purchase only unexpired products.
    broadcast: bool
        Whether the data was broadcast to all instances of the extension.
    """

    __slots__ = ("domain", "cost", "sku", "in_development", "display_name", "expiration", "broadcast")

    def __init__(self, data: ProductDataResponse) -> None:
        self.domain: str = data["domain"]
        self.sku: str = data["sku"]
        self.cost: ExtensionCost = ExtensionCost(data["cost"])
        self.in_development: bool = data["in_development"]
        self.display_name: str = data["display_name"]
        self.expiration: str = data["expiration"]
        self.broadcast: bool = data["broadcast"]


class ExtensionCost:
    """
    Represents Cost of an Extension Transaction.

    Attributes
    -----------
    amount: int
        The amount exchanged for the digital product.
    type: str
        The type of currency exchanged. Currently only ``bits``
    """

    __slots__ = ("amount", "type")

    def __init__(self, data: CostResponse) -> None:
        self.amount: int = int(data["amount"])
        self.type: str = data["type"]


class Game:
    """Represents a Game on Twitch.

    You can retrieve a game by its ID, name or IGDB ID using the [`Client.fetch_game`][twitchio.Client.fetch_game]
    method or the various `.fetch_game()` methods of other models.

    To fetch a list of games, see: [`Client.fetch_games`][twitchio.Client.fetch_games]

    Supported Operations
    --------------------

    | Operation   | Usage(s)                                 | Description                                        |
    |-----------  |------------------------------------------|----------------------------------------------------|
    | `__str__`   | `str(game)`, `f"{game}"`                 | Returns the games name.                            |
    | `__repr__`  | `repr(game)`, `f"{game!r}"`              | Returns the games official representation.         |
    | `__eq__`    | `game == game2`, `game != game2`         | Checks if two games are equal.                     |


    Attributes
    ----------
    id: str
        The ID of the game provided by Twitch.
    name: str
        The name of the game.
    box_art: Asset
        The box art of the game as an [`Asset`][twitchio.Asset].
    igdb_id: str | None
        The IGDB ID of the game. If this is not available to Twitch it will be `None`.
    """

    __slots__ = ("id", "name", "box_art", "igdb_id")

    def __init__(self, data: GameResponse, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.igdb_id: str | None = data.get("igdb_id", None)
        self.box_art: Asset = Asset(data["box_art_url"], http=http, dimensions=(1080, 1440))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Game id={self.id} name={self.name}>"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Game):
            return NotImplemented

        return __value.id == self.id


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

    def __init__(self, data: GlobalEmoteResponse, *, template: str, http: HTTPClient) -> None:
        self._data = data
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.images: dict[str, str] = data["images"]
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
        """Creates an [`Asset`][twitchio.Asset] for the emote, which can be used to download/save the emote image.

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


class SearchChannel:
    __slots__ = (
        "_http",
        "id",
        "game_id",
        "name",
        "display_name",
        "language",
        "title",
        "thumbnail",
        "live",
        "started_at",
        "tag_ids",
    )

    def __init__(self, data: SearchChannelResponse, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.display_name: str = data["display_name"]
        self.name: str = data["broadcaster_login"]
        self.id: str = data["id"]
        self.game_id: str = data["game_id"]
        self.title: str = data["title"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.language: str = data["broadcaster_language"]
        self.live: bool = data["is_live"]
        self.started_at = parse_timestamp(data["started_at"]) if self.live else None
        self.tag_ids: list[str] = data["tag_ids"]

    def __repr__(self) -> str:
        return f"<SearchUser name={self.name} title={self.title} live={self.live}>"

    async def fetch_game(self) -> Game:
        """Fetches the [`Game`][twitchio.Game] associated with this channel.

        !!! note
            The [`Game`][twitchio.Game] returned is current from the time the [`SearchChannel`][twitchio.SearchChannel]
            instance was created.

        Returns
        -------
        twitchio.Game
            The game associated with this [`SearchChannel`][twitchio.SearchChannel] instance.
        """
        payload: GamePayload = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http)


class SnoozeAd:
    """
    Represents ad schedule information.

    Attributes
    -----------
    snooze_count: int
        The number of snoozes available for the broadcaster.
    snooze_refresh_at: datetime.datetime
        The UTC datetime when the broadcaster will gain an additional snooze.
    next_ad_at: datetime.datetime | None
        The UTC datetime of the broadcaster's next scheduled ad. None if channel has no ad scheduled.
    """

    __slots__ = ("snooze_count", "snooze_refresh_at", "next_ad_at")

    def __init__(self, data: SnoozeAdResponse) -> None:
        self.snooze_count: int = int(data["snooze_count"])
        self.snooze_refresh_at: datetime.datetime = parse_timestamp(data["snooze_refresh_at"])
        self.next_ad_at: datetime.datetime | None = parse_timestamp(data["next_ad_at"]) if data["next_ad_at"] else None


class Stream:
    """
    Represents a Stream

    Attributes
    -----------
    id: str
        The current stream ID.
    user: twitchio.PartialUser
        The user who is streaming.
    game_id: str
        Current game ID being played on the channel.
    game_name: str
        Name of the game being played on the channel.
    type: str
        Whether the stream is "live" or not.
    title: str
        Title of the stream.
    viewer_count: int
        Current viewer count of the stream
    started_at: datetime.datetime
        UTC timestamp of when the stream started.
    language: str
        Language of the channel.
    thumbnail_url: str
        Thumbnail URL of the stream.
    is_mature: bool
        Indicates whether the stream is intended for mature audience.
    tags: list[str]
        The tags applied to the channel.
    """

    __slots__ = (
        "_http",
        "id",
        "user",
        "game_id",
        "game_name",
        "type",
        "title",
        "viewer_count",
        "started_at",
        "language",
        "thumbnail",
        "is_mature",
        "tags",
    )

    def __init__(self, data: StreamResponse, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http

        self.id: str = data["id"]
        self.user = PartialUser(data["user_id"], data["user_login"])
        self.game_id: str = data["game_id"]
        self.game_name: str = data["game_name"]
        self.type: str = data["type"]
        self.title: str = data["title"]
        self.viewer_count: int = data["viewer_count"]
        self.started_at = parse_timestamp(data["started_at"])
        self.language: str = data["language"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.is_mature: bool = data["is_mature"]
        self.tags: list[str] = data["tags"]

    def __repr__(self) -> str:
        return f"<Stream id={self.id} user={self.user} title={self.title} started_at={self.started_at}>"

    async def fetch_game(self) -> Game:
        """Fetches the [`Game`][twitchio.Game] associated with this stream.

        !!! note
            The [`Game`][twitchio.Game] returned is current from the time the [`Stream`][twitchio.Stream]
            instance was created.

        Returns
        -------
        twitchio.Game
            The game associated with this [`Stream`][twitchio.Stream] instance.
        """
        payload: GamePayload = await self._http.get_games(ids=[self.game_id])
        return Game(payload["data"][0], http=self._http)


class Team:
    """
    Represents information for a specific Twitch Team

    Attributes
    -----------
    users: list[twitchio.PartialUser]
        List of users in the specified Team.
    background_image_url: str
        URL for the Team background image.
    banner: str
        URL for the Team banner.
    created_at: datetime.datetime
        Date and time the Team was created.
    updated_at: datetime.datetime
        Date and time the Team was last updated.
    info: str
        Team description.
    thumbnail_url: str
        Image URL for the Team logo.
    name: str
        Team name.
    display_name: str
        Team display name.
    id: str
        Team ID.
    """

    __slots__ = (
        "users",
        "background_image",
        "banner",
        "created_at",
        "updated_at",
        "info",
        "thumbnail",
        "name",
        "display_name",
        "id",
    )

    def __init__(self, data: TeamResponse, *, http: HTTPClient) -> None:
        self.users: list[PartialUser] = [PartialUser(x["user_id"], x["user_login"]) for x in data["users"]]
        self.background_image: Asset = Asset(data["background_image_url"], http=http)
        self.banner: str = data["banner"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        self.updated_at: datetime.datetime = parse_timestamp(data["updated_at"])
        self.info: str = data["info"]
        self.thumbnail: Asset = Asset(data["thumbnail_url"], http=http)
        self.name: str = data["team_name"]
        self.display_name: str = data["team_display_name"]
        self.id: str = data["id"]

    def __repr__(self) -> str:
        return f"<Team users={self.users} team_name={self.name} team_display_name={self.display_name} id={self.id} created_at={self.created_at}>"

    def __str__(self) -> str:
        return self.name

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Team):
            return NotImplemented

        return __value.id == self.id


class Video:
    """
    Represents video information

    Attributes
    -----------
    id: int
        The ID of the video.
    user: twitchio.PartialUser
        User who owns the video.
    title: str
        Title of the video
    description: str
        Description of the video.
    created_at: datetime.datetime
        Date when the video was created.
    published_at: datetime.datetime
       Date when the video was published.
    url: str
        URL of the video.
    thumbnail_url: str
        Template URL for the thumbnail of the video.
    viewable: str
        Indicates whether the video is public or private.
    view_count: int
        Number of times the video has been viewed.
    language: str
        Language of the video.
    type: str
        The type of video.
    duration: str
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

    def __init__(self, data: VideoResponse, *, http: HTTPClient) -> None:
        self._http: HTTPClient = http
        self.id: str = data["id"]
        self.user = PartialUser(data["user_id"], data["user_login"])
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

    async def delete(self, token_for: str) -> None:
        """|coro|

        Deletes the video. For bulk deletion see :func:`Client.delete_videos`

        Parameters
        -----------
        ids: list[str | int]
            List of video IDs to delete
        token_for: str
            A user oauth token with the channel:manage:videos
        """
        await self._http.delete_videos(ids=[self.id], token_for=token_for)
