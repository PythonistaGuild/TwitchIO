from twitchio import commands


class Bot(commands.TwitchBot):

    def __init__(self):
        super().__init__(irc_token='...', api_token='...', nick='mysterialpy', prefix='!',
                         channels=['mysterialpy'])

    # Events don't need decorators when subclassed
    async def event_ready(self):
        print(f'Ready | {self.nick}')

    async def event_message(self, message):
        print(message.content)
        await self.process_commands(message)

    # Commands use a different decorator
    @commands.twitch_command(name='test')
    async def my_command(self, ctx):
        await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot()
bot.run()