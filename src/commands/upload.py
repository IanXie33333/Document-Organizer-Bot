from discord import app_commands, Interaction, Attachment

from bot.permissions import can_upload
from config.settings import get_settings
from domain.models import Document
from repositories.document_repo import document_repo
from services.naming_service import build_filename
from storage.drive_adapter import GoogleDriveAdapter
from utils.file_hash import sha256_bytes


drive_adapter = GoogleDriveAdapter()


@app_commands.command(name='upload', description='Upload and organize a document')
@app_commands.describe(
    file='Document attachment',
    project='Project name',
    category='Document category',
    title='Optional title',
    tags='Comma-separated tags',
)
async def upload_command(
    interaction: Interaction,
    file: Attachment,
    project: str,
    category: str,
    title: str | None = None,
    tags: str | None = None,
) -> None:
    await interaction.response.defer(ephemeral=True)

    settings = get_settings()
    if not can_upload(interaction):
        await interaction.followup.send('You do not have permission to upload.', ephemeral=True)
        return

    ext = file.filename.rsplit('.', maxsplit=1)[-1].lower() if '.' in file.filename else ''
    if ext not in settings.extensions:
        await interaction.followup.send(f'File type .{ext or "unknown"} is not allowed.', ephemeral=True)
        return

    if file.size > settings.max_upload_mb * 1024 * 1024:
        await interaction.followup.send('File exceeds max upload size.', ephemeral=True)
        return

    content = await file.read()
    checksum = sha256_bytes(content)

    final_title = title or file.filename.rsplit('.', maxsplit=1)[0]
    filename = build_filename(project, category, final_title, version=1, extension=ext, date_format=settings.date_format)

    folder_id = drive_adapter.ensure_folder_path(settings.google_drive_root_folder_id, [project, category])
    uploaded = drive_adapter.upload_file(folder_id, filename, content, file.content_type)

    tag_list = [t.strip() for t in (tags or '').split(',') if t.strip()]
    doc = document_repo.create(
        Document(
            filename=filename,
            project=project,
            category=category,
            uploader_discord_id=str(interaction.user.id),
            drive_file_id=uploaded.file_id,
            checksum_sha256=checksum,
            tags=tag_list,
        )
    )

    await interaction.followup.send(
        (
            f'Uploaded successfully.\n'
            f'Doc ID: `{doc.id}`\n'
            f'File: `{doc.filename}`\n'
            f'Link: {uploaded.web_view_link}'
        ),
        ephemeral=True,
    )
