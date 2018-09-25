from twitchio import commands

# api token can be passed as test if not needed.
# Channels is the initial channels to join, this could be a list, tuple or callable
bot = commands.TwitchBot(irc_token='...', api_token='test', nick='mysterialpy', prefix='!',
                         initial_channels=['mysterialpy'])


# Register an event with the bot
@bot.event
async def event_ready():
    print(f'Ready | {bot.nick}')


@bot.event
async def event_message(message):
    print(message.content)

    # If you override event_message you will need to process_commands for commands to work.
    await bot.process_commands(message)


# Register a command with the bot
@bot.command(name='test', aliases=['t'])
async def test_command(ctx):
    await ctx.send(f'Hello {ctx.author.name}')

bot.run()