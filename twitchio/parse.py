# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-2021 TwitchIO

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

import re
import typing

if typing.TYPE_CHECKING:
    from .websocket import WSConnection

ACTIONS = (
    "JOIN",
    "PART",
    "PING",
    "PRIVMSG",
    "PRIVMSG(ECHO)",
    "USERSTATE",
    "MODE",
    "RECONNECT",
    "WHISPER",
    "USERNOTICE",
)
ACTIONS2 = ("USERSTATE", "ROOMSTATE", "PRIVMSG", "USERNOTICE", "WHISPER")
USER_SUB = re.compile(r":(?P<user>.*)!")
TMI = "tmi.twitch.tv"


def parser(data: str, nick: str):
    groups = data.split()
    action = groups[1] if groups[1] == "JOIN" else groups[-2]
    channel = None
    message = None
    user = None
    badges = None

    if action == "PING":
        return dict(action="PING")

    elif groups[2] in {"PRIVMSG", "PRIVMSG(ECHO)"}:
        action = groups[2]
        channel = groups[3].lstrip("#")
        message = " ".join(groups[4:]).lstrip(":")
        user = re.search(USER_SUB, groups[1]).group("user")

    elif groups[2] == "WHISPER":
        action = groups[2]
        message = " ".join(groups[4:]).lstrip(":")
        user = re.search(USER_SUB, groups[1]).group("user")

    elif groups[2] == "USERNOTICE":
        action = groups[2]
        channel = groups[3].lstrip("#")
        message = " ".join(groups[4:]).lstrip(":")

    elif action in ACTIONS:
        channel = groups[-1].lstrip("#")

    elif groups[3] in {"PRIVMSG", "PRIVMSG(ECHO)"}:
        action = groups[3]
        channel = groups[4].lstrip("#")
        message = " ".join(groups[5:]).lstrip(":")
        user = re.search(USER_SUB, groups[2]).group("user")

    if action in ACTIONS2:
        prebadge = groups[0].split(";")
        badges = {}

        for badge in prebadge:
            badge = badge.split("=")

            try:
                badges[badge[0]] = badge[1]
            except IndexError:
                pass

    if action not in ACTIONS and action not in ACTIONS2:
        action = None

    if not user:
        try:
            user = re.search(USER_SUB, groups[0]).group("user")
        except (AttributeError, ValueError):
            pass

    try:
        code = int(groups[1])
    except ValueError:
        code = 0

    batches = []
    if code == 353:
        if not channel:
            channel = groups[4].lstrip("#")

        for b in groups[5:-1]:
            b = b.lstrip(":")

            if "\r\n:" in b:
                batches.append(b.split("\r\n:")[0])
                break
            else:
                batches.append(b)

    return dict(
        data=data,
        nick=nick,
        groups=groups,
        action=action,
        channel=channel,
        user=user,
        badges=badges,
        code=code,
        message=message,
        batches=batches,
    )


def parse(data: str, ws: "WSConnection"):
    messages = data.split("\r\n")
    output = []

    for msg in messages:
        if not msg:
            continue

        if msg == "PING :tmi.twitch.tv":
            output.append(dict(action="PING"))
            continue

        msg = msg.replace(":tmi.twitch.tv ", "")
        groups = msg.split()
        length = len(groups)
