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
import uuid
from typing import Optional, List, Type


__all__ = (
    "Topic",
    "bits",
    "bits_badge",
    "channel_points",
    "channel_subscriptions",
    "moderation_user_action",
    "whispers",
)


class _topic:
    __slots__ = "__topic__", "__args__"

    def __init__(self, topic: str, args: List[Type]):
        self.__topic__ = topic
        self.__args__ = args

    def __call__(self, token: str):
        cls = Topic(self.__topic__, self.__args__)
        cls.token = token
        return cls

    def copy(self):
        return self.__class__(self.__topic__, self.__args__)


class Topic(_topic):
    """
    Represents a PubSub Topic. This should not be created manually,
    use the provided methods to create these.

    Attributes
    -----------
    token: :class:`str`
        The token to use to authorize this topic
    args: List[Union[:class:`int`, Any]]
        The arguments to substitute in to the topic string
    """

    __slots__ = "token", "args", "_nonce"

    def __init__(self, topic, args):
        super().__init__(topic, args)
        self.token = None
        self._nonce = None
        self.args = []

    def __getitem__(self, item):
        assert len(self.args) < len(self.__args__), ValueError("Too many arguments")
        assert isinstance(item, self.__args__[len(self.args)]), ValueError(
            f"Got {item!r}, excepted {self.__args__[len(self.args)]}"
        )  # noqa
        self.args.append(item)
        return self

    @property
    def present(self) -> Optional[str]:
        """
        Returns a websocket-ready topic string, if all the arguments needed have been provided.
        Otherwise returns ``None``
        """
        try:
            return self.__topic__.format(*self.args)
        except:
            return None

    def _present_set_nonce(self, nonce: str) -> Optional[str]:
        self._nonce = nonce
        return self.present

    def __eq__(self, other):
        return other is self or (isinstance(other, Topic) and other.present == self.present)

    def __hash__(self):
        return hash(self.present)

    def __repr__(self):
        return f"<Topic {self.__topic__} args={self.args}>"


bits = _topic("channel-bits-events-v2.{0}", [int])
bits_badge = _topic("channel-bits-badge-unlocks.{0}", [int])
channel_points = _topic("channel-points-channel-v1.{0}", [int])
channel_subscriptions = _topic("channel-subscribe-events-v1.{0}", [int])
moderation_user_action = _topic("chat_moderator_actions.{0}.{1}", [int, int])
whispers = _topic("whispers.{0}", [int])
