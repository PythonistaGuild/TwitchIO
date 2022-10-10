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
import asyncio
import datetime
import sys
import traceback
from typing import Callable, Optional


__all__ = ("Routine", "routine")


def compute_timedelta(dt: datetime.datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.astimezone()

    now = datetime.datetime.now(datetime.timezone.utc)
    return max((dt - now).total_seconds(), 0)


class Routine:
    """The main routine class which helps run async background tasks on a schedule.

    Examples
    --------
    .. code:: py

        @routine(seconds=5, iterations=3)
        async def test(arg):
            print(f'Hello {arg}')

        test.start('World!')


    .. warning::

        This class should not be instantiated manually. Use the decorator :func:`routine` instead.
    """

    def __init__(
        self,
        *,
        coro: Callable,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        iterations: Optional[int] = None,
        time: Optional[datetime.datetime] = None,
        delta: Optional[float] = None,
        wait_first: Optional[bool] = False,
    ):
        self._coro = coro
        self._loop = loop or asyncio.get_event_loop()
        self._task: asyncio.Task = None  # type: ignore

        self._time = time
        self._delta = delta

        self._start_time: datetime.datetime = None  # type: ignore

        self._completed_loops = 0

        iterations = iterations if iterations != 0 else None
        self._iterations = iterations
        self._remaining_iterations = iterations

        self._before = None
        self._after = None
        self._error = None

        self._stop_set = False
        self._restarting = False
        self._wait_first = wait_first

        self._stop_on_error = True

        self._instance = None

        self._args: tuple | None = None
        self._kwargs: dict | None = None

    def __get__(self, instance, owner):
        if instance is None:
            return self

        copy = Routine(
            coro=self._coro,
            loop=self._loop,
            iterations=self._iterations,
            time=self._time,
            delta=self._delta,
            wait_first=self._wait_first,
        )

        copy._instance = instance
        copy._before = self._before
        copy._after = self._after
        copy._error = self._error
        setattr(instance, self._coro.__name__, copy)

        return copy

    def start(self, *args, **kwargs) -> asyncio.Task:
        """Start the routine and return the created task.

        Parameters
        ----------
        stop_on_error: Optional[bool]
            Whether or not to stop and cancel the routine on error. Defaults to True.
        \*args
            The args to pass to the routine.
        \*\*kwargs
            The kwargs to pass to the routine.

        Returns
        -------
        :class:`asyncio.Task`
            The created internal asyncio task.

        Raises
        ------
        RuntimeError
            Raised when this routine is already running when start is called.
        """
        if self._task is not None and not self._task.done() and not self._restarting:
            raise RuntimeError(f"Routine {self._coro.__name__!r} is already running and is not done.")

        self._args, self._kwargs = args, kwargs

        self._restarting = False
        self._task = self._loop.create_task(self._routine(*args, **kwargs))

        if not self._error:
            self._error = self.on_error

        return self._task

    def stop(self) -> None:
        """Stop the routine gracefully.

        .. note::

            This allows the current iteration to complete before the routine is cancelled.
            If immediate cancellation is desired consider using :meth:`cancel` instead.
        """
        self._stop_set = True

    def cancel(self) -> None:
        """Cancel the routine effective immediately and non-gracefully.

        .. note::

            Consider using :meth:`stop` if a graceful stop, which will complete the current iteration, is desired.
        """
        if self._can_be_cancelled():
            self._task.cancel()

        if not self._restarting:
            self._task = None

    def restart(self, *args, **kwargs) -> None:
        """Restart the currently running routine.

        Parameters
        ----------
        stop_on_error: Optional[bool]
            Whether or not to stop and cancel the routine on error. Defaults to True.
        force: Optional[bool]
            If True the restart will cancel the currently running routine effective immediately and restart.
            If False a graceful stop will occur, which allows the routine to finish it's current iteration.
            Defaults to True.
        \*args
            The args to pass to the routine.
        \*\*kwargs
            The kwargs to pass to the routine.


        .. note::

            This does not return the internal task unlike :meth:`start`.
        """
        force = kwargs.pop("force", True)
        self._restarting = True

        self._remaining_iterations = self._iterations

        def restart_when_over(fut, *, args=args, kwargs=kwargs):
            self._task.remove_done_callback(restart_when_over)
            self.start(*args, **kwargs)

        if self._can_be_cancelled():
            self._task.add_done_callback(restart_when_over)

            if force:
                self._task.cancel()
            else:
                self.stop()

    def before_routine(self, coro: Callable) -> None:
        """A decorator to assign a coroutine to run before the routine starts."""
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"Expected coroutine function not type, {type(coro).__name__!r}.")

        self._before = coro

    def after_routine(self, coro: Callable) -> None:
        """A decorator to assign a coroutine to run after the routine has ended."""
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"Expected coroutine function not type, {type(coro).__name__!r}.")

        self._after = coro

    def change_interval(
        self,
        *,
        seconds: Optional[float] = 0,
        minutes: Optional[float] = 0,
        hours: Optional[float] = 0,
        time: Optional[datetime.datetime] = None,
        wait_first: Optional[bool] = False,
    ) -> None:
        """Method which schedules the running interval of the task to change.

        Parameters
        ----------
        seconds: Optional[float]
            The seconds to wait before the next iteration of the routine.
        minutes: Optional[float]
            The minutes to wait before the next iteration of the routine.
        hours: Optional[float]
            The hours to wait before the next iteration of the routine.
        time: Optional[datetime.datetime]
            A specific time to run this routine at. If a naive datetime is passed, your system local time will be used.
        wait_first: Optional[bool]
            Whether to wait the specified time before running the first iteration at the new interval.
            Defaults to False.

        Raises
        ------
        RuntimeError
            Raised when the time argument and any hours, minutes or seconds is passed together.


        .. warning::

            The time argument can not be passed in conjunction with hours, minutes or seconds.
            This behaviour is intended as it allows the time to be exact every day.
        """
        time_ = time

        if any((seconds, minutes, hours)) and time_:
            raise RuntimeError(
                "Argument <time> can not be used in conjunction with any <seconds>, <minutes> or <hours> argument(s)."
            )

        if not time_:
            delta = compute_timedelta(
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours)
            )

            self._delta = delta
        else:
            now = datetime.datetime.now(time_.tzinfo)
            if time_ < now:
                time_ = datetime.datetime.combine(now.date(), time_.time())
            if time_ < now:
                time_ = time_ + datetime.timedelta(days=1)

            self._time = time_

        kwargs: dict = self._kwargs
        kwargs["force"] = not wait_first

        self.restart(*self._args, **kwargs)

    def error(self, coro: Callable):
        """A decorator to assign a coroutine as the error handler for this routine.

        The error handler takes in one argument: the exception caught.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"Expected coroutine function not type, {type(coro).__name__!r}.")

        self._error = coro

    async def on_error(self, error: Exception):
        """The default error handler for this routine. Can be overwritten with :meth:`error`."""
        print(f"Exception in routine {self._coro.__name__!r}:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @property
    def completed_iterations(self) -> int:
        """A count of completed iterations."""
        return self._completed_loops

    @property
    def remaining_iterations(self) -> Optional[int]:
        """A count of remaining iterations."""
        return self._remaining_iterations

    @property
    def start_time(self) -> Optional[datetime.datetime]:
        """The time the routine was started.

        .. note::

            This does not reset when restarting, stopping or cancelling the routine.
        """
        return self._start_time

    def _can_be_cancelled(self) -> bool:
        return self._task and not self._task.done()

    async def _routine(self, *args, **kwargs) -> None:
        self._stop_on_error = kwargs.pop("stop_on_error", self._stop_on_error)

        self._start_time = datetime.datetime.now(datetime.timezone.utc)

        try:
            if self._before:
                if self._instance:
                    await self._before(self._instance)
                else:
                    await self._before()
        except Exception as e:
            await self._error(e)

            if self._stop_on_error:
                return self.cancel()

        if self._time:
            wait = compute_timedelta(self._time)
            await asyncio.sleep(wait)

        if self._wait_first and not self._time:
            await asyncio.sleep(self._delta)

        if self._remaining_iterations == 0:
            self._remaining_iterations = self._iterations

        while True:
            start = datetime.datetime.now(datetime.timezone.utc)

            try:
                if self._instance:
                    await self._coro(self._instance, *args, **kwargs)
                else:
                    await self._coro(*args, **kwargs)
            except Exception as e:
                await self._error(e)

                if self._stop_on_error:
                    return self.cancel()

            try:
                self._remaining_iterations -= 1
            except TypeError:
                pass
            else:
                if self._remaining_iterations == 0:
                    break

            if self._stop_set:
                self._stop_set = False
                break

            if self._time:
                sleep = compute_timedelta(self._time + datetime.timedelta(days=self._completed_loops))
            else:
                sleep = max((start - datetime.datetime.now(datetime.timezone.utc)).total_seconds() + self._delta, 0)

            self._completed_loops += 1
            await asyncio.sleep(sleep)

        try:
            if self._after:
                if self._instance:
                    await self._after(self._instance)
                else:
                    await self._after()
        except Exception as e:
            await self._error(e)
        finally:
            return self.cancel()


def routine(
    *,
    seconds: Optional[float] = 0,
    minutes: Optional[float] = 0,
    hours: Optional[float] = 0,
    time: Optional[datetime.datetime] = None,
    iterations: Optional[int] = None,
    wait_first: Optional[bool] = False,
):
    """A decorator to assign a coroutine as a :class:`Routine`.

    Parameters
    ----------
    seconds: Optional[float]
        The seconds to wait before the next iteration of the routine.
    minutes: Optional[float]
        The minutes to wait before the next iteration of the routine.
    hours: Optional[float]
        The hours to wait before the next iteration of the routine.
    time: Optional[datetime.datetime]
        A specific time to run this routine at. If a naive datetime is passed, your system local time will be used.
    iterations: Optional[int]
        The amount of iterations to run this routine before stopping.
        If set to None or 0, the routine will run indefinitely.
    wait_first: Optional[bool]
        Whether to wait the specified time before running the first iteration.
        This has no effect when the time argument is used. Defaults to False.

    Raises
    ------
    RuntimeError
        Raised when the time argument and any hours, minutes or seconds is passed together.
    TypeError
        Raised when used on a non-coroutine.


    .. warning::

        The time argument can not be passed in conjunction with hours, minutes or seconds.
        This behaviour is intended as it allows the time to be exact every day.
    """

    def decorator(coro: Callable) -> Routine:
        time_ = time

        if any((seconds, minutes, hours)) and time_:
            raise RuntimeError(
                "Argument <time> can not be used in conjunction with any <seconds>, <minutes> or <hours> argument(s)."
            )

        if not time_:
            delta = compute_timedelta(
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(seconds=seconds, minutes=minutes, hours=hours)
            )
        else:
            delta = None

            now = datetime.datetime.now(time_.tzinfo)
            if time_ < now:
                time_ = datetime.datetime.combine(now.date(), time_.time())
            if time_ < now:
                time_ = time_ + datetime.timedelta(days=1)

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError(f"Expected coroutine function not type, {type(coro).__name__!r}.")

        return Routine(coro=coro, time=time_, delta=delta, iterations=iterations, wait_first=wait_first)

    return decorator
