import asyncio

from discord import Attachment, Interaction, app_commands

from bot.permissions import can_upload
from config.settings import get_settings
from services.document_service import DocumentService
from storage.drive_adapter import GoogleDriveAdapter


def _service() -> tuple[DocumentService, object]:
    settings = get_settings()
    return DocumentService(GoogleDriveAdapter(), date_format=settings.date_format), settings


@app_commands.command(name='upload', description='Upload and organize a document')
@app_commands.describe(file='Document attachment', project='Project name', category='Category', title='Optional title', tags='Comma-separated tags')
async def upload_command(
    interaction: Interaction,
    file: Attachment,
    project: str,
    category: str,
    title: str | None = None,
    tags: str | None = None,
    confidential: bool = False,
) -> None:
    await interaction.response.defer(ephemeral=True)

    if not can_upload(interaction):
        await interaction.followup.send('You do not have permission to upload.', ephemeral=True)
        return

    try:
        document_service, settings = _service()
    except FileNotFoundError as err:
        await interaction.followup.send(f'Upload failed: {err}', ephemeral=True)
        return

    ext = file.filename.rsplit('.', maxsplit=1)[-1].lower() if '.' in file.filename else ''
    if ext not in settings.extensions:
        await interaction.followup.send(f'File type .{ext or "unknown"} is not allowed.', ephemeral=True)
        return
    if file.size > settings.max_upload_mb * 1024 * 1024:
        await interaction.followup.send('File exceeds max upload size.', ephemeral=True)
        return

    content = await file.read()
    resolved_title = title or file.filename.rsplit('.', maxsplit=1)[0]

    try:
        created, link = await asyncio.to_thread(
            document_service.upload_document,
            original_filename=file.filename,
            content=content,
            mime_type=file.content_type,
            project=project,
            category=category,
            title=resolved_title,
            tags_csv=tags,
            uploader_id=str(interaction.user.id),
            root_folder_id=settings.google_drive_root_folder_id,
            is_confidential=confidential,
        )
    except Exception as err:  # surfaced to user instead of silent command failure
        await interaction.followup.send(f'Upload failed: {err}', ephemeral=True)
        return
    await interaction.followup.send(
        (
            'Uploaded successfully.\n'
            f'Doc ID: `{created.id}`\n'
            f'Version: `{created.version}`\n'
            f'File: `{created.filename}`\n'
            f'Project/Category: `{created.project}/{created.category}`\n'
            f'Link: {link}'
        ),
        ephemeral=True,
    )
