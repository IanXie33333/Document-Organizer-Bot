from discord import Interaction, app_commands

from bot.permissions import can_view
from db.session import session_scope
from repositories.document_repo import document_repo


@app_commands.command(name='list_docs', description='List recent documents (optional project/category filters)')
async def list_docs_command(interaction: Interaction, project: str | None = None, category: str | None = None, limit: int = 10) -> None:
    await interaction.response.defer(ephemeral=True)
    if not can_view(interaction):
        await interaction.followup.send('You do not have permission to view documents.', ephemeral=True)
        return

    with session_scope() as session:
        docs = document_repo.search(session, project=project, category=category, limit=max(1, min(limit, 25)))
    if not docs:
        await interaction.followup.send('No documents found.', ephemeral=True)
        return

    lines = [f"- `{d.id[:8]}` {d.filename} v{d.version} ({d.project}/{d.category})" for d in docs]
    await interaction.followup.send('Recent docs:\n' + '\n'.join(lines), ephemeral=True)
