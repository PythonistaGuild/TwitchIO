import twitchio
from twitchio.ext import eventsub, routines, commands, pubsub
import logging
logging.basicConfig(level=10)
token = "m3pjokacck7q14e6cxf41ys164uh9m"

client = commands.Bot(token, initial_channels=["iamtomahawkx"], prefix="!")
client.load_module("blah")

@client.command()
async def yeet(ctx):
    client.reload_module("blah")

client.run()
