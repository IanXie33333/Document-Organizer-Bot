from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class DocumentRecord(Base):
    __tablename__ = 'documents'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    logical_doc_id: Mapped[str] = mapped_column(String(36), index=True, default=lambda: str(uuid4()))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)

    filename: Mapped[str] = mapped_column(String(512), index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    project: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(128), index=True)
    tags_csv: Mapped[str] = mapped_column(Text, default='')

    drive_file_id: Mapped[str] = mapped_column(String(255), unique=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    uploader_discord_id: Mapped[str] = mapped_column(String(64), index=True)
    mime_type: Mapped[str] = mapped_column(String(128), default='application/octet-stream')
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
