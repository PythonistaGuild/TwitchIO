# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2017-present TwitchIO

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
import logging

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
    "WHISPER",
    "USERNOTICE",
)
ACTIONS2 = ("USERSTATE", "ROOMSTATE", "PRIVMSG", "USERNOTICE", "WHISPER")
USER_SUB = re.compile(r":(?P<user>.*)!")
MESSAGE_RE = re.compile(r":(?P<useraddr>\S+) (?P<action>\S+) (?P<channel>\S+)( :(?P<message>.*))?$")
FAST_RETURN = {"RECONNECT": {"code": 0, "action": "RECONNECT"}, "PING": {"action": "PING"}}

logger = logging.getLogger("twitchio.parser")


def parser(data: str, nick: str):
    groups = data.split()
    action = groups[1] if groups[1] == "JOIN" else groups[-2]
    channel = None
    message = None
    user = None
    badges = None

    _group_len = len(groups)

    if action in FAST_RETURN:
        return FAST_RETURN[action]

    elif groups[1] in FAST_RETURN:
        return FAST_RETURN[groups[1]]

    elif (
        groups[1] in ACTIONS
        or (_group_len > 2 and groups[2] in ACTIONS)
        or (_group_len > 3 and groups[3] in {"PRIVMSG", "PRIVMSG(ECHO)"})
    ):
        result = re.search(MESSAGE_RE, data)
        if not result:
            logger.error("****** MESSAGE_RE Failed! ******")
            return None  # raise exception?
        user = result.group("useraddr").split("!")[0]
        action = result.group("action")
        channel = result.group("channel").lstrip("#")
        message = result.group("message")

    if action == "WHISPER":
        channel = None

    if action in ACTIONS2:
        prebadge = groups[0].split(";")
        badges = {}

        for badge in prebadge:
            badge = badge.split("=")

            try:
                badges[badge[0]] = badge[1]
            except IndexError:
                pass

    if action == "USERSTATE" and badges.get("display-name"):
        user = badges.get("display-name").lower()

    if action == "USERNOTICE" and badges.get("login"):
        user = badges.get("login").lower()

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
        channel = groups[4]
        if channel[0] == "#":
            channel = channel[1:]
        else:
            logger.warning(f" (353) parse failed? ||{channel}||")

    if user is None:
        user = groups[-1][1:].lower()
        for b in groups[5:-1]:
            if b[0] == ":":
                b = b[1:]

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
