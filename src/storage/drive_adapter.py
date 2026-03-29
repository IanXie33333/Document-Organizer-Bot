from io import BytesIO
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from google_auth_oauthlib.flow import InstalledAppFlow

from config.settings import get_settings
from storage.interface import UploadResult


class GoogleDriveAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = self._build_credentials(scopes)
        self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    def _build_credentials(self, scopes: list[str]) -> Credentials | service_account.Credentials:
        if self.settings.google_auth_mode == 'oauth_user':
            return self._load_oauth_user_credentials(scopes)
        return self._load_service_account_credentials(scopes)

    def _load_service_account_credentials(self, scopes: list[str]) -> service_account.Credentials:
        creds_path = Path(self.settings.google_service_account_file).expanduser()
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Google service account credentials file not found: {creds_path}. "
                'Set GOOGLE_SERVICE_ACCOUNT_FILE in .env to a valid JSON key path.'
            )
        return service_account.Credentials.from_service_account_file(str(creds_path), scopes=scopes)

    def _load_oauth_user_credentials(self, scopes: list[str]) -> Credentials:
        client_secrets_path = Path(self.settings.google_oauth_client_secrets_file).expanduser()
        if not client_secrets_path.exists():
            raise FileNotFoundError(
                f"Google OAuth client secrets file not found: {client_secrets_path}. "
                'Set GOOGLE_OAUTH_CLIENT_SECRETS_FILE in .env to a valid JSON key path.'
            )

        token_path = Path(self.settings.google_oauth_token_file).expanduser()
        creds: Credentials | None = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes=scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), scopes)
                creds = flow.run_local_server(port=0, open_browser=False)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(creds.to_json(), encoding='utf-8')

        return creds

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

    def file_exists(self, file_id: str) -> bool:
        try:
            file = self.service.files().get(fileId=file_id, fields='id,trashed', supportsAllDrives=True).execute()
        except HttpError as err:
            status = getattr(getattr(err, 'resp', None), 'status', None)
            if status in {403, 404}:
                return False
            raise
        return not bool(file.get('trashed', False))

    def get_web_link(self, file_id: str) -> str:
        return f'https://drive.google.com/file/d/{file_id}/view'
