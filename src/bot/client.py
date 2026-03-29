import discord
from discord.ext import commands


class DriveBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self) -> None:
        from commands.find import find_command
        from commands.help import help_docs_command
        from commands.library_tree import library_tree_command
        from commands.list_docs import list_docs_command
        from commands.move import move_command
        from commands.new_version import new_version_command
        from commands.upload import upload_command

        self.tree.add_command(upload_command)
        self.tree.add_command(find_command)
        self.tree.add_command(list_docs_command)
        self.tree.add_command(library_tree_command)
        self.tree.add_command(move_command)
        self.tree.add_command(new_version_command)
        self.tree.add_command(help_docs_command)

        await self.tree.sync()
