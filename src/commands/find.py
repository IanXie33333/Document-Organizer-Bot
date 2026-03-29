from discord import app_commands, Interaction

from bot.permissions import can_view
from repositories.document_repo import document_repo


@app_commands.command(name='find', description='Search uploaded documents')
@app_commands.describe(query='Keyword in filename', project='Project filter', category='Category filter')
async def find_command(
    interaction: Interaction,
    query: str | None = None,
    project: str | None = None,
    category: str | None = None,
) -> None:
    await interaction.response.defer(ephemeral=True)

    if not can_view(interaction):
        await interaction.followup.send('You do not have permission to view documents.', ephemeral=True)
        return

    if not any([query, project, category]):
        await interaction.followup.send('Provide at least one filter: query, project, or category.', ephemeral=True)
        return

    matches = document_repo.search(query=query, project=project, category=category)

    if not matches:
        await interaction.followup.send('No matching documents found.', ephemeral=True)
        return

    lines = []
    for doc in matches[:10]:
        lines.append(f"- `{doc.id[:8]}` {doc.filename} ({doc.project}/{doc.category})")

    await interaction.followup.send('Matches:\n' + '\n'.join(lines), ephemeral=True)
