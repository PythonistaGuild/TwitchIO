from twitchio.ext.commands import Cog

def prepare(bot):
    bot.add_cog(Foo())

class Foo(Cog):
    @Cog.event()
    async def event_message(self, msg):
        print(msg)
