from typing import Optional, List, Type

__all__ = (
    "Topic",
    "bits",
    "bits_badge",
    "channel_points",
    "channel_subscriptions",
    "moderation_user_action",
    "whispers"
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
    __slots__ = "token", "args"
    def __init__(self, topic, args):
        super().__init__(topic, args)
        self.token = None
        self.args = []

    def __getitem__(self, item):
        assert len(self.args) < len(self.__args__), ValueError("Too many arguments")
        assert isinstance(item, self.__args__[len(self.args)]) # noqa
        self.args.append(item)
        return self

    @property
    def present(self) -> Optional[str]:
        try:
            return self.__topic__.format(*self.args)
        except:
            return None

    def __eq__(self, other):
        return other is self or (isinstance(other, Topic) and other.present == self.present)

    def __hash__(self):
        return hash(self.present)

bits = _topic("channel-bits-events-v2.{0}", [int])
bits_badge = _topic("channel-bits-badge-unlocks.{0}", [int])
channel_points = _topic("channel-points-v1.{0}", [int])
channel_subscriptions = _topic("channel-subscribe-events-v1.{0}", [int])
moderation_user_action = _topic("chat_moderator_actions.{0}.{1}", [int, int])
whispers = _topic("whispers.{0}", [int])
