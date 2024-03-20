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

from typing import Any, Generic, TypeAlias, TypedDict, TypeVar

from typing_extensions import TypedDict as TypedDictExt


__all__ = (
    "RefreshTokenResponse",
    "ValidateTokenResponse",
    "ClientCredentialsResponse",
    "OAuthResponses",
    "UserTokenResponse",
    "RawResponse",
    "AuthorizationURLResponse",
    "ChatterColorResponse",
    "ChatterColorPayload",
    "ChannelInfoResponse",
    "ChannelInfoPayload",
    "CheerEmoteTierResponse",
    "CheerEmoteResponse",
    "CheerEmotePayload",
    "ClipResponse",
    "ClipPayload",
    "CCLResponse",
    "ClassificationLabelsResponse",
    "ClassificationLabelsPayload",
    "GameResponse",
    "GamePayload",
    "GlobalEmoteResponse",
    "GlobalEmotePayload",
    "SearchChannelResponse",
    "SearchChannelPayload",
    "StreamResponse",
    "StreamPayload",
    "TeamMemberResponse",
    "TeamResponse",
    "TeamPayload",
    "VideoDeletePayload",
    "VideoResponse",
    "VideoPayload",
)

T = TypeVar("T")


class Payload(TypedDictExt, Generic[T]):
    data: list[T]


class _TokenResponseBase(TypedDict):
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str | list[str]
    token_type: str


RefreshTokenResponse: TypeAlias = _TokenResponseBase
UserTokenResponse: TypeAlias = _TokenResponseBase


class ValidateTokenResponse(TypedDict):
    client_id: str
    login: str
    scopes: list[str]
    user_id: str
    expires_in: int


class ClientCredentialsResponse(TypedDict):
    access_token: str
    expires_in: int
    token_type: str


class AuthorizationURLResponse(TypedDict):
    url: str
    client_id: str
    redirect_uri: str
    response_type: str
    scopes: list[str]
    force_verify: bool
    state: str


OAuthResponses: TypeAlias = (
    RefreshTokenResponse
    | ValidateTokenResponse
    | ClientCredentialsResponse
    | UserTokenResponse
    | AuthorizationURLResponse
)
RawResponse: TypeAlias = dict[str, Any]


class Pagination(TypedDict):
    cursor: str | None


class ChatterColorResponse(TypedDict):
    user_id: str
    user_login: str
    user_name: str
    color: str


class ChannelInfoResponse(TypedDict):
    broadcaster_id: str
    broadcaster_login: str
    broadcaster_name: str
    broadcaster_language: str
    game_name: str
    game_id: str
    title: str
    delay: int
    tags: list[str]
    content_classification_labels: list[str]
    is_branded_content: bool


class CheerEmoteTierResponse(TypedDict):
    min_bits: int
    id: str
    color: str
    images: dict[str, dict[str, dict[str, str]]]
    can_cheer: bool
    show_in_bits_card: bool


class CheerEmoteResponse(TypedDict):
    prefix: str
    tiers: list[CheerEmoteTierResponse]
    type: str
    order: int
    last_updated: str
    is_charitable: bool


class ClipResponse(TypedDict):
    broadcaster_id: str
    game_id: str
    id: list[str]
    started_at: str
    ended_at: str
    first: int
    before: str
    after: str
    is_featured: bool


class CCLResponse(TypedDict):
    id: str
    description: str
    name: str


class ClassificationLabelsResponse(TypedDict):
    classification_labels: list[CCLResponse]


class GameResponse(TypedDict):
    id: str
    name: str
    igdb_id: str
    box_art_url: str


class GlobalEmoteResponse(TypedDict):
    id: str
    name: str
    images: dict[str, str]
    format: list[str]
    scale: list[str]
    theme_mode: list[str]
    template: str


class SearchChannelResponse(TypedDict):
    broadcaster_language: str
    broadcaster_login: str
    display_name: str
    game_id: str
    game_name: str
    id: str
    is_live: bool
    tag_ids: list[str]
    tags: list[str]
    thumbnail_url: str
    title: str
    started_at: str


class StreamResponse(TypedDict):
    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    type: str
    title: str
    tags: list[str]
    viewer_count: int
    started_at: str
    language: str
    thumbnail_url: str
    tag_ids: list[str]
    is_mature: bool
    pagination: dict[str, str]
    cursor: str


class TeamMemberResponse(TypedDict):
    user_id: str
    user_login: str
    user_name: str


class TeamResponse(TypedDict):
    users: list[TeamMemberResponse]
    background_image_url: str
    banner: str
    created_at: str
    updated_at: str
    info: str
    thumbnail_url: str
    team_name: str
    team_display_name: str
    id: str


class MutedSegment(TypedDict):
    duration: int
    offset: int


class VideoResponse(TypedDict):
    id: str
    stream_id: str | None
    user_id: str
    user_login: str
    user_name: str
    title: str
    description: str
    created_at: str
    published_at: str
    url: str
    thumbnail_url: str
    viewable: str
    view_count: int
    language: str
    type: str
    duration: str
    muted_segments: list[MutedSegment] | None


class StreamPayload(TypedDict):
    data: list[StreamResponse]
    pagination: Pagination


class VideoPayload(TypedDict):
    data: list[VideoResponse]
    pagination: Pagination

class VideoDeletePayload(TypedDict):
    data: list[str]

ChatterColorPayload = Payload[ChatterColorResponse]
ChannelInfoPayload = Payload[ChannelInfoResponse]
ClipPayload = Payload[ClipResponse]
CheerEmotePayload = Payload[CheerEmoteResponse]
ClassificationLabelsPayload = Payload[ClassificationLabelsResponse]
GamePayload = Payload[GameResponse]
GlobalEmotePayload = Payload[GlobalEmoteResponse]
SearchChannelPayload = Payload[SearchChannelResponse]
TeamPayload = Payload[TeamResponse]
