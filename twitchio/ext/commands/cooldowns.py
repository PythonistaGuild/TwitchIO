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

import abc
import asyncio
import datetime
import enum
from collections.abc import Callable, Coroutine, Hashable
from typing import TYPE_CHECKING, Any, Generic, Self, TypeAlias, TypeVar


if TYPE_CHECKING:
    import twitchio

    from .context import Context
    from .types_ import BotT


__all__ = ("BaseCooldown", "Bucket", "BucketType", "Cooldown", "GCRACooldown")


PT = TypeVar("PT")
CT = TypeVar("CT")


class BucketType(enum.Enum):
    """Enum representing default implementations for the key argument in :func:`~.commands.cooldown`.

    Attributes
    ----------
    default
        The cooldown will be considered a global cooldown shared across every channel and user.
    user
        The cooldown will apply per user, accross all channels.
    channel
        The cooldown will apply to every user/chatter in the channel.
    chatter
        The cooldown will apply per user, per channel.
    """

    default = 0
    user = 1
    channel = 2
    chatter = 3

    def get_key(self, payload: twitchio.ChatMessage | Context[BotT]) -> Any:
        if self is BucketType.user:
            return payload.chatter.id

        elif self is BucketType.channel:
            return ("channel", payload.broadcaster.id)

        elif self is BucketType.chatter:
            return (payload.broadcaster.id, payload.chatter.id)

    def __call__(self, payload: twitchio.ChatMessage | Context[BotT]) -> Any:
        return self.get_key(payload)


class BaseCooldown(abc.ABC):
    """Base class used to implement your own cooldown algorithm for use with :func:`~.commands.cooldown`.

    Some built-in cooldown algorithms already exist:

    - :class:`~.commands.Cooldown` - (``Token Bucket Algorithm``)

    - :class:`~.commands.GCRACooldown` - (``Generic Cell Rate Algorithm``)


    .. note::

        Every base method must be implemented in this base class.
    """

    @abc.abstractmethod
    def reset(self) -> None:
        """Base method which should be implemented to reset the cooldown."""
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, *args: Any, **kwargs: Any) -> float | None:
        """Base method which should be implemented to update the cooldown/ratelimit.

        This is where your algorithm logic should be contained.

        .. important::

            This method should always return a :class:`float` or ``None``. If ``None`` is returned by this method,
            the cooldown will be considered bypassed.

        Returns
        -------
        :class:`float`
            The time needed to wait before you are off cooldown.
        ``None``
            Bypasses the cooldown.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self) -> Self:
        """Base method which should be implemented to return a copy of this class in it's original state."""
        raise NotImplementedError

    @abc.abstractmethod
    def is_ratelimited(self, *args: Any, **kwargs: Any) -> bool:
        """Base method which should be implemented which returns a bool indicating whether the cooldown is ratelimited.

        Returns
        -------
        bool
            A bool indicating whether this cooldown is currently ratelimited.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def is_dead(self, *args: Any, **kwargs: Any) -> bool:
        """Base method which should be implemented to indicate whether the cooldown should be considered stale and allowed
        to be removed from the ``bucket: cooldown`` mapping.

        Returns
        -------
        bool
            A bool indicating whether this cooldown is stale/old.
        """
        raise NotImplementedError


class Cooldown(BaseCooldown):
    """Default cooldown algorithm for :func:`~.commands.cooldown`, which implements a ``Token Bucket Algorithm``.

    See: :func:`~.commands.cooldown` for more documentation.
    """

    def __init__(self, *, rate: int, per: float | datetime.timedelta) -> None:
        if rate <= 0:
            raise ValueError(f'Cooldown rate must be equal to or greater than 1. Got "{rate}" expected >= 1.')

        self._rate: int = rate
        self._per: datetime.timedelta = datetime.timedelta(seconds=per) if not isinstance(per, datetime.timedelta) else per

        now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
        self._window: datetime.datetime = now + self._per

        if self._window <= now:
            raise ValueError("The provided per value for Cooldowns can not go into the past.")

        self._tokens: int = self._rate
        self.last_updated: datetime.datetime | None = None

    @property
    def per(self) -> datetime.timedelta:
        return self._per

    def reset(self) -> None:
        self._tokens = self._rate
        self._window = datetime.datetime.now(tz=datetime.UTC) + self._per

    def get_tokens(self, now: datetime.datetime | None = None) -> int:
        if now is None:
            now = datetime.datetime.now(tz=datetime.UTC)

        tokens = max(self._tokens, 0)
        if now > self._window:
            tokens = self._rate

        return tokens

    def is_ratelimited(self) -> bool:
        self._tokens = self.get_tokens()
        return self._tokens == 0

    def update(self, *, factor: int = 1) -> float | None:
        now = datetime.datetime.now(tz=datetime.UTC)
        self.last_updated = now

        self._tokens = self.get_tokens(now)

        if self._tokens == self._rate:
            self._window = datetime.datetime.now(tz=datetime.UTC) + self._per

        self._tokens -= factor

        if self._tokens < 0:
            remaining = (self._window - now).total_seconds()
            return remaining

    def copy(self) -> Self:
        return self.__class__(rate=self._rate, per=self._per)

    def is_dead(self) -> bool:
        if self.last_updated is None:
            return False

        now = datetime.datetime.now(tz=datetime.UTC)
        return now > (self.last_updated + self.per)


class GCRACooldown(BaseCooldown):
    """GCRA cooldown algorithm for :func:`~.commands.cooldown`, which implements the ``GCRA`` ratelimiting algorithm.

    See: :func:`~.commands.cooldown` for more documentation.
    """

    def __init__(self, *, rate: int, per: float | datetime.timedelta) -> None:
        if rate <= 0:
            raise ValueError(f'Cooldown rate must be equal to or greater than 1. Got "{rate}" expected >= 1.')

        self._rate: int = rate
        self._per: datetime.timedelta = datetime.timedelta(seconds=per) if not isinstance(per, datetime.timedelta) else per

        now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
        self._tat: datetime.datetime | None = None

        if (now + self._per) <= now:
            raise ValueError("The provided per value for Cooldowns can not go into the past.")

        self.last_updated: datetime.datetime | None = None

    @property
    def inverse(self) -> float:
        return self._per.total_seconds() / self._rate

    @property
    def per(self) -> datetime.timedelta:
        return self._per

    def reset(self) -> None:
        self.last_updated = None
        self._tat = None

    def is_ratelimited(self, *, now: datetime.datetime | None = None) -> bool:
        now = now or datetime.datetime.now(tz=datetime.UTC)
        tat: datetime.datetime = max(self._tat or now, now)

        separation: float = (tat - now).total_seconds()
        max_interval: float = self._per.total_seconds() - self.inverse

        return separation > max_interval

    def update(self) -> float | None:
        now: datetime.datetime = datetime.datetime.now(tz=datetime.UTC)
        tat: datetime.datetime = max(self._tat or now, now)

        self.last_updated = now

        separation: float = (tat - now).total_seconds()
        max_interval: float = self._per.total_seconds() - self.inverse

        if separation > max_interval:
            return separation - max_interval

        new = max(tat, now) + datetime.timedelta(seconds=self.inverse)
        self._tat = new

    def copy(self) -> Self:
        return self.__class__(rate=self._rate, per=self._per)

    def is_dead(self) -> bool:
        if self.last_updated is None:
            return False

        now = datetime.datetime.now(tz=datetime.UTC)
        return now > (self.last_updated + self.per)


KeyT: TypeAlias = Callable[..., Hashable] | Callable[..., Coroutine[Any, Any, Hashable]] | BucketType


class Bucket(Generic[PT]):
    def __init__(self, cooldown: BaseCooldown, *, key: KeyT) -> None:
        self._cooldown: BaseCooldown = cooldown
        self._cache: dict[Hashable, BaseCooldown] = {}
        self._key: KeyT = key

    @classmethod
    def from_cooldown(cls, *, base: type[BaseCooldown], key: KeyT, **kwargs: Any) -> Self:
        cd: BaseCooldown = base(**kwargs)
        return cls(cd, key=key)

    def create_cooldown(self) -> BaseCooldown | None:
        return self._cooldown.copy()

    def verify_cache(self) -> None:
        dead = [k for k, v in self._cache.items() if v.is_dead()]
        for key in dead:
            del self._cache[key]

    async def get_key(self, payload: PT) -> Hashable:
        if asyncio.iscoroutinefunction(self._key):
            key = await self._key(payload)  # type: ignore
        else:
            key = self._key(payload)  # type: ignore

        return key

    async def get_cooldown(self, payload: PT) -> BaseCooldown | None:
        if self._key is BucketType.default:
            return self._cooldown

        self.verify_cache()
        key = await self.get_key(payload)
        if key is None:
            return

        if key not in self._cache:
            cooldown = self.create_cooldown()

            if cooldown is not None:
                self._cache[key] = cooldown
        else:
            cooldown = self._cache[key]

        return cooldown

    async def update(self, payload: PT, **kwargs: Any) -> float | None:
        bucket = await self.get_cooldown(payload)

        if bucket is None:
            return None

        return bucket.update(**kwargs)
