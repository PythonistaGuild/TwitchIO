from discord.ext import commands
from twitchio.ext import commands as tcommands


class DiscordCog(tcommands.TwitchBot):

    def __init__(self, bot):
        # Discord bot instance
        self.dbot = bot
        super().__init__(irc_token='...', nick='...', prefix='!', initial_channels=['...'])

        # Start the Twitch Bot
        self.loop.create_task(self.start())

    # Discord.py event
    async def on_message(self, message):
        print(message.content)

    # TwitchIO event
    async def event_message(self, message):
        print(message.content)
        await self.handle_commands(message)

    # Discord command
    @commands.command(name='test')
    async def discord_command(self, ctx):
        await ctx.send('Hai there!')

    # TwitchIO command
    @tcommands.twitch_command(name='test')
    async def twitch_command(self, ctx):
        await ctx.send('Hai there!')


# Add the Discord cog as per usual
def setup(bot):
    bot.add_cog(DiscordCog(bot))
