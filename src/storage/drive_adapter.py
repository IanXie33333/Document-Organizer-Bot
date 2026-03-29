from storage.interface import UploadResult


class GoogleDriveAdapter:
    """Placeholder adapter.

    Replace internals with google-api-python-client calls once credentials and
    target shared-drive rules are finalized by the team.
    """

    def ensure_folder_path(self, root_folder_id: str, path_parts: list[str]) -> str:
        del path_parts
        return root_folder_id

    def upload_file(self, folder_id: str, filename: str, content_bytes: bytes, mime_type: str | None) -> UploadResult:
        del folder_id, filename, content_bytes, mime_type
        return UploadResult(file_id='mock-file-id', web_view_link='https://drive.google.com/file/d/mock-file-id/view')

    def get_web_link(self, file_id: str) -> str:
        return f'https://drive.google.com/file/d/{file_id}/view'
