from discord import Attachment, Interaction, app_commands

from bot.permissions import can_upload
from config.settings import get_settings
from services.document_service import DocumentService
from storage.drive_adapter import GoogleDriveAdapter


def _service() -> tuple[DocumentService, object]:
    settings = get_settings()
    return DocumentService(GoogleDriveAdapter(), date_format=settings.date_format), settings


@app_commands.command(name='new_version', description='Upload a new version for an existing document ID')
async def new_version_command(interaction: Interaction, doc_id: str, file: Attachment) -> None:
    await interaction.response.defer(ephemeral=True)
    if not can_upload(interaction):
        await interaction.followup.send('You do not have permission to upload a new version.', ephemeral=True)
        return
    content = await file.read()
    document_service, settings = _service()
    try:
        created, link = document_service.new_version(
            doc_id=doc_id,
            original_filename=file.filename,
            content=content,
            mime_type=file.content_type,
            uploader_id=str(interaction.user.id),
            root_folder_id=settings.google_drive_root_folder_id,
        )
    except ValueError as err:
        await interaction.followup.send(str(err), ephemeral=True)
        return

    await interaction.followup.send(f'Uploaded `{created.filename}` as v{created.version}. {link}', ephemeral=True)
