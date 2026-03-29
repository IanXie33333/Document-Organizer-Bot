from datetime import datetime, timezone
from uuid import uuid4

from config.settings import parse_csv_str
from db.session import session_scope
from repositories.document_repo import document_repo
from services.naming_service import build_filename
from storage.interface import StorageAdapter
from utils.file_hash import sha256_bytes


class DocumentService:
    def __init__(self, storage: StorageAdapter, date_format: str) -> None:
        self.storage = storage
        self.date_format = date_format

    def upload_document(
        self,
        *,
        original_filename: str,
        content: bytes,
        mime_type: str | None,
        project: str,
        category: str,
        title: str,
        tags_csv: str | None,
        uploader_id: str,
        root_folder_id: str,
        is_confidential: bool = False,
    ):
        checksum = sha256_bytes(content)
        tags = parse_csv_str(tags_csv)
        extension = original_filename.rsplit('.', maxsplit=1)[-1].lower() if '.' in original_filename else 'bin'

        with session_scope() as session:
            duplicate = document_repo.find_latest_by_checksum(session, checksum)
            if duplicate:
                logical_doc_id = duplicate.logical_doc_id
                next_version = duplicate.version + 1
                document_repo.mark_group_non_latest(session, logical_doc_id)
            else:
                logical_doc_id = str(uuid4())
                next_version = 1

            filename = build_filename(
                project=project,
                category=category,
                title=title,
                version=next_version,
                extension=extension,
                date_format=self.date_format,
            )
            month_folder = datetime.now(timezone.utc).strftime('%Y-%m')
            folder_id = self.storage.ensure_folder_path(root_folder_id, [project, category, month_folder])
            upload = self.storage.upload_file(folder_id, filename, content, mime_type)

            created = document_repo.create(
                session,
                logical_doc_id=logical_doc_id,
                version=next_version,
                is_latest=True,
                filename=filename,
                original_filename=original_filename,
                project=project,
                category=category,
                tags_csv=','.join(tags),
                drive_file_id=upload.file_id,
                checksum_sha256=checksum,
                uploader_discord_id=uploader_id,
                mime_type=mime_type or 'application/octet-stream',
                size_bytes=len(content),
                is_confidential=is_confidential,
            )
            session.refresh(created)
            return created, upload.web_view_link

    def new_version(self, *, doc_id: str, original_filename: str, content: bytes, mime_type: str | None, uploader_id: str, root_folder_id: str):
        with session_scope() as session:
            target = document_repo.find_by_id(session, doc_id)
            if not target:
                raise ValueError('Document not found')

            document_repo.mark_group_non_latest(session, target.logical_doc_id)
            latest = document_repo.find_latest_in_logical_group(session, target.logical_doc_id)
            next_version = (latest.version + 1) if latest else (target.version + 1)
            extension = original_filename.rsplit('.', maxsplit=1)[-1].lower() if '.' in original_filename else 'bin'
            filename = build_filename(target.project, target.category, target.original_filename.rsplit('.', 1)[0], next_version, extension, self.date_format)
            folder_id = self.storage.ensure_folder_path(root_folder_id, [target.project, target.category, datetime.now(timezone.utc).strftime('%Y-%m')])
            upload = self.storage.upload_file(folder_id, filename, content, mime_type)

            created = document_repo.create(
                session,
                logical_doc_id=target.logical_doc_id,
                version=next_version,
                is_latest=True,
                filename=filename,
                original_filename=original_filename,
                project=target.project,
                category=target.category,
                tags_csv=target.tags_csv,
                drive_file_id=upload.file_id,
                checksum_sha256=sha256_bytes(content),
                uploader_discord_id=uploader_id,
                mime_type=mime_type or 'application/octet-stream',
                size_bytes=len(content),
                is_confidential=target.is_confidential,
            )
            session.refresh(created)
            return created, upload.web_view_link

    def move_document(self, *, doc_id: str, project: str, category: str, root_folder_id: str):
        with session_scope() as session:
            doc = document_repo.find_by_id(session, doc_id)
            if not doc:
                raise ValueError('Document not found')
            folder_id = self.storage.ensure_folder_path(root_folder_id, [project, category, datetime.now(timezone.utc).strftime('%Y-%m')])
            self.storage.move_file(doc.drive_file_id, folder_id)
            doc.project = project
            doc.category = category
            session.flush()
            return doc
