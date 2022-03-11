from twitchio.ext import routines

# This routine will run every 5 seconds for 5 iterations.
@routines.routine(seconds=5.0, iterations=5)
async def hello(arg: str):
    print(f'Hello {arg}!')


hello.start('World')