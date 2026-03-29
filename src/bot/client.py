import logging

import discord
from discord.ext import commands

from config.settings import get_settings


logger = logging.getLogger(__name__)


class DriveBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self) -> None:
        settings = get_settings()
        guild = discord.Object(id=settings.discord_guild_id) if settings.discord_guild_id else None

        from commands.find import find_command
        from commands.help import help_docs_command
        from commands.library_tree import library_tree_command
        from commands.list_docs import list_docs_command
        from commands.move import move_command
        from commands.new_version import new_version_command
        from commands.upload import upload_command

        add_kwargs = {'guild': guild} if guild else {}
        self.tree.add_command(upload_command, **add_kwargs)
        self.tree.add_command(find_command, **add_kwargs)
        self.tree.add_command(list_docs_command, **add_kwargs)
        self.tree.add_command(library_tree_command, **add_kwargs)
        self.tree.add_command(move_command, **add_kwargs)
        self.tree.add_command(new_version_command, **add_kwargs)
        self.tree.add_command(help_docs_command, **add_kwargs)

        if guild:
            # Prevent duplicate slash commands in a single server by using guild-only sync.
            # If global commands were previously published, clear them from Discord.
            if settings.discord_clear_global_commands_on_startup:
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                logger.info('Cleared global app commands before guild sync')
            else:
                logger.info('Skipped clearing global app commands before guild sync')

            synced = await self.tree.sync(guild=guild)
            logger.info('Synced %d app commands to guild %s', len(synced), settings.discord_guild_id)
            return

        synced = await self.tree.sync()
        logger.info('Synced %d global app commands', len(synced))
