from discord import Interaction, app_commands

from bot.permissions import can_view
from config.settings import parse_csv_str
from db.session import session_scope
from repositories.document_repo import document_repo

@app_commands.command(name='find', description='Search uploaded documents')
@app_commands.describe(query='Keyword', project='Project filter', category='Category filter', tags='Comma-separated tags', uploader='Discord user ID')
async def find_command(
    interaction: Interaction,
    query: str | None = None,
    project: str | None = None,
    category: str | None = None,
    tags: str | None = None,
    uploader: str | None = None,
) -> None:
    await interaction.response.defer(ephemeral=True)

    if not can_view(interaction):
        await interaction.followup.send('You do not have permission to view documents.', ephemeral=True)
        return
    if not any([query, project, category, tags, uploader]):
        await interaction.followup.send('Provide at least one filter.', ephemeral=True)
        return

    with session_scope() as session:
        matches = document_repo.search(
            session,
            query=query,
            project=project,
            category=category,
            tags=parse_csv_str(tags),
            uploader=uploader,
            limit=20,
        )

    if not matches:
        await interaction.followup.send('No matching documents found.', ephemeral=True)
        return

    lines = []
    for doc in matches[:10]:
        lines.append(f"- `{doc.id[:8]}` {doc.filename} v{doc.version} ({doc.project}/{doc.category}) https://drive.google.com/file/d/{doc.drive_file_id}/view")
    await interaction.followup.send('Matches:\n' + '\n'.join(lines), ephemeral=True)
