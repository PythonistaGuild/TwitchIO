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

import urllib.parse
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


class _scope_property:
    def __set_name__(self, owner: type[Scopes], name: str) -> None:
        self._name = name

    def __get__(self, *_: object) -> _scope_property:
        return self

    def __set__(self, instance: Scopes, value: bool) -> None:
        if value is True:
            instance._selected.add(self)
        elif value is False:
            instance._selected.discard(self)
        else:
            raise TypeError(f"Expected bool for scope, got {type(value).__name__}")

    def __str__(self) -> str:
        return self._name.replace("_", ":", 2)

    def quoted(self) -> str:
        return urllib.parse.quote(str(self))

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> str:
        return str(self)

    def __hash__(self) -> int:
        return hash(self._name)

    def __eq__(self, other: object, /) -> bool:
        if not isinstance(other, (_scope_property, str)):
            return NotImplemented

        return str(self) == str(other)


class _ScopeMeta(type):
    def __setattr__(self, name: str, value: object, /) -> None:
        raise AttributeError("Cannot set the value of a Scope property.")

    def __delattr__(self, name: str, /) -> None:
        raise AttributeError("Cannot delete the value of a Scope property.")


class Scopes(metaclass=_ScopeMeta):
    """The Scopes class is a helper utility class to help with selecting and formatting scopes for use in Twitch OAuth.

    The Scopes class can be initialised and used a few different ways:

    - Passing a ``list[str]`` of scopes to the constructor which can be in the same format as seen on Twitch. E.g. ``["user:read:email", ...]``.

    - Passing ``Keyword-Arguments`` to the constructor. E.g. ``user_read_email=True``

    - Or Constructing the class without passing anything and giving each required scope a bool when needed.

    - There is also a classmethod :meth:`.all` which selects all scopes for you.



    All scopes on this class are special descriptors.

    Attributes
    ----------
    analytics_read_extensions
        Equivalent to the ``analytics:read:extensions`` scope on Twitch.
    analytics_read_games
        Equivalent to the ``analytics:read:games`` scope on Twitch.
    bits_read
        Equivalent to the ``bits:read`` scope on Twitch.
    channel_bot
        Equivalent to the ``channel:bot`` scope on Twitch.
    channel_manage_ads
        Equivalent to the ``channel:manage:ads`` scope on Twitch.
    channel_read_ads
        Equivalent to the ``channel:read:ads`` scope on Twitch.
    channel_manage_broadcast
        Equivalent to the ``channel:manage:broadcast`` scope on Twitch.
    channel_read_charity
        Equivalent to the ``channel:read:charity`` scope on Twitch.
    channel_edit_commercial
        Equivalent to the ``channel:edit:commercial`` scope on Twitch.
    channel_read_editors
        Equivalent to the ``channel:read:editors`` scope on Twitch.
    channel_manage_extensions
        Equivalent to the ``channel:manage:extensions`` scope on Twitch.
    channel_read_goals
        Equivalent to the ``channel:read:goals`` scope on Twitch.
    channel_read_guest_star
        Equivalent to the ``channel:read:guest_star`` scope on Twitch.
    channel_manage_guest_star
        Equivalent to the ``channel:manage:guest_star`` scope on Twitch.
    channel_read_hype_train
        Equivalent to the ``channel:read:hype_train`` scope on Twitch.
    channel_manage_moderators
        Equivalent to the ``channel:manage:moderators`` scope on Twitch.
    channel_read_polls
        Equivalent to the ``channel:read:polls`` scope on Twitch.
    channel_manage_polls
        Equivalent to the ``channel:manage:polls`` scope on Twitch.
    channel_read_predictions
        Equivalent to the ``channel:read:predictions`` scope on Twitch.
    channel_manage_predictions
        Equivalent to the ``channel:manage:predictions`` scope on Twitch.
    channel_manage_raids
        Equivalent to the ``channel:manage:raids`` scope on Twitch.
    channel_read_redemptions
        Equivalent to the ``channel:read:redemptions`` scope on Twitch.
    channel_manage_redemptions
        Equivalent to the ``channel:manage:redemptions`` scope on Twitch.
    channel_manage_schedule
        Equivalent to the ``channel:manage:schedule`` scope on Twitch.
    channel_read_stream_key
        Equivalent to the ``channel:read:stream_key`` scope on Twitch.
    channel_read_subscriptions
        Equivalent to the ``channel:read:subscriptions`` scope on Twitch.
    channel_manage_videos
        Equivalent to the ``channel:manage:videos`` scope on Twitch.
    channel_read_vips
        Equivalent to the ``channel:read:vips`` scope on Twitch.
    channel_manage_vips
        Equivalent to the ``channel:manage:vips`` scope on Twitch.
    channel_moderate
        Equivalent to the ``channel:moderate`` scope on Twitch.
    clips_edit
        Equivalent to the ``clips:edit`` scope on Twitch.
    moderation_read
        Equivalent to the ``moderation:read`` scope on Twitch.
    moderator_manage_announcements
        Equivalent to the ``moderator:manage:announcements`` scope on Twitch.
    moderator_manage_automod
        Equivalent to the ``moderator:manage:automod`` scope on Twitch.
    moderator_read_automod_settings
        Equivalent to the ``moderator:read:automod_settings`` scope on Twitch.
    moderator_manage_automod_settings
        Equivalent to the ``moderator:manage:automod_settings`` scope on Twitch.
    moderator_read_banned_users
        Equivalent to the ``moderator:read:banned_users`` scope on Twitch.
    moderator_manage_banned_users
        Equivalent to the ``moderator:manage:banned_users`` scope on Twitch.
    moderator_read_blocked_terms
        Equivalent to the ``moderator:read:blocked_terms`` scope on Twitch.
    moderator_read_chat_messages
        Equivalent to the ``moderator:read:chat_messages`` scope on Twitch.
    moderator_manage_blocked_terms
        Equivalent to the ``moderator:manage:blocked_terms`` scope on Twitch.
    moderator_manage_chat_messages
        Equivalent to the ``moderator:manage:chat_messages`` scope on Twitch.
    moderator_read_chat_settings
        Equivalent to the ``moderator:read:chat_settings`` scope on Twitch.
    moderator_manage_chat_settings
        Equivalent to the ``moderator:manage:chat_settings`` scope on Twitch.
    moderator_read_chatters
        Equivalent to the ``moderator:read:chatters`` scope on Twitch.
    moderator_read_followers
        Equivalent to the ``moderator:read:followers`` scope on Twitch.
    moderator_read_guest_star
        Equivalent to the ``moderator:read:guest_star`` scope on Twitch.
    moderator_manage_guest_star
        Equivalent to the ``moderator:manage:guest_star`` scope on Twitch.
    moderator_read_moderators
        Equivalent to the ``moderator:read:moderators`` scope on Twitch.
    moderator_read_shield_mode
        Equivalent to the ``moderator:read:shield_mode`` scope on Twitch.
    moderator_manage_shield_mode
        Equivalent to the ``moderator:manage:shield_mode`` scope on Twitch.
    moderator_read_shoutouts
        Equivalent to the ``moderator:read:shoutouts`` scope on Twitch.
    moderator_manage_shoutouts
        Equivalent to the ``moderator:manage:shoutouts`` scope on Twitch.
    moderator_read_suspicious_users
        Equivalent to the ``moderator:read:suspicious_users`` scope on Twitch.
    moderator_read_unban_requests
        Equivalent to the ``moderator:read:unban_requests`` scope on Twitch.
    moderator_manage_unban_requests
        Equivalent to the ``moderator:manage:unban_requests`` scope on Twitch.
    moderator_read_vips
        Equivalent to the ``moderator:read:vips`` scope on Twitch.
    moderator_read_warnings
        Equivalent to the ``moderator:read:warnings`` scope on Twitch.
    moderator_manage_warnings
        Equivalent to the ``moderator:manage:warnings`` scope on Twitch.
    user_bot
        Equivalent to the ``user:bot`` scope on Twitch.
    user_edit
        Equivalent to the ``user:edit`` scope on Twitch.
    user_edit_broadcast
        Equivalent to the ``user:edit:broadcast`` scope on Twitch.
    user_read_blocked_users
        Equivalent to the ``user:read:blocked_users`` scope on Twitch.
    user_manage_blocked_users
        Equivalent to the ``user:manage:blocked_users`` scope on Twitch.
    user_read_broadcast
        Equivalent to the ``user:read:broadcast`` scope on Twitch.
    user_read_chat
        Equivalent to the ``user:read:chat`` scope on Twitch.
    user_manage_chat_color
        Equivalent to the ``user:manage:chat_color`` scope on Twitch.
    user_read_email
        Equivalent to the ``user:read:email`` scope on Twitch.
    user_read_emotes
        Equivalent to the ``user:read:emotes`` scope on Twitch.
    user_read_follows
        Equivalent to the ``user:read:follows`` scope on Twitch.
    user_read_moderated_channels
        Equivalent to the ``user:read:moderated_channels`` scope on Twitch.
    user_read_subscriptions
        Equivalent to the ``user:read:subscriptions`` scope on Twitch.
    user_read_whispers
        Equivalent to the ``user:read:whispers`` scope on Twitch.
    user_manage_whispers
        Equivalent to the ``user:manage:whispers`` scope on Twitch.
    user_write_chat
        Equivalent to the ``user:write:chat`` scope on Twitch.
    chat_edit
        Equivalent to the ``chat:edit`` scope on Twitch.
    chat_read
        Equivalent to the ``chat:read`` scope on Twitch.
    user_edit_follows
        Equivalent to the ``user:edit:follows`` scope on Twitch.
    whispers_read
        Equivalent to the ``whispers:read`` scope on Twitch.
    whispers_edit
        Equivalent to the ``whispers:edit`` scope on Twitch.
    """

    __slots__ = ("_selected",)

    analytics_read_extensions = _scope_property()
    analytics_read_games = _scope_property()
    bits_read = _scope_property()
    channel_bot = _scope_property()
    channel_manage_ads = _scope_property()
    channel_read_ads = _scope_property()
    channel_manage_broadcast = _scope_property()
    channel_read_charity = _scope_property()
    channel_edit_commercial = _scope_property()
    channel_read_editors = _scope_property()
    channel_manage_extensions = _scope_property()
    channel_read_goals = _scope_property()
    channel_read_guest_star = _scope_property()
    channel_manage_guest_star = _scope_property()
    channel_read_hype_train = _scope_property()
    channel_manage_moderators = _scope_property()
    channel_read_polls = _scope_property()
    channel_manage_polls = _scope_property()
    channel_read_predictions = _scope_property()
    channel_manage_predictions = _scope_property()
    channel_manage_raids = _scope_property()
    channel_read_redemptions = _scope_property()
    channel_manage_redemptions = _scope_property()
    channel_manage_schedule = _scope_property()
    channel_read_stream_key = _scope_property()
    channel_read_subscriptions = _scope_property()
    channel_manage_videos = _scope_property()
    channel_read_vips = _scope_property()
    channel_manage_vips = _scope_property()
    channel_moderate = _scope_property()
    clips_edit = _scope_property()
    moderation_read = _scope_property()
    moderator_manage_announcements = _scope_property()
    moderator_manage_automod = _scope_property()
    moderator_read_automod_settings = _scope_property()
    moderator_manage_automod_settings = _scope_property()
    moderator_read_banned_users = _scope_property()
    moderator_manage_banned_users = _scope_property()
    moderator_read_blocked_terms = _scope_property()
    moderator_read_chat_messages = _scope_property()
    moderator_manage_blocked_terms = _scope_property()
    moderator_manage_chat_messages = _scope_property()
    moderator_read_chat_settings = _scope_property()
    moderator_manage_chat_settings = _scope_property()
    moderator_read_chatters = _scope_property()
    moderator_read_followers = _scope_property()
    moderator_read_guest_star = _scope_property()
    moderator_manage_guest_star = _scope_property()
    moderator_read_moderators = _scope_property()
    moderator_read_shield_mode = _scope_property()
    moderator_manage_shield_mode = _scope_property()
    moderator_read_shoutouts = _scope_property()
    moderator_manage_shoutouts = _scope_property()
    moderator_read_suspicious_users = _scope_property()
    moderator_read_unban_requests = _scope_property()
    moderator_manage_unban_requests = _scope_property()
    moderator_read_vips = _scope_property()
    moderator_read_warnings = _scope_property()
    moderator_manage_warnings = _scope_property()
    user_bot = _scope_property()
    user_edit = _scope_property()
    user_edit_broadcast = _scope_property()
    user_read_blocked_users = _scope_property()
    user_manage_blocked_users = _scope_property()
    user_read_broadcast = _scope_property()
    user_read_chat = _scope_property()
    user_manage_chat_color = _scope_property()
    user_read_email = _scope_property()
    user_read_emotes = _scope_property()
    user_read_follows = _scope_property()
    user_read_moderated_channels = _scope_property()
    user_read_subscriptions = _scope_property()
    user_read_whispers = _scope_property()
    user_manage_whispers = _scope_property()
    user_write_chat = _scope_property()
    chat_edit = _scope_property()
    chat_read = _scope_property()
    user_edit_follows = _scope_property()
    whispers_read = _scope_property()
    whispers_edit = _scope_property()

    def __init__(self, scopes: Iterable[str | _scope_property] | None = None, /, **kwargs: bool) -> None:
        if scopes is None:
            scopes = []
        self._selected: set[_scope_property] = set()

        prop: _scope_property

        for scope in scopes:
            if isinstance(scope, str):
                if scope == "openid":
                    continue

                prop = getattr(self, scope.replace(":", "_"))
            elif isinstance(scope, _scope_property):  # type: ignore
                prop = scope
            else:
                raise TypeError(f"Invalid scope provided: {type(scope)} is not a valid scope.")

            self._selected.add(prop)

        for key, value in kwargs.items():
            prop = getattr(self, key)

            if value is True:
                self._selected.add(prop)
            elif value is False:
                self._selected.discard(prop)
            else:
                raise TypeError(f'Expected bool for scope kwarg "{key}", got {type(value).__name__}')

    def __iter__(self) -> Iterator[str]:
        return iter([str(scope) for scope in self._selected])

    def __repr__(self) -> str:
        return f"<Scopes selected={list(self)}>"

    def __str__(self) -> str:
        return self.urlsafe()

    def __contains__(self, scope: _scope_property | str, /) -> bool:
        if isinstance(scope, str):
            return any(s.value == scope for s in self._selected)

        return scope in self._selected

    def urlsafe(self, *, unquote: bool = False) -> str:
        """Method which returns a URL-Safe formatted ``str`` of selected scopes.

        The string returned by this method is safe to use in browsers etc.

        Parameters
        ----------
        unqoute: bool
            If this is ``True``, this will return scopes without URL quoting, E.g. as ``user:read:email+channel:bot``
            compared to ``user%3Aread%3Aemail+channel%3Abot``. Defaults to ``False``.
        """
        return "+".join([scope.value if unquote else scope.quoted() for scope in self._selected])

    @property
    def selected(self) -> list[str]:
        """Property that returns a ``list[str]`` of selected scopes.

        This is not URL-Safe. See: :meth:`.urlsafe` for a method which returns a URL-Safe string.
        """
        return list(self)

    @classmethod
    def all(cls) -> Scopes:
        """Classmethod which creates this :class:`.Scopes` object with all scopes selected."""
        return cls([scope for scope in cls.__dict__.values() if isinstance(scope, _scope_property)])
