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
        return self._name.replace("_", ":")

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
    __slots__ = ("_selected",)

    analytics_read_extensions = _scope_property()
    analytics_read_games = _scope_property()
    bits_read = _scope_property()
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
    clips_edit = _scope_property()
    moderation_read = _scope_property()
    moderator_manage_announcements = _scope_property()
    moderator_manage_automod = _scope_property()
    moderator_read_automod_settings = _scope_property()
    moderator_manage_automod_settings = _scope_property()
    moderator_manage_banned_users = _scope_property()
    moderator_read_blocked_terms = _scope_property()
    moderator_manage_blocked_terms = _scope_property()
    moderator_manage_chat_messages = _scope_property()
    moderator_read_chat_settings = _scope_property()
    moderator_manage_chat_settings = _scope_property()
    moderator_read_chatters = _scope_property()
    moderator_read_followers = _scope_property()
    moderator_read_guest_star = _scope_property()
    moderator_manage_guest_star = _scope_property()
    moderator_read_shield_mode = _scope_property()
    moderator_manage_shield_mode = _scope_property()
    moderator_read_shoutouts = _scope_property()
    moderator_manage_shoutouts = _scope_property()
    user_edit = _scope_property()
    user_edit_follows = _scope_property()
    user_read_blocked_users = _scope_property()
    user_manage_blocked_users = _scope_property()
    user_read_broadcast = _scope_property()
    user_manage_chat_color = _scope_property()
    user_read_email = _scope_property()
    user_read_follows = _scope_property()
    user_read_moderated_channels = _scope_property()
    user_read_subscriptions = _scope_property()
    user_manage_whispers = _scope_property()
    channel_bot = _scope_property()
    channel_moderate = _scope_property()
    chat_edit = _scope_property()
    chat_read = _scope_property()
    user_bot = _scope_property()
    user_read_chat = _scope_property()
    user_write_chat = _scope_property()
    whispers_read = _scope_property()
    whispers_edit = _scope_property()

    def __init__(self, scopes: Iterable[str | _scope_property] = [], /, **kwargs: bool) -> None:
        self._selected: set[_scope_property] = set()

        prop: _scope_property

        for scope in scopes:
            if isinstance(scope, str):
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

    def __contains__(self, scope: _scope_property | str, /) -> bool:
        if isinstance(scope, str):
            return any(s.value == scope for s in self._selected)

        return scope in self._selected

    def urlsafe(self, *, unquote: bool = False) -> str:
        return "+".join([scope.value if unquote else scope.quoted() for scope in self._selected])

    @property
    def selected(self) -> list[str]:
        return list(self)

    @classmethod
    def all(cls) -> Scopes:
        return cls([scope for scope in cls.__dict__.values() if isinstance(scope, _scope_property)])
