import discord
from discord.ext import commands


class DriveBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self) -> None:
        from commands.upload import upload_command
        from commands.find import find_command

        self.tree.add_command(upload_command)
        self.tree.add_command(find_command)
