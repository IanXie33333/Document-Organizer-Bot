from io import BytesIO

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from config.settings import get_settings
from storage.interface import UploadResult


class GoogleDriveAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_file(settings.google_service_account_file, scopes=scopes)
        self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    def _drive_kwargs(self) -> dict:
        kwargs: dict = {'supportsAllDrives': True}
        if self.settings.google_drive_use_shared_drive and self.settings.google_drive_shared_drive_id:
            kwargs['driveId'] = self.settings.google_drive_shared_drive_id
            kwargs['corpora'] = 'drive'
            kwargs['includeItemsFromAllDrives'] = True
        return kwargs

    def _find_folder(self, parent_id: str, name: str) -> str | None:
        query = (
            f"name='{name}' and '{parent_id}' in parents and "
            "mimeType='application/vnd.google-apps.folder' and trashed=false"
        )
        result = self.service.files().list(q=query, fields='files(id,name)', **self._drive_kwargs()).execute()
        files = result.get('files', [])
        return files[0]['id'] if files else None

    def _create_folder(self, parent_id: str, name: str) -> str:
        metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
        folder = self.service.files().create(body=metadata, fields='id', supportsAllDrives=True).execute()
        return folder['id']

    def ensure_folder_path(self, root_folder_id: str, path_parts: list[str]) -> str:
        current = root_folder_id
        for part in path_parts:
            folder_id = self._find_folder(current, part)
            if not folder_id:
                folder_id = self._create_folder(current, part)
            current = folder_id
        return current

    def upload_file(self, folder_id: str, filename: str, content_bytes: bytes, mime_type: str | None) -> UploadResult:
        metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaIoBaseUpload(BytesIO(content_bytes), mimetype=mime_type or 'application/octet-stream', resumable=False)
        created = self.service.files().create(
            body=metadata,
            media_body=media,
            fields='id,webViewLink',
            supportsAllDrives=True,
        ).execute()
        return UploadResult(file_id=created['id'], web_view_link=created.get('webViewLink') or self.get_web_link(created['id']))

    def move_file(self, file_id: str, new_folder_id: str) -> None:
        file = self.service.files().get(fileId=file_id, fields='parents', supportsAllDrives=True).execute()
        previous_parents = ','.join(file.get('parents', []))
        self.service.files().update(
            fileId=file_id,
            addParents=new_folder_id,
            removeParents=previous_parents,
            fields='id,parents',
            supportsAllDrives=True,
        ).execute()

    def get_web_link(self, file_id: str) -> str:
        return f'https://drive.google.com/file/d/{file_id}/view'
