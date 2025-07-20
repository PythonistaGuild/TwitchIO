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

from typing import TYPE_CHECKING, Any, TypedDict, TypeVar, Union

from twitchio.types_.options import AutoClientOptions, ClientOptions


if TYPE_CHECKING:
    from .bot import AutoBot, Bot
    from .components import Component
    from .context import Context


Component_T = TypeVar("Component_T", bound="Component | None")

ContextT = TypeVar("ContextT", bound="Context[Any]")
ContextT_co = TypeVar("ContextT_co", bound="Context[Any]", covariant=True)

_Bot = Union["Bot", "AutoBot"]
BotT = TypeVar("BotT", bound=_Bot, covariant=True)


class CommandOptions(TypedDict, total=False):
    aliases: list[str]
    extras: dict[Any, Any]
    guards_after_parsing: bool
    cooldowns_before_guards: bool


class ComponentOptions(TypedDict, total=False):
    name: str | None
    extras: dict[Any, Any]


class BotOptions(ClientOptions, total=False):
    case_insensitive: bool


class AutoBotOptions(AutoClientOptions, total=False):
    case_insensitive: bool
