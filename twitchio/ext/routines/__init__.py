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

import asyncio
import datetime
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeAlias, TypeVar

from twitchio.backoff import Backoff


__all__ = ("Routine", "routine")


T = TypeVar("T")
CoroT: TypeAlias = Callable[..., Coroutine[Any, Any, Any]]


LOGGER: logging.Logger = logging.getLogger(__name__)


def compute_timedelta(dt: datetime.datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.astimezone()

    now = datetime.datetime.now(tz=datetime.UTC)
    return max((dt - now).total_seconds(), 0)


class Routine:
    """The TwitchIO Routine class which runs asynchronously in the background on a timed loop.

    .. note::

        You should not instantiate this class manually, instead use the :func:`routine` decorator instead.


    Examples
    --------

    .. code:: python3

        # This routine will run every minute until stopped or canceled.

        @routines.routine(delta=datetime.timedelta(minutes=1))
        async def my_routine() -> None:
            print("Hello World!")

        my_routine.start()

    .. code:: python3

        # Pass some arguments to a routine...

        @routines.routine(delta=datetime.timedelta(minutes=1))
        async def my_routine(hello: str) -> None:
            print(f"Hello {hello}")

        my_routine.start("World!")

    .. code:: python3

        # Only run the routine three of times...

        @routines.routine(delta=datetime.timedelta(minutes=1), iterations=3)
        async def my_routine(hello: str) -> None:
            print(f"Hello {hello}")

        my_routine.start("World!")

    """

    def __init__(
        self,
        *,
        name: str | None = None,
        coro: CoroT,
        max_attempts: int | None = None,
        iterations: int | None,
        wait_remainder: bool = False,
        stop_on_error: bool = False,
        wait_first: bool,
        time: datetime.datetime | None,
        delta: datetime.timedelta | None,
    ) -> None:
        self._coro: CoroT = coro
        self._name: str = name or f"twitchio.ext.routines: <{self.__class__.__qualname__}[{self._coro.__qualname__}]>"
        self._task: asyncio.Task[None] | None = None
        self._injected = None
        self._time: datetime.datetime | None = time
        self._original_delta: datetime.timedelta | None = delta
        self._delta: float | None = delta.total_seconds() if delta else None

        self._before_routine: CoroT | None = None
        self._after_routine: CoroT | None = None
        self._on_error: CoroT | None = None

        self._stop_on_error: bool = stop_on_error
        self._should_stop: bool = False
        self._restarting: bool = False
        self._wait_first: bool = wait_first

        self._completed: int = 0
        self._iterations: int | None = iterations
        self._current_iteration: int = 0
        self._wait_remainder: bool = wait_remainder
        self._last_start: datetime.datetime | None = None

        self._max_attempts: int | None = max_attempts

        self._args: Any = ()
        self._kwargs: Any = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}[{self._coro.__qualname__}]>"

    def __get__(self, instance: T, type_: type[T]) -> Routine:
        if instance is None:
            return self

        copy: Routine = Routine(
            coro=self._coro,
            name=self._name,
            time=self._time,
            delta=self._original_delta,
            max_attempts=self._max_attempts,
            iterations=self._iterations,
            wait_remainder=self._wait_remainder,
            wait_first=self._wait_first,
            stop_on_error=self._stop_on_error,
        )
        copy._injected = instance
        copy._before_routine = self._before_routine
        copy._after_routine = self._after_routine
        copy._on_error = self._on_error

        setattr(instance, self._coro.__name__, copy)
        return copy

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self._injected:
            args = (self._injected, *args)

        await self._coro(*args, **kwargs)

    def _can_cancel(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _call_error(self, error: Exception) -> None:
        if self._on_error is None:
            await self.on_error(error)
            return

        if self._injected is not None:
            await self._on_error(self._injected, error)
        else:
            await self._on_error(error)

    async def _routine_loop(self, *args: Any, **kwargs: Any) -> None:
        backoff: Backoff = Backoff(base=3, maximum_time=10, maximum_tries=5)

        if self._should_stop:
            return

        if self._before_routine:
            try:
                await self._before_routine(*args, **kwargs)
            except Exception as e:
                await self._call_error(e)
                return self.cancel()

        if self._wait_first:
            if self._time:
                await asyncio.sleep(compute_timedelta(self._time))
            elif self._delta:
                await asyncio.sleep(self._delta)

        attempts: int | None = self._max_attempts
        try:
            while True:
                self._last_start: datetime.datetime | None = datetime.datetime.now(tz=datetime.UTC)
                self._current_iteration += 1

                try:
                    await self._coro(*args, **kwargs)
                except Exception as e:
                    await self._call_error(e)

                    if self._stop_on_error:
                        self._should_stop = False
                        break

                    if attempts is not None:
                        attempts -= 1

                        if attempts <= 0:
                            LOGGER.warning(
                                "The maximum retry attempts for Routine: %s has been reached and will now be canceled.",
                                self.__repr__(),
                            )
                            break

                        await asyncio.sleep(backoff.calculate())
                        continue

                else:
                    attempts = self._max_attempts
                    self._completed += 1

                if self.remaining_iterations is not None and self.remaining_iterations <= 0:
                    break

                if self._should_stop:
                    self._should_stop = False
                    break

                if self._time:
                    sleep = compute_timedelta(self._time + datetime.timedelta(days=self._current_iteration))
                else:
                    assert self._delta is not None

                    if not self._wait_remainder:
                        sleep = self._delta
                    else:
                        maxxed = (self._last_start - datetime.datetime.now(tz=datetime.UTC)).total_seconds()
                        sleep = max(maxxed + self._delta, 0)

                await asyncio.sleep(sleep)

        except Exception as e:
            msg = "A fatal error occured during an iteration of Routine: %s. This routine will now be canceled."
            LOGGER.error(msg, self.__repr__(), exc_info=e)

        if self._after_routine:
            try:
                await self._after_routine(*args, **kwargs)
            except Exception as e:
                await self._call_error(e)

        self.cancel()

    @property
    def args(self) -> tuple[Any, ...]:
        """Property returning any positional arguments passed to the routine via :meth:`.start`."""
        return self._args

    @property
    def kwargs(self) -> Any:
        """Property returning any keyword arguments passed to the routine via :meth:`.start`."""
        return self._kwargs

    def start(self, *args: Any, **kwargs: Any) -> asyncio.Task[None]:
        r"""Method to start the :class:`~Routine` in the background.

        .. note::

            You can not start an already running task. See: :meth:`.restart` instead.

        Parameters
        ----------
        *args: Any
            Any positional args passed to this method will also be passed to your :class:`~Routine` callback.
        **kwargs: Any
            Any keyword arguments passed to this method will also be passed to your :class:`~Routine` callback.

        Returns
        -------
        :class:`asyncio.Task`
            The internal background task associated with this :class:`~Routine`.
        """
        if self._task and not self._task.done() and not self._restarting:
            raise RuntimeError(f"Routine {self!r} is currently running and has not completed.")

        self._args = args
        self._kwargs = kwargs

        if self._injected:
            args = (self._injected, *args)

        self._restarting = False

        loop = self._routine_loop(*args, **kwargs)
        self._task = asyncio.create_task(loop, name=self._name)

        return self._task

    def stop(self) -> None:
        """Method to stop the currently running task after it completes its current iteration.

        Unlike :meth:`.cancel` this will schedule the task to stop after it completes its next iteration.
        """
        self._should_stop = True

    def cancel(self) -> None:
        """Method to immediately cancel the currently running :class:`~Routine`.

        Unlike :meth:`.stop`, this method is not graceful and will cancel the task in its current iteration.
        """
        if self._can_cancel():
            assert self._task is not None
            self._task.cancel()

        if not self._restarting:
            self._task = None

    def restart(self, *, force: bool = True) -> None:
        """Method which restarts the :class:`~Routine`.

        If the :class:`~Routine` has not yet been started, this method immediately returns.

        Parameters
        ----------
        force: bool
            Whether to cancel the currently running routine and restart it immediately. If this is ``False`` the
            :class:`~Routine` will start after it's current iteration. Defaults to ``True``.
        """
        self._restarting = True
        self._current_iteration = 0

        if not self._task:
            return

        def restart_when_over(fut: asyncio.Task[None]) -> None:
            fut.remove_done_callback(restart_when_over)
            self.start(*self._args, **self._kwargs)

        if self._can_cancel():
            self._task.add_done_callback(restart_when_over)

            if force:
                self._task.cancel()
            else:
                self.stop()

    def before_routine(self, func: CoroT) -> None:
        """|deco|

        Decorator used to set a coroutine to run before the :class:`~Routine` has started.

        Any arguments passed to :meth:`.start` will also be passed to this coroutine callback.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'"before_routine" for {self!r} expected a coroutine function not {type(func).__name__!r}')

        if self._before_routine is not None:
            LOGGER.warning("The before_routine for %s has previously been set.", self.__repr__())

        self._before_routine = func

    def after_routine(self, func: CoroT) -> None:
        """|deco|

        Decorator used to set a coroutine to run after the :class:`~Routine` has been stopped, canceled or completed.

        Any arguments passed to :meth:`.start` will also be passed to this coroutine callback.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'"after_routine" for {self!r} expected a coroutine function not {type(func).__name__!r}')

        if self._after_routine is not None:
            LOGGER.warning("The after_routine for %s has previously been set.", self.__repr__())

        self._after_routine = func

    async def on_error(self, error: Exception) -> None:
        """|coro|

        Default error handler for this :class:`~Routine`. You can override this with the :meth:`.error` decorator.

        By default this handler will log the exception.

        Parameters
        ----------
        error: Exception
            The exception raised in the routine.
        """
        msg = "Ignoring Exception in Routine %s: %s\n"
        LOGGER.error(msg, self.__repr__(), error, exc_info=error)

    def error(self, func: CoroT) -> None:
        """|deco|

        Decorator used to set a coroutine as an error handler for this :class:`~Routine`.
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f'"error" for {self!r} expected a coroutine function not {type(func).__name__!r}')

        self._on_error = func

    @property
    def completed_iterations(self) -> int:
        """Property returning a :class:`int` of the successfully completed iterations.

        .. note::

            Iterations where an error occured do not count towards completed iterations.
        """
        return self._completed

    @property
    def remaining_iterations(self) -> int | None:
        """Property returning a :class:`int` or :class:`None` of the remaining iterations.

        If ``iterations`` was not set this returns ``None``.
        """
        return None if self._iterations is None else self._iterations - self._completed

    @property
    def current_iteration(self) -> int:
        """Property returning the current iteration count as a :class:`int`."""
        return self._current_iteration

    @property
    def last_iteration(self) -> datetime.datetime | None:
        """Property which returns a :class:`datetime.datetime` of when the current iteration started."""
        return self._last_start

    def next_iteration(self) -> float:
        """Method which returns the time until the next iteration as a float of seconds."""
        if self._time:
            return compute_timedelta(self._time + datetime.timedelta(days=self._current_iteration))

        assert self._delta is not None

        if self._last_start is None:
            return self._delta
        else:
            return max((self._last_start - datetime.datetime.now(tz=datetime.UTC)).total_seconds() + self._delta, 0)

    def change_interval(
        self,
        *,
        delta: datetime.timedelta | None = None,
        time: datetime.datetime | None = None,
        wait_first: bool = False,
    ) -> None:
        """Method to change the running interval of a currently running routine.

        Parameters
        ----------
        delta: datetime.timedelta | None
            A :class:`datetime.timedelta` of time to wait per iteration of the :class:`~Routine`. If this is ``None``,
            you must pass the ``time`` parameter. Defaults to ``None``.
        time: datetime.datetime | None
            A :class:`datetime.datetime` to schedule an run each iteration of the :class:`~Routine`. The :class:`~Routine` will
            run at the same time everyday. If this is ``None``, you must pass the ``delta`` parameter. Defaults to ``None``.
        wait_first: bool
            An optional :class:`bool` indicating whether the currently running routine should complete it's current iteration
            before restarting. Defaults to ``False`` which will immediately cancel the currently running iteration and restart
            the routine with the new times provided.
        """
        if not time and not delta:
            raise RuntimeError('One of either the "time" or "delta" arguments must be passed.')

        if time is not None and delta is not None:
            raise RuntimeError(
                'The "time" argument can not be used in conjunction with the "delta" argument. Only one should be set.'
            )

        if not time:
            delta_ = delta
        else:
            delta_ = None

            now = datetime.datetime.now(time.tzinfo)
            if time < now:
                time = datetime.datetime.combine(now.date(), time.time())
            if time < now:
                time = time + datetime.timedelta(days=1)

        self._time = time
        self._original_delta = delta_
        self._delta = delta_.total_seconds() if delta_ else None

        self.restart(force=not wait_first)


def routine(
    *,
    delta: datetime.timedelta | None = None,
    time: datetime.datetime | None = None,
    name: str | None = None,
    iterations: int | None = None,
    wait_first: bool = False,
    wait_remainder: bool = False,
    max_attempts: int | None = 5,
    stop_on_error: bool = False,
) -> Callable[[CoroT], Routine]:
    """|deco|

    A decorator to assign a coroutine as a :class:`~Routine`.

    .. important::

        One parameter of either ``time`` or ``delta`` must be passed. Both parameters CAN NOT be used together.

    Parameters
    ----------
    delta: :class:`datetime.timedelta` | None
        A :class:`datetime.timedelta` of time to wait per iteration of the :class:`~Routine`. If this is ``None``,
        you must pass the ``time`` parameter. Defaults to ``None``.
    time: :class:`datetime.datetime` | None
        A :class:`datetime.datetime` to schedule an run each iteration of the :class:`~Routine`. The :class:`~Routine` will
        run at the same time everyday. If this is ``None``, you must pass the ``delta`` parameter. Defaults to ``None``.
    name: str | None
        An optional name to use for this routine. Defaults to ``None`` which uses the repr of the :class:`~Routine`.
    iterations: int | None
        An optional :class:`int` amount of iterations to run this routine for. For example if set to ``3``, the
        :class:`~Routine` will only run ``3`` times and complete. If set to ``None`` the routine will continue running
        until stopped or canceled. Defaults to ``None``.
    wait_first: bool
        Whether the :class:`~Routine` should wait the amount of time specified in ``time`` or ``delta`` before starting.
        Defaults to ``False``, which will run the first iteration immediately after :meth:`~Routine.start` is called.
    wait_remainder: bool
        Whether to wait **only** the remaining time to the next iteration after the current iteration completes.
        For example if your :class:`~Routine` is scheduled to run every minute, and your iteration took ``30 seconds``,
        the routine will only wait an additional ``30 seconds`` before running its next iteration. Defaults to ``False``
        which means that the :class:`~Routine` will wait the full time **after** each iteration. Note: this has no effect
        when the ``time`` parameter is passed.
    max_attempts: int | None
        The maximum times the :class:`~Routine` should be allowed to error consecuitevely before stopping. When an error
        occurs and this parameter is set, the routine will sleep for a small backoff interval before retrying the iteration.
        If the ``max_attempts`` counter is hit after multiple consecutive errors, the routine will stop. This counter resets
        when a successful iteration occurs. Note: ``max_attempts`` has no effect when ``stop_on_error`` is set.
        If set to ``None``, the routine will backoff indefinitely. Defaults to ``5``.
    stop_on_error: bool
        A bool indicating whether the :class:`~Routine` should immediately stop when encountering an error. This parameter
        takes precedence over ``max_attempts``. Defaults to ``False``.

    Raises
    ------
    :class:`TypeError`
        The function decorated is not a coroutine function.
    :class:`RuntimeError`
        The ``time`` and ``delta`` arguments were both passed together. Only one of these parameters can be used.
    :class:`RuntimeError`
        Both the ``time`` and ``delta`` arguments are missing. One of these parameters must be used.
    """

    def wrapper(func: CoroT) -> Routine:
        nonlocal time

        if not asyncio.iscoroutinefunction(func):
            raise TypeError(f"Routine expected coroutine function not {type(func).__name__!r}")

        if not time and not delta:
            raise RuntimeError('One of either the "time" or "delta" arguments must be passed.')

        if time is not None and delta is not None:
            raise RuntimeError(
                'The "time" argument can not be used in conjunction with the "delta" argument. Only one should be set.'
            )

        if not time:
            delta_ = delta
        else:
            delta_ = None

            now = datetime.datetime.now(time.tzinfo)
            if time < now:
                time = datetime.datetime.combine(now.date(), time.time())
            if time < now:
                time = time + datetime.timedelta(days=1)

        return Routine(
            coro=func,
            time=time,
            delta=delta_,
            name=name,
            iterations=iterations,
            wait_first=wait_first,
            wait_remainder=wait_remainder,
            max_attempts=max_attempts,
            stop_on_error=stop_on_error,
        )

    return wrapper
