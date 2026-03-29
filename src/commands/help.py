from discord import Interaction, app_commands


@app_commands.command(name='help_docs', description='Show document bot command help')
async def help_docs_command(interaction: Interaction) -> None:
    message = (
        'Document Organizer Bot Commands:\n'
        '- `/upload file project category [title] [tags] [confidential]`\n'
        '- `/find [query] [project] [category] [tags] [uploader]`\n'
        '- `/list_docs [project] [category] [limit]`\n'
        '- `/library_tree [project] [category] [limit]`\n'
        '- `/move doc_id project category`\n'
        '- `/new_version doc_id file`\n'
    )
    await interaction.response.send_message(message, ephemeral=True)
