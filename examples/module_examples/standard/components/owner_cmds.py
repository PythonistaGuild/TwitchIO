from twitchio.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import Bot
else:
    from twitchio.ext.commands import Bot

# Custom Exception for our component guard.
class NotOwnerError(commands.GuardFailure): ...

class OwnerCmds(commands.Component):
    def __init__(self, bot: commands.Bot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot
 

    async def component_command_error(self, payload: commands.CommandErrorPayload) -> bool | None:
        error = payload.exception
        if isinstance(error, NotOwnerError):
            ctx = payload.context

            await ctx.reply("Only the owner can use this command!")

            # This explicit False return stops the error from being dispatched anywhere else...
            return False
        
    # Restrict all of the commands in this component to the owner.
    @commands.Component.guard()
    def is_owner(self, ctx: commands.Context[Bot]) -> bool:
        if ctx.chatter.id != self.bot.owner_id:
            raise NotOwnerError

        return True
    
    # Manually load the cmds module.
    @commands.command()
    async def load_cmds(self, ctx: commands.Context[Bot]) -> None:
        await self.bot.load_module("components.cmds")

    # Manually unload the cmds module.
    @commands.command()
    async def unload_cmds(self, ctx: commands.Context[Bot]) -> None:
        await self.bot.unload_module("components.cmds")

    # Hot reload the cmds module atomically.
    @commands.command()
    async def reload_cmds(self, ctx: commands.Context[Bot]) -> None:
        await self.bot.reload_module("components.cmds")

    # Check which modules are loaded.
    @commands.command()
    async def loaded_modules(self, ctx: commands.Context[Bot]) -> None:
        print(self.bot.modules)
        
# This is our entry point for the module.
async def setup(bot: commands.Bot) -> None:
    await bot.add_component(OwnerCmds(bot))

# This is an optional teardown coroutine for miscellaneous clean-up if necessary.
async def teardown(bot: commands.Bot) -> None:
    ...
