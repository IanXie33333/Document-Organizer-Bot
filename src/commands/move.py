from discord import Interaction, app_commands

from bot.permissions import can_upload
from config.settings import get_settings
from services.document_service import DocumentService
from storage.drive_adapter import GoogleDriveAdapter


def _service() -> tuple[DocumentService, object]:
    settings = get_settings()
    return DocumentService(GoogleDriveAdapter(), date_format=settings.date_format), settings


@app_commands.command(name='move', description='Move a document to another project/category')
async def move_command(interaction: Interaction, doc_id: str, project: str, category: str) -> None:
    await interaction.response.defer(ephemeral=True)
    if not can_upload(interaction):
        await interaction.followup.send('You do not have permission to move documents.', ephemeral=True)
        return
    document_service, settings = _service()
    try:
        doc = document_service.move_document(doc_id=doc_id, project=project, category=category, root_folder_id=settings.google_drive_root_folder_id)
    except ValueError as err:
        await interaction.followup.send(str(err), ephemeral=True)
        return

    await interaction.followup.send(f'Moved `{doc.id}` to `{doc.project}/{doc.category}`.', ephemeral=True)
