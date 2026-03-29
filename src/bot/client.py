import asyncio
import logging

import discord
from discord.ext import commands

from config.settings import get_settings
from db.session import session_scope
from repositories.document_repo import document_repo
from storage.drive_adapter import GoogleDriveAdapter


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
        else:
            synced = await self.tree.sync()
            logger.info('Synced %d global app commands', len(synced))

        if settings.drive_deletion_monitor_enabled:
            self.loop.create_task(self._drive_deletion_monitor_loop())
            logger.info(
                'Started Drive deletion monitor (poll=%ss, scan_limit=%s)',
                settings.drive_deletion_poll_seconds,
                settings.drive_deletion_scan_limit,
            )

    async def _drive_deletion_monitor_loop(self) -> None:
        settings = get_settings()
        poll_seconds = max(30, settings.drive_deletion_poll_seconds)
        scan_limit = max(1, min(settings.drive_deletion_scan_limit, 1000))
        await self.wait_until_ready()

        while not self.is_closed():
            try:
                removed_docs = await asyncio.to_thread(self._scan_and_prune_deleted_drive_files, scan_limit)
                if removed_docs:
                    await self._send_drive_deletion_alert(removed_docs)
            except Exception:
                logger.exception('Drive deletion monitor loop failed')
            await asyncio.sleep(poll_seconds)

    def _scan_and_prune_deleted_drive_files(self, limit: int) -> list[dict[str, str]]:
        with session_scope() as session:
            docs = document_repo.list_recent(session, limit=limit)

        if not docs:
            return []

        storage = GoogleDriveAdapter()
        stale_docs: list[dict[str, str]] = []
        stale_ids: list[str] = []
        for doc in docs:
            if not storage.file_exists(doc.drive_file_id):
                stale_ids.append(doc.id)
                stale_docs.append(
                    {
                        'filename': doc.filename,
                        'project': doc.project,
                        'category': doc.category,
                    }
                )

        if stale_ids:
            with session_scope() as session:
                document_repo.delete_by_ids(session, stale_ids)
        return stale_docs

    async def _send_drive_deletion_alert(self, removed_docs: list[dict[str, str]]) -> None:
        settings = get_settings()
        if not settings.channel_allowlist:
            logger.warning('Deleted-file alert skipped: ALLOWED_CHANNEL_IDS is empty')
            return

        channel_id = next(iter(settings.channel_allowlist))
        channel = self.get_channel(channel_id)
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception:
                logger.exception('Deleted-file alert failed: could not fetch channel %s', channel_id)
                return

        preview = removed_docs[:5]
        lines = ['🗑️ **Drive Deletion Detected**', f'Removed `{len(removed_docs)}` stale file record(s) from the bot index:']
        for item in preview:
            lines.append(f"- `{item['filename']}` ({item['project']}/{item['category']})")
        if len(removed_docs) > len(preview):
            lines.append(f'- ...and {len(removed_docs) - len(preview)} more')

        try:
            await channel.send('\n'.join(lines))
        except Exception:
            logger.exception('Deleted-file alert failed: could not send message to channel %s', channel_id)
