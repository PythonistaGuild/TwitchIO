import asyncio
from twitchio.ext import routines, commands
from dotenv import load_dotenv
import os

load_dotenv()
from datetime import datetime, timedelta


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

    @routines.routine(seconds=1.0, iterations=5)
    async def basic_timed_routine(self, arg: str):
        print(f"Hello {arg}!")

    @routines.routine(seconds=0.1)
    async def basic_test(self):
        print(self.basic_timed_routine.next_execution_time)
        if self.basic_timed_routine.remaining_iterations == 0:
            self.basic_timed_routine.start("Restarted")

    @routines.routine(seconds=1.0, iterations=5, wait_first=True)
    async def basic_timed_wait_routine(self, arg: str):
        print(f"Hello {arg}!")

    @routines.routine(seconds=0.1)
    async def basic_wait_test(self):
        print(self.basic_timed_wait_routine.next_execution_time)
        if self.basic_timed_wait_routine.remaining_iterations == 0:
            self.basic_timed_wait_routine.start("Restarted")

    @routines.routine(time=datetime.now() + timedelta(seconds=5), wait_first=True)
    async def basic_scheduled_routine(self):
        # Note this seems to get called twice in execution. I don't think this is a result of my changes
        self.call_count += 1
        print(f"{self.call_count} the time is now {datetime.now()}")

    @routines.routine(seconds=0.1)
    async def basic_schedule_test(self):
        print(self.basic_scheduled_routine.next_execution_time)

    @routines.routine(seconds=2)
    async def restart_schedule_test(self):
        pass


bot = Bot()
# bot.basic_timed_wait_routine.start("Test")
# bot.basic_wait_test.start()

bot.basic_scheduled_routine.start()

bot.run()
