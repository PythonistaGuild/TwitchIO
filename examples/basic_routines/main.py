"""A bare minimum example of running Routines.

This example assumes you have a Client/Bot or Components already setup and configured.
Consider reading the following examples first:

Basic Bot: https://github.com/PythonistaGuild/TwitchIO/tree/main/examples/basic_bot
Basic Bot (Using Conduits): https://github.com/PythonistaGuild/TwitchIO/tree/main/examples/basic_conduits

Routines can be used and started anywhere, but an asyncio.Loop should generally be running first.
"""
import datetime

from twitchio.ext import commands, routines


class Bot(commands.Bot):
    ...
    
    @routines.routine(delta=datetime.timedelta(seconds=60), wait_first=True)
    async def minute_routine(self) -> None:
        """A basic routine which does something every minute.
        
        This routine will wait a minute first after starting, before making the first iteration.
        """
        print("A minute has passed!")
    
    @routines.routine(delta=datetime.timedelta(seconds=1), iterations=5)
    async def first_five(self) -> None:
        """A basic routine which outputs an incrementing number every second, 5 times: E.g. 1 to 5.
        
        After 5 iterations, this routine will stop.
        """
        print(f"{self.first_five.current_iteration}!")
        
    @routines.routine(time=datetime.datetime.now())
    async def schedule(self) -> None:
        """A basic routine which runs at a specific time each day.
        
        For example purposes the routine will run at it's initial start time every day.
        """
        print(f"Hello, I run at the same time everyday!")
        
    @routines.routine(delta=datetime.timedelta(hours=1))
    async def hour_routine(self, number: int) -> None:
        """A basic routine which runs every hour.
        
        This routine has arguments parsed to it from .start()
        """
        print(f"I say the number {number} every hour!")

    async def setup_hook(self) -> None:
        self.minute_routine.start()
        self.first_five.start()
        self.schedule.start()
        self.hour_routine.start(23)

