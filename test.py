import asyncio
from twitchio.ext import routines, commands
from dotenv import load_dotenv
import os

load_dotenv()
from datetime import datetime, timedelta

import random

THRESHOLD = 0.1


class Bot(commands.Bot):
    call_count = 0

    def __init__(self):
        super().__init__(
            token=os.getenv("access_token"),
            prefix="#!",
            initial_channels=["dreamingofelectricsheep"],
        )

    async def event_ready(self):
        print(f"Logged in as | {self.nick}")
        print(f"User id is | {self.user_id}")
        bot.low_freq_routine.start()
        bot.reschedule_schedule_nowait_test.start()
        bot.test_low_freq_restart.start()

    @routines.routine(seconds=1.0, iterations=5)
    async def basic_timed_routine(self, arg: str):
        print(f"Hello {arg}!")

    @routines.routine(seconds=0.1)
    async def basic_test(self):
        print(self.basic_timed_routine.time_until_next_execution)
        if self.basic_timed_routine.remaining_iterations == 0:
            self.basic_timed_routine.start("Restarted")

    @routines.routine(seconds=1.0, wait_first=True)
    async def basic_timed_wait_routine(self, arg: str):
        print(f"Hello {arg}!")

    @routines.routine(seconds=0.1)
    async def basic_wait_test(self):
        print(self.basic_timed_wait_routine.time_until_next_execution)

    @routines.routine(time=datetime.now() + timedelta(seconds=5))
    async def basic_scheduled_routine(self):
        print(f"{self.call_count} the time is now {datetime.now()}")

    @routines.routine(seconds=0.1)
    async def basic_schedule_test(self):
        print(self.basic_scheduled_routine.time_until_next_execution)

    @routines.routine(minutes=5, wait_first=True)
    async def low_freq_routine(self):
        print("I ran")

    @routines.routine(seconds=5)
    async def restart_schedule_test(self):
        self.low_freq_routine.restart(force=True)

    @routines.routine(seconds=1)
    async def test_low_freq_restart(self):
        print(self.low_freq_routine.time_until_next_execution)

    @routines.routine(seconds=5, iterations=2, wait_first=True)
    async def reschedule_schedule_wait_test(self):
        print("Rescheduling")
        self.low_freq_routine.change_interval(wait_first=True, minutes=random.random() * 2)

    @routines.routine(seconds=5, iterations=2, wait_first=True)
    async def reschedule_schedule_nowait_test(self):
        print("Rescheduling")
        self.low_freq_routine.change_interval(wait_first=False, minutes=random.random() * 2)


bot = Bot()

bot.run()
