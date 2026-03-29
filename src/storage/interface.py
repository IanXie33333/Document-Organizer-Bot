from dataclasses import dataclass
from typing import Protocol


@dataclass
class UploadResult:
    file_id: str
    web_view_link: str


class StorageAdapter(Protocol):
    def ensure_folder_path(self, root_folder_id: str, path_parts: list[str]) -> str: ...
    def upload_file(self, folder_id: str, filename: str, content_bytes: bytes, mime_type: str | None) -> UploadResult: ...
    def move_file(self, file_id: str, new_folder_id: str) -> None: ...
    def get_web_link(self, file_id: str) -> str: ...
