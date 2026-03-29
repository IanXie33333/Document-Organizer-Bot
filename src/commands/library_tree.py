from collections import defaultdict

from discord import Interaction, app_commands

from bot.permissions import can_view_by_role
from db.session import session_scope
from repositories.document_repo import document_repo
from storage.drive_adapter import GoogleDriveAdapter


@app_commands.command(name='library_tree', description='Show library folder structure and recent file names')
@app_commands.describe(
    project='Optional project filter',
    category='Optional category filter',
    limit='Max files to include (default 50, max 150)',
)
async def library_tree_command(
    interaction: Interaction,
    project: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> None:
    await interaction.response.defer(ephemeral=True)
    if not can_view_by_role(interaction):
        await interaction.followup.send('You do not have permission to view documents.', ephemeral=True)
        return

    capped_limit = max(1, min(limit, 150))
    with session_scope() as session:
        docs = document_repo.search(session, project=project, category=category, limit=capped_limit)

    if not docs:
        await interaction.followup.send('No documents found for that scope.', ephemeral=True)
        return

    verification_note = ''
    stale_ids: list[str] = []
    try:
        storage = GoogleDriveAdapter()
        verified_docs = []
        for doc in docs:
            if storage.file_exists(doc.drive_file_id):
                verified_docs.append(doc)
            else:
                stale_ids.append(doc.id)
        docs = verified_docs
    except Exception:
        verification_note = '⚠️ Could not verify Drive deletions right now; showing stored index results.\n'

    if stale_ids:
        with session_scope() as session:
            removed = document_repo.delete_by_ids(session, stale_ids)
        if removed:
            verification_note += f'ℹ️ Removed {removed} stale record(s) for deleted Drive files.\n'

    if not docs:
        message = 'No documents found for that scope.'
        if verification_note:
            message = verification_note + message
        await interaction.followup.send(message, ephemeral=True)
        return

    tree: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for doc in docs:
        month = doc.created_at.strftime('%Y-%m')
        tree[doc.project][doc.category][month].append(f'{doc.filename} (v{doc.version})')

    lines = []
    if verification_note:
        lines.append(verification_note.rstrip())
    lines.append('Library structure (Project / Category / Month):')
    for project_name in sorted(tree.keys()):
        lines.append(f'📁 {project_name}')
        for category_name in sorted(tree[project_name].keys()):
            lines.append(f'  └─ 📂 {category_name}')
            for month in sorted(tree[project_name][category_name].keys(), reverse=True):
                lines.append(f'      └─ 🗂️ {month}')
                for filename in tree[project_name][category_name][month]:
                    lines.append(f'          • {filename}')

    message = '\n'.join(lines)
    if len(message) > 1900:
        message = message[:1890] + '\n... (truncated)'
    await interaction.followup.send(message, ephemeral=True)
