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
        self.basic_scheduled_routine.start()

    @routines.routine(time=datetime.now() + timedelta(seconds=5), wait_first=True)
    async def basic_scheduled_routine(self):
        self.call_count += 1
        print(f"{self.call_count} the time is now {datetime.now()}")


bot = Bot()
bot.run()
